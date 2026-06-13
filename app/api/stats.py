import re
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_session
from app.models.sync_log import SyncLog
from app.repositories import document_repo

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db_session)]

_SYNC_FINISHED_RE = re.compile(r"uploaded=\d+ skipped=(\d+) errors=(\d+)")


class StatsResponse(BaseModel):
    labels: list[str]
    uploads_per_day: list[int]
    total_uploaded: int
    total_skipped: int
    total_errors: int
    permanently_failed: int


def build_stats(db: Session) -> StatsResponse:
    today = date.today()
    days = 14

    daily = document_repo.get_daily_upload_counts(db, days=days)
    labels: list[str] = []
    uploads_per_day: list[int] = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime("%d.%m"))
        uploads_per_day.append(daily.get(d.isoformat(), 0))

    total_uploaded = document_repo.count_total(db)
    permanently_failed = document_repo.count_permanently_failed(db, settings.MAX_RETRIES)

    total_skipped = 0
    total_errors = 0
    for entry in db.query(SyncLog).filter(SyncLog.message.like("Sync finished:%")).all():
        m = _SYNC_FINISHED_RE.search(entry.message)
        if m:
            total_skipped += int(m.group(1))
            total_errors += int(m.group(2))

    return StatsResponse(
        labels=labels,
        uploads_per_day=uploads_per_day,
        total_uploaded=total_uploaded,
        total_skipped=total_skipped,
        total_errors=total_errors,
        permanently_failed=permanently_failed,
    )


@router.get("/api/stats", response_model=StatsResponse)
def get_stats(db: DbSession) -> StatsResponse:
    return build_stats(db)
