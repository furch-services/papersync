# Stage 1: Build dependencies
FROM python:3.13-slim AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --prefix=/install --no-cache-dir --no-warn-script-location -r requirements.txt

# Stage 2: Runtime image
FROM python:3.13-slim AS runtime

LABEL org.opencontainers.image.title="PaperSync" \
      org.opencontainers.image.description="Synchronizes Papierkram invoices to Paperless-ngx"

RUN groupadd --gid 1000 papersync \
    && useradd --uid 1000 --gid papersync --no-create-home --shell /usr/sbin/nologin papersync

WORKDIR /app

COPY --from=builder /install /usr/local
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .

RUN mkdir -p /app/data /app/logs \
    && chown -R papersync:papersync /app

USER papersync

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
