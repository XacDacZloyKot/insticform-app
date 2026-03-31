from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, Boolean, Float, Enum, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.model.domain.base import Base
from src.model.domain.enums import GradingMethod, QuestionType, MediaType

if TYPE_CHECKING:
    from src.model.domain import Discipline, TestAttempt, User

test_student_association = Table(
    "test_student_association",
    Base.metadata,
    Column("test_id", Integer, ForeignKey("tests.id", ondelete="CASCADE"), primary_key=True),
    Column("student_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)


class Test(Base):
    """Сам тест с настройками."""
    __tablename__ = "tests"

    discipline_id: Mapped[int] = mapped_column(ForeignKey("disciplines.id", ondelete="CASCADE"))
    creator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)

    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False)
    questions_to_show: Mapped[Optional[int]] = mapped_column(Integer)
    grading_method: Mapped[GradingMethod] = mapped_column(Enum(GradingMethod), default=GradingMethod.AUTO)

    assigned_students: Mapped[List["User"]] = relationship("User", secondary=test_student_association,
                                                           backref="assigned_tests")

    media_files: Mapped[List["TestMedia"]] = relationship(back_populates="test", cascade="all, delete-orphan")

    discipline: Mapped["Discipline"] = relationship(back_populates="tests")
    creator: Mapped[Optional["User"]] = relationship()
    questions: Mapped[List["Question"]] = relationship(back_populates="test", cascade="all, delete-orphan")
    attempts: Mapped[List["TestAttempt"]] = relationship(back_populates="test")


class Question(Base):
    """Вопрос внутри теста."""
    __tablename__ = "questions"

    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"))

    text: Mapped[str] = mapped_column(Text)
    media_url: Mapped[Optional[str]] = mapped_column(String(255))
    type: Mapped[QuestionType] = mapped_column(Enum(QuestionType))
    time_limit_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    allow_partial_credit: Mapped[bool] = mapped_column(Boolean, default=False)
    media_type: Mapped[Optional[MediaType]] = mapped_column(Enum(MediaType), nullable=True,
                                                            doc="Тип прикрепленного медиа")

    test: Mapped["Test"] = relationship(back_populates="questions")
    options: Mapped[List["AnswerOption"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class AnswerOption(Base):
    """Вариант ответа на вопрос."""
    __tablename__ = "answer_options"

    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))

    text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    score_weight: Mapped[float] = mapped_column(Float, default=1.0)

    question: Mapped["Question"] = relationship(back_populates="options")


class TestMedia(Base):
    """Медиафайлы, прикрепленные к тесту."""
    __tablename__ = "test_media"

    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"))

    file_path: Mapped[str] = mapped_column(String(255), doc="Относительный путь к файлу")
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType), doc="Тип медиа (image, video, audio)")
    original_filename: Mapped[str] = mapped_column(String(255), doc="Оригинальное имя файла")

    test: Mapped["Test"] = relationship(back_populates="media_files")
