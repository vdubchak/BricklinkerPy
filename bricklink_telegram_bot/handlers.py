import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes

from response_formatters import formatInfoResponse, formatPriceResponse
from request_matcher import resolve_price, resolve_info

BOT_NAME = os.environ['BOT_NAME']


async def helpHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Processing start command")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to Bricklink telegram bot.\n" \
             "Try typing in set number or minifigure number to get more info on it.\n" \
             "Example \"75100\" or \"sw0547\""
    )


async def startHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Processing start command")
    if context.args[0]:
        reply_markup = None
        try:
            response = resolve_info(context.args[0])
            itemNumber = response['no']
            response = formatInfoResponse(response)
            keyboard = [
                [InlineKeyboardButton("Price guide for " + itemNumber, callback_data="price " + itemNumber)],
                [InlineKeyboardButton("Recently sold items", callback_data="sold " + itemNumber)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        except Exception as e:
            print(e)
            response = e

        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Welcome to Bricklink telegram bot.\n" \
                 "Try typing in set number or minifigure number to get more info on it.\n" \
                 "Example \"75100\" or \"sw0547\""
        )


async def infoHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Processing info request")
    reply_markup = None
    try:
        response = resolve_info(update.message.text)
        itemNumber = response['no']
        if update.effective_chat.type == Chat.SUPERGROUP or update.effective_chat.type == Chat.GROUP:
            keyboard = [
                [InlineKeyboardButton("More info on " + itemNumber, callback_data="more " + itemNumber)],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("Price guide for " + itemNumber, callback_data="price " + itemNumber)],
                [InlineKeyboardButton("Recently sold items", callback_data="sold " + itemNumber)]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        response = formatInfoResponse(response)
    except Exception as e:
        print(e)
        response = e

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)


async def priceHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Processing info request")
    try:
        response = resolve_price(update.message.text)
        response = formatPriceResponse(response)
    except Exception as e:
        print(e)
        response = e
    if response is None or response.__sizeof__() == 0:
        response = "Cannot find data for "

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def groupButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    print("Query data: " + query.data)
    item = query.data.replace("more ", "")
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer(url="https://t.me/" + BOT_NAME + "?start=" + item)
    # await context.bot.send_message(chat_id=update.effective_user.id, text="Selected option: " + query.data)


async def priceButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    print("Query data: " + query.data)
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    print("Processing price button request")
    try:
        response = resolve_price(query.data)
        response = formatPriceResponse(response)
    except Exception as e:
        print(e)
        response = e
    if response is None or response.__sizeof__() == 0:
        response = "Cannot find data for " + query.data

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    # await context.bot.send_message(chat_id=update.effective_user.id, text="Selected option: " + query.data)


async def defButtonHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer(text="Not implemented yet")
