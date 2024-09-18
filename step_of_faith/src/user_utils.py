# user utils
import os

from dotenv import load_dotenv
import yaml


class UserUtils:
    def __init__(self, env_file: str, yaml_file: str) -> None:
        self.read = load_dotenv(env_file)
        with open(yaml_file, encoding="utf-8") as f:
            self.replies = yaml.safe_load(f)

    # select username from text for ban/unban
    def select_username_from_text(self, text: str) -> str:
        username = []

        if len(text) > 0:
            for i in text:
                if i != " ":
                    username.append(i)
                else:
                    break

            return "".join(username)
        else:
            return "none"

    # make schedule text
    def make_schedule_text(self, schedule: list) -> str:
        result = [
            self.replies["button"]["schedule"]["text"]["body"].format(time=event[0], event=event[1])
            for event in schedule
        ]
        return self.replies["button"]["schedule"]["text"]["head"] + "".join(result)

    # get id for counselor sheet
    def get_sheet_id(self, counselor: int) -> None:
        if counselor == 1:
            return os.getenv("SHEET_OF_COUNSELOR_1")
        elif counselor == 2:
            return os.getenv("SHEET_OF_COUNSELOR_2")
        elif counselor == 3:
            return os.getenv("SHEET_OF_COUNSELOR_3")
        elif counselor == 4:
            return os.getenv("SHEET_OF_COUNSELOR_4")
