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
            return cur.execute("SELECT time, event FROM schedule WHERE day = %s", (day,)).fetchall()

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

    def get_counselor_info(self, counselor_id: str) -> list:
        with get_connection().cursor() as cur:
            return cur.execute(
                """
                    SELECT name, description FROM counselors
                    WHERE id = %s;
                """,
                (counselor_id,),
            ).fetchone()

    def get_counselor_timeslots(self, counselor_id: str) -> list:
        with get_connection().cursor() as cur:
            return cur.execute(
                """
                    SELECT time FROM counseling
                    WHERE counselor_id = %s AND user_id IS NULL
                    ORDER BY time;
                """,
                (counselor_id,),
            ).fetchall()

    def book_counseling(self, counselor_id: int, user_id: int, time: str) -> bool:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    UPDATE counseling
                    SET user_id = %s
                    WHERE counselor_id = %s
                        AND user_id IS NULL
                        AND time = %s
                """,
                (user_id, counselor_id, time),
            )
            status = cur.rowcount != 0
            conn.commit()
        return status

    def get_my_counseling(self, user_id: int) -> list:
        with get_connection().cursor() as cur:
            return cur.execute(
                """
                    SELECT name, description, time
                    FROM counseling
                    JOIN counselors
                    ON counseling.counselor_id = counselors.id
                    WHERE user_id = %s
                    """,
                (user_id,),
            ).fetchone()

    # delete_user_from_schedule_counselor_appointment
    def cancel_counseling(self, user_id: int) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    UPDATE counseling
                    SET user_id = NULL WHERE user_id = %s
                """,
                (user_id,),
            )

    # get seminar of user
    def get_user_seminar(self, user_id: int) -> list:
        with get_connection().cursor() as cur:
            result = cur.execute(
                """
                    SELECT seminar FROM users
                    WHERE user_id = %s
                """,
                (user_id,),
            )
            return next(iter(result))[0]

    # set up seminar for user
    def setup_seminar_for_user(self, user_id: int, seminar: str | None) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("UPDATE users SET seminar = %s WHERE user_id = %s", (seminar, user_id))
