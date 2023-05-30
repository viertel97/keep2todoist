import os

import requests
from quarter_lib.logging import setup_logging

from helper.caching import ttl_cache

logger = setup_logging(__file__)

CATEGORIES_URL = os.getenv("categories_url")


@ttl_cache(ttl=60 * 60)
def get_sections_from_web():
    logger.info("getting sections from web")
    response = requests.get(CATEGORIES_URL, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
    data = response.json()
    unknown_section = data.pop(len(data) - 1)
    return data, unknown_section


def get_section(item):
    section_list, unknown_section = get_sections_from_web()
    for section_object in section_list:
        for product in section_object['items']:
            if product.lower() in item.lower():
                print(product)
                return section_object['id'], section_object['name']
    return unknown_section['id'], unknown_section['name']
