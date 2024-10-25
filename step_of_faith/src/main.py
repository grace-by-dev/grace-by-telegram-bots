# step of faith telegram bot
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


# function for show buttons of seminars
def show_seminars(callback: types.CallbackQuery) -> None:
    edit_keyboard_message(callback, buttons["show_seminars"], columns=1)


# # function for show seminar
# def show_seminar(callback: types.CallbackQuery, seminar_id: str) -> None:
# text = f'{buttons['seminars'][seminar_id]['name']} \n{buttons.seminars[seminar_id]['info']}'
#     keyboard = types.InlineKeyboardMarkup(row_width=2)
#     _buttons = [
#         types.InlineKeyboardButton(
#             text=buttons["show_seminar"]["children"][0]["text"],
#             callback_data=f"{buttons['show_seminar']['children'][0]['data']}{seminar_id}",
#         ),
#         types.InlineKeyboardButton(
#             text=buttons["show_seminar"]["children"][1]["text"],
#             callback_data=buttons["show_seminar"]["children"][1]["data"],
#         ),
#     ]
#     keyboard.add(*_buttons)
#     bot.edit_message_text(
#         chat_id=callback.message.chat.id,
#         message_id=callback.message.id,
#         text=text,
#         reply_markup=keyboard,
#     )


# # write to seminar
# def write_to_seminar(callback: types.CallbackQuery, seminar_id: str) -> None:
#     sql.setup_seminar_for_user(callback.from_user.id, seminar_id)
#     edit_keyboard_message(
#         callback, buttons["completed"], reply=buttons["completed"]["reply"]["success"]
#     )


# # my seminar
# def my_seminar(callback: types.CallbackQuery) -> None:
#     seminar_id = sql.get_user_seminar(callback.from_user.id)
#     text = ""

#     if not seminar_id:
#         status = False
#         text = buttons["my_seminar"]["not_available"]["reply"]
#     else:
#         status = True
#         text = buttons["my_seminar"]["available"]["reply"].format(
#             seminar=buttons["seminars"][seminar_id]["name"],
#             info=buttons["seminars"][seminar_id]["info"],
#         )

#     edit_keyboard_message(
#         callback, buttons["my_seminar"]["available" if status else "not_available"], reply=text
#     )


# # cancel seminar
# def cancel_seminar(callback: types.CallbackQuery) -> None:
#     sql.setup_seminar_for_user(callback.from_user.id, None)
#     edit_keyboard_message(
#         callback, buttons["completed"], reply=buttons["completed"]["reply"]["removed"]
#     )


# # function for write question
# def write_question(callback: types.CallbackQuery) -> None:
#     if str(callback.from_user.id) not in waiting_for_question:
#         waiting_for_question.append(str(callback.from_user.id))
#     edit_keyboard_message(callback, buttons["question"])


# # function for write feedback
# def write_feedback(callback: types.CallbackQuery) -> None:
#     if str(callback.from_user.id) not in waiting_for_feedback:
#         waiting_for_feedback.append(str(callback.from_user.id))
#     edit_keyboard_message(callback, buttons["feedback"])


# # function send social network
# def show_social_networks(callback: types.CallbackQuery) -> None:
#     edit_keyboard_message(callback, buttons["social_networks"])


# # function send church schedule
# def show_church_schedule(callback: types.CallbackQuery) -> None:
#     edit_keyboard_message(callback, buttons["church_schedule"])


# # command cancel
# def cancel(callback: types.CallbackQuery) -> None:
#     user_id = callback.from_user.id
#     status = False

#     if str(user_id) in waiting_for_question:
#         waiting_for_question.remove(str(user_id))
#         status = True

#     elif str(user_id) in waiting_for_feedback:
#         waiting_for_feedback.remove(str(user_id))
#         status = True

#     if status:
#         edit_keyboard_message(
#             callback, buttons["completed"], reply=buttons["completed"]["reply"]["cancel"]
#         )


# # echo command
# @bot.message_handler(regexp="^echo ")
# def echo(message: types.Message) -> None:
#     bot.send_message(message.from_user.id, message.text[5:])


# # check for answer
# @bot.message_handler(func=lambda message: str(message.from_user.id) in waiting_for_question)
# def answer_for_question(message: types.Message) -> None:
#     waiting_for_question.remove(str(message.from_user.id))
#     sql.write_message("question", message.text)
#     send_keyboard_message(
#         message, buttons["completed"], reply=buttons["completed"]["reply"]["question"]
#     )


# # check for feedback
# @bot.message_handler(func=lambda message: str(message.from_user.id) in waiting_for_feedback)
# def answer_for_feedback(message: types.Message) -> None:
#     waiting_for_feedback.remove(str(message.from_user.id))
#     sql.write_message("feedback", message.text)
#     send_keyboard_message(
#         message, buttons["completed"], reply=buttons["completed"]["reply"]["feedback"]
#     )


@bot.message_handler(commands=["start", "help", "menu"])
def menu(message: types.Message) -> None:
    if not sql.check_user_id(message.from_user.id):
        sql.add_to_database(message.from_user.id)
    current = sql.is_banned(message.from_user.id)
    if not current:
        send_keyboard_message(message, **replies["welcome"], bot=bot)
    else:
        bot.send_message(message.from_user.id, replies["ban"]["banned"])


# # check callback data
# @bot.callback_query_handler(func=lambda callback: callback.data)
# def check_callback_data(callback: types.CallbackQuery) -> None:
#     if callback.data == "menu":
#         show_menu(callback)

#     elif callback.data == "schedule_menu":
#         schedule_menu(callback)
#     elif callback.data.startswith("show_schedule::"):
#         show_schedule(callback, int(callback.data.split("::")[1]))

#     elif callback.data == "appointment_menu":
#         appointment_menu(callback)
#     elif callback.data == "show_counselors":
#         show_counselors(callback)
#     elif callback.data.startswith("show_counselor::"):
#         counselor_id = callback.data.split("::")[1]
#         show_counselor(callback, counselor_id)
#     elif callback.data.startswith("write_appointment::"):
#         time, counselor_id = list(callback.data.split("::")[1:])
#         write_to_appointment(callback, time, counselor_id)
#     elif callback.data == "my_appointment":
#         my_appointment(callback)
#     elif callback.data == "cancel_appointment":
#         cancel_appointment(callback)

#     elif callback.data == "seminars_menu":
#         seminars_menu(callback)
#     elif callback.data == "show_seminars":
#         show_seminars(callback)
#     elif callback.data.startswith("seminar::"):
#         show_seminar(callback, callback.data.split("::")[1])
#     elif callback.data.startswith("write_to_seminar::"):
#         write_to_seminar(callback, callback.data.split("::")[1])
#     elif callback.data == "my_seminar":
#         my_seminar(callback)
#     elif callback.data == "cancel_seminar":
#         cancel_seminar(callback)

#     elif callback.data == "question":
#         write_question(callback)
#     elif callback.data == "feedback":
#         write_feedback(callback)
#     elif callback.data == "cancel":
#         cancel(callback)
#     elif callback.data == "social_networks":
#         show_social_networks(callback)
#     elif callback.data == "church_schedule":
#         show_church_schedule(callback)


# RUN BOT
if __name__ == "__main__":
    logger.info("START BOT...")
    bot.infinity_polling()
