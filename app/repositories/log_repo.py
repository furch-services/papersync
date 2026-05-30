from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.sync_log import SyncLog


def write_log(db: Session, level: str, source: str, message: str) -> SyncLog:
    entry = SyncLog(
        timestamp=datetime.now(timezone.utc),
        level=level.upper(),
        source=source,
        message=message,
    )
    db.add(entry)
    db.flush()
    return entry


def get_logs(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    level: str | None = None,
    search: str | None = None,
) -> tuple[list[SyncLog], int]:
    q = db.query(SyncLog)
    if level:
        q = q.filter(SyncLog.level == level.upper())
    if search:
        q = q.filter(SyncLog.message.ilike(f"%{search}%"))
    total = q.count()
    items = q.order_by(SyncLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total
