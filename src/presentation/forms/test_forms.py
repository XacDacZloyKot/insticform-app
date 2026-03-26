from fastapi import Form
from typing import Optional
from src.model.domain.enums import GradingMethod

def create_test_form(
    title: str = Form(..., description="Название теста"),
    discipline_id: int = Form(..., description="ID дисциплины"),
    description: Optional[str] = Form(None, description="Описание"),
    time_limit_minutes: Optional[int] = Form(None, description="Лимит в минутах"),
    shuffle_questions: bool = Form(False, description="Перемешивать вопросы"),
    grading_method: GradingMethod = Form(GradingMethod.AUTO)
) -> dict:
    return {
        "title": title,
        "discipline_id": discipline_id,
        "description": description,
        "time_limit_minutes": time_limit_minutes,
        "shuffle_questions": shuffle_questions,
        "grading_method": grading_method
    }