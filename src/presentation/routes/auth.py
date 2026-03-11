import logging

from fastapi import APIRouter, Depends
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse

from src.core.dependencies import get_user_service
from src.core.templates import templates
from src.core.utils.auth.cookie_helper import TokenHelper
from src.core.utils.auth.tokens import decode_jwt
from src.model.domain.enums import UserRole
from src.model.schemas.user import UserCreate
from src.presentation.forms.user_forms import login_form, registration_form, UserLoginSchema
from src.services.user_service import UserService

logger = logging.getLogger("Auth app")

router = APIRouter(
    prefix='/auth',
    tags=['Authentication'],
)


@router.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("auth/login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def post_login(
        request: Request,
        form_data: UserLoginSchema = Depends(login_form),
        service: UserService = Depends(get_user_service)
):
    try:
        user, tokens = await service.login_user(username=form_data.username, password=form_data.password)
        logger.info(f"Пользователь {user.username} успешно авторизовался.")

        if user.role == UserRole.ADMIN:
            url = request.url_for("get_home_admin_page")
        elif user.role == UserRole.TEACHER:
            url = request.url_for("get_home_teacher_page")
        else:
            url = request.url_for("get_home_student_page")

        response = RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
        response = TokenHelper.set_tokens_cookies(response=response, tokens=tokens)
        return response
    except Exception as e:
        logger.error(f"Ошибка входа: {str(e)}")
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Неверное имя пользователя или пароль"},
            status_code=status.HTTP_400_BAD_REQUEST
        )


@router.get("/register", response_class=HTMLResponse)
async def get_registration_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("auth/registration.html", {"request": request, "error": None})


@router.post("/register", response_class=HTMLResponse)
async def post_register_user(
        request: Request,
        form_data: UserCreate = Depends(registration_form),
        service: UserService = Depends(get_user_service)
):
    try:
        await service.register_user(form_data)
        url = request.url_for("get_login_page").include_query_params(registered="true")
        return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        logger.error(f"Ошибка регистрации: {str(e)}")
        return templates.TemplateResponse(
            "auth/registration.html",
            {"request": request, "error": "Пользователь с таким логином уже существует"},
            status_code=status.HTTP_400_BAD_REQUEST
        )


@router.post("/logout", response_class=RedirectResponse)
async def logout(request: Request) -> RedirectResponse:
    response = RedirectResponse(url=request.url_for("get_login_page"), status_code=status.HTTP_302_FOUND)
    response = TokenHelper.delete_tokens_cookies(response)
    return response


@router.get("/refresh", response_class=RedirectResponse)
async def refresh_tokens(request: Request, next_url: str = "/", service: UserService = Depends(get_user_service)):
    """Эндпоинт для автоматического обновления access_token с помощью refresh_token"""
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        return RedirectResponse(url=request.url_for("get_login_page"), status_code=status.HTTP_303_SEE_OTHER)

    try:
        payload = decode_jwt(refresh_token)
        user_id = payload.get("id")

        user = await service.get_user_by_id(user_id)

        tokens = await service._generate_tokens(user)

        response = RedirectResponse(url=next_url, status_code=status.HTTP_303_SEE_OTHER)
        response = TokenHelper.set_tokens_cookies(response=response, tokens=tokens)
        return response

    except Exception as e:
        logger.warning(f"Ошибка при попытке автоматического рефреша токена: {str(e)}")
        response = RedirectResponse(url=request.url_for("get_login_page"), status_code=status.HTTP_303_SEE_OTHER)
        response = TokenHelper.delete_tokens_cookies(response)
        return response
