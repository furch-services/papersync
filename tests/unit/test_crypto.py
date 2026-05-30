import os
import pytest

os.environ.setdefault("SECRET_KEY", "20JYBYlqYwBOJcWMP7_7UC1ja3fPiJnXq10SEF09L6Q=")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.core.crypto import decrypt, encrypt  # noqa: E402


def test_roundtrip():
    plaintext = "super-secret-api-key-12345"
    assert decrypt(encrypt(plaintext)) == plaintext


def test_encrypted_differs_from_plaintext():
    value = "my-token"
    assert encrypt(value) != value


def test_decrypt_wrong_key_raises():
    original_key = os.environ["SECRET_KEY"]
    encrypted = encrypt("test-value")

    os.environ["SECRET_KEY"] = "d3JvbmdrZXl3cm9uZ2tleXdyb25na2V5d3Jvbmc="
    # Re-import to pick up new key — patch the module instead
    import app.core.crypto as crypto_mod
    from cryptography.fernet import Fernet
    crypto_mod._fernet = lambda: Fernet(os.environ["SECRET_KEY"].encode())  # type: ignore

    with pytest.raises(Exception):
        decrypt(encrypted)

    os.environ["SECRET_KEY"] = original_key
    crypto_mod._fernet = lambda: Fernet(os.environ["SECRET_KEY"].encode())  # type: ignore
