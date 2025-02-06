from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from assistant.app.tg_app import create_user, ask
from assistant.core.constants import START_MESSAGE

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    await create_user(str(message.from_user.id))
    await message.answer(START_MESSAGE)


@router.message()
async def handle_query_command(message: Message):
    user_id = str(message.from_user.id)
    try:
        response = await ask(user_id, message.text)
        await message.answer(response["response"].replace("**", ""))
    except Exception as e:
        print(f"Error asking question: {e}")
