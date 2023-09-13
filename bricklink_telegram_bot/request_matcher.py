import re

SET_EXPR = "\\b[\\d]{2,5}(?:-\\d)?\\b"
MINIFIG_EXPR = "\\b[a-z]{1,3}[\\d]{2,4}\\b"


def resolve_request(message):
    match = re.search(SET_EXPR, message)
    if match:
        setNum = match.group()
        print('Requesting info for set ' + setNum)
        return "items/SET/" + setNum if setNum.endswith('-1') else "items/SET/" + setNum + '-1'
    match = re.search(MINIFIG_EXPR, message)
    if match:
        minifigNum = match.group()
        print('Requesting info for minifigure ' + minifigNum)
        return "items/MINIFIG/" + minifigNum
    if message and str(message).startswith('/'):
        print('Could not resolve request: ' + message)
        raise Exception('Could not match request: ' + message)
