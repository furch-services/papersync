import os

os.environ.setdefault("SECRET_KEY", "20JYBYlqYwBOJcWMP7_7UC1ja3fPiJnXq10SEF09L6Q=")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.scheduler import scheduler  # noqa: E402


def test_get_status_when_not_running():
    status = scheduler.get_status()
    assert status["running"] is False
    assert status["next_run"] is None


def test_reschedule_when_not_running_is_noop():
    scheduler.reschedule(10)


def test_stop_when_not_running_is_noop():
    scheduler.stop()
