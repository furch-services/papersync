from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.sync_state import SyncState


def get_or_create_state(db: Session) -> SyncState:
    obj = db.get(SyncState, 1)
    if obj is None:
        obj = SyncState(id=1)
        db.add(obj)
        db.flush()
    return obj


def record_sync_start(db: Session) -> SyncState:
    state = get_or_create_state(db)
    state.last_sync_at = datetime.now(timezone.utc)
    db.flush()
    return state


def record_sync_success(db: Session, docs_added: int) -> SyncState:
    state = get_or_create_state(db)
    state.last_successful_sync_at = datetime.now(timezone.utc)
    state.last_error = None
    state.last_error_at = None
    state.documents_synced_total = (state.documents_synced_total or 0) + docs_added
    db.flush()
    return state


def record_sync_error(db: Session, error: str) -> SyncState:
    state = get_or_create_state(db)
    state.last_error = error
    state.last_error_at = datetime.now(timezone.utc)
    db.flush()
    return state
