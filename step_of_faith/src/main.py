# step of faith telegram bot
from datetime import datetime
import os

from dotenv import load_dotenv
import telebot
from telebot import types
import yaml

from common import utils
from step_of_faith.src.postgres_sql import PostgreSQL
from step_of_faith.src.user_utils import UserUtils


env_file = "step_of_faith/.env"
yaml_file = "step_of_faith/resources/replies.yaml"


read = load_dotenv(env_file)
token = os.getenv("BOT_TOKEN")

with open(yaml_file, encoding="utf-8") as f:
    replies = yaml.safe_load(f)

bot = telebot.TeleBot(token)

logger = utils.get_logger(__name__)

sql = PostgreSQL()
user_utils = UserUtils(env_file, yaml_file)

# for callback data
waiting_for_question = []
waiting_for_feedback = []

# seminar list
seminars = [
    "seminar_1",
    "seminar_2",
    "seminar_3",
    "seminar_4",
    "seminar_5",
    "seminar_6",
    "seminar_7",
    "seminar_8",
]


# function show menu
def show_menu(callback: types.CallbackQuery) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn_schedule = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["schedule"], callback_data="show_days"
    )
    btn_appointment = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["appointment"], callback_data="counselor_appointment"
    )
    btn_seminar_registration = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["seminar"], callback_data="seminar_registration"
    )
    btn_question = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["question"], callback_data="question"
    )
    btn_feedback = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["feedback"], callback_data="feedback"
    )
    btn_social_networks = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["social_networks"], callback_data="social_networks"
    )
    btn_church_schedule = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["church_schedule"], callback_data="church_schedule"
    )
    keyboard.add(
        btn_schedule,
        btn_appointment,
        btn_seminar_registration,
        btn_question,
        btn_feedback,
        btn_social_networks,
        btn_church_schedule,
    )
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=replies["button"]["menu"]["text"],
        reply_markup=keyboard,
    )


# function for show days
def show_days(callback: types.CallbackQuery) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn_first_day = types.InlineKeyboardButton(
        text=replies["button"]["schedule"]["days"]["first"],
        callback_data="show_first_day_schedule",
    )
    btn_second_day = types.InlineKeyboardButton(
        text=replies["button"]["schedule"]["days"]["second"],
        callback_data="show_second_day_schedule",
    )
    cancel = types.InlineKeyboardButton(text=replies["button"]["cancel"], callback_data="menu")
    keyboard.add(btn_first_day, btn_second_day, cancel)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=replies["button"]["schedule"]["days"]["text"],
        reply_markup=keyboard,
    )


# function for show schedule
def show_schedule(callback: types.CallbackQuery, day: int) -> None:
    schedule = sql.get_schedule(day)
    schedule_text = user_utils.formation_text_of_schedule(schedule)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    cancel = types.InlineKeyboardButton(text=replies["button"]["cancel"], callback_data="show_days")
    keyboard.add(cancel)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=schedule_text,
        reply_markup=keyboard,
    )


# appointment menu
def counselor_appointment_menu(callback: types.CallbackQuery) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    make_an_appointment_btn = types.InlineKeyboardButton(
        text=replies["button"]["make_an_appointment"],
        callback_data="show_counselors",
    )
    appointment_status = types.InlineKeyboardButton(
        text=replies["button"]["appointment"]["my_appointment"],
        callback_data="my_appointment",
    )
    cancel = types.InlineKeyboardButton(text=replies["button"]["cancel"], callback_data="menu")
    keyboard.add(make_an_appointment_btn, appointment_status, cancel)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=replies["button"]["appointment"]["text"],
        reply_markup=keyboard,
    )


# make an counselor appointment
def show_counselors(callback: types.CallbackQuery) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    counselors = sql.get_counselors()
    for counselor in counselors:
        counselor_btn = types.InlineKeyboardButton(
            text=replies["button"]["appointment"][f"counselor_{counselor}"]["name"],
            callback_data=f"show_counselor::{counselor}",
        )
        keyboard.add(counselor_btn)
    cancel = types.InlineKeyboardButton(
        text=replies["button"]["cancel"], callback_data="counselor_appointment"
    )
    keyboard.add(cancel)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=replies["button"]["appointment"]["text"],
        reply_markup=keyboard,
    )


# make an counselor appointment
def show_counselor(callback: types.CallbackQuery, counselor_id: str) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    times = sql.get_counselor_appointment_times(counselor_id)
    for time in times:
        time_btn = types.InlineKeyboardButton(
            text=replies["button"]["clock"] + str(time[0])[:5],
            callback_data=f"write_appointment::{time[0]}::{counselor_id}",
        )
        keyboard.add(time_btn)
    cancel = types.InlineKeyboardButton(
        text=replies["button"]["cancel"], callback_data="show_counselors"
    )
    keyboard.add(cancel)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=replies["button"]["appointment"]["text"],
        reply_markup=keyboard,
    )


# write_user_to_schedule_counselor_appointment
def write_user_to_schedule_counselor_appointment(
    callback: types.CallbackQuery, time: str, counselor_id: str
) -> None:
    time = datetime.strptime(time, "%H:%M:%S").time()
    success = sql.write_user_to_schedule_counselor_appointment(
        counselor_id, time, callback.from_user.id
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    menu_btn = types.InlineKeyboardButton(text=replies["button"]["back"], callback_data="menu")
    keyboard.add(menu_btn)
    if success:
        text = replies["button"]["writing_success"]
    else:
        text = replies["button"]["writing_unsuccess"]
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=text,
        reply_markup=keyboard,
    )


# my_appointment
def my_appointment(callback: types.CallbackQuery) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    cancel = types.InlineKeyboardButton(
        text=replies["button"]["cancel"], callback_data="counselor_appointment"
    )
    data = sql.get_user_counselor_appointment(callback.from_user.id)

    if not data:
        status = False
    else:
        status = True
        counselor_id, time = next(iter(data))

    if status:
        text = replies["button"]["appointment"]["appointment_info"].format(
            counselor_name=replies["button"]["appointment"][f"counselor_{counselor_id}"]["name"],
            time=str(time)[:5],
            info_about_counselor=replies["button"]["appointment"][f"counselor_{counselor_id}"][
                "info"
            ],
        )
        cancel_appointment_btn = types.InlineKeyboardButton(
            text=replies["button"]["delete_appointment"], callback_data="cancel_appointment"
        )
        keyboard.add(cancel_appointment_btn, cancel)
    else:
        text = replies["button"]["appointment"]["not_appointment_info"]
        keyboard.add(cancel)

    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=text,
        reply_markup=keyboard,
    )


# delete counselor appointment
def delete_counselor_appointment(callback: types.CallbackQuery) -> None:
    sql.delete_user_from_schedule_counselor_appointment(callback.from_user.id)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    cancel = types.InlineKeyboardButton(text=replies["button"]["back"], callback_data="menu")
    keyboard.add(cancel)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=replies["button"]["appointment_removed"],
        reply_markup=keyboard,
    )


# function for show buttons of seminars
def show_seminars(callback: types.CallbackQuery) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for seminar in seminars:
        seminar_btn = types.InlineKeyboardButton(
            text=replies["button"]["seminar"][seminar]["name"],
            callback_data=seminar.replace("_", "::"),
        )
        keyboard.add(seminar_btn)
    cancel = types.InlineKeyboardButton(
        text=replies["button"]["delete_appointment"], callback_data="seminar::None"
    )
    back = types.InlineKeyboardButton(text=replies["button"]["cancel"], callback_data="menu")
    keyboard.add(cancel, back)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=replies["button"]["seminar"]["text"],
        reply_markup=keyboard,
    )


def set_seminar_for_user(callback: types.CallbackQuery, seminar_id: str) -> None:
    if seminar_id == "None":
        seminar_id = None
    sql.setup_seminar_for_user(
        callback.from_user.id,
        [replies["button"]["seminar"][f"seminar_{seminar_id}"]["name"] if seminar_id else None],
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    menu_btn = types.InlineKeyboardButton(text=replies["button"]["back"], callback_data="menu")
    keyboard.add(menu_btn)
    if seminar_id:
        text = replies["button"]["writing_success"]
    else:
        text = replies["button"]["appointment_removed"]
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=text,
        reply_markup=keyboard,
    )


# function for write question
def write_question(callback: types.CallbackQuery) -> None:
    if str(callback.from_user.id) not in waiting_for_question:
        waiting_for_question.append(str(callback.from_user.id))
    bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id)
    bot.send_message(callback.from_user.id, replies["button"]["ask_question"]["text"])


# function for write feedback
def write_feedback(callback: types.CallbackQuery) -> None:
    if str(callback.from_user.id) not in waiting_for_feedback:
        waiting_for_feedback.append(str(callback.from_user.id))
    bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id)
    bot.send_message(callback.from_user.id, replies["button"]["feedback"]["text"])


# function send social network
def show_social_networks(callback: types.CallbackQuery) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    telegram_btn = types.InlineKeyboardButton(
        text=replies["button"]["social_networks"]["telegram"],
        url=replies["button"]["social_networks"]["telegram_url"],
    )
    instagram_btn = types.InlineKeyboardButton(
        text=replies["button"]["social_networks"]["instagram"],
        url=replies["button"]["social_networks"]["instagram_url"],
    )
    cancel = types.InlineKeyboardButton(text=replies["button"]["cancel"], callback_data="menu")
    keyboard.add(telegram_btn, instagram_btn, cancel)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=replies["button"]["social_networks"]["text"],
        reply_markup=keyboard,
    )


# function send church schedule
def show_church_schedule(callback: types.CallbackQuery) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    cancel = types.InlineKeyboardButton(text=replies["button"]["cancel"], callback_data="menu")
    keyboard.add(cancel)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=replies["button"]["church_schedule"]["text"],
        reply_markup=keyboard,
    )


# echo command
@bot.message_handler(regexp="^echo ")
def echo(message: types.Message) -> None:
    bot.send_message(message.from_user.id, message.text[5:])


# command cancel
@bot.message_handler(commands=["cancel"])
def cancel(message: telebot.types.Message) -> None:
    text = None
    if str(message.from_user.id) in waiting_for_question:
        waiting_for_question.remove(str(message.from_user.id))
        text = replies["button"]["ask_question"]["cancel"]

    elif str(message.from_user.id) in waiting_for_feedback:
        waiting_for_feedback.remove(str(message.from_user.id))
        text = replies["button"]["feedback"]["cancel"]

    if text is not None:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        menu_btn = types.InlineKeyboardButton(text=replies["button"]["back"], callback_data="menu")
        keyboard.add(menu_btn)
        bot.send_message(message.from_user.id, text, reply_markup=keyboard)


# check for answer
@bot.message_handler(func=lambda message: str(message.from_user.id) in waiting_for_question)
def answer_for_question(message: types.Message) -> None:
    waiting_for_question.remove(str(message.from_user.id))
    sql.write_message("question", message.text)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    back_to_menu_btn = types.InlineKeyboardButton(
        text=replies["button"]["back"], callback_data="menu"
    )
    keyboard.add(back_to_menu_btn)
    bot.send_message(
        message.from_user.id, replies["button"]["ask_question"]["success"], reply_markup=keyboard
    )


# check for feedback
@bot.message_handler(func=lambda message: str(message.from_user.id) in waiting_for_feedback)
def answer_for_feedback(message: types.Message) -> None:
    waiting_for_feedback.remove(str(message.from_user.id))
    sql.write_message("feedback", message.text)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    back_to_menu_btn = types.InlineKeyboardButton(
        text=replies["button"]["back"], callback_data="menu"
    )
    keyboard.add(back_to_menu_btn)
    bot.send_message(
        message.from_user.id, replies["button"]["feedback"]["success"], reply_markup=keyboard
    )


# command start
@bot.message_handler(commands=["start", "help", "menu"])
def menu(message: telebot.types.Message) -> None:
    if not sql.check_user_id(message.from_user.id):
        sql.add_to_database(message.from_user.id)
    current = sql.is_banned(message.from_user.id)
    if not current:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        menu_btn = types.InlineKeyboardButton(
            text=replies["button"]["menu"]["btn_text"], callback_data="menu"
        )
        keyboard.add(menu_btn)
        bot.send_message(message.from_user.id, replies["welcome"], reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, replies["ban"]["banned"])


# check callback data
@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback: types.CallbackQuery) -> None:
    if callback.data == "menu":
        show_menu(callback)
    elif callback.data == "show_days":
        show_days(callback)
    elif callback.data == "show_first_day_schedule":
        show_schedule(callback, 1)
    elif callback.data == "show_second_day_schedule":
        show_schedule(callback, 2)
    elif callback.data == "counselor_appointment":
        counselor_appointment_menu(callback)
    elif callback.data == "seminar_registration":
        show_seminars(callback)
    elif callback.data.startswith("seminar::"):
        set_seminar_for_user(callback, callback.data.split("::")[1])
    elif callback.data == "question":
        write_question(callback)
    elif callback.data == "feedback":
        write_feedback(callback)
    elif callback.data == "social_networks":
        show_social_networks(callback)
    elif callback.data == "church_schedule":
        show_church_schedule(callback)
    elif callback.data == "show_counselors":
        show_counselors(callback)
    elif callback.data.startswith("show_counselor::"):
        counselor_id = callback.data.split("::")[1]
        show_counselor(callback, counselor_id)
    elif callback.data.startswith("write_appointment::"):
        time, counselor_id = list(callback.data.split("::")[1:])
        write_user_to_schedule_counselor_appointment(callback, time, counselor_id)
    elif callback.data == "my_appointment":
        my_appointment(callback)
    elif callback.data == "cancel_appointment":
        delete_counselor_appointment(callback)


# command ban
@bot.message_handler(regexp="^/ban ")
def ban(message: types.Message) -> None:
    if not sql.is_banned(message.from_user.id):
        if sql.is_admin(message.from_user.id):
            username = user_utils.select_username_from_text(message.text[5:])
            completed = sql.change_ban_status(username, 1)
            if completed:
                bot.send_message(
                    message.from_user.id, replies["ban"]["success"].format(username=username)
                )
            else:
                bot.send_message(message.from_user.id, replies["ban"]["failure"])
    else:
        bot.send_message(message.from_user.id, replies["ban"]["banned"])


# command ban
@bot.message_handler(regexp="^/unban ")
def unban(message: types.Message) -> None:
    if not sql.is_banned(message.from_user.id):
        if sql.is_admin(message.from_user.id):
            username = user_utils.select_username_from_text(message.text[7:])
            completed = sql.change_ban_status(username, 0)
            if completed:
                bot.send_message(
                    message.from_user.id, replies["unban"]["success"].format(username=username)
                )
            else:
                bot.send_message(message.from_user.id, replies["unban"]["failure"])
    else:
        bot.send_message(message.from_user.id, replies["ban"]["banned"])


# RUN BOT
if __name__ == "__main__":
    logger.info("START BOT...")
    bot.infinity_polling()
