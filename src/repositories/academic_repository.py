from sqlalchemy.ext.asyncio import AsyncSession
from src.model.domain.academic import Group, Discipline
from src.model.domain.user import User
from src.repositories.base_repository import BaseRepository

class GroupRepository(BaseRepository[Group]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Group)

    async def add_student(self, group: Group, student: User) -> None:
        if student not in group.students:
            group.students.append(student)
            await self._session.flush()

    async def remove_student(self, group: Group, student: User) -> None:
        if student in group.students:
            group.students.remove(student)
            await self._session.flush()


class DisciplineRepository(BaseRepository[Discipline]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Discipline)

    async def add_teacher(self, discipline: Discipline, teacher: User) -> None:
        if teacher not in discipline.teachers:
            discipline.teachers.append(teacher)
            await self._session.flush()

    async def remove_teacher(self, discipline: Discipline, teacher: User) -> None:
        if teacher in discipline.teachers:
            discipline.teachers.remove(teacher)
            await self._session.flush()