import asyncio
import json
import os
import logging

from telegram import Update
from telegram.ext import MessageHandler, CommandHandler, filters, Application, CallbackQueryHandler

from handlers import start_handler, price_command_handler, help_handler, group_button_handler, price_button_handler, \
    def_button_handler, sold_button_handler, stock_button_handler, info_command_handler, info_message_handler, set_search_handler, \
    info_button_handler, minifigure_search_handler, search_set_button_handler, subset_button_handler, superset_button_handler, \
    file_message_handler

TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
LOGLEVEL = os.environ.get('LOGLEVEL', 'DEBUG')
logging.getLogger().setLevel(level=LOGLEVEL.upper())


def lambda_handler(event, context):
    try:
        asyncio.get_event_loop().run_until_complete(run_handler(event))
        return {"statusCode": 200}
    except Exception as e:
        logging.error(e)
        return {"statusCode": 500}


async def run_handler(event):
    logging.debug("[App] Calling lambda")
    dispatcher = Application.builder().token(token=TOKEN).build()
    logging.debug("[App] Adding command handlers")
    dispatcher.add_handler(CommandHandler(command='start', callback=start_handler))
    dispatcher.add_handler(CommandHandler(command='price', callback=price_command_handler))
    dispatcher.add_handler(CommandHandler(command='help', callback=help_handler))
    dispatcher.add_handler(CommandHandler(command='info', callback=info_command_handler))
    dispatcher.add_handler(CommandHandler(command='search', callback=info_command_handler))
    dispatcher.add_handler(CommandHandler(command='search_set', callback=set_search_handler))
    dispatcher.add_handler(CommandHandler(command='search_fig', callback=minifigure_search_handler))
    dispatcher.add_handler(MessageHandler(filters=(filters.Document.XML | filters.Document.MimeType("application/xml") |
                                                  filters.Document.TEXT) & (~filters.COMMAND),
                                          callback=file_message_handler))
    dispatcher.add_handler(MessageHandler(filters=filters.TEXT & (~filters.COMMAND), callback=info_message_handler))
    dispatcher.add_handler(CallbackQueryHandler(group_button_handler, pattern="^.*more.*$"))
    dispatcher.add_handler(CallbackQueryHandler(price_button_handler, pattern="^.*PRICE.*$"))
    dispatcher.add_handler(CallbackQueryHandler(sold_button_handler, pattern="^.*SOLD.*$"))
    dispatcher.add_handler(CallbackQueryHandler(stock_button_handler, pattern="^.*STOCK.*$"))
    dispatcher.add_handler(CallbackQueryHandler(info_button_handler, pattern="^.*INFO.*$"))
    dispatcher.add_handler(CallbackQueryHandler(search_set_button_handler, pattern="^.*SETSEARCH.*$"))
    dispatcher.add_handler(CallbackQueryHandler(minifigure_search_handler, pattern="^.*MINIFIGSEARCH.*$"))
    dispatcher.add_handler(CallbackQueryHandler(subset_button_handler, pattern="^.*SUBSET.*$"))
    dispatcher.add_handler(CallbackQueryHandler(superset_button_handler, pattern="^.*SUPERSET.*$"))
    dispatcher.add_handler(CallbackQueryHandler(def_button_handler))
    await dispatcher.initialize()
    logging.debug("[App] Application initialized")
    await dispatcher.process_update(update=Update.de_json(json.loads(event["body"]), dispatcher.bot))
    logging.debug("[App] Event: ")
    logging.debug(event["body"])
    logging.debug("Shutting down application")

    await dispatcher.shutdown()
