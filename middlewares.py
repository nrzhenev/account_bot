"""Аутентификация — пропускаем сообщения только от одного Telegram аккаунта"""
from typing import List

from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware


class AccessMiddleware(BaseMiddleware):
    def __init__(self, allowed_user_ids: list):
        self.allowed_user_ids = allowed_user_ids
        super().__init__()

    async def __call__(self, handler, event: types.Message, data: dict):
        # Проверка ID пользователя
        if event.from_user.id not in self.allowed_user_ids:
            await event.answer("У вас нет доступа к этому боту.")
            return None  # Останавливает дальнейшую обработку сообщения
        return await handler(event, data)