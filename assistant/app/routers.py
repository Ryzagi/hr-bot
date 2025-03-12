import re

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from assistant.core.constants import START_MESSAGE
from assistant.app.handlers import create_user_tg, ask

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
    await create_user_tg(data)
    await message.answer(START_MESSAGE)


def escape_markdown(text: str) -> str:
    # Escape special characters except asterisks for bold text
    special_chars = r"_[]()~`>#+-=|{}.!"
    escaped_text = re.sub(rf"([{re.escape(special_chars)}])", r"\\\1", text)

    # Preserve clickable links
    escaped_text = re.sub(r"\\\[(.*?)\\\]\\\((.*?)\\\)", r"[\1](\2)", escaped_text)

    return escaped_text


def detect_markdown(text: str) -> bool:
    # Detect if text contains Markdown patterns
    return "[" in text and "](" in text or any(c in text for c in "_*~`>#+-=|{}.!")


async def send_message(message, text):
    try:
        # Detect and escape text if Markdown is found
        if detect_markdown(text):
            escaped_text = escape_markdown(text)
            await message.answer(escaped_text, parse_mode="MarkdownV2", disable_web_page_preview=False)
        else:
            await message.answer(text)
    except Exception as e:
        print(f"MarkdownV2 failed: {e}")
        # Fallback to HTML
        try:
            await message.answer(text, parse_mode="HTML", disable_web_page_preview=False)
        except Exception as e:
            print(f"HTML failed: {e}")
            await message.answer(text)  # Plain text fallback


@router.message()
async def handle_query_command(message: Message):
    user_id = str(message.from_user.id)
    try:
        response = await ask(user_id, message.text, message.bot)
        text = response["response"]
        await send_message(message, text)
    except Exception as e:
        print(f"Error asking question: {e}")
