import os
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

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


def test_start_adds_job_and_starts_scheduler():
    with patch.object(scheduler, "_scheduler") as mock_sched:
        scheduler.start(10)
        mock_sched.add_job.assert_called_once()
        mock_sched.start.assert_called_once()


def test_stop_when_running_shuts_down():
    with patch.object(scheduler, "_scheduler") as mock_sched:
        mock_sched.running = True
        scheduler.stop()
        mock_sched.shutdown.assert_called_once_with(wait=False)


def test_reschedule_when_running():
    with patch.object(scheduler, "_scheduler") as mock_sched:
        mock_sched.running = True
        scheduler.reschedule(15)
        mock_sched.reschedule_job.assert_called_once()


def test_get_status_when_running_with_job():
    mock_job = MagicMock()
    mock_job.next_run_time.isoformat.return_value = "2026-07-08T12:00:00+00:00"

    with patch.object(scheduler, "_scheduler") as mock_sched:
        mock_sched.running = True
        mock_sched.get_job.return_value = mock_job
        status = scheduler.get_status()

    assert status["running"] is True
    assert status["next_run"] == "2026-07-08T12:00:00+00:00"


def test_get_status_when_running_no_job():
    with patch.object(scheduler, "_scheduler") as mock_sched:
        mock_sched.running = True
        mock_sched.get_job.return_value = None
        status = scheduler.get_status()

    assert status["running"] is True
    assert status["next_run"] is None


def test_sync_job_success():
    from app.services.sync import SyncResult

    mock_result = SyncResult(uploaded=2, skipped=1, errors=0, dry_run=False)
    mock_db = MagicMock()

    @contextmanager
    def mock_get_db():
        yield mock_db

    with patch("app.scheduler.scheduler.get_db", mock_get_db), \
         patch("app.scheduler.scheduler.SyncService") as mock_svc:
        mock_svc.return_value.run_sync.return_value = mock_result
        scheduler._sync_job()

    mock_svc.return_value.run_sync.assert_called_once()


def test_sync_job_handles_exception():
    @contextmanager
    def failing_get_db():
        raise Exception("DB unavailable")
        yield  # noqa: unreachable — required for @contextmanager

    with patch("app.scheduler.scheduler.get_db", failing_get_db), \
         patch("app.scheduler.scheduler.logger") as mock_logger:
        scheduler._sync_job()  # must not raise

    mock_logger.error.assert_called_once()
