# Open Pedalboard Hardware and Software Platform

<img src="../img/pedalboard-logo-large.png" alt="Logo" width="600"/>

An open source MIDI foot controller and audio processing platform — the open
hardware alternative to Morningstar, built for guitarists who want full control
over their rig.

## What It Does

One board controls your entire setup: amp channel switching, multi-effect preset
recall, looper control, expression pedal routing — all from a single flat
pedalboard. Define your setlist as code, and every song gets its own button
layout, encoder assignments, and LED colors.

**Live on stage**: step through your setlist with preset next/prev, see active
effects at a glance via color-coded LED rings, control parameters with expression
pedals — all with instant startup and zero boot delay on the MIDI side.

**In the studio**: spin encoders to scroll presets and tweak parameters between
takes, hands-free editing without reaching for a mouse.

## Key Features

- **6 foot buttons** — momentary, toggle, radio group, long-press, multi-action sequences
- **12-LED RGB rings** per button — spatial patterns (fill, dots, single) + animations (pulse, blink, rotate) for at-a-glance state feedback
- **2 rotary encoders** — preset scrolling, parameter control, BPM adjust
- **2 expression pedal inputs** — continuous real-time control (wah, volume)
- **2 OLED displays** — button labels, encoder overlays, preset name
- **DIN + USB MIDI** — control any MIDI gear, bidirectional
- **MIDI Clock** — sync tempo with loopers and delay pedals
- **32 presets** with per-preset defaults, state recall across power cycles
- **Optional audio processing** — CM5 + ELK Audio OS for guitar effects (independent from MIDI controller)
- **30mm flat case** — sits under your foot, not on top of your pedalboard

## Design Goals

- Fully open source hardware and software ([CERN-OHL-P-2.0](https://ohwr.org/cernohl))
- Modular: MIDI-only or combined MIDI + audio
- Independent MIDI controller with instant startup — audio issues don't affect MIDI
- Maker friendly: common components, existing modules
- Configuration as code — YAML setlists, version-controlled, diffable
- Built for live performance and studio use

## Discussion

Please join us on the [community Discord server](https://discord.gg/ncyKyryHAc).

## Architecture

The hardware architecture is modular. Two independent processors handle MIDI and audio processing, connected over USB-MIDI.

![Architecture Overview](https://raw.githubusercontent.com/pedalboard/.github/refs/heads/main/docs/architecture.drawio.svg)

### Hardware Components

| Component                                                                | Description                                                          | Image |
|--------------------------------------------------------------------------|----------------------------------------------------------------------|-------|
| [Main Board](https://pedalboard.github.io/pedalboard-hw/latest/)        | CM4/CM5 carrier, RP-2040 MIDI controller, 6 buttons, 2 encoders     | <img src="https://pedalboard.github.io/pedalboard-hw/latest/3D/pedalboard-hw-3D_blender_1_top.png" alt="Main Board" width="200"> |
| [Display Board](https://pedalboard.github.io/pedalboard-display/latest/)| 8 RGB LED rings + 2 OLED display ports                               | <img src="https://pedalboard.github.io/pedalboard-display/latest/3D/pedalboard-display-3D_blender_1_top.png" alt="Display Board" width="200"> |
| [Sound Card](https://pedalboard.github.io/pedalboard-soundcard/latest/) | I²S audio codec HAT — PCM1863 ADC (106dB SNR) + PCM5242 DAC (112dB) | <img src="https://pedalboard.github.io/pedalboard-soundcard/latest/3D/pedalboard-soundcard-3D_blender_1_top.png" alt="Sound Card" width="200"> |
| [RGB LED Ring](https://github.com/pedalboard/pedalboard-led-ring)       | RGB LED ring around foot button                                      | |
| [Mechanical Parts](https://github.com/pedalboard/pedalboard-case)       | 3D printable case and mounting parts                                 | |

### Software

| Component | Description |
|-----------|-------------|
| [MIDI Firmware](https://github.com/pedalboard/pedalboard-midi) | RP-2040 firmware (Rust) for MIDI control |
| [CLI](https://github.com/pedalboard/pedalboard-cli) | Configuration tool — YAML setlists → device upload |
| [ELK Audio OS](https://www.elk.audio/how-elk-audio-os-works) | Real-time audio processing on CM4/CM5 |
| [Software Architecture](https://github.com/pedalboard/.github/blob/main/docs/software-architecture.md) | System overview, task structure, PE data flow |

### Assembly

| top view                  | rear view                   |
|---------------------------|-----------------------------|
| ![top](../img/v4-top.png) | ![rear](../img/v4-rear.png) |

## Open Source Tools

- [KiCad](https://www.kicad.org) — PCB design
- [OpenSCAD](https://openscad.org/) — 3D printable parts
- [LumenPnP](https://www.opulo.io/) — PCB assembly
- [Rust](https://www.rust-lang.org/) — MIDI controller firmware
- [ELK Audio OS](https://www.elk.audio/how-elk-audio-os-works) — real-time audio
