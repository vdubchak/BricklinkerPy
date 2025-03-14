import re
import logging

from bricklink_client import ApiClient

SET_EXPR = "\\b[\\d]{2,7}(?:-\\d)?\\b"
MINIFIG_EXPR = "\\b[a-z]{1,3}[\\d]{2,4}\\b"
USED_EXPR = "\\bUSED\\b"
NEW_EXPR = "\\bNEW\\b"
STOCK_EXPR = "\\bSTOCK\\b"
SOLD_EXPR = "\\bSOLD\\b"
client = ApiClient()


class InfoRequest:
    def __init__(self, item_type, item_number, state="N", mode="stock", currency_code="EUR"):
        self.itemType = item_type
        self.itemNumber = item_number
        self.state = state
        self.mode = mode
        self.currency_code = currency_code


def resolve_request(message) -> InfoRequest:
    itemNum = match_regexp(message, SET_EXPR)
    itemType = None
    if itemNum:
        itemType = "SET"
        if itemNum.find("-") == -1:
            itemNum = itemNum + "-1"
        logging.info('[RequestMatchers] Requesting info for set ' + itemNum)
    else:
        itemNum = match_regexp(message, MINIFIG_EXPR)
        if itemNum:
            itemType = "MINIFIG"
            logging.info('[RequestMatchers] Requesting info for minifigure ' + itemNum)
        elif message and str(message).startswith('/'):
            logging.error('[RequestMatchers] Could not resolve request: ' + message)
            raise Exception('Could not match request: ' + message)
    request = InfoRequest(item_type=itemType, item_number=itemNum)
    state = match_regexp(message, NEW_EXPR)
    if not state:
        state = match_regexp(message, USED_EXPR)
    if state:
        if state == "NEW":
            state = "N"
        elif state == "USED":
            state = "U"
        logging.debug("[RequestMatchers] State resolved = " + state)
        request.state = state
    mode = match_regexp(message, STOCK_EXPR)
    if not mode:
        mode = match_regexp(message, SOLD_EXPR)
    if mode:
        logging.debug("[RequestMatchers] Mode resolved = " + mode)
        request.mode = mode
    return request


def resolve_info(message) -> dict:
    info_request = resolve_request(message)
    url = "items/" + info_request.itemType + "/" + info_request.itemNumber
    response = client.get(url=url)
    return response


def resolve_subsets(message) -> []:
    info_request = resolve_request(message)
    url = "items/" + info_request.itemType + "/" + info_request.itemNumber + "/subsets"
    response = client.get(url=url)
    return response


def resolve_supersets(message) -> []:
    info_request = resolve_request(message)
    url = "items/" + info_request.itemType + "/" + info_request.itemNumber + "/supersets"
    response = client.get(url=url)
    return response



def resolve_price(message):
    info_request = resolve_request(message)
    url = "items/" + info_request.itemType + "/" + info_request.itemNumber + "/price"
    logging.debug("[RequestMatchers] Requesting URL: " + url)
    response = client.get(url=url, params={
        "guide_type": info_request.mode,
        "new_or_used": info_request.state,
        "currency_code": info_request.currency_code
    })
    return response


def resolve_availability(item_type, item_num):
    new_count = resolve_availability_by_cond_count(item_type, item_num, "N")
    used_count = resolve_availability_by_cond_count(item_type, item_num, "U")
    return new_count + used_count > 0


def resolve_availability_by_cond_count(itemType, itemNum, condition):
    url = "items/" + itemType + "/" + itemNum + "/price"
    logging.debug("[RequestMatchers] Requesting URL: " + url)
    response = client.get(url=url, params={
        "country_code": "UA",
        "guide_type": "STOCK",
        "new_or_used": condition
    })
    return len(response["price_detail"])


def resolve_sold(message):
    info_request = resolve_request(message)
    url = "items/" + info_request.itemType + "/" + info_request.itemNumber + "/price"
    response = client.get(url=url, params={
        "guide_type": info_request.mode,
        "new_or_used": info_request.state,
        "currency_code": info_request.currency_code
    })
    return response


def match_regexp(message, expr):
    match = re.search(expr, message)
    if match:
        res = match.group()
        return res
