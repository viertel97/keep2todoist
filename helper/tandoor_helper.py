import requests
from quarter_lib.akeyless import get_secrets
from quarter_lib.logging import setup_logging

logger = setup_logging(__file__)

TANDOOR_API_KEY = get_secrets(["tandoor/api_key"])


BASE_URL = "https://recipes.viertel-it.de/api"
HEADERS = {
			"Content-Type": "application/json",
			"Authorization": f"Bearer {TANDOOR_API_KEY}",
		}

def add_to_shopping_list(item):
	create_food_response = requests.post(
		BASE_URL + "/api/food/",
		headers=HEADERS,
		json={"name": item},
	)

	create_shopping_list_entry_response = requests.post(
		BASE_URL + "/shopping-list-entry/",
		headers=HEADERS,
		json={"food": {"name": item}, "amount": 1},
	)
	if create_shopping_list_entry_response.status_code != 201:
		logger.error(create_shopping_list_entry_response.content)
		raise Exception(f"Error adding item '{item}' to shopping list")
