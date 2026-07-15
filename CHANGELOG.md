# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Initial repository scaffold: project structure, `.env.example`, `requirements.txt`, GitHub issue/PR templates, CI workflow stub.
- Initial [Software Development Document](docs/SDD.md) covering mission, architecture, data model, page-by-page UI spec, and branding guidelines.

### Decided
- Adopted a live-search architecture (GovInfo Search Service for keyword search + on-demand Congress.gov lookups) instead of bulk-syncing the full bill corpus — see `docs/SDD.md` §3.

### Known issues
- Congress.gov API key on file is invalid (`API_KEY_INVALID`) — needs re-registration before the bill-detail integration can be tested end-to-end.

## [0.1.0] - 2026-07-14
### Added
- Project initialized.
