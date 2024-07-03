import logging
import os
import requests

REBRICKABLE_KEY = os.environ['REBRICKABLE_KEY']
BASE_URL = 'https://rebrickable.com/api/v3'


def set_search_request(search_str: str):
    url = BASE_URL + "/lego/sets/"
    headers = {
        "Authorization": "key " + REBRICKABLE_KEY
    }
    params = {
        "search": search_str
    }
    response = requests.get(url=url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error("[RebrickableClient] Rebrickable returned error code " + str(response.status_code))
        logging.error(response.text)

