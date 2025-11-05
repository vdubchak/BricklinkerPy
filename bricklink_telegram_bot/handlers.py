import os
import logging
import xml.etree.ElementTree as ET
from io import BytesIO

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat, InputFile
from telegram.ext import ContextTypes

from authorization import is_admin
from s3_client import minifigure_search_request, write_minifigs_to_file
from rebrickable_client import set_search_request
from response_formatters import format_info_response, format_price_response, format_items_sold_response, \
    format_items_for_sale_response, set_search_response_formatter, fig_search_response_formatter, search_response_formatter, \
    escape, subset_response_formatter, superset_response_formatter
from request_matcher import resolve_price, resolve_info, resolve_sold, resolve_subsets, resolve_supersets

BOT_NAME = os.environ['BOT_NAME']
HELP_TEXT = "Try typing in set number, name or minifigure number to get more info on it.\n" \
            "Example \"75100-1\", \"4950\", \"sw0547\" or \"hotel\"" \
            "Alternatively or if bot is in group chat you can use commands like " \
            "/info 42069 or /price col404\n" \
            "You can also use /search command to find set numbers (currently not working for minifigures)\n" \
            "Example: /search hotel"
START_TEXT = "What are you looking for? Try typing set/minifigure number or name, for example 4950, " \
             "sw0547 or fishing store."
BL_URL = "https://www.bricklink.com/v2/catalog/catalogitem.page?{}={}"


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("[Handlers] Processing start command")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=HELP_TEXT
    )


async def search_dialog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request_str = None
    logging.info("[Handlers] Processing search by name request")
    if context.args and context.args[0] and len(context.args[0]) > 0:
        request_str = " "
        request_str = request_str.join(context.args)
    elif len(update.message.text) > 0:
        request_str = update.message.text
    logging.info("[Handlers] Argument: " + request_str)
    response_keyboard = search_response_formatter(request_str)
    response = escape("Is '" + request_str + "' Set or Minifigure?")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response,
        reply_markup=InlineKeyboardMarkup(response_keyboard),
        parse_mode='MarkdownV2'
    )


async def set_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = None
    reply_markup = None
    request_str = None
    logging.info("[Handlers] Processing search command")
    if context.args and context.args[0] and len(context.args[0]) > 0:
        request_str = " "
        request_str = request_str.join(context.args)
        logging.info("[Handlers] Argument using context argument: " + request_str)
    elif update.message and len(update.message.text.replace('/search_set', '').strip()) > 0:
        request_str = update.message.text.replace('/search_set', '').strip()
        logging.info("[Handlers] Argument using update message: " + request_str)
    elif update.callback_query:
        request_str = update.callback_query.data.replace("SETSEARCH", '').strip()
        logging.info("[Handlers] Argument using callback query: " + request_str)
    re_response = set_search_request(request_str)
    if re_response:
        target = "more" if (update.effective_chat.type == Chat.SUPERGROUP
                            or update.effective_chat.type == Chat.GROUP) else "INFO"
        response_keyboard = set_search_response_formatter(re_response, target)
        if len(response_keyboard) > 0:
            reply_markup = InlineKeyboardMarkup(response_keyboard)
            response = escape("Search result for '" + request_str + "'")
        else:
            response = escape("Nothing found for: " + request_str)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )


async def minifigure_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = None
    request_str = None
    logging.info("[Handlers] Processing search minifigure command")
    if context.args and context.args[0] and len(context.args[0]) > 0:
        request_str = " "
        request_str = request_str.join(context.args)
    elif update.message and len(update.message.text.replace('/search_fig', '').strip()) > 0:
        request_str = update.message.text.replace('/search_fig', '').strip()
    elif update.callback_query:
        request_str = update.callback_query.data.replace("MINIFIGSEARCH", '').strip()
    logging.info("[Handlers] Argument: " + request_str)
    re_response = minifigure_search_request(request_str)
    logging.debug("[Handlers] Received response from S3 client.")
    if re_response and len(re_response) != 0:
        logging.debug('[Handlers] Forming bot reply for minifigure search.')
        target = "more" if (update.effective_chat.type == Chat.SUPERGROUP
                            or update.effective_chat.type == Chat.GROUP) else "INFO"
        response_keyboard = fig_search_response_formatter(re_response, target)
        if len(response_keyboard) > 0:
            reply_markup = InlineKeyboardMarkup(response_keyboard)
            response = escape("Search result for '" + request_str + "'")
        else:
            response = escape("Nothing found for: " + request_str)
    else:
        response = escape("Nothing found for: " + request_str)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("[Handlers] Processing start command")
    if context.args and context.args[0] and len(context.args[0]) > 0:
        reply_markup = None
        try:
            logging.info("[Handlers] Argument: " + str(context.args[0]))
            response = resolve_info(context.args[0])
            if response:
                itemNumber = response['no']
                reply_markup = InlineKeyboardMarkup(resolve_item_info_keyboard(update, item_number=itemNumber,
                                                                               item_type=response["type"]))
                response = format_info_response(response)
        except Exception as e:
            logging.error(e)
            response = e
        if response is None or len(response) == 0:
            response = escape("Can't find anything for " + context.args[0])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup,
                                       parse_mode='MarkdownV2')
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=escape(START_TEXT),
            parse_mode='MarkdownV2'
        )


async def info_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("[Handlers] Processing info request")
    reply_markup = None
    response = None
    formatted_response = None
    try:
        query = update.message.text.lower()
        logging.info("[Handlers] Argument: " + str(query))
        response = resolve_info(query)
        if response:
            itemNumber = response['no']
            reply_markup = InlineKeyboardMarkup(resolve_item_info_keyboard(update, item_number=itemNumber,
                                                                           item_type=response["type"]))
            formatted_response = format_info_response(response)
    except Exception as e:
        logging.error(e)
    if formatted_response is None or len(formatted_response) == 0:
        await set_search_handler(update, context)
    else:
        await respond_info(context, formatted_response, reply_markup, response, update)

async def file_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("[Handlers] File handler.")
    logging.info("[Handlers] Argument: " + update.message.document.file_id)
    logging.info("[Handlers] Sender: " + update.message.from_user.name)
    response = "Failed to update."
    if is_admin(update.message.from_user):
        try:
            file = await context.bot.get_file(update.message.document)
            bytecontent = bytes(await file.download_as_bytearray())
            root = ET.XML(bytecontent)
            minifig_dict = {}
            mapped = True
            for child in root:
                itemid = child.find('ITEMID')
                itemname = child.find('ITEMNAME')
                itemyear = child.find('ITEMYEAR')
                if itemid is None or itemyear is None or itemname is None:
                    response = ("Invalid file format. "
                                "Make sure you are using valid Bricklink XML and don't forget to include a year.")
                    mapped = False
                    break
                minifig_dict[itemid.text] = {
                    'name': itemname.text,
                    'year': itemyear.text
                }
            if mapped:
                write_minifigs_to_file(minifig_dict)
                response = "Successfully updated."
        except Exception as e:
            logging.error(e)
            response = "Can not read file. Make sure it has a valid Bricklink XML format."
    else:
        response = "Forbidden."
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response
    )


async def info_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("[Handlers] Processing info message handler")
    reply_markup = None
    response = None
    formatted_response = None
    try:
        query = update.message.text.lower()
        logging.info("[Handlers] Argument: " + str(query))
        response = resolve_info(query)
        if response and response['no']:
            itemNumber = response['no']
            reply_markup = InlineKeyboardMarkup(resolve_item_info_keyboard(update, item_number=itemNumber,
                                                                           item_type=response["type"]))
            formatted_response = format_info_response(response)
    except Exception as e:
        logging.error(e)
    if (formatted_response is None or len(formatted_response) == 0) \
            and (update.effective_chat.type != Chat.SUPERGROUP and update.effective_chat.type != Chat.GROUP):
        await search_dialog_handler(update, context)
    else:
        await respond_info(context, formatted_response, reply_markup, response, update)


async def respond_info(context, formatted_response, reply_markup, response, update):
    if response["image_url"]:
        try:
            image_url = "https:" + response["image_url"]
            logging.debug("[Handlers] Image URL: " + image_url)
            #scummy hack
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            }

            image_response = requests.get(image_url, headers=headers)
            image_response.raise_for_status()
            image_file = BytesIO(image_response.content)

            image = InputFile(image_file)
            image.filename = response["no"] + ".jpg"
            await context.bot.send_photo(photo=image, chat_id=update.effective_chat.id, caption=formatted_response,
                                         reply_markup=reply_markup,
                                         parse_mode='MarkdownV2')
        except requests.RequestException as e:
            logging.error(e)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=formatted_response,
                                           reply_markup=reply_markup,
                                           parse_mode='MarkdownV2')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=formatted_response,
                                       reply_markup=reply_markup,
                                       parse_mode='MarkdownV2')


async def info_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logging.info("[Handlers] Info button")
    logging.info("[Handlers] Argument: " + query.data)
    reply_markup = None
    response = None
    formatted_response = None
    try:
        itemNumber = query.data.replace("INFO ", "")
        response = resolve_info(itemNumber)
        if response:
            reply_markup = InlineKeyboardMarkup(resolve_item_info_keyboard(update, item_number=itemNumber,
                                                                           item_type=response["type"]))
            formatted_response = format_info_response(response)
    except Exception as e:
        logging.error(e)
    if formatted_response is None or len(response) == 0:
        formatted_response = escape("Can't find anything for " +
                          query.data.replace("INFO ", "") +
                          ". It is possible that this item is missing from BrickLink database.")
    await query.answer()
    await respond_info(context, formatted_response, reply_markup, response, update)


async def subset_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    itemNumber = query.data.replace("SUBSET ", "")
    logging.info("[Handlers] Subsets button")
    logging.info("[Handlers] Argument: " + query.data)
    reply_markup = None
    response_keyboard = []
    try:
        response = resolve_subsets(itemNumber)
        if response:
            response_keyboard = subset_response_formatter(response, "INFO")
    except Exception as e:
        logging.error(e)
    if len(response_keyboard) > 0:
        reply_markup = InlineKeyboardMarkup(response_keyboard)
        response_str = escape("Minifigures in '" + itemNumber + "'")
    else:
        response_str = escape("Nothing found in: " + itemNumber)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response_str,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )


async def superset_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    itemNumber = query.data.replace("SUPERSET ", "")
    logging.info("[Handlers] Supersets button")
    logging.info("[Handlers] Argument: " + query.data)
    reply_markup = None
    response_keyboard = []
    try:
        response = resolve_supersets(itemNumber)
        if response:
            response_keyboard = superset_response_formatter(response, "INFO")
    except Exception as e:
        logging.error(e)
    if len(response_keyboard) > 0:
        reply_markup = InlineKeyboardMarkup(response_keyboard)
        response_str = escape("Sets containing '" + itemNumber + "'")
    else:
        response_str = escape("No sets found containing: " + itemNumber)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response_str,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )


async def search_set_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logging.info("[Handlers] Search set button")
    logging.info("[Handlers] Argument: " + query.data)

    await query.answer()
    await set_search_handler(update, context)


async def search_minifigure_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logging.info("[Handlers] Search minifigure button")
    logging.info("[Handlers] Argument: " + query.data)

    await query.answer()
    await minifigure_search_handler(update, context)


async def price_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("[Handlers] Processing price request")
    try:
        query = update.message.text.lower()
        logging.info("[Handlers] Argument: " + str(query))
        response = resolve_price(query)
        if response:
            logging.debug("[Handlers] Response from bl: " + str(response))
            response = format_price_response(response)
    except Exception as e:
        logging.error(e)
        response = e
    if response is None or len(response) == 0:
        response = escape("Cannot find data for " + update.message.text)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode='MarkdownV2')


async def group_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("[Handlers] Processing group button request")
    query = update.callback_query
    logging.info("[Handlers] Argument: " + str(query))
    item = query.data.replace("more ", "")
    await query.answer(url="https://t.me/" + BOT_NAME + "?start=" + item)


async def price_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("[Handlers] Processing price button request")
    query = update.callback_query
    logging.info("[Handlers] Query data: " + query.data)
    await query.answer()
    try:
        response = resolve_price(query.data)
        if response:
            logging.debug("[Handlers] Response from bl: " + str(response))
            response = format_price_response(response)

    except Exception as e:
        logging.error(e)
        response = e
    if response is None or response.__sizeof__() == 0:
        response = escape("Cannot find data for " + query.data)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode='MarkdownV2')


async def sold_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    response = None
    logging.info("[Handlers] Processing sold button request")
    logging.info("[Handlers] Query data: " + query.data)
    await query.answer()
    try:
        response = resolve_sold(query.data)
        if response:
            response = format_items_sold_response(response)
    except Exception as e:
        logging.error(e)
        # response = str(e)
    if response is None or len(response) == 0:
        response = escape("Cannot find data for " + query.data)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode='MarkdownV2')


async def stock_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    response = None
    logging.info("[Handlers] Processing stock button request")
    logging.info("[Handlers] Argument: " + query.data)
    await query.answer()
    try:
        response = resolve_sold(query.data)
        response = format_items_for_sale_response(response)
    except Exception as e:
        logging.error(e)
        # response = str(e)
    if response is None or len(response) == 0:
        response = escape("Cannot find data for " + query.data)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode='MarkdownV2')


async def def_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.warning("[Handlers] Processing default button request")
    query = update.callback_query
    await query.answer(text="Not implemented yet")


def resolve_item_info_keyboard(update: Update, item_number, item_type):
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
            [InlineKeyboardButton("Minifigures of " + item_number, callback_data="SUBSET " + item_number) if item_type == "SET" else
             InlineKeyboardButton("Sets containing " + item_number, callback_data="SUPERSET " + item_number)],
            [InlineKeyboardButton("View on BL", url=BL_URL.format(item_type[0], item_number))]
        ]

    return keyboard
