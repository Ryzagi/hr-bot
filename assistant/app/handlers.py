import asyncio
import aiohttp
from assistant.core.constants import CREATE_USER_ENDPOINT, ASK_ENDPOINT, NETWORK, SUMMARY_PARAMS, \
    GET_CONVERSATIONS_ENDPOINT
from assistant.config import HR_CHAT_ID


async def create_user_tg(user_data: dict):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"http://{NETWORK}:9000{CREATE_USER_ENDPOINT}",
                json=user_data
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to create user. Status code: {response.status}")
            return await response.json()


async def ask(user_id: str, user_text: str, bot=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"http://{NETWORK}:9000{ASK_ENDPOINT}",
                json={"user_id": user_id, "user_text": user_text}
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to get response. Status code: {response.status}")
            if bot:
                await bot.send_chat_action(user_id, "typing")
                await asyncio.sleep(0.5)
            response_json = await response.json()
            print(response_json)
            if bot and response_json.get("user_info"):
                response_json["user_info"]["messagenger"] = "telegram"
                await send_user_info(bot, response_json["user_info"])
            return response_json


async def send_user_info(bot, user_info: dict):
    message_text = SUMMARY_PARAMS["summary_message"].format(**user_info)
    await bot.send_message(HR_CHAT_ID, text=message_text)


async def get_conversations():
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"http://{NETWORK}:9000{GET_CONVERSATIONS_ENDPOINT}"
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to get conversations. Status code: {response.status}")
            return await response.json()
