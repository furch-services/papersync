import logging
from dataclasses import dataclass

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger("papersync.paperless")


@dataclass
class PaperlessTag:
    id: int
    name: str


@dataclass
class PaperlessDocumentType:
    id: int
    name: str


@dataclass
class PaperlessCorrespondent:
    id: int
    name: str


class PaperlessService:
    def __init__(self, base_url: str, api_token: str) -> None:
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={
                "Authorization": f"Token {api_token}",
                "Accept": "application/json; version=2",
            },
            timeout=60,
        )

    def close(self) -> None:
        self._client.close()

    @retry(
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        reraise=True,
    )
    def upload_document(
        self,
        pdf_bytes: bytes,
        filename: str,
        title: str | None = None,
        created: str | None = None,
        correspondent: int | None = None,
        document_type: int | None = None,
        tags: list[int] | None = None,
    ) -> str:
        """Upload PDF to Paperless. Returns the async task UUID."""
        files = {"document": (filename, pdf_bytes, "application/pdf")}
        data: dict[str, object] = {}
        if title:
            data["title"] = title
        if created:
            data["created"] = created
        if correspondent:
            data["correspondent"] = correspondent
        if document_type:
            data["document_type"] = document_type
        # tags is a repeated field
        tag_data = [("tags", tag_id) for tag_id in (tags or [])]

        response = self._client.post(
            "/api/documents/post_document/",
            files=files,
            data=data,
        )
        if tag_data:
            # httpx doesn't support mixed data + repeated fields cleanly;
            # send tags as separate multipart fields
            response = self._client.post(
                "/api/documents/post_document/",
                content=_build_multipart(filename, pdf_bytes, data, tag_data),
                headers={"Content-Type": _multipart_content_type(filename, pdf_bytes, data, tag_data)},
            )
        response.raise_for_status()
        task_uuid: str = response.json()
        logger.info("Uploaded %s to Paperless, task UUID: %s", filename, task_uuid)
        return task_uuid

    def get_task_status(self, task_uuid: str) -> dict:
        response = self._client.get("/api/tasks/", params={"task_id": task_uuid})
        response.raise_for_status()
        results = response.json()
        if isinstance(results, list) and results:
            return results[0]
        return {}

    def list_tags(self) -> list[PaperlessTag]:
        response = self._client.get("/api/tags/")
        response.raise_for_status()
        return [PaperlessTag(id=t["id"], name=t["name"]) for t in response.json().get("results", [])]

    def list_document_types(self) -> list[PaperlessDocumentType]:
        response = self._client.get("/api/document_types/")
        response.raise_for_status()
        return [PaperlessDocumentType(id=t["id"], name=t["name"]) for t in response.json().get("results", [])]

    def list_correspondents(self) -> list[PaperlessCorrespondent]:
        response = self._client.get("/api/correspondents/")
        response.raise_for_status()
        return [PaperlessCorrespondent(id=t["id"], name=t["name"]) for t in response.json().get("results", [])]


def _build_multipart(
    filename: str, pdf_bytes: bytes, data: dict, tag_data: list[tuple[str, int]]
) -> bytes:
    """Build raw multipart body supporting repeated tag fields."""
    boundary = b"----PaperSyncBoundary"
    parts = []
    parts.append(
        b'--' + boundary + b'\r\nContent-Disposition: form-data; name="document"; '
        b'filename="' + filename.encode() + b'"\r\n'
        b'Content-Type: application/pdf\r\n\r\n' + pdf_bytes + b'\r\n'
    )
    for key, value in data.items():
        parts.append(
            b'--' + boundary + b'\r\nContent-Disposition: form-data; name="'
            + key.encode() + b'"\r\n\r\n' + str(value).encode() + b'\r\n'
        )
    for key, value in tag_data:
        parts.append(
            b'--' + boundary + b'\r\nContent-Disposition: form-data; name="'
            + key.encode() + b'"\r\n\r\n' + str(value).encode() + b'\r\n'
        )
    parts.append(b'--' + boundary + b'--\r\n')
    return b''.join(parts)


def _multipart_content_type(filename: str, pdf_bytes: bytes, data: dict, tag_data: list) -> str:
    return "multipart/form-data; boundary=----PaperSyncBoundary"
