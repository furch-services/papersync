from unittest.mock import patch

from app.core.csrf import generate_csrf_token


def test_settings_post_saves(client, db):
    from app.core.crypto import encrypt
    from app.models.app_settings import AppSettings

    db.add(AppSettings(
        id=1,
        papierkram_api_url="https://old.papierkram.de",
        papierkram_api_key_encrypted=encrypt("old-key"),
        paperless_base_url="https://old-paperless.example.com",
        paperless_api_token_encrypted=encrypt("old-token"),
        polling_interval_minutes=5,
    ))
    db.commit()

    with patch("app.api.settings.scheduler"):
        response = client.post("/settings", data={
            "csrf_token": generate_csrf_token(),
            "papierkram_api_url": "https://new.papierkram.de",
            "paperless_base_url": "https://new-paperless.example.com",
            "polling_interval_minutes": "10",
            "papierkram_api_key": "",
            "paperless_api_token": "",
            "default_tags": "",
            "default_document_type": "",
            "default_correspondent": "",
        }, follow_redirects=False)

    assert response.status_code == 303


def test_settings_post_invalid_csrf(client, db):
    response = client.post("/settings", data={
        "csrf_token": "invalid-token",
        "papierkram_api_url": "https://x.papierkram.de",
        "paperless_base_url": "https://x-paperless.example.com",
        "polling_interval_minutes": "5",
    }, follow_redirects=False)

    assert response.status_code == 403


def test_sync_run_triggers_background_task(client):
    with patch("app.api.sync._run_sync") as mock_sync:
        response = client.post("/sync/run", data={
            "csrf_token": generate_csrf_token(),
        }, follow_redirects=False)

    assert response.status_code == 303
    assert "/dashboard" in response.headers["location"]


def test_sync_run_invalid_csrf(client):
    response = client.post("/sync/run", data={
        "csrf_token": "bad",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert "error=csrf" in response.headers["location"]


def test_sync_test_dry_run(client, db):
    from unittest.mock import patch
    from app.services.sync import SyncResult

    with patch("app.api.sync.SyncService") as MockSvc:
        MockSvc.return_value.run_sync.return_value = SyncResult(
            uploaded=3, skipped=1, errors=0, dry_run=True
        )
        response = client.post("/sync/test", data={
            "csrf_token": generate_csrf_token(),
        })

    assert response.status_code == 200
    assert "3" in response.text
