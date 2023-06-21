import time

import gkeepapi
import schedule
from quarter_lib.akeyless import get_secrets
from quarter_lib.logging import setup_logging
from todoist_api_python.api import TodoistAPI

from helper.todoist_helper import get_section, rename_item

logger = setup_logging(__file__)

GOOGLE_E_MAIL, GOOGLE_APP_PASSWORD, GOOGLE_DEVICE_ID, TODOIST_TOKEN = get_secrets(
    ["google/email", "google/app_password", "google/device_id", "todoist/token"]
)

API = TodoistAPI(TODOIST_TOKEN)


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
            item_text = rename_item(item.text)
            if check_categories:
                section_id, section_name = get_section(item_text, API)
            if todoist_project:
                todoist_project_id = get_todoist_project_id(API, todoist_project)
                API.add_task(
                    content=item_text,
                    project_id=todoist_project_id,
                    section_id=None if not check_categories else section_id,
                    due_lang="en",
                )
            else:
                API.add_task(content=item_text, due_lang="en")
            item.delete()
            if check_categories and section_id:
                logger.info(f"added '{item_text}' to '{todoist_project}' and section '{section_name}'")
            else:
                logger.info(f"added '{item_text}' to '{todoist_project}'")
    keep.sync()
    logger.info("Added {} items to '{}'".format(len(keep_list.items), todoist_project))


def update():
    transfer_list("Einkaufsliste", "Einkaufsliste", check_categories=True)
    transfer_list("ToDo-Liste", "Inbox")


if __name__ == "__main__":
    keep = gkeepapi.Keep()
    keep.login(GOOGLE_E_MAIL, GOOGLE_APP_PASSWORD, device_id=GOOGLE_DEVICE_ID)

    schedule.every(10).minutes.do(update)

    logger.info("start scheduler")
    update()

    while True:
        schedule.run_pending()
        time.sleep(1)
