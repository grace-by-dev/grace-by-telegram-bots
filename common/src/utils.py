from functools import partial
import logging
import re
from typing import Callable
from typing import Dict
from typing import List

import telebot
from telebot import types


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler("bot.log")
    handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | (%(levelname)s): %(message)s (Line:" + "%(lineno)d) [%(filename)s]",
        datefmt="%d-%m-%Y %I:%M:%S",
    )

    handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger


def callback_query_handler_x(func: partial, bot: telebot.TeleBot) -> Callable:
    def inner(f: Callable) -> Callable:
        f = partial(f, **func.keywords)
        bot.callback_query_handler(func=func)(f)
        return f

    return inner


def create_keyboard(row_width: int, children: List[Dict[str, str]]) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=row_width)
    _buttons = [
        types.InlineKeyboardButton(
            text=child["text"], callback_data=child.get("data"), url=child.get("url")
        )
        for child in children
    ]
    keyboard.add(*_buttons)
    return keyboard


def edit_keyboard_message(
    callback: types.CallbackQuery,
    reply: str,
    row_width: int,
    children: List[Dict[str, str]],
    bot: telebot.TeleBot,
) -> None:
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=reply,
        reply_markup=create_keyboard(row_width, children),
        parse_mode="Markdown",
    )


def send_keyboard_message(
    message: types.Message,
    reply: str,
    row_width: int,
    children: List[Dict[str, str]],
    bot: telebot.TeleBot,
) -> None:
    bot.send_message(
        message.chat.id,
        reply,
        reply_markup=create_keyboard(row_width, children),
        parse_mode="Markdown",
    )


def filter_callback(callback: types.CallbackQuery, pattern: str) -> bool:
    print(re.search(pattern, callback.data), pattern, callback.data)
    return re.search(pattern, callback.data) is not None
