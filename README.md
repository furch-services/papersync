# PaperSync

Synchronizes sent invoices from [Papierkram](https://www.papierkram.de) to [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx) automatically.

## What it does

- Polls the Papierkram API every N minutes for sent invoices (`state: open | paid`)
- Downloads the invoice PDF
- Uploads it to Paperless-ngx with configurable tags, document type, and correspondent
- Prevents duplicate uploads via a local SQLite database
- Provides a web dashboard for status, manual sync, and logs

## Architecture

```
Internet → Cloudflare Tunnel → Caddy → PaperSync Container
                                              ↕                    ↕
                                    Papierkram API      Paperless-ngx API
```

- **FastAPI** — web UI and REST health check
- **APScheduler** — polling loop (runs inside the app container)
- **SQLite** — settings, dedup table, sync logs
- **Fernet** — encrypted storage of API credentials

## Deployment (Docker Compose)

**1. Create the network** (shared with Caddy):
```bash
docker network create internal
```

**2. Generate a secret key:**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**3. Create `.env`** from `.env.example`:
```bash
cp .env.example .env
# Edit .env and set SECRET_KEY
```

**4. Start:**
```bash
docker compose up -d
```

**5. Configure** — open the web UI and enter Papierkram + Paperless credentials.

## docker-compose.yml example

```yaml
services:
  papersync:
    image: registry.example.com/furchservices/papersync:latest
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

## Caddy configuration

```caddyfile
papersync.example.com {
    reverse_proxy papersync:8000
}
```

## Gitea CI/CD setup

1. Push the repository to Gitea
2. In repository **Settings → Variables**, set:
   - `REGISTRY` — your Gitea hostname, e.g. `gitea.example.com`
3. In **Settings → Secrets**, set:
   - `REGISTRY_TOKEN` — a Gitea personal access token with `write:packages` scope
4. Push to `main` — the workflow builds and pushes the image automatically

## Configuration

All settings are stored in the database and configurable via the web UI (`/settings`):

| Setting | Description |
|---|---|
| Papierkram API URL | Your Papierkram instance URL |
| Papierkram API Key | Bearer token from /einstellungen/api |
| Paperless Base URL | Your Paperless-ngx instance URL |
| Paperless API Token | Token from your Paperless user profile |
| Polling Interval | How often to check for new invoices (minutes) |
| Default Tags | Paperless tag IDs to apply (JSON array, e.g. `[5, 12]`) |
| Default Document Type | Paperless document type ID |
| Default Correspondent | Paperless correspondent ID |

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Generate a key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set env
export SECRET_KEY=<generated-key>
export DATABASE_URL=sqlite:///./data/papersync.db
mkdir -p data logs

# Run migrations
alembic upgrade head

# Start
uvicorn app.main:app --reload
```

## Tests

```bash
pip install -r requirements.txt
pytest
```

## Backup & Restore

All persistent data is in the `./data/` volume mount:
- `papersync.db` — SQLite database (settings, dedup table, logs)

Backup: `cp data/papersync.db data/papersync.db.bak`

Restore: Stop container, replace `papersync.db`, restart.

## Troubleshooting

**Container won't start:** Check that `SECRET_KEY` is set and is a valid Fernet key.

**Sync fails with auth error:** Re-enter credentials in Settings — the key may have changed.

**Duplicate documents in Paperless:** Check the `processed_documents` table. A row per invoice should already exist.

**`Too Many Requests` from Papierkram:** Increase the polling interval in Settings.
