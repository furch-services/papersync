from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.csrf import generate_csrf_token
from app.core.database import get_db_session
from app.repositories import document_repo, log_repo, sync_state_repo
from app.scheduler import scheduler

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

DbSession = Annotated[Session, Depends(get_db_session)]


@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: DbSession) -> HTMLResponse:
    state = sync_state_repo.get_or_create_state(db)
    sched_status = scheduler.get_status()
    recent_logs, _ = log_repo.get_logs(db, page=1, page_size=10)
    total_docs = document_repo.count_total(db)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "state": state,
            "scheduler": sched_status,
            "recent_logs": recent_logs,
            "total_docs": total_docs,
            "csrf_token": generate_csrf_token(),
        },
    )
