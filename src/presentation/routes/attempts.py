from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse

from src.core.utils.auth.access_rights import get_current_teacher, get_current_admin
from src.services.user_service import UserService
from src.core.templates import templates
from src.core.utils.auth.access_rights import get_current_user
from src.model.domain.user import User
from src.core.dependencies import get_test_service, get_user_service
from src.core.dependencies import get_attempt_service
from src.services.test_service import TestService
from src.services.attempt_service import AttemptService

router = APIRouter(prefix='/attempts', tags=['Test Attempts'])

class ProctoringData(BaseModel):
    action_type: str
    details: str = None

@router.get("/intro/{test_id}", response_class=HTMLResponse)
async def get_intro_page(
        test_id: int, request: Request,
        test_service: TestService = Depends(get_test_service),
        current_user: User = Depends(get_current_user)
):
    """Ознакомительная страница перед стартом теста."""
    test = await test_service.get_test_by_id(test_id)
    return templates.TemplateResponse("attempts/intro.html", {"request": request, "user": current_user, "test": test})

@router.post("/start/{test_id}")
async def start_test_attempt(
        test_id: int,
        attempt_service: AttemptService = Depends(get_attempt_service),
        current_user: User = Depends(get_current_user)
):
    """Генерация попытки (старт таймера) и редирект в сам тест."""
    attempt = await attempt_service.start_attempt(test_id, current_user.id)
    return RedirectResponse(url=f"/attempts/{attempt.id}/take", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{attempt_id}/take", response_class=HTMLResponse)
async def take_test_page(
        attempt_id: int, request: Request,
        attempt_service: AttemptService = Depends(get_attempt_service),
        current_user: User = Depends(get_current_user)
):
    """Сам интерфейс тестирования."""
    attempt = await attempt_service.get_attempt_with_test(attempt_id)

    time_left_seconds = None
    if attempt.test.time_limit_minutes:
        start_time = attempt.start_time
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

        time_left_seconds = max(0, int(attempt.test.time_limit_minutes * 60 - elapsed))

    return templates.TemplateResponse(
        "attempts/take.html",
        {
            "request": request,
            "user": current_user,
            "attempt": attempt,
            "test": attempt.test,
            "time_left_seconds": time_left_seconds
        }
    )

@router.post("/{attempt_id}/proctoring")
async def log_proctoring(
        attempt_id: int, data: ProctoringData,
        attempt_service: AttemptService = Depends(get_attempt_service)
):
    """API-эндпоинт для фоновой записи событий прокторинга."""
    await attempt_service.log_proctoring_event(attempt_id, data.action_type, data.details)
    return JSONResponse(content={"status": "logged"})


@router.post("/{attempt_id}/submit")
async def submit_test_attempt(
        attempt_id: int,
        request: Request,
        attempt_service: AttemptService = Depends(get_attempt_service),
        test_service: TestService = Depends(get_test_service),
        current_user: User = Depends(get_current_user)
):
    """Принимает ответы студента и завершает тест."""
    form_data = await request.form()

    # Завершаем тест и считаем баллы
    attempt = await attempt_service.finish_attempt(attempt_id, form_data)

    await test_service.unassign_student(attempt.test_id, current_user.id)

    return RedirectResponse(url=f"/attempts/{attempt_id}/result", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{attempt_id}/result", response_class=HTMLResponse)
async def attempt_result_page(
        attempt_id: int, request: Request,
        attempt_service: AttemptService = Depends(get_attempt_service),
        current_user: User = Depends(get_current_user)
):
    """Страница об успешном завершении теста."""
    attempt = await attempt_service.get_attempt_with_test(attempt_id)
    return templates.TemplateResponse("attempts/result.html",
                                      {"request": request, "user": current_user, "attempt": attempt,
                                       "test": attempt.test})


@router.get("/{attempt_id}/details", response_class=HTMLResponse)
async def attempt_details_page(
        attempt_id: int, request: Request,
        attempt_service: AttemptService = Depends(get_attempt_service),
        current_user: User = Depends(get_current_user)
):
    """Детальная страница результатов тестирования (для преподавателей/админов)."""
    attempt = await attempt_service.get_full_attempt_details(attempt_id)

    proctoring_logs = sorted(attempt.proctoring_logs, key=lambda x: x.timestamp)

    return templates.TemplateResponse(
        "attempts/detail.html",
        {"request": request, "user": current_user, "attempt": attempt, "proctoring_logs": proctoring_logs}
    )

@router.post("/{attempt_id}/proctoring/clear")
async def clear_proctoring(
        attempt_id: int,
        attempt_service: AttemptService = Depends(get_attempt_service),
        current_user: User = Depends(get_current_user)
):
    """Очистка логов прокторинга преподавателем."""
    await attempt_service.clear_proctoring_logs(attempt_id)
    return RedirectResponse(url=f"/attempts/{attempt_id}/details", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{attempt_id}/delete")
async def delete_test_attempt(
        attempt_id: int,
        attempt_service: AttemptService = Depends(get_attempt_service),
        current_user: User = Depends(get_current_user)
):
    """Полное удаление попытки прохождения теста."""
    student_id = await attempt_service.delete_attempt(attempt_id)
    return RedirectResponse(url=f"/users/{student_id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("", response_class=HTMLResponse)
async def list_attempts_page(
        request: Request,
        attempt_service: AttemptService = Depends(get_attempt_service),
        user_service: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_teacher)
):
    if current_user.role.value not in ['admin', 'teacher']:
        return RedirectResponse(url="/", status_code=303)

    user_with_relations = await user_service.get_user_with_relations(current_user.id)

    attempts = await attempt_service.list_attempts_for_staff(user_with_relations)

    return templates.TemplateResponse(
        "attempts/list.html",
        {"request": request, "user": current_user, "attempts": attempts}
    )

@router.get("/proctoring/journal", response_class=HTMLResponse)
async def proctoring_journal_page(
        request: Request,
        attempt_service: AttemptService = Depends(get_attempt_service),
        user_service: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_admin)
):
    """Страница глобального журнала прокторинга."""
    if current_user.role.value not in ['admin', 'teacher']:
        return RedirectResponse(url="/", status_code=303)

    # Загружаем полные данные пользователя для фильтрации по дисциплинам
    user_with_relations = await user_service.get_user_with_relations(current_user.id)
    events = await attempt_service.list_all_proctoring_events(user_with_relations)

    return templates.TemplateResponse(
        "attempts/proctoring_journal.html",
        {"request": request, "user": current_user, "events": events}
    )


@router.get("/available", response_class=HTMLResponse)
async def available_tests_page(
        request: Request,
        user_service: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_user)
):
    """Страница со списком тестов, которые назначены студенту."""
    student = await user_service.get_user_with_relations(current_user.id)

    return templates.TemplateResponse("attempts/available_tests.html", {
        "request": request,
        "user": current_user,
        "available_tests": student.assigned_tests
    })


@router.get("/my-results", response_class=HTMLResponse)
async def my_results_page(
        request: Request,
        user_service: UserService = Depends(get_user_service),
        current_user: User = Depends(get_current_user)
):
    """Страница с историей всех прохождений студента."""
    student = await user_service.get_user_with_relations(current_user.id)

    attempts = sorted(student.test_attempts, key=lambda x: x.start_time, reverse=True)

    return templates.TemplateResponse("attempts/my_results.html", {
        "request": request,
        "user": current_user,
        "attempts": attempts
    })