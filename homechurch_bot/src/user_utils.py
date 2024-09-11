# user_utils_module
import sqlite3


class UserUtils:
    def __init__(self, database_file: str) -> None:
        self.database_file = database_file

    # checking for user_id in the database
    def check_user_id(self, user_id: int) -> bool:
        with sqlite3.connect(self.database_file) as cursor:
            info = cursor.execute(
                "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()

        return info is not None

    # checking for username in the database
    def check_username(self, username: str) -> bool:
        with sqlite3.connect(self.database_file) as cursor:
            info = cursor.execute(
                "SELECT username FROM users WHERE username = ?", (username,)
            ).fetchone()

        return info is not None and info[0] is not None
