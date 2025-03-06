import os

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager

from langchain_core.messages import AIMessage
from loguru import logger
from starlette.requests import Request

from assistant.app.data import AppState, UserInput
from assistant.core.constants import CREATE_USER_ENDPOINT, ASK_ENDPOINT, START_MESSAGE
from assistant.generator import HRChatBot
from assistant.database.supabase_service import SupabaseService
from assistant.notion_service import NotionParser

load_dotenv()

#HISTORY_WRITER = HistoryWriter()
#USER_STATUSES = HISTORY_WRITER.load_user_statuses()
#CONVERSATIONS = HISTORY_WRITER.load_user_conversations()


hr_bot = HRChatBot()
SUPABASE_WRITER = SupabaseService(supabase_url=os.getenv("SUPABASE_URL"), supabase_key=os.getenv("SUPABASE_KEY"))
CONVERSATIONS = SUPABASE_WRITER.load_conversations()
NOTION_SERVICE = NotionParser(api_key=os.getenv("NOTION_API_KEY"), page_id=os.getenv("NOTION_ROOT_PAGE_ID"))

def register_wazzup_webhook():
    url = "https://api.wazzup24.com/v3/webhooks"
    headers = {
        "Authorization": f"Bearer {os.getenv('WAZZUP_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {
        "webhooksUri": os.getenv("WAZZUP_WEBHOOK_URL"),
        "subscriptions": {
            "messagesAndStatuses": True
        }
    }
    response = requests.patch(url, headers=headers, json=payload)
    logger.info(f"Wazzup Webhook Registration: {response.status_code}, {response.json()}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    # Load all user statuses and conversations
    app.state = AppState()
    app.state.conversations = CONVERSATIONS

    print("CONVERSATIONS", app.state.conversations)

    register_wazzup_webhook()  # Register webhook on startup

    yield  # Application is running

    # On shutdown, save all statuses and conversations
    #HISTORY_WRITER.save_user_conversations(app.state.conversations)
    SUPABASE_WRITER.save_conversations(app.state.conversations)
    logger.info("Conversation and user statuses saved, application shutting down.")


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def root():
    return {"message": "OK"}


@app.post(CREATE_USER_ENDPOINT)
async def create_user(data: dict) -> dict:
    user_id = data.get("user_id")
    #HISTORY_WRITER.create_json_file(user_id=user_id)
    await SUPABASE_WRITER.add_new_user(user_data=data)
    app.state.conversations[user_id] = {
        "messages": [AIMessage(content=START_MESSAGE, additional_kwargs={}, response_metadata={})], "summary": "",
        "stage": "0"}
    return {"message": "User created successfully."}


@app.post(ASK_ENDPOINT)
async def ask_endpoint(request: UserInput):
    user_text = request.user_text
    user_id = request.user_id

    conversation_state = app.state.conversations[user_id]

    # Process user input and get updated conversation state
    updated_conversation, user_stage, user_info = hr_bot.ask(user_text, conversation_state)

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
    notion_data = NOTION_SERVICE.fetch_page_recursively(os.getenv("NOTION_ROOT_PAGE_ID"))

    SUPABASE_WRITER.save_hr_scripts(notion_data)
    return {"response": notion_data}


@app.post("/wazzup-webhook")
async def wazzup_webhook(request: Request):
    try:
        payload = await request.json()
        logger.info(f"Incoming Wazzup message: {payload}")

        messages = payload.get("messages", [])
        for message in messages:
            user_id = message.get("chat_id")
            user_text = message.get("text")

            if user_id and user_text:
                updated_conversation, user_stage, user_info = hr_bot.ask(user_text, app.state.conversations[user_id])

                # Save the conversation
                app.state.conversations[user_id] = updated_conversation
                app.state.conversations[user_id]["stage"] = user_stage

                bot_response = updated_conversation["messages"][-1].content
                send_wazzup_message(user_id, bot_response)

                if user_info:
                    SUPABASE_WRITER.save_user_summary(user_id=user_id, summary=user_info)

        return {"status": "received"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}

def send_wazzup_message(chat_id: str, text: str):
    headers = {
        "Authorization": f"Bearer {os.getenv('WAZZUP_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel_id": os.getenv("WAZZUP_CHANNEL_ID"),
        "chat_id": chat_id,
        "text": text
    }

    response = requests.post(os.getenv("WAZZUP_API_URL"), headers=headers, json=payload)
    logger.info(f"Message sent to {chat_id}: {response.status_code}, {response.json()}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
