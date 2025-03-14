import os
from contextlib import asynccontextmanager

import requests
from aiogram import Bot
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_core.messages import AIMessage
from loguru import logger
from starlette.requests import Request

from assistant.app.data import AppState, UserInput
from assistant.app.handlers import send_user_info
from assistant.config import (NOTION_API_KEY, NOTION_ROOT_PAGE_ID,
                              OPENAI_API_KEY, SUPABASE_KEY, SUPABASE_URL,
                              TELEGRAM_BOT_TOKEN)
from assistant.core.constants import (ASK_ENDPOINT, CREATE_USER_ENDPOINT,
                                      START_MESSAGE, WAZZAP_ENDPOINT, GET_CONVERSATIONS_ENDPOINT)
from assistant.database.supabase_service import SupabaseService
from assistant.generator import HRChatBot
from assistant.notion_service import NotionParser

load_dotenv()

# HISTORY_WRITER = HistoryWriter()
# USER_STATUSES = HISTORY_WRITER.load_user_statuses()
# CONVERSATIONS = HISTORY_WRITER.load_user_conversations()

telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

hr_bot = HRChatBot(api_key=OPENAI_API_KEY)
SUPABASE_WRITER = SupabaseService(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)
CONVERSATIONS = SUPABASE_WRITER.load_conversations()
NOTION_SERVICE = NotionParser(api_key=NOTION_API_KEY, page_id=NOTION_ROOT_PAGE_ID)


def register_wazzup_webhook():
    url = "https://api.wazzup24.com/v3/webhooks"
    headers = {
        "Authorization": f"Bearer {os.getenv('WAZZUP_TOKEN')}",
        "Content-Type": "application/json",
    }
    payload = {
        "webhooksUri": os.getenv("WAZZUP_WEBHOOK_URL"),
        "subscriptions": {"messagesAndStatuses": True},
    }
    response = requests.patch(url, headers=headers, json=payload)
    logger.info(
        f"Wazzup Webhook Registration: {response.status_code}, {response.json()}"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    # Load all user statuses and conversations
    app.state = AppState()
    app.state.conversations = CONVERSATIONS

    try:
        register_wazzup_webhook()  # Register webhook on startup
    except Exception as e:
        logger.error(f"Failed to register Wazzup webhook: {e}")

    yield  # Application is running

    # On shutdown, save all statuses and conversations
    # HISTORY_WRITER.save_user_conversations(app.state.conversations)
    SUPABASE_WRITER.save_conversations(app.state.conversations)
    logger.info("Conversation and user statuses saved, application shutting down.")


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def root():
    return {"message": "OK"}


@app.post(CREATE_USER_ENDPOINT)
async def create_user(data: dict) -> dict:
    user_id = data.get("user_id")
    # HISTORY_WRITER.create_json_file(user_id=user_id)
    await SUPABASE_WRITER.add_new_user(user_data=data)
    app.state.conversations[user_id] = {
        "messages": [
            AIMessage(content=START_MESSAGE, additional_kwargs={}, response_metadata={})
        ],
        "summary": "",
        "stage": "0",
    }
    return {"message": "User created successfully."}


@app.post(ASK_ENDPOINT)
async def ask_endpoint(request: UserInput):
    user_text = request.user_text
    user_id = request.user_id

    conversation_state = app.state.conversations[user_id]

    # Process user input and get updated conversation state
    updated_conversation, user_stage, user_info = hr_bot.ask(
        user_text, conversation_state
    )

    # Extract the latest bot response
    latest_response = updated_conversation["messages"][-1].content

    # Save the updated state back into app.state
    app.state.conversations[user_id] = updated_conversation
    app.state.conversations[user_id]["stage"] = user_stage
    print(f"Updated conversation: {updated_conversation}")
    if user_info:
        SUPABASE_WRITER.save_user_summary(user_id=user_id, summary=user_info)
    return {"response": latest_response, "user_info": user_info}


@app.post("/notion")
async def notion_endpoint(request: dict):
    user_id = request.get("user_id")

    # Fetch notion data
    notion_data = NOTION_SERVICE.fetch_page_recursively(
        os.getenv("NOTION_ROOT_PAGE_ID")
    )

    SUPABASE_WRITER.save_hr_scripts(notion_data)
    return {"response": notion_data}


@app.post(WAZZAP_ENDPOINT)
async def wazzup_webhook(request: Request):
    try:
        payload = await request.json()
        logger.info(f"Incoming Wazzup message: {payload}")

        messages = payload.get("messages", [])
        for message in messages:
            # Skip if message is from bot or is an echo
            if message.get("messageFrom") == "business" or message.get("isEcho"):
                continue

            # Only process text messages
            if message.get("type") != "text":
                continue

            user_id = message.get("chatId")
            user_text = message.get("text")
            channel_id = message.get("channelId")

            # Process valid text messages
            if user_id and user_text:
                if user_id not in app.state.conversations:
                    await create_user({"user_id": user_id})

                updated_conversation, user_stage, user_info = hr_bot.ask(
                    user_text, app.state.conversations[user_id]
                )

                # Save the conversation
                app.state.conversations[user_id] = updated_conversation
                app.state.conversations[user_id]["stage"] = user_stage

                bot_response = updated_conversation["messages"][-1].content
                send_wazzup_message(user_id, bot_response, channel_id)

                if user_info:
                    SUPABASE_WRITER.save_user_summary(
                        user_id=user_id, summary=user_info
                    )
                    user_info["messenger"] = "whatsapp"
                    await send_user_info(telegram_bot, user_info)

        return {"status": "received"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}


def send_wazzup_message(user_id: str, message: str, channel_id: str):
    url = "https://api.wazzup24.com/v3/message"  # URL for sending messages via Wazzup
    headers = {
        "Authorization": "Bearer " + os.getenv("WAZZUP_TOKEN"),
        "Content-Type": "application/json",
    }

    payload = {
        "channelId": channel_id,  # The channelId from the incoming message
        "chatId": user_id,  # The chatId from the incoming message (phone number or user identifier)
        "chatType": "whatsapp",  # The chat type (WhatsApp in this case)
        "text": message,  # The message content (response from your bot)
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            logger.info(f"Successfully sent message to {user_id} via WhatsApp")
        else:
            logger.error(
                f"Failed to send message: {response.status_code} - {response.text}"
            )
    except Exception as e:
        logger.error(f"Error while sending message: {e}")


@app.get(GET_CONVERSATIONS_ENDPOINT)
async def export_conversations():
    conversations = SUPABASE_WRITER.load_conversations()
    return conversations


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
