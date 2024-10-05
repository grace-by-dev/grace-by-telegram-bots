# user utils

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
