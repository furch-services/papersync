import hmac
import hashlib
import secrets
from typing import Set

from itsdangerous import URLSafeTimedSerializer, BadSignature

from app.core.config import settings

SESSION_COOKIE = "ps_session"
SESSION_TTL = 8 * 60 * 60  # 8 hours

_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="auth-session")
_revoked_jtis: Set[str] = set()


def check_credentials(username: str, password: str) -> bool:
    username_ok = hmac.compare_digest(username, settings.APP_USERNAME)
    password_ok = hmac.compare_digest(
        hashlib.sha256(password.encode()).hexdigest(),
        hashlib.sha256(settings.APP_PASSWORD.encode()).hexdigest(),
    )
    return username_ok and password_ok


def create_session_token() -> str:
    jti = secrets.token_urlsafe(16)
    return _serializer.dumps({"auth": True, "jti": jti})


def verify_session_token(token: str) -> bool:
    try:
        data = _serializer.loads(token, max_age=SESSION_TTL)
        jti = data.get("jti")
        return bool(data.get("auth")) and jti not in _revoked_jtis
    except BadSignature:
        return False


def revoke_session_token(token: str) -> None:
    try:
        data = _serializer.loads(token, max_age=SESSION_TTL)
        jti = data.get("jti")
        if jti:
            _revoked_jtis.add(jti)
    except BadSignature:
        pass
