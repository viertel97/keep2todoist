import os

import requests
from quarter_lib.logging import setup_logging
from quarter_lib.akeyless import get_secrets
from helper.caching import ttl_cache

logger = setup_logging(__file__)

MASTER_KEY, CATEGORIES_BIN, RENAIMING_BIN = get_secrets(
    ["jsonbin/masterkey", "jsonbin/categories-bin", "jsonbin/renaiming-bin"])


BASE_URL = "https://api.jsonbin.io/v3"
THIS_WEEK_PROJECT_ID = os.getenv("todoist_project_id_this_week")

CATEGORIES_URL = f"{BASE_URL}/b/{CATEGORIES_BIN}/latest"
RENAMING_URL = f"{BASE_URL}/b/{RENAIMING_BIN}/latest"

section_data = []
renaming_data = []

@ttl_cache(ttl=60 * 60)
def get_sections_from_web():
    global section_data
    logger.info("getting sections from web")
    try:
        response = requests.get(CATEGORIES_URL, headers={'User-Agent': 'Mozilla/5.0', 'X-Master-Key': MASTER_KEY}, verify=False, timeout=10)
        section_data = response.json()["record"]
    except Exception as e:
        logger.error(e)
    temp_data = section_data.copy()
    temp_data.reverse()
    unknown_section = temp_data.pop(len(temp_data) - 1)
    return temp_data, unknown_section


@ttl_cache(ttl=60 * 60)
def get_renaming_from_web():
    global renaming_data
    logger.info("getting renaming from web")
    try:
        response = requests.get(RENAMING_URL, headers={'User-Agent': 'Mozilla/5.0', 'X-Master-Key': MASTER_KEY}, verify=False, timeout=10)
        renaming_data = response.json()["record"]
    except Exception as e:
        logger.error(e)
    return renaming_data


def rename_item(text):
    renaming_mapping = get_renaming_from_web()
    for key, value in renaming_mapping.items():
        for real_value in value:
            if real_value.lower() in text.lower():
                return key
    return text


def get_section(item, todoist_api):
    section_list, unknown_section = get_sections_from_web()
    for section_object in section_list: # direct matching
        for product in section_object['items']:
            if product.lower() == item.lower():
                logger.info("direct matching: " + product)
                return section_object['section_id'], section_object['name']
    for section_object in section_list: # partly matching
        for product in section_object['items']:
            if product.lower() in item.lower():
                logger.info("partly matching: " + product)
                return section_object['section_id'], section_object['name']
    todoist_api.add_task(content="item not found: " + item, project_id="2244725398", description=CATEGORIES_URL)
    return unknown_section['section_id'], unknown_section['name']
