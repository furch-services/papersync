import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.database import get_db
from app.services.sync import SyncService

logger = logging.getLogger("papersync.scheduler")

_scheduler = BackgroundScheduler(timezone="UTC")
JOB_ID = "papersync_sync"


def _sync_job() -> None:
    try:
        with get_db() as db:
            result = SyncService(db).run_sync()
            logger.info(
                "Scheduled sync complete: uploaded=%d skipped=%d errors=%d",
                result.uploaded,
                result.skipped,
                result.errors,
            )
    except Exception as exc:
        logger.error("Scheduled sync job crashed unexpectedly: %s", exc, exc_info=True)


def start(interval_minutes: int = 5) -> None:
    _scheduler.add_job(
        _sync_job,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id=JOB_ID,
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info("Scheduler started (interval: %d min)", interval_minutes)


def stop() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def reschedule(interval_minutes: int) -> None:
    if _scheduler.running:
        _scheduler.reschedule_job(JOB_ID, trigger=IntervalTrigger(minutes=interval_minutes))
        logger.info("Scheduler rescheduled to %d min", interval_minutes)


def get_status() -> dict:
    if not _scheduler.running:
        return {"running": False, "next_run": None}
    job = _scheduler.get_job(JOB_ID)
    return {
        "running": True,
        "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
    }
