from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from jose import jwt, ExpiredSignatureError, JWTError

from src.core.settings import settings


class TypeToken(str, Enum):
    """Типы токенов."""
    ACCESS = 'access_token'
    REFRESH = 'refresh_token'


def encode_jwt(data: dict, scope: TypeToken, time_expire: int) -> str:
    """
    Кодирует данные в JWT (JSON Web Token).

    :param data: Данные для кодирования (словарь).
    :param scope: Тип токена (TypeToken.ACCESS или TypeToken.REFRESH).
    :param time_expire: Время жизни токена в минутах.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=time_expire)

    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "scope": scope.value
    })

    return jwt.encode(to_encode, key=settings.token.secret_key, algorithm=settings.token.algorithm)


def decode_jwt(
        token: str,
        secret: str = settings.token.secret_key,
        algorithm: str = "HS256",
) -> dict[str, Any]:
    """
    Декодирует JWT и проверяет его валидность.

    :raises ValueError: Если токен истек или некорректен.
    """
    try:
        payload = jwt.decode(token, key=secret, algorithms=[algorithm])
        return payload

    except ExpiredSignatureError as e:
        raise ValueError("Время действия токена истекло") from e
    except JWTError as e:
        raise ValueError("Некорректный токен") from e


def create_access_token(data: dict, time_expire: int = settings.token.access_token_expires_minutes) -> str:
    """Создает access token."""
    return encode_jwt(data, TypeToken.ACCESS, time_expire)


def create_refresh_token(data: dict, time_expire: int = settings.token.refresh_token_expires_minutes) -> str:
    """Создает refresh token."""
    return encode_jwt(data, TypeToken.REFRESH, time_expire)