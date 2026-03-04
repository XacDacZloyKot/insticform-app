from typing import List, TYPE_CHECKING, Optional
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.model.domain.base import Base
from src.model.domain.enums import UserRole

if TYPE_CHECKING:
    from src.model.domain import Group, Discipline, TestAttempt


class User(Base):
    """Модель пользователя системы (Студент, Преподаватель, Администратор)."""
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, doc="Пользовательское имя")
    hashed_password: Mapped[str] = mapped_column(String(255), doc="Зашифрованный пароль")
    first_name: Mapped[str] = mapped_column(String(64), doc="Имя")
    last_name: Mapped[str] = mapped_column(String(64), doc="Фамилия")
    patronymic: Mapped[Optional[str]] = mapped_column(String(64), doc="Отчество")
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STUDENT, index=True, doc="Роль")

    groups: Mapped[List["Group"]] = relationship(secondary="student_group_link", back_populates="students")
    taught_disciplines: Mapped[List["Discipline"]] = relationship(secondary="teacher_discipline_link",
                                                                  back_populates="teachers")
    test_attempts: Mapped[List["TestAttempt"]] = relationship(back_populates="student")

    repr_cols = ("username", "role")
