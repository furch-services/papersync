from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from app.core.auth import SESSION_COOKIE, check_credentials, create_session_token, revoke_session_token
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

FormField = Annotated[str, Form()]


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = "") -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html", {"error": error})


@router.post("/login")
def login(
    request: Request,
    username: FormField,
    password: FormField,
) -> Response:
    if not check_credentials(username, password):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Ungültige Zugangsdaten."}, status_code=401
        )
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(),
        httponly=True,
        samesite="lax",
        secure=settings.APP_ENV == "production",
    )
    return response


@router.post("/logout")
def logout(request: Request) -> Response:
    token = request.cookies.get(SESSION_COOKIE, "")
    revoke_session_token(token)
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response
