from fastapi import Form, HTTPException, status
from pydantic import BaseModel, ValidationError

from src.model.domain.enums import UserRole
from src.model.schemas.user import UserCreate

class UserLoginSchema(BaseModel):
    """Схема для входа пользователя."""
    username: str
    password: str

def registration_form(
        username: str = Form(..., max_length=50, description="Имя пользователя"),
        first_name: str = Form(..., max_length=64, description="Имя"),
        last_name: str = Form(..., max_length=64, description="Фамилия"),
        patronymic: str = Form(None, max_length=64, description="Отчество"),
        password: str = Form(..., min_length=6, max_length=72, description="Пароль")
) -> UserCreate:
    try:
        return UserCreate(
            username=username,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic or "",
            password=password,
            role=UserRole.STUDENT
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

def login_form(
        username: str = Form(..., description="Имя пользователя"),
        password: str = Form(..., description="Пароль")
) -> UserLoginSchema:
    return UserLoginSchema(username=username, password=password)