# Security Policy

## Supported versions

Only the latest release of PaperSync receives security fixes. Older versions are not backported.

| Version | Supported |
|---|---|
| latest | ✅ |
| older | ❌ |

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities by email to **Maximilian Furch** at **github@furch-services.de**. Include:

- A description of the vulnerability and its potential impact
- Steps to reproduce or a proof-of-concept (redact any credentials)
- The PaperSync version affected (Docker image tag or commit SHA)

You will receive an acknowledgement within **72 hours**. We aim to release a fix within **14 days** for critical issues, depending on complexity.

We will credit you in the release notes unless you prefer to remain anonymous.

## Scope

The following are in scope:

- Authentication bypass or session token vulnerabilities
- Sensitive data exposure (API keys, credentials stored in the database)
- Remote code execution or server-side injection
- Path traversal or arbitrary file read/write
- CSRF vulnerabilities in the web UI
- Dependency vulnerabilities with a known CVE and active exploit

The following are out of scope:

- Vulnerabilities that require physical access to the host
- Issues in dependencies without a known CVE or active exploit
- Self-XSS or attacks that require the attacker to already be authenticated as an admin
- Denial-of-service via API flooding (mitigate with your reverse proxy)
- Security findings from automated scanners without manual validation

## Security model

PaperSync is designed as a **single-tenant, self-hosted** application. The assumed deployment is:

- Running inside a private Docker network
- Exposed exclusively through a reverse proxy (Caddy, nginx, Traefik, etc.) with TLS
- Not directly accessible from the public internet on port 8000

Within that model:

- API credentials (Papierkram, Paperless-ngx) are encrypted at rest using **Fernet** symmetric encryption.
- Web UI sessions use **signed, timed tokens** (itsdangerous) with a per-session nonce (jti) and server-side revocation on logout.
- Passwords are never stored — only compared at runtime using `hmac.compare_digest`.
- The container runs as an **unprivileged user** (UID 1000) after startup.

If you deploy PaperSync outside this model (e.g. exposed directly to the internet without a reverse proxy), additional hardening is your responsibility.
