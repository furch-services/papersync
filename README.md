<div align="center">
  <img src="app/static/img/logo.svg" alt="PaperSync" width="300">
  <p><em>Your invoices, filed automatically.</em></p>

  [![Quality Gate Status](https://sonarqube.furch-services.de/api/project_badges/measure?project=PaperSync&metric=alert_status&token=sqb_13d28642f6f40efc5e6c534261cc5da4b243dce7)](https://sonarqube.furch-services.de/dashboard?id=PaperSync)
  [![Coverage](https://sonarqube.furch-services.de/api/project_badges/measure?project=PaperSync&metric=coverage&token=sqb_13d28642f6f40efc5e6c534261cc5da4b243dce7)](https://sonarqube.furch-services.de/dashboard?id=PaperSync)
  [![Security Rating](https://sonarqube.furch-services.de/api/project_badges/measure?project=PaperSync&metric=software_quality_security_rating&token=sqb_13d28642f6f40efc5e6c534261cc5da4b243dce7)](https://sonarqube.furch-services.de/dashboard?id=PaperSync)
  [![Maintainability Rating](https://sonarqube.furch-services.de/api/project_badges/measure?project=PaperSync&metric=software_quality_maintainability_rating&token=sqb_13d28642f6f40efc5e6c534261cc5da4b243dce7)](https://sonarqube.furch-services.de/dashboard?id=PaperSync)
</div>

---

Automatically syncs sent invoices from [Papierkram](https://www.papierkram.de) to [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx). Runs as a single self-hosted container behind a reverse proxy — no separate workers, no message queues.

## What it does

- Polls the Papierkram API every N minutes for sent invoices (`state: unpaid | paid | overdue | open`)
- Downloads each invoice as PDF
- Uploads it to Paperless-ngx with configurable tags, document type, and correspondent
- Prevents duplicate uploads via a local SQLite dedup table
- Provides a password-protected web dashboard for status, manual sync, dry-run, and logs

## Architecture

```
Internet → Cloudflare Tunnel → Caddy → PaperSync Container
                                              ↕                    ↕
                                    Papierkram API      Paperless-ngx API
```

| Component | Role |
|---|---|
| **FastAPI + Jinja2** | Web UI and `/health` endpoint |
| **APScheduler** | Polling loop (runs inside the app container) |
| **SQLite + Alembic** | Settings, dedup table, sync logs |
| **Fernet** | Encrypted storage of API credentials |
| **itsdangerous** | CSRF protection and signed session cookies |

## Deployment

### 1. Create the shared Docker network

```bash
docker network create internal
```

### 2. Generate a secret key

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Create `.env`

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```env
SECRET_KEY=<generated-key>
APP_USERNAME=admin
APP_PASSWORD=<your-password>
```

### 4. Create `docker-compose.yml`

```yaml
services:
  papersync:
    image: git.furch-services.de/gitea_max.furch/papersync:latest
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - internal

networks:
  internal:
    external: true
```

### 5. Start

```bash
docker compose up -d
```

### 6. Configure

Open the web UI, log in, and enter your Papierkram and Paperless-ngx credentials under **Einstellungen**.

## Caddy configuration

```caddyfile
papersync.example.com {
    reverse_proxy papersync:8000
}
```

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | Fernet key — generate with `cryptography.fernet.Fernet.generate_key()` |
| `APP_USERNAME` | — | `admin` | Web UI login username |
| `APP_PASSWORD` | ✅ | — | Web UI login password |
| `DATABASE_URL` | — | `sqlite:////app/data/papersync.db` | SQLAlchemy database URL |
| `LOG_LEVEL` | — | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_FILE` | — | `/app/logs/app.log` | Log file path inside the container |
| `APP_ENV` | — | `production` | Set to `development` to disable the secure cookie flag |

## Settings (Web UI)

All sync settings are stored in the database and configurable via `/settings`:

| Setting | Description |
|---|---|
| Papierkram API URL | Your Papierkram subdomain URL, e.g. `https://yourcompany.papierkram.de` |
| Papierkram API Key | Bearer token from Papierkram → Einstellungen → API |
| Paperless Base URL | Your Paperless-ngx instance URL |
| Paperless API Token | Token from Paperless → your user profile |
| Polling Interval | How often to check for new invoices (minutes) |
| Default Tags | Paperless tag IDs to apply (JSON array, e.g. `[5, 12]`) |
| Default Document Type | Paperless document type ID |
| Default Correspondent | Paperless correspondent ID |

## CI/CD

The Gitea Actions pipeline runs on every push to `main`:

1. **SonarQube scan** — runs tests with coverage, sends report to SonarQube, enforces Quality Gate
2. **Docker build** — only runs if the Quality Gate passes; builds, tags (`latest` + commit SHA), and pushes to the Gitea Container Registry

Required Gitea secrets/variables:

| Key | Type | Value |
|---|---|---|
| `REGISTRY` | Variable | Gitea hostname, e.g. `git.example.com` |
| `REGISTRY_TOKEN` | Secret | Personal access token with `write:packages` |
| `SONAR_TOKEN` | Secret | SonarQube user token |
| `SONAR_HOST_URL` | Variable | SonarQube instance URL |
| `SONAR_TEST_SECRET_KEY` | Secret | Valid Fernet key for running tests in CI |

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export SECRET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export DATABASE_URL=sqlite:///./data/papersync.db
export APP_PASSWORD=dev
mkdir -p data logs

alembic upgrade head
uvicorn app.main:app --reload
```

## Tests

```bash
pytest tests/
# With coverage:
pytest tests/ --cov=app --cov-report=term-missing
```

## Backup

All persistent data lives in `./data/`:

```bash
# Backup
cp data/papersync.db data/papersync.db.bak

# Restore (container must be stopped)
docker compose stop
cp data/papersync.db.bak data/papersync.db
docker compose up -d
```

## Troubleshooting

**Container won't start / permission error on logs:** The bind-mounted `./logs` directory may be owned by root. The entrypoint script fixes this automatically — if it persists, check that the `papersync` user (UID 1000) can write to the volume.

**No invoices synced:** Check the web UI logs. Common cause: Papierkram API key is wrong, or the invoice state doesn't match (`unpaid`, `paid`, `overdue`).

**Auth errors after restart:** Session tokens are in-memory — users need to log in again after a container restart.

**`Too Many Requests` from Papierkram:** Increase the polling interval in Settings.

## License

[AGPL-3.0](LICENSE)
