import asyncio
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models.client import Client, ClientSource
from app.db.models.chat import Chat, ChatStatus
from app.db.models.chat_participant import ChatParticipant, ParticipantRole
from app.db.models.message import Message
from app.db.models.user import User, UserRole
from app.ws.chat_ws import manager
from app.redis_client import redis_manager
import uuid
import httpx
import json


class MaxBotClient:
    def __init__(self, bot_token: str, api_base: str = "https://api.max.ru/v1"):
        self.bot_token = bot_token
        self.api_base = api_base
        self.headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
        # Словарь для хранения соответствия chat_id MAX -> chat_id в вашей системе
        self.max_chat_to_system_chat: Dict[int, int] = {}

    async def send_message_to_user(self, user_id: int, text: str,
                                   operator_name: str = None, keyboard: dict = None,
                                   media_url: str = None, media_type: str = None):

        """Отправить сообщение пользователю MAX"""
        formatted_text = f"👨‍💼 {operator_name}:\n{text}" if operator_name else text

        async with httpx.AsyncClient() as client:
            payload = {
                "user_id": user_id,
                "text": formatted_text
            }

            # Добавляем клавиатуру, если есть
            if keyboard:
                payload["keyboard"] = keyboard

            # Добавляем поддержку медиа (если есть)
            if media_url and media_type:
                payload["attachments"] = [{
                    "type": media_type,
                    "url": media_url
                }]

            response = await client.post(
                f"{self.api_base}/messages/send",
                headers=self.headers,
                json=payload
            )
            return response.json()

    async def send_typing_action(self, user_id: int):
        """Отправить индикатор набора текста"""
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.api_base}/messages/typing",
                headers=self.headers,
                json={"user_id": user_id}
            )

    async def register_webhook(self, webhook_url: str):
        """Зарегистрировать вебхук для получения сообщений от MAX"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/webhooks/set",
                headers=self.headers,
                json={"url": webhook_url}
            )
            return response.json()


# Глобальный экземпляр клиента MAX
max_bot = None


def init_max_bot(bot_token: str):
    global max_bot
    max_bot = MaxBotClient(bot_token)
    return max_bot


async def send_operator_message_to_max(self, user_id: int, text: str,
                                       operator_name: str = None):
    """Отправить сообщение от оператора в MAX"""
    formatted_text = f"👨‍💼 {operator_name}:\n{text}" if operator_name else text

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.api_base}/messages/send",
            headers=self.headers,
            json={
                "user_id": user_id,
                "text": formatted_text
            }
        )
        return response.json()