from typing import Dict, Union

from langchain_core.load import dumps, loads
from supabase import create_client, Client


class SupabaseService:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_client: Client = create_client(supabase_url, supabase_key)
        self.bucket_name: str = "tasks"
        self._users_table = "users"
        self._conversations_table = "conversations"
        self._prompts_table = "hr_scripts"
        self._summary_table = "user_summaries"

    async def add_new_user(self, user_data: dict) -> Dict[str, Union[str, int]]:
        # Add a new user to the "users" table in Supabase, if the user does not already exist
        user_id = user_data.get("user_id")
        if await self.is_exist(user_id):
            return {"message": "User already exists", "status_code": 200}
        try:
            self.supabase_client.table(self._users_table).insert(user_data).execute()
            #self.supabase_client.table(self._users_status_table).insert(
            #    {"user_id": user_id, "last_processing_date": None, "daily_limit": DEFAULT_DAILY_LIMIT,
            #     "subscription_limit": 0}).execute()
            return {"message": "User added successfully", "status_code": 200}
        except Exception as e:
            return {"message": "Failed to add user", "status_code": str(e)}

    async def is_exist(self, user_id: str) -> bool:
        # Check if the user with the given user_id exists in the Supabase table
        data = self.supabase_client.table(self._users_table).select("user_id").eq("user_id", user_id).execute()
        print(data)
        print(data.data)
        return len(data.data) > 0

    def save_conversations(self, conversations: dict) -> Dict[str, Union[str, int]]:
        # Insert the solution into the "tasks" table in Supabase
        try:
            for user_id, conversation in conversations.items():
                print("User ID", user_id, "Conversation", conversation)
                data_to_insert = {"user_id": user_id, "conversation": dumps(conversation, ensure_ascii=False, indent=4, pretty=True)}
                print("Data to insert", data_to_insert)
                # Insert the conversation into the "conversations" table in Supabase for each user ID
                response = self.supabase_client.table(self._conversations_table).insert(data_to_insert).execute()
                print("Conversations inserted", response)
            return {"message": "Conversations inserted successfully", "status_code": 200}
        except Exception as e:
            return {"message": "Failed to insert conversations", "status_code": str(e)}


    def load_conversations(self):
        # Load all conversations from the "conversations" table in Supabase
        data = self.supabase_client.table(self._conversations_table).select("user_id, conversation").execute()
        if data.data:
            print("Conversations loaded", data)
            return {row["user_id"]: loads(row["conversation"]) for row in data.data}
        return {}

    def save_user_summary(self, user_id: str, summary: dict) -> Dict[str, Union[str, int]]:
        try:
            print("User ID", user_id, "Summary", summary)
            summary["user_id"] = user_id
            response = self.supabase_client.table(self._summary_table).insert(summary).execute()
            return {"message": "User summary updated successfully", "status_code": 200}
        except Exception as e:
            return {"message": "Failed to update user summary", "status_code": str(e)}
