# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1] - 2026-07-08

### Added
- Dependabot configuration for automated dependency updates (pip, Docker, GitHub Actions), running weekly on Mondays

### Security
- Updated `python-multipart` 0.0.20 → 0.0.32: resolves 6 CVEs including denial-of-service via unbounded multipart part headers, quadratic querystring parsing, large preamble/epilogue data, arbitrary file write, negative Content-Length memory buffering, and parameter smuggling via RFC 2231/5987
- Updated `cryptography` 45.0.3 → 49.0.0: resolves 3 CVEs including vulnerable OpenSSL included in wheels, buffer overflow with non-contiguous buffers, and subgroup attack due to missing validation for SECT curves
- Updated `pytest` 8.3.5 → 9.1.1: resolves vulnerable tmpdir handling
- Replaced SHA-256 password hashing with Argon2 to prevent brute-force attacks on stored credentials (CWE-327, CWE-328, CWE-916)
- Added explicit least-privilege `permissions` block to GitHub Actions workflow to enforce principle of least privilege regardless of repository defaults

## [1.0.0] - 2026-05-30

### Added
- Initial release: synchronizes sent invoices from Papierkram to Paperless-ngx
- Password-protected web dashboard with status monitoring, manual sync, dry-run mode, and log viewer
- Retry mechanism for failed document uploads with configurable `MAX_RETRIES`
- Sync statistics on the dashboard
- Webhook endpoint for external trigger via `POST /sync/trigger`
- Single-container deployment with SQLite, APScheduler, and no external dependencies
- Docker image published to GitHub Container Registry
- Unraid community template
