from pydantic import BaseModel, ConfigDict
from src.model.domain.enums import UserRole


class UserBase(BaseModel):
    """Базовая информация о пользователе."""
    username: str
    first_name: str
    last_name: str
    patronymic: str
    role: UserRole = UserRole.STUDENT


class UserCreate(UserBase):
    """Схема для регистрации (требует пароль)."""
    password: str


class UserResponse(UserBase):
    """Схема для отправки данных клиенту (без пароля, но с ID)."""
    id: int

    model_config = ConfigDict(from_attributes=True)