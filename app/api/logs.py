from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.repositories import log_repo

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
PAGE_SIZE = 50


@router.get("/logs", response_class=HTMLResponse)
def logs_page(
    request: Request,
    db: Session = Depends(get_db_session),
    page: int = Query(default=1, ge=1),
    level: str = Query(default=""),
    search: str = Query(default=""),
):
    items, total = log_repo.get_logs(
        db,
        page=page,
        page_size=PAGE_SIZE,
        level=level or None,
        search=search or None,
    )
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    return templates.TemplateResponse(
        request,
        "logs.html",
        {
            "logs": items,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "level_filter": level,
            "search": search,
            "levels": LEVELS,
        },
    )
