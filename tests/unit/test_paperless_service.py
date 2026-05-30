import os
from unittest.mock import MagicMock, patch

import httpx

os.environ.setdefault("SECRET_KEY", "20JYBYlqYwBOJcWMP7_7UC1ja3fPiJnXq10SEF09L6Q=")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.services.paperless import (  # noqa: E402
    PaperlessService,
    _build_multipart,
    _multipart_content_type,
)


def _mock_response(json_data=None, status_code=200):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.json.return_value = json_data
    return resp


def test_build_multipart_contains_file():
    result = _build_multipart("invoice.pdf", b"%PDF content", {}, [])
    assert b"invoice.pdf" in result
    assert b"%PDF content" in result
    assert b"----PaperSyncBoundary" in result


def test_build_multipart_with_data_fields():
    result = _build_multipart("f.pdf", b"data", {"title": "Test", "created": "2024-01-01"}, [])
    assert b"title" in result
    assert b"Test" in result


def test_build_multipart_with_tags():
    result = _build_multipart("f.pdf", b"data", {}, [("tags", 5), ("tags", 12)])
    assert result.count(b'name="tags"') == 2


def test_multipart_content_type():
    ct = _multipart_content_type()
    assert "multipart/form-data" in ct
    assert "PaperSyncBoundary" in ct


def test_upload_document_no_tags():
    mock_resp = _mock_response(json_data="uuid-abc")
    with patch.object(httpx.Client, "post", return_value=mock_resp):
        svc = PaperlessService("https://paperless.example.com", "tok")
        result = svc.upload_document(b"%PDF", "inv.pdf", title="Invoice 1")
        svc.close()
    assert result == "uuid-abc"


def test_upload_document_with_tags():
    mock_resp = _mock_response(json_data="uuid-xyz")
    with patch.object(httpx.Client, "post", return_value=mock_resp):
        svc = PaperlessService("https://paperless.example.com", "tok")
        result = svc.upload_document(b"%PDF", "inv.pdf", tags=[1, 2])
        svc.close()
    assert result == "uuid-xyz"


def test_get_task_status_found():
    mock_resp = _mock_response(json_data=[{"status": "SUCCESS", "related_document": 42}])
    with patch.object(httpx.Client, "get", return_value=mock_resp):
        svc = PaperlessService("https://paperless.example.com", "tok")
        status = svc.get_task_status("some-uuid")
        svc.close()
    assert status["related_document"] == 42


def test_get_task_status_empty():
    mock_resp = _mock_response(json_data=[])
    with patch.object(httpx.Client, "get", return_value=mock_resp):
        svc = PaperlessService("https://paperless.example.com", "tok")
        status = svc.get_task_status("some-uuid")
        svc.close()
    assert status == {}


def test_list_tags():
    mock_resp = _mock_response(json_data={"results": [{"id": 1, "name": "Rechnung"}, {"id": 2, "name": "2024"}]})
    with patch.object(httpx.Client, "get", return_value=mock_resp):
        svc = PaperlessService("https://paperless.example.com", "tok")
        tags = svc.list_tags()
        svc.close()
    assert len(tags) == 2
    assert tags[0].name == "Rechnung"


def test_list_document_types():
    mock_resp = _mock_response(json_data={"results": [{"id": 3, "name": "Invoice"}]})
    with patch.object(httpx.Client, "get", return_value=mock_resp):
        svc = PaperlessService("https://paperless.example.com", "tok")
        types = svc.list_document_types()
        svc.close()
    assert types[0].id == 3


def test_list_correspondents():
    mock_resp = _mock_response(json_data={"results": [{"id": 7, "name": "ACME GmbH"}]})
    with patch.object(httpx.Client, "get", return_value=mock_resp):
        svc = PaperlessService("https://paperless.example.com", "tok")
        correspondents = svc.list_correspondents()
        svc.close()
    assert correspondents[0].name == "ACME GmbH"
