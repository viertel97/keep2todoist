import time
import uuid
import sys

import gkeepapi
import requests
import schedule
from quarter_lib.akeyless import get_secrets
from quarter_lib.logging import setup_logging
from todoist_api_python.api import TodoistAPI
from todoist_api_python.endpoints import get_sync_url
from todoist_api_python.headers import create_headers

from helper.todoist_helper import get_section, rename_item

logger = setup_logging(__file__)

GOOGLE_E_MAIL, GOOGLE_PASSWORD, MASTER_TOKEN, DEVICE_ID, TODOIST_TOKEN = get_secrets(
    ["google/email", "google/password", "google/master_token","google/device_id", "todoist/token"]
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


def transfer_list(keep_list_names: [], todoist_project: str, check_categories: bool = False):
    logger.info(f"transferring {keep_list_names} to {todoist_project}")
    total_items_transferred = 0
    deleted_duplicates = 0
    keep.sync()
    for keep_list in keep.find(func=lambda x: x.title in keep_list_names):
        logger.info(f"found list '{keep_list.title}' with {len(keep_list.items)} items and ID {keep_list.id}")
        if len(keep_list.items) == 0:
            logger.info(f"Nothing to transfer for '{keep_list.title}' (ID {keep_list.id})")
            continue
        todoist_project_id, project_tasks = get_todoist_project_id(todoist_project)
        for item in keep_list.items:
            item_text = rename_item(item.text)
            project_task_names = [task.content for task in project_tasks]
            if item_text in project_task_names:
                deleted_duplicates += 1
                logger.info(f"item '{item_text}' already exists in '{todoist_project}' and will be deleted")
                item.delete()
                continue
            else:
                if check_categories:
                    section_id, section_name = get_section(item_text, API)
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
    keep.sync()
    logger.info(
        f"Added {total_items_transferred} items to '{todoist_project}' from {keep_list_names} - deleted {deleted_duplicates} duplicates")


def get_items_without_section(project_id="2247224944"):
    items = API.get_tasks(project_id=project_id)
    return [item for item in items if not item.section_id]


def transfer_todoist_non_section_list():
    logger.info(f"transferring non section items to categories")
    items_without_section = get_items_without_section()
    logger.info(f"found {len(items_without_section)} items")
    for item in items_without_section:
        section_id, section_name = get_section(item.content, API)
        move_item_to_section(item.id, section_id)
        logger.info(f"moved '{item.content}' to section '{section_name}'")

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
        transfer_list(["Einkaufsliste", "Einkaufszettel"], "Einkaufsliste", check_categories=True)
        transfer_list(["To-Do", "ToDo-Liste", "To-Do-Liste"], "Inbox")
        transfer_todoist_non_section_list()
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    keep = gkeepapi.Keep()
    logger.info(GOOGLE_E_MAIL)
    logger.info(MASTER_TOKEN)
    logger.info(GOOGLE_PASSWORD)
    logged_in = False

    try:
        with open('gkeepapi_token', 'r') as cached_token:
            token = cached_token.read()
    except FileNotFoundError:
        token = None

    if MASTER_TOKEN:
        try:
            keep.authenticate(GOOGLE_E_MAIL, master_token=token, sync=False, device_id=DEVICE_ID)
            logged_in = True
            logger.info("Successfully authenticated with token 👍")
        except gkeepapi.exception.LoginException:
            logger.warning("invalid token ⚠️")

    if not logged_in:
        try:
            logger.info('requesting new token')
            keep.login(GOOGLE_E_MAIL, password=GOOGLE_PASSWORD, sync=False, device_id=DEVICE_ID)
            logged_in = True
            token = keep.getMasterToken()
            with open('gkeepapi_token', 'w') as cached_token:
                cached_token.write(token)
            logger.info("authenticated successfully 👍")
        except gkeepapi.exception.LoginException as ex:
            logger.info(f'failed to authenticate ❌ {ex}')
            sys.exit(1)

    schedule.every(10).minutes.do(update)

    logger.info("start scheduler")
    update()

    while True:
        schedule.run_pending()
        time.sleep(1)
