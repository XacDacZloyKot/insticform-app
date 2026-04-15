from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from src.model.domain.enums import AttemptStatus, ProctoringAction


class ProctoringEventBase(BaseModel):
    action_type: ProctoringAction
    details: Optional[str] = None


class ProctoringEventCreate(ProctoringEventBase):
    attempt_id: int


class ProctoringEventResponse(ProctoringEventBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


class StudentAnswerBase(BaseModel):
    question_id: int
    text_answer: Optional[str] = None
    time_spent_seconds: Optional[int] = None
    selected_option_ids: List[int] = []


class StudentAnswerCreate(StudentAnswerBase):
    pass


class StudentAnswerResponse(StudentAnswerBase):
    id: int
    is_correct: Optional[bool] = None
    score_awarded: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


class TestAttemptBase(BaseModel):
    test_id: int
    student_id: int


class TestAttemptResponse(TestAttemptBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: AttemptStatus
    total_score: Optional[float] = None
    confidence_index: Optional[float] = None
    proctoring_logs: List[ProctoringEventResponse] = []

    answers: List[StudentAnswerResponse] = []

    model_config = ConfigDict(from_attributes=True)