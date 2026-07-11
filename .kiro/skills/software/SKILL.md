---
name: software
description: Firmware (Rust/RTIC on RP2040), PE protocol, bridge (Rust on CM5), CLI, flash persistence, and stack constraints. Use when working on firmware, protocol, bridge, CLI, or debugging embedded software.
---

# Software Knowledge

> Architecture details: `dotgithub/docs/software-architecture.md` (cross-module), `pedalboard-midi/docs/architecture.md` (firmware)
> Unsafe policy: `pedalboard-midi/docs/adr/002-unsafe-code-policy.md`

## Architectural Principles (MUST follow)

### ADR-003: Controller Owns Routing

ALL MIDI logic and routing decisions belong in the `midi-controller` crate:
- Input event processing (buttons → CC, encoders → CC, expression → CC)
- Output port routing (which messages go to DIN, USB, BLE)
- Thru routing (incoming DIN→USB, USB→DIN)
- Output filtering (internal channel → USB only, future per-message rules)
- Reactive LED triggers from incoming CC
- Preset switching, state management, tap tempo

The firmware (`pedalboard-midi`) is a **pure I/O adapter**:
- Feed hardware events into `Controller::process()`
- Dispatch `Output.midi` to physical ports by reading `msg.dest` port flags
- Never make routing decisions — just obey the Controller's output

When implementing any MIDI-related feature, put the logic in `midi-controller`, not in firmware or CLI.

### ADR-006: Thin Frontends, Smart Backend

Frontends (CLI, sim, future apps) are **presentation only**. All logic lives in shared crates:

| Belongs in shared code | Does NOT belong in frontend |
|------------------------|-----------------------------|
| Validation | ❌ CLI validates |
| Protocol encoding (PE) | ❌ CLI builds SysEx |
| Default generation | ❌ CLI generates buttons |
| Audio config resolution | ❌ CLI resolves snapshots |
| CC allocation | ❌ CLI picks CC numbers |

Shared logic lives in:
- `midi-controller` — protocol, types, routing, controller engine
- `pedalboard-config` — schema, YAML parsing, validation, compilation
- `pedalboard-bridge` — audio state, runtime control, mod-host abstraction

Test: *"If someone builds a different UI, would they rewrite this?"* → put it in a shared crate.

### Consequence for new features

1. **New MIDI behavior** → `midi-controller` crate (unit tested, no_std)
2. **New config field** → `midi-controller` (binary) + `pedalboard-config` (YAML) + schema regeneration
3. **New compile/generation logic** → `pedalboard-config` crate (not CLI directly)
4. **New runtime behavior** → bridge (audio) or firmware (I/O dispatch)
5. **New UI command** → CLI calls into shared crates, formats output

## Stack and Memory Constraints (RP2040)

- `Preset` = 1.4KB in memory, ~130 bytes serialized. `Config` = 45KB (32 presets).
- **Never return/hold a `Preset` across an await point** — inflates async state machine → stack overflow
- **Never allocate `Config` or `Preset` as locals** — use statics only
- Stack overflow only manifests when code paths are exercised — test with real data
- Presets loaded async in `persist` task (callback pattern avoids returning large structs)
- PE Get replies serialize from `pe_config` RAM via static buffer (no flash read in ISR)
- USB_OUT_CAPACITY = 64 packets (PE Get Reply needs ~51)

## RTIC / Embedded Patterns

- `or_else` on `Option` short-circuits — don't use for polling multiple inputs; use `heapless::Vec`
- `Mono::delay().await` in loop is less precise than `spawn_after`
- USB send task must loop waiting for configured state, not return early
- `defmt` feature removed from protocol dep to allow host-side testing
- Host tests: `cargo test --lib --target x86_64-unknown-linux-gnu`

## Encoders

- `rotary-encoder-embedded` **pin to v0.3.1** — v0.5.0 breaks detection
- Set `pulses_per_step=1` (default 4 requires 4 detent clicks per message)
- Both encoders MUST have unique MIDI IDs (they default to matching index)

## Bridge (summary)

- Rust (tokio + axum + jack-rs) WebSocket↔MIDI on CM5. Restart bridge if it misses re-enumeration after probe reset.

## Firmware Gotcha

- Factory reset now reboots automatically (1s delay for USB flush before sys_reset)
- `--wait` flag on CLI reboot/reset polls for device readiness (two-phase: offline → online + 2s settle)


## Cross-Repo Development Workflow

### Commands (`pedalboard-midi`)

- Build: `make build` — Lint: `make lint` — Run (probe): `make run`
- Flash: `make flash` (UF2 via bridge) or `make flash-probe` (SWD local)
- Integration test: `cd pedalboard-cli && ./tests/integration.sh` (run before pushing firmware/protocol)

### Local deps

- **Never modify `Cargo.toml` `[patch]` sections** — Makefile `PATCHES` var handles `--config` flags
- Host tests with local protocol: use `PROTOCOL_PATCH` from Makefile

### Push order (both repos changed)

1. Push `midi-controller` first
2. `cargo update` in `pedalboard-midi` (clear `~/.cargo/git/db/midi-controller-*` if stale)
3. Verify `Cargo.lock` has new commit hash, then push `pedalboard-midi`

### Pre-commit hooks

- `fmt`, `clippy`, `check` use remote protocol (must be pushed first)
- `host-tests` uses local protocol via `--config` patch

### Protocol-first rule

- Business logic in `midi-controller` (pure, `#![no_std]`, testable without hardware)
- `pe_handler.rs` is a thin hardware adapter only
- **When extending the protocol**, follow `midi-controller/CONTRIBUTING.md` (checklist: protocol → CLI → firmware, docs locations, push order)

