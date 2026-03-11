from fastapi import APIRouter, Depends, Request
from starlette.responses import HTMLResponse

from src.core.templates import templates
from src.core.utils.auth.access_rights import get_current_user, get_current_teacher, get_current_admin
from src.model.domain.user import User

router = APIRouter(
    prefix='/home',
    tags=['Dashboards'],
)

@router.get("/student", response_class=HTMLResponse)
async def get_home_student_page(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> HTMLResponse:
    """Личный кабинет студента."""
    return templates.TemplateResponse(
        "home/dashboard_student.html",
        {"request": request, "user": current_user}
    )

@router.get("/teacher", response_class=HTMLResponse)
async def get_home_teacher_page(
    request: Request,
    current_user: User = Depends(get_current_teacher)
) -> HTMLResponse:
    """Панель управления преподавателя."""
    return templates.TemplateResponse(
        "home/dashboard_teacher.html",
        {"request": request, "user": current_user}
    )

@router.get("/admin", response_class=HTMLResponse)
async def get_home_admin_page(
    request: Request,
    current_user: User = Depends(get_current_admin)
) -> HTMLResponse:
    """Панель администрирования платформы."""
    return templates.TemplateResponse(
        "home/dashboard_admin.html",
        {"request": request, "user": current_user}
    )