# sql functions
import os

from dotenv import load_dotenv
import psycopg
import yaml


def get_connection() -> object:
    return psycopg.connect(
        host=os.getenv("POSTGRES_ADDRESS"),
        dbname=os.getenv("DATABSE"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        options="-c search_path=step_of_faith",
    )


class PostgreSQL:
    def __init__(self, yaml_file: str) -> None:
        self.read = load_dotenv()
        with open(yaml_file, encoding="utf-8") as f:
            self.replies = yaml.safe_load(f)

    # add to the database
    def add_to_database(self, user_id: int, username: str) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (user_id, username) VALUES (%s, %s)",
                (user_id, username),
            )
            conn.commit()

    # checking availability user_id in the database
    def check_user_id(self, user_id: int) -> bool:
        with get_connection().cursor() as cur:
            data = cur.execute(
                "SELECT user_id FROM users WHERE user_id = %s", (user_id,)
            ).fetchone()
        return data is not None

    # checking ban status of user
    def is_banned(self, user_id: int) -> bool:
        with get_connection().cursor() as cur:
            data = cur.execute("SELECT ban FROM users WHERE user_id = %s", (user_id,)).fetchone()
        if data is not None:
            return data[0]

    # checking for admin status of user
    def is_admin(self, user_id: int) -> bool:
        with get_connection().cursor() as cur:
            data = cur.execute("SELECT admin FROM users WHERE user_id = %s", (user_id,)).fetchone()
        if data is not None:
            return data[0]

    # change ban status
    def change_ban_status(self, username: str, ban: bool) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            data = cur.execute("SELECT ban FROM users WHERE username = %s", (username,)).fetchone()
            if data is not None:
                if data[0] != ban:
                    cur.execute(
                        "UPDATE users SET ban = %s WHERE username = %s",
                        (ban, username),
                    )
                    conn.commit()
                    return True
            else:
                return False

    # write message to database
    def write_message(self, message_type: str, message: str) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO feedbacks (type, data) VALUES (%s, %s)", (message_type, message)
            )
            conn.commit()

    # get schedule from sheet
    def get_schedule(self, day: int) -> str:
        result = self.replies["button"]["schedule"]["text"]["head"]
        with get_connection().cursor() as cur:
            schedule = cur.execute("SELECT time, event FROM schedule WHERE day = (%s)", (day,))
            for event in schedule:
                result += self.replies["button"]["schedule"]["text"]["body"].format(
                    time=str(event[0])[:5], event=event[1]
                )
        return result
