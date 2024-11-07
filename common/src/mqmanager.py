import json
from typing import Dict
from typing import List

from omegaconf import ListConfig
from omegaconf import OmegaConf
import pika
from telebot import types


class MQManager:
    def __init__(self, queue: str, max_priority: int, user: str, password: str) -> None:
        self.queue = queue

        params = pika.ConnectionParameters(
            "localhost", credentials=pika.credentials.PlainCredentials(user, password)
        )
        connection = pika.BlockingConnection(params)

        self.channel = connection.channel()
        self.channel.queue_declare(
            queue=queue, arguments={"x-max-priority": max_priority}, durable=True
        )

    def edit_keyboard_message(
        self,
        callback: types.CallbackQuery,
        reply: str,
        row_width: int,
        children: List[Dict[str, str]],
        priority: int = 0,
    ) -> None:
        body = json.dumps(
            {
                "chat_id": callback.message.chat.id,
                "message_id": callback.message.id,
                "text": reply,
                "row_width": row_width,
                "children": OmegaConf.to_object(ListConfig(children)),
                "parse_mode": "Markdown",
            }
        )
        self.channel.basic_publish(
            exchange="",
            routing_key=self.queue,
            body=body,
            properties=pika.BasicProperties(priority=priority),
        )

    def send_keyboard_message(
        self,
        message: types.Message,
        reply: str,
        row_width: int,
        children: List[Dict[str, str]],
        priority: int = 0,
    ) -> None:
        body = json.dumps(
            {
                "chat_id": message.chat.id,
                "text": reply,
                "row_width": row_width,
                "children": OmegaConf.to_object(ListConfig(children)),
                "parse_mode": "Markdown",
            }
        )
        self.channel.basic_publish(
            exchange="",
            routing_key=self.queue,
            body=body,
            properties=pika.BasicProperties(priority=priority),
        )
