import json
import os

from quarter_lib.logging import setup_logging

logger = setup_logging(__file__)


def get_sections_from_file():
    with open(os.path.join(os.getcwd(), 'data', "categories.json"), encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data


def get_section(item):
    section_list = get_sections_from_file()
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
