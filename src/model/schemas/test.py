from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from src.model.domain.enums import GradingMethod, QuestionType

class AnswerOptionBase(BaseModel):
    text: str

class AnswerOptionCreate(AnswerOptionBase):
    """Схема для создания варианта ответа (содержит веса и правильность)"""
    is_correct: bool = False
    score_weight: float = 1.0

class AnswerOptionStudentResponse(AnswerOptionBase):
    """БЕЗОПАСНАЯ схема для студента: отдаем только ID и текст, никаких правильных ответов!"""
    id: int
    model_config = ConfigDict(from_attributes=True)

class AnswerOptionTeacherResponse(AnswerOptionStudentResponse):
    """Схема для преподавателя/админа: содержит правильные ответы и веса"""
    is_correct: bool
    score_weight: float


class QuestionBase(BaseModel):
    text: str
    media_url: Optional[str] = None
    type: QuestionType
    time_limit_seconds: Optional[int] = None
    allow_partial_credit: bool = False

class QuestionCreate(QuestionBase):
    """Позволяет создать вопрос сразу с вариантами ответов"""
    options: List[AnswerOptionCreate] = []

class QuestionStudentResponse(QuestionBase):
    id: int
    options: List[AnswerOptionStudentResponse] = []
    model_config = ConfigDict(from_attributes=True)

class QuestionTeacherResponse(QuestionBase):
    id: int
    options: List[AnswerOptionTeacherResponse] = []
    model_config = ConfigDict(from_attributes=True)


class TestBase(BaseModel):
    title: str
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    shuffle_questions: bool = False
    questions_to_show: Optional[int] = None
    grading_method: GradingMethod = GradingMethod.AUTO

class TestCreate(TestBase):
    """Позволяет создать тест сразу со всеми вопросами и ответами одним JSON"""
    discipline_id: int
    questions: List[QuestionCreate] = []

class TestStudentResponse(TestBase):
    """Безопасная схема отдачи теста студенту"""
    id: int
    discipline_id: int
    creator_id: Optional[int] = None
    questions: List[QuestionStudentResponse] = []
    model_config = ConfigDict(from_attributes=True)

class TestTeacherResponse(TestBase):
    """Полная схема отдачи теста для режима редактирования"""
    id: int
    discipline_id: int
    creator_id: Optional[int] = None
    questions: List[QuestionTeacherResponse] = []
    model_config = ConfigDict(from_attributes=True)