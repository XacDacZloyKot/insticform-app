import logging
from typing import Optional, Dict, List, Tuple

from sqlalchemy.orm import selectinload

from src.core.utils.auth import tokens
from src.core.utils.auth.password import verify_password
from src.model.domain.enums import UserRole
from src.model.domain.user import User
from src.model.schemas.user import UserCreate
from src.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository: UserRepository = user_repository

    @staticmethod
    async def _check_credentials(user: User, password: str) -> None:
        """Проверка учетных данных пользователя."""
        if not user or not verify_password(password, user.hashed_password):
            logger.warning("Ошибка аутентификации для пользователя")
            raise ValueError("Неверные имя пользователя или пароль")

        logger.info(f"Учетные данные проверены для пользователя: {user.username}")

    @staticmethod
    async def _generate_tokens(user: User) -> Dict[str, str]:
        """Генерация токенов для пользователя."""
        access_token_data = {
            "id": user.id,
            "role": user.role.value,
            "username": user.username
        }
        refresh_token_data = {
            "id": user.id,
            "username": user.username
        }

        return {
            "access_token": tokens.create_access_token(access_token_data),
            "refresh_token": tokens.create_refresh_token(refresh_token_data)
        }

    async def authenticate_user(self, username: str, password: str) -> Tuple[User, Dict[str, str]]:
        """
        Аутентификация с возвратом пользователя и его токенов.
        """
        user = await self.user_repository.get_by_username(username=username)

        if not user:
            raise ValueError("Пользователь не найден")

        await self._check_credentials(user, password)
        logger.info(f"Пользователь '{user.username}' успешно аутентифицирован")

        generated_tokens = await self._generate_tokens(user)
        return user, generated_tokens

    async def login_user(self, username: str, password: str) -> Tuple[User, Dict[str, str]]:
        """Аутентификации пользователя по username и паролю."""
        return await self.authenticate_user(username, password)

    async def register_user(self, user_data: UserCreate) -> User:
        """Регистрация нового пользователя."""
        try:
            new_user = await self.user_repository.create(user_data)
            logger.info(f"Пользователь '{new_user.username}' успешно зарегистрирован")
            return new_user
        except ValueError as e:
            logger.warning(f"Попытка регистрации: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при регистрации пользователя {user_data.username}: {str(e)}")
            raise RuntimeError(f"Внутренняя ошибка регистрации: {str(e)}")

    async def get_user_by_id(self, user_id: int) -> User:
        """Получение информации о пользователе по ID."""
        try:
            return await self.user_repository.get_one(id=user_id)
        except Exception:
            logger.warning(f"Запрос несуществующего пользователя: ID {user_id}")
            raise ValueError(f"Пользователь с ID {user_id} не найден")

    async def list(
            self,
            order_by: Optional[str] = None,
            order_direction: Optional[str] = "asc",
            offset: Optional[int] = None,
            limit: Optional[int] = None
    ) -> List[User]:
        """Получение списка пользователей с подгрузкой групп."""
        try:
            # Подгружаем связанные учебные группы
            joins = [selectinload(User.groups)]

            return await self.user_repository.list_with_joins(
                order_by=order_by,
                order_direction=order_direction,
                offset=offset,
                limit=limit,
                joins=joins
            )
        except Exception as e:
            logger.error(f"Ошибка при получении списка пользователей: {str(e)}")
            raise RuntimeError("Ошибка получения списка")

    async def delete_user(self, user_id: int) -> None:
        """Удаление пользователя по ID."""
        try:
            await self.user_repository.delete(user_id)
            logger.info(f"Пользователь ID {user_id} успешно удален")
        except ValueError:
            raise