import re

from bricklink_client import ApiClient

SET_EXPR = "\\b[\\d]{2,5}(?:-\\d)?\\b"
MINIFIG_EXPR = "\\b[a-z]{1,3}[\\d]{2,4}\\b"
USED_EXPR = "\\bUSED\\b"
NEW_EXPR = "\\bUSED\\b"
client = ApiClient()


class InfoRequest:
    def __init__(self, item_type, item_number):
        self.itemType = item_type
        self.itemNumber = item_number


def resolve_request(message) -> InfoRequest:
    setNum = matchSet(message)
    if setNum:
        print('Requesting info for set ' + setNum)
        return InfoRequest("SET", setNum)
    minifigNum = matchMinifig(message)
    if minifigNum:
        print('Requesting info for minifigure ' + minifigNum)
        return InfoRequest("MINIFIG", minifigNum)
    if message and str(message).startswith('/'):
        print('Could not resolve request: ' + message)
        raise Exception('Could not match request: ' + message)


def resolve_info(message):
    info_request = resolve_request(message)
    url = "items/" + info_request.itemType + "/" + info_request.itemNumber
    response = client.get(url=url)
    return response


def resolve_price(message):
    info_request = resolve_request(message)
    url = "items/" + info_request.itemType + "/" + info_request.itemNumber + "/price"
    response = client.get(url=url, params={
        "region": "europe",
        "guide_type": "stock",
        "new_or_used": "N"
    })
    return response


def matchSet(message):
    match = re.search(SET_EXPR, message)
    if match:
        set_num = match.group()
        return set_num if set_num.endswith('-1') else set_num + '-1'


def matchMinifig(message):
    match = re.search(MINIFIG_EXPR, message)
    if match:
        minifig_num = match.group()
        return minifig_num
