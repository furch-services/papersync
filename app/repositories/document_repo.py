from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.processed_document import FAILED, PENDING, UPLOADED, ProcessedDocument


def is_processed(db: Session, papierkram_id: int) -> bool:
    doc = db.query(ProcessedDocument).filter_by(papierkram_document_id=papierkram_id).first()
    return doc is not None and doc.status in (PENDING, UPLOADED)


def is_permanently_failed(db: Session, papierkram_id: int, max_retries: int) -> bool:
    doc = db.query(ProcessedDocument).filter_by(papierkram_document_id=papierkram_id).first()
    return doc is not None and doc.status == FAILED and doc.retry_count >= max_retries


def mark_processed(
    db: Session,
    papierkram_id: int,
    task_uuid: str | None,
    invoice_no: str | None,
    document_date: str | None,
    total_gross: float | None,
) -> ProcessedDocument:
    doc = db.query(ProcessedDocument).filter_by(papierkram_document_id=papierkram_id).first()
    now = datetime.now(timezone.utc)
    if doc is None:
        doc = ProcessedDocument(
            papierkram_document_id=papierkram_id,
            paperless_task_uuid=task_uuid,
            invoice_no=invoice_no,
            document_date=document_date,
            total_gross=total_gross,
            uploaded_at=now,
            status=PENDING,
            retry_count=0,
        )
        db.add(doc)
    else:
        doc.paperless_task_uuid = task_uuid
        doc.invoice_no = invoice_no
        doc.document_date = document_date
        doc.total_gross = total_gross
        doc.uploaded_at = now
        doc.status = PENDING
        doc.retry_count = 0
    db.flush()
    return doc


def mark_failed(
    db: Session,
    papierkram_id: int,
    invoice_no: str | None,
    document_date: str | None,
    total_gross: float | None,
) -> ProcessedDocument:
    doc = db.query(ProcessedDocument).filter_by(papierkram_document_id=papierkram_id).first()
    now = datetime.now(timezone.utc)
    if doc is None:
        doc = ProcessedDocument(
            papierkram_document_id=papierkram_id,
            invoice_no=invoice_no,
            document_date=document_date,
            total_gross=total_gross,
            uploaded_at=now,
            status=FAILED,
            retry_count=1,
        )
        db.add(doc)
    else:
        doc.retry_count += 1
        doc.status = FAILED
    db.flush()
    return doc


def update_paperless_id(db: Session, papierkram_id: int, paperless_id: int) -> None:
    db.query(ProcessedDocument).filter_by(papierkram_document_id=papierkram_id).update(
        {"paperless_document_id": paperless_id, "status": UPLOADED}
    )


def get_pending_tasks(db: Session) -> list[ProcessedDocument]:
    return (
        db.query(ProcessedDocument)
        .filter(
            ProcessedDocument.paperless_task_uuid.isnot(None),
            ProcessedDocument.paperless_document_id.is_(None),
            ProcessedDocument.status == PENDING,
        )
        .all()
    )


def count_total(db: Session) -> int:
    return (
        db.query(ProcessedDocument)
        .filter(ProcessedDocument.status.in_([PENDING, UPLOADED]))
        .count()
    )


def count_permanently_failed(db: Session, max_retries: int) -> int:
    return (
        db.query(ProcessedDocument)
        .filter(
            ProcessedDocument.status == FAILED,
            ProcessedDocument.retry_count >= max_retries,
        )
        .count()
    )
