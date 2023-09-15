import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes

from response_formatters import formatInfoResponse, formatPriceResponse, formatItemsSoldResponse, \
    formatItemsForSaleResponse
from request_matcher import resolve_price, resolve_info, resolve_sold

BOT_NAME = os.environ['BOT_NAME']
HELP_TEXT = "Welcome to Bricklink telegram bot.\n"\
                 "Try typing in set number or minifigure number to get more info on it.\n"\
                 "Example \"75100\" or \"sw0547\""\
                 "Alternatively or if bot is in group chat you can use commands like "\
                 "/info 42069 or /price col404"


async def helpHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Processing start command")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=HELP_TEXT
    )


async def startHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Processing start command")
    if context.args and context.args[0] and len(context.args[0]) > 0:
        reply_markup = None
        try:
            response = resolve_info(context.args[0])
            itemNumber = response['no']
            response = formatInfoResponse(response)
            reply_markup = InlineKeyboardMarkup(resolveKeyboard(update, item_number=itemNumber))
        except Exception as e:
            logging.debug(e)
            response = e
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=HELP_TEXT
        )


async def infoHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Processing info request")
    reply_markup = None
    try:
        response = resolve_info(update.message.text)
        itemNumber = response['no']
        reply_markup = InlineKeyboardMarkup(resolveKeyboard(update, item_number=itemNumber))
        response = formatInfoResponse(response)
    except Exception as e:
        logging.debug(e)
        response = e

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)


async def priceHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Processing info request")
    try:
        response = resolve_price(update.message.text)
        logging.debug("Response from bl: " + str(response))
        response = formatPriceResponse(response)
    except Exception as e:
        logging.debug(e)
        response = e
    if response is None or response.__sizeof__() == 0:
        response = "Cannot find data for "

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def groupButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
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
        logging.debug("Response from bl: " + str(response))
        response = formatPriceResponse(response)

    except Exception as e:
        logging.debug(e)
        response = e
    if response is None or response.__sizeof__() == 0:
        response = "Cannot find data for " + query.data

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def soldButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    logging.debug("Query data: " + query.data)
    await query.answer()
    logging.debug("Processing sold button request")
    try:
        response = resolve_sold(query.data)
        response = formatItemsSoldResponse(response)
    except Exception as e:
        logging.debug(e)
        response = e
    if response is None or response.__sizeof__() == 0:
        response = "Cannot find data for " + query.data

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def stockButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    logging.debug("Query data: " + query.data)
    await query.answer()
    logging.debug("Processing stock button request")
    try:
        response = resolve_sold(query.data)
        response = formatItemsForSaleResponse(response)
    except Exception as e:
        logging.debug(e)
        response = e
    if response is None or response.__sizeof__() == 0:
        response = "Cannot find data for " + query.data

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def defButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer(text="Not implemented yet")


def resolveKeyboard(update: Update, item_number):
    if update.effective_chat.type == Chat.SUPERGROUP or update.effective_chat.type == Chat.GROUP:
        keyboard = [
            [InlineKeyboardButton("More info on " + item_number, callback_data="more " + item_number)],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("Price guide for new " + item_number, callback_data="PRICE NEW " + item_number),
             InlineKeyboardButton("Price guide for used " + item_number, callback_data="PRICE USED " + item_number)],
            [InlineKeyboardButton("Recently sold new", callback_data="SOLD NEW " + item_number),
             InlineKeyboardButton("Recently sold used", callback_data="SOLD USED " + item_number)],
            [InlineKeyboardButton("For sale new", callback_data="STOCK NEW " + item_number),
             InlineKeyboardButton("For sale used", callback_data="STOCK USED " + item_number)],
        ]
    return keyboard
