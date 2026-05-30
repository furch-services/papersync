import os
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("SECRET_KEY", "20JYBYlqYwBOJcWMP7_7UC1ja3fPiJnXq10SEF09L6Q=")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.services.papierkram import Invoice
from app.services.sync import SyncService


def test_dry_run_does_not_upload(db):
    from app.models.app_settings import AppSettings
    from app.core.crypto import encrypt

    cfg = AppSettings(
        id=1,
        papierkram_api_url="https://test.papierkram.de",
        papierkram_api_key_encrypted=encrypt("test-key"),
        paperless_base_url="https://test-paperless.example.com",
        paperless_api_token_encrypted=encrypt("test-token"),
        polling_interval_minutes=5,
    )
    db.add(cfg)
    db.commit()

    mock_invoices = [
        Invoice(id=1, name="Test", invoice_no="RE-001", document_date="2024-01-01", state="open", total_gross=100.0)
    ]

    with patch("app.services.sync.PapierkramService") as MockPK, \
         patch("app.services.sync.PaperlessService") as MockPL:
        MockPK.return_value.list_sent_invoices.return_value = mock_invoices
        MockPK.return_value.download_pdf.return_value = b"%PDF test"
        MockPL.return_value.upload_document.return_value = "uuid-123"

        svc = SyncService(db)
        result = svc.run_sync(dry_run=True)

    assert result.dry_run is True
    assert result.uploaded == 1
    MockPL.return_value.upload_document.assert_not_called()


def test_skips_already_processed(db):
    from app.models.app_settings import AppSettings
    from app.models.processed_document import ProcessedDocument
    from app.core.crypto import encrypt
    from datetime import datetime, timezone

    cfg = AppSettings(
        id=1,
        papierkram_api_url="https://test.papierkram.de",
        papierkram_api_key_encrypted=encrypt("test-key"),
        paperless_base_url="https://test-paperless.example.com",
        paperless_api_token_encrypted=encrypt("test-token"),
        polling_interval_minutes=5,
    )
    already_done = ProcessedDocument(
        papierkram_document_id=99,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add_all([cfg, already_done])
    db.commit()

    mock_invoices = [
        Invoice(id=99, name="Already done", invoice_no="RE-099",
                document_date="2024-01-01", state="open", total_gross=100.0)
    ]

    with patch("app.services.sync.PapierkramService") as MockPK, \
         patch("app.services.sync.PaperlessService") as MockPL:
        MockPK.return_value.list_sent_invoices.return_value = mock_invoices

        svc = SyncService(db)
        result = svc.run_sync(dry_run=False)

    assert result.skipped == 1
    assert result.uploaded == 0
    MockPL.return_value.upload_document.assert_not_called()
