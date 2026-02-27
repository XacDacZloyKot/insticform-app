import logging
import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from src.core.settings import settings
from src.core.log_config import setup_logging

setup_logging()
logger = logging.getLogger("InsticForm")

app = FastAPI(
    title="InsticForm",
    description="Система опросов и тестирования для учебных заведений (с поддержкой видео)",
    version="0.1.0"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "src", "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
else:
    logger.warning(f"Директория со статикой не найдена: {STATIC_DIR}. Создайте папку src/static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origin,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.token.secret_key,
    session_cookie="session",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Возвращает понятный JSON при ошибках валидации Pydantic-схем"""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.get("/ping", tags=["System"])
async def root_ping():
    """Эндпоинт для проверки статуса сервера"""
    return {"status": "online", "app": "InsticForm"}


if __name__ == "__main__":
    try:
        logger.info(f"Запуск InsticForm на {settings.run.host}:{settings.run.port}")
        uvicorn.run(
            "src.main:app",
            host=settings.run.host,
            port=settings.run.port,
            log_level=settings.run.log_level,
            reload=settings.run.reload,
        )
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}", exc_info=True)
        sys.exit(1)
