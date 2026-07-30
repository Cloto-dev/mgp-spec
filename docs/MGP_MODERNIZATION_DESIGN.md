# MGP Modernization Design — Adapting to MCP 2026-07-28 (Stateless Core)

**Status**: draft proposal — not yet part of the specification. Target version: open question (§8.1).
**Date**: 2026-07-30
**Inputs**: MCP 2026-07-28 changelog and versioning/discovery pages (primary sources, read 2026-07-30);
MCP python SDK 2.0.0 measurements (Cloto-dev/claude-ops `docs/mcp-python-sdk-v2-spike-20260730.md`).

---

## 1. Background

The MCP 2026-07-28 revision ("stateless core") is the largest protocol revision since launch:

- The `initialize` / `notifications/initialized` handshake and protocol-level sessions
  (`Mcp-Session-Id`) are **removed**. Every request carries its protocol version and client
  capabilities in `_meta`.
- `server/discover` is **mandatory** for servers; it returns supported versions, capabilities,
  identity, and `instructions`.
- An **official extension mechanism** is introduced: `capabilities.extensions`, a map keyed by
  reverse-DNS extension identifiers, with specified negotiation-fallback semantics.
- Multi Round-Trip Requests (**MRTR**) replace server-initiated requests: results carry a required
  `resultType` (`"complete"` | `"input_required"`).
- The HTTP GET stream and `resources/subscribe` are replaced by `subscriptions/listen` with an
  enumerated set of subscription types. `ping`, `logging/setLevel`, and SSE resumability are removed.
- Roots, Sampling, and Logging are deprecated (minimum twelve-month window).

MCP's own compatibility terminology is adopted throughout this document: **legacy** era
(revisions ≤ 2025-11-25, handshake-based), **modern** era (2026-07-28 and later, per-request
metadata), **dual-era** (an implementation supporting both).

### 1.1 MGP anchors affected

| MGP section | Current anchor | Status under modern era |
|---|---|---|
| §2 Capability Negotiation | Piggybacks on the `initialize` handshake | Anchor removed — no activation path |
| §3 Permission Flow | Inserted between `initialize` response and `initialized` notification | Seam no longer exists |
| §12 Streaming | Custom methods/notifications on the session | Request-scoped flows survive; see §5 |
| §13 Bidirectional | Unsolicited server→client push | No channel on modern HTTP; see §5.2 |
| §6 Observability | MGP-specific fields | MCP now specifies OTel `_meta` conventions; see §6 |

### 1.2 What is NOT affected

- **The superset property.** Modern-era MCP messages are ordinary JSON-RPC; nothing in MGP
  rejects them. "Any valid MCP message is a valid MGP message" holds in both eras.
- **Graceful degradation.** A modern client that never activates MGP simply receives core MCP
  behavior. What is lost until this design lands is only the *activation* path in the modern era —
  a forward-compatibility gap, not a backward-compatibility break.
- **The kernel-tool layer.** `mgp.health.*`, `mgp.lifecycle.*`, `mgp.events.subscribe` are
  ordinary MCP tools and work unchanged in both eras.
- **The connector manifest and seal** (`cloto-connector.json`, `magic_seal`): transport-agnostic,
  unaffected.

## 2. Design principles

1. **Dual-era, legacy-first compatibility.** MGP MUST remain fully functional on the legacy era
   for at least MCP's own deprecation window. Modern-era support is additive; nothing in this
   design changes legacy behavior.
2. **From tolerated piggyback to the official seat.** MGP's capability declaration moves from
   unofficial fields on `initialize` (dependent on implementations silently ignoring unknown
   fields) to a registered extension under the official mechanism. Proposed identifier:
   **`dev.cloto/mgp`** (Cloto-dev already owns `cloto.dev`; schemas are published under
   `https://cloto.dev/schemas/`).
3. **No protocol-session state.** Modern-era MGP state (notably permission grants) is expressed
   per-request or through explicit server-minted handles passed as ordinary values — the same
   pattern the core spec prescribes for cross-call state (SEP-2567).

## 3. Capability declaration in the modern era

Replaces the §2 piggyback when the client speaks 2026-07-28+. Legacy path is unchanged.

- **Server → client**: the server advertises MGP in its `server/discover` result:

  ```json
  {
    "resultType": "complete",
    "supportedVersions": ["2026-07-28", "2025-11-25"],
    "capabilities": {
      "tools": {},
      "extensions": {
        "dev.cloto/mgp": {
          "version": "0.8.0",
          "extensions": ["permissions", "streaming"],
          "permissions_required": ["network.outbound"],
          "trust_level": "standard"
        }
      }
    }
  }
  ```

  The settings object carries exactly what the §2.3 initialize response carries today; field
  semantics are unchanged.
- **Client → server**: the client declares MGP support in the per-request
  `io.modelcontextprotocol/clientCapabilities`:

  ```json
  { "extensions": { "dev.cloto/mgp": { "version": "0.8.0" } } }
  ```

- **Fallback**: per the core extension-negotiation rules, if either party does not advertise
  `dev.cloto/mgp`, both revert to core protocol behavior. This is MGP's long-standing graceful
  degradation, now backed by specified semantics instead of tolerated unknown fields.

## 4. Permission Flow re-anchor (§3)

**Legacy (unchanged)**: the host gates between the `initialize` response (which names
`permissions_required`) and the `initialized` notification.

**Modern (proposed)** — two cooperating paths:

- **(a) Discover-driven upfront grant (primary).** The host calls `server/discover` before first
  use, reads `permissions_required` from the extension settings, and runs its grant flow (user
  consent, policy) before issuing the first tool call. This preserves the current host-driven UX
  (ClotoCore's Permission Flow) with `server/discover` taking the structural place of the
  handshake gap.
- **(b) MRTR enforcement backstop.** A server receiving a request that requires an ungranted
  permission returns `resultType: "input_required"` with an `inputRequests` entry describing the
  needed grant; the client retries with the grant attached. This gives servers a spec-native way
  to enforce rather than trust the client to have gated.

**Grant conveyance**: with no session to persist grants, the client attaches them per-request in
`_meta` under `dev.cloto/mgp/grants` — either the grant list itself or a server-minted grant
handle previously returned by the server. Servers MUST treat the absence of grant metadata as
ungranted (stateless default). On stdio, where the server process is dedicated to one client, a
server MAY cache grants for the process lifetime as an optimization; on modern HTTP it MUST NOT
assume cross-request memory unless a handle is presented.

## 5. Streaming (§12) and bidirectional communication (§13)

### 5.1 Request-scoped flows survive

Stream chunks, progress, and gap re-delivery are all correlated to an initiating request. In the
modern era they ride the response stream of that request (Streamable HTTP) or the pipe (stdio) —
matching the core rule that request-scoped notifications flow on the request's own stream.
`mgp/stream/cancel` is a client→server request and remains a registered vendor method.

*Informative — SDK reality*: python SDK 2.0 officially opens the receive side to vendor methods
(`add_request_handler` / `add_notification_handler`; unknown methods now return `-32601`), which
removes the need for receive-loop interception. Its typed send side is a closed union; on stdio an
implementation may write vendor notifications directly to the transport write stream, which is
legal on the wire — the protocol is JSON-RPC over the transport, not the SDK's type surface.

### 5.2 Unsolicited push is scoped to stdio + legacy era

Modern Streamable HTTP has exactly one server-initiated channel — `subscriptions/listen` — with an
enumerated, non-extensible set of subscription types. Until MCP allows vendor subscription types,
MGP's unsolicited push (§11.5 lifecycle notifications, §13.3 server push, §13.4 callbacks) is
**specified as available on stdio and on legacy-era HTTP only**. Hosts on modern HTTP obtain
equivalent signals by polling the corresponding kernel tools (`mgp.health.status`,
`mgp.events.*`). This is a documented limitation, revisited if the core protocol opens
`subscriptions/listen` to extensions.

## 6. Observability (§6) migrates to OTel conventions

MCP 2026-07-28 documents OpenTelemetry trace-context propagation in `_meta` (`traceparent`,
`tracestate`, `baggage`). This is the first activation of the §1.7 migration policy's
"Observability: Medium likelihood" row. Per the §1.7 commitment:

1. 0.8 provides a compatibility mapping (MGP observability fields ↔ OTel `_meta` keys) and
   supports both.
2. The MGP-specific fields are deprecated in 0.8 and removed no earlier than 0.9 (one minor
   version of overlap, as committed).

## 7. Compatibility matrix and validation

Era (client) × MGP support (server), assuming the server is dual-era MCP:

| Client | Server MGP | Outcome |
|---|---|---|
| Legacy, MGP-aware | yes | Full MGP via initialize piggyback (§2/§3 as today) |
| Legacy, plain MCP | yes | Core MCP; MGP dormant (degradation, as today) |
| Modern, MGP-aware | yes | Full MGP via `dev.cloto/mgp` extension (§3/§4 of this design) |
| Modern, plain MCP | yes | Core MCP; MGP dormant — **new capability delivered by this design** |

A modern-only server (no initialize) with a legacy MGP client fails at the MCP layer itself, as
specified by the core compatibility matrix — MGP adds nothing to that failure mode.

`mgp-validate` today validates connector manifests only. When lifecycle/protocol compliance checks
are added, they MUST cover both eras of the activation path (piggyback and extension).

## 8. Open questions (governance decisions)

1. **Version slotting.** Recommendation: dedicate **0.8.0** to this adaptation and move the
   previously planned Layer 4/5/6 work to 0.9.0. Rationale: the adaptation is externally driven
   (MCP's clock, ecosystem SDKs already shipped), while Layer 4/5/6 is internally paced.
   Alternative: bundle both into a larger 0.8.0.
2. **§1.7 amendment — base-revision tracking policy.** §1.7 today covers only "MCP adopts an
   MGP-equivalent feature". Add the inverse commitment: when MCP publishes a new protocol
   revision, MGP publishes an adaptation assessment (impact + plan, this document being the
   first instance) within one minor version. Wording to be drafted with the 0.8.0 changes.
3. **Grant handle format** (§4): opaque server-minted string vs. structured claim. Leaning
   opaque-string (server-defined, consistent with SEP-2567 handles); to be settled during
   reference implementation.

## 9. References

- MCP 2026-07-28 changelog: `modelcontextprotocol.io/specification/2026-07-28/changelog`
- Versioning & compatibility (era terminology, matrix):
  `modelcontextprotocol.io/specification/2026-07-28/basic/versioning`
- Discovery (`server/discover`, `DiscoverResult.instructions`):
  `modelcontextprotocol.io/specification/2026-07-28/server/discover`
- python SDK 2.0 spike verdict: Cloto-dev/claude-ops `docs/mcp-python-sdk-v2-spike-20260730.md`
- Reference-implementation counterpart: ClotoCore kernel dual-era client work (tracked separately)
