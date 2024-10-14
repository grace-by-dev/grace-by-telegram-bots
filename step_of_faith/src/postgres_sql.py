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


class PostgreSQL:
    def __init__(self) -> None:
        self.read = load_dotenv()

    # add to the database
    def add_to_database(self, user_id: int) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (user_id) VALUES (%s)",
                (user_id,),
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
    def get_schedule(self, day: int) -> list:
        with get_connection().cursor() as cur:
            return list(cur.execute("SELECT time, event FROM schedule WHERE day = (%s)", (day,)))

    # get list of counselors
    def get_counselors(self) -> list:
        with get_connection().cursor() as cur:
            counselors = list(
                cur.execute("SELECT counselor_id FROM schedule_counselor_appointment")
            )
            counselors_list = []
            for counselor in counselors:
                if counselor[0] not in counselors_list:
                    counselors_list.append(counselor[0])
            return counselors_list

    # get times for schedule counselor appointment
    def get_counselor_appointment_times(self, counselor_id: str) -> list:
        with get_connection().cursor() as cur:
            return list(
                cur.execute(
                    """
                    SELECT time FROM schedule_counselor_appointment
                    WHERE counselor_id = %s AND user_id IS NULL
                """,
                    (counselor_id,),
                )
            )

    # write_user_to_schedule_counselor_appointment
    def write_user_to_schedule_counselor_appointment(
        self, counselor_id: str, time: str, user_id: int
    ) -> bool:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE schedule_counselor_appointment
                SET user_id = NULL
                WHERE user_id = %s
            """,
                (user_id,),
            )
            cur.execute(
                """
                UPDATE schedule_counselor_appointment
                SET user_id = %s WHERE counselor_id = %s
                and time = %s and user_id IS NULL
            """,
                (user_id, counselor_id, time),
            )
            conn.commit()
        with get_connection().cursor() as cur:
            check_data = list(
                cur.execute(
                    """SELECT * FROM schedule_counselor_appointment
                WHERE counselor_id = %s and time = %s and user_id = %s
                LIMIT 1""",
                    (counselor_id, time, user_id),
                )
            )
        return bool(
            check_data[0][0] == counselor_id
            and check_data[0][1] == time
            and check_data[0][2] == user_id
        )

    # delete_user_from_schedule_counselor_appointment
    def delete_user_from_schedule_counselor_appointment(self, user_id: int) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE schedule_counselor_appointment
                SET user_id = NULL WHERE user_id = %s
            """,
                (user_id,),
            )
