import itertools
import re

from telegram import InlineKeyboardButton

from request_matcher import SET_EXPR

ASCII_LOWER = "abcdefghijklmnopqrstuvwxyz0123456789"
OFFSET = ord("🇦") - ord("A")


def formatInfoResponse(message: dict) -> str:
    return u"\U0001F170\uFE0F Name: " + unescape_html(message["name"]) + "\n" \
                                                                         "\U0001F5BC Image: " + message[
               "image_url"] + "\n" \
                              "\U0001F4C6 Year released: " + str(message["year_released"]) + "\n" \
                                                                                             "\u2693\uFE0F Weight: " + str(
        message["weight"]) + "g\n" \
                             "\U0001F4D0 Dimensions: " + str(message["dim_x"]) + "x" + str(
        message["dim_y"]) + "x" + str(message["dim_z"])


def formatPriceResponse(message: dict) -> str:
    return u"Price for " + message["item"]["no"] + " (" + message["new_or_used"] + ")" + "\n" \
        "\U0001F4C9 Minimal price: " + message["min_price"] + unescape_html(message["currency_code"]) + "\n" \
        "\U0001F4C6 Maximal price: " + message["max_price"] + unescape_html(message["currency_code"]) + "\n" \
        "\U0001F4CA Average price: " + message["avg_price"] + unescape_html(message["currency_code"]) + "\n" \
        "\U0001F522 Quantity for sale: " + str(message["total_quantity"])


def formatItemsSoldResponse(message: dict) -> str:
    if len(message["price_detail"]) > 0:
        res = u"Recently sold " + message["item"]["no"] + " (" + message["new_or_used"] + "):"
        for item in itertools.islice(message["price_detail"], 20):
            res += "\nSeller: " + resolve_flag_emoji(item["seller_country_code"]) + \
                   ", Buyer: " + resolve_flag_emoji(item["buyer_country_code"]) + \
                   ", Price: " + item["unit_price"] + " " + unescape_html(message["currency_code"]) + \
                   ", Quantity: " + str(item["quantity"])
    else:
        res = "Seems like no " + message["item"]["no"] + " were sold recently \U0001F914"
    return res


def formatItemsForSaleResponse(message: dict) -> str:
    if len(message["price_detail"]) > 0:
        res = message["item"]["no"] + " for sale (" + message["new_or_used"] + "):"
        for item in itertools.islice(message["price_detail"], 20):
            res += u"\n\U0001F4B5 Price: " + item["unit_price"] + unescape_html(message["currency_code"]) +\
                   ", \U0001F522 Quantity: " + str(item["quantity"]) + \
                   ", \U0001F69A Ships to " + resolve_flag_emoji("ua") + ": " + \
                   (u"\u2705" if item["shipping_available"] else u"\u274C")
    else:
        res = "Seems like " + message["item"]["no"] + " is out of stock \U0001F914"
    return res


def unescape_html(s: str):
    s = s.replace("&#40;", "(")
    s = s.replace("&#41;", ")")
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&#39;", "'")
    # this has to be last:
    s = s.replace("&amp;", "&")
    return s


def resolve_flag_emoji(countrycode: str) -> str:
    if countrycode == "UK":
        return u"\U0001F1EC\U0001F1E7"
    elif countrycode == "RU":
        return u"\U0001F4A9"
    code = [c for c in countrycode.lower() if c in ASCII_LOWER]
    return "".join([chr(ord(c.upper()) + OFFSET) for c in code])


def set_search_response_formatter(message: dict, target: str):
    keyboard = []
    sets = list(filter(lambda x: re.search(SET_EXPR, x["set_num"]), message["results"]))
    if len(sets) > 0:
        sets = sorted(sets, key=lambda k: k['year'], reverse=True)
        for item in itertools.islice(sets, 20):
            keyboard.append([
                InlineKeyboardButton(
                    item["set_num"] + " - " + unescape_html(item["name"]) + " (" + str(item["year"]) + ")",
                    callback_data=target + " " + item["set_num"])])
    return keyboard


def fig_search_response_formatter(minifigs: dict, target: str):
    keyboard = []
    limit = 0
    if len(minifigs) > 0:
        for code, name in minifigs.items():
            if limit == 20:
                break
            limit += 1
            keyboard.append([
                InlineKeyboardButton(
                    code + " - " + unescape_html(name),
                    callback_data=target + " " + code)])
    return keyboard
