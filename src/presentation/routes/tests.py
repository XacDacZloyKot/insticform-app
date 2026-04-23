from typing import List
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, status
from fastapi import Form
from fastapi import Request
from pydantic import ValidationError
from starlette.responses import HTMLResponse
from starlette.responses import JSONResponse
from starlette.responses import RedirectResponse

from src.services.user_service import UserService
from src.core.dependencies import get_academic_service, get_user_service
from src.core.dependencies import get_test_service
from src.core.templates import templates
from src.core.utils.auth.access_rights import get_current_user
from src.model.domain.user import User
from src.model.schemas.test import QuestionCreate
from src.presentation.forms.test_forms import create_test_form
from src.services.academic_service import AcademicService
from src.services.test_service import TestService

router = APIRouter(prefix='/tests', tags=['Tests Management'])


@router.get("", response_class=HTMLResponse)
async def list_tests_page(
        request: Request,
        discipline_id: Optional[int] = None,
        test_service: TestService = Depends(get_test_service),
        academic_service: AcademicService = Depends(get_academic_service),
        user_service: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_user)
):
    if current_user.role.value not in ['admin', 'teacher']:
        return RedirectResponse(url="/", status_code=303)

    user_with_relations = await user_service.get_user_with_relations(current_user.id)

    # Получаем отфильтрованные тесты
    tests = await test_service.list_tests_for_staff(user_with_relations, discipline_id)

    if current_user.role.value == 'admin':
        disciplines = await academic_service.list_disciplines()
    else:
        disciplines = user_with_relations.taught_disciplines

    return templates.TemplateResponse(
        "tests/list.html",
        {
            "request": request,
            "user": current_user,
            "tests": tests,
            "disciplines": disciplines,
            "selected_discipline_id": discipline_id
        }
    )


@router.get("/{test_id}/questions/create", response_class=HTMLResponse)
async def get_create_question_page(test_id: int, request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "tests/create_question.html",
        {"request": request, "user": current_user, "test_id": test_id}
    )


@router.post("/{test_id}/questions/create")
async def api_create_question(
        test_id: int,
        question_data: str = Form(...),
        file: Optional[UploadFile] = File(None),  # Опциональный файл
        test_service: TestService = Depends(get_test_service),
        current_user: User = Depends(get_current_user)
):
    try:
        parsed_data = QuestionCreate.model_validate_json(question_data)

        await test_service.create_question_with_options(test_id, parsed_data, file)

        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "Вопрос успешно создан!"})
    except ValidationError as ve:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            content={"error": "Ошибка валидации данных", "details": ve.errors()})
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(e)})


@router.post("/{test_id}/media", summary="Загрузить медиафайл для теста")
async def upload_test_media(
        test_id: int,
        files: List[UploadFile] = File(...),  # Принимаем сразу несколько файлов
        test_service: TestService = Depends(get_test_service),
        current_user: User = Depends(get_current_user)
):
    try:
        uploaded_media = []
        for file in files:
            media = await test_service.attach_media_to_test(test_id, file)
            uploaded_media.append({
                "id": media.id,
                "original_filename": media.original_filename,
                "url": f"/static/media{media.file_path}"
            })

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": "Файлы загружены", "files": uploaded_media}
        )
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(e)})


@router.get("/create", response_class=HTMLResponse)
async def get_create_test_page(
        request: Request,
        academic_service: AcademicService = Depends(get_academic_service),
        user_service: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_user)
):
    """Страница создания оболочки теста."""
    user_with_relations = await user_service.get_user_with_relations(current_user.id)

    if current_user.role.value == 'admin':
        disciplines = await academic_service.list_disciplines()
    else:
        disciplines = user_with_relations.taught_disciplines

    return templates.TemplateResponse("tests/create_test.html", {
        "request": request,
        "user": current_user,
        "disciplines": disciplines
    })


@router.post("/create", response_class=HTMLResponse)
async def post_create_test(
        request: Request,
        form_data: dict = Depends(create_test_form),
        test_service: TestService = Depends(get_test_service),
        current_user: User = Depends(get_current_user)
):
    """Обработка формы и редирект в конструктор вопросов."""
    form_data["creator_id"] = current_user.id

    # Создаем тест в БД
    test = await test_service.create_test(form_data)

    # Перенаправляем препода в конструктор вопросов
    return RedirectResponse(url=f"/tests/{test.id}/questions/create", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{test_id}", response_class=HTMLResponse)
async def test_detail_page(
        test_id: int,
        request: Request,
        test_service: TestService = Depends(get_test_service),
        current_user: User = Depends(get_current_user)
):
    test = await test_service.get_test_by_id(test_id)
    return templates.TemplateResponse(
        "tests/detail.html",
        {"request": request, "user": current_user, "test": test}
    )


@router.post("/{test_id}/delete")
async def delete_test(
        test_id: int,
        test_service: TestService = Depends(get_test_service),
        current_user: User = Depends(get_current_user)
):
    """Удаление теста (только для создателя или администратора)"""
    test = await test_service.get_test_by_id(test_id)

    if current_user.role.value != 'admin' and test.creator_id != current_user.id:
        return RedirectResponse(url="/tests", status_code=status.HTTP_303_SEE_OTHER)

    await test_service.delete_test(test_id)
    return RedirectResponse(url="/tests", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{test_id}/questions/{question_id}/delete")
async def delete_question(test_id: int, question_id: int, test_service: TestService = Depends(get_test_service),
                          current_user: User = Depends(get_current_user)):
    await test_service.delete_question(question_id)
    return RedirectResponse(url=f"/tests/{test_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{test_id}/media/{media_id}/delete")
async def delete_test_media(test_id: int, media_id: int, test_service: TestService = Depends(get_test_service),
                            current_user: User = Depends(get_current_user)):
    await test_service.delete_test_media(media_id)
    return RedirectResponse(url=f"/tests/{test_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{test_id}/questions/{question_id}/media/delete")
async def delete_question_media(test_id: int, question_id: int, test_service: TestService = Depends(get_test_service),
                                current_user: User = Depends(get_current_user)):
    await test_service.delete_question_media(question_id)
    return RedirectResponse(url=f"/tests/{test_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{test_id}/unassign/{student_id}")
async def unassign_test_from_student(
        test_id: int,
        student_id: int,
        test_service: TestService = Depends(get_test_service),
        current_user: User = Depends(get_current_user)
):
    await test_service.unassign_student(test_id, student_id)
    return RedirectResponse(url=f"/tests/{test_id}", status_code=status.HTTP_303_SEE_OTHER)
