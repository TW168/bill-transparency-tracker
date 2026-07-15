# Bill Transparency Tracker

A web app for browsing and searching bills before the U.S. Congress — with a focus on surfacing **who actually benefits** from each bill, not just its official public-facing framing.

Most bill-tracking sites (like [GovTrack](https://www.govtrack.us/congress/bills)) present bills using broad, public-interest language. In practice, many bills concentrate their real benefit on a narrow set of companies, industries, or organizations. This project aims to make that visible — backed by transparent, sourced evidence (lobbying disclosures, extracted bill text references, sponsor/committee patterns) rather than unexplained claims.

**Read the full [Software Development Document](docs/SDD.md) before contributing** — it is the living source of truth for scope, architecture, and page-by-page design.

## Status

🚧 Early development. See [CHANGELOG.md](CHANGELOG.md) for progress and [docs/SDD.md § 15](docs/SDD.md#15-open-decisions-track-and-resolve-beforewhile-building) for open decisions.

## Tech stack

FastAPI · Jinja2 · Bootstrap 5 · MySQL 8 · SQLAlchemy 2.0 · Alembic · httpx · APScheduler · Docker

## Data sources

- [Congress.gov API](https://api.congress.gov/) — bill metadata, sponsors, actions, status
- [GovInfo Search Service](https://www.govinfo.gov/features/search-service-overview) — full-text bill search
- [Senate LDA API](https://lda.senate.gov/api/) — lobbying disclosure filings (migrating to lda.gov by 07/31/2026)
- [USAFacts](https://usafacts.org/) — contextual public statistics (manual CSV/XLSX import)

## Getting started

1. Copy `.env.example` to `.env` and fill in your API keys (see comments in the file for where to get each one).
2. `docker compose up --build` (once the compose file exists — see [docs/SDD.md § 14](docs/SDD.md#14-deployment)).
3. Visit `http://localhost:8000`.

## Contributing

This is currently a solo project, but it follows normal open-source hygiene — see [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming, commit conventions, and the PR checklist.

## License

[MIT](LICENSE)
