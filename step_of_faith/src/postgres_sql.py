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

    def add_to_database(self, user_id: int) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users VALUES (%(user_id)s);
                """,
                {"user_id": user_id},
            )
            cur.execute(
                """
                INSERT INTO seminar_enrollement VALUES 
                (NULL, %(user_id)s, 1),
                (NULL, %(user_id)s, 2);
                """,
                {"user_id": user_id},
            )
            conn.commit()

    def check_user_id(self, user_id: int) -> bool:
        with get_connection().cursor() as cur:
            data = cur.execute("SELECT id FROM users WHERE id = %s", (user_id,)).fetchone()
        return data is not None

    def is_banned(self, user_id: int) -> bool:
        with get_connection().cursor() as cur:
            data = cur.execute("SELECT ban FROM users WHERE id = %s", (user_id,)).fetchone()
        if data is not None:
            return data[0]

    def is_admin(self, user_id: int) -> bool:
        with get_connection().cursor() as cur:
            data = cur.execute("SELECT admin FROM users WHERE id = %s", (user_id,)).fetchone()
        if data is not None:
            return data[0]

    def write_message(self, message_type: str, message: str) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO feedbacks (type, data) VALUES (%s, %s)", (message_type, message)
            )
            conn.commit()

    def get_schedule(self, day: int) -> list:
        with get_connection().cursor() as cur:
            return cur.execute("SELECT time, event FROM schedule WHERE day = %s", (day,)).fetchall()

    def get_counselors(self) -> list:
        with get_connection().cursor() as cur:
            return cur.execute(
                """
                    SELECT id, name 
                    FROM counselors
                    ORDER BY id;
                    """
            ).fetchall()

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
            if status:
                cur.execute(
                    """
                    UPDATE counseling
                    SET user_id = NULL
                    WHERE NOT (counselor_id = %s AND time = %s)
                        AND user_id = %s
                    """,
                    (counselor_id, time, user_id),
                )
                conn.commit()
            else:
                conn.rollback()
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

    def cancel_counseling(self, user_id: int) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE counseling
                SET user_id = NULL WHERE user_id = %s
                """,
                (user_id,),
            )
            conn.commit()

    def get_seminars(self) -> list:
        with get_connection().cursor() as cur:
            return cur.execute(
                """
                SELECT id, title 
                FROM seminars
                ORDER BY id;
                """
            ).fetchall()

    def get_seminar_info(self, seminar_id: int) -> list:
        with get_connection().cursor() as cur:
            return cur.execute(
                """
                SELECT title, description 
                FROM seminars
                WHERE id = %s;
                """,
                (seminar_id,),
            ).fetchone()

    def enroll_for_seminar(self, seminar_id: int, user_id: int, seminar_number: int) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE seminar_enrollement
                SET seminar_id = %s
                WHERE user_id = %s and seminar_number = %s
                """,
                (seminar_id, user_id, seminar_number),
            )
            conn.commit()

    def get_my_seminars(self, user_id: int) -> list:
        with get_connection().cursor() as cur:
            return cur.execute(
                """
                SELECT title, description
                FROM seminar_enrollement enrollement
                LEFT JOIN seminars
                    ON enrollement.seminar_id = seminars.id
                WHERE user_id = %s
                ORDER BY seminar_number; 
                """,
                (user_id,),
            ).fetchall()

    def cancel_my_seminar(self, user_id: int, seminar_number: int) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE seminar_enrollement
                SET seminar_id = NULL
                WHERE user_id = %s and seminar_number = %s
                """,
                (user_id, seminar_number),
            )
            conn.commit()
