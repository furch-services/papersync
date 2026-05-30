#!/bin/sh
set -e

chown -R papersync:papersync /app/data /app/logs 2>/dev/null || true

exec gosu papersync uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --proxy-headers \
    --forwarded-allow-ips "*"
