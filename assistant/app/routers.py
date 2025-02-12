from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from assistant.app.tg_app import create_user, ask
from assistant.core.constants import START_MESSAGE

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    data = {
        "user_id": str(message.from_user.id),
        "tg_username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "language_code": message.from_user.language_code,
        "is_premium": message.from_user.is_premium,
        "is_bot": message.from_user.is_bot
    }
    await create_user(data)
    await message.answer(START_MESSAGE)


@router.message()
async def handle_query_command(message: Message):
    user_id = str(message.from_user.id)
    try:
        response = await ask(user_id, message.text)
        await message.answer(response["response"].replace("**", ""))
    except Exception as e:
        print(f"Error asking question: {e}")
