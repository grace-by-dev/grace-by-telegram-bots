from functools import partial
import os
import re

from dotenv import load_dotenv
from omegaconf import OmegaConf
import telebot
from telebot import types

from common.src.utils import edit_keyboard_message
from common.src.utils import get_logger
from common.src.utils import send_keyboard_message
from step_of_faith.src.postgres_sql import PostgreSQL
from step_of_faith.src.user_utils import UserUtils


env_file = "step_of_faith/.env"
yaml_file = "step_of_faith/resources/replies.yaml"
buttons_yaml_file = "step_of_faith/resources/buttons.yaml"

replies = OmegaConf.load(yaml_file)
buttons = OmegaConf.load(buttons_yaml_file)


read = load_dotenv(env_file)
token = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(token)

logger = get_logger(__name__)

sql = PostgreSQL()
user_utils = UserUtils(env_file)

def show_schedule_day(callback: types.CallbackQuery, button, day: int) -> None:
    schedule = sql.get_schedule(day)
    schedule = [
        button.reply.row_template.format(time=time, event=event) for (time, event) in schedule
    ]
    schedule = button.reply.header + "\n" + "\n".join(schedule)
    edit_keyboard_message(
        callback, reply=schedule, row_width=button.row_width, children=button.children, bot=bot
    )


def show_counselors(callback: types.CallbackQuery, button) -> None:
    counselors = sql.get_counselors()
    children = []
    for counselor_id, name in counselors:
        children.append({"text": name, "data": f"{callback.data}::{counselor_id}"})
    children.extend(button.children)
    edit_keyboard_message(
        callback, reply=button.reply, row_width=button.row_width, children=children, bot=bot
    )


def show_particular_counselor(callback: types.CallbackQuery, button, counselor_id: int) -> None:
    name, description = sql.get_counselor_info(counselor_id)
    timeslots = sql.get_counselor_timeslots(counselor_id)
    reply = button.reply.format(name=name, n=len(timeslots), description=description)
    children = []
    for (slot,) in timeslots:
        time = slot.strftime("%H:%M")
        children.append(
            {"text": button.child_template.format(time=time), "data": f"{callback.data}::{time}"}
        )
    children.extend(button.children)
    edit_keyboard_message(
        callback, reply=reply, row_width=button.row_width, children=children, bot=bot
    )


def book_counseling(callback: types.CallbackQuery, button, counselor_id: int, time: str) -> None:
    status = sql.book_counseling(
        counselor_id=counselor_id, user_id=callback.message.chat.id, time=time
    )
    button = button.success if status else button.failure
    edit_keyboard_message(callback, **button, bot=bot)


def show_my_counseling(callback: types.CallbackQuery, button) -> None:
    booking = sql.get_my_counseling(user_id=callback.message.chat.id)
    if booking:
        name, description, time = booking
        time = time.strftime("%H:%M")
        button = button.exists
        reply = button.reply.format(name=name, time=time, description=description)
        edit_keyboard_message(
            callback, reply=reply, row_width=button.row_width, children=button.children, bot=bot
        )
    else:
        edit_keyboard_message(callback, **button.missing, bot=bot)


def cancel_counseling(callback: types.CallbackQuery, button) -> None:
    sql.cancel_counseling(callback.message.chat.id)
    edit_keyboard_message(callback, **button, bot=bot)


def show_seminars(callback: types.CallbackQuery, button) -> None:
    seminars = sql.get_seminars()
    children = []
    for seminar_id, title in seminars:
        children.append({"text": title, "data": f"{callback.data}::{seminar_id}"})
    children.extend(button.children)
    edit_keyboard_message(
        callback, reply=button.reply, row_width=button.row_width, children=children, bot=bot
    )


def show_particular_seminar(callback: types.CallbackQuery, button, seminar_id: int) -> None:
    enroll, back = button.children
    title, description = sql.get_seminar_info(seminar_id)
    reply = button.reply.format(title=title, description=description)
    children = [{"text": enroll.text, "data": enroll.data.format(seminar_id=seminar_id)}, back]
    edit_keyboard_message(
        callback, reply=reply, row_width=button.row_width, children=children, bot=bot
    )


def choose_seminar_number(callback: types.CallbackQuery, button, seminar_id: int) -> None:
    first, second, back = button.children
    title, description = sql.get_seminar_info(seminar_id)
    reply = button.reply.format(title=title, description=description)
    children = [
        {"text": first.text, "data": first.data.format(seminar_id=seminar_id)},
        {"text": second.text, "data": second.data.format(seminar_id=seminar_id)},
        back,
    ]
    edit_keyboard_message(
        callback, reply=reply, row_width=button.row_width, children=children, bot=bot
    )


def enroll_for_seminar(callback: types.CallbackQuery, button, seminar_id: int, seminar_number: int) -> None:
    sql.enroll_for_seminar(
        seminar_id=seminar_id, user_id=callback.message.chat.id, seminar_number=seminar_number
    )
    edit_keyboard_message(callback, **button, bot=bot)


def show_my_seminars(callback: types.CallbackQuery, button) -> None:
    (title1, description1), (title2, description2) = sql.get_my_seminars(callback.message.chat.id)
    reply = button.reply.exists if title1 else button.reply.missing
    seminar1, seminar2, back = button.children
    children = []
    if title1:
        children.append(seminar1)
    if title2:
        children.append(seminar2)
    children.append(back)
    edit_keyboard_message(
        callback, reply=reply, children=children, row_width=button.row_width, bot=bot
    )


def show_my_particular_seminar(callback: types.CallbackQuery, button, id: int) -> None:
    id = int(id)
    seminars = sql.get_my_seminars(callback.message.chat.id)
    (title, description) = seminars[int(id) - 1]
    reply = button.reply.template.format(title=title, description=description)
    cancel, back = button.children
    children = [{"text": cancel.text, "data": f"{callback.data}::cancel"}, back]
    edit_keyboard_message(
        callback, reply=reply, children=children, row_width=button.row_width, bot=bot
    )


def cancel_my_seminar(callback: types.CallbackQuery, button, id: int) -> None:
    id = int(id)
    sql.cancel_my_seminar(callback.message.chat.id, id)
    edit_keyboard_message(
        callback, reply=button.reply, children=button.children, row_width=button.row_width, bot=bot
    )


def show_basic_button(callback: types.CallbackQuery, button) -> None:
    edit_keyboard_message(callback, **button, bot=bot)


@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback: types.CallbackQuery) -> None:
    callback_patterns = [
        ("^menu$", show_basic_button),
        ("^schedule$", show_basic_button),
        ("^counseling$", show_basic_button),
        ("^seminars$", show_basic_button),
        ("^subscribe$", show_basic_button),
        ("^church_schedule$", show_basic_button),
        ("^schedule::day::(\\d+)$", show_schedule_day),
        ("^counseling::options$", show_counselors),
        ("^counseling::options::(\\d+)$", show_particular_counselor),
        ("^counseling::options::(\\d+)::(\\d{1,2}):(\\d{1,2})$", book_counseling),
        ("^counseling::my$", show_my_counseling),
        ("^seminars::options$", show_seminars),
        ("^seminars::options::(\\d+)$", show_particular_seminar),
        ("^seminars::options::(\\d+)::enroll$", choose_seminar_number),
        ("^seminars::options::(\\d+)::enroll::(\\d)$", enroll_for_seminar),
        ("^seminars::my$", show_my_seminars),
        ("^seminars::my::(\\d{1,2})$", show_my_particular_seminar),
        ("^seminars::my::(\\d{1,2})::cancel$", cancel_my_seminar),
    ]
    for pattern, func in callback_patterns:
        match = re.search(pattern, callback.data)
        if match is not None:
            func(callback, buttons[pattern], *match.groups())
            break


@bot.message_handler(commands=["start"])
def menu(message: types.Message) -> None:
    if not sql.check_user_id(message.from_user.id):
        sql.add_to_database(message.from_user.id)
    current = sql.is_banned(message.from_user.id)
    if not current:
        send_keyboard_message(message, **replies["welcome"], bot=bot)
    else:
        bot.send_message(message.from_user.id, replies["ban"]["banned"])


if __name__ == "__main__":
    logger.info("START BOT...")
    bot.infinity_polling()