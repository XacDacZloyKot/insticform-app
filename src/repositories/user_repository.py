import logging
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.utils.auth.password import hash_password
from src.model.domain.user import Users
from src.model.schemas import UserCreateSchema
from src.repositories.base_repository.base_repository import BaseRepository
from src.repositories.base_repository.decorators import with_exception_handling, with_read_operation_handling
from src.repositories.base_repository.exceptions import AlreadyExistsException

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[Users]):
    """
    Репозиторий для работы с пользователями.
    Предоставляет методы для создания, чтения, обновления и удаления пользователей.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Users)

    @with_exception_handling("Ошибка при создании пользователя")
    async def create(self, user_data: UserCreateSchema) -> Users:
        """
        Создает нового пользователя в базе данных.

        :param user_data: Данные для создания пользователя.
        :raises AlreadyExistsException: Если пользователь с таким email или username уже существует.
        """
        existing_user = await self.get_by_username_or_email(
            username=user_data.username,
            email=user_data.email
        )

        if existing_user:
            logger.warning(
                f"Пользователь с email '{user_data.email}' или username '{user_data.username}' уже существует")
            raise AlreadyExistsException(
                error_message=f"Пользователь с такой почтой '{user_data.email}' или именем '{user_data.username}' уже существует",
                class_name=self.model_name
            )

        new_user = Users(
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            patronymic=user_data.patronymic,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
            division=user_data.division,
        )

        result = await super().create(new_user)
        logger.info(f"Создан пользователь {self.model_name}: {result}")
        return result

    @with_read_operation_handling("Ошибка при поиске пользователя по email")
    async def get_by_email(self, email: str) -> Optional[Users]:
        """
        Возвращает пользователя по email.

        :param email: Email пользователя для поиска.
        :return: Пользователь или None, если не найден.
        """
        result = await self.find_first(email=email)
        logger.debug(f"Поиск пользователя по email: {email}")
        return result

    @with_read_operation_handling("Ошибка при поиске пользователя по username")
    async def get_by_username(self, username: str) -> Optional[Users]:
        """
        Возвращает пользователя по username.

        :param username: Имя пользователя для поиска.
        :return: Пользователь или None, если не найден.
        """
        result = await self.find_first(username=username)
        logger.debug(f"Поиск пользователя по username: {username}")
        return result

    @with_read_operation_handling("Ошибка при поиске пользователя по username или email")
    async def get_by_username_or_email(self, username: str, email: str) -> Optional[Users]:
        """
        Возвращает пользователя по username или email.

        :param username: Имя пользователя для поиска.
        :param email: Email пользователя для поиска.
        :return: Пользователь или None, если не найден.
        """
        query = select(Users).where(or_(
            Users.username == username,
            Users.email == email
        ))
        result = await self._session.execute(query)
        user = result.scalar_one_or_none()

        logger.debug(f"Поиск пользователя по username '{username}' или email '{email}': {user is not None}")
        return user