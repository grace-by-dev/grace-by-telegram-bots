# google sheets module
import datetime
import os

from dotenv import load_dotenv
import gspread

from step_of_faith import UserUtils


class GoogleSheets:
    TIME_RELOAD = 10
    READ = load_dotenv(".env")

    CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
    TOKEN = os.getenv("GOOGLE_SHEETS_TOKEN")

    def __init__(self) -> None:
        self.now = datetime.datetime.now() - datetime.timedelta(minutes=self.TIME_RELOAD)
        self.result: str

        self.client = gspread.service_account(filename=self.CREDENTIALS_FILE)
        self.book = self.client.open_by_key(self.TOKEN)

    # write question to sheet
    def write_question(self, question: str) -> None:
        sheet = self.book.get_worksheet_by_id(os.getenv("SHEET_OF_QUESTION"))
        current_data = sheet.get_all_values()
        data = [*current_data, [question]]
        sheet.update(data)

    # write feedback to sheet
    def write_feedback(self, feedback: str) -> None:
        sheet = self.book.get_worksheet_by_id(os.getenv("SHEET_OF_FEEDBACK"))
        current_data = sheet.get_all_values()
        data = [*current_data, [feedback]]
        sheet.update(data)

    # get schedule from sheet
    def get_schedule(self) -> list:
        difference = datetime.datetime.now() - self.now
        if difference >= datetime.timedelta(minutes=self.TIME_RELOAD):
            sheet = self.book.get_worksheet_by_id(os.getenv("SHEET_OF_SCHEDULE"))
            schedule = sheet.get_all_values()
            schedule.pop(0)
            self.now = datetime.datetime.now()
            self.result = UserUtils.make_schedule_text(schedule)
        return self.result

    # write to talk with counselor
    def write_to_talk(self, counselor: int, user_data: list) -> None:
        sheet = self.book.get_worksheet_by_id(UserUtils.get_sheet_id(counselor))
        current_data = sheet.get_all_values()
        data = [*current_data, user_data]
        sheet.update(data)
