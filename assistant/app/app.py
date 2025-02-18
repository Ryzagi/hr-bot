import os

from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager

from langchain_core.messages import AIMessage
from loguru import logger

from assistant.app.data import AppState, UserInput
from assistant.core.constants import CREATE_USER_ENDPOINT, ASK_ENDPOINT, START_MESSAGE
from assistant.generator import HRChatBot
from assistant.database.supabase_service import SupabaseService

load_dotenv()

#HISTORY_WRITER = HistoryWriter()
#USER_STATUSES = HISTORY_WRITER.load_user_statuses()
#CONVERSATIONS = HISTORY_WRITER.load_user_conversations()


hr_bot = HRChatBot()
SUPABASE_WRITER = SupabaseService(supabase_url=os.getenv("SUPABASE_URL"), supabase_key=os.getenv("SUPABASE_KEY"))
CONVERSATIONS = SUPABASE_WRITER.load_conversations()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    # Load all user statuses and conversations
    app.state = AppState()
    app.state.conversations = CONVERSATIONS
    print("CONVERSATIONS", app.state.conversations)

    yield  # Application is running
    print("CONVERSATIONS", app.state.conversations)
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
