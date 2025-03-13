import json
import os
import pathlib
from typing import Dict

from langchain_core.load import dumps

from assistant.core.constants import (CONVERSATIONS_DIRECTORY,
                                      USER_STATUSES_DIRECTORY)


class HistoryWriter:
    def __init__(self):
        self._conversation_directory = CONVERSATIONS_DIRECTORY
        self._user_status_directory = USER_STATUSES_DIRECTORY
        self.create_directories()

    def create_directories(self) -> None:
        """Create directories for conversations and user status."""
        self.create_directory(self._conversation_directory)
        self.create_directory(self._user_status_directory)

    @staticmethod
    def create_directory(file_path: str) -> None:
        """Create a directory if it does not exist."""
        try:
            if not os.path.exists(file_path):
                os.makedirs(file_path)
        except Exception as e:
            print(f"Error creating directory: {e}")

    @staticmethod
    def write_json(file_path: pathlib.Path, data: dict) -> None:
        """Write data to a JSON file."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing to JSON file: {e}")

    @staticmethod
    def read_json(file_path: pathlib.Path) -> Dict:
        """Read data string from a JSON file using json.loads()."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data
        except Exception as e:
            print(f"Error reading from JSON file: {e}")

    def load_user_conversations(self) -> Dict:
        """Load all conversations from the conversation directory."""
        return self.load_all_files(self._conversation_directory)

    def load_all_files(self, directory: pathlib.Path) -> Dict:
        """Load all files from a directory to a dictionary using pathlib."""
        data = {}
        for file_path in directory.glob("*.json"):
            file_data = self.read_json(file_path)
            data.update(file_data)
        return data

    def load_user_statuses(self) -> Dict:
        """Load all user status from the user status directory."""
        return self.load_all_files(self._user_status_directory)

    def save_user_conversation(self, user_id: str, conversation: str) -> None:
        """Save a user conversation to a JSON file."""
        file_path = pathlib.Path(self._conversation_directory, f"{user_id}.json")
        data = self.read_json(file_path)
        data[user_id] = conversation
        self.write_json(file_path, data)

    def update_user_status(self, user_id: str, status: str) -> None:
        """Update a user status in a JSON file."""
        file_path = pathlib.Path(self._user_status_directory, f"{user_id}.json")
        data = self.read_json(file_path)
        data[user_id] = status
        self.write_json(file_path, data)

    def save_user_conversations(self, conversations: dict) -> None:
        """Save all user conversations to JSON files."""
        for user_id, conversation in conversations.items():
            # Serialize the conversation dictionary to a JSON-formatted string
            conversation_json = dumps(
                conversation, ensure_ascii=False, indent=4, pretty=True
            )
            self.save_user_conversation(user_id, conversation_json)

    def save_user_statuses(self, statuses: dict) -> None:
        """Save all user statuses to JSON files."""
        # Save dict of user statuses to JSON files
        for user_id, status in statuses.items():
            self.update_user_status(user_id, status)

    @staticmethod
    def create_json_file(user_id: str) -> None:
        """Create a JSON file in the conversation directory and user status directory."""
        conversation_file = os.path.join(CONVERSATIONS_DIRECTORY, f"{user_id}.json")
        status_file = os.path.join(USER_STATUSES_DIRECTORY, f"{user_id}.json")
        # Create empty JSON files with user_id as the key
        with open(conversation_file, "w", encoding="utf-8") as file:
            json.dump({user_id: {"messages": [], "summary": "", "stage": ""}}, file)
        with open(status_file, "w", encoding="utf-8") as file:
            json.dump({user_id: {"role": "", "animal": ""}}, file)
