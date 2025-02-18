from typing_extensions import Annotated, TypedDict

from pydantic import BaseModel, Field


class UserInput(BaseModel):
    user_text: str
    user_id: str


class ModelOutputResponseFormat(BaseModel):
    """Model output response."""

    content: str = Field(description="Answer for the user query.")
    stage: int = Field(description="State of the conversation.")


class CandidateInformation(TypedDict):
    """Candidate information from the conversation."""
    vacancy: Annotated[str, ..., "Название вакансии"]
    schedule: Annotated[str, ..., "График работы"]
    full_name: Annotated[str, ..., "ФИО"]
    date_of_birth: Annotated[str, ..., "Дата рождения"]
    city: Annotated[str, ..., "Город"]
    metro: Annotated[str, ..., "Метро"]
    citizenship: Annotated[str, ..., "Гражданство"]
    documents: Annotated[str, ..., "Документы"]
    phone_number: Annotated[str, ..., "Номер телефона"]
    interview_date: Annotated[str, ..., "Дата интервью"]
    interview_time: Annotated[str, ..., "Время интервью"]


class AppState(BaseModel):
    user_statuses: dict[str, str] = Field(default_factory=dict)
    conversations: dict[str, list[str]] = Field(default_factory=dict)
