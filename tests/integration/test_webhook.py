from unittest.mock import patch


def test_webhook_trigger_not_configured(client):
    response = client.post("/sync/trigger")
    assert response.status_code == 503
    assert response.json()["detail"] == "Webhook not configured"


def test_webhook_trigger_missing_token(client):
    with patch.object(__import__("app.core.config", fromlist=["settings"]).settings, "WEBHOOK_SECRET", "secret123"):
        response = client.post("/sync/trigger")
    assert response.status_code == 401


def test_webhook_trigger_wrong_token(client):
    with patch.object(__import__("app.core.config", fromlist=["settings"]).settings, "WEBHOOK_SECRET", "secret123"):
        response = client.post("/sync/trigger", headers={"Authorization": "Bearer wrongtoken"})
    assert response.status_code == 401


def test_webhook_trigger_valid_token(client):
    with patch.object(__import__("app.core.config", fromlist=["settings"]).settings, "WEBHOOK_SECRET", "secret123"):
        with patch("app.api.sync._run_sync"):
            response = client.post("/sync/trigger", headers={"Authorization": "Bearer secret123"})
    assert response.status_code == 202
    assert response.json() == {"status": "started"}


def test_webhook_trigger_dry_run(client):
    with patch.object(__import__("app.core.config", fromlist=["settings"]).settings, "WEBHOOK_SECRET", "secret123"):
        with patch("app.api.sync._run_sync") as mock_sync:
            response = client.post(
                "/sync/trigger?dry_run=true",
                headers={"Authorization": "Bearer secret123"},
            )
    assert response.status_code == 202
    mock_sync.assert_called_once_with(dry_run=True)
