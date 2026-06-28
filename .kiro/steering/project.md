# OpenDeck Pedalboard Project

## Repositories

All repos live under `/home/laenzi/projects/gh/pedalboard/`:

| Repo | Language | Purpose | Runs on |
|------|----------|---------|---------|
| `pedalboard-hw` | KiCad 9 | Main board: RP2040 + CM4/CM5 carrier | — |
| `pedalboard-display` | KiCad 9 | Display daughter board (LEDs + OLEDs) | — |
| `pedalboard-soundcard` | KiCad 9 | I²S audio codec (PCM1863 + PCM5242) | — |
| `pedalboard-led-ring` | KiCad 9 | RGB LED ring per foot button | — |
| `pedalboard-case` | OpenSCAD | 3D printable enclosure | — |
| `pedalboard-midi` | Rust (RTIC) | RP2040 firmware | RP2040 |
| `pedalboard-protocol` | Rust (`#![no_std]`) | Shared config types + MIDI-CI PE framing | library |
| `pedalboard-cli` | Rust | Config upload (OpenDeck SysEx + PE) | dev machine |
| `pedalboard-bridge` | Go | WebSocket↔MIDI bridge (raw ALSA I/O) | CM5 |
| `pedalboard-graphics` | Rust | Display UI prototype (desktop sim) | dev machine |
| `dotgithub` | — | Org profile, architecture diagram, logos | — |

## Development Workflow

- Dev machine: Arch Linux, GPG SSH key (subkey 7C71F5DC)
- Test host: Raspberry Pi CM5 (`ssh laenzi@cm5-dev.home`)
- Pre-commit hooks in all repos — never use `--no-verify`
- Push to main directly (solo project, no PRs)
- CI validates on GitHub Actions (all repos have `ci.yml`)
- All code changes on dev machine, never edit directly on CM5

### Deploy

- Firmware: `cd pedalboard-midi && make flash` (DFU via bridge) or `make flash-probe` (SWD)
- Bridge: `cd pedalboard-bridge && make deploy` (push, pull on CM5, build, restart)
- CLI: `cargo build` (runs locally)

### Version Convention

All binaries embed `<semver>-<git-hash>`. Uncommitted builds show `+dev` suffix.

## Key Rules

- Run `cd pedalboard-cli && ./tests/integration.sh` before pushing firmware or protocol changes
- `pedalboard-midi` uses `--config` patches for local deps — **never modify `Cargo.toml` `[patch]` sections**
- Go binary on CM5 not in PATH — use `/usr/local/go/bin/go`
- Bridge auto-reconnects on firmware reboot/flash

## Licensing

- Hardware: CERN OHL-P v2
- Software/firmware: GPL
- OSHWA certified: CH000023
