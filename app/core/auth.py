import hmac
import hashlib
from itsdangerous import URLSafeSerializer, BadSignature

from app.core.config import settings

SESSION_COOKIE = "ps_session"
_serializer = URLSafeSerializer(settings.SECRET_KEY, salt="auth-session")


def check_credentials(username: str, password: str) -> bool:
    username_ok = hmac.compare_digest(username, settings.APP_USERNAME)
    password_ok = hmac.compare_digest(
        hashlib.sha256(password.encode()).hexdigest(),
        hashlib.sha256(settings.APP_PASSWORD.encode()).hexdigest(),
    )
    return username_ok and password_ok


def create_session_token() -> str:
    return _serializer.dumps({"auth": True})


def verify_session_token(token: str) -> bool:
    try:
        data = _serializer.loads(token)
        return bool(data.get("auth"))
    except BadSignature:
        return False
