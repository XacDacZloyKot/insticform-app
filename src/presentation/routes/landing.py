from fastapi import APIRouter, Depends, Request

from src.core.templates import templates
from src.core.utils.auth.access_rights import get_current_user
from src.model.domain.user import User

router = APIRouter(
    tags=["Landing"]
)


@router.get("/", name="get_landing_page")
async def get_landing_page(
        request: Request,
        current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("landing/index.html", {"request": request, "user": current_user})
