# HOME OF UNITY BOT
import os
import random
import sqlite3
from typing import Literal
from typing import Tuple

from dotenv import load_dotenv
import telebot
import yaml

from common import utils
import config
from homechurch import Role
from homechurch import UserUtils


read = load_dotenv("homechurch/.env")
token = os.getenv("TOKEN")
database_file = "homechurch/data.db"
yaml_file = "homechurch/resources/replies.yaml"

with open(yaml_file, encoding="utf-8") as f:
    replies = yaml.safe_load(f)

bot = telebot.TeleBot(token)

logger = utils.get_logger(__name__)

user_utils = UserUtils(database_file)


# adding data of user to database
def add_to_database(user_id: int, username: str) -> None:
    with sqlite3.connect(database_file) as cursor:
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, 0, Role.DEFAULT.value, "empty", 0, "empty", "empty", 0),
        )
    logger.info(f"user {user_id} added to the database")
    send_message_to_specific_category_users(
        replies["start"]["notification"].format(username=username),
        Role.ADMIN.value,
        user_id,
    )


# get username from text
def get_username_from_text(text: str) -> str:
    username = []

    for i in text:
        if i != " ":
            username.append(i)
        elif i == " ":
            break

    return "".join(username)


# select username and role from text
def get_username_and_role_from_text(text: str) -> Tuple[str, int] | Literal[False]:
    username = []
    one = True
    level = 0

    for i in text:
        if i != " " and one:
            username.append(i)
        elif i == " ":
            one = False
        else:
            try:
                level = int(i)
            except ValueError as e:
                logger.debug(e)

    if level >= Role.DEFAULT.value and level <= Role.DEV.value:
        username = "".join(username)
        return username, level
    else:
        return False


# get random text from the databse
def get_random_text() -> str:
    with sqlite3.connect(database_file) as cursor:
        texts = cursor.execute("SELECT text FROM texts")
    texts_list = [text[0] for text in texts]
    random_text_id = random.randint(0, len(texts_list) - 1)
    return str(texts_list[random_text_id])


# notifications of baned user try use bot
def is_banned(user_id: int) -> bool:
    with sqlite3.connect(database_file) as cursor:
        ban = cursor.execute("SELECT ban FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
    if ban:
        bot.send_message(user_id, replies["is_banned"])
    return ban


# check role of user
def get_user_role(user_id: int) -> int | Literal[False]:
    with sqlite3.connect(database_file) as cursor:
        info = cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if info is None:
        return False
    else:
        return info[0]


# get user id from username
def get_id_using_username(username: int) -> int:
    with sqlite3.connect(database_file) as cursor:
        info = cursor.execute(
            "SELECT user_id FROM users WHERE username = ?", (username,)
        ).fetchone()
    if info is None:
        return False
    else:
        return info[0]


# send a message to a specific category of users
def send_message_to_specific_category_users(text: str, necessary_role: int, sender: int) -> int:
    count = 0
    with sqlite3.connect(database_file) as cursor:
        users = cursor.execute("SELECT user_id FROM users WHERE role >= ?", (necessary_role,))
    for user in users:
        if user[0] != str(sender):
            try:
                bot.send_message(user[0], text)
                count += 1
            except telebot.apihelper.ApiTelegramException as e:
                logger.error(e)
    return count


# COMMAND START
@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message) -> None:
    if not user_utils.check_user_id(message.from_user.id):
        add_to_database(message.from_user.id, message.from_user.username)

    if not is_banned(message.from_user.id):
        bot.send_message(message.from_user.id, replies["start"]["welcome"])


# COMMAND ECHO FOR CHECK WORKING BOT
@bot.message_handler(regexp="^echo ")
def echo(message: telebot.types.Message) -> None:
    bot.send_message(message.from_user.id, message.text[5:])


# ADDIDNG USER TO PRAYS LISTS
@bot.message_handler(commands=["prays_lists"])
def change_state(message: telebot.types.Message) -> None:
    if not is_banned(message.from_user.id):
        if user_utils.check_username(message.from_user.username):
            with sqlite3.connect(database_file) as cursor:
                users = cursor.execute(
                    "SELECT user_id, state FROM users WHERE role >= ?",
                    (Role.DEFAULT.value,),
                )
            for user in users:
                if user[0] == str(message.from_user.id):
                    state = 0
                    if user[1] == 1:
                        logger.info(f"user {user[0]} has been removed from prays lists")
                        send_message_to_specific_category_users(
                            replies["prays_lists"]["removed"]["notification"].format(
                                username=message.from_user.username
                            ),
                            Role.ADMIN.value,
                            message.from_user.id,
                        )
                        bot.send_message(user[0], replies["prays_lists"]["removed"]["success"])
                    else:
                        state = 1
                        logger.info(f"user {user[0]} added to prays lists")
                        send_message_to_specific_category_users(
                            replies["prays_lists"]["added"]["notification"].format(
                                username=message.from_user.username
                            ),
                            Role.ADMIN.value,
                            message.from_user.id,
                        )
                        bot.send_message(user[0], replies["prays_lists"]["added"]["success"])
                    with sqlite3.connect(database_file) as cursor:
                        cursor.execute(
                            "UPDATE users SET state = ? WHERE user_id = ?", (state, user[0])
                        )
        else:
            bot.send_message(message.from_user.id, replies["none_username"])


# ADDING USER TO EVENT
@bot.message_handler(commands=["event"])
def change_event_state(message: telebot.types.Message) -> None:
    if not is_banned(message.from_user.id):
        if user_utils.check_username(message.from_user.username):
            if config.SECRET_ANGEL:
                with sqlite3.connect(database_file) as cursor:
                    users = cursor.execute(
                        "SELECT user_id, event FROM users WHERE role >= ?",
                        (Role.DEFAULT.value,),
                    )
                for user in users:
                    if user[0] == str(message.from_user.id):
                        state = 0
                        if user[1] == 1:
                            send_message_to_specific_category_users(
                                replies["event"]["removed"]["notification"].format(
                                    username=message.from_user.username
                                ),
                                Role.ADMIN.value,
                                message.from_user.id,
                            )
                            bot.send_message(user[0], replies["event"]["removed"]["success"])
                        else:
                            state = 1
                            send_message_to_specific_category_users(
                                replies["event"]["added"]["notification"].format(
                                    username=message.from_user.username
                                ),
                                Role.ADMIN.value,
                                message.from_user.id,
                            )
                            bot.send_message(user[0], replies["event"]["added"]["success"])
                        with sqlite3.connect(database_file) as cursor:
                            cursor.execute(
                                "UPDATE users SET event = ? WHERE user_id = ?", (state, user[0])
                            )
            else:
                bot.send_message(message.from_user.id, replies["event"]["denied"])
        else:
            bot.send_message(message.from_user.id, replies["none_username"])


# SET THE USER TO DEVELOPER ROLE
@bot.message_handler(commands=[os.getenv("KEY")])
def set_the_user_to_developer_category(message: telebot.types.Message) -> None:
    with sqlite3.connect(database_file) as cursor:
        cursor.execute(
            "UPDATE users SET role = ? WHERE user_id = ?",
            (Role.DEV.value, message.from_user.id),
        )
    logger.info(f"user {message.from_user.id} has been granted developer rights")
    bot.send_message(
        message.from_user.id,
        replies["set_user_developer"]["success"].format(role=Role.DEV.name),
    )
    send_message_to_specific_category_users(
        replies["set_user_developer"]["notification"].format(username=message.from_user.username),
        Role.DEV.value,
        message.from_user.id,
    )


# SEND TO USER INFORMATION ABOUT BOT
@bot.message_handler(commands=["info"])
def send_info(message: telebot.types.Message) -> None:
    if not is_banned(message.from_user.id):
        bot.send_message(message.from_user.id, replies["info"])


# UPDATE USERNAME OF USER IN DATABASE
@bot.message_handler(commands=["update"])
def update_username(message: telebot.types.Message) -> None:
    if not user_utils.check_user_id(message.from_user.id):
        add_to_database(message.from_user.id, message.from_user.username)

    else:
        with sqlite3.connect(database_file) as cursor:
            cursor.execute(
                "UPDATE users SET username = ? WHERE user_id = ?",
                (message.from_user.username, message.from_user.id),
            )
        send_message_to_specific_category_users(
            replies["update"]["notification"].format(username=message.from_user.username),
            Role.DEV.value,
            message.from_user.id,
        )
        bot.send_message(message.from_user.id, replies["update"]["success"])


# SEND TO USER HIS ROLE
@bot.message_handler(commands=["who"])
def who(message: telebot.types.Message) -> None:
    role = get_user_role(message.from_user.id)

    if role == Role.DEFAULT.value:
        role = Role.DEFAULT.name
    elif role == Role.MOD.value:
        role = Role.MOD.name
    elif role == Role.ADMIN.value:
        role = Role.ADMIN.name
    elif role == Role.DEV.value:
        role = Role.DEV.name

    bot.send_message(message.from_user.id, replies["who"].format(role=role))


# SEND HELP LIST
@bot.message_handler(commands=["help"])
def get_help(message: telebot.types.Message) -> None:
    role = get_user_role(message.from_user.id)

    if not is_banned(message.from_user.id):
        if role >= Role.ADMIN.value:
            bot.send_message(
                message.from_user.id,
                f"{replies['help_lists']['moderator_help_list']}\n{replies['help_lists']['admin_help_list']}",
            )
        elif role >= Role.MOD.value:
            bot.send_message(
                message.from_user.id,
                f"{replies['help_lists']['moderator_help_list']}",
            )


# RANDOMIZE USERS FOR PRAYS LISTS
@bot.message_handler(commands=["randomize"])
def randomize_prayers(message: telebot.types.Message) -> None:
    if (
        not is_banned(message.from_user.id)
        and get_user_role(message.from_user.id) >= Role.MOD.value
    ):
        with sqlite3.connect(database_file) as cursor:
            users = cursor.execute("SELECT username FROM users WHERE state = 1")
        prayers_list_parallel = []
        users_id_in_use = []

        prayers_list = [user[0] for user in users]

        for i in range(len(prayers_list)):
            run_randomize = True
            while run_randomize:
                rand = True
                stop = False
                random_id = random.randint(0, len(prayers_list) - 1)
                for id_n in users_id_in_use:
                    if id_n == random_id:
                        rand = False

                # dont user1 -> user1
                if random_id == i and rand:
                    if i == len(prayers_list) - 1 and i != 0:
                        prayers_list_parallel.append(prayers_list_parallel[0])
                        prayers_list_parallel[0] = prayers_list[i]
                        stop = True
                        run_randomize = False
                    else:
                        rand = False

                if rand and not stop:
                    prayers_list_parallel.append(prayers_list[random_id])
                    users_id_in_use.append(random_id)
                    run_randomize = False

        for i in range(len(prayers_list)):
            logger.debug(
                f"{get_id_using_username(prayers_list[i])} -> "
                f"{get_id_using_username(prayers_list_parallel[i])}"
            )
            try:
                bot.send_message(
                    get_id_using_username(prayers_list[i]),
                    replies["randomize"]["message"].format(
                        username=prayers_list_parallel[i],
                        text=get_random_text(),
                    ),
                )
            except telebot.apihelper.ApiTelegramException:
                logger.warning(
                    "error sending message to user" f"{get_id_using_username(prayers_list[i])}"
                )
            with sqlite3.connect(database_file) as cursor:
                cursor.execute(
                    "UPDATE users SET prays_friend = ? WHERE username = ?",
                    (prayers_list_parallel[i], prayers_list[i]),
                )


# START EVENT (RANDOMIZE)
@bot.message_handler(commands=["start_event"])
def randomize_angels(message: telebot.types.Message) -> None:
    if not is_banned(message.from_user.id):
        if config.SECRET_ANGEL:
            with sqlite3.connect(database_file) as cursor:
                users = cursor.execute("SELECT username, wish FROM users WHERE event = 1")
            users_list = []
            users_list_parallel = []
            users_id_in_use = []
            wish_of_users = []
            wish_of_users_parallel = []

            for user in users:
                users_list.append(user[0])
                wish_of_users.append(user[1])

            for i in range(len(users_list)):
                run_randomize = True
                while run_randomize:
                    rand = True
                    stop = False
                    random_id = random.randint(0, len(users_list) - 1)
                    for id_n in users_id_in_use:
                        if id_n == random_id:
                            rand = False

                    # gont user1 -> user1
                    if random_id == i and rand:
                        if i == len(users_list) - 1 and i != 0:
                            users_list_parallel.append(users_list_parallel[0])
                            wish_of_users_parallel.append(wish_of_users_parallel[0])
                            users_list_parallel[0] = users_list[i]
                            wish_of_users_parallel[0] = wish_of_users[i]
                            stop = True
                            run_randomize = False
                        else:
                            rand = False

                    if rand and not stop:
                        users_list_parallel.append(users_list[random_id])
                        wish_of_users_parallel.append(wish_of_users[random_id])
                        users_id_in_use.append(random_id)
                        run_randomize = False

            for i in range(len(users_list)):
                logger.debug(
                    f"{get_id_using_username(users_list[i])} -> "
                    f"{get_id_using_username(users_list_parallel[i])}"
                )
                try:
                    bot.send_message(
                        get_id_using_username(users_list[i]),
                        replies["event"]["message"].format(
                            username=users_list_parallel[i], wish=wish_of_users_parallel[i]
                        ),
                    )
                except telebot.apihelper.ApiTelegramException:
                    logger.warning(
                        f"error sending message to user {get_id_using_username(users_list[i])}"
                    )
                with sqlite3.connect(database_file) as cursor:
                    cursor.execute(
                        "UPDATE users SET angel = ? WHERE username = ?",
                        (users_list_parallel[i], users_list[i]),
                    )
        else:
            bot.send_message(message.from_user.id, replies["event"]["denied"])


# SET WISH
@bot.message_handler(regexp="^my_wish ")
def set_wish(message: telebot.types.Message) -> None:
    if message.from_user.username is not None:
        if not is_banned(message.from_user.id):
            if config.SECRET_ANGEL:
                text = message.text[8:]
                with sqlite3.connect(database_file) as cursor:
                    cursor.execute(
                        "UPDATE users SET my_wish = ? WHERE user_id = ?",
                        (text, message.from_user.id),
                    )
                logger.debug(f"set wish for {message.from_user.id}")
                bot.send_message(message.from_user.id, replies["event"]["wish"])
            else:
                bot.send_message(message.from_user.id, replies["event"]["denied"])
    else:
        bot.send_message(message.from_user.id, replies["none_username"])


# SEND MESSAGE TO ALL USERS
@bot.message_handler(regexp="^all_msg ")
def send_message_for_all_users(message: telebot.types.Message) -> None:
    if (
        not is_banned(message.from_user.id)
        and get_user_role(message.from_user.id) >= Role.MOD.value
    ):
        text = message.text[8:]
        count = send_message_to_specific_category_users(
            text,
            Role.DEFAULT.value,
            message.from_user.id,
        )
        bot.send_message(message.from_user.id, replies["message"]["success"].format(count=count))


# SEND MESSAGE TO ALL PRAYERS
@bot.message_handler(regexp="^msg ")
def send_message_for_all_prayers(message: telebot.types.Message) -> None:
    if (
        not is_banned(message.from_user.id)
        and get_user_role(message.from_user.id) >= Role.MOD.value
    ):
        text = message.text[4:]
        count = 0
        with sqlite3.connect(database_file) as cursor:
            users = cursor.execute(
                "SELECT user_id, state FROM users WHERE role >= ?",
                (Role.DEFAULT.value,),
            )
        for user in users:
            if user[1] == 1 and str(message.from_user.id) != user[0]:
                try:
                    bot.send_message(user[0], text)
                    count += 1
                except telebot.apihelper.ApiTelegramException:
                    logger.info(f"error sending message to user {user[0]}")
                    send_message_to_specific_category_users(
                        replies["message"]["not_found_user"].format(user=user[0]),
                        Role.DEV.value,
                        0,
                    )
        bot.send_message(
            message.from_user.id,
            replies["message"]["success"].format(count=count),
        )


# SEND MESSAGE TO MODERATORS AND ADMINS
@bot.message_handler(regexp="^admin_msg ")
def send_message_for_all_mod_plus(message: telebot.types.Message) -> None:
    if (
        not is_banned(message.from_user.id)
        and get_user_role(message.from_user.id) >= Role.ADMIN.value
    ):
        text = message.text[10:]
        count = send_message_to_specific_category_users(
            text,
            Role.MOD.value,
            message.from_user.id,
        )
        bot.send_message(
            message.from_user.id,
            replies["message"]["success"].format(count=count),
        )


# CHANGE ROLE OF USER
@bot.message_handler(regexp="^/setRole ")
def set_role(message: telebot.types.Message) -> None:
    if get_user_role(message.from_user.id) >= Role.ADMIN.value:
        resours = get_username_and_role_from_text(message.text[9:])
        if not resours:
            bot.send_message(
                message.from_user.id,
                replies["change_role"]["level_not_found"],
            )
        else:
            if user_utils.check_username(resours[0]):
                if get_user_role(message.from_user.id) >= resours[1]:
                    if get_user_role(message.from_user.id) >= get_user_role(
                        get_id_using_username(resours[0])
                    ):
                        logger.debug("changing role...")
                        with sqlite3.connect(database_file) as cursor:
                            cursor.execute(
                                "UPDATE users SET role = ? WHERE username = ?",
                                (resours[1], resours[0]),
                            )
                        logger.info(
                            f"user {message.from_user.id} set role {resours[1]} "
                            f"to user {get_id_using_username(resours[0])}",
                        )
                        if str(message.from_user.id) != str(get_id_using_username(resours[0])):
                            bot.send_message(
                                message.from_user.id,
                                replies["change_role"]["success"].format(
                                    resours_0=resours[0],
                                    resours_1=resours[1],
                                ),
                            )
                        if (
                            get_user_role(get_id_using_username(resours[0])) < Role.DEV.value
                            or get_user_role(get_id_using_username(resours[0])) == Role.DEV.value
                            and str(message.from_user.id) == str(get_id_using_username(resours[0]))
                        ):
                            try:
                                bot.send_message(
                                    get_id_using_username(resours[0]),
                                    replies["change_role"]["success_me"].format(role=resours[1]),
                                )
                            except telebot.apihelper.ApiTelegramException:
                                logger.info(
                                    "error sending message to user"
                                    f"{get_id_using_username(resours[0])}"
                                )
                                send_message_to_specific_category_users(
                                    replies["change_role"]["notification_error"].format(
                                        resours=resours[0]
                                    ),
                                    Role.DEV.value,
                                    0,
                                )
                        send_message_to_specific_category_users(
                            replies["change_role"]["notification"].format(
                                username=message.from_user.username,
                                resours_0=resours[0],
                                resours_1=resours[1],
                            ),
                            Role.DEV.value,
                            message.from_user.id,
                        )
                    else:
                        logger.debug(
                            f"user {message.from_user.id} role is lower than" f"user @{resours[0]}"
                        )
                        bot.send_message(message.from_user.id, replies["change_role"]["denied"])
                else:
                    bot.send_message(
                        message.from_user.id,
                        replies["change_role"]["denied"],
                    )
            else:
                logger.debug(f"user @{resours[0]} not found!")
                bot.send_message(
                    message.from_user.id,
                    replies["change_role"]["user_not_found"].format(username=resours[0]),
                )


# BAN USER
@bot.message_handler(regexp="^/ban ")
def ban(message: telebot.types.Message) -> None:
    role = get_user_role(message.from_user.id)
    ban_status = is_banned(message.from_user.id)

    if role >= Role.ADMIN.value and not ban_status:
        username = get_username_from_text(message.text[5:])

        if user_utils.check_username(username):
            other_user_id = get_id_using_username(username)
            other_role = get_user_role(other_user_id)
            if role >= other_role:
                with sqlite3.connect(database_file) as cursor:
                    cursor.execute(
                        "UPDATE users SET ban = ?, state = ? WHERE username = ?",
                        (1, 0, username),
                    )
                logger.info(f"user {message.from_user.id} banned user " f"{other_user_id}")
                if str(message.from_user.id) != other_user_id:
                    bot.send_message(
                        message.from_user.id,
                        replies["ban"]["success"].format(username=username),
                    )
                if other_role != Role.DEV.value:
                    try:
                        bot.send_message(
                            other_user_id,
                            replies["ban"]["user_notification"],
                        )
                    except telebot.apihelper.ApiTelegramException:
                        logger.info(
                            "error sending message to user" f"{get_id_using_username(username)}"
                        )
                        send_message_to_specific_category_users(
                            replies["ban"]["user_notification_error"].format(
                                user_id=other_user_id,
                                username=username,
                            ),
                            Role.DEV.value,
                            0,
                        )
                send_message_to_specific_category_users(
                    replies["ban"]["notification"].format(
                        my_username=message.from_user.username,
                        username=username,
                    ),
                    Role.DEV.value,
                    message.from_user.id,
                )
            else:
                bot.send_message(
                    message.from_user.id,
                    replies["ban"]["denied"].format(username=username),
                )
        else:
            bot.send_message(
                message.from_user.id,
                replies["ban"]["user_not_found"].format(username=username),
            )


# UNBAN USER
@bot.message_handler(regexp="^/unban ")
def unban(message: telebot.types.Message) -> None:
    role = get_user_role(message.from_user.id)
    ban_status = is_banned(message.from_user.id)

    if role >= Role.ADMIN.value and not ban_status:
        username = get_username_from_text(message.text[7:])

        if user_utils.check_username(username):
            other_user_id = get_id_using_username(username)
            other_role = get_user_role(other_user_id)
            if role >= other_role:
                with sqlite3.connect(database_file) as cursor:
                    cursor.execute(
                        "UPDATE users SET ban = ?, state = ? WHERE username = ?",
                        (0, 0, username),
                    )
                logger.info(f"user {message.from_user.id} unbanned user " f"{other_user_id}")
                if str(message.from_user.id) != other_user_id:
                    bot.send_message(
                        message.from_user.id,
                        replies["unban"]["success"].format(username=username),
                    )
                if other_role != Role.DEV.value:
                    try:
                        bot.send_message(other_user_id, replies["unban"]["user_notification"])
                    except telebot.apihelper.ApiTelegramException:
                        logger.info(
                            "error sending message to user" f"{get_id_using_username(username)}"
                        )
                        send_message_to_specific_category_users(
                            replies["unban"]["user_notification_error"].format(
                                user_id=other_user_id,
                                username=username,
                            ),
                            Role.DEV.value,
                            0,
                        )
                send_message_to_specific_category_users(
                    replies["unban"]["notification"].format(
                        my_username=message.from_user.username,
                        username=username,
                    ),
                    Role.DEV.value,
                    message.from_user.id,
                )
            else:
                bot.send_message(
                    message.from_user.id,
                    replies["unban"]["denied"].format(username=username),
                )
        else:
            bot.send_message(
                message.from_user.id,
                replies["unban"]["user_not_found"].format(username=username),
            )


# START
if __name__ == "__main__":
    logger.info("START BOT")
    bot.polling()
