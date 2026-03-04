from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Text, ForeignKey, Float, DateTime, Enum, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.model.domain.base import Base, BaseWithoutId
from src.model.domain.enums import AttemptStatus, ProctoringAction

if TYPE_CHECKING:
    from src.model.domain import Test, User, Question, AnswerOption


class StudentAnswerOptionLink(BaseWithoutId):
    """Связь: Какие конкретно варианты выбрал студент в рамках своего ответа."""
    __tablename__ = "student_answer_option_link"

    student_answer_id: Mapped[int] = mapped_column(ForeignKey("student_answers.id", ondelete="CASCADE"),
                                                   primary_key=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("answer_options.id", ondelete="CASCADE"), primary_key=True)


class TestAttempt(Base):
    """Попытка сдачи теста студентом."""
    __tablename__ = "test_attempts"

    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    # Используем timezone-aware datetime
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[AttemptStatus] = mapped_column(Enum(AttemptStatus), default=AttemptStatus.IN_PROGRESS)
    total_score: Mapped[Optional[float]] = mapped_column(Float)

    confidence_index: Mapped[Optional[float]] = mapped_column(Float)

    test: Mapped["Test"] = relationship(back_populates="attempts")
    student: Mapped["User"] = relationship(back_populates="test_attempts")
    student_answers: Mapped[List["StudentAnswer"]] = relationship(back_populates="attempt",
                                                                  cascade="all, delete-orphan")
    proctoring_logs: Mapped[List["ProctoringEvent"]] = relationship(back_populates="attempt",
                                                                    cascade="all, delete-orphan")


class StudentAnswer(Base):
    """Ответ студента на один вопрос."""
    __tablename__ = "student_answers"
    __table_args__ = (UniqueConstraint('attempt_id', 'question_id',
                                       name='uq_attempt_question'),)

    attempt_id: Mapped[int] = mapped_column(ForeignKey("test_attempts.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    text_answer: Mapped[Optional[str]] = mapped_column(Text)

    awarded_score: Mapped[Optional[float]] = mapped_column(Float)

    attempt: Mapped["TestAttempt"] = relationship(back_populates="student_answers")
    question: Mapped["Question"] = relationship()

    # Отношение к выбранным вариантам (поддерживает и один, и несколько ответов)
    selected_options: Mapped[List["AnswerOption"]] = relationship(secondary="student_answer_option_link")


class ProctoringEvent(Base):
    """Событие прокторинга (например, переключение вкладки)."""
    __tablename__ = "proctoring_events"

    # Добавляем составной индекс для ускорения аналитических выборок
    __table_args__ = (
        Index('ix_proctoring_event_attempt_timestamp', 'attempt_id', 'timestamp'),
    )

    # Убираем index=True у attempt_id, так как он теперь входит в составной индекс выше
    attempt_id: Mapped[int] = mapped_column(ForeignKey("test_attempts.id", ondelete="CASCADE"))

    action_type: Mapped[ProctoringAction] = mapped_column(Enum(ProctoringAction))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    details: Mapped[Optional[str]] = mapped_column(Text)

    attempt: Mapped["TestAttempt"] = relationship(back_populates="proctoring_logs")
