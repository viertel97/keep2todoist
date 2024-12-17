import requests
from quarter_lib.akeyless import get_secrets
from quarter_lib.logging import setup_logging

logger = setup_logging(__file__)

TANDOOR_API_KEY = get_secrets(["tandoor/api_key"])


BASE_URL = "https://recipes.viertel-it.de/api"


def add_to_shopping_list(item):
	response = requests.post(
		BASE_URL + "/shopping-list-entry/",
		headers={
			"Content-Type": "application/json",
			"Authorization": f"Bearer {TANDOOR_API_KEY}",
		},
		json={"food": {"name": item}, "amount": 0},
	)
	if response.status_code != 201:
		logger.error(response.content)
		raise Exception(f"Error adding item '{item}' to shopping list")
