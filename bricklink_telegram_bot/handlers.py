import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes

from s3_search_client import minifigure_search_request
from rebrickable_client import set_search_request
from response_formatters import formatInfoResponse, formatPriceResponse, formatItemsSoldResponse, \
    formatItemsForSaleResponse, set_search_response_formatter, fig_search_response_formatter, search_response_formatter
from request_matcher import resolve_price, resolve_info, resolve_sold

BOT_NAME = os.environ['BOT_NAME']
HELP_TEXT = "Try typing in set number, name or minifigure number to get more info on it.\n" \
            "Example \"75100-1\", \"4950\", \"sw0547\" or \"hotel\"" \
            "Alternatively or if bot is in group chat you can use commands like " \
            "/info 42069 or /price col404\n" \
            "You can also use /search command to find set numbers (currently not working for minifigures)\n" \
            "Example: /search hotel"
START_TEXT = "What are you looking for? Try typing set/minifigure number or name, for example 4950, " \
             "sw0547 or helicopter."
BL_URL = "https://www.bricklink.com/v2/catalog/catalogitem.page?{}={}"


async def helpHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Processing start command")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=HELP_TEXT
    )

async def searchDialogHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request_str = None
    logging.debug("Processing search request")
    if context.args and context.args[0] and len(context.args[0]) > 0:
        request_str = " "
        request_str = request_str.join(context.args)
    elif len(update.message.text) > 0:
        request_str = update.message.text
    response_keyboard = search_response_formatter(request_str)
    response = "Is '" + request_str + "' Set or Minifigure?"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response,
        reply_markup=InlineKeyboardMarkup(response_keyboard)
    )

async def setSearchHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = None
    reply_markup = None
    request_str = None
    logging.debug("Processing search set command")
    if context.args and context.args[0] and len(context.args[0]) > 0:
        logging.debug("Using context arguments")
        request_str = " "
        request_str = request_str.join(context.args)
    elif update.message and len(update.message.text.replace('/search_set', '').strip()) > 0:
        logging.debug("Using update message")
        request_str = update.message.text.replace('/search_set', '').strip()
    elif update.callback_query:
        logging.debug("Using callback query")
        request_str = update.callback_query.data.replace("SETSEARCH", '').strip()
    logging.debug("Request string is: " + str(request_str))
    re_response = set_search_request(request_str)
    if re_response:
        target = "more" if (update.effective_chat.type == Chat.SUPERGROUP
                            or update.effective_chat.type == Chat.GROUP) else "INFO"
        response_keyboard = set_search_response_formatter(re_response, target)
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


async def minifigureSearchHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = None
    request_str = None
    logging.debug("Processing search minifigure command")
    if context.args and context.args[0] and len(context.args[0]) > 0:
        request_str = " "
        request_str = request_str.join(context.args)
    elif update.message and len(update.message.text.replace('/search_fig', '').strip()) > 0:
        request_str = update.message.text.replace('/search_fig', '').strip()
    elif update.callback_query:
        request_str = update.callback_query.data.replace("MINIFIGSEARCH", '').strip()
    re_response = minifigure_search_request(request_str)
    logging.debug('Recieved response from S3 client.')
    if re_response and len(re_response) != 0:
        logging.debug('Forming bot reply for minifigure search.')
        target = "more" if (update.effective_chat.type == Chat.SUPERGROUP
                            or update.effective_chat.type == Chat.GROUP) else "INFO"
        response_keyboard = fig_search_response_formatter(re_response, target)
        if len(response_keyboard) > 0:
            reply_markup = InlineKeyboardMarkup(response_keyboard)
            response = "Search result for '" + request_str + "'"
        else:
            response = "Nothing found for: " + request_str
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
                reply_markup = InlineKeyboardMarkup(resolveItemInfoKeyboard(update, item_number=itemNumber,
                                                                            item_type=response["type"]))
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
            text=START_TEXT
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
            reply_markup = InlineKeyboardMarkup(resolveItemInfoKeyboard(update, item_number=itemNumber,
                                                                        item_type=response["type"]))
            response = formatInfoResponse(response)
    except Exception as e:
        logging.debug(e)
    if response is None or len(response) == 0:
        await setSearchHandler(update, context)
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
            reply_markup = InlineKeyboardMarkup(resolveItemInfoKeyboard(update, item_number=itemNumber,
                                                                        item_type=response["type"]))
            response = formatInfoResponse(response)
    except Exception as e:
        logging.error(e)
    if (response is None or len(response) == 0) \
            and (update.effective_chat.type != Chat.SUPERGROUP and update.effective_chat.type != Chat.GROUP):
        await searchDialogHandler(update, context)
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
            reply_markup = InlineKeyboardMarkup(resolveItemInfoKeyboard(update, item_number=itemNumber,
                                                                        item_type=response["type"]))
            response = formatInfoResponse(response)
    except Exception as e:
        logging.error(e)
    if response is None or len(response) == 0:
        response = "Can't find anything for " + context.args[0]
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)

async def searchSetButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logging.debug("Query data: " + query.data)
    await query.answer()
    await setSearchHandler(update, context)

async def searchMinifigureButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logging.debug("Query data: " + query.data)
    await query.answer()
    await minifigureSearchHandler(update, context)


async def priceCommandHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Processing info request")
    try:
        query = update.message.text.lower()
        response = resolve_price(query)
        if response:
            logging.debug("Response from bl: " + str(response))
            response = formatPriceResponse(response)
    except Exception as e:
        logging.error(e)
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


def resolveItemInfoKeyboard(update: Update, item_number, item_type):
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
