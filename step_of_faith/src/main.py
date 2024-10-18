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
buttons_yaml_file = "step_of_faith/resources/buttons.yaml"

with open(yaml_file, encoding="utf-8") as f:
    replies = yaml.safe_load(f)
with open(buttons_yaml_file, encoding="utf-8") as f:
    buttons = yaml.safe_load(f)

read = load_dotenv(env_file)
token = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(token)

logger = utils.get_logger(__name__)

sql = PostgreSQL()
user_utils = UserUtils(env_file)

# for callback data
waiting_for_question = []
waiting_for_feedback = []


def formation_text_of_schedule(schedule: object) -> str:
    result = buttons["schedule"]["reply"]
    for event in schedule:
        result += buttons["schedule"]["point"].format(time=str(event[0])[:5], event=event[1])
    return result


# function for create keyboard
def create_keyboard(button: object, columns: int) -> object:
    keyboard = types.InlineKeyboardMarkup(row_width=columns)
    _buttons = [
        types.InlineKeyboardButton(
            text=child["text"], callback_data=child.get("data"), url=child.get("url")
        )
        for child in button["children"]
    ]
    keyboard.add(*_buttons)
    return keyboard


# function edit keyboard message
def edit_keyboard_message(
    callback: types.CallbackQuery, button: object, reply: str | None, columns: int
) -> None:
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=reply if reply else button["reply"],
        reply_markup=create_keyboard(button, columns),
    )


# function send keyboard message
def send_keyboard_message(
    message: types.Message, button: object, reply: str | None, columns: int
) -> None:
    bot.send_message(
        message.chat.id,
        reply if reply else button["reply"],
        reply_markup=create_keyboard(button, columns),
    )


# function render message
def render_keyboard_message(
    data: types.CallbackQuery, button: object, reply: str | None = None, columns: int = 2
) -> None:
    arguments = (data, button, reply, columns)
    (
        send_keyboard_message(*arguments)
        if type(data) is types.Message
        else edit_keyboard_message(*arguments)
    )


# function show menu
def show_menu(callback: types.CallbackQuery) -> None:
    render_keyboard_message(callback, buttons["menu"], columns=2)


# function for show days
def schedule_menu(callback: types.CallbackQuery) -> None:
    render_keyboard_message(callback, buttons["schedule_menu"])


# function for show schedule
def show_schedule(callback: types.CallbackQuery, day: int) -> None:
    schedule = sql.get_schedule(day)
    schedule_text = formation_text_of_schedule(schedule)
    render_keyboard_message(callback, buttons["schedule"], reply=schedule_text)


# appointment menu
def appointment_menu(callback: types.CallbackQuery) -> None:
    render_keyboard_message(callback, buttons["appointment_menu"])


# make an counselor appointment
def show_counselors(callback: types.CallbackQuery) -> None:
    render_keyboard_message(callback, buttons["appointment"], columns=1)


# make an counselor appointment
def show_counselor(callback: types.CallbackQuery, counselor_id: str) -> None:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    times = sql.get_counselor_appointment_times(counselor_id)
    text = replies["counselors"][counselor_id]["name"] + "\n"
    replies["counselors"][counselor_id]["info"]
    _buttons = [
        types.InlineKeyboardButton(
            text=buttons["show_counselor"]["time"].format(time=str(time[0])[:5]),
            callback_data=f"write_appointment::{time[0]}::{counselor_id}",
        )
        for time in times
    ]
    keyboard.add(*_buttons)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=text,
        reply_markup=keyboard,
    )


# write_user_to_schedule_counselor_appointment
def write_to_appointment(callback: types.CallbackQuery, time: str, counselor_id: str) -> None:
    time = datetime.strptime(time, "%H:%M:%S").time()
    success = sql.write_user_to_schedule_counselor_appointment(
        counselor_id, time, callback.from_user.id
    )
    text = (
        buttons["completed"]["reply"]["success"]
        if success
        else buttons["completed"]["reply"]["unsuccess"]
    )
    render_keyboard_message(callback, buttons["completed"], reply=text)


# my_appointment
def my_appointment(callback: types.CallbackQuery) -> None:
    data = sql.get_user_counselor_appointment(callback.from_user.id)

    if not data:
        status = False
    else:
        status = True
        counselor_id, time = next(iter(data))

    text = [
        buttons["my_appointment"]["available"]["reply"].format(
            time=str(time)[:5],
            counselor_name=replies["counselors"][counselor_id]["name"],
            counselor_info=replies["counselors"][counselor_id]["info"],
        )
        if status
        else buttons["my_appointment"]["not_available"]["reply"]
    ]
    render_keyboard_message(
        callback, buttons["my_appointment"]["available" if status else "not_available"], reply=text
    )


# delete counselor appointment
def cancel_appointment(callback: types.CallbackQuery) -> None:
    sql.delete_user_from_schedule_counselor_appointment(callback.from_user.id)
    text = buttons["completed"]["reply"]["removed"]
    render_keyboard_message(callback, buttons["completed"], reply=text)


def seminars_menu(callback: types.CallbackQuery) -> None:
    render_keyboard_message(callback, buttons["seminars_menu"])


# function for show buttons of seminars
def show_seminars(callback: types.CallbackQuery) -> None:
    render_keyboard_message(callback, buttons["seminars"], columns=1)


# function for show seminar
def show_seminar(callback: types.CallbackQuery, seminar_id: str) -> None:
    text = f'{replies['seminars'][seminar_id]['name']} \n{replies['seminars'][seminar_id]['info']}'
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    _buttons = [
        types.InlineKeyboardButton(
            text=buttons["show_seminar"]["children"][0]["text"],
            callback_data=f"{buttons['show_seminar']['children'][0]['data']}{seminar_id}",
        ),
        types.InlineKeyboardButton(
            text=buttons["show_seminar"]["children"][1]["text"],
            callback_data=buttons["show_seminar"]["children"][1]["data"],
        ),
    ]
    keyboard.add(*_buttons)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=text,
        reply_markup=keyboard,
    )


# write to seminar
def write_to_seminar(callback: types.CallbackQuery, seminar_id: str) -> None:
    print("writing")
    sql.setup_seminar_for_user(callback.from_user.id, f"seminar::{seminar_id}")
    print("writed")
    render_keyboard_message(
        callback, buttons["completed"], reply=buttons["completed"]["reply"]["success"]
    )
    print("rendered")


# my seminar
def my_seminar(callback: types.CallbackQuery) -> None:
    data = sql.get_user_seminar(callback.from_user.id)
    text = ""

    if not data:
        status = False
        text = buttons["my_seminar"]["not_available"]["reply"]
    else:
        seminar_id = next(iter(data))
        if seminar_id == "NULL":
            status = True
            text = buttons["my_seminar"]["available"]["reply"].format(
                seminar=replies["seminars"][seminar_id]["name"]
            )
        else:
            status = False

    render_keyboard_message(
        callback, buttons["my_seminar"]["available" if status else "not_available"], reply=text
    )


# cancel seminar
def cancel_seminar(callback: types.CallbackQuery) -> None:
    sql.setup_seminar_for_user(callback.from_user.id, None)
    render_keyboard_message(
        callback, buttons["completed"], reply=buttons["completed"]["reply"]["removed"]
    )


# function for write question
def write_question(callback: types.CallbackQuery) -> None:
    if str(callback.from_user.id) not in waiting_for_question:
        waiting_for_question.append(str(callback.from_user.id))
    render_keyboard_message(callback, buttons["question"])


# function for write feedback
def write_feedback(callback: types.CallbackQuery) -> None:
    if str(callback.from_user.id) not in waiting_for_feedback:
        waiting_for_feedback.append(str(callback.from_user.id))
    render_keyboard_message(callback, buttons["feedback"])


# function send social network
def show_social_networks(callback: types.CallbackQuery) -> None:
    render_keyboard_message(callback, buttons["social_networks"])


# function send church schedule
def show_church_schedule(callback: types.CallbackQuery) -> None:
    render_keyboard_message(callback, buttons["church_schedule"])


# command cancel
def cancel(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    status = False

    if str(user_id) in waiting_for_question:
        waiting_for_question.remove(str(user_id))
        status = True

    elif str(user_id) in waiting_for_feedback:
        waiting_for_feedback.remove(str(user_id))
        status = True

    if status:
        render_keyboard_message(
            callback, buttons["completed"], reply=buttons["completed"]["reply"]["cancel"]
        )


# echo command
@bot.message_handler(regexp="^echo ")
def echo(message: types.Message) -> None:
    bot.send_message(message.from_user.id, message.text[5:])


# check for answer
@bot.message_handler(func=lambda message: str(message.from_user.id) in waiting_for_question)
def answer_for_question(message: types.Message) -> None:
    waiting_for_question.remove(str(message.from_user.id))
    sql.write_message("question", message.text)
    render_keyboard_message(
        message, buttons["completed"], reply=buttons["completed"]["reply"]["question"]
    )


# check for feedback
@bot.message_handler(func=lambda message: str(message.from_user.id) in waiting_for_feedback)
def answer_for_feedback(message: types.Message) -> None:
    waiting_for_feedback.remove(str(message.from_user.id))
    sql.write_message("feedback", message.text)
    render_keyboard_message(
        message, buttons["completed"], reply=buttons["completed"]["reply"]["feedback"]
    )


# command start
@bot.message_handler(commands=["start", "help", "menu"])
def menu(message: types.Message) -> None:
    if not sql.check_user_id(message.from_user.id):
        sql.add_to_database(message.from_user.id)
    current = sql.is_banned(message.from_user.id)
    if not current:
        render_keyboard_message(message, replies["welcome"])
    else:
        bot.send_message(message.from_user.id, replies["ban"]["banned"])


# check callback data
@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback: types.CallbackQuery) -> None:
    if callback.data == "menu":
        show_menu(callback)

    elif callback.data == "schedule_menu":
        schedule_menu(callback)
    elif callback.data.startswith("show_schedule::"):
        show_schedule(callback, int(callback.data.split("::")[1]))

    elif callback.data == "appointment_menu":
        appointment_menu(callback)
    elif callback.data == "show_counselors":
        show_counselors(callback)
    elif callback.data.startswith("show_counselor::"):
        counselor_id = callback.data.split("::")[1]
        show_counselor(callback, counselor_id)
    elif callback.data.startswith("write_appointment::"):
        time, counselor_id = list(callback.data.split("::")[1:])
        write_to_appointment(callback, time, counselor_id)
    elif callback.data == "my_appointment":
        my_appointment(callback)
    elif callback.data == "cancel_appointment":
        cancel_appointment(callback)

    elif callback.data == "seminars_menu":
        seminars_menu(callback)
    elif callback.data == "show_seminars":
        show_seminars(callback)
    elif callback.data.startswith("seminar::"):
        show_seminar(callback, callback.data.split("::")[1])
    elif callback.data.startswith("write_to_seminar::"):
        print(f"data: {callback.data}")
        write_to_seminar(callback, callback.data.split("::")[1])
    elif callback.data == "my_seminar":
        my_seminar(callback)
    elif callback.data == "cancel_seminar":
        cancel_seminar(callback, "None")

    elif callback.data == "question":
        write_question(callback)
    elif callback.data == "feedback":
        write_feedback(callback)
    elif callback.data == "cancel":
        cancel(callback)
    elif callback.data == "social_networks":
        show_social_networks(callback)
    elif callback.data == "church_schedule":
        show_church_schedule(callback)


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
