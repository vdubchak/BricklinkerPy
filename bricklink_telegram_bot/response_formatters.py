import itertools

ASCII_LOWER = "abcdefghijklmnopqrstuvwxyz0123456789"
OFFSET = ord("🇦") - ord("A")


def formatInfoResponse(message: dict) -> str:
    return u"\U0001F170\uFE0F Name: " + unescape_html(message["name"]) + "\n"\
        "\U0001F5BC Image: " + message["image_url"] + "\n"\
        "\U0001F4C6 Year released: " + str(message["year_released"]) + "\n" \
        "\u2693\uFE0F Weight: " + str(message["weight"]) + "g\n" \
        "\U0001F4D0 Dimensions: " + str(message["dim_x"]) + "x" + str(message["dim_y"]) + "x" + str(message["dim_z"])


def formatPriceResponse(message: dict) -> str:
    return u"\U0001F4B1 Currency: " + unescape_html(message["currency_code"]) + "\n"\
        "\U0001F4C9 Minimal price: " + message["min_price"] + "\n"\
        "\U0001F4C6 Maximal price: " + message["max_price"] + "\n" \
        "\U0001F4CA Average price: " + message["avg_price"] + "\n" \
        "\U0001F522 Quantity for sale: " + str(message["total_quantity"])


def formatItemsSoldResponse(message: dict) -> str:
    res = u"\U0001F4B1 Currency: " + unescape_html(message["currency_code"]) + resolve_flag_emoji("ua") + ""
    for item in itertools.islice(message["price_detail"], 20):
        res += "\nSeller: " + resolve_flag_emoji(item["seller_country_code"]) + \
            ", Buyer: " + resolve_flag_emoji(item["buyer_country_code"]) + \
            ", Price: " + item["unit_price"] + ", Quantity: " + str(item["quantity"])
    return res


def formatItemsForSaleResponse(message: dict) -> str:
    res = u"\U0001F4B1 Currency: " + unescape_html(message["currency_code"]) + resolve_flag_emoji("ua") + ""
    for item in itertools.islice(message["price_detail"], 20):
        res += u"\n\U0001F4B5 Price: " + item["unit_price"] + ", \U0001F522 Quantity: " + str(item["quantity"]) + \
               ", \U0001F69A Ships to " + resolve_flag_emoji("ua") + ": " + \
               (u"\u2705" if item["shipping_available"] else u"\u274C")
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
