import os
import tempfile

os.environ.setdefault("SECRET_KEY", "20JYBYlqYwBOJcWMP7_7UC1ja3fPiJnXq10SEF09L6Q=")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.core.logging_config import setup_logging  # noqa: E402


def test_setup_logging_creates_log_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")
        logger = setup_logging(log_level="DEBUG", log_file=log_file)
        logger.info("test entry")
        assert os.path.exists(log_file)
        with open(log_file) as f:
            content = f.read()
        assert "test entry" in content


def test_setup_logging_returns_logger():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = setup_logging(log_level="INFO", log_file=os.path.join(tmpdir, "app.log"))
        assert logger.name == "papersync"


def test_setup_logging_idempotent():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "app.log")
        logger1 = setup_logging(log_level="INFO", log_file=log_file)
        logger2 = setup_logging(log_level="INFO", log_file=log_file)
        assert logger1 is logger2
