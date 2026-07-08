# Architecture: Where Logic Lives

## Principle

**If it's testable without hardware, it belongs in the protocol crate.**

The protocol crate is the product's brain. The firmware is just its hands.

## Layer Responsibilities

```
┌─────────────────────────────────────────────────────┐
│  pedalboard-protocol (the "midi-controller" crate)  │
│                                                     │
│  All behavior:                                      │
│  • Button logic (toggle, momentary, radio group)    │
│  • Long-press detection                            │
│  • Encoder acceleration                            │
│  • Tap tempo                                       │
│  • Preset state management                         │
│  • Preset switching (on_enter, on_exit, recall)    │
│  • MIDI generation (CC, NoteOn, PC, SysEx)         │
│  • Incoming MIDI trigger processing                │
│                                                     │
│  API: process(event, timestamp, config) → output    │
├─────────────────────────────────────────────────────┤
│  pedalboard-midi (firmware)                         │
│                                                     │
│  Hardware I/O only:                                 │
│  • GPIO → Event mapping                            │
│  • MIDI bytes → USB/UART output                    │
│  • LED ring rendering (RGB animations)             │
│  • EEPROM persistence                              │
│  • Display drawing                                 │
├─────────────────────────────────────────────────────┤
│  pedalboard-sim (simulator)                         │
│                                                     │
│  Alternative I/O:                                   │
│  • Keyboard/WebSocket → Event mapping              │
│  • Virtual MIDI port output                        │
│  • Browser UI (state visualization)                │
└─────────────────────────────────────────────────────┘
```

## Decision Test

When adding a feature, ask:

1. **Does it need GPIO, USB, or specific hardware?** → Firmware
2. **Is it behavior that should work identically in the simulator?** → Protocol crate
3. **Is it about displaying state to the user?** → Frontend (firmware display, web UI, TUI)

## What This Means in Practice

- The firmware's `pe_handler.rs` is a thin adapter (~400 lines). It maps hardware events to abstract `Event` values and converts `Output` MIDI back to raw bytes.
- The simulator uses the exact same `Controller` as the firmware. If it works in the sim, it works on hardware.
- Adding a new button mode or encoder behavior means changing only the protocol crate. All frontends get it for free.
- All timing-sensitive behavior is tested with deterministic timestamps — no hardware-in-the-loop needed.

## API Summary

```rust
let result = controller.process(event, now_ms, &config);
// result.midi      → send these bytes out
// result.leds_changed  → re-render LED rings
// result.preset_changed → update display
// result.bpm       → new tempo detected
```

That's it. One call, one result, no orchestration.
