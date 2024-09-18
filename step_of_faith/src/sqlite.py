# sql functions
import os
import sqlite3

from dotenv import load_dotenv


class SQLite:
    def __init__(self, env_file: str) -> None:
        self.read = load_dotenv(env_file)
        self.database = os.getenv('FILE_DATABASE')


    # add to the database
    def add_to_database(self, user_id: int, username: str) -> None:
        with sqlite3.connect(self.database) as cursor:
            cursor.execute('INSERT INTO users VALUES (?, ?, ?, ?)', (user_id, username, 0, 0))


    # checking availability user_id in the database
    def check_user_id(self, user_id: int) -> bool:
        with sqlite3.connect(self.database) as cursor:
            data = cursor.execute(
                'SELECT user_id FROM users WHERE user_id = ?', (user_id,)
            ).fetchone()
        return data is not None


    # checking ban status of user
    def is_banned(self, user_id: int) -> bool:
        with sqlite3.connect(self.database) as cursor:
            data = cursor.execute('SELECT ban FROM users WHERE user_id = ?', (user_id,)).fetchone()
        if data is not None:
            return data[0]


    # checking for admin status of user
    def is_admin(self, user_id: int) -> bool:
        with sqlite3.connect(self.database) as cursor:
            data = cursor.execute(
                'SELECT admin FROM users WHERE user_id = ?', (user_id,)
            ).fetchone()
        if data is not None:
            return data[0]


    # change ban status
    def change_ban_status(self, username: str, ban: bool) -> None:
        with sqlite3.connect(self.database) as cursor:
            data = cursor.execute(
                'SELECT ban FROM users WHERE username = ?', (username,)
            ).fetchone()
            if data is not None:
                if data[0] != ban:
                    cursor.execute('UPDATE users SET ban = ? WHERE username = ?', (ban, username))
                    return True
            else:
                return False
