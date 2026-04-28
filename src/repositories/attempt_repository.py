from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.model.domain.attempt import TestAttempt, ProctoringEvent, StudentAnswer
from src.model.domain.enums import AttemptStatus
from src.repositories.base_repository import BaseRepository


class AttemptRepository(BaseRepository[TestAttempt]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=TestAttempt)

    async def finish_attempt(self, attempt: TestAttempt) -> None:
        """Помечает попытку как завершенную и фиксирует время."""
        attempt.status = AttemptStatus.COMPLETED
        attempt.end_time = datetime.now(timezone.utc)
        await self._session.flush()


class ProctoringRepository(BaseRepository[ProctoringEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ProctoringEvent)

    async def clear_by_attempt_id(self, attempt_id: int) -> None:
        """Удаляет все события прокторинга для указанной попытки."""
        stmt = delete(self.model).where(self.model.attempt_id == attempt_id)
        await self._session.execute(stmt)
        await self._session.flush()

    async def clear_all(self) -> None:
        """Удаляет вообще все события прокторинга из базы данных."""
        stmt = delete(self.model)
        await self._session.execute(stmt)
        await self._session.flush()


class StudentAnswerRepository(BaseRepository[StudentAnswer]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=StudentAnswer)
