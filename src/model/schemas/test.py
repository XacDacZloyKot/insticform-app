from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from src.model.domain.enums import GradingMethod, QuestionType

# --- Варианты ответов ---
class AnswerOptionBase(BaseModel):
    text: str
    is_correct: bool = False
    score_weight: float = 1.0

class AnswerOptionResponse(AnswerOptionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Вопросы ---
class QuestionBase(BaseModel):
    text: str
    media_url: Optional[str] = None
    type: QuestionType
    time_limit_seconds: Optional[int] = None
    allow_partial_credit: bool = False

class QuestionResponse(QuestionBase):
    id: int
    options: List[AnswerOptionResponse] = [] # Вкладываем варианты ответов
    model_config = ConfigDict(from_attributes=True)

# --- Тесты ---
class TestBase(BaseModel):
    title: str
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    shuffle_questions: bool = False
    questions_to_show: Optional[int] = None
    grading_method: GradingMethod = GradingMethod.AUTO

class TestResponse(TestBase):
    id: int
    discipline_id: int
    creator_id: Optional[int] = None
    questions: List[QuestionResponse] = []
    model_config = ConfigDict(from_attributes=True)