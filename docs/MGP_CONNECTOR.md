# MGP Connector Manifest (`cloto-connector.json`) v1

**Schema:** [`schemas/connector/v1.json`](../schemas/connector/v1.json) (`$id = https://cloto.dev/schemas/connector/v1.json`)
**Reference implementation:** `mgp-sdk` crate in the [`Cloto-dev/mgp-rs`](https://github.com/Cloto-dev/mgp-rs) workspace (`crates/mgp-sdk/src/types.rs`, `validate/connector_v1.rs`, `adapters/`).
**Companion sections in MGP_SPEC.md / MGP_SECURITY.md:** §2.3 (trust tiers), §8 (L0 Magic Seal).

---

## 1. Purpose

`cloto-connector.json` is the contract a connector repository publishes so the catalog layer (ClotoHub.dev) and the runtime layer (ClotoCore install path) can sync, validate, install, and seal it without per-connector special-casing.

The manifest is intentionally minimal in v1:

- Catalog-level metadata (id, name, description, version, category, tags, icon)
- Trust posture (`trust_level`, `magic_seal`)
- One typed source descriptor (`install.source`)
- One package-manager / runtime pair (`install.package_manager`, `install.runtime`)
- Optional host-side hints (`host_compatibility`, `env_vars`, `auto_restart`, `changelog`)

Anything that can be derived (e.g. `entry_point` from `directory` + runtime conventions) or that belongs to a separate spec layer (platform-specific pre-built binaries, multi-file Merkle seals) is deferred to a future revision — see §6.

## 2. Authority and Drift Policy

The Rust struct `mgp_sdk::types::ConnectorManifest` and this JSON Schema are kept in lock-step:

- The schema in this repository is the **normative** contract — third-party validators, web admin UIs, and editors that consume JSON Schema MUST agree with this file.
- `mgp-sdk` is the **reference implementation** — its `serde` derives, `validate_v1`, and `adapters/` are the executable mirror.
- The catalog (ClotoHub.dev `clotohub-web`) and runtime (ClotoCore install path) both depend on `mgp-sdk`; a drift between schema and SDK is a bug to fix in the SDK first, then republish the schema.

When the two ever disagree, the SDK is the truth at the wire level (deserialization, validation), and this schema describes the wire format the SDK currently produces and accepts. The repair direction is therefore SDK → schema, not the reverse.

## 3. Required Fields

| Field | Type | Constraint |
|---|---|---|
| `spec_version` | integer | `= 1` |
| `connector_type` | string | `= "mgp_server"` |
| `id` | string | kebab-case (`[a-z0-9]([a-z0-9-]*[a-z0-9])?`) |
| `name` | string | non-empty |
| `description` | string | (any) |
| `version` | string | non-empty; SHOULD follow SemVer |
| `category` | string | non-empty; open vocabulary |
| `trust_level` | string | one of `core`, `standard`, `experimental`, `untrusted` |
| `magic_seal` | string | `sha256:` + 64 lowercase hex chars |
| `install` | object | see §5 |

### 3.1 `trust_level`

Mirrors MGP_SECURITY.md §2.3. The catalog layer enforces the MGP 0.6.3-draft Security Invariant 3: if `magic_seal` is missing or malformed at registration, the connector is forced to `untrusted` regardless of the value declared here. The declared value is therefore a *request*, not a guarantee.

### 3.2 `magic_seal`

MGP_SECURITY.md §8 L0 Magic Seal. For v1 connectors the seal covers a single entry-file at registration time. Integrity of the remaining files in the source tree is delegated to the package manager's lockfile (`uv.lock`, `Cargo.lock`, etc.) — see §6.1 for the rationale and the multi-file plan.

The format is `sha256:` followed by 64 lowercase hex characters. Catalog implementations MUST reject any other shape, including uppercase hex, missing prefix, or non-SHA-256 algorithms. Future revisions of this schema may add additional algorithms; the prefix discriminant exists for that reason.

## 4. Optional Top-Level Fields

| Field | Type | Default | Notes |
|---|---|---|---|
| `icon` | string &#124; null | `null` | URL or short identifier; UI hint only. |
| `tags` | string[] | `[]` | Marketplace filtering. |
| `host_compatibility` | string[] | `[]` | Hosts that can run this connector (e.g. `clotocore`, `claude-code`, `claude-desktop`, `cursor`, `project-airi`). Empty array means *unspecified*, not *no hosts*. |
| `env_vars` | `EnvVarDef[]` | `[]` | Required environment variables; hosts MUST refuse startup when any is missing. |
| `optional_env_vars` | `EnvVarDef[]` | `[]` | Optional environment variables; hosts MAY pass through when set. |
| `auto_restart` | boolean | `false` | Whether the host should auto-restart on unexpected exit. |
| `changelog` | string &#124; null | `null` | Markdown CHANGELOG; catalogs MAY render on a detail page. |

`EnvVarDef` is `{ name: string, default?: string | null, description?: string | null }`.

| Field | Type | Default | Notes |
|---|---|---|---|
| `name` | string | — | Variable name. Required. Spec-level canonical key. SDK implementations MAY accept legacy field names (e.g. `key`) as a *deserialization alias* for migration from pre-v1 registries that predate this schema; producers MUST emit `name` going forward. The alias is an implementation-side convenience, not a spec-level synonym, so validators applied to a manifest SHOULD reject `key` even when the loading SDK accepted it. See §2 (Authority and Drift Policy) for the (α) implementation-cost-leniency vs (β) acceptance-leniency taxonomy. |
| `default` | string &#124; null | `null` | Default value the host SHOULD inject when the operator has not provided one. Hosts MUST still treat the variable as *set* for downstream contracts when defaulted. Null or omitted means no default; missing values then fall through to host policy (= refuse-to-start for `env_vars`, pass-through-when-set for `optional_env_vars`). |
| `description` | string &#124; null | `null` | Human description. |

Unknown top-level fields are ignored on deserialize to keep v1 → v2 evolution additive. Producers SHOULD NOT rely on this — write only the fields documented here.

## 5. `install` Block

The `install` block is required. It declares how to materialize the connector on the host machine.

```json
{
  "install": {
    "source": { "type": "git", "url": "https://github.com/Cloto-dev/example.git", "reference": "v1.2.3" },
    "package_manager": "uv",
    "runtime": "python",
    "directory": "servers/example",
    "dependencies": [],
    "bin_name": null
  }
}
```

| Field | Type | Required | Constraint |
|---|---|---|---|
| `source` | `SourceSpec` | yes | see §5.1 |
| `package_manager` | string | yes | `= "uv"` in v1 |
| `runtime` | string | yes | one of `python`, `rust`, `node` |
| `dependencies` | string[] | no (default `[]`) | extra deps to resolve in addition to the source's own lockfile |
| `directory` | string | no (default `""`) | subdirectory inside the source tree; `""` means root |
| `bin_name` | string &#124; null | no (default `null`) | binary name produced by the build; used when `runtime = "rust"`, ignored otherwise |

### 5.1 `SourceSpec`

`source` is a discriminated union tagged by `type` (snake_case). v1 defines four variants:

| `type` | Required fields | Optional fields |
|---|---|---|
| `git` | `url` | `reference` (default `""`), `subdir` |
| `raw_url` | `url` (http/https) | `sha256` (64 hex chars when present), `subdir` |
| `pypi` | `package` (no whitespace) | `version` (PEP 440 pin) |
| `docker` | `image` (no whitespace) | `tag` (defaults to `latest`; catalogs SHOULD reject `latest` for production registration) |

`git.reference = ""` means "use the upstream default branch, resolved at fetch time". `raw_url.sha256` is optional but strongly recommended; for binary releases the consumer cannot re-derive, treat it as required at the catalog policy layer. `raw_url.subdir` names the subdirectory inside the extracted archive tree where the connector lives (after the consumer strips a single shared top-level prefix, GitHub-archive-style) — it lets one monorepo tarball serve multiple connectors and mirrors `git.subdir`. `docker.tag = "" | "latest" | null` are all considered unpinned by the SDK's `is_unpinned()` helper.

## 6. Out of Scope for v1 (Planned for v2)

These were considered during v1 design and intentionally deferred. The plan is to introduce them in a v2 schema (new `$id`, additive on the wire) and a parallel `mgp-sdk` minor bump.

### 6.1 Multi-File Seal Coverage

v1 binds `magic_seal` to a single entry-file. Integrity of the remaining files in a connector's source tree is delegated to the lockfile of `install.package_manager` (`uv.lock`, `Cargo.lock`).

v2 candidates:

- Source-tree Merkle root (single hash covering every file at registration time).
- Per-asset seals when `install.assets` (§6.2) is declared.

The package-manager-lockfile delegation in v1 was chosen because it costs zero protocol surface, reuses the existing audit signal of the runtime ecosystem, and is sufficient for the threat model the catalog enforces (post-publish tamper detection). It is not sufficient for adversarial supply-chain attacks against the lockfile itself; v2's Merkle option exists for that scenario.

### 6.2 Platform Compatibility & Pre-Built Binaries

v1 is platform-agnostic — the catalog layer does not branch on OS or architecture, and every host receives the same manifest.

v2 candidates:

- `platform_compatibility`: array of `os-arch` strings (e.g. `["linux-x86_64", "darwin-aarch64"]`); empty / `["*"]` keeps the v1 platform-agnostic default.
- `install.assets`: map keyed by `os-arch` to `{ url, sha256 }`, alongside the existing `install.source`.
- Per-asset seal hatch: an `asset_label` column on the catalog's `seals` table (NULL meaning "manifest seal", non-NULL meaning a specific asset). Schema is reserved server-side in the Phase 5b implementation but unused in v1.

The v1 stance is "if you cannot run the source on this platform, declare a stricter `host_compatibility` and ship a separate connector". This is sufficient for the current corpus of Python and pure-Rust connectors. The v2 hatch exists for connectors that ship platform-specific binaries (e.g. VOICEVOX-bound, native UI shims).

## 7. Validation

A connector manifest is **wire-valid** when it parses against the JSON Schema. It is **catalog-valid** when, additionally, the SDK's `validate_v1` returns `Ok(())`. The schema covers the structural envelope (required fields, types, regex shapes, enum sets). The SDK covers cross-field rules (`spec_version = 1`, `connector_type = "mgp_server"`, `magic_seal` shape, source-specific URL parsing, runtime ↔ binary-name compatibility hints, etc.).

Catalog implementations SHOULD run both. Editors and CI tooling that consume only JSON Schema get the structural layer for free.

The error vocabulary of the SDK is `mgp_sdk::ValidationError`; the variant set is itself part of the stable contract because tooling matches on it.

## 8. Compatibility Window

v1 will remain the only published version until the v2 hatches in §6 land. While v1 is the only version, third parties can rely on:

- The `$id` URL of the schema staying stable.
- Required fields and their types staying frozen.
- The `SourceSpec` variant set being non-shrinking (additions are allowed, removals are not).
- The `mgp_sdk` major version staying at 0.1.x for the lifetime of v1.

v2 will be introduced under a new `$id` (`https://cloto.dev/schemas/connector/v2.json`), and v1 will be supported in parallel for at least one MGP minor release.

## 9. Layered Manifest Provisioning

Writing a full `cloto-connector.json` (§3–§5) by hand is the most explicit way to register a connector, but it is heavyweight: every server author must author and maintain a complete manifest. For a monorepo of many servers this multiplies the authoring cost.

Layered Manifest Provisioning lets a catalog **synthesize** a v1 `ConnectorManifest` from progressively cheaper sources, so that a connector can be registered with as little as a few lines of project metadata — while preserving the hand-authored full manifest as an escape hatch. It defines four provisioning layers and a deterministic precedence between them.

The layers describe **where manifest fields come from**, not a new wire format. The result of merging the layers is an ordinary v1 `ConnectorManifest` that validates against §3–§5 and `schemas/connector/v1.json`. A catalog MAY implement only a subset of the layers; an implementation that synthesizes a manifest MUST validate the merged result with the same rules as a hand-authored one (§7).

### 9.1 The Four Layers

| Layer | Source | Cost | Status |
|---|---|---|---|
| **Layer 0** — Zero-touch | The project's own packaging metadata: `pyproject.toml` `[project]` (`name`, `description`, `version`). | none | v1 (`[project]` fields). Inspecting `server.py` / entry-module ASTs to infer tools or capabilities is reserved for a future revision. |
| **Layer 1** — Hint | A `[tool.cloto.mgp]` table in `pyproject.toml` (§9.3). | ~10 lines | v1 |
| **Layer 2** — Explicit override | Fields supplied out-of-band at registration time (e.g. a catalog registration/import request). | per-field | v1 |
| **Layer 3** — Full manifest | A complete `cloto-connector.json` committed to the source tree (§3–§5). | full | v1 |

Layer 0 and Layer 1 live **in the connector's repository** (server-side, versioned with the code). Layer 2 is **registration-time** input (catalog-side, not committed). Layer 3 is the pre-existing full-manifest path and remains fully supported for backward compatibility.

### 9.2 Precedence

When more than one layer supplies the same field, the **more explicit layer wins**:

```
Layer 3  >  Layer 2  >  Layer 1  >  Layer 0
(full)      (override)  (hint)      (zero-touch)
```

- A present Layer 3 manifest is authoritative and bypasses synthesis entirely — Layers 0–2 are ignored for any field the full manifest already carries. (A catalog MAY still consult Layer 2 for registration-only concerns that are not manifest fields, e.g. the source URL.)
- Absent Layer 3, the catalog synthesizes the manifest field-by-field, taking each field from the highest-precedence layer that provides it and falling through toward Layer 0.
- `magic_seal` is never authored across Layers 0–2; for a synthesized manifest the catalog computes the entry-file SHA-256 from the fetched source at registration time (§3.2, MGP_SECURITY.md §8). A Layer 3 manifest MAY carry a pre-computed `magic_seal`, but the catalog SHOULD recompute it from the fetched bytes and reject a mismatch.

### 9.3 `[tool.cloto.mgp]` (Layer 1)

A Python connector MAY advertise catalog metadata through a `[tool.cloto.mgp]` table in its `pyproject.toml`, following the PEP 518 `[tool.*]` convention. The table is **advisory hint** data: a catalog reads it to fill manifest fields the project's `[project]` block cannot express (category, trust posture, icon, environment contract, …).

All keys are optional; a catalog falls back to Layer 0 (or its own defaults) for any key not present.

| Key | Type | Maps to | Notes |
|---|---|---|---|
| `name` | string | `name` | Human-readable display name. Defaults to `[project].name` (Layer 0) when absent. |
| `id` | string | `id` | kebab-case (§3). Defaults to `[project].name` with any `cloto-mcp-` prefix stripped. |
| `category` | string | `category` | Open vocabulary (§3). |
| `trust_level` | string | `trust_level` | One of `core`/`standard`/`experimental`/`untrusted`. A *request* only — the catalog still enforces Security Invariant 3 (§3.1). |
| `icon` | string | `icon` | UI hint. |
| `tags` | string[] | `tags` | |
| `host_compatibility` | string[] | `host_compatibility` | |
| `env_vars` | array of tables | `env_vars` | Each `{ name, default?, description? }` (§4 `EnvVarDef`). |
| `optional_env_vars` | array of tables | `optional_env_vars` | Same shape. |
| `auto_restart` | boolean | `auto_restart` | |
| `dependencies` | string[] | `install.dependencies` | Extra dependency identifiers the host resolves in addition to the source's own lockfile (§4 `InstallSpec`). For monorepo connectors this names shared sibling packages (e.g. `"common"`) the host must provision before launch. |
| `directory` | string | `install.directory` | Subdirectory inside the source tree (monorepo servers). |
| `required_mgp_version` | string | *(catalog metadata)* | Minimum MGP spec version this connector targets, e.g. `"0.7"`. The catalog records it for compatibility gating; it is not a `ConnectorManifest` field in v1. |

Fields not expressible in `[tool.cloto.mgp]` — notably `install.source` (where to fetch from) and the computed `magic_seal` — are supplied by Layer 2 at registration time and by the catalog respectively.

Example (`pyproject.toml`):

```toml
[project]
name = "cloto-mcp-cscheduler"
version = "0.4.0-alpha.4"
description = "Cloto MCP Server: CScheduler intentionality + scheduling with operations log and revert"

[tool.cloto.mgp]
id = "cscheduler"
category = "tool"
trust_level = "core"
icon = "calendar-clock"
tags = ["core", "scheduler", "intentionality"]
auto_restart = true
required_mgp_version = "0.7"
dependencies = ["common"]
directory = "servers/cscheduler"

[[tool.cloto.mgp.env_vars]]
name = "CSCHEDULER_DB_PATH"
description = "SQLite database path"
```

### 9.4 Registration Principals (informative)

Layered provisioning is **principal-agnostic**: the same synthesis applies regardless of who initiates registration. v1 catalogs (ClotoHub.dev) gate registration to human administrators authenticated through the platform session. A future revision MAY accept a machine identity (an automated agent presenting an API token) on the same import path, so that an agent can register or update a connector on its own behalf; the synthesis rules above do not change. Wiring machine-identity authentication is out of scope for v1 and is tracked separately by the catalog implementation.

### 9.5 Authority

`schemas/connector/v1.json` remains the normative schema for the **output** `cloto-connector.json`. `[tool.cloto.mgp]` is an **input convention**, not part of the connector manifest wire format; its reference parser lives in the catalog / SDK implementations (`mgp-rs` for ClotoHub.dev's Rust catalog; a Python reader MAY be added to `mgp-py` for server-side tooling). Because Layer 1 only ever *feeds* fields that already exist in §3–§4, adding `[tool.cloto.mgp]` requires no change to the v1 connector schema `$id`.
