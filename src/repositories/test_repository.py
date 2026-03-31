from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from src.model.domain.test import Test, TestMedia, Question, AnswerOption
from src.model.domain.user import User
from src.repositories.base_repository import BaseRepository

class TestRepository(BaseRepository[Test]):
    """Репозиторий для работы с тестами."""
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Test)

    async def assign_students(self, test: Test, students: List[User]) -> None:
        for student in students:
            if student not in test.assigned_students:
                test.assigned_students.append(student)
        await self._session.flush()

    async def unassign_student(self, test: Test, student: User) -> None:
        if student in test.assigned_students:
            test.assigned_students.remove(student)
            await self._session.flush()


class TestMediaRepository(BaseRepository[TestMedia]):
    """Репозиторий для работы с медиафайлами тестов."""
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=TestMedia)


class QuestionRepository(BaseRepository[Question]):
    """Репозиторий для работы с вопросами."""
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Question)

    async def remove_media(self, question: Question) -> None:
        """Очищает пути медиафайла у вопроса."""
        question.media_url = None
        question.media_type = None
        await self._session.flush()


class AnswerOptionRepository(BaseRepository[AnswerOption]):
    """Репозиторий для работы с вариантами ответов."""
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=AnswerOption)