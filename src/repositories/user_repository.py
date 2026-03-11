import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.utils.auth.password import hash_password
from src.model.domain.user import User
from src.model.schemas.user import UserCreate
from src.repositories.base_repository import BaseRepository
from src.repositories.decorators import with_exception_handling, with_read_operation_handling

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """
    Репозиторий для работы с пользователями.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=User)

    @with_exception_handling("Ошибка при создании пользователя")
    async def create(self, user_data: UserCreate) -> User:
        """
        Создает нового пользователя в базе данных.
        """
        existing_user = await self.get_by_username(username=user_data.username)

        if existing_user:
            logger.warning(f"Пользователь с username '{user_data.username}' уже существует")
            raise ValueError(f"Пользователь с именем '{user_data.username}' уже существует")

        new_user = User(
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            patronymic=user_data.patronymic,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
        )

        result = await super().create(new_user)
        logger.info(f"Создан пользователь {self.model_name}: {result.username}")
        return result

    @with_read_operation_handling("Ошибка при поиске пользователя по username")
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Возвращает пользователя по username.
        """
        result = await self.find_first(username=username)
        logger.debug(f"Поиск пользователя по username: {username}")
        return result