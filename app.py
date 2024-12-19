import time
import uuid

import gkeepapi
import requests
import schedule
from quarter_lib.akeyless import get_secrets
from quarter_lib.logging import setup_logging
from todoist_api_python.api import TodoistAPI
from todoist_api_python.endpoints import get_sync_url
from todoist_api_python.headers import create_headers

from helper.tandoor_helper import add_to_shopping_list
from helper.todoist_helper import get_section, rename_item

logger = setup_logging(__file__)

GOOGLE_E_MAIL, GOOGLE_PASSWORD, MASTER_TOKEN, DEVICE_ID, TODOIST_TOKEN = get_secrets(
	[
		"google/email",
		"google/password",
		"google/master_token",
		"google/device_id",
		"todoist/token",
	]
)
HEADERS = create_headers(TODOIST_TOKEN)

API = TodoistAPI(TODOIST_TOKEN)

TODOIST_PROJECTS = API.get_projects()
TODOIST_PROJECT_NAMES = ["Einkaufsliste", "Inbox"]
FILTERED_TODOIST_PROJECTS = [project for project in TODOIST_PROJECTS if project.name in TODOIST_PROJECT_NAMES]


def get_todoist_project_id(name):
	for project in FILTERED_TODOIST_PROJECTS:
		if project.name == name:
			tasks = API.get_tasks(project_id=project.id)
			return project.id, tasks
	return None


def keep_to_tandoor(
	total_items_transferred,
	keep_list_names,
):
	for keep_list in keep.find(func=lambda x: x.title.lower() in [name.lower() for name in keep_list_names]):
		logger.info(f"found list '{keep_list.title}' with {len(keep_list.items)} items and ID {keep_list.id}")
		if len(keep_list.items) == 0:
			logger.info(f"Nothing to transfer for '{keep_list.title}' (ID {keep_list.id})")
			continue
		for item in keep_list.items:
			try:
				item_text = rename_item(item.text)
			except Exception as e:
				logger.error(f"error renaming item '{item.text}': {e}")
				item_text = item.text
			add_to_shopping_list(item_text)
			total_items_transferred += 1
			logger.info(f"added '{item_text}' to Tandoor'")
			item.delete()
	# keep_list.delete()
	return 0, total_items_transferred


def keep_to_todoist(
	check_categories,
	deleted_duplicates,
	todoist_project,
	total_items_transferred,
	keep_list_names,
):
	for keep_list in keep.find(func=lambda x: x.title.lower() in [name.lower() for name in keep_list_names]):
		logger.info(f"found list '{keep_list.title}' with {len(keep_list.items)} items and ID {keep_list.id}")
		if len(keep_list.items) == 0:
			logger.info(f"Nothing to transfer for '{keep_list.title}' (ID {keep_list.id})")
			continue
		todoist_project_id, project_tasks = get_todoist_project_id(todoist_project)
		for item in keep_list.items:
			try:
				item_text = rename_item(item.text)
			except Exception as e:
				logger.error(f"error renaming item '{item.text}': {e}")
				item_text = item.text
			project_task_names = [task.content for task in project_tasks]
			if item_text in project_task_names:
				deleted_duplicates += 1
				logger.info(f"item '{item_text}' already exists in '{todoist_project}' and will be deleted")
				item.delete()
				continue
			else:
				if check_categories:
					try:
						section_id, section_name = get_section(item_text, API)
					except Exception as e:
						logger.error(f"error getting section for item '{item_text}': {e}")
						section_id = 124643194  # Unbekannt
						section_name = None
					API.add_task(
						content=item_text,
						project_id=todoist_project_id,
						section_id=None if not check_categories else section_id,
						due_lang="en",
					)
				else:
					API.add_task(content=item_text, due_lang="en")
				total_items_transferred += 1
			if check_categories and section_id:
				logger.info(f"added '{item_text}' to '{todoist_project}' and section '{section_name}'")
			else:
				logger.info(f"added '{item_text}' to '{todoist_project}'")
			item.delete()
	# keep_list.delete()
	return deleted_duplicates, total_items_transferred


def transfer_list(
	keep_list_names: [],
	todoist_project: str,
	check_categories: bool = False,
	use_tandoor: bool = False,
):
	logger.info(f"transferring {keep_list_names} to {todoist_project}")
	total_items_transferred = 0
	deleted_duplicates = 0
	keep.sync()

	if not use_tandoor:
		deleted_duplicates, total_items_transferred = keep_to_todoist(
			check_categories,
			deleted_duplicates,
			todoist_project,
			total_items_transferred,
			keep_list_names,
		)
	else:
		deleted_duplicates, total_items_transferred = keep_to_tandoor(
			total_items_transferred,
			keep_list_names,
		)
	keep.sync()
	logger.info(
		f"Added {total_items_transferred} items to '{todoist_project}' from {keep_list_names} - deleted {deleted_duplicates} duplicates"
	)


def get_items_without_section(project_id="2247224944"):
	items = API.get_tasks(project_id=project_id)
	return [item for item in items if not item.section_id]


def transfer_todoist_non_section_list():
	logger.info("transferring non section items to categories")
	items_without_section = get_items_without_section()
	logger.info(f"found {len(items_without_section)} items")
	for item in items_without_section:
		try:
			section_id, section_name = get_section(item.content, API)
		except Exception as e:
			logger.error(f"error getting section for item '{item.content}': {e}")
			continue
		response = move_item_to_section(item.id, section_id)
		if list(response["sync_status"].values())[0] == "ok":
			logger.info(f"moved '{item.content}' to section '{section_name}'")
		else:
			logger.error(f"error moving '{item.content}' to section '{section_name}': {response}")
	logger.info("Moved {} items to correct categories".format(len(items_without_section)))


def move_item_to_section(task_id, section_id):
	return requests.post(
		get_sync_url("sync"),
		headers=HEADERS,
		json={
			"commands": [
				{
					"type": "item_move",
					"uuid": str(uuid.uuid4()),
					"args": {
						"id": task_id,
						"section_id": section_id,
					},
				}
			]
		},
	).json()


def update():
	try:
		transfer_list(
			["Einkaufsliste", "Einkaufszettel"],
			"Einkaufsliste",
			check_categories=True,
			use_tandoor=True,
		)
		transfer_list(["To-Do", "ToDo-Liste", "To-Do-Liste"], "Inbox", use_tandoor=False)
		transfer_todoist_non_section_list()
	except Exception as e:
		logger.error(e)


if __name__ == "__main__":
	keep = gkeepapi.Keep()
	keep.authenticate(GOOGLE_E_MAIL, master_token=MASTER_TOKEN, sync=False, device_id=DEVICE_ID)

	schedule.every(10).minutes.do(update)

	logger.info("start scheduler")
	update()

	while True:
		schedule.run_pending()
		time.sleep(1)
