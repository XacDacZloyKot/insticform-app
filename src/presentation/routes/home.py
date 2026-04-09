from fastapi import APIRouter, Depends, Request
from starlette.responses import HTMLResponse

from src.core.dependencies import get_user_service
from src.core.templates import templates
from src.core.utils.auth.access_rights import get_current_teacher, get_current_admin
from src.core.utils.auth.access_rights import get_current_user
from src.model.domain.enums import AttemptStatus
from src.model.domain.user import User
from src.services.user_service import UserService

router = APIRouter(
    prefix='/home',
    tags=['Dashboards'],
)


@router.get("/home/student", response_class=HTMLResponse)
async def get_home_student_page(
        request: Request,
        user_service: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_user)
):
    student = await user_service.get_user_with_relations(current_user.id)

    available_tests = student.assigned_tests

    completed_tests_dict = {}
    for attempt in student.test_attempts:
        if attempt.status == AttemptStatus.COMPLETED:
            completed_tests_dict[attempt.test.id] = attempt.test

    completed_tests = list(completed_tests_dict.values())

    return templates.TemplateResponse(
        "home/dashboard_student.html",
        {
            "request": request,
            "user": student,
            "available_tests": available_tests,
            "completed_tests": completed_tests
        }
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
