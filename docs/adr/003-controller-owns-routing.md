# ADR: Controller Owns MIDI Routing

## Status

Accepted (2026-07-09) — Design agreed, implementation pending (issue midi-controller#12).

## Context

MIDI routing decisions are currently scattered across 3 firmware tasks:

- **`midi_in`** (DIN IRQ): reads DIN MIDI, forwards to USB if `din_to_usb_thru`, flashes Mon LED, feeds reactive LEDs
- **`usb_rx`** (USB IRQ): reads USB MIDI, forwards to DIN if `usb_to_din_thru`, flashes Mon LED, feeds reactive LEDs
- **`poll_input`** (periodic): generates MIDI from button/encoder actions, sends to USB+DIN based on `din_enabled`

Each task independently:
- Checks thru routing config
- Flashes the Mon LED
- Calls `reactive_led_event()` for LED ring updates
- Decides which port(s) to send on

This causes:
- Mon LED flashed from 3 places (inconsistent flash behavior)
- Thru routing logic duplicated (can't easily make it per-preset)
- Adding a new port (BLE) requires touching all 3 tasks
- Reactive LED processing in 3 call sites (already deduplicated to a helper, but still called from 3 places)
- No way to test routing decisions without hardware

## Decision

The `midi-controller` crate's `Controller` takes ownership of all MIDI routing. The firmware becomes a pure I/O adapter: it feeds events in and dispatches outputs.

### Port model

Ports are a bitmask, extensible without API change:

```rust
bitflags! {
    pub struct MidiPort: u8 {
        const DIN = 0x01;
        const USB = 0x02;
        const BLE = 0x04;
    }
}
```

Adding a port (BLE, JACK, wireless) is one new bit. Routing rules are port masks — no enums to extend.

### Event input

```rust
pub enum Event {
    ButtonEdge { index: u8, edge: Edge },
    EncoderTurn { index: u8, clockwise: bool },
    Analog { index: u8, raw: u16 },
    Midi { data: [u8; 8], len: u8, source: MidiPort },
    Tick,
}
```

All incoming MIDI (from any port) flows through `Event::Midi`. The controller sees the source port and decides what to do: update reactive LEDs, process triggers, compute thru routing.

### Output

```rust
pub struct Output {
    pub midi: Vec<MidiOut, 32>,
    pub leds_changed: bool,
    pub mon_led: Option<Rgb>,
    pub mode_led: Option<Rgb>,
    pub display: Vec<DisplayEvent, 2>,
    pub state_dirty: bool,
    pub preset_changed: bool,
    pub bpm: Option<u16>,
}

pub struct MidiOut {
    pub data: [u8; 8],
    pub len: u8,
    pub dest: MidiPort,  // bitmask: which ports to send on
}
```

The firmware dispatches `Output.midi` by checking port bits against hardware:

```rust
for msg in &output.midi {
    if msg.dest.contains(MidiPort::DIN) { uart_write(msg); }
    if msg.dest.contains(MidiPort::USB) { usb_send(msg); }
    if msg.dest.contains(MidiPort::BLE) { ble_send(msg); }
}
```

### Thru routing

Thru is a routing decision made by the controller when processing `Event::Midi`:

```rust
// Controller internal logic:
fn handle_incoming_midi(&mut self, data, source, config) {
    // Thru routing (configurable per-preset or global)
    let thru_mask = config.thru_mask(source);
    if !thru_mask.is_empty() {
        self.output.midi.push(MidiOut { data, len, dest: thru_mask });
    }
    // Reactive LEDs
    self.update_reactive_leds(data);
    // Mon LED
    self.output.mon_led = Some(BLUE);
    // Trigger processing
    self.check_triggers(data);
}
```

### SysEx / PE boundary

The controller does **not** handle SysEx. PE (Property Exchange) is a transport/protocol concern handled by the firmware's `pe_sysex` module. The split:

```
Incoming bytes
  ├─ SysEx (F0..F7) → pe_sysex → persist/config (firmware infrastructure)
  └─ Channel messages → controller.process(Event::Midi) (business logic)
```

This boundary is future-proof: if PE evolves (MIDI 2.0 UMP, CI negotiation, System Exclusive 8), the controller is unaffected.

### MIDI 2.0 path

The `data: [u8; 8]` field accommodates both MIDI 1.0 (3 bytes) and MIDI 2.0 UMP (4-8 bytes). The controller pattern-matches on message type internally. When the `midi2` crate matures (PE support, stable UMP types), the controller's internal parsing can switch to typed messages behind a feature flag — the external API stays unchanged.

## Consequences

- **Firmware shrinks**: `midi_in`, `usb_rx`, and `poll_input` become thin I/O adapters (~10 lines each for MIDI routing)
- **Per-preset thru routing**: trivial to implement (routing mask stored in preset config)
- **New ports**: adding BLE is one bit + one dispatch line in firmware, zero controller changes
- **Testable**: all routing decisions covered by unit tests with deterministic port masks
- **Simulator**: `pedalboard-sim` gets accurate MIDI routing behavior for free
- **Mon LED consistency**: one place flashes it, always correct
- **state_dirty flag**: firmware persists when told to, doesn't inspect internal state

## Migration path

1. Add `MidiPort` bitflags and `MidiOut` to `midi-controller`
2. Add `Event::Midi { data, len, source }` variant
3. Move thru routing into controller (process incoming → emit thru in output)
4. Move reactive LED triggering into controller (already just a function call)
5. Move Mon LED flash into controller output
6. Update firmware tasks to feed `Event::Midi` and dispatch `Output.midi` by port mask
7. Remove thru logic and Mon LED flashing from firmware tasks
8. Add `state_dirty` to output, replace firmware persist logic with flag check
