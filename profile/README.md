# Open Pedalboard Hardware and Software Platform

<img src="../img/pedalboard-logo-large.png" alt="Logo" width="600"/>

An open source platform for building pedalboard components — MIDI foot controllers
and audio processing for guitar effects.

## Design Goals

- Fully open source hardware and software ([CERN-OHL-P-2.0](https://ohwr.org/cernohl))
- Modular: MIDI-only or combined MIDI + audio
- Independent MIDI controller with instant startup — audio issues don't affect MIDI
- Maker friendly: common components, existing modules
- Flat design: 30mm case height target
- Built for live performance, not a playground

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
