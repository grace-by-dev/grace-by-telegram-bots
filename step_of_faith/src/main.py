from functools import partial
import os

from dotenv import load_dotenv
from omegaconf import OmegaConf
import telebot
from telebot import types

from common.src.utils import callback_query_handler_x
from common.src.utils import edit_keyboard_message
from common.src.utils import filter_callback
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


for data in [
    "^menu$",
    "^schedule$",
    "^counseling$",
    "^seminars$",
    "^subscribe$",
]:
    filter_ = partial(filter_callback, pattern=data)
    processor = partial(edit_keyboard_message, **buttons[data], bot=bot)
    bot.callback_query_handler(func=filter_)(processor)


@callback_query_handler_x(func=partial(filter_callback, pattern="^schedule::day::\\d*$"), bot=bot)
def show_schedule_day(callback: types.CallbackQuery, pattern: str) -> None:
    *_, day = callback.data.rsplit("::", maxsplit=1)
    day = int(day)
    button = buttons[pattern]
    schedule = sql.get_schedule(day)
    schedule = [
        button.reply.row_template.format(time=time, event=event) for (time, event) in schedule
    ]
    schedule = button.reply.header + "\n" + "\n".join(schedule)
    edit_keyboard_message(
        callback, reply=schedule, row_width=button.row_width, children=button.children, bot=bot
    )


@callback_query_handler_x(func=partial(filter_callback, pattern="^counseling::options$"), bot=bot)
def show_counselors(callback: types.CallbackQuery, pattern: str) -> None:
    button = buttons[pattern]
    counselors = sql.get_counselors()
    children = []
    for counselor_id, name in counselors:
        children.append({"text": name, "data": f"{callback.data}::{counselor_id}"})
    children.extend(button.children)
    edit_keyboard_message(
        callback, reply=button.reply, row_width=button.row_width, children=children, bot=bot
    )


@callback_query_handler_x(
    func=partial(filter_callback, pattern="^counseling::options::\\d*$"), bot=bot
)
def show_particular_counselor(callback: types.CallbackQuery, pattern: str) -> None:
    *_, counselor_id = callback.data.rsplit("::", maxsplit=1)
    counselor_id = int(counselor_id)
    button = buttons[pattern]
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


@callback_query_handler_x(
    func=partial(filter_callback, pattern="^counseling::options::\\d*::\\d{1,2}:\\d{1,2}$"),
    bot=bot,
)
def book_counseling(callback: types.CallbackQuery, pattern: str) -> None:
    *_, counselor_id, time = callback.data.rsplit("::", maxsplit=2)
    counselor_id = int(counselor_id)
    button = buttons[pattern]
    status = sql.book_counseling(
        counselor_id=counselor_id, user_id=callback.message.chat.id, time=time
    )
    button = button.success if status else button.failure
    edit_keyboard_message(callback, **button, bot=bot)


@callback_query_handler_x(func=partial(filter_callback, pattern="^counseling::my$"), bot=bot)
def show_my_counseling(callback: types.CallbackQuery, pattern: str) -> None:
    button = buttons[pattern]
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


@callback_query_handler_x(
    func=partial(filter_callback, pattern="^counseling::my::cancel$"), bot=bot
)
def cancel_counseling(callback: types.CallbackQuery, pattern: str) -> None:
    button = buttons[pattern]
    sql.cancel_counseling(callback.message.chat.id)
    edit_keyboard_message(callback, **button, bot=bot)


@callback_query_handler_x(func=partial(filter_callback, pattern="^seminars::options$"), bot=bot)
def show_seminars(callback: types.CallbackQuery, pattern: str) -> None:
    button = buttons[pattern]
    seminars = sql.get_seminars()
    children = []
    for seminar_id, title in seminars:
        children.append({"text": title, "data": f"{callback.data}::{seminar_id}"})
    children.extend(button.children)
    edit_keyboard_message(
        callback, reply=button.reply, row_width=button.row_width, children=children, bot=bot
    )


@callback_query_handler_x(
    func=partial(filter_callback, pattern="^seminars::options::\\d*$"), bot=bot
)
def show_particular_seminar(callback: types.CallbackQuery, pattern: str) -> None:
    *_, seminar_id = callback.data.rsplit("::", maxsplit=1)
    seminar_id = int(seminar_id)
    button = buttons[pattern]
    enroll, back = button.children
    title, description = sql.get_seminar_info(seminar_id)
    reply = button.reply.format(title=title, description=description)
    children = [{"text": enroll.text, "data": enroll.data.format(seminar_id=seminar_id)}, back]
    edit_keyboard_message(
        callback, reply=reply, row_width=button.row_width, children=children, bot=bot
    )


@callback_query_handler_x(
    func=partial(filter_callback, pattern="^seminars::options::\\d*::enroll$"), bot=bot
)
def choose_seminar_number(callback: types.CallbackQuery, pattern: str) -> None:
    *_, seminar_id, _ = callback.data.rsplit("::", maxsplit=2)
    button = buttons[pattern]
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


@callback_query_handler_x(
    func=partial(filter_callback, pattern="^seminars::options::\\d*::enroll::\\d$"), bot=bot
)
def enroll_for_seminar(callback: types.CallbackQuery, pattern: str) -> None:
    *_, seminar_id, _, seminar_number = callback.data.rsplit("::", maxsplit=3)
    button = buttons[pattern]
    sql.enroll_for_seminar(
        seminar_id=seminar_id, user_id=callback.message.chat.id, seminar_number=seminar_number
    )
    edit_keyboard_message(callback, **button, bot=bot)


@callback_query_handler_x(func=partial(filter_callback, pattern="^seminars::my$"), bot=bot)
def show_my_seminars(callback: types.CallbackQuery, pattern: str) -> None:
    button = buttons[pattern]
    template = button.reply.seminar_template
    (title1, desc1), (title2, desc2) = sql.get_my_seminars(callback.message.chat.id)
    seminar1 = template.format(title=title1, description=desc1) if title1 else button.reply.missing
    seminar2 = template.format(title=title2, description=desc2) if title2 else button.reply.missing
    reply = button.reply.template.format(seminar1=seminar1, seminar2=seminar2)
    cancel, back = button.children
    children = [cancel, back] if title1 or title2 else [back]
    edit_keyboard_message(
        callback, reply=reply, children=children, row_width=button.row_width, bot=bot
    )


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
