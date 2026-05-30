import os
from unittest.mock import MagicMock, patch

import httpx

os.environ.setdefault("SECRET_KEY", "20JYBYlqYwBOJcWMP7_7UC1ja3fPiJnXq10SEF09L6Q=")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.services.papierkram import PapierkramService  # noqa: E402

_INVOICE_LIST_RESPONSE = {
    "type": "list",
    "page": 1,
    "total_pages": 1,
    "has_more": False,
    "entries": [
        {"id": 1, "name": "Invoice A", "state": "open", "invoice_no": "RE-001",
         "document_date": "2024-01-15", "total_gross": 119.0},
        {"id": 2, "name": "Draft", "state": "draft", "invoice_no": None,
         "document_date": "2024-01-16", "total_gross": 50.0},
        {"id": 3, "name": "Invoice C", "state": "paid", "invoice_no": "RE-002",
         "document_date": "2024-01-17", "total_gross": 238.0},
    ],
}


def _mock_response(status_code: int = 200, json: dict | None = None, content: bytes | None = None):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    if json is not None:
        resp.json.return_value = json
    if content is not None:
        resp.content = content
    return resp


def test_list_sent_invoices_filters_drafts():
    mock_resp = _mock_response(json=_INVOICE_LIST_RESPONSE)

    with patch.object(httpx.Client, "get", return_value=mock_resp):
        svc = PapierkramService("https://test.papierkram.de", "test-token")
        invoices = svc.list_sent_invoices()
        svc.close()

    assert len(invoices) == 2
    assert all(inv.state != "draft" for inv in invoices)
    assert invoices[0].id == 1
    assert invoices[1].id == 3


def test_download_pdf_returns_bytes():
    pdf_content = b"%PDF-1.4 test"
    mock_resp = _mock_response(content=pdf_content)

    with patch.object(httpx.Client, "get", return_value=mock_resp):
        svc = PapierkramService("https://test.papierkram.de", "test-token")
        result = svc.download_pdf(42)
        svc.close()

    assert result == pdf_content
