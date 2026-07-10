# ADR: Compiled Setlist — If It Uploads, It Works

## Status

Accepted (2026-07-10)

## Context

The pedalboard system has two deployment targets:

- **RP2040 firmware** — MIDI presets (buttons, LEDs, encoders) via PE SysEx
- **CM5 bridge** — audio plugin chain (mod-host plugins, connections, snapshots)

Configuration comes from a library of reusable building blocks:
- Rig definitions (plugin chains + snapshot parameter sets)
- Song definitions (button layouts + audio snapshot references)
- Global settings (calibration, MIDI routing)

A musician prepares for a specific gig by assembling songs into a setlist. Each gig is slightly different — different song order, different rigs, different venues.

**The problem:** if the system assembles configuration at runtime (resolves references, discovers files, imports libraries), failures can happen on stage. A missing file, a typo in a reference, an incompatible plugin version — all invisible until the moment you need it.

## Decision

The setlist file is a **compiled deployment artifact**. It is:

1. **Self-contained** — no external references, no imports, no file paths to resolve at runtime
2. **Fully resolved** — all building blocks (rigs, songs, snapshots) inlined into a single flat structure
3. **Validated at compile time** — the compilation tool verifies all references exist, all plugin URIs are valid, all connections are coherent, all snapshot parameters match loaded plugins
4. **Immutable at runtime** — the bridge and firmware load it once at boot and never modify it
5. **Tested before deploy** — if `pedalboard-cli upload` succeeds and you play through the setlist once at home, it will behave identically on stage

### Compilation pipeline

```
Library (reusable, version-controlled)
  ├── rigs/*.yaml          (plugin chains + snapshots)
  ├── songs/*.yaml         (button layouts + audio refs)
  └── global.yaml          (device settings)
           │
           ▼  setlist tool (compile + validate)
Setlist (compiled, single file)
  └── gig-2026-07-15.yaml
           │
           ▼  pedalboard-cli upload
Devices (runtime)
  ├── RP2040: MIDI presets in flash
  └── CM5: audio config in memory
```

### Compiled file properties

- **One file** — contains everything for one gig
- **No references** — rigs are inlined, songs are inlined, everything flat
- **Schema-validated** — JSON Schema enforces structure
- **Versioned** — `version:` field for forward compatibility
- **Deterministic** — same library + same song list = same output

### Runtime guarantees

The bridge and firmware make these promises about the compiled file:

- **Load entirely into memory at boot** — no lazy loading, no disk I/O during performance
- **No network calls** — everything local, no dependencies on external services
- **No file resolution** — all paths (model files) are absolute and validated at compile time
- **Fail fast** — if anything is wrong (missing model, invalid URI), fail at upload/boot, never mid-performance
- **Atomic switch** — snapshot changes are a batch of `param_set` + `bypass` commands, not a sequence that can partially fail

### What the setlist tool validates at compile time

- All plugin URIs exist in the LV2 world on the target device
- All model files exist at the specified paths
- All JACK port names in connections are syntactically valid
- All snapshot references in presets resolve to defined snapshots
- All button/encoder configs are within firmware limits
- Total plugin count fits in CM5 RAM budget
- No duplicate instance IDs

### What stays outside the compiled file

- **Model files** (.aidax/.json) — too large to inline, deployed separately to `/etc/pedalboard/models/`
- **Plugin binaries** (LV2 .so) — installed system-wide, not per-setlist
- **Firmware binary** — flashed separately via `pedalboard-cli flash`

These are system prerequisites, not per-gig configuration. The setlist tool validates they exist but doesn't bundle them.

## Consequences

- **Zero runtime surprises** — compilation catches all errors before the gig
- **Fast boot** — no file scanning, no discovery, just parse one YAML and send commands
- **Portable** — copy one file to back up your entire gig configuration
- **Diffable** — git-track compiled setlists, see exactly what changed between rehearsal and gig
- **Library independence** — the devices don't know about the library structure; they only see the compiled output
- **Tool flexibility** — the compilation tool can be replaced, extended, or rewritten without touching devices

## Format (high-level structure)

```yaml
version: 2

audio:
  plugins: [...]        # full rig, loaded at boot
  connections: [...]    # JACK wiring
  snapshots: [...]      # named parameter states

global:
  din_enabled: true
  midi_clock: true
  bpm: 120

presets:
  - name: "Song 1"
    audio_snapshot: "Clean"    # or per-button switching
    buttons: { ... }
    encoders: { ... }
```

Exact schema TBD — see pedalboard-cli for implementation.
