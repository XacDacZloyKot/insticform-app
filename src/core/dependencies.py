from fastapi import Depends

from src.db.connection import get_uow_dependency
from src.db.uow import UnitOfWork
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService


def get_user_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> UserRepository:
    """
    Создает репозиторий пользователей.
    FastAPI создает uow, а мы достаем из него сессию и прокидываем в репозиторий.
    """
    return UserRepository(uow.session)


def get_user_service(repository: UserRepository = Depends(get_user_repository)) -> UserService:
    """Создает сервис пользователей, прокидывая в него готовый репозиторий."""
    return UserService(repository)