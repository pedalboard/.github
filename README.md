# Open Pedalboard

Open source guitar pedalboard — MIDI foot controller + neural amp modeling in one unit.

**€200 in parts. Fully FOSS. No compromises.**

## What is it?

A modular guitar effects platform built around:
- **RP2040** — 6 foot switches with RGB LED rings, 2 encoders, 2 expression pedals, 2 OLEDs, DIN + USB MIDI
- **Raspberry Pi CM5** — neural amp modeling (AIDA-X), LV2 effects, 1.3ms latency at 48kHz
- **Configuration as code** — YAML setlists, version-controlled, deployed with one command

Design your rig in a browser, deploy to hardware, perform without surprises.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Dev Machine                                                  │
│   pedalboard-cli (upload presets, flash firmware)            │
│   pedalboard-sim (virtual pedalboard in browser)            │
└────────────────────────┬────────────────────────────────────┘
                         │ WebSocket
┌────────────────────────▼────────────────────────────────────┐
│ CM5 (Raspberry Pi)                                           │
│   pedalboard-bridge (Rust: MIDI routing + audio switching)   │
│   mod-host (LV2 plugin host) + AIDA-X (amp modeling)        │
│   JACK Audio (48kHz, 64 frames, 1.3ms latency)              │
└────────────────────────┬────────────────────────────────────┘
                         │ USB MIDI
┌────────────────────────▼────────────────────────────────────┐
│ RP2040 (Firmware)                                            │
│   pedalboard-midi (Rust/RTIC: buttons, LEDs, encoders, PE)   │
│   midi-controller (protocol engine, no_std library)          │
└──────────────────────────────────────────────────────────────┘
```

## Repositories

| Repo | Language | Purpose |
|------|----------|---------|
| [pedalboard-hw](https://github.com/pedalboard/pedalboard-hw) | KiCad 9 | Main board: RP2040 + CM5 carrier |
| [pedalboard-midi](https://github.com/pedalboard/pedalboard-midi) | Rust (RTIC) | RP2040 firmware |
| [midi-controller](https://github.com/pedalboard/midi-controller) | Rust (`no_std`) | MIDI controller engine (library) |
| [pedalboard-bridge](https://github.com/pedalboard/pedalboard-bridge) | Rust | WebSocket↔MIDI bridge + audio engine |
| [pedalboard-cli](https://github.com/pedalboard/pedalboard-cli) | Rust | Config upload, flash, monitor |
| [pedalboard-sim](https://github.com/pedalboard/pedalboard-sim) | Rust | Virtual pedalboard simulator |
| [pedalboard-os](https://github.com/pedalboard/pedalboard-os) | Docker/Make | CM5 system config (JACK + services) |
| [pedalboard-soundcard](https://github.com/pedalboard/pedalboard-soundcard) | KiCad 9 | I²S audio codec (PCM1863 + PCM5242) |
| [pedalboard-display](https://github.com/pedalboard/pedalboard-display) | KiCad 9 | Display daughter board |
| [pedalboard-led-ring](https://github.com/pedalboard/pedalboard-led-ring) | KiCad 9 | RGB LED ring per foot button |
| [pedalboard-case](https://github.com/pedalboard/pedalboard-case) | OpenSCAD | 3D printable enclosure |

## Key Features

- **Instant tone switching** — all amp models pre-loaded, snapshots toggle bypass/params (<1ms)
- **Neural amp modeling** — AIDA-X with community-trained models (3.4% CPU per instance)
- **Per-snapshot expression pedals** — same pedal controls different parameters per tone (like Helix/Kemper)
- **12 RGB LEDs per button** — animations, heatmaps, reactive CC visualization
- **MIDI clock + tap tempo** — sync your looper and delay
- **Config as code** — YAML setlists in git, compile once, perform reliably (ADR-004)

## Design Principles

- **If it uploads, it works** — compiled setlist is validated before deploy, no runtime surprises ([ADR-004](docs/adr/004-compiled-setlist.md))
- **Audio-first configuration** — define your rig, controller adapts automatically ([ADR-005](docs/adr/005-audio-first-configuration.md))
- **Thin frontends, smart backend** — business logic lives in shared crates, not in UIs ([ADR-006](docs/adr/006-thin-frontends.md))

## Compared to

| | Open Pedalboard | MOD Dwarf (€499) | Morningstar MC6 (€450) |
|---|---|---|---|
| Audio processing | ✅ AIDA-X + LV2 | ✅ mod-host + LV2 | ❌ |
| LED rings (12 RGB) | ✅ per button | ❌ | 1 LED per button |
| Open hardware | ✅ CERN-OHL-P | ❌ | ❌ |
| Open software | ✅ GPL | Partial | ❌ |
| Config as code | ✅ YAML + git | ❌ | ❌ |
| Price (kit) | ~€200 | €499 | €450 |

## License

- Hardware: CERN Open Hardware License - Permissive v2
- Software/firmware: GPL
- OSHWA certified: CH000023

## Documentation

- [Software Architecture](docs/software-architecture.md)
- [Audio Integration](docs/audio-integration.md)
- [Hardware Architecture](docs/hardware-architecture.md)
- [Architecture Decision Records](docs/adr/)
