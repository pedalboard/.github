---
name: hardware
description: KiCad PCB design, component selection, power supply, audio signal path, CI/KiBot, and fabrication. Use when working on schematics, PCB layout, BOM, or hardware documentation.
---

# Hardware Knowledge

## Architecture

- Dual-processor: RP2040 (MIDI, instant startup) + Raspberry Pi CM4/CM5 (audio, ELK Audio OS)
- Modular: MIDI-only build possible without audio module
- Target form factor: 200mm × 100mm control surface, 30mm case height

## Main Board (pedalboard-hw)

- 6 foot buttons (push/release/long/short press) on GPIO2-7
- 2 rotary encoders (Alps EC11E) on GPIO16/17/18 (Vol) and GPIO19/20/21 (Gain)
- 2 expression pedal inputs (ADC) on GPIO27/28
- 8 RGB LED rings (WS2812) via SPI1 — 12 LEDs per ring + 2 single LEDs
- 2x SSD1327 128x128 OLED via I2C0 (addr 0x3C, 0x3D), STEMMA connectors
- I2C EEPROM for config storage
- MIDI I/O: DIN5, 3.5mm TRS, header pins, USB-MIDI
- UART0 on GPIO0/1 (DIN MIDI)
- USB-A host + Micro-USB device
- Power: 6-28V input with 3A buck converter, USB power with ORing

## Audio Options

- Custom pedalboard-soundcard: PCM1863 ADC (106dB SNR) + PCM5242 DAC (112dB), 2-channel differential I/O
- Alternative: HiFiBerry DAC+ ADC PRO (stereo)
- ~2ms latency with ELK Audio OS

## KiCad Rules

- Do NOT edit .kicad_sch files with regex — use KiCad GUI
- After schematic changes: Update PCB from Schematic, then refill zones
- Footprint compatibility must be verified before swapping parts
- Run ERC + DRC checks before committing schematic/PCB changes

## CI/CD (KiBot)

- KiBot generates outputs on push (GitHub Actions, `kicad9_auto_full` container)
- Outputs: schematics, iBOM, 3D renders, gerbers
- Deploy to `-site` companion repos via `JamesIves/github-pages-deploy-action`
- Large 3D STEP models removed before deploy

## Build & Test (pedalboard-hw)

- `make test` — run ERC and DRC checks
- `make bom` — export BOM + InvenTree conversion (`bon2inventree`)
- `make step` — export 3D STEP model
- `make pdf` — export schematic and PCB PDFs
- `make pos` — export pick-and-place position file

## Fabrication

- PCBWay for PCB manufacturing
- Digi-Key for component sourcing
- Generated iBOM for assembly reference
- LumenPnP for PCB assembly
- Release procedure documented in `doc/release-procedure.md`
