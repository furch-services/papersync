from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.csrf import generate_csrf_token, verify_csrf_token
from app.core.crypto import encrypt
from app.core.database import get_db_session
from app.repositories import settings_repo
from app.scheduler import scheduler

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db_session)):
    cfg = settings_repo.get_or_create_settings(db)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {"cfg": cfg, "csrf_token": generate_csrf_token(), "error": None},
    )


@router.post("/settings", response_class=HTMLResponse)
def settings_save(
    request: Request,
    db: Session = Depends(get_db_session),
    csrf_token: str = Form(...),
    papierkram_api_url: str = Form(...),
    papierkram_api_key: str = Form(default=""),
    paperless_base_url: str = Form(...),
    paperless_api_token: str = Form(default=""),
    polling_interval_minutes: int = Form(default=5),
    default_tags: str = Form(default=""),
    default_document_type: str = Form(default=""),
    default_correspondent: str = Form(default=""),
):
    if not verify_csrf_token(csrf_token):
        cfg = settings_repo.get_or_create_settings(db)
        return templates.TemplateResponse(
            request,
            "settings.html",
            {"cfg": cfg, "csrf_token": generate_csrf_token(),
             "error": "Invalid CSRF token — please reload and try again."},
            status_code=403,
        )

    cfg = settings_repo.get_or_create_settings(db)
    cfg.papierkram_api_url = papierkram_api_url.strip()
    cfg.paperless_base_url = paperless_base_url.strip()
    cfg.polling_interval_minutes = max(1, polling_interval_minutes)
    cfg.default_tags = default_tags.strip() or None
    cfg.default_document_type = int(default_document_type) if default_document_type.strip() else None
    cfg.default_correspondent = int(default_correspondent) if default_correspondent.strip() else None

    if papierkram_api_key.strip():
        cfg.papierkram_api_key_encrypted = encrypt(papierkram_api_key.strip())
    if paperless_api_token.strip():
        cfg.paperless_api_token_encrypted = encrypt(paperless_api_token.strip())

    settings_repo.save_settings(db, cfg)
    scheduler.reschedule(cfg.polling_interval_minutes)

    return RedirectResponse("/settings?saved=1", status_code=303)
