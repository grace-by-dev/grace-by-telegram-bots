# sql functions
import os

from dotenv import load_dotenv
import psycopg


def get_connection() -> object:
    return psycopg.connect(
        host=os.getenv("POSTGRES_ADDRESS"),
        dbname=os.getenv("DATABSE"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        options="-c search_path=step_of_faith",
    )


class PostgresSQL:
    def __init__(self) -> None:
        self.read = load_dotenv()

    # add to the database
    def add_to_database(self, user_id: int, username: str) -> None:
        with get_connection().cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (user_id, username) VALUES (%s, %s)",
                (user_id, username),
            )

    # checking availability user_id in the database
    def check_user_id(self, user_id: int) -> bool:
        with get_connection().cursor() as cursor:
            data = cursor.execute(
                "SELECT user_id FROM users WHERE user_id = %s", (user_id,)
            ).fetchone()
        return data is not None

    # checking ban status of user
    def is_banned(self, user_id: int) -> bool:
        with get_connection().cursor() as cursor:
            data = cursor.execute("SELECT ban FROM users WHERE user_id = %s", (user_id,)).fetchone()
        if data is not None:
            return data[0]

    # checking for admin status of user
    def is_admin(self, user_id: int) -> bool:
        with get_connection().cursor() as cursor:
            data = cursor.execute(
                "SELECT admin FROM users WHERE user_id = %s", (user_id,)
            ).fetchone()
        if data is not None:
            return data[0]

    # change ban status
    def change_ban_status(self, username: str, ban: bool) -> None:
        with get_connection().cursor() as cursor:
            data = cursor.execute(
                "SELECT ban FROM users WHERE username = %s", (username,)
            ).fetchone()
            if data is not None:
                if data[0] != ban:
                    cursor.execute(
                        "UPDATE users SET ban = %s WHERE username = %s",
                        (ban, username),
                    )
                    return True
            else:
                return False
