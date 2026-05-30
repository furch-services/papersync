from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.csrf import verify_csrf_token
from app.core.database import get_db_session
from app.services.sync import SyncResult, SyncService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _run_sync(dry_run: bool = False) -> SyncResult:
    from app.core.database import get_db

    with get_db() as db:
        return SyncService(db).run_sync(dry_run=dry_run)


@router.post("/sync/run")
def trigger_sync(
    background_tasks: BackgroundTasks,
    csrf_token: str = Form(...),
):
    if not verify_csrf_token(csrf_token):
        return RedirectResponse("/dashboard?error=csrf", status_code=303)
    background_tasks.add_task(_run_sync, dry_run=False)
    return RedirectResponse("/dashboard?syncing=1", status_code=303)


@router.post("/sync/test")
async def trigger_test_run(
    request: Request,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db_session),
):
    if not verify_csrf_token(csrf_token):
        return RedirectResponse("/dashboard?error=csrf", status_code=303)

    result = SyncService(db).run_sync(dry_run=True)
    return templates.TemplateResponse(request, "dry_run_result.html", {"result": result})
