# ADR: Thin Frontends, Smart Backend

## Status

Accepted (2026-07-10)

## Context

The system has multiple frontends today and will gain more over time:

- **pedalboard-cli** — terminal interface
- **pedalboard-sim** — web UI (TUI + browser)
- **MOD UI** — plugin chain designer (browser)
- Future: mobile app, desktop app, Electron, custom web UI, third-party tools

Each frontend is a different presentation layer. If business logic (validation, compilation, default generation, protocol encoding) lives in the frontend, it gets duplicated every time a new UI appears. Bugs get fixed in one frontend but not another. Behavior diverges.

## Decision

**Frontends are thin — they handle presentation and user interaction only. All logic lives in shared backend code (crates, bridge, protocol).**

### What belongs in the frontend

- User input (buttons, forms, CLI args)
- Display (rendering, formatting, layout)
- Transport (WebSocket connection, HTTP calls)
- Local UX state (which tab is open, cursor position)

### What does NOT belong in the frontend

- **Validation** — schema validation, range checks, reference resolution → shared crate or compile tool
- **Protocol encoding** — PE SysEx framing, binary encoding → `midi-controller` crate
- **Default generation** — auto-generated buttons, CC allocation → compile tool
- **Audio config resolution** — snapshot merging, expression routing → bridge
- **State management** — what's the current preset, which snapshot is active → bridge/firmware report it

### Architecture

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  CLI (thin) │  │  Sim (thin) │  │ Future App  │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────────────────────────────────────────┐
│            Shared logic layer                    │
│  • midi-controller crate (protocol, types)      │
│  • pedalboard-config (schema, validation)       │
│  • compile tool (default generation, CC alloc)  │
│  • bridge (audio state, runtime control)        │
└─────────────────────────────────────────────────┘
       │                 │
       ▼                 ▼
┌────────────┐    ┌─────────────┐
│  Firmware  │    │  mod-host   │
└────────────┘    └─────────────┘
```

### Practical implications

1. **CLI doesn't encode presets** — it calls `midi-controller` crate's encoding functions. A future web UI uses the same crate (via WASM or bridge API).

2. **Sim doesn't validate config** — it sends YAML to the compile tool/bridge and gets back errors or success. Same validation logic regardless of which UI invoked it.

3. **No frontend knows about mod-host** — they send snapshot names to the bridge, bridge translates to TCP commands. If mod-host is replaced with something else, only the bridge changes.

4. **Bridge exposes state, not raw data** — frontends ask "what's the active snapshot?" not "what was the last param_set sent to instance 3." The bridge is the source of truth for runtime state.

5. **New frontend = new presentation only** — adding a mobile app means writing UI code that talks to the same WebSocket API. Zero new business logic.

## Consequences

- **Pro**: New frontends are cheap to build (just UI + WebSocket)
- **Pro**: Bug fixes in shared logic propagate to all frontends automatically
- **Pro**: Testing is concentrated (test the crate/bridge, not each UI)
- **Pro**: Third-party tools can use the same APIs without reimplementing logic
- **Con**: Frontends depend on shared crates — version coordination needed
- **Con**: Bridge becomes more important (single point of failure for runtime)
- **Con**: Some UX latency for operations that could be validated locally (mitigated by client-side schema validation for immediate feedback)

## Guideline

When implementing a new feature, ask: **"If someone builds a different UI tomorrow, would they need to rewrite this logic?"**

If yes → it belongs in a shared crate or the bridge, not the frontend.
