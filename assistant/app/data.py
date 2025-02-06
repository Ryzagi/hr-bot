from pydantic import BaseModel, Field


class UserInput(BaseModel):
    user_text: str
    user_id: str


class ModelOutputResponseFormat(BaseModel):
    """Model output response."""

    content: str = Field(description="Answer for the user query.")
    stage: int = Field(description="State of the conversation.")


class CandidateInformation(BaseModel):
    """Candidate information from the conversation."""

    vacancy: str = Field(..., description="Название вакансии")
    schedule: str = Field(..., description="График работы")
    full_name: str = Field(..., description="ФИО")
    date_of_birth: str = Field(..., description="Дата рождения")
    city: str = Field(..., description="Город")
    metro: str = Field(..., description="Метро")
    citizenship: str = Field(..., description="Гражданство")
    documents: str = Field(..., description="Документы")
    phone_number: str = Field(..., description="Номер телефона")
    interview_date: str = Field(..., description="Дата и время интервью")


class AppState(BaseModel):
    user_statuses: dict[str, str] = Field(default_factory=dict)
    conversations: dict[str, list[str]] = Field(default_factory=dict)
