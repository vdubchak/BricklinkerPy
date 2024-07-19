import itertools
import logging
import re

from telegram import InlineKeyboardButton

from request_matcher import SET_EXPR, resolve_availability

ASCII_LOWER = "abcdefghijklmnopqrstuvwxyz0123456789"
OFFSET = ord("🇦") - ord("A")


def formatInfoResponse(message_dict: dict) -> str:
    logging.debug("[Response formatter] format info response for: " + str(message_dict))
    raw = u"\U0001F170\uFE0F Name: " + unescape_html(message_dict["name"]) + "\n" \
                                                                        "\U0001F5BC Image: " + message_dict[
              "image_url"] + "\n" \
                             "\U0001F4C6 Year released: " + str(message_dict["year_released"]) + "\n" \
                                                                                            "\u2693\uFE0F Weight: " + str(
        message_dict["weight"]) + "g\n" \
        # "\U0001F4D0 Dimensions: " + str(message["dim_x"]) + "x" + str(message["dim_y"]) + "x" + str(message[
    # "dim_z"]) + "\n"
    return escape(raw) + resolve_availability_section(message_dict)


def formatPriceResponse(message: dict) -> str:
    res = u"Price for " + message["item"]["no"] + " (" + message[
        "new_or_used"] + ")" + "\n" + "\U0001F4C9 Minimal price: " + format_price(message["min_price"]) + unescape_html(
        message["currency_code"]) + "\n" + u"\U0001F4C8 Maximal price: " + format_price(
        message["max_price"]) + unescape_html(
        message["currency_code"]) + "\n" + "\U0001F4CA Average price: " + format_price(
        message["avg_price"]) + unescape_html(message["currency_code"]) + "\n" + "\U0001F522 Quantity for sale: " + str(
        message["total_quantity"])
    return escape(res)


def formatItemsSoldResponse(message: dict) -> str:
    if len(message["price_detail"]) > 0:
        res = u"Recently sold " + message["item"]["no"] + " (" + message["new_or_used"] + "):"
        for item in itertools.islice(message["price_detail"], 20):
            res += "\nSeller: " + resolve_flag_emoji(item["seller_country_code"]) + \
                   ", Buyer: " + resolve_flag_emoji(item["buyer_country_code"]) + \
                   ", Price: " + format_price(item["unit_price"]) + " " + unescape_html(message["currency_code"]) + \
                   ", Quantity: " + str(item["quantity"])
    else:
        res = "Seems like no " + message["item"]["no"] + " were sold recently \U0001F914"
    return escape(res)


def formatItemsForSaleResponse(message: dict) -> str:
    if len(message["price_detail"]) > 0:
        res = message["item"]["no"] + " for sale (" + message["new_or_used"] + "):"
        for item in itertools.islice(message["price_detail"], 20):
            res += u"\n\U0001F4B5 Price: " + format_price(item["unit_price"]) + unescape_html(
                message["currency_code"]) + \
                   ", \U0001F522 Quantity: " + str(item["quantity"]) + \
                   ", \U0001F69A Ships to " + resolve_flag_emoji("ua") + ": " + \
                   (u"\u2705" if item["shipping_available"] else u"\u274C")
    else:
        res = "Seems like " + message["item"]["no"] + " is out of stock \U0001F914"
    return escape(res)


def unescape_html(s: str) -> str:
    s = s.replace("&#40;", "(")
    s = s.replace("&#41;", ")")
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&#39;", "'")
    # this has to be last:
    s = s.replace("&amp;", "&")
    return s


def escape(s: str) -> str:
    s = s.replace("-", "\\-")
    s = s.replace("!", "\\!")
    s = s.replace("[", "\\[")
    s = s.replace("]", "\\]")
    s = s.replace("(", "\\(")
    s = s.replace(")", "\\)")
    s = s.replace(".", "\\.")
    s = s.replace("_", "\\_")
    s = s.replace("*", "\\*")
    s = s.replace("`", "\\`")
    s = s.replace("&", "\\&")
    s = s.replace("<", "\\<")
    s = s.replace(">", "\\>")
    s = s.replace("#", "\\#")
    return s


def resolve_availability_section(message):
    available = resolve_availability(message['type'], message["no"])
    if available:
        item_type = 'M' if message['type'] == 'MINIFIG' else 'S'
        return u"\u2705 Available in " + resolve_flag_emoji("ua") + ": " + \
            u"\U0001F6D2 [Buy now\\!]" + \
            "(https://store.bricklink.com/v2/catalog/catalogitem.page?" + item_type + "=" + message["no"] + \
            "#T=S&O={%22loc%22:%22UA%22})"
    else:
        return u"\u274C Not available in " + resolve_flag_emoji("ua")


def resolve_flag_emoji(countrycode: str) -> str:
    if countrycode == "UK":
        return u"\U0001F1EC\U0001F1E7"
    elif countrycode == "RU":
        return u"\U0001F4A9"
    code = [c for c in countrycode.lower() if c in ASCII_LOWER]
    return "".join([chr(ord(c.upper()) + OFFSET) for c in code])


def search_response_formatter(query_text: str):
    keyboard = [[
        InlineKeyboardButton(
            "Search Set '" + query_text + "'",
            callback_data="SETSEARCH" + " " + query_text)], [
        InlineKeyboardButton(
            "Search Minifigure '" + query_text + "'",
            callback_data="MINIFIGSEARCH" + " " + query_text)]]
    return keyboard


def subset_response_formatter(subset_response, target: str):
    minifigures = []
    keyboard = []
    for entry in subset_response:
        item = entry["entries"][0]
        if item["item"]["type"] == "MINIFIG":
            minifigures.append(item)
            logging.debug("[Response formatter] subset added: " + str(item))

    if len(minifigures) > 0:
        for item in itertools.islice(minifigures, 20):
            keyboard.append([
                InlineKeyboardButton(
                    item["item"]["no"] + " - " + unescape_html(item["item"]["name"]) + " (" + str(item["quantity"]) + ")",
                    callback_data=target + " " + item["item"]["no"])])
    return keyboard


def superset_response_formatter(subset_response, target: str):
    sets = []
    keyboard = []
    for item in subset_response[0]["entries"]:
        if item["item"]["type"] == "SET":
            sets.append(item)
            logging.debug("[Response formatter] subset added: " + str(item))

    if len(sets) > 0:
        for item in itertools.islice(sets, 20):
            keyboard.append([
                InlineKeyboardButton(
                    item["item"]["no"] + " - " + unescape_html(item["item"]["name"]) + " (" + str(item["quantity"]) + ")",
                    callback_data=target + " " + item["item"]["no"])])
    return keyboard


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
        for code, name in reversed(minifigs.items()):
            if limit == 20:
                break
            limit += 1
            keyboard.append([
                InlineKeyboardButton(
                    code + " - " + unescape_html(name),
                    callback_data=target + " " + code)])
    return keyboard


def format_price(price_str: str):
    return str(round(float(price_str), 2))
