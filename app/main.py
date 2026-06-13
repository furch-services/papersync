from contextlib import asynccontextmanager
from typing import AsyncGenerator

from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, Response

from app import __version__
from app.core.auth import SESSION_COOKIE, verify_session_token
from app.core.config import settings
from app.core.database import engine, get_db
from app.core.logging_config import setup_logging
from app.repositories.settings_repo import get_settings
from app.repositories import sync_state_repo
from app.scheduler import scheduler as sched
from app.api import auth as auth_router, dashboard, logs, settings as settings_router, stats, sync


_AUTH_EXEMPT = {"/login", "/health", "/sync/trigger"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _AUTH_EXEMPT or request.url.path.startswith("/static"):
            return await call_next(request)
        token = request.cookies.get(SESSION_COOKIE)
        if not token or not verify_session_token(token):
            return RedirectResponse("/login", status_code=303)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Logging
    logger = setup_logging(log_level=settings.LOG_LEVEL, log_file=settings.LOG_FILE)
    logger.info("PaperSync starting up")

    # Run DB migrations
    alembic_cfg = AlembicConfig("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    alembic_command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied")

    # Start scheduler with configured interval
    with get_db() as db:
        cfg = get_settings(db)
        interval = cfg.polling_interval_minutes if cfg else 5
    sched.start(interval_minutes=interval)

    yield

    sched.stop()
    engine.dispose()
    logger.info("PaperSync shut down")


app = FastAPI(
    title="PaperSync",
    description="Synchronizes Papierkram invoices to Paperless-ngx",
    version=__version__,
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuthMiddleware)

app.include_router(auth_router.router)
app.include_router(dashboard.router)
app.include_router(settings_router.router)
app.include_router(logs.router)
app.include_router(stats.router)
app.include_router(sync.router)


@app.get("/health")
def health() -> JSONResponse:
    db_status = "ok"
    last_sync_at: str | None = None
    last_sync_status = "never"

    try:
        with get_db() as db:
            state = sync_state_repo.get_or_create_state(db)
            if state.last_sync_at:
                last_sync_at = state.last_sync_at.isoformat()
                last_sync_status = "error" if state.last_error else "success"
    except Exception:
        db_status = "error"

    status = "ok" if db_status == "ok" else "degraded"
    return JSONResponse(
        {
            "status": status,
            "database": db_status,
            "last_sync_at": last_sync_at,
            "last_sync_status": last_sync_status,
            "version": __version__,
        },
        status_code=200 if status == "ok" else 503,
    )
