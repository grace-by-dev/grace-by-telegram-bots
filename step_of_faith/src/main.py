from datetime import datetime
from enum import Enum
import os
import re

from dotenv import load_dotenv
from omegaconf import DictConfig
from omegaconf import OmegaConf
import pytz
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

TZ = pytz.timezone(os.getenv("TIMEZONE"))

logger = get_logger(__name__)

db = PostgreSQL()
user_utils = UserUtils(env_file)

MIN_BOOKING_TIME = int(os.getenv("MIN_BOOKING_TIME"))


class TimediffCheckStatus(Enum):
    success = 1
    passed = 2
    too_close = 3


def validate_timediff(time: datetime) -> bool:
    now = datetime.now(TZ)
    timediff = (
        ((time.hour - now.hour) * 60 + time.minute - now.minute) * 60 + time.second - now.second
    )
    if timediff < 0:
        return TimediffCheckStatus.passed
    elif timediff < MIN_BOOKING_TIME:
        return TimediffCheckStatus.too_close
    else:
        return TimediffCheckStatus.success


def show_schedule_day(callback: types.CallbackQuery, button: DictConfig, day: int) -> None:
    schedule = db.get_schedule(day)
    day_text = "четверг" if day == "1" else "пятница"
    schedule = [
        button.reply.row_template.format(time=time.strftime("%H:%M"), event=event)
        for (time, event) in schedule
    ]
    schedule = "\n".join([button.reply.header.format(day=day_text), *schedule])
    edit_keyboard_message(
        callback, reply=schedule, row_width=button.row_width, children=button.children, bot=bot
    )


def show_counselors(callback: types.CallbackQuery, button: DictConfig) -> None:
    counselors = db.get_counselors()
    children = []
    for counselor_id, name in counselors:
        children.append({"text": name, "data": f"{callback.data}::{counselor_id}"})
    children.extend(button.children)
    edit_keyboard_message(
        callback, reply=button.reply, row_width=button.row_width, children=children, bot=bot
    )


def show_particular_counselor(
    callback: types.CallbackQuery, button: DictConfig, counselor_id: int
) -> None:
    name, place = db.get_counselor_info(counselor_id)
    timeslots = db.get_counselor_timeslots(counselor_id)
    children = []
    for (slot,) in timeslots:
        if validate_timediff(slot) == TimediffCheckStatus.success:
            time = slot.strftime("%H:%M")
            children.append(
                {
                    "text": button.child_template.format(time=time),
                    "data": f"{callback.data}::{time}",
                }
            )
    reply = button.reply.format(name=name, n=len(children), place=place)
    children.extend(button.children)
    edit_keyboard_message(
        callback, reply=reply, row_width=button.row_width, children=children, bot=bot
    )


def book_counseling(
    callback: types.CallbackQuery, button: DictConfig, counselor_id: int, time: str
) -> None:
    time = datetime.strptime(time, "%H:%M").time()
    match validate_timediff(time):
        case TimediffCheckStatus.too_close:
            button = button.too_close
            edit_keyboard_message(
                callback,
                button.reply.format(minutes=MIN_BOOKING_TIME),
                button.row_width,
                button.children,
                bot=bot,
            )
        case TimediffCheckStatus.passed:
            edit_keyboard_message(callback, **button.passed, bot=bot)
        case TimediffCheckStatus.success:
            booking = db.get_my_counseling(user_id=callback.message.chat.id)
            match booking:
                case None:
                    status = db.book_counseling(
                        counselor_id=counselor_id, user_id=callback.message.chat.id, time=time
                    )
                    button = button.success if status else button.too_slow
                    edit_keyboard_message(callback, **button, bot=bot)
                case *_, old_time, _:
                    match validate_timediff(old_time):
                        case TimediffCheckStatus.too_close:
                            button = button.booking_too_close
                            edit_keyboard_message(
                                callback,
                                button.reply.format(minutes=MIN_BOOKING_TIME),
                                button.row_width,
                                button.children,
                                bot=bot,
                            )
                        case TimediffCheckStatus.passed:
                            edit_keyboard_message(callback, **button.booking_passed, bot=bot)
                        case TimediffCheckStatus.success:
                            status = db.book_counseling(
                                counselor_id=counselor_id,
                                user_id=callback.message.chat.id,
                                time=time,
                            )
                            button = button.success if status else button.too_slow
                            edit_keyboard_message(callback, **button, bot=bot)


def show_my_counseling(callback: types.CallbackQuery, button: DictConfig) -> None:
    booking = db.get_my_counseling(user_id=callback.message.chat.id)
    if booking:
        name, time, place = booking
        time = time.strftime("%H:%M")
        button = button.exists
        reply = button.reply.format(name=name, time=time, place=place)
        edit_keyboard_message(
            callback, reply=reply, row_width=button.row_width, children=button.children, bot=bot
        )
    else:
        edit_keyboard_message(callback, **button.missing, bot=bot)


def cancel_counseling(callback: types.CallbackQuery, button: DictConfig) -> None:
    _, time, _ = db.get_my_counseling(user_id=callback.message.chat.id)
    if validate_timediff(time):
        reply = button.reply.success
        db.cancel_counseling(callback.message.chat.id)
    else:
        reply = button.reply.failure
    edit_keyboard_message(
        callback, children=button.children, reply=reply, row_width=button.row_width, bot=bot
    )


def choose_seminar_action(
    callback: types.CallbackQuery, button: DictConfig, seminar_number: int
) -> None:
    reply = button.first if seminar_number == "1" else button.second
    enroll, check_enrollement, back = button.children
    children = [
        {"text": enroll.text, "data": enroll.data.format(seminar_number=seminar_number)},
        {
            "text": check_enrollement.text,
            "data": check_enrollement.data.format(seminar_number=seminar_number),
        },
        back,
    ]
    edit_keyboard_message(
        callback, reply=reply, row_width=button.row_width, children=children, bot=bot
    )


def show_seminar_options(
    callback: types.CallbackQuery, button: DictConfig, seminar_number: int
) -> None:
    seminars = db.get_seminars(seminar_number)
    children = []
    back = button.children[0]
    for seminar_id, title in seminars:
        children.append({"text": title, "data": f"{callback.data}::{seminar_id}"})
    children.append({"text": back.text, "data": back.data.format(seminar_number=seminar_number)})
    edit_keyboard_message(
        callback, reply=button.reply, row_width=button.row_width, children=children, bot=bot
    )


def show_particular_seminar(
    callback: types.CallbackQuery, button: DictConfig, seminar_number: int, seminar_id: int
) -> None:
    enroll, back = button.children
    title, description, speaker = db.get_seminar_info(seminar_id)
    reply = button.reply.format(
        title=title, speaker=speaker, description=description.replace("<endl>", "\n")
    )
    children = [
        {
            "text": enroll.text,
            "data": enroll.data.format(seminar_id=seminar_id, seminar_number=seminar_number),
        },
        {"text": back.text, "data": back.data.format(seminar_number=seminar_number)},
    ]
    edit_keyboard_message(
        callback, reply=reply, row_width=button.row_width, children=children, bot=bot
    )


def enroll_for_seminar(
    callback: types.CallbackQuery, button: DictConfig, seminar_number: int, seminar_id: int
) -> None:
    seminar_id = int(seminar_id)
    match validate_timediff(db.get_seminar_start_time(seminar_number)):
        case TimediffCheckStatus.too_close:
            button = button.too_close
            edit_keyboard_message(
                callback,
                button.reply.format(minutes=MIN_BOOKING_TIME),
                button.row_width,
                button.children,
                bot=bot,
            )
        case TimediffCheckStatus.passed:
            edit_keyboard_message(callback, **button.passed, bot=bot)
        case TimediffCheckStatus.success:
            status = db.enroll_for_seminar(
                seminar_id=seminar_id,
                user_id=callback.message.chat.id,
                seminar_number=seminar_number,
            )
            button = button.success if status else button.room_failure
            edit_keyboard_message(callback, **button, bot=bot)


def show_my_seminar(callback: types.CallbackQuery, button: DictConfig, seminar_number: int) -> None:
    title, description, speaker = db.get_my_seminar(
        seminar_number,
        callback.message.chat.id,
    )
    cancel, back = button.children
    children = []
    if title:
        reply = button.reply.exists.format(
            title=title, description=description.replace("<endl>", "\n"), speaker=speaker
        )
        children.append(
            {"text": cancel.text, "data": cancel.data.format(seminar_number=seminar_number)}
        )
    else:
        reply = button.reply.missing.format(
            number_text="первый" if seminar_number == "1" else "второй"
        )
    children.append({"text": back.text, "data": back.data.format(seminar_number=seminar_number)})
    edit_keyboard_message(
        callback, reply=reply, children=children, row_width=button.row_width, bot=bot
    )


def cancel_my_seminar(callback: types.CallbackQuery, button: DictConfig, seminar_num: int) -> None:
    time = db.get_seminar_start_time(seminar_num)
    match validate_timediff(time):
        case TimediffCheckStatus.too_close:
            button = button.too_close
            edit_keyboard_message(
                callback,
                button.reply.format(minutes=MIN_BOOKING_TIME),
                button.row_width,
                button.children,
                bot=bot,
            )
        case TimediffCheckStatus.passed:
            edit_keyboard_message(callback, **button.passed, bot=bot)
        case TimediffCheckStatus.success:
            db.cancel_my_seminar(callback.message.chat.id, seminar_num)
            edit_keyboard_message(callback, **button.success, bot=bot)


def show_basic_button(callback: types.CallbackQuery, button: DictConfig) -> None:
    edit_keyboard_message(callback, **button, bot=bot)


@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback: types.CallbackQuery) -> None:
    static_callbacks_dict = {
        "menu": show_basic_button,
        "schedule": show_basic_button,
        "counseling": show_basic_button,
        "seminars": show_basic_button,
        "subscribe": show_basic_button,
        "church_schedule": show_basic_button,
        "counseling::options": show_counselors,
        "counseling::my": show_my_counseling,
        "counseling::my::cancel": cancel_counseling,
        "feedback": show_basic_button,
    }
    if callback.data in static_callbacks_dict:
        static_callbacks_dict[callback.data](callback, buttons[f"^{callback.data}$"])
    else:
        dinamic_callback_patterns = [
            ("^schedule::day::(\\d+)$", show_schedule_day),
            ("^counseling::options::(\\d+)$", show_particular_counselor),
            ("^counseling::options::(\\d+)::(\\d{1,2}:\\d{1,2})$", book_counseling),
            ("^seminars::(\\d+)$", choose_seminar_action),
            ("^seminars::(\\d+)::options$", show_seminar_options),
            ("^seminars::(\\d+)::options::(\\d+)$", show_particular_seminar),
            ("^seminars::(\\d+)::options::(\\d+)::enroll$", enroll_for_seminar),
            ("^seminars::(\\d+)::my$", show_my_seminar),
            ("^seminars::(\\d+)::my::cancel$", cancel_my_seminar),
        ]
        for pattern, func in dinamic_callback_patterns:
            match = re.search(pattern, callback.data)
            if match is not None:
                func(callback, buttons[pattern], *match.groups())
                break
        else:
            print("missed")


@bot.message_handler(commands=["start"])
def menu(message: types.Message) -> None:
    if not db.check_user_id(message.from_user.id):
        db.add_to_database(message.from_user.id, message.from_user.username)
    send_keyboard_message(message, **buttons["^menu$"], bot=bot)


if __name__ == "__main__":
    logger.info("START BOT...")
    bot.infinity_polling()
