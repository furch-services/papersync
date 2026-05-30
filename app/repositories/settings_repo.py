from sqlalchemy.orm import Session

from app.models.app_settings import AppSettings


def get_settings(db: Session) -> AppSettings | None:
    return db.get(AppSettings, 1)


def get_or_create_settings(db: Session) -> AppSettings:
    obj = db.get(AppSettings, 1)
    if obj is None:
        obj = AppSettings(id=1)
        db.add(obj)
        db.flush()
    return obj


def save_settings(db: Session, obj: AppSettings) -> AppSettings:
    db.add(obj)
    db.flush()
    return obj
