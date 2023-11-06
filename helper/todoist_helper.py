import os

import requests
from quarter_lib.logging import setup_logging

from helper.caching import ttl_cache

logger = setup_logging(__file__)

CATEGORIES_URL = os.getenv("categories_url")
RENAMING_URL = os.getenv("renaming_url")
THIS_WEEK_PROJECT_ID = os.getenv("todoist_project_id_this_week")


@ttl_cache(ttl=60 * 60)
def get_sections_from_web():
    logger.info("getting sections from web")
    response = requests.get(CATEGORIES_URL, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
    data = response.json()
    unknown_section = data.pop(len(data) - 1)
    data.reverse()
    return data, unknown_section


@ttl_cache(ttl=60 * 60)
def get_renaming_from_web():
    logger.info("getting renaming from web")
    response = requests.get(RENAMING_URL, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
    return response.json()


def rename_item(text):
    renaming_mapping = get_renaming_from_web()
    for key, value in renaming_mapping.items():
        for real_value in value:
            if real_value.lower() in text.lower():
                return key
    return text


def get_section(item, todoist_api):
    section_list, unknown_section = get_sections_from_web()
    for section_object in section_list:
        for product in section_object['items']:
            if product.lower() in item.lower():
                print(product)
                return section_object['id'], section_object['name']
    todoist_api.add_task(content="item not found: " + item, project_id="2244725398", description=CATEGORIES_URL)
    return unknown_section['id'], unknown_section['name']
