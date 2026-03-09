from src.model.domain.base import Base, BaseWithoutId, AbstractBase

from src.model.domain.user import User
from src.model.domain.academic import Group, Discipline, StudentGroupLink, TeacherDisciplineLink, GroupDisciplineLink
from src.model.domain.test import Test, Question, AnswerOption
from src.model.domain.attempt import TestAttempt, StudentAnswer, ProctoringEvent, StudentAnswerOptionLink

__all__ = [
    "Base",
    "BaseWithoutId",
    "AbstractBase",
    "User",
    "Group",
    "Discipline",
    "StudentGroupLink",
    "TeacherDisciplineLink",
    "GroupDisciplineLink",
    "Test",
    "Question",
    "AnswerOption",
    "TestAttempt",
    "StudentAnswer",
    "ProctoringEvent",
    "StudentAnswerOptionLink",
]