from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.model.domain.base import Base, BaseWithoutId

if TYPE_CHECKING:
    from src.model.domain import Test, User


# Таблицы связи
class StudentGroupLink(BaseWithoutId):
    """Связь: Студент состоит в Группе."""
    __tablename__ = "student_group_link"

    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)


class TeacherDisciplineLink(BaseWithoutId):
    """Связь: Преподаватель ведет Дисциплину."""
    __tablename__ = "teacher_discipline_link"

    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    discipline_id: Mapped[int] = mapped_column(ForeignKey("disciplines.id", ondelete="CASCADE"), primary_key=True)


class GroupDisciplineLink(BaseWithoutId):
    """Связь: Группа изучает Дисциплину."""
    __tablename__ = "group_discipline_link"

    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    discipline_id: Mapped[int] = mapped_column(ForeignKey("disciplines.id", ondelete="CASCADE"), primary_key=True)


class Group(Base):
    """Академическая учебная группа."""
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(String(100), unique=True)

    students: Mapped[List["User"]] = relationship(secondary="student_group_link", back_populates="groups")
    disciplines: Mapped[List["Discipline"]] = relationship(secondary="group_discipline_link", back_populates="groups")


class Discipline(Base):
    """Учебная дисциплина (предмет)."""
    __tablename__ = "disciplines"

    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[Optional[str]] = mapped_column(Text)

    teachers: Mapped[List["User"]] = relationship(secondary="teacher_discipline_link",
                                                  back_populates="taught_disciplines")
    groups: Mapped[List["Group"]] = relationship(secondary="group_discipline_link", back_populates="disciplines")
    tests: Mapped[List["Test"]] = relationship(back_populates="discipline")