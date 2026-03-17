from fastapi import APIRouter, Depends, Request, status
from starlette.responses import HTMLResponse, RedirectResponse
from src.core.templates import templates
from src.core.utils.auth.access_rights import get_current_admin
from src.model.domain.user import User
from src.presentation.forms.user_forms import create_teacher_form, edit_user_form
from src.model.schemas.user import UserCreate
from src.services.user_service import UserService
from src.core.dependencies import get_user_service

router = APIRouter(prefix='/users', tags=['Users Management'])

@router.get("", response_class=HTMLResponse)
async def list_users(request: Request, user_service: UserService = Depends(get_user_service), current_user: User = Depends(get_current_admin)):
    users = await user_service.list()
    return templates.TemplateResponse("users/list.html", {"request": request, "user": current_user, "users_list": users})

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
        return templates.TemplateResponse("users/create_teacher.html", {"request": request, "user": current_user, "error": str(e)})

@router.get("/{user_id}", response_class=HTMLResponse)
async def user_detail(user_id: int, request: Request, user_service: UserService = Depends(get_user_service), current_user: User = Depends(get_current_admin)):
    target_user = await user_service.get_user_by_id(user_id)
    return templates.TemplateResponse("users/detail.html", {"request": request, "user": current_user, "target_user": target_user})

@router.post("/{user_id}/delete")
async def delete_user(user_id: int, user_service: UserService = Depends(get_user_service), current_user: User = Depends(get_current_admin)):
    await user_service.delete_user(user_id)
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def get_edit_user_page(user_id: int, request: Request, user_service: UserService = Depends(get_user_service), current_user: User = Depends(get_current_admin)):
    target_user = await user_service.get_user_by_id(user_id)
    return templates.TemplateResponse("users/create_teacher.html", {"request": request, "user": current_user, "target_user": target_user, "edit_mode": True})

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
        return templates.TemplateResponse("users/create_teacher.html", {"request": request, "user": current_user, "target_user": target_user, "edit_mode": True, "error": str(e)})