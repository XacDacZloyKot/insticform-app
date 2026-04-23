from fastapi import APIRouter, Depends, Request, status
from fastapi import Form
from starlette.responses import HTMLResponse, RedirectResponse

from src.core.utils.auth.access_rights import get_current_teacher
from src.core.dependencies import get_academic_service
from src.core.dependencies import get_test_service
from src.core.dependencies import get_user_service
from src.core.templates import templates
from src.core.utils.auth.access_rights import get_current_admin
from src.model.domain.enums import UserRole
from src.model.domain.user import User
from src.model.schemas.academic import GroupBase, DisciplineBase
from src.presentation.forms.academic_forms import create_group_form, create_discipline_form
from src.services.academic_service import AcademicService
from src.services.test_service import TestService
from src.services.user_service import UserService

router = APIRouter(prefix='/academic', tags=['Academic Management'])


# УПРАВЛЕНИЕ ГРУППАМИ

@router.get("/groups", response_class=HTMLResponse)
async def list_groups(request: Request, academic_service: AcademicService = Depends(get_academic_service),
                      current_user: User = Depends(get_current_admin)):
    """Вывод списка всех учебных групп"""
    groups = await academic_service.list_groups()
    return templates.TemplateResponse("academic/groups_list.html",
                                      {"request": request, "user": current_user, "groups": groups})


@router.get("/create/group", response_class=HTMLResponse)
async def get_create_group_page(request: Request, current_user: User = Depends(get_current_admin)):
    """Страница с формой создания группы"""
    return templates.TemplateResponse("academic/create_group.html", {"request": request, "user": current_user})


@router.post("/create/group", response_class=HTMLResponse)
async def post_create_group(
        request: Request, form_data: GroupBase = Depends(create_group_form),
        academic_service: AcademicService = Depends(get_academic_service),
        current_user: User = Depends(get_current_admin)
):
    """Обработка формы создания группы"""
    try:
        await academic_service.create_group(form_data)
        return RedirectResponse(url="/academic/groups", status_code=status.HTTP_303_SEE_OTHER)
    except ValueError as e:
        return templates.TemplateResponse("academic/create_group.html",
                                          {"request": request, "user": current_user, "error": str(e)})


@router.get("/groups/{group_id}", response_class=HTMLResponse)
async def group_detail(
        group_id: int, request: Request,
        academic_service: AcademicService = Depends(get_academic_service),
        test_service: TestService = Depends(get_test_service),
        user_service: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_teacher)  
):
    group = await academic_service.get_group_with_relations(group_id)
    all_students = await user_service.list(role=UserRole.STUDENT)

    all_tests = await test_service.list_tests()

    if current_user.role == UserRole.ADMIN:
        available_tests = all_tests
    else:
        teacher_discipline_ids = [d.id for d in getattr(current_user, 'taught_disciplines', [])]

        available_tests = [
            t for t in all_tests
            if t.discipline_id in teacher_discipline_ids or t.creator_id == current_user.id
        ]

    existing_student_ids = [s.id for s in group.students]
    available_students = [s for s in all_students if s.id not in existing_student_ids]

    return templates.TemplateResponse("academic/group_detail.html", {
        "request": request,
        "user": current_user,
        "group": group,
        "available_tests": available_tests,
        "available_students": available_students
    })


@router.post("/groups/{group_id}/add_student")
async def add_student_to_group(
        group_id: int, student_id: int = Form(...),
        academic_service: AcademicService = Depends(get_academic_service),
        user_service: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_admin)
):
    student = await user_service.get_user_by_id(student_id)
    await academic_service.add_student_to_group(group_id, student)
    return RedirectResponse(url=f"/academic/groups/{group_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/groups/{group_id}/remove_student/{student_id}")
async def remove_student_from_group(
        group_id: int, student_id: int,
        academic_service: AcademicService = Depends(get_academic_service),
        current_user: User = Depends(get_current_admin)
):
    await academic_service.remove_student_from_group(group_id, student_id)
    return RedirectResponse(url=f"/academic/groups/{group_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/groups/{group_id}/delete")
async def delete_group(group_id: int, academic_service: AcademicService = Depends(get_academic_service),
                       current_user: User = Depends(get_current_admin)):
    """Удаление группы"""
    await academic_service.delete_group(group_id)
    return RedirectResponse(url="/academic/groups", status_code=status.HTTP_303_SEE_OTHER)


# УПРАВЛЕНИЕ ДИСЦИПЛИНАМИ

@router.get("/disciplines", response_class=HTMLResponse)
async def list_disciplines(request: Request, academic_service: AcademicService = Depends(get_academic_service),
                           current_user: User = Depends(get_current_admin)):
    """Вывод списка всех дисциплин"""
    disciplines = await academic_service.list_disciplines()
    return templates.TemplateResponse("academic/disciplines_list.html",
                                      {"request": request, "user": current_user, "disciplines": disciplines})


@router.get("/create/discipline", response_class=HTMLResponse)
async def get_create_discipline_page(request: Request, current_user: User = Depends(get_current_admin)):
    """Страница с формой создания дисциплины"""
    return templates.TemplateResponse("academic/create_discipline.html", {"request": request, "user": current_user})


@router.post("/create/discipline", response_class=HTMLResponse)
async def post_create_discipline(
        request: Request, form_data: DisciplineBase = Depends(create_discipline_form),
        academic_service: AcademicService = Depends(get_academic_service),
        current_user: User = Depends(get_current_admin)
):
    """Обработка формы создания дисциплины"""
    try:
        await academic_service.create_discipline(form_data)
        return RedirectResponse(url="/academic/disciplines", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse("academic/create_discipline.html",
                                          {"request": request, "user": current_user, "error": str(e)})


@router.get("/disciplines/{discipline_id}", response_class=HTMLResponse)
async def discipline_detail(
        discipline_id: int, request: Request,
        academic_service: AcademicService = Depends(get_academic_service),
        user_service: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_admin)
):
    discipline = await academic_service.get_discipline_with_relations(discipline_id)
    all_teachers = await user_service.list(role=UserRole.TEACHER)

    existing_teacher_ids = [t.id for t in discipline.teachers]
    available_teachers = [t for t in all_teachers if t.id not in existing_teacher_ids]

    return templates.TemplateResponse("academic/discipline_detail.html", {
        "request": request, "user": current_user, "discipline": discipline,
        "available_teachers": available_teachers
    })


@router.post("/disciplines/{discipline_id}/add_teacher")
async def add_teacher_to_discipline(
        discipline_id: int, teacher_id: int = Form(...),
        academic_service: AcademicService = Depends(get_academic_service),
        user_service: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_admin)
):
    teacher = await user_service.get_user_by_id(teacher_id)
    await academic_service.add_teacher_to_discipline(discipline_id, teacher)
    return RedirectResponse(url=f"/academic/disciplines/{discipline_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/disciplines/{discipline_id}/remove_teacher/{teacher_id}")
async def remove_teacher_from_discipline(
        discipline_id: int, teacher_id: int,
        academic_service: AcademicService = Depends(get_academic_service),
        current_user: User = Depends(get_current_admin)
):
    await academic_service.remove_teacher_from_discipline(discipline_id, teacher_id)
    return RedirectResponse(url=f"/academic/disciplines/{discipline_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/disciplines/{discipline_id}/delete")
async def delete_discipline(discipline_id: int, academic_service: AcademicService = Depends(get_academic_service),
                            current_user: User = Depends(get_current_admin)):
    """Удаление дисциплины"""
    await academic_service.delete_discipline(discipline_id)
    return RedirectResponse(url="/academic/disciplines", status_code=status.HTTP_303_SEE_OTHER)


# --- ЭНДПОИНТЫ ДЛЯ РЕДАКТИРОВАНИЯ ГРУППЫ ---

@router.get("/groups/{group_id}/edit", response_class=HTMLResponse)
async def get_edit_group_page(group_id: int, request: Request,
                              academic_service: AcademicService = Depends(get_academic_service),
                              current_user: User = Depends(get_current_admin)):
    group = await academic_service.get_group_by_id(group_id)
    # Используем тот же шаблон create_group.html, но передаем флаг edit_mode=True и саму группу
    return templates.TemplateResponse("academic/create_group.html",
                                      {"request": request, "user": current_user, "group": group, "edit_mode": True})


@router.post("/groups/{group_id}/edit", response_class=HTMLResponse)
async def post_edit_group(
        group_id: int, request: Request, form_data: GroupBase = Depends(create_group_form),
        academic_service: AcademicService = Depends(get_academic_service),
        current_user: User = Depends(get_current_admin)
):
    try:
        await academic_service.update_group(group_id, form_data)
        return RedirectResponse(url=f"/academic/groups/{group_id}", status_code=status.HTTP_303_SEE_OTHER)
    except ValueError as e:
        group = await academic_service.get_group_by_id(group_id)
        return templates.TemplateResponse("academic/create_group.html",
                                          {"request": request, "user": current_user, "group": group, "edit_mode": True,
                                           "error": str(e)})


# --- ЭНДПОИНТЫ ДЛЯ РЕДАКТИРОВАНИЯ ДИСЦИПЛИНЫ ---

@router.get("/disciplines/{discipline_id}/edit", response_class=HTMLResponse)
async def get_edit_discipline_page(discipline_id: int, request: Request,
                                   academic_service: AcademicService = Depends(get_academic_service),
                                   current_user: User = Depends(get_current_admin)):
    discipline = await academic_service.get_discipline_by_id(discipline_id)
    return templates.TemplateResponse("academic/create_discipline.html",
                                      {"request": request, "user": current_user, "discipline": discipline,
                                       "edit_mode": True})


@router.post("/disciplines/{discipline_id}/edit", response_class=HTMLResponse)
async def post_edit_discipline(
        discipline_id: int, request: Request, form_data: DisciplineBase = Depends(create_discipline_form),
        academic_service: AcademicService = Depends(get_academic_service),
        current_user: User = Depends(get_current_admin)
):
    try:
        await academic_service.update_discipline(discipline_id, form_data)
        return RedirectResponse(url=f"/academic/disciplines/{discipline_id}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        discipline = await academic_service.get_discipline_by_id(discipline_id)
        return templates.TemplateResponse("academic/create_discipline.html",
                                          {"request": request, "user": current_user, "discipline": discipline,
                                           "edit_mode": True, "error": str(e)})


@router.post("/groups/{group_id}/assign_test")
async def assign_test_to_group_from_group_page(
        group_id: int,
        test_id: int = Form(...),
        academic_service: AcademicService = Depends(get_academic_service),
        test_service: TestService = Depends(get_test_service),
        current_user: User = Depends(get_current_teacher)
):
    # Получаем группу со студентами
    group = await academic_service.get_group_with_relations(group_id)

    # Выдаем тест всем студентам этой группы (наша плоская логика!)
    await test_service.assign_students(test_id, group.students)

    return RedirectResponse(url=f"/academic/groups/{group_id}", status_code=status.HTTP_303_SEE_OTHER)
