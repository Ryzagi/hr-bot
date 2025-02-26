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
                response_json = response_json['user_info']
                #await bot.send_message(user_id, text=f"Диалог завершен! Вот информация о кандидате:\n{response_json['user_info']}")
                message_text = (
                    f"Диалог завершен!\n"
                    f"📌 Вакансия: {response_json['vacancy']}\n"
                    f"🗓 График: {response_json['schedule']}\n"
                    f"👤 ФИО: {response_json['full_name']}\n"
                    f"🎂 Дата рождения: {response_json['date_of_birth']}\n"
                    f"📍 Город: {response_json['city']}\n"
                    f"🚇 Метро: {response_json['metro']}\n"
                    f"🌍 Гражданство: {response_json['citizenship']}\n"
                    f"📄 Документы: {response_json['documents']}\n"
                    f"📞 Телефон: {response_json['phone_number']}\n"
                    f"🔔 Дата собеседования: {response_json['interview_date']}\n"
                    f"🕒 Время собеседования: {response_json['interview_time']}"
                )
                await bot.send_message(ADMIN_TG_ID,
                                       text=message_text)
                await bot.send_message(HR_CHAT_ID, text=message_text)
            return response_json


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
