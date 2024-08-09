import asyncio
import json
import os
import logging

from telegram import Update
from telegram.ext import MessageHandler, CommandHandler, filters, Application, CallbackQueryHandler

from handlers import startHandler, priceCommandHandler, helpHandler, groupButtonHandler, priceButtonHandler, \
    defButtonHandler, soldButtonHandler, stockButtonHandler, infoCommandHandler, infoMessageHandler, setSearchHandler, \
    infoButtonHandler, minifigureSearchHandler, searchSetButtonHandler, subsetButtonHandler, supersetButtonHandler, \
    fileMessageHandler

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
    dispatcher.add_handler(CommandHandler(command='start', callback=startHandler))
    dispatcher.add_handler(CommandHandler(command='price', callback=priceCommandHandler))
    dispatcher.add_handler(CommandHandler(command='help', callback=helpHandler))
    dispatcher.add_handler(CommandHandler(command='info', callback=infoCommandHandler))
    dispatcher.add_handler(CommandHandler(command='search', callback=infoCommandHandler))
    dispatcher.add_handler(CommandHandler(command='search_set', callback=setSearchHandler))
    dispatcher.add_handler(CommandHandler(command='search_fig', callback=minifigureSearchHandler))
    dispatcher.add_handler(MessageHandler(filters=(filters.Document.XML | filters.Document.MimeType("application/xml") |
                                                  filters.Document.TEXT) & (~filters.COMMAND),
                                          callback=fileMessageHandler))
    dispatcher.add_handler(MessageHandler(filters=filters.TEXT & (~filters.COMMAND), callback=infoMessageHandler))
    dispatcher.add_handler(CallbackQueryHandler(groupButtonHandler, pattern="^.*more.*$"))
    dispatcher.add_handler(CallbackQueryHandler(priceButtonHandler, pattern="^.*PRICE.*$"))
    dispatcher.add_handler(CallbackQueryHandler(soldButtonHandler, pattern="^.*SOLD.*$"))
    dispatcher.add_handler(CallbackQueryHandler(stockButtonHandler, pattern="^.*STOCK.*$"))
    dispatcher.add_handler(CallbackQueryHandler(infoButtonHandler, pattern="^.*INFO.*$"))
    dispatcher.add_handler(CallbackQueryHandler(searchSetButtonHandler, pattern="^.*SETSEARCH.*$"))
    dispatcher.add_handler(CallbackQueryHandler(minifigureSearchHandler, pattern="^.*MINIFIGSEARCH.*$"))
    dispatcher.add_handler(CallbackQueryHandler(subsetButtonHandler, pattern="^.*SUBSET.*$"))
    dispatcher.add_handler(CallbackQueryHandler(supersetButtonHandler, pattern="^.*SUPERSET.*$"))
    dispatcher.add_handler(CallbackQueryHandler(defButtonHandler))
    await dispatcher.initialize()
    logging.debug("[App] Application initialized")
    await dispatcher.process_update(update=Update.de_json(json.loads(event["body"]), dispatcher.bot))
    logging.debug("[App] Event: ")
    logging.debug(event["body"])
    logging.debug("Shutting down application")

    await dispatcher.shutdown()
