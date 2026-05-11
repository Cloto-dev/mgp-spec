# MGP — Multi-Agent Gateway Protocol

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-draft%20v0.6.1-orange.svg)](docs/MGP_SPEC.md)

> Strict superset of MCP (Model Context Protocol) that adds protocol-level security, access control, and observability while maintaining full backward compatibility. Any valid MCP message is a valid MGP message. Any MGP server can operate as a standard MCP server when connected to a client that does not support MGP extensions.

— [docs/MGP_SPEC.md §1.1](docs/MGP_SPEC.md)

## Documents

| File | Sections | Content |
|------|----------|---------|
| [docs/MGP_SPEC.md](docs/MGP_SPEC.md) | §1 | Overview, Architecture, Migration Policy |
| [docs/MGP_SECURITY.md](docs/MGP_SECURITY.md) | §2-§7 | Capability Negotiation, Permissions, Tool Security, Access Control, Audit, Code Safety |
| [docs/MGP_COMMUNICATION.md](docs/MGP_COMMUNICATION.md) | §11-§14 | Lifecycle, Streaming, Bidirectional Communication, Errors |
| [docs/MGP_DISCOVERY.md](docs/MGP_DISCOVERY.md) | §15-§16 | Discovery, Dynamic Tool Discovery |
| [docs/MGP_GUIDE.md](docs/MGP_GUIDE.md) | §17-§20 | Implementation, History, Patterns |
| [docs/MGP_ISOLATION_DESIGN.md](docs/MGP_ISOLATION_DESIGN.md) | (§8-§10 reserved) | OS-Level Isolation |
| [docs/MGP_CONNECTOR.md](docs/MGP_CONNECTOR.md) | — | Connector Manifest (`cloto-connector.json`) v1 — companion to [`schemas/connector/v1.json`](schemas/connector/v1.json) |

## Compliance Tiers

`mgp-validate` tests MGP compliance for servers and clients. Compliance badges:

`[MGP Tier 1]` `[MGP Tier 2]` `[MGP Tier 3]` `[MGP Tier 4]`

See [MGP_GUIDE.md §17.5 Staged Adoption Path](docs/MGP_GUIDE.md#175-staged-adoption-path) for tier definitions and [§17.8](docs/MGP_GUIDE.md#178-validation-tool--mgp-validate) for the validation tool.

## Reference Implementation

[ClotoCore](https://github.com/Cloto-dev/ClotoCore) is the reference implementation of MGP. See [MGP_GUIDE.md §17.3](docs/MGP_GUIDE.md#173-relationship-to-clotocore) for the mapping of MGP specification sections to ClotoCore source-code locations.

## Status

- Current draft: **v0.6.1-draft** (2026-04-22)
- See [CHANGELOG.md](CHANGELOG.md) for version history
- License: **MIT** — this specification (and future SDKs) is MIT-licensed independently from ClotoCore (see [MGP_GUIDE.md §17.4 License and Distribution Strategy](docs/MGP_GUIDE.md#174-license-and-distribution-strategy))

## Schemas

Machine-readable schemas live under [`schemas/`](schemas/). Each schema has a stable `$id` under `https://cloto.dev/schemas/`.

| Schema | `$id` | Companion doc |
|---|---|---|
| [`schemas/connector/v1.json`](schemas/connector/v1.json) | `https://cloto.dev/schemas/connector/v1.json` | [`docs/MGP_CONNECTOR.md`](docs/MGP_CONNECTOR.md) |

Additional schemas (isolation profile, audit event format, etc.) will be added as the ClotoHub integration roadmap advances.
