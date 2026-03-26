from sqlalchemy.ext.asyncio import AsyncSession
from src.model.domain.test import Test, TestMedia, Question, AnswerOption
from src.repositories.base_repository import BaseRepository

class TestRepository(BaseRepository[Test]):
    """Репозиторий для работы с тестами."""
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Test)

class TestMediaRepository(BaseRepository[TestMedia]):
    """Репозиторий для работы с медиафайлами тестов."""
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=TestMedia)

class QuestionRepository(BaseRepository[Question]):
    """Репозиторий для работы с вопросами."""
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Question)

class AnswerOptionRepository(BaseRepository[AnswerOption]):
    """Репозиторий для работы с вариантами ответов."""
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=AnswerOption)