def test_dashboard_returns_200(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "PaperSync" in response.text


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["last_sync_status"] == "never"
    assert body["version"] == "1.0.0"


def test_settings_page_loads(client):
    response = client.get("/settings")
    assert response.status_code == 200
    assert "Papierkram" in response.text


def test_logs_page_loads(client):
    response = client.get("/logs")
    assert response.status_code == 200
