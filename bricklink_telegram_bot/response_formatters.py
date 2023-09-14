ASCII_LOWER = "abcdefghijklmnopqrstuvwxyz0123456789"
OFFSET = ord("🇦") - ord("A")


def formatInfoResponse(message: dict) -> str:
    return u"\U0001F170\uFE0F Name: " + unescape_html(message["name"]) + "\n"\
        "\U0001F5BC Image: " + message["image_url"] + "\n"\
        "\U0001F4C6 Year released: " + str(message["year_released"]) + "\n" \
        "\u2693\uFE0F Weight: " + str(message["weight"]) + "g\n" \
        "\U0001F4D0 Dimensions: " + str(message["dim_x"]) + "x" + str(message["dim_y"]) + "x" + str(message["dim_z"])


def formatPriceResponse(message: dict) -> str:
    return u"\U0001F4B1 Currency: " + unescape_html(message["currency_code"]) + resolve_flag_emoji("ua") + "\n"\
        "\U0001F4C9 Minimal price: " + message["min_price"] + "\n"\
        "\U0001F4C6 Maximal price: " + message["max_price"] + "\n" \
        "\U0001F4CA Average price: " + message["avg_price"] + "\n" \
        "\U0001F522 Quantity for sale: " + str(message["total_quantity"])


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
    code = [c for c in countrycode.lower() if c in ASCII_LOWER]
    return "".join([chr(ord(c.upper()) + OFFSET) for c in code])
