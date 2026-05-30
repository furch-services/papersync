import os
import tempfile
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_tmpdir = tempfile.mkdtemp()
_TEST_DB = f"sqlite:///{_tmpdir}/test.db"
_TEST_KEY = "20JYBYlqYwBOJcWMP7_7UC1ja3fPiJnXq10SEF09L6Q="

# Must be set before any app imports
os.environ["SECRET_KEY"] = _TEST_KEY
os.environ["DATABASE_URL"] = _TEST_DB
os.environ["LOG_FILE"] = f"{_tmpdir}/test.log"
os.environ.setdefault("APP_PASSWORD", "testpassword")

from app.core.auth import SESSION_COOKIE, create_session_token  # noqa: E402
from app.core.database import Base, get_db_session  # noqa: E402
from app.main import app  # noqa: E402

TEST_ENGINE = create_engine(f"sqlite:///{_tmpdir}/test.db", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@asynccontextmanager
async def _null_lifespan(_app: Any) -> AsyncGenerator[None, None]:
    yield


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestingSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def client(db):
    def override_db():
        yield db

    app.dependency_overrides[get_db_session] = override_db
    with patch.object(app.router, "lifespan_context", _null_lifespan):
        with TestClient(app, raise_server_exceptions=True) as c:
            c.cookies.set(SESSION_COOKIE, create_session_token())
            yield c
    app.dependency_overrides.clear()
