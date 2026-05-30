from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import settings


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt="csrf")


def generate_csrf_token() -> str:
    return _serializer().dumps("csrf-token")


def verify_csrf_token(token: str, max_age: int = 3600) -> bool:
    try:
        _serializer().loads(token, max_age=max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False
