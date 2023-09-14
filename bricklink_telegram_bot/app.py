import asyncio
import json
import os

from telegram import Update
from telegram.ext import MessageHandler, CommandHandler, filters, Application, CallbackQueryHandler

from handlers import startHandler, priceHandler, helpHandler, infoHandler, groupButtonHandler, priceButtonHandler, \
    defButtonHandler

TOKEN = os.environ['API_TEST_TOKEN']


def lambda_handler(event, context):
    try:
        asyncio.get_event_loop().run_until_complete(run_handler(event))
        return {"statusCode": 200}
    except Exception as e:
        print(e)
        return {"statusCode": 500}


async def run_handler(event):
    print("Calling lambda")
    dispatcher = Application.builder().token(token=TOKEN).build()
    print("Adding command handlers")
    dispatcher.add_handler(CommandHandler(command='start', callback=startHandler))
    dispatcher.add_handler(CommandHandler(command='price', callback=priceHandler))
    dispatcher.add_handler(CommandHandler(command='help', callback=helpHandler))
    print("Adding message handler")
    dispatcher.add_handler(MessageHandler(filters=filters.TEXT & (~filters.COMMAND), callback=infoHandler))
    dispatcher.add_handler(CallbackQueryHandler(groupButtonHandler, pattern="^.*more.*$"))
    dispatcher.add_handler(CallbackQueryHandler(priceButtonHandler, pattern="^.*price.*$"))
    dispatcher.add_handler(CallbackQueryHandler(defButtonHandler))
    await dispatcher.initialize()
    print("Application initialized")
    await dispatcher.process_update(update=Update.de_json(json.loads(event["body"]), dispatcher.bot))
    print("Shutting down application")
    await dispatcher.shutdown()

