import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from src.core.log_config import setup_logging
from src.core.settings import settings
from src.core.templates import templates
from src.presentation.routes.academic import router as academic_router
from src.presentation.routes.auth import router as auth_router
from src.presentation.routes.home import router as home_router
from src.presentation.routes.tests import router as tests_router
from src.presentation.routes.users import router as users_router

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

app.include_router(auth_router)
app.include_router(home_router)
app.include_router(users_router)
app.include_router(academic_router)
app.include_router(tests_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Возвращает понятный JSON при ошибках валидации Pydantic-схем"""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Умный обработчик HTTP ошибок для SSR (Jinja2)."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    if exc.status_code == 401:
        next_url = request.url.path
        return RedirectResponse(
            url=f"/auth/refresh?next_url={next_url}",
            status_code=303
        )

    if exc.status_code == 403:
        logger.warning(f"Попытка несанкционированного доступа к {request.url.path}")
        url = request.url_for("get_login_page").include_query_params(forbidden="true")
        return RedirectResponse(url=url, status_code=303)

    if exc.status_code == 404:
        return templates.TemplateResponse("errors/404.html", {"request": request}, status_code=404)

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


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
        logger.error(f"Ошибка при запуске сервера: {str(e)}")
