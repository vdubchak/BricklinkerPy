import re
import logging

from bricklink_client import ApiClient

SET_EXPR = "\\b[\\d]{2,5}(?:-\\d)?\\b"
MINIFIG_EXPR = "\\b[a-z]{1,3}[\\d]{2,4}\\b"
USED_EXPR = "\\bUSED\\b"
NEW_EXPR = "\\bNEW\\b"
STOCK_EXPR = "\\bSTOCK\\b"
SOLD_EXPR = "\\bSOLD\\b"
client = ApiClient()


class InfoRequest:
    def __init__(self, item_type, item_number, state="N", mode="stock"):
        self.itemType = item_type
        self.itemNumber = item_number
        self.state = state
        self.mode = mode


def resolve_request(message) -> InfoRequest:
    itemNum = matchRegexp(message, SET_EXPR)
    itemType = None
    if itemNum:
        itemType = "SET"
        if itemNum.find("-") == -1:
            itemNum = itemNum + "-1"
        logging.info('[RequestMatchers] Requesting info for set ' + itemNum)
    else:
        itemNum = matchRegexp(message, MINIFIG_EXPR)
        if itemNum:
            itemType = "MINIFIG"
            logging.info('[RequestMatchers] Requesting info for minifigure ' + itemNum)
        elif message and str(message).startswith('/'):
            logging.error('[RequestMatchers] Could not resolve request: ' + message)
            raise Exception('Could not match request: ' + message)
    request = InfoRequest(item_type=itemType, item_number=itemNum)
    state = matchRegexp(message, NEW_EXPR)
    if not state:
        state = matchRegexp(message, USED_EXPR)
    if state:
        if state == "NEW":
            state = "N"
        elif state == "USED":
            state = "U"
        logging.debug("[RequestMatchers] State resolved = " + state)
        request.state = state
    mode = matchRegexp(message, STOCK_EXPR)
    if not mode:
        mode = matchRegexp(message, SOLD_EXPR)
    if mode:
        logging.debug("[RequestMatchers] Mode resolved = " + mode)
        request.mode = mode
    return request


def resolve_info(message):
    info_request = resolve_request(message)
    url = "items/" + info_request.itemType + "/" + info_request.itemNumber
    response = client.get(url=url)
    return response


def resolve_price(message):
    info_request = resolve_request(message)
    url = "items/" + info_request.itemType + "/" + info_request.itemNumber + "/price"
    logging.debug("[RequestMatchers] Requesting URL: " + url)
    response = client.get(url=url, params={
        "region": "europe",
        "guide_type": info_request.mode,
        "new_or_used": info_request.state
    })
    return response


def resolve_sold(message):
    info_request = resolve_request(message)
    url = "items/" + info_request.itemType + "/" + info_request.itemNumber + "/price"
    response = client.get(url=url, params={
        "region": "europe",
        "guide_type": info_request.mode,
        "new_or_used": info_request.state
    })
    return response


def matchRegexp(message, expr):
    match = re.search(expr, message)
    if match:
        res = match.group()
        return res