import hmac
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.csrf import verify_csrf_token
from app.core.database import get_db_session
from app.services.sync import SyncResult, SyncService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

DbSession = Annotated[Session, Depends(get_db_session)]


def _run_sync(dry_run: bool = False) -> SyncResult:
    from app.core.database import get_db

    with get_db() as db:
        return SyncService(db).run_sync(dry_run=dry_run)


@router.post("/sync/run")
def trigger_sync(
    request: Request,
    background_tasks: BackgroundTasks,
    csrf_token: Annotated[str, Form()],
) -> Response:
    if not verify_csrf_token(csrf_token):
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                '<div class="alert alert-danger"><i class="bi bi-exclamation-triangle me-1"></i>'
                "Ungültiger CSRF-Token — bitte Seite neu laden.</div>",
                status_code=200,
            )
        return RedirectResponse("/dashboard?error=csrf", status_code=303)
    background_tasks.add_task(_run_sync, dry_run=False)
    if request.headers.get("HX-Request"):
        return HTMLResponse(
            '<div class="alert alert-info alert-dismissible fade show" role="alert">'
            '<i class="bi bi-arrow-repeat me-1"></i> Synchronisation gestartet…'
            '<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
        )
    return RedirectResponse("/dashboard?syncing=1", status_code=303)


@router.post("/sync/trigger", status_code=202)
def webhook_trigger(
    background_tasks: BackgroundTasks,
    dry_run: bool = False,
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    if not settings.WEBHOOK_SECRET:
        return JSONResponse({"detail": "Webhook not configured"}, status_code=503)
    if not authorization or not hmac.compare_digest(authorization, f"Bearer {settings.WEBHOOK_SECRET}"):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    background_tasks.add_task(_run_sync, dry_run=dry_run)
    return JSONResponse({"status": "started"}, status_code=202)


@router.post("/sync/test")
async def trigger_test_run(
    request: Request,
    csrf_token: Annotated[str, Form()],
    db: DbSession,
) -> Response:
    if not verify_csrf_token(csrf_token):
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                '<div class="alert alert-danger"><i class="bi bi-exclamation-triangle me-1"></i>'
                "Ungültiger CSRF-Token — bitte Seite neu laden.</div>",
                status_code=200,
            )
        return RedirectResponse("/dashboard?error=csrf", status_code=303)

    result = SyncService(db).run_sync(dry_run=True)
    template = "_dry_run_result.html" if request.headers.get("HX-Request") else "dry_run_result.html"
    return templates.TemplateResponse(request, template, {"result": result})
