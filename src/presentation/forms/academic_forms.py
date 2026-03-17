from fastapi import Form
from typing import Optional
from src.model.schemas.academic import GroupBase, DisciplineBase


def create_group_form(name: str = Form(..., description="Название группы")) -> GroupBase:
    return GroupBase(name=name)


def create_discipline_form(
        name: str = Form(..., description="Название дисциплины"),
        description: Optional[str] = Form(None, description="Описание")
) -> DisciplineBase:
    return DisciplineBase(name=name, description=description)
