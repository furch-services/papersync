import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

os.environ.setdefault("SECRET_KEY", "20JYBYlqYwBOJcWMP7_7UC1ja3fPiJnXq10SEF09L6Q=")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.services.papierkram import Invoice  # noqa: E402
from app.services.sync import SyncService  # noqa: E402


def _make_settings(db):
    from app.core.crypto import encrypt
    from app.models.app_settings import AppSettings

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
    return cfg


def test_dry_run_does_not_upload(db):
    _make_settings(db)
    mock_invoices = [
        Invoice(id=1, name="Test", invoice_no="RE-001", document_date="2024-01-01",
                state="open", total_gross=100.0)
    ]
    with patch("app.services.sync.PapierkramService") as MockPK, \
         patch("app.services.sync.PaperlessService") as MockPL:
        MockPK.return_value.list_sent_invoices.return_value = mock_invoices
        MockPL.return_value.upload_document.return_value = "uuid-123"

        result = SyncService(db).run_sync(dry_run=True)

    assert result.dry_run is True
    assert result.uploaded == 1
    MockPL.return_value.upload_document.assert_not_called()


def test_skips_already_processed(db):
    from app.models.processed_document import ProcessedDocument

    _make_settings(db)
    db.add(ProcessedDocument(papierkram_document_id=99, uploaded_at=datetime.now(timezone.utc)))
    db.commit()

    with patch("app.services.sync.PapierkramService") as MockPK, \
         patch("app.services.sync.PaperlessService") as MockPL:
        MockPK.return_value.list_sent_invoices.return_value = [
            Invoice(id=99, name="Done", invoice_no="RE-099",
                    document_date="2024-01-01", state="open", total_gross=100.0)
        ]
        result = SyncService(db).run_sync(dry_run=False)

    assert result.skipped == 1
    assert result.uploaded == 0
    MockPL.return_value.upload_document.assert_not_called()


def test_full_sync_uploads_new_invoice(db):
    _make_settings(db)
    mock_invoices = [
        Invoice(id=5, name="New", invoice_no="RE-005", document_date="2024-03-01",
                state="open", total_gross=200.0)
    ]
    with patch("app.services.sync.PapierkramService") as MockPK, \
         patch("app.services.sync.PaperlessService") as MockPL:
        MockPK.return_value.list_sent_invoices.return_value = mock_invoices
        MockPK.return_value.download_pdf.return_value = b"%PDF-1.4"
        MockPL.return_value.upload_document.return_value = "task-uuid-999"
        MockPL.return_value.get_task_status.return_value = {}

        result = SyncService(db).run_sync(dry_run=False)

    assert result.uploaded == 1
    assert result.errors == 0
    MockPL.return_value.upload_document.assert_called_once()


def test_sync_aborts_when_settings_missing(db):
    result = SyncService(db).run_sync()
    assert result.errors == 1
    assert result.uploaded == 0


def test_sync_handles_pdf_download_error(db):
    _make_settings(db)
    with patch("app.services.sync.PapierkramService") as MockPK, \
         patch("app.services.sync.PaperlessService") as MockPL:
        MockPK.return_value.list_sent_invoices.return_value = [
            Invoice(id=7, name="Fail", invoice_no="RE-007",
                    document_date="2024-01-01", state="open", total_gross=50.0)
        ]
        MockPK.return_value.download_pdf.side_effect = Exception("Network error")
        MockPL.return_value.get_task_status.return_value = {}

        result = SyncService(db).run_sync(dry_run=False)

    assert result.errors == 1
    assert result.uploaded == 0


def test_sync_handles_fetch_invoices_error(db):
    _make_settings(db)
    with patch("app.services.sync.PapierkramService") as MockPK, \
         patch("app.services.sync.PaperlessService"):
        MockPK.return_value.list_sent_invoices.side_effect = Exception("Timeout")

        result = SyncService(db).run_sync()

    assert result.errors == 1


def test_sync_handles_upload_error(db):
    _make_settings(db)
    with patch("app.services.sync.PapierkramService") as MockPK, \
         patch("app.services.sync.PaperlessService") as MockPL:
        MockPK.return_value.list_sent_invoices.return_value = [
            Invoice(id=8, name="UpFail", invoice_no="RE-008",
                    document_date="2024-01-01", state="open", total_gross=80.0)
        ]
        MockPK.return_value.download_pdf.return_value = b"%PDF"
        MockPL.return_value.upload_document.side_effect = Exception("Upload failed")
        MockPL.return_value.get_task_status.return_value = {}

        result = SyncService(db).run_sync(dry_run=False)

    assert result.errors == 1
    assert result.uploaded == 0
