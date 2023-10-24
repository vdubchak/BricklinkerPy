import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes

from rebrickable_client import make_search_request
from response_formatters import formatInfoResponse, formatPriceResponse, formatItemsSoldResponse, \
    formatItemsForSaleResponse, search_response_formatter
from request_matcher import resolve_price, resolve_info, resolve_sold

BOT_NAME = os.environ['BOT_NAME']
HELP_TEXT = "Welcome to Bricklink telegram bot.\n" \
            "Try typing in set number or minifigure number to get more info on it.\n" \
            "Example \"75100\" or \"sw0547\"" \
            "Alternatively or if bot is in group chat you can use commands like " \
            "/info 42069 or /price col404\n" \
            "You can also use /search command to find set numbers (currently not working for minifigures)\n" \
            "Example: /search hotel"
BL_URL = "https://www.bricklink.com/v2/catalog/catalogitem.page?{}={}"


async def helpHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Processing start command")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=HELP_TEXT
    )


async def searchHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = None
    reply_markup = None
    request_str = None
    logging.debug("Processing search command")
    if context.args and context.args[0] and len(context.args[0]) > 0:
        request_str = " "
        request_str = request_str.join(context.args)
    elif len(update.message.text.replace('/search', '')) > 0:
        request_str = update.message.text.replace('/search', '')
    re_response = make_search_request(request_str)
    if re_response:
        target = "more" if (update.effective_chat.type == Chat.SUPERGROUP
                            or update.effective_chat.type == Chat.GROUP) else "INFO"
        response_keyboard = search_response_formatter(re_response, target)
        if len(response_keyboard) > 0:
            reply_markup = InlineKeyboardMarkup(response_keyboard)
            response = "Search result for '" + request_str + "'"
        else:
            response = "Nothing found for: " + request_str
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response,
        reply_markup=reply_markup
    )


async def startHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Processing start command")
    if context.args and context.args[0] and len(context.args[0]) > 0:
        reply_markup = None
        try:
            response = resolve_info(context.args[0])
            if response:
                itemNumber = response['no']
                reply_markup = InlineKeyboardMarkup(resolveKeyboard(update, item_number=itemNumber, item_type=response["type"]))
                response = formatInfoResponse(response)
        except Exception as e:
            logging.debug(e)
            response = e
        if response is None or len(response) == 0:
            response = "Can't find anything for " + context.args[0]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=HELP_TEXT
        )


async def infoCommandHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Processing info request")
    reply_markup = None
    response = None
    try:
        query = update.message.text.lower()
        response = resolve_info(query)
        if response:
            itemNumber = response['no']
            reply_markup = InlineKeyboardMarkup(resolveKeyboard(update, item_number=itemNumber, item_type=response["type"]))
            response = formatInfoResponse(response)
    except Exception as e:
        logging.debug(e)
    if response is None or len(response) == 0:
        await searchHandler(update, context)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)


async def infoMessageHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Processing info request")
    reply_markup = None
    response = None
    try:
        query = update.message.text.lower()
        response = resolve_info(query)
        if response and response['no']:
            itemNumber = response['no']
            reply_markup = InlineKeyboardMarkup(resolveKeyboard(update, item_number=itemNumber, item_type=response["type"]))
            response = formatInfoResponse(response)
    except Exception as e:
        logging.debug(e)
    if (response is None or len(response) == 0) \
            and (update.effective_chat.type != Chat.SUPERGROUP and update.effective_chat.type != Chat.GROUP):
        await searchHandler(update, context)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)


async def infoButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logging.debug("Query data: " + query.data)
    reply_markup = None
    response = None
    try:
        itemNumber = query.data.replace("INFO ", "")
        response = resolve_info(itemNumber)
        if response:
            reply_markup = InlineKeyboardMarkup(resolveKeyboard(update, item_number=itemNumber, item_type=response["type"]))
            response = formatInfoResponse(response)
    except Exception as e:
        logging.debug(e)
    if response is None or len(response) == 0:
        response = "Can't find anything for " + context.args[0]
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)


async def priceCommandHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Processing info request")
    try:
        query = update.message.text.lower()
        response = resolve_price(query)
        if response:
            logging.debug("Response from bl: " + str(response))
            response = formatPriceResponse(response)
    except Exception as e:
        logging.debug(e)
        response = e
    if response is None or len(response) == 0:
        response = "Cannot find data for " + update.message.text

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def groupButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    logging.debug("Query data: " + query.data)
    item = query.data.replace("more ", "")
    await query.answer(url="https://t.me/" + BOT_NAME + "?start=" + item)


async def priceButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    logging.debug("Query data: " + query.data)
    await query.answer()
    logging.debug("Processing price button request")
    try:
        response = resolve_price(query.data)
        if response:
            logging.debug("Response from bl: " + str(response))
            response = formatPriceResponse(response)

    except Exception as e:
        logging.error(e)
        response = e
    if response is None or response.__sizeof__() == 0:
        response = "Cannot find data for " + query.data

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def soldButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    response = None
    logging.debug("Query data: " + query.data)
    await query.answer()
    logging.debug("Processing sold button request")
    try:
        response = resolve_sold(query.data)
        if response:
            response = formatItemsSoldResponse(response)
    except Exception as e:
        logging.error(e)
        # response = str(e)
    if response is None or len(response) == 0:
        response = "Cannot find data for " + query.data

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def stockButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    response = None
    logging.debug("Query data: " + query.data)
    await query.answer()
    logging.debug("Processing stock button request")
    try:
        response = resolve_sold(query.data)
        response = formatItemsForSaleResponse(response)
    except Exception as e:
        logging.error(e)
        # response = str(e)
    if response is None or len(response) == 0:
        response = "Cannot find data for " + query.data

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def defButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer(text="Not implemented yet")


def resolveKeyboard(update: Update, item_number, item_type):
    if update.effective_chat.type == Chat.SUPERGROUP or update.effective_chat.type == Chat.GROUP:
        keyboard = [
            [InlineKeyboardButton("More info on " + item_number, callback_data="more " + item_number)],
            [InlineKeyboardButton("View on BL", url=BL_URL.format(item_type[0], item_number))]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("Prices for new " + item_number, callback_data="PRICE NEW " + item_number),
             InlineKeyboardButton("Prices for used " + item_number, callback_data="PRICE USED " + item_number)],
            [InlineKeyboardButton("Recently sold new", callback_data="SOLD NEW " + item_number),
             InlineKeyboardButton("Recently sold used", callback_data="SOLD USED " + item_number)],
            [InlineKeyboardButton("For sale new", callback_data="STOCK NEW " + item_number),
             InlineKeyboardButton("For sale used", callback_data="STOCK USED " + item_number)],
            [InlineKeyboardButton("View on BL", url=BL_URL.format(item_type[0], item_number))]
        ]
    return keyboard
