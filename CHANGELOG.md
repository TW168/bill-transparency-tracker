# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Initial repository scaffold: project structure, `.env.example`, `requirements.txt`, GitHub issue/PR templates, CI workflow stub.
- Initial [Software Development Document](docs/SDD.md) covering mission, architecture, data model, page-by-page UI spec, and branding guidelines.
- Full FastAPI baseline implementation: public routes (`/`, `/search`, `/bills/{congress}/{bill_type}/{number}`, `/about`, `/healthz`) and admin routes (`/admin/rules`, `/admin/entity-review`, approve/reject endpoints).
- SQLAlchemy data model for beneficiary rules, bill cache, lobbying matches, named entities, concentration scores, and optional USAFacts stats.
- Service layer scaffolding for GovInfo/Congress/LDA clients, beneficiary engine, concentration scoring, analysis orchestration, and lightweight APScheduler refresh job.
- Jinja2 templates and themed Bootstrap 5.3.3 UI for all specified pages, including HTMX-based admin entity review actions.
- Docker deployment files (`Dockerfile`, `docker-compose.yml`) and Alembic scaffold (`alembic.ini`, `migrations/env.py`, initial migration).
- Baseline tests for health and core pages.

### Decided
- Adopted a live-search architecture (GovInfo Search Service for keyword search + on-demand Congress.gov lookups) instead of bulk-syncing the full bill corpus — see `docs/SDD.md` §3.
- Resolved v1 admin auth implementation as single-owner HTTP Basic auth using `ADMIN_USERNAME` / `ADMIN_PASSWORD`.

### Known issues
- Congress.gov API key on file is invalid (`API_KEY_INVALID`) — needs re-registration before the bill-detail integration can be tested end-to-end.

## [0.1.0] - 2026-07-14
### Added
- Project initialized.
