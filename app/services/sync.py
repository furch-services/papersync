import json
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.crypto import decrypt
from app.repositories import document_repo, log_repo, settings_repo, sync_state_repo
from app.services.papierkram import Invoice, PapierkramService
from app.services.paperless import PaperlessService

logger = logging.getLogger("papersync.sync")


@dataclass
class SyncResult:
    uploaded: int
    skipped: int
    errors: int
    dry_run: bool


class SyncService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _build_clients(self) -> tuple[PapierkramService, PaperlessService] | None:
        cfg = settings_repo.get_settings(self._db)
        if not cfg or not cfg.papierkram_api_url or not cfg.paperless_base_url:
            log_repo.write_log(self._db, "ERROR", "sync", "Settings not configured — aborting sync")
            return None

        try:
            pk_key = decrypt(cfg.papierkram_api_key_encrypted) if cfg.papierkram_api_key_encrypted else ""
            pl_token = decrypt(cfg.paperless_api_token_encrypted) if cfg.paperless_api_token_encrypted else ""
        except ValueError as exc:
            log_repo.write_log(self._db, "ERROR", "sync", f"Failed to decrypt credentials: {exc}")
            return None

        return PapierkramService(cfg.papierkram_api_url, pk_key), PaperlessService(cfg.paperless_base_url, pl_token)

    def _fetch_invoices(self, pk: PapierkramService) -> list[Invoice] | None:
        try:
            return pk.list_sent_invoices()
        except Exception as exc:
            msg = f"Failed to fetch invoices from Papierkram: {exc}"
            log_repo.write_log(self._db, "ERROR", "papierkram", msg)
            sync_state_repo.record_sync_error(self._db, msg)
            return None

    def _upload_invoice(
        self,
        invoice: Invoice,
        pk: PapierkramService,
        pl: PaperlessService,
        cfg: object,
    ) -> tuple[int, int]:
        """Returns (uploaded, errors) delta."""
        try:
            pdf_bytes = pk.download_pdf(invoice.id)
        except Exception as exc:
            log_repo.write_log(self._db, "ERROR", "papierkram",
                f"PDF download failed for invoice {invoice.id}: {exc}")
            document_repo.mark_failed(
                self._db,
                papierkram_id=invoice.id,
                invoice_no=invoice.invoice_no,
                document_date=invoice.document_date,
                total_gross=invoice.total_gross,
            )
            return 0, 1

        tags = json.loads(cfg.default_tags) if cfg and cfg.default_tags else []  # type: ignore[union-attr]
        filename = f"invoice_{invoice.invoice_no or invoice.id}.pdf"
        title = invoice.name or f"Rechnung {invoice.invoice_no or invoice.id}"

        try:
            task_uuid = pl.upload_document(
                pdf_bytes=pdf_bytes,
                filename=filename,
                title=title,
                created=invoice.document_date,
                correspondent=cfg.default_correspondent if cfg else None,  # type: ignore[union-attr]
                document_type=cfg.default_document_type if cfg else None,  # type: ignore[union-attr]
                tags=tags,
            )
        except Exception as exc:
            log_repo.write_log(self._db, "ERROR", "paperless",
                f"Paperless upload failed for invoice {invoice.id}: {exc}")
            document_repo.mark_failed(
                self._db,
                papierkram_id=invoice.id,
                invoice_no=invoice.invoice_no,
                document_date=invoice.document_date,
                total_gross=invoice.total_gross,
            )
            return 0, 1

        document_repo.mark_processed(
            self._db,
            papierkram_id=invoice.id,
            task_uuid=task_uuid,
            invoice_no=invoice.invoice_no,
            document_date=invoice.document_date,
            total_gross=invoice.total_gross,
        )
        log_repo.write_log(self._db, "INFO", "sync",
            f"Uploaded invoice {invoice.invoice_no or invoice.id} (task: {task_uuid})")
        return 1, 0

    def _finalize(self, uploaded: int, errors: int) -> None:
        if errors == 0:
            sync_state_repo.record_sync_success(self._db, uploaded)
        else:
            sync_state_repo.record_sync_error(self._db, f"Sync completed with {errors} error(s)")

    def run_sync(self, dry_run: bool = False) -> SyncResult:
        sync_state_repo.record_sync_start(self._db)
        log_repo.write_log(self._db, "INFO", "sync", f"Sync started (dry_run={dry_run})")

        clients = self._build_clients()
        if clients is None:
            return SyncResult(uploaded=0, skipped=0, errors=1, dry_run=dry_run)

        pk, pl = clients
        invoices = self._fetch_invoices(pk)
        if invoices is None:
            pk.close()
            pl.close()
            return SyncResult(uploaded=0, skipped=0, errors=1, dry_run=dry_run)

        cfg = settings_repo.get_settings(self._db)
        max_retries = settings.MAX_RETRIES
        uploaded = skipped = errors = 0

        for invoice in invoices:
            if document_repo.is_processed(self._db, invoice.id):
                skipped += 1
                continue
            if document_repo.is_permanently_failed(self._db, invoice.id, max_retries):
                log_repo.write_log(self._db, "WARNING", "sync",
                    f"Invoice {invoice.invoice_no or invoice.id} permanently failed after "
                    f"{max_retries} attempts, skipping")
                skipped += 1
                continue
            if dry_run:
                log_repo.write_log(self._db, "INFO", "sync",
                    f"[DRY RUN] Would upload invoice {invoice.invoice_no or invoice.id}")
                uploaded += 1
                continue
            up, err = self._upload_invoice(invoice, pk, pl, cfg)
            uploaded += up
            errors += err

        if not dry_run:
            self._resolve_pending_tasks(pl)

        pk.close()
        pl.close()
        self._finalize(uploaded, errors)
        log_repo.write_log(self._db, "INFO", "sync",
            f"Sync finished: uploaded={uploaded} skipped={skipped} errors={errors}")
        return SyncResult(uploaded=uploaded, skipped=skipped, errors=errors, dry_run=dry_run)

    def _resolve_pending_tasks(self, pl: PaperlessService) -> None:
        pending = document_repo.get_pending_tasks(self._db)
        for doc in pending:
            try:
                status = pl.get_task_status(doc.paperless_task_uuid)
                result_id = status.get("related_document")
                if result_id:
                    document_repo.update_paperless_id(self._db, doc.papierkram_document_id, result_id)
            except Exception as exc:
                logger.warning("Could not resolve task %s: %s", doc.paperless_task_uuid, exc)
