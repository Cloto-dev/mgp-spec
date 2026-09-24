# mgp-spec Development Rules

Canonical specification repository for the **Multi-Agent Gateway Protocol (MGP)** — a strict superset of MCP that adds protocol-level security, access control, and observability. This repo contains only the **protocol documents** (`docs/MGP_*.md`), **JSON schemas** (`schemas/`), and **CHANGELOG**. Runtime implementations live in `mgp-rs` (Rust), `mgp-py` (Python), and downstream server collections.

> Inherits: `../CLAUDE.md` — Conventions (RFC 2119), Public Repository English-only, Git Rules.

## Mandatory Reads

Read the actual files; do not summarize (parent rule `feedback_doc_firsthand_reading`).

- **`docs/MGP_SPEC.md`** — Top-level entrypoint. Carries the canonical `**Version:** X.Y.Z-draft` header that all sub-docs align to.
- **`docs/MGP_GUIDE.md` §18 Version History** — Companion to `CHANGELOG.md`. The two must agree.
- **`schemas/connector/v1.json`** — Canonical `cloto-connector.json` schema (Draft 2020-12, `$id = https://cloto.dev/schemas/connector/v1.json`). Reference implementations: `mgp-rs/crates/mgp-sdk` (Rust) and `mgp-py/packages/mcp-common` (Python). Companion doc: `docs/MGP_CONNECTOR.md`.

## Repository Scope

| In scope | Out of scope |
|---|---|
| Normative protocol text (`docs/MGP_*.md`) | Runtime / SDK code |
| JSON schemas (`schemas/**/*.json`) | SDK helpers (those live in `mgp-rs` / `mgp-py`) |
| Reference examples within docs | Working server implementations |
| CHANGELOG.md | Test fixtures of implementations |
| README.md, LICENSE | Build configs |
| The consistency check (`.github/`) | |

## Versioning Discipline

The protocol version (e.g. `0.6.3-draft`) is **stamped in three places** that must move together:

1. `docs/MGP_SPEC.md` — top header `**Version:** X.Y.Z-draft`
2. All sub-docs (`MGP_COMMUNICATION.md`, `MGP_DISCOVERY.md`, `MGP_GUIDE.md`, `MGP_SECURITY.md`) — `> Part of the [MGP Specification](MGP_SPEC.md) (vX.Y.Z-draft, YYYY-MM-DD)`
3. `CHANGELOG.md` — corresponding entry with date

**MUST**: A spec bump touches all three in the same commit. A drift between MGP_SPEC.md and CHANGELOG.md is a release-blocking inconsistency.

**SHOULD**: Update `README.md` status badge (`status-draft%20vX.Y.Z`) in the same commit. (Historical drift: README has lagged real version before.)

**MAY**: Skip intermediate version numbers (e.g. `0.6.2` was skipped between `0.6.1` and `0.6.3`) when reserving for parallel work — note the skip in CHANGELOG.

`docs/MGP_ISOLATION_DESIGN.md` carries its own independent version (`0.1.0-draft` at time of writing) because it is staged separately; do **not** auto-bump it during MGP_SPEC version bumps unless its content actually changed.

## Schema Authority

`cloto-connector.json` is the manifest connector repos publish to advertise themselves to ClotoHub. `schemas/connector/v1.json` is its **single normative source**.

- **MUST**: For any backwards-incompatible schema change, mint a new file (`v2.json`) with bumped `$id` path. Additive optional fields may stay on `v1`.
- **MUST**: Companion doc `docs/MGP_CONNECTOR.md` explains schema fields in prose and stays in sync with the JSON Schema.
- **SHOULD**: Reference implementations cite the schema `$id` URL in their docstrings/comments so consumers can trace authority.

## Consistency Check (CI)

This is a **docs-only** repository: no test runner, no build step. One check runs on every pull request and on every push to `main` (`.github/workflows/check.yml` → `.github/scripts/check_spec.py`):

1. **Relative Markdown links resolve** — the target file exists and, for `#anchor` links, the target has that heading (GitHub's anchor rules). Links inside code are not checked.
2. **Schemas are valid** — every `schemas/**/*.json` is a Draft 2020-12 schema whose `$id` is `https://cloto.dev/schemas/<path>`.
3. **Version stamps agree** — the `**Version:**` of `docs/MGP_SPEC.md` equals the stamp of the four sub-docs and has a row in `CHANGELOG.md` and in `docs/MGP_GUIDE.md` §18.1, with the same date. The README badge is a SHOULD (see Versioning Discipline), so a mismatch there is a warning, not a failure.

- **MUST**: A pull request merges only once `check` has passed.
- Run it locally with `python3 -m venv .venv && .venv/bin/pip install jsonschema && .venv/bin/python .github/scripts/check_spec.py`.
- A new rule in this file that can be checked mechanically belongs in the script, not only here.

## Public Repo Implications

This repo is `visibility=public` and MIT-licensed. Per the parent rule:

- All Markdown content (including this CLAUDE.md) **MUST** be English.
- Commit messages, PR descriptions, and CHANGELOG entries **MUST** be English.
- Existing Japanese example dialogue / phrases preserved in `MGP_DISCOVERY.md` etc. as historical or linguistic content are exempt — they are quoted text, not normative prose.

## Prohibited

- **MUST NOT**: Land runtime code, executable fixtures, or SDK helpers here. They belong in `mgp-rs` / `mgp-py` / consumer repos.
- **MUST NOT**: Bump a sub-doc's version stamp without also touching `MGP_SPEC.md` and `CHANGELOG.md` in the same commit.
- **MUST NOT**: Edit historical CHANGELOG entries (they are an append-only record of past decisions).
