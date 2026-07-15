# Software Development Document — Bill Transparency Tracker

**Version:** 0.1.0 (Draft — Initial Build Spec)
**Status:** Ready for implementation
**Owner:** Tony
**Last updated:** 2026-07-14

> This document is the single source of truth for building this application. It is written to be handed to an AI coding assistant (e.g. GitHub Copilot / Copilot Workspace) to scaffold and implement the app. Any implementation decision not covered here should be flagged as an open question rather than silently assumed — see Section 15.
>
> **Living document policy:** This app is an ongoing project. Every meaningful change to scope, architecture, or behavior MUST be reflected here and in `CHANGELOG.md` in the same pull request that makes the change. See Section 13.

---

## 1. Mission & Core Thesis

Most bill-tracking sites (e.g. [GovTrack](https://www.govtrack.us/congress/bills)) present bills using their official titles and summaries, which are usually written in broad, public-interest language ("An Act to promote small business growth..."). In practice, many bills concentrate their real-world benefit on a narrow set of companies, industries, or organizations.

**This app's core value proposition:** for each bill, show *who actually benefits* — not just the generic demographic/public framing, but the specific companies, industries, or organizations most likely to gain, backed by transparent, inspectable evidence (lobbying disclosures, named entities in bill text, sponsor/committee patterns). The goal is to build user trust by making concentrated-benefit patterns visible, not to editorialize on whether a bill is good or bad.

Every beneficiary claim shown to a user must be traceable to a rule, a lobbying filing, or an extracted text reference — never an unexplained AI assertion.

## 2. Goals (v1) and Non-Goals

**Goals:**
- Search and browse bills from the current Congress (119th) and view full bill detail (status, sponsors, actions, summary).
- Layer A: broad, rule-based beneficiary tagging (industry/sector level) derived from bill metadata (policy area, subjects, committee).
- Layer B: narrow, named-beneficiary detection via lobbying disclosure matching + light AI-assisted entity extraction from bill text, with a human-in-the-loop admin review queue before anything is shown as "confirmed."
- A "Benefit Concentration Score" summarizing how narrow vs. broad a bill's likely beneficiaries are.
- Clean, professional, official-feeling UI (Bootstrap 5, red/white/blue theme).
- Dockerized deployment to a personal VPS.

**Non-goals (v1):**
- Campaign finance data (deferred to v2).
- Full historical Congress coverage (v1 is current Congress only; schema should not preclude adding more later).
- Real-time (sub-hour) data freshness — not needed for this use case.
- Public user accounts / comments / social features.

## 3. Architecture Overview

**Key architectural decision: live search, no bulk corpus sync.**

Earlier drafts of this project considered bulk-syncing the entire bill corpus into MySQL on a schedule. That has been superseded by a **live-query architecture**, because:
- Congress.gov's API has no keyword/full-text search — it only filters by congress, bill type, and date range ([Congress.gov API BillEndpoint docs](https://github.com/LibraryOfCongress/api.congress.gov/blob/main/Documentation/BillEndpoint.md)).
- GovInfo (also a Library of Congress / GPO service) exposes a proper **Search Service API** that does full-text keyword search over the Congressional Bills collection, live, with no local index needed ([GovInfo Search Service](https://www.govinfo.gov/features/search-service-overview)).

Resulting flow:

```
User searches keyword
        │
        ▼
POST https://api.govinfo.gov/search   (collection:(BILLS), query, congress filter)
        │  returns ranked matches: congress, bill type, bill number, title, package id
        ▼
User clicks a result
        │
        ▼
GET https://api.congress.gov/v3/bill/{congress}/{billType}/{number}   (live, on-demand)
        │  returns sponsors, actions, subjects, summary, status
        ▼
App checks local cache (MySQL) for this bill's beneficiary analysis
        │
   ┌────┴────┐
   │ cached? │──yes──▶ render immediately
   └────┬────┘
        no
        ▼
Run Layer A (rule match) + Layer B (lobbying match, AI text extraction if needed)
        │
        ▼
Persist result to local cache, render page
```

This means: **no scheduled bulk sync job**, no "how much disk do I need for 17,000 bills" problem, and no staleness — search and bill detail are always live. The only things stored long-term are:
- Beneficiary rules and beneficiary groups (small, curated, edited by admin).
- Cached beneficiary analysis *per bill actually viewed* (grows slowly, proportional to traffic, not corpus size).
- Lobbying filings that have been matched to a viewed bill (not the entire LDA database).
- Named entities extracted from bill text (per viewed bill).
- Admin entity-review queue state.

A lightweight background job still exists, but its job is much smaller: periodically refresh cached analysis for bills whose lobbying/text data may have changed (see Section 6), not a full-corpus sync.

## 4. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.12 | |
| Web framework | FastAPI | async, OpenAPI docs for free |
| Templating | Jinja2 | server-rendered pages |
| Frontend | Bootstrap 5 (via CDN or `django-bootstrap`-style local vendoring — decide in Section 8) + light HTMX for partial updates (e.g. admin approve/reject without full reload) | no SPA framework needed for v1 |
| Database | MySQL 8 | via SQLAlchemy 2.0 ORM |
| DB driver | `PyMySQL` (pure Python, simplest to containerize) | |
| Migrations | Alembic | |
| HTTP client | `httpx` (async) | for Congress.gov, GovInfo, LDA calls |
| Scheduler | APScheduler | small periodic refresh job only (see Section 6), not a bulk sync |
| Settings/secrets | `pydantic-settings` reading from `.env` | never commit real secrets |
| AI layer | Provider-agnostic wrapper (pluggable — OpenAI/Anthropic/etc. behind one interface) used only for: (a) bill text summarization, (b) named-entity suggestion for Layer B | All AI output is a *suggestion*, gated by human review before being shown as confirmed |
| Testing | `pytest` + `httpx.AsyncClient` for endpoint tests | |
| Containerization | Docker + docker-compose (app + MySQL, persistent named volume for DB data) | |

## 5. External Integrations

### 5.1 GovInfo Search Service API (bill search)
- Endpoint: `POST https://api.govinfo.gov/search`
- Auth: `api.data.gov` API key (query param `api_key`), free signup at [api.data.gov](https://api.data.gov/)
- Query pattern: `collection:(BILLS) AND congress:119 AND <keywords>`
- Rate limit: standard api.data.gov tier (~1,000 req/hr) — fine for personal use.
- Source: [GovInfo Search Service announcement](https://www.govinfo.gov/features/search-service-overview)

### 5.2 Congress.gov API v3 (bill detail)
- Endpoint: `GET https://api.congress.gov/v3/bill/{congress}/{billType}/{billNumber}` and sub-resources (`/actions`, `/subjects`, `/summaries`, `/cosponsors`)
- Auth: separate `api.congress.gov` key. **Known issue:** the key currently on file for this project returns `API_KEY_INVALID` — needs re-registration at [api.congress.gov/sign-up](https://api.congress.gov/sign-up) before this integration can go live. Track as an open item (Section 15).
- No keyword search — congress/bill type/date range filters only.
- Source: [Congress.gov API BillEndpoint docs](https://github.com/LibraryOfCongress/api.congress.gov/blob/main/Documentation/BillEndpoint.md)

### 5.3 Senate LDA (Lobbying Disclosure Act) API — Layer B data source
- Current base: `https://lda.senate.gov/api/v1/` — **retiring after 07/31/2026**, migrating to `https://lda.gov/`. Build against current base now; isolate behind a client module (`lda_client.py`) so the migration is a one-file change.
- Unauthenticated: 15 req/min. Registered (free) key: 120 req/min — register at [lda.senate.gov/api/register](https://lda.senate.gov/api/register/).
- Filings have a free-text `specific_issues` field, not directly linked to bill IDs. Matching requires text-matching bill numbers/titles in that field, or AI-assisted inference for filings that reference a bill without citing its number explicitly.

### 5.4 AI layer (Layer B assist + summarization)
- Used for: (a) plain-language summarization of dense bill text, (b) suggesting named entities/organizations likely to benefit when lobbying filings don't give an explicit match.
- **All AI-suggested beneficiary matches are non-authoritative until approved** in the admin entity-review queue (Section 8.5). Never render an AI suggestion as a confirmed fact.

### 5.5 USAFacts (contextual stats — optional enrichment)
- No public API. Manual CSV/XLSX download, imported via a one-off admin script. Used only for contextual statistics (e.g. "this policy area affects X% of..."), not core beneficiary logic.

## 6. Sync / Refresh Job (lightweight, not a bulk sync)

Since there is no bulk corpus, the background job's only responsibilities are:
1. **Re-check cached bills periodically** — for bills already cached (i.e., previously viewed), re-check Congress.gov for status changes on a modest cadence (e.g. every 6–24 hours) so a user re-visiting a bill they cached weeks ago sees current status, not a stale snapshot.
2. **Lobbying filing refresh** — LDA filings update quarterly (LD-2) / semi-annually (LD-203) by law, so a weekly-to-monthly check for new filings referencing cached bills is sufficient.
3. **Re-run entity extraction only on bill text version change** — detected via version count/hash comparison, never on a timer.

This job touches only the (small, slowly-growing) set of bills users have actually viewed — not the full ~17,000-bill/Congress corpus.

## 7. Data Model

| Table | Purpose | Key fields |
|---|---|---|
| `beneficiary_group` | Curated list of broad beneficiary categories (e.g. "Defense Contractors", "Small Business", "Pharmaceutical Industry") | id, name, description |
| `beneficiary_rule` | Rule mapping bill metadata (policy area / subject / committee) → beneficiary_group (Layer A) | id, group_id, match_field, match_value |
| `bill_cache` | On-demand cache of a fetched bill's Congress.gov detail (replaces bulk bill sync) | congress, bill_type, bill_number (composite key), title, sponsor, status, summary, last_fetched_at, text_version_count |
| `bill_beneficiary` | Layer A result: which beneficiary_group(s) matched a cached bill | bill fk, group_id, rule_id |
| `lobbying_filing` | LDA filings matched to a cached bill (subset only, not the full LDA dataset) | id, registrant, client, specific_issues_text, filing_period, amount |
| `bill_lobbying_match` | Link between a cached bill and a lobbying_filing, with match confidence/method | bill fk, filing fk, match_method (explicit/AI-inferred), confidence |
| `named_entity` | Organizations/companies extracted from bill text or lobbying data | id, name, entity_type, source |
| `bill_named_entity` | Link between a cached bill and a named_entity, pending or approved | bill fk, entity_id, status (pending/approved/rejected), source, reviewed_by, reviewed_at |
| `concentration_score` | Computed Benefit Concentration Score per cached bill | bill fk, score, label (broad/moderate/narrow), computed_at, entity_count, breadth_ratio |
| `usafacts_stat` | Optional contextual stats imported from USAFacts CSV/XLSX | id, topic, value, source_url, imported_at |

All tables reference bills by the composite natural key `(congress, bill_type, bill_number)` — never store a bulk "all bills" table; `bill_cache` only ever contains rows for bills a user has actually opened.

## 8. Beneficiary Analysis Engine

### 8.1 Layer A — Broad, rule-based (runs first, cheap, always available)
Matches a cached bill's policy area / legislative subjects / committee against `beneficiary_rule` entries. No AI involved. Always shown, always fast.

### 8.2 Layer B — Narrow, named-beneficiary detection
1. **Explicit match**: search matched lobbying filings' `specific_issues_text` for the bill's number/short title.
2. **AI-assisted inference**: when no explicit match exists, the AI layer proposes candidate organizations from bill text + related lobbying filings on similar issue codes. Output is a *suggestion*, stored in `bill_named_entity` with `status = pending`.
3. **Human review**: nothing from step 2 is shown to end users as confirmed until approved via `/admin/entity-review`.

### 8.3 Benefit Concentration Score
Computed from: number of distinct confirmed named entities, how concentrated lobbying spend is among them, and the ratio of named beneficiaries to the bill's stated "public" scope (breadth ratio). Bands (broad / moderate / narrow) — exact thresholds are an open decision (Section 15); ship with a documented default and make it easy to retune without a migration.

### 8.4 Trust & transparency requirement
Every beneficiary shown on a bill detail page must link back to its evidence: the matched rule, the lobbying filing, or "AI-suggested, pending human review" — never an unlabeled claim.

### 8.5 Admin entity review queue
A page where the site owner (only) approves/rejects AI-suggested entities before they appear publicly. This is what keeps the trust thesis credible — no AI guess reaches an end user unreviewed.

## 9. Page-by-Page UI Spec

**Global requirement: one Jinja2 template per page unless otherwise specified. Bootstrap 5. Red/white/blue color theme, professional/official look (see Section 10 for exact styling).**

| # | Page | Route | Template | Purpose / key elements |
|---|---|---|---|---|
| 1 | Home / Landing | `GET /` | `base.html` + `home.html` | Hero section explaining the mission (Section 1) in plain language, prominent search bar, "how it works" 3-step visual (Search → Bill → Who Benefits), a few featured/recent bills as cards |
| 2 | Search Results | `GET /search?q=...&congress=119` | `search_results.html` | Search bar (persisted query), Congress-session toggle, result list as Bootstrap cards/list-group (title, bill number, introduced date, status badge), pagination, empty-state message |
| 3 | Bill Detail | `GET /bills/{congress}/{bill_type}/{number}` | `bill_detail.html` | Official bill header (number, title, sponsor, status timeline), tabbed or sectioned layout: Summary, Actions, **"Who Actually Benefits"** panel (Concentration Score badge + Layer A group chips + confirmed Layer B named entities with evidence links), source citations to Congress.gov/GovInfo |
| 4 | About / Mission | `GET /about` | `about.html` | Explains the transparency thesis, methodology (how Layer A/B work, what "pending review" means), data source credits/links |
| 5 | Admin — Beneficiary Rules | `GET /admin/rules` | `admin_rules.html` | CRUD table for `beneficiary_group` / `beneficiary_rule` (owner-only, auth-gated) |
| 6 | Admin — Entity Review | `GET /admin/entity-review` | `admin_entity_review.html` | Queue of pending `bill_named_entity` rows with approve/reject actions (HTMX partial update, no full reload), shows the evidence (filing text / AI rationale) next to each |
| 7 | Base layout | (shared) | `base.html` | Navbar (brand, Search, About, Admin dropdown if authenticated), footer (data source attribution, GitHub link), red/white/blue theme applied via `static/css/theme.css` override on top of Bootstrap 5 |
| 8 | Error pages | 404 / 500 | `404.html`, `500.html` | On-brand, simple, link back to home |

Admin pages (5, 6) require basic auth-gating (a single-owner login, not multi-user accounts — v1 scope) — implementation detail for Copilot to propose, flagged as an open decision in Section 15 if session-based auth vs. simple token isn't specified.

## 10. Visual Design & Branding

**Goal: look like an official, professional government-transparency site — trustworthy, not flashy.**

- **Color palette** (WCAG-AA contrast checked for text-on-background use):
  - Navy blue (primary): `#0A3161` — navbar, headers, primary buttons
  - Old Glory red (accent): `#B31942` — status badges, "narrow beneficiary" concentration alerts, active nav state
  - White: `#FFFFFF` — page background, card backgrounds
  - Neutral gray (supporting): `#5A6B7B` — secondary text, muted metadata
  - Avoid pure bright red (`#FF0000`) on white for large text blocks — insufficient contrast/too aggressive; reserve red for badges, small accents, and alert states only.
- **Typography:** Bootstrap 5 default system font stack for body text (fast, native, professional); a slightly more formal serif (e.g. "Georgia", `serif` fallback) for the site title/logo wordmark only, to read as "official" rather than "startup."
- **Bootstrap 5 usage:** use Bootstrap 5 via CDN (simplest for a solo project; document the exact version pinned, e.g. 5.3.x) with a small custom `theme.css` that overrides Bootstrap CSS variables (`--bs-primary`, `--bs-danger`, etc.) to the palette above rather than fighting Bootstrap's defaults with `!important` overrides.
- **Concentration Score badge:** use Bootstrap `badge` component — green/blue for "broad", amber for "moderate", red (`#B31942`) for "narrow" — always paired with the word label, never color alone (accessibility).
- **Logo/header:** simple text wordmark is acceptable for v1 (e.g. "🔎 Bill Transparency Tracker" or a plain shield-style icon) — no custom illustration required for v1.

## 11. API Endpoints (FastAPI routes)

| Method | Path | Description |
|---|---|---|
| GET | `/` | Home page |
| GET | `/search` | Search results (proxies GovInfo Search Service) |
| GET | `/bills/{congress}/{bill_type}/{number}` | Bill detail (fetch-or-cache from Congress.gov + run/read beneficiary analysis) |
| GET | `/about` | Mission/methodology page |
| GET | `/admin/rules` | List beneficiary rules (auth-gated) |
| POST | `/admin/rules` | Create/update a rule (auth-gated) |
| GET | `/admin/entity-review` | Pending entity review queue (auth-gated) |
| POST | `/admin/entity-review/{id}/approve` | Approve a pending named entity (auth-gated, HTMX partial response) |
| POST | `/admin/entity-review/{id}/reject` | Reject a pending named entity (auth-gated, HTMX partial response) |
| GET | `/healthz` | Liveness check for Docker/VPS monitoring |

## 12. Project Structure

```
bill-transparency-tracker/
├── app/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── config.py                # pydantic-settings, reads .env
│   ├── routers/                 # one router module per page group (public, admin)
│   ├── models/                  # SQLAlchemy models (one file per table or logical group)
│   ├── services/                # govinfo_client.py, congress_client.py, lda_client.py,
│   │                             # beneficiary_engine.py, concentration_service.py, ai_client.py
│   ├── templates/                # Jinja2 templates, one per page (Section 9) + base.html
│   └── static/
│       ├── css/theme.css        # Bootstrap 5 variable overrides (Section 10)
│       ├── js/
│       └── img/
├── migrations/                  # Alembic migrations
├── tests/                       # pytest suite
├── docs/
│   └── SDD.md                   # this document — keep current
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/ci.yml
├── .env.example                 # documented env vars, no real secrets
├── .gitignore
├── requirements.txt
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## 13. Development Workflow & Documentation Policy

- **Branching:** GitHub Flow — `main` is always deployable. All work happens on short-lived feature branches (`feature/<short-name>`, `fix/<short-name>`), merged via pull request. No long-lived `develop` branch for a solo project — adds overhead without benefit at this scale.
- **Commit messages:** [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`) — makes CHANGELOG generation and history scanning easier later.
- **Pull requests:** use `.github/PULL_REQUEST_TEMPLATE.md`; every PR that changes scope, architecture, data model, or user-facing behavior MUST update `docs/SDD.md` and add an entry to `CHANGELOG.md` in the same PR.
- **Versioning:** [Semantic Versioning](https://semver.org/) starting at `0.1.0`; bump minor for new features, patch for fixes, major only after v1 is stable and a breaking change is made.
- **Changelog:** [Keep a Changelog](https://keepachangelog.com/) format in `CHANGELOG.md`, with an `Unreleased` section always at the top.
- **CI:** GitHub Actions runs lint + tests on every push/PR (see `.github/workflows/ci.yml`). Keep it green — a red `main` branch defeats the "always deployable" branching model.

## 14. Deployment

- Docker + docker-compose: `app` service (FastAPI/Uvicorn) + `db` service (MySQL 8) with a **named, persistent volume** for the MySQL data directory (containers are ephemeral — data must not live only in the container's writable layer).
- Given the live-search architecture (Section 3), storage needs are small: no bulk corpus, only per-viewed-bill caches. A modest VPS (1–2 vCPU, 2 GB RAM, 20 GB disk) is more than sufficient.
- Environment variables injected via `.env` (local) or the VPS's secret store (production) — never baked into the image.
- Periodic `mysqldump` backups recommended, primarily to avoid re-running AI entity extraction on cached bills (the underlying public data is always re-fetchable, but the AI-derived + admin-approved analysis is not free to regenerate).

## 15. Open Decisions (track and resolve before/while building)

1. **Congress.gov API key is currently invalid** (`API_KEY_INVALID`) — must re-register at [api.congress.gov/sign-up](https://api.congress.gov/sign-up) before Section 5.2 integration can be tested end-to-end.
2. GovInfo API key registration (api.data.gov) not yet done.
3. Exact Concentration Score thresholds (Section 8.3) — ship a documented default, revisit after seeing real data.
4. Admin auth mechanism (single-owner session vs. token) — not yet specified, needs a decision before Section 9 items 5–6 are built.
5. LDA → lda.gov migration timeline (deadline 07/31/2026) — build against current `lda.senate.gov` base now, isolate in `lda_client.py`.
6. AI provider choice for the AI layer (Section 5.4) — keep behind a provider-agnostic interface so this is swappable without touching business logic.

## 16. Notes for the AI Coding Assistant (Copilot)

- Treat this document as the source of truth. If an instruction here conflicts with a general best practice, prefer this document, but flag the conflict in the PR description.
- Build incrementally: scaffold `app/main.py` + `base.html` + Home page first, then Search, then Bill Detail (the core loop), then the two admin pages, then the AI-assisted Layer B pieces last (they depend on everything else existing).
- Do not implement bulk bill-corpus syncing — this was intentionally rejected in favor of the live-search architecture (Section 3). If you find yourself writing a "sync all bills" job, stop and re-read Section 3.
- Every new table, endpoint, or template must show up in Sections 7, 11, and 9/12 respectively — update this document as part of the same change.
- Never render an AI-suggested beneficiary as confirmed without the admin approval step (Section 8.5) — this is the credibility mechanism the whole app is built around.
