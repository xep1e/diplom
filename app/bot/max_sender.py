import os
import requests


class MaxSender:

    def __init__(self):

        self.token = os.getenv("MAX_BOT_TOKEN")

        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }

    async def send_message_to_user(
        self,
        user_id: int,
        text: str,
        operator_name: str = None,
        keyboard=None
    ):

        if operator_name:
            text = f"👨‍💻 {operator_name}:\n{text}"

        payload = {
            "text": text
        }

        if keyboard:

            payload["attachments"] = [
                {
                    "type": "inline_keyboard",
                    "payload": {
                        "buttons": (
                            keyboard["inline_keyboard"]
                        )
                    }
                }
            ]

        r = requests.post(
            f"https://platform-api.max.ru/messages?user_id={user_id}",
            headers=self.headers,
            json=payload,
            timeout=10
        )

        print("MAX SEND:")
        print(r.status_code)
        print(r.text)

        r.raise_for_status()

        return r.json()


max_bot = MaxSender()