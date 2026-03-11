import logging
from fastapi import Depends, HTTPException, status
from starlette.requests import Request

from src.core.dependencies import get_user_service
from src.core.utils.auth.cookie_helper import TokenHelper
from src.core.utils.auth.tokens import decode_jwt
from src.model.domain.enums import UserRole
from src.model.domain.user import User
from src.services.user_service import UserService

logger = logging.getLogger("UserAccessRights")


async def get_current_user(
        request: Request,
        token: str = Depends(TokenHelper.get_valid_access_token),
        user_service: UserService = Depends(get_user_service),
) -> User:
    """Получает текущего пользователя из базы по токену. Для всех авторизованных."""
    try:
        payload = decode_jwt(token)
        user_id = payload.get("id")

        user = await user_service.get_user_by_id(user_id)
        return user

    except ValueError as e:
        logger.warning(f"Ошибка проверки токена: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сеанс истек")


async def get_current_teacher(user: User = Depends(get_current_user)) -> User:
    """Пускает только Преподавателей и Администраторов."""
    if user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        logger.warning(f"Отказ в доступе: {user.username} не является преподавателем.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права преподавателя")
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """Пускает строго Администраторов."""
    if user.role != UserRole.ADMIN:
        logger.warning(f"Отказ в доступе: {user.username} не является администратором.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права администратора")
    return user