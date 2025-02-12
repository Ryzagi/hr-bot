import asyncio
import logging
import sys

from aiogram.client.session import aiohttp

from assistant.app import routers
from assistant.config import TELEGRAM_BOT_TOKEN

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from assistant.core.constants import CREATE_USER_ENDPOINT, NETWORK, ASK_ENDPOINT

bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(routers.router)
    await dp.start_polling(bot, polling_timeout=5)


async def create_user(user_data: dict):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"http://{NETWORK}:8000{CREATE_USER_ENDPOINT}",
                json=user_data
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to create user. Status code: {response.status}")
            return await response.json()


async def ask(user_id: str, user_text: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"http://{NETWORK}:8000{ASK_ENDPOINT}",
                json={"user_id": user_id, "user_text": user_text}
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to get response. Status code: {response.status}")
            await bot.send_chat_action(user_id, "typing")
            await asyncio.sleep(0.5)
            response_json = await response.json()
            if response_json.get("user_info"):
                #await bot.send_message(user_id, text=f"Диалог завершен! Вот информация о кандидате:\n{response_json['user_info']}")
                await bot.send_message(656996538,
                                       text=f"Диалог завершен! Вот информация о кандидате:\n{response_json['user_info']}")
            return response_json


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
