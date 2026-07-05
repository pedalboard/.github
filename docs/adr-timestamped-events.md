# ADR: Timestamped Events and Protocol-Layer Timing

## Status

Proposed (2026-07-05)

## Context

The system has three time-dependent behaviors:

1. **Long press detection** — distinguish short press (<500ms) from long press (≥500ms)
2. **Encoder acceleration** — faster turning = larger steps (interval between detents → step multiplier)
3. **Tap tempo** — measure intervals between button presses to compute BPM

Currently, all timing logic lives in the firmware adapter layer (`pe_handler.rs`):
- `LongPressDetector` tracks per-button hold duration via a tick counter
- Encoder acceleration uses `last_encoder_tick` timestamps per encoder
- Tap tempo (new) would add another timing struct here

The protocol engine (`engine.rs`) is pure and stateless — it receives abstract events (`ButtonEvent::Press`, `EncoderDirection::Clockwise`) with no timing information and returns results. This means:
- Timing behavior is **untestable** at the protocol level
- The firmware adapter contains **business logic** (when does a long press fire? what's the acceleration curve?)
- A future **web UI simulator** would need to reimplement all timing logic
- The "thin adapter" principle is violated — `pe_handler.rs` is 600+ lines

## Decision Options

### Option A: Timestamps on events (engine receives time)

```rust
// Protocol crate
pub struct Controller {
    state_store: PresetStateStore,
    long_press: [LongPressDetector; 6],
    encoder_accel: [EncoderAccel; 2],
    tap_tempo: TapTempo,
}

impl Controller {
    pub fn process(&mut self, event: InputEvent, now_ms: u32, preset: &Preset) -> ControllerResult;
}
```

The engine receives a monotonic timestamp with each event. All timing decisions happen in the protocol crate.

**Pros:**
- All behavior testable with deterministic timestamps (no mocking)
- Single source of truth for timing thresholds (500ms long press, 2s tap timeout)
- Web UI / simulator gets identical behavior for free
- `pe_handler.rs` becomes trivially thin (GPIO → InputEvent + timestamp)
- Timing-sensitive bugs are reproducible in unit tests

**Cons:**
- Engine becomes stateful (owns long press, acceleration, tap tempo state)
- Larger protocol crate surface area
- Requires refactoring existing firmware code

### Option B: Keep timing in firmware adapter (status quo)

The engine stays pure and stateless. `pe_handler.rs` handles all timing. New features (tap tempo) add more state there.

**Pros:**
- No refactor needed
- Engine remains simple
- Working code stays untouched

**Cons:**
- Business logic in firmware (hard to test without hardware)
- Timing behavior duplicated if web UI needs it
- `pe_handler.rs` grows unbounded
- Tap tempo, long press, acceleration logic not covered by protocol tests

### Option C: Hybrid — timing structs in protocol, called by firmware

Timing state machines (TapTempo, LongPressDetector) live in the protocol crate as standalone structs, but the firmware orchestrates them. The engine itself doesn't own them.

```rust
// Protocol crate — standalone, testable
pub struct TapTempo { ... }
pub struct LongPressDetector { ... }

// Firmware — orchestrates
let gesture = long_press[i].update(edge, now_ms);
let bpm = tap_tempo.tap(now_ms);
let result = engine::process_button(&mut state, preset, i, gesture_to_event(gesture));
```

**Pros:**
- Timing logic is testable in protocol (individual struct tests)
- No big refactor — move structs one at a time
- Engine stays stateless
- Incremental migration path

**Cons:**
- Orchestration logic still in firmware (which struct to call when, in what order)
- A web UI would still need to replicate the orchestration
- Not a single entry point — multiple structs to coordinate

## Recommendation

**Option A** for the long term — it's the right architecture for a multi-tool platform (CLI, web UI, simulator all share identical behavior).

**Option C** as the migration path — move structs incrementally from firmware to protocol, each independently testable. Once all timing structs are in protocol, unify them into a `Controller` (completing Option A).

**Immediate next step (Option C):**
- `TapTempo` already in protocol ✅
- `LongPressDetector` already in firmware's `long_press.rs` — move to protocol (it's already pure, just needs relocating)
- Encoder acceleration — extract from `pe_handler.rs` into protocol struct

**Future step (Option A):**
- Unify into `Controller` struct with `process(event, now_ms, preset)` API
- Slim `pe_handler.rs` to pure I/O mapping

## Consequences

- Protocol crate grows to include all input processing logic (appropriate — it's the "business logic" crate)
- Firmware adapter shrinks to hardware I/O only
- All timing-sensitive behavior becomes deterministically testable
- Future tools get identical behavior without reimplementation
- `InputEvent` may need a `now_ms` field or the controller API accepts it as a parameter
