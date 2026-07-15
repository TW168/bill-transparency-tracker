# Contributing

This is currently a solo project, but it's managed with normal open-source hygiene so it stays maintainable as it grows.

## Branching

We use **GitHub Flow**: `main` is always deployable.

- Create a short-lived branch off `main` for each change: `feature/<short-name>` or `fix/<short-name>`.
- Open a pull request into `main` when ready. Don't push directly to `main`.

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add bill search endpoint`
- `fix: correct concentration score rounding`
- `docs: update SDD with admin auth decision`
- `chore: bump dependencies`
- `refactor: extract lda_client into its own module`

## Pull requests

Use the PR template (`.github/PULL_REQUEST_TEMPLATE.md`). Before requesting review, confirm:

- [ ] CI passes (lint + tests)
- [ ] If this change affects scope, architecture, the data model, or user-facing behavior, `docs/SDD.md` has been updated in the same PR
- [ ] `CHANGELOG.md` has a new entry under `[Unreleased]`

## Versioning

[Semantic Versioning](https://semver.org/): bump **minor** for new features, **patch** for fixes, **major** only after v1 is stable and a breaking change is made.

## Documentation policy

`docs/SDD.md` is the living source of truth for this project. Any change to scope, architecture, data model, or page design must be reflected there — not just in code comments or PR descriptions.
