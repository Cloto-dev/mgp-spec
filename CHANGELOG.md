# Changelog

Version history for the MGP specification. Extracted from [MGP_GUIDE.md §18.1 Version History](docs/MGP_GUIDE.md#181-version-history).

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0-draft | 2026-02-27 | Initial draft — Security layer (§2-7) |
| 0.2.0-draft | 2026-02-27 | Communication & Lifecycle layer (§11-15) |
| 0.3.0-draft | 2026-02-27 | Intelligence layer — Dynamic Tool Discovery & Active Tool Request (§16) |
| 0.4.0-draft | 2026-02-28 | Expert review response (see §18.2) |
| 0.5.0-draft | 2026-02-28 | Selective Minimalism (see §18.3) |
| 0.5.1-draft | 2026-02-28 | Document consolidation: merged MGP_PATTERNS.md, MGP_ADOPTION.md, MGP_REVIEW_RESPONSE.md into single specification |
| 0.5.2-draft | 2026-02-28 | Second review response: sequential section numbering (§17-19), `notifications/mgp.event` added to Layer 2, kernel tool visibility rules (§16.8), §14 Layer classification, MCP comparison compressed |
| 0.6.0-draft | 2026-03-06 | Transport layer analysis (see §18.4) + structural audit & architectural revision (see §18.5) |
| 0.6.0-impl | 2026-03-07 | ClotoCore Tier 1-4 implementation complete: 21 kernel tools, 13 extensions, bug-182 to bug-226 fixed. New modules: `mcp_mgp.rs`, `mcp_lifecycle.rs`, `mcp_streaming.rs`, `mcp_events.rs`, `mcp_discovery.rs`, `mcp_tool_discovery.rs` |
| 0.6.1-draft | 2026-04-22 | §14.7 Tool Rejection Envelope — structured `CallToolResult.isError` body for policy/logic refusals distinct from JSON-RPC errors, 9-variant RejectionCode registry, server opt-in semantics, kernel agentic-loop break + mechanical final response contract, security hardening against rejection-text-driven privilege escalation |
| 0.6.3-draft | 2026-05-07 | Security Invariant 3 universalize — seal absence forces `untrusted` regardless of declared tier (previously specified for `core` only). §4.0 behavior table unified to "Force untrusted (allow startup)" for seal-missing cases except invalid seals. New audit event `TRUST_LEVEL_DOWNGRADED_NO_SEAL` (§6.4). |
| connector v1 schema | 2026-05-11 | Add [`schemas/connector/v1.json`](schemas/connector/v1.json) (`$id = https://cloto.dev/schemas/connector/v1.json`) and companion [`docs/MGP_CONNECTOR.md`](docs/MGP_CONNECTOR.md) formalizing `cloto-connector.json`. Reference implementation is the `mgp-sdk` crate (Cloto-dev/mgp-rs, tag `mgp-sdk-v0.1.2`); the v0.1.2 patch ships alongside this schema to align `validate::validate_v1`'s `magic_seal` format check with the schema's strict lowercase hex rule (previously the SDK accepted uppercase hex that could never verify). Schema is additive to 0.6.3-draft and does not bump the MGP version. Multi-platform / per-asset binary seal hatches deferred to v2 (see MGP_CONNECTOR §6). |
| connector v1 schema (additive) | 2026-05-15 | Add `EnvVarDef.default` (string &#124; null, optional) to v1 — defaulted values the host SHOULD inject when the operator has not supplied one. Document SDK-side `key` deserialization alias on `EnvVarDef.name` for migration from pre-v1 registries (e.g. legacy `cloto-mcp-servers/registry.json`); the alias is implementation leniency only and is not a spec-level synonym. `$id` unchanged — v1 stays compatible because every change is additive (new optional field; new SDK behavior, not new schema rule). Companion `docs/MGP_CONNECTOR.md` §4 EnvVarDef table updated. Driven by the `mgp-sdk` v0.1.2 → v0.2.0 work that lets ClotoCore replace its bespoke `RegistryEntry` / `EnvVarDef` definitions with `pub use mgp_sdk::shape::*` (Goal #36 connector source-aware install cutover). |
| 0.7.0-draft | 2026-05-31 | §9 Layered Manifest Provisioning ([`docs/MGP_CONNECTOR.md`](docs/MGP_CONNECTOR.md)): four provisioning layers (0 zero-touch `pyproject [project]` / 1 `[tool.cloto.mgp]` hint / 2 registration-time override / 3 full `cloto-connector.json`) with deterministic precedence 3 > 2 > 1 > 0, so a catalog can synthesize a v1 `ConnectorManifest` from minimal project metadata. Adds the `[tool.cloto.mgp]` pyproject table (Layer 1 hint) — an input convention, additive to the connector v1 schema (`$id` unchanged), not a wire-format change. Minor bump per §2.5. |

## Migration to mgp-spec repo

Prior to 2026-05-07, the MGP specification was maintained inside [`Cloto-dev/cloto-mcp-servers/docs/`](https://github.com/Cloto-dev/cloto-mcp-servers/tree/main/docs). The specification has been extracted into this independent repository (`Cloto-dev/mgp-spec`) under MIT license, fulfilling the planned "License and Distribution Strategy" described in [MGP_GUIDE.md §17.4](docs/MGP_GUIDE.md#174-license-and-distribution-strategy). The 6 specification documents migrated to this repo retain their original content; the only changes are:

- Child documents (`MGP_SECURITY.md`, `MGP_COMMUNICATION.md`, `MGP_DISCOVERY.md`, `MGP_GUIDE.md`) version header bumped from `v0.6.0-draft, 2026-03-06` to `v0.6.1-draft, 2026-04-22` (sanity-aligned with main `MGP_SPEC.md`)
- Cross-document URLs converted from absolute `cloto-mcp-servers/blob/main/docs/...` paths to relative paths (`MGP_*.md`)

The historical record in `MGP_GUIDE.md §17.10 Roadmap` (which lists `v0.6.0-draft` as the Phase 0 deliverable) is preserved unchanged because it documents the original draft state, not the current spec version.
