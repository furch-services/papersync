import logging
from dataclasses import dataclass

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger("papersync.papierkram")

# States that represent sent/finalized invoices (not drafts)
SENT_STATES = {"open", "paid", "overdue"}


@dataclass
class Invoice:
    id: int
    name: str | None
    invoice_no: str | None
    document_date: str | None
    state: str
    total_gross: float | None


class PapierkramService:
    def __init__(self, api_url: str, api_key: str) -> None:
        base = api_url.rstrip("/")
        if not base.endswith("/api/v1"):
            base = f"{base}/api/v1"
        self._base_url = base + "/"  # trailing slash required for httpx path merging
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            timeout=30,
        )

    def close(self) -> None:
        self._client.close()

    @retry(
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        reraise=True,
    )
    def _get(self, path: str, **params: object) -> dict:
        # Strip leading slash so httpx resolves relative to base_url (which has trailing slash)
        rel_path = path.lstrip("/")
        response = self._client.get(rel_path, params={k: v for k, v in params.items() if v is not None})
        response.raise_for_status()
        return response.json()

    def list_sent_invoices(self) -> list[Invoice]:
        """Fetch all sent (non-draft) invoices across all pages."""
        invoices: list[Invoice] = []
        page = 1

        while True:
            data = self._get("/income/invoices", page=page, page_size=100)
            for entry in data.get("entries", []):
                state = entry.get("state", "")
                if state not in SENT_STATES:
                    continue
                invoices.append(
                    Invoice(
                        id=entry["id"],
                        name=entry.get("name"),
                        invoice_no=entry.get("invoice_no"),
                        document_date=entry.get("document_date"),
                        state=state,
                        total_gross=entry.get("total_gross"),
                    )
                )
            if not data.get("has_more", False):
                break
            page += 1

        logger.info("Fetched %d sent invoices from Papierkram", len(invoices))
        return invoices

    @retry(
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        reraise=True,
    )
    def download_pdf(self, invoice_id: int) -> bytes:
        response = self._client.get(f"income/invoices/{invoice_id}/pdf")
        response.raise_for_status()
        return response.content
