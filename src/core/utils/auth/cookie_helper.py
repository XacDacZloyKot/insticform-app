from fastapi import Request, HTTPException, status
from starlette.responses import Response

from src.core.settings import settings


class TokenHelper:
    """Утилита для работы с JWT-токенами в cookies."""

    @staticmethod
    def set_tokens_cookies(response: Response, tokens: dict) -> Response:
        """Устанавливает access и refresh токены в защищенные HttpOnly cookies."""
        response.set_cookie(
            key="access_token",
            value=tokens.get("access_token"),
            httponly=True,
            max_age=settings.token.access_token_expires_minutes * 60,
            samesite="lax"
        )
        response.set_cookie(
            key="refresh_token",
            value=tokens.get("refresh_token"),
            httponly=True,
            max_age=settings.token.refresh_token_expires_minutes * 60,
            samesite="lax"
        )
        return response

    @staticmethod
    def delete_tokens_cookies(response: Response) -> Response:
        """Удаляет токены при выходе из системы (logout)."""
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response

    @staticmethod
    def get_valid_access_token(request: Request) -> str:
        """Достает access токен из запроса для проверки авторизации."""
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен отсутствует. Пожалуйста, авторизуйтесь."
            )
        return token