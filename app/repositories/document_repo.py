from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.processed_document import ProcessedDocument


def is_processed(db: Session, papierkram_id: int) -> bool:
    return db.query(ProcessedDocument).filter_by(papierkram_document_id=papierkram_id).first() is not None


def mark_processed(
    db: Session,
    papierkram_id: int,
    task_uuid: str | None,
    invoice_no: str | None,
    document_date: str | None,
    total_gross: float | None,
) -> ProcessedDocument:
    doc = ProcessedDocument(
        papierkram_document_id=papierkram_id,
        paperless_task_uuid=task_uuid,
        invoice_no=invoice_no,
        document_date=document_date,
        total_gross=total_gross,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(doc)
    db.flush()
    return doc


def update_paperless_id(db: Session, papierkram_id: int, paperless_id: int) -> None:
    db.query(ProcessedDocument).filter_by(
        papierkram_document_id=papierkram_id
    ).update({"paperless_document_id": paperless_id})


def get_pending_tasks(db: Session) -> list[ProcessedDocument]:
    return (
        db.query(ProcessedDocument)
        .filter(
            ProcessedDocument.paperless_task_uuid.isnot(None),
            ProcessedDocument.paperless_document_id.is_(None),
        )
        .all()
    )


def count_total(db: Session) -> int:
    return db.query(ProcessedDocument).count()
