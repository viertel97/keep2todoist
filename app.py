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

from helper.todoist_helper import get_section

logger = setup_logging(__file__)

GOOGLE_E_MAIL, GOOGLE_APP_PASSWORD, GOOGLE_DEVICE_ID, TODOIST_TOKEN = get_secrets(
    ["google/email", "google/app_password", "google/device_id", "todoist/token"]
)
HEADERS = create_headers(TODOIST_TOKEN)


def get_todoist_project_id(api: TodoistAPI, name):
    for project in api.get_projects():
        if project.name == name:
            return project.id
    return None


def transfer_list(keep_list_name: str, todoist_project: str, check_categories: bool = False):
    logger.info(f"transferring {keep_list_name} to {todoist_project}")
    keep.sync()
    for keep_list in keep.find(func=lambda x: x.title == keep_list_name):
        if len(keep_list.items) == 0:
            logger.info("Nothing to transfer")
            return
        logger.info(f"found {len(keep_list.items)} items")
        for item in keep_list.items:
            if check_categories:
                section_id, section_name = get_section(item.text)
                todoist_project_id = get_todoist_project_id(todoist_api, todoist_project)
                todoist_api.add_task(
                    content=item.text,
                    project_id=todoist_project_id,
                    section_id=section_id,
                    due_lang="en",
                )
                logger.info(f"added '{item.text}' to '{todoist_project}' and section '{section_name}'")
            else:
                todoist_api.add_task(
                    content=item.text,
                    due_lang="en",
                )
                logger.info(f"added '{item.text}' to '{todoist_project}'")

            item.delete()
    keep.sync()
    logger.info("Added {} items to '{}'".format(len(keep_list.items), todoist_project))


def get_items_without_section(project_id="2247224944"):
    items = todoist_api.get_tasks(project_id=project_id)
    return [item for item in items if not item.section_id]


def transfer_todoist_non_section_list():
    logger.info(f"transferring non section items to categories")
    items_without_section = get_items_without_section()
    logger.info(f"found {len(items_without_section)} items")
    for item in items_without_section:
        section_id, section_name = get_section(item.content)
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
    transfer_list("Einkaufsliste", "Einkaufsliste", check_categories=True)
    transfer_list("ToDo-Liste", "Inbox")
    transfer_todoist_non_section_list()


if __name__ == "__main__":
    keep = gkeepapi.Keep()
    keep.login(GOOGLE_E_MAIL, GOOGLE_APP_PASSWORD, device_id=GOOGLE_DEVICE_ID)

    todoist_api = TodoistAPI(TODOIST_TOKEN)

    schedule.every(10).minutes.do(update)

    logger.info("start scheduler")
    update()

    while True:
        schedule.run_pending()
        time.sleep(1)
