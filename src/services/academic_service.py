from typing import List

from sqlalchemy.orm import selectinload

from src.model.domain.academic import Group, Discipline
from src.model.domain.user import User
from src.model.schemas.academic import GroupBase, DisciplineBase
from src.repositories.academic_repository import GroupRepository, DisciplineRepository


class AcademicService:
    def __init__(self, group_repo: GroupRepository, discipline_repo: DisciplineRepository):
        self.group_repo = group_repo
        self.discipline_repo = discipline_repo

    # СОЗДАНИЕ
    async def create_group(self, group_data: GroupBase) -> Group:
        existing = await self.group_repo.find_first(name=group_data.name)
        if existing:
            raise ValueError(f"Группа '{group_data.name}' уже существует.")
        new_group = Group(name=group_data.name)
        return await self.group_repo.create(new_group)

    async def create_discipline(self, discipline_data: DisciplineBase) -> Discipline:
        new_discipline = Discipline(name=discipline_data.name, description=discipline_data.description)
        return await self.discipline_repo.create(new_discipline)

    # ЧТЕНИЕ СПИСКОВ
    async def list_groups(self) -> List[Group]:
        return await self.group_repo.list()

    async def list_disciplines(self) -> List[Discipline]:
        return await self.discipline_repo.list()

    # ЧТЕНИЕ ОДНОЙ СУЩНОСТИ
    async def get_group_by_id(self, group_id: int) -> Group:
        return await self.group_repo.get_one(id=group_id)

    async def get_discipline_by_id(self, discipline_id: int) -> Discipline:
        return await self.discipline_repo.get_one(id=discipline_id)

    # УДАЛЕНИЕ
    async def delete_group(self, group_id: int) -> None:
        await self.group_repo.delete(group_id)

    async def delete_discipline(self, discipline_id: int) -> None:
        await self.discipline_repo.delete(discipline_id)

    async def update_group(self, group_id: int, group_data: GroupBase) -> Group:
        group = await self.group_repo.get_one(id=group_id)
        if group.name != group_data.name:
            existing = await self.group_repo.find_first(name=group_data.name)
            if existing:
                raise ValueError(f"Группа '{group_data.name}' уже существует.")

        return await self.group_repo.update(id=group_id, data=group_data.model_dump())

    async def update_discipline(self, discipline_id: int, discipline_data: DisciplineBase) -> Discipline:
        await self.discipline_repo.get_one(id=discipline_id)

        return await self.discipline_repo.update(id=discipline_id, data=discipline_data.model_dump())

    async def get_group_with_relations(self, group_id: int) -> Group:
        """Получает группу вместе со списком студентов"""
        return await self.group_repo.get_one_with_joins(joins=[selectinload(Group.students)], id=group_id)

    async def get_discipline_with_relations(self, discipline_id: int) -> Discipline:
        """Получает дисциплину вместе со списком преподавателей"""
        return await self.discipline_repo.get_one_with_joins(joins=[selectinload(Discipline.teachers)],
                                                             id=discipline_id)

    # --- СВЯЗЫВАНИЕ: ГРУППЫ И СТУДЕНТЫ ---
    async def add_student_to_group(self, group_id: int, student: User) -> None:
        group = await self.get_group_with_relations(group_id)
        await self.group_repo.add_student(group, student)

    async def remove_student_from_group(self, group_id: int, student_id: int) -> None:
        group = await self.get_group_with_relations(group_id)
        student_to_remove = next((s for s in group.students if s.id == student_id), None)
        if student_to_remove:
            await self.group_repo.remove_student(group, student_to_remove)

    # --- СВЯЗЫВАНИЕ: ДИСЦИПЛИНЫ И ПРЕПОДАВАТЕЛИ ---
    async def add_teacher_to_discipline(self, discipline_id: int, teacher: User) -> None:
        discipline = await self.get_discipline_with_relations(discipline_id)
        await self.discipline_repo.add_teacher(discipline, teacher)

    async def remove_teacher_from_discipline(self, discipline_id: int, teacher_id: int) -> None:
        discipline = await self.get_discipline_with_relations(discipline_id)
        teacher_to_remove = next((t for t in discipline.teachers if t.id == teacher_id), None)
        if teacher_to_remove:
            await self.discipline_repo.remove_teacher(discipline, teacher_to_remove)
