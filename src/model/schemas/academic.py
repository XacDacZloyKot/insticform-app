from typing import Optional
from pydantic import BaseModel, ConfigDict

class GroupBase(BaseModel):
    """Базовая схема учебной группы."""
    name: str

class GroupResponse(GroupBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DisciplineBase(BaseModel):
    """Базовая схема учебной дисциплины."""
    name: str
    description: Optional[str] = None

class DisciplineResponse(DisciplineBase):
    id: int
    model_config = ConfigDict(from_attributes=True)