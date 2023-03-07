# -*- coding: utf-8 -*-
# @Time    : 3/6/2023
# @Author  : nzooherd
# @File    : telegram_user.py.py
# @Software: PyCharm
import asyncio
import functools
from typing import Callable

import socks
from telethon import TelegramClient
from telethon.events import NewMessage

from openai_helper import OpenAIHelper


class TelegramUserApp:

    def __init__(self, config: dict, openai: OpenAIHelper):
        self.config = config
        self.openai = openai
        self.client = TelegramClient('.chatgpt-telegram-user', config["telegram_app_id"], config["telegram_app_hash"],
                                     proxy=(socks.SOCKS5, '192.168.10.118', 7891))
        self.client.start()

        self.prompts = {
            "polish": "Revise the following sentences to make them more clear, concise, and coherent."
        }

    async def _polish_do(self, versus_event: NewMessage.Event):
        chat_id = versus_event.chat_id
        query = f"{self.prompts['polish']}: {versus_event.message.text}"
        polish_response = self.openai.get_chat_response(chat_id=chat_id, function="polish", query=query, stream=False)
        response = versus_event.message.text + "\n----\n" + f"**`{polish_response}`**"
        entity = await self.client.get_entity(versus_event.message.to_id.user_id)

        async for message in self.client.iter_messages(entity, limit=10):
            if message.text == versus_event.message.text:
                await self.client.edit_message(entity=entity, message=message, text=response)
                break


    @staticmethod
    def polish_api(func: Callable):
        @functools.wraps(func)
        async def wrapped(cls, *args, **kwargs):
            event = None
            for arg in args:
                if isinstance(arg, NewMessage.Event):
                    event = arg
                    break
            if not event:
                return func(cls, *args, **kwargs)

            self = cls.telegram_user_app
            if not self._check_need_polish(event) or not self._check_allow_polish(event):
                return func(cls, *args, **kwargs)
            await self._polish_do(event)
            return await func(cls, *args, **kwargs)
        return wrapped

    def _check_allow_polish(self, event: NewMessage.Event) -> bool:
        return True

    def _check_need_polish(self, event: NewMessage.Event) -> bool:
        """
        """
        query_text = event.message.text
        for c in query_text:
            if 0 <= ord(c) <= 256:
                pass
            else:
                return False
        return True









