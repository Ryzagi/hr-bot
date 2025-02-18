import os
from typing import Dict, Tuple

from dotenv import load_dotenv
from langchain_core.load import loads
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import PydanticToolsParser
from langchain_openai import ChatOpenAI

from assistant.app.data import ModelOutputResponseFormat, CandidateInformation
from assistant.core.constants import SCRIPT_PROMPT, SYSTEM_PROMPT

load_dotenv()


class HRChatBot:
    def __init__(self, model_name="gpt-4o-mini", max_messages=10):
        """
        Initialize the summarizing chatbot.

        Args:
            model_name (str): The OpenAI model to use.
            max_messages (int): Number of messages before summarizing.
        """
        # Chat model for answering and summarizing
        api_key = os.getenv("OPENAI_API")
        self.model = ChatOpenAI(model=model_name, temperature=0, api_key=api_key).with_structured_output(
            ModelOutputResponseFormat)

        #self.candidate_output_model = ChatOpenAI(model=model_name, temperature=0, api_key=api_key).bind_tools([CandidateInformation])
        #self.candidate_output_model = self.candidate_output_model | PydanticToolsParser(tools=CandidateInformation)

        self.candidate_output_model = ChatOpenAI(model=model_name, temperature=0, api_key=api_key).with_structured_output(CandidateInformation)

        # Initialize conversation state
        self.messages = []
        self.summary = ""
        self.max_messages = max_messages

        self._system_prompt = [SystemMessage(content=SYSTEM_PROMPT)]
        self._script_prompt = [SystemMessage(content=SCRIPT_PROMPT)]

    def _summarize_conversation(self):
        """
        Summarize the current conversation and update the summary.
        """
        if self.summary:
            summary_prompt = (
                f"Это саммари беседы до сих пор: {self.summary}\n\n"
                "Пожалуйста, расширьте саммари, включив новые сообщения выше и оставь данные кандидата (Название вакансии, график работы, ФИО, дата рождения, город, метро, гражданство, документы, номер телефона, дата и время интервью)."
            )
        else:
            summary_prompt = "Суммаризуй беседу выше, сохранив данные кандидата (Название вакансии, график работы, ФИО, дата рождения, город, метро, гражданство, документы, номер телефона, дата и время интервью)."

        # Add a prompt to summarize the conversation
        messages_for_summary = self.messages + [HumanMessage(content=summary_prompt)]
        response = self.model.invoke(messages_for_summary)

        # Update summary and keep recent messages
        self.summary = response.content
        self.messages = self.messages[-2:]  # Keep only the last two messages

    def ask(self, user_input: str, conversation_state: Dict) -> Tuple[Dict, int, Dict]:
        """
        Process a user input, summarize if needed, and return the AI response.

        Args:
            user_input (str): The user input message.
            user_config (dict): The user's configuration (role and animal).
            conversation_state (dict): The conversation state, including messages and summary.

        Returns:
            dict: Updated conversation state with new messages and summary.
        """
        user_info = None
        print("TYpe of conversation_state", type(conversation_state))
        # Extract messages and summary
        if isinstance(conversation_state, str):
            conversation_state = loads(conversation_state)  # Convert JSON string to dictionary
        print(conversation_state, type(conversation_state))
        user_conversation = conversation_state["messages"]
        summary = conversation_state.get("summary", "")

        # Add user input to messages
        user_conversation.append(HumanMessage(content=user_input))

        # Insert summary if available
        if summary:
            summary_system_message = SystemMessage(content=f"Summary of conversation so far: {summary}")
            messages_to_send = self._system_prompt + self._script_prompt + [summary_system_message] + user_conversation
        else:
            messages_to_send = self._system_prompt + self._script_prompt + self._script_prompt + user_conversation

        response = self.model.invoke(messages_to_send)
        print(response.content)
        print("Stage: ", response.stage)

        user_conversation.append(AIMessage(content=response.content))

        # Summarize if message count exceeds the threshold
        if len(user_conversation) > self.max_messages:
            self.messages = user_conversation  # Update messages for summarization
            self.summary = summary  # Preserve existing summary
            self._summarize_conversation()
            conversation_state["summary"] = self.summary  # Update the summary
            conversation_state["messages"] = self.messages[-2:]  # Keep only the last two messages
        else:
            conversation_state["messages"] = user_conversation

        if conversation_state.get("stage") == 7:
            messages_to_send = conversation_state["messages"] + [SystemMessage(content=conversation_state["summary"])]

            print("Messages: ", messages_to_send)
            print("User conversation: ", conversation_state)
            user_info = self.candidate_output_model.invoke(messages_to_send)
            print("User info: ", user_info)

        return conversation_state, response.stage, user_info
