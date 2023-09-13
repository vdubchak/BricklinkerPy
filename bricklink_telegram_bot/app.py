import asyncio
import json
import os
import sys

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, CommandHandler, filters, ContextTypes, Application, CallbackQueryHandler

from bricklink_client import ApiClient
from request_matcher import resolve_request

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "./vendored"))

TOKEN = os.environ['API_TEST_TOKEN']
BL_CONSUMER_KEY = os.environ['BL_CONSUMER_KEY']
BL_CONSUMER_SECRET = os.environ['BL_CONSUMER_SECRET']
BL_ACCESS_TOKEN = os.environ['BL_ACCESS_TOKEN']
BL_TOKEN_SECRET = os.environ['BL_TOKEN_SECRET']


def lambda_handler(event, context):
    try:
        asyncio.get_event_loop().run_until_complete(run_handler(event))
        return {"statusCode": 200}
    except Exception as e:
        print(e)
        return {"statusCode": 500}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Processing start command")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to Bricklink telegram bot.\n" \
             "Try typing in set number or minifigure number to get more info on it.\n" \
             "Example \"75100\" or \"sw0547\""
    )


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = None
    print("Processing info request")
    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2"),
        ],
        [InlineKeyboardButton("Option 3", callback_data="3")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        client = ApiClient(BL_CONSUMER_KEY, BL_CONSUMER_SECRET, BL_ACCESS_TOKEN, BL_TOKEN_SECRET)
        url = resolve_request(update.message.text)
        if url:
            response = client.get(url)
    except Exception as e:
        print(e)
        response = e

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)


async def run_handler(event):
    print("Calling lambda")
    dispatcher = Application.builder().token(token=TOKEN).build()
    print("Adding command handler")
    dispatcher.add_handler(CommandHandler(command='start', callback=start))
    print("Adding message handler")
    dispatcher.add_handler(MessageHandler(filters=filters.TEXT & (~filters.COMMAND), callback=info))
    dispatcher.add_handler(CallbackQueryHandler(button))
    await dispatcher.initialize()
    print("Application initialized")
    await dispatcher.process_update(update=Update.de_json(json.loads(event["body"]), dispatcher.bot))
    print("Shutting down application")
    await dispatcher.shutdown()


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer(text=f"Selected option: {query.data}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Selected option: {query.data}")
