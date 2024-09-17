# step of faith telegram bot
import os

from dotenv import load_dotenv
import telebot
from telebot import types
import yaml

from common import utils
from step_of_faith import GoogleSheets
from step_of_faith import SQLite
from step_of_faith import UserUtils


read = load_dotenv("step_of_faith/.env")
token = os.getenv("BOT_TOKEN")
yaml_file = "step_of_faith/resources/replies.yaml"

with open(yaml_file, encoding="utf-8") as f:
    replies = yaml.safe_load(f)

bot = telebot.TeleBot(token)

logger = utils.get_logger(__name__)

sheets = GoogleSheets()

# for callback data
waiting_for_question = []
waiting_for_feedback = []
waiting_for_user_info = {}


# make an appointment with a counselor 1
def function_counselor_1(callback: types.CallbackQuery) -> None:
    waiting_for_user_info[str(callback.from_user.id)] = {"progress": 0, "counselor": 1}
    bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id)
    bot.send_message(
        callback.from_user.id, replies["button"]["appointment"]["counselor"]["first_name"]
    )


# make an appointment with a counselor 2
def function_counselor_2(callback: types.CallbackQuery) -> None:
    waiting_for_user_info[str(callback.from_user.id)] = {"progress": 0, "counselor": 2}
    bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id)
    bot.send_message(
        callback.from_user.id, replies["button"]["appointment"]["counselor"]["first_name"]
    )


# make an appointment with a counselor 3
def function_counselor_3(callback: types.CallbackQuery) -> None:
    waiting_for_user_info[str(callback.from_user.id)] = {"progress": 0, "counselor": 3}
    bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id)
    bot.send_message(
        callback.from_user.id, replies["button"]["appointment"]["counselor"]["first_name"]
    )


# make an appointment with a counselor 4
def function_counselor_4(callback: types.CallbackQuery) -> None:
    waiting_for_user_info[str(callback.from_user.id)] = {"progress": 0, "counselor": 4}
    bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id)
    bot.send_message(
        callback.from_user.id, replies["button"]["appointment"]["counselor"]["first_name"]
    )


# function show menu
def function_show_menu(callback: types.CallbackQuery) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn_schedule = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["schedule"], callback_data="func_schedule"
    )
    btn_appointment = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["appointment"], callback_data="func_appointment"
    )
    btn_question = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["question"], callback_data="func_question"
    )
    btn_feedback = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["feedback"], callback_data="func_feedback"
    )
    btn_social_networks = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["social_networks"], callback_data="func_social_networks"
    )
    btn_church_schedule = types.InlineKeyboardButton(
        text=replies["button"]["menu"]["church_schedule"], callback_data="func_church_schedule"
    )
    keyboard.add(
        btn_schedule,
        btn_appointment,
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


# function for getting schedule
def function_show_schedule(callback: types.CallbackQuery) -> None:
    schedule_text = sheets.get_schedule()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    cancel = types.InlineKeyboardButton(text=replies["button"]["cancel"], callback_data="func_menu")
    keyboard.add(cancel)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=schedule_text,
        reply_markup=keyboard,
    )


# function for make an appointment with a counselor
def function_make_appointment(callback: types.CallbackQuery) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    counselor_1_bnt = types.InlineKeyboardButton(
        text=replies["button"]["appointment"]["counselor_1"], callback_data="func_counselor_1"
    )
    counselor_2_bnt = types.InlineKeyboardButton(
        text=replies["button"]["appointment"]["counselor_2"], callback_data="func_counselor_2"
    )
    counselor_3_bnt = types.InlineKeyboardButton(
        text=replies["button"]["appointment"]["counselor_3"], callback_data="func_counselor_3"
    )
    counselor_4_bnt = types.InlineKeyboardButton(
        text=replies["button"]["appointment"]["counselor_4"], callback_data="func_counselor_4"
    )
    cancel = types.InlineKeyboardButton(text=replies["button"]["cancel"], callback_data="func_menu")
    keyboard.add(counselor_1_bnt, counselor_2_bnt, counselor_3_bnt, counselor_4_bnt, cancel)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=replies["button"]["appointment"]["text"],
        reply_markup=keyboard,
    )


# function for write question
def function_ask_question(callback: types.CallbackQuery) -> None:
    if str(callback.from_user.id) not in waiting_for_question:
        waiting_for_question.append(str(callback.from_user.id))
    bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id)
    bot.send_message(callback.from_user.id, replies["button"]["ask_question"]["text"])


# function for write feedback
def function_write_feedback(callback: types.CallbackQuery) -> None:
    if str(callback.from_user.id) not in waiting_for_feedback:
        waiting_for_feedback.append(str(callback.from_user.id))
    bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.id)
    bot.send_message(callback.from_user.id, replies["button"]["feedback"]["text"])


# function send social network
def function_show_social_networks(callback: types.CallbackQuery) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    telegram_btn = types.InlineKeyboardButton(
        text=replies["button"]["social_networks"]["telegram"],
        url=replies["button"]["social_networks"]["telegram_url"],
    )
    instagram_btn = types.InlineKeyboardButton(
        text=replies["button"]["social_networks"]["instagram"],
        url=replies["button"]["social_networks"]["instagram_url"],
    )
    cancel = types.InlineKeyboardButton(text=replies["button"]["cancel"], callback_data="func_menu")
    keyboard.add(telegram_btn, instagram_btn, cancel)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=replies["button"]["social_networks"]["text"],
        reply_markup=keyboard,
    )


# function send church schedule
def function_show_church_schedule(callback: types.CallbackQuery) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    cancel = types.InlineKeyboardButton(text=replies["button"]["cancel"], callback_data="func_menu")
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


# check for answer
@bot.message_handler(func=lambda message: str(message.from_user.id) in waiting_for_question)
def answer_for_question(message: types.Message) -> None:
    waiting_for_question.remove(str(message.from_user.id))
    sheets.write_question(message.text)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    back_to_menu_btn = types.InlineKeyboardButton(
        text=replies["button"]["back"], callback_data="func_menu"
    )
    keyboard.add(back_to_menu_btn)
    bot.send_message(
        message.from_user.id, replies["button"]["ask_question"]["success"], reply_markup=keyboard
    )


# check for feedback
@bot.message_handler(func=lambda message: str(message.from_user.id) in waiting_for_feedback)
def answer_for_feedback(message: types.Message) -> None:
    waiting_for_feedback.remove(str(message.from_user.id))
    sheets.write_feedback(message.text)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    back_to_menu_btn = types.InlineKeyboardButton(
        text=replies["button"]["back"], callback_data="func_menu"
    )
    keyboard.add(back_to_menu_btn)
    bot.send_message(
        message.from_user.id, replies["button"]["feedback"]["success"], reply_markup=keyboard
    )


# check for user info
@bot.message_handler(func=lambda message: str(message.from_user.id) in waiting_for_user_info)
def answer_for_user_info(message: types.Message) -> None:
    data = waiting_for_user_info[str(message.from_user.id)]
    if data["progress"] == 0:
        data["first_name"] = message.text
        data["progress"] = 1
        bot.send_message(
            message.from_user.id, replies["button"]["appointment"]["counselor"]["second_name"]
        )
    elif data["progress"] == 1:
        data["second_name"] = message.text
        data["progress"] = 2
        bot.send_message(
            message.from_user.id, replies["button"]["appointment"]["counselor"]["phone"]
        )
    elif data["progress"] == 2:
        data["phone"] = message.text
        sheets.write_to_talk(
            data["counselor"], [data["first_name"], data["second_name"], data["phone"]]
        )
        del waiting_for_user_info[str(message.from_user.id)]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        back_to_menu_btn = types.InlineKeyboardButton(
            text=replies["button"]["back"], callback_data="func_menu"
        )
        keyboard.add(back_to_menu_btn)
        bot.send_message(
            message.from_user.id,
            replies["button"]["appointment"]["counselor"]["success"],
            reply_markup=keyboard,
        )


# command cancel
@bot.message_handler(commands=["cancel"])
def cancel(message: telebot.types.Message) -> None:
    if str(message.from_user.id) in waiting_for_question:
        waiting_for_question.remove(str(message.from_user.id))
        text = replies["button"]["ask_question"]["cancel"]

    elif str(message.from_user.id) in waiting_for_feedback:
        waiting_for_feedback.remove(str(message.from_user.id))
        text = replies["button"]["feedback"]["cancel"]

    elif str(message.from_user.id) in waiting_for_user_info:
        del waiting_for_user_info[str(message.from_user.id)]
        text = replies["button"]["appointment"]["counselor"]["cancel"]

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    menu_btn = types.InlineKeyboardButton(text=replies["button"]["back"], callback_data="func_menu")
    keyboard.add(menu_btn)
    bot.send_message(message.from_user.id, text, reply_markup=keyboard)


# command start
@bot.message_handler(commands=["start", "help", "menu"])
def menu(message: telebot.types.Message) -> None:
    if not SQLite.check_user_id(message.from_user.id):
        SQLite.add_to_database(message.from_user.id, message.from_user.username)
    if not SQLite.is_banned(message.from_user.id):
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        menu_btn = types.InlineKeyboardButton(
            text=replies["button"]["menu"]["btn_text"], callback_data="func_menu"
        )
        keyboard.add(menu_btn)
        bot.send_message(message.from_user.id, replies["welcome"], reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, replies["ban"]["banned"])


# check callback data
@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback: types.CallbackQuery) -> None:
    if callback.data == "func_menu":
        function_show_menu(callback)
    elif callback.data == "func_schedule":
        function_show_schedule(callback)
    elif callback.data == "func_appointment":
        function_make_appointment(callback)
    elif callback.data == "func_question":
        function_ask_question(callback)
    elif callback.data == "func_feedback":
        function_write_feedback(callback)
    elif callback.data == "func_social_networks":
        function_show_social_networks(callback)
    elif callback.data == "func_church_schedule":
        function_show_church_schedule(callback)
    elif callback.data == "func_counselor_1":
        function_counselor_1(callback)
    elif callback.data == "func_counselor_2":
        function_counselor_2(callback)
    elif callback.data == "func_counselor_3":
        function_counselor_3(callback)
    elif callback.data == "func_counselor_4":
        function_counselor_4(callback)


# command ban
@bot.message_handler(regexp="^/ban ")
def ban(message: types.Message) -> None:
    if not SQLite.is_banned(message.from_user.id):
        if SQLite.is_admin(message.from_user.id):
            username = UserUtils.select_username_from_text(message.text[5:])
            completed = SQLite.change_ban_status(username, 1)
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
    if not SQLite.is_banned(message.from_user.id):
        if SQLite.is_admin(message.from_user.id):
            username = UserUtils.select_username_from_text(message.text[7:])
            completed = SQLite.change_ban_status(username, 0)
            if completed:
                bot.send_message(
                    message.from_user.id, replies["unban"]["success"].format(username=username)
                )
            else:
                bot.send_message(message.from_user.id, replies["unban"]["failure"])
    else:
        bot.send_message(message.from_user.id, replies["ban"]["banned"])


# RUN BOT
logger.info("START BOT...")
bot.polling()
