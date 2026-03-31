from fastapi import APIRouter, Depends, Request, status, Form
from starlette.responses import HTMLResponse, RedirectResponse

from src.core.dependencies import get_user_service, get_test_service
from src.core.templates import templates
from src.core.utils.auth.access_rights import get_current_admin
from src.model.domain.user import User
from src.model.schemas.user import UserCreate
from src.presentation.forms.user_forms import create_teacher_form, edit_user_form
from src.services.test_service import TestService
from src.services.user_service import UserService

router = APIRouter(prefix='/users', tags=['Users Management'])


@router.get("", response_class=HTMLResponse)
async def list_users(request: Request, user_service: UserService = Depends(get_user_service),
                     current_user: User = Depends(get_current_admin)):
    users = await user_service.list()
    return templates.TemplateResponse("users/list.html",
                                      {"request": request, "user": current_user, "users_list": users})


@router.get("/create/teacher", response_class=HTMLResponse)
async def get_create_teacher_page(request: Request, current_user: User = Depends(get_current_admin)):
    return templates.TemplateResponse("users/create_teacher.html", {"request": request, "user": current_user})


@router.post("/create/teacher", response_class=HTMLResponse)
async def post_create_teacher(
        request: Request, form_data: UserCreate = Depends(create_teacher_form),
        user_service: UserService = Depends(get_user_service), current_user: User = Depends(get_current_admin)
):
    try:
        await user_service.register_user(form_data)
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse("users/create_teacher.html",
                                          {"request": request, "user": current_user, "error": str(e)})


@router.get("/{user_id}", response_class=HTMLResponse)
async def user_detail(
        user_id: int,
        request: Request,
        user_service: UserService = Depends(get_user_service),
        test_service: TestService = Depends(get_test_service),
        current_user: User = Depends(get_current_admin)
):
    # Используем новый метод, чтобы получить студента с тестами
    target_user = await user_service.get_user_with_relations(user_id)

    # Получаем все тесты для выпадающего списка
    available_tests = await test_service.list_tests()

    # Отфильтровываем тесты, которые УЖЕ назначены студенту
    assigned_test_ids = [t.id for t in target_user.assigned_tests]
    available_tests = [t for t in available_tests if t.id not in assigned_test_ids]

    return templates.TemplateResponse("users/detail.html", {
        "request": request,
        "user": current_user,
        "target_user": target_user,
        "available_tests": available_tests
    })


@router.post("/{user_id}/delete")
async def delete_user(user_id: int, user_service: UserService = Depends(get_user_service),
                      current_user: User = Depends(get_current_admin)):
    await user_service.delete_user(user_id)
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def get_edit_user_page(user_id: int, request: Request, user_service: UserService = Depends(get_user_service),
                             current_user: User = Depends(get_current_admin)):
    target_user = await user_service.get_user_by_id(user_id)
    return templates.TemplateResponse("users/create_teacher.html",
                                      {"request": request, "user": current_user, "target_user": target_user,
                                       "edit_mode": True})


@router.post("/{user_id}/edit", response_class=HTMLResponse)
async def post_edit_user(
        user_id: int, request: Request, form_data: dict = Depends(edit_user_form),
        user_service: UserService = Depends(get_user_service), current_user: User = Depends(get_current_admin)
):
    try:
        await user_service.update_user(user_id, form_data)
        return RedirectResponse(url=f"/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        target_user = await user_service.get_user_by_id(user_id)
        return templates.TemplateResponse("users/create_teacher.html",
                                          {"request": request, "user": current_user, "target_user": target_user,
                                           "edit_mode": True, "error": str(e)})


@router.post("/{user_id}/assign_test")
async def assign_test_to_user(
        user_id: int,
        test_id: int = Form(...),
        test_service: TestService = Depends(get_test_service),
        user_service: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_admin)
):
    """Точечное назначение теста конкретному студенту"""
    student = await user_service.get_user_by_id(user_id)
    await test_service.assign_students(test_id, [student])
    return RedirectResponse(url=f"/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{user_id}/unassign_test/{test_id}")
async def unassign_test_from_user(
        user_id: int,
        test_id: int,
        test_service: TestService = Depends(get_test_service),
        current_user: User = Depends(get_current_admin)
):
    """Снятие теста у конкретного студента"""
    await test_service.unassign_student(test_id, user_id)
    return RedirectResponse(url=f"/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER)
