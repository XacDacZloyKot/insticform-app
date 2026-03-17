from fastapi import Depends

from src.db.connection import get_uow_dependency
from src.db.uow import UnitOfWork
from src.repositories.user_repository import UserRepository
from src.repositories.academic_repository import GroupRepository, DisciplineRepository
from src.services.academic_service import AcademicService
from src.services.user_service import UserService


def get_user_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> UserRepository:
    """
    Создает репозиторий пользователей.
    FastAPI создает uow, а мы достаем из него сессию и прокидываем в репозиторий.
    """
    return UserRepository(uow.session)


def get_group_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> GroupRepository:
    """
    Создает репозиторий групп.
    """
    return GroupRepository(uow.session)


def get_discipline_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> DisciplineRepository:
    """
    Создает репозиторий дисциплин.
    """
    return DisciplineRepository(uow.session)


def get_user_service(repository: UserRepository = Depends(get_user_repository)) -> UserService:
    """Создает сервис пользователей, прокидывая в него репозиторий пользователей."""
    return UserService(repository)


def get_academic_service(
        group_repo: GroupRepository = Depends(get_group_repository),
        discipline_repo: DisciplineRepository = Depends(get_discipline_repository)) -> AcademicService:
    """Создает сервис для академических сущностей, прокидывая в него репозитории групп и дисциплин."""
    return AcademicService(group_repo, discipline_repo)
