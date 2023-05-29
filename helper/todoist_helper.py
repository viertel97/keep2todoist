import json
import os

import requests
from quarter_lib.logging import setup_logging

from helper.caching import ttl_cache

logger = setup_logging(__file__)

CATEGORIES_URL = os.getenv("categories_url")


@ttl_cache(ttl=60 * 60 * 24)
def get_sections_from_web():
    response = requests.get(CATEGORIES_URL, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
    data = response.json()
    return data


def get_section(item):
    section_list = get_sections_from_web()
    for section_object in section_list:
        for product in section_object['items']:
            if product.lower() in item.lower():
                print(product)
                return section_object['id'], section_object['name']
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "not_found.log")
    with open(path, "a") as file:
        file.write("{item}\n".format(item=item))
    logger.info("no section found for item: " + item)
    return None, None
