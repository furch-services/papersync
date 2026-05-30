# Contributing to PaperSync

Thank you for your interest in contributing. PaperSync is maintained by [Furch Services](https://furch-services.de) — this document covers everything you need to get started.

## Before you start

- Check the [open issues](../../issues) before opening a new one — your bug or idea may already be tracked.
- For significant changes, open an issue first to discuss the approach before writing code.
- By contributing, you agree that your work will be licensed under [AGPL-3.0](LICENSE).

## Development setup

**Requirements:** Python 3.13, Docker

```bash
git clone https://github.com/furch-services/papersync.git
cd papersync

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

The app is now running at `http://localhost:8000`. Log in with username `admin` and the password you set via `APP_PASSWORD`.

## Project structure

```
app/
  api/          # Route handlers
  core/         # Config, auth, security utilities
  models/       # SQLAlchemy models
  schemas/      # Pydantic schemas
  services/     # Papierkram and Paperless-ngx API clients
  templates/    # Jinja2 HTML templates
  static/       # Fonts, images, CSS
tests/          # Pytest test suite
alembic/        # Database migrations
```

## Architecture constraints

Please read [CLAUDE.md](CLAUDE.md) for the full architecture rules. The short version:

- **No new infrastructure.** No Redis, RabbitMQ, Celery, PostgreSQL, React, Vue, or Node.js.
- **Scheduler stays in-process.** APScheduler runs inside the app container — no separate worker.
- **SQLite by default.** Only introduce PostgreSQL if explicitly needed and discussed first.
- **Docker must always build.** Every PR must produce a working Docker image.

## Making changes

### Database migrations

If you change a SQLAlchemy model, generate a migration:

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

Always review the generated migration file before committing — autogenerate isn't perfect.

### Code style

The project uses [Ruff](https://docs.astral.sh/ruff/) for linting and [Black](https://black.readthedocs.io/) for formatting:

```bash
ruff check app/ tests/
black app/ tests/
```

Both run as part of CI. PRs with lint or formatting errors will not be merged.

### Type hints

All new code must have full type hints. Use `Pydantic` models for request/response schemas and `SQLAlchemy` typed columns for models.

## Tests

```bash
pytest tests/
# With coverage report:
pytest tests/ --cov=app --cov-report=term-missing
```

Write tests for new features and bug fixes. PRs that reduce coverage without justification will be asked to add tests.

## Submitting a pull request

1. Fork the repository and create a branch from `main`.
2. Make your changes, including tests.
3. Verify the Docker image still builds: `docker build -t papersync:test .`
4. Run the test suite and linters.
5. Open a pull request against `main` with a clear description of what and why.

### Commit messages

Use the conventional commits format:

```
feat: add dry-run mode to manual sync
fix: handle missing invoice PDF gracefully
chore: update dependencies
docs: clarify polling interval setting
```

## Reporting bugs

Open a GitHub issue with:

- PaperSync version (Docker image tag or commit SHA)
- Steps to reproduce
- Expected vs. actual behavior
- Relevant log output (redact any API keys)

## Security vulnerabilities

Do **not** open a public issue for security vulnerabilities. Contact **Maximilian Furch** directly at **github@furch-services.de**. See [SECURITY.md](SECURITY.md) for the full policy.
