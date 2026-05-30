from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


def _fernet() -> Fernet:
    key = settings.SECRET_KEY
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Decryption failed — SECRET_KEY may have changed") from exc
