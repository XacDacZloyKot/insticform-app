from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class DisciplineBase(BaseModel):
    """Базовая схема учебной дисциплины."""
    name: str
    description: Optional[str] = None


class DisciplineResponse(DisciplineBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class GroupBase(BaseModel):
    """Базовая схема учебной группы."""
    name: str


class GroupResponse(GroupBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class GroupWithDisciplinesResponse(GroupResponse):
    """Схема группы, в которую сразу подгружен список её дисциплин"""
    disciplines: List[DisciplineResponse] = []


class DisciplineWithGroupsResponse(DisciplineResponse):
    """Схема дисциплины, в которую подгружен список изучающих её групп"""
    groups: List[GroupResponse] = []