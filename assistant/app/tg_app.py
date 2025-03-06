import asyncio
import logging
import sys

from aiogram.client.session import aiohttp

from assistant.app import routers
from assistant.config import TELEGRAM_BOT_TOKEN, ADMIN_TG_ID, HR_CHAT_ID

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
                f"http://{NETWORK}:9000{CREATE_USER_ENDPOINT}",
                json=user_data
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to create user. Status code: {response.status}")
            return await response.json()


async def ask(user_id: str, user_text: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"http://{NETWORK}:9000{ASK_ENDPOINT}",
                json={"user_id": user_id, "user_text": user_text}
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to get response. Status code: {response.status}")
            await bot.send_chat_action(user_id, "typing")
            await asyncio.sleep(0.5)
            response_json = await response.json()
            print(response_json)
            if response_json.get("user_info"):
                await send_user_info(response_json["user_info"])
            return response_json

async def send_user_info(user_info: dict):
    message_text = (
        f"Диалог завершен!\n"
        f"📌 Вакансия: {user_info['vacancy']}\n"
        f"👤 ФИО: {user_info['full_name']}\n"
        f"🎂 Дата рождения: {user_info['date_of_birth']}\n"
        f"📍 Город: {user_info['city']}\n"
        f"🚇 Метро: {user_info['metro']}\n"
        f"🌍 Гражданство: {user_info['citizenship']}\n"
        f"📞 Телефон: {user_info['phone_number']}\n"
    )
    await bot.send_message(HR_CHAT_ID, text=message_text)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
