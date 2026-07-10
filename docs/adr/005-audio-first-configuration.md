# ADR: Audio-First Configuration with Standalone Fallback

## Status

Accepted (2026-07-10)

## Context

The pedalboard hardware serves two fundamentally different use cases:

1. **Standalone MIDI controller** — like a Morningstar MC6: sends CC, PC, Note messages to external gear over USB/DIN MIDI. User configures every button, LED, encoder manually. No audio processing, no CM5 needed.

2. **Integrated audio processor** — like a Helix/Kemper: the controller + audio engine work as one unit. Amp models, effects, expression routing are all managed together. The controller's job is to operate the audio rig.

These are not separate products — they're the same hardware in two modes. A user might start with standalone control (existing pedalboard, external amps) and later add the CM5 for audio processing. The configuration format must support both without making either mode awkward.

## Decision

**Audio-first configuration with optional controller overrides, falling back to full manual control when no audio is present.**

### Principle

When an `audio` section is present in the setlist:
- The audio rig (plugins, snapshots, expression mappings) is the **source of truth**
- The controller configuration **derives automatically** from the audio definition
- The user only specifies **overrides** for what should differ from defaults
- Unspecified buttons, labels, colors, and expression routes are generated from audio context

When no `audio` section is present:
- The controller operates in standalone mode
- Every button, CC, color, label must be explicitly configured
- Identical to a Morningstar — maximum flexibility, manual control

### Auto-generation rules (when audio is present)

#### Buttons from snapshots
If a preset has `audio_snapshot` but no explicit button definitions for snapshot switching:
- Generate one button per audio snapshot, in order
- Labels = snapshot names
- Colors = auto-assigned (green → yellow → red → blue → ...)
- Action = switch to that audio snapshot
- Remaining buttons available for manual override

#### Expression from snapshot
If the audio snapshot defines expression assignments:
- Pedal labels auto-derived from target param name ("MASTER" → "Volume", "PREGAIN" → "Gain")
- CC numbers inherited from the audio `expression` pedal mapping
- No need to define `analog:` section manually unless overriding labels

#### Default snapshot on preset enter
If a preset has `audio_snapshot` defined:
- On preset switch, the audio engine switches to that snapshot automatically
- No explicit `on_enter` action needed

### Override precedence

Explicit configuration always wins over auto-generated defaults:

```yaml
presets:
  - name: "My Song"
    audio_snapshot: "Clean"
    buttons:
      # A is explicitly defined — overrides any auto-generation
      A: { label: "Boost", cc: 80, toggle: true, color: white }
      # B, C auto-generated from remaining snapshots if not specified
```

### Examples

#### Minimal audio-integrated setlist (maximum auto-config)
```yaml
audio:
  plugins: [...]
  connections: [...]
  snapshots:
    - name: "Clean"
      ...
    - name: "Crunch"
      ...
    - name: "Lead"
      ...

presets:
  - name: "Song 1"
    # That's it. Buttons A/B/C auto-mapped to Clean/Crunch/Lead.
    # Labels, colors, expression all derived from audio config.
```

#### Partially overridden (audio + custom buttons)
```yaml
presets:
  - name: "Song 1"
    audio_snapshot: "Clean"
    buttons:
      A: { label: "Clean", audio_snapshot: "Clean", color: green }
      B: { label: "Crunch", audio_snapshot: "Crunch", color: yellow }
      C: { label: "Solo!", audio_snapshot: "Lead", color: red, animation: pulse }
      # D-F: custom external gear control
      D: { label: "Looper", cc: 3, toggle: true, color: blue }
      E: { label: "Tap", tap_tempo: true }
      F: { label: "Next", on_long_press: next_preset, color: magenta }
```

#### Pure standalone (no audio, full manual)
```yaml
presets:
  - name: "Live FX"
    buttons:
      A: { label: "Board 1", program_change: 0, channel: 2, color: blue }
      B: { label: "Board 2", program_change: 1, channel: 2, color: green }
      C: { label: "Bypass", cc: 0, toggle: true, color: red }
    encoders:
      Vol: { label: "HotKnob", cc: 107, channel: 2 }
    analog:
      Exp1: { label: "Volume", cc: 7 }
```

## Consequences

### For users
- **Audio users**: define your rig and snapshots, controller "just works" with sensible defaults
- **Standalone users**: nothing changes, full manual configuration as before
- **Migration path**: start standalone, add CM5 + audio section later, keep custom overrides

### For implementation
- **Compile tool** (setlist compiler): resolves auto-generation at compile time. The compiled output is always fully explicit — devices never auto-generate at runtime.
- **Firmware**: receives the same binary format regardless of mode. It doesn't know whether config was auto-generated or manual.
- **Bridge**: reads the audio section. Controller config is firmware-only — bridge doesn't need to know about button layouts.
- **Schema**: `buttons`, `encoders`, `analog` remain optional on presets. When omitted + audio present = auto-generated at compile time.

### Trade-offs
- **Pro**: Simple for audio users (less config to write), powerful for standalone users (nothing restricted)
- **Pro**: Compiled output is always explicit — no runtime ambiguity
- **Pro**: Clear mental model: audio defines the intent, controller follows
- **Con**: Auto-generation logic lives in the compile tool — needs well-defined rules
- **Con**: Users might be surprised by auto-generated defaults (mitigation: `pedalboard-cli compile --preview` shows what will be generated)

### Design guideline for future features

When adding a new feature, ask:
1. Can this be derived from the audio configuration? → Auto-generate it.
2. Should the user be able to override it? → Always yes.
3. Does it make sense in standalone mode? → Must work without audio section.

**Never require the user to configure the controller when the audio config already expresses the intent.**

### CC and channel allocation

When the compile tool auto-generates controller configuration from audio, it must not conflict with user-defined MIDI assignments. Strategy:

1. **Scan all explicit presets** — collect every CC number + channel pair already in use
2. **Allocate internal CCs from unused space** — auto-generated snapshot buttons, expression routing, etc. use CCs that don't appear in any user-defined button/encoder/analog config
3. **Use a dedicated internal channel** — default: channel 16. Configurable via `global.internal_channel`. This channel carries bridge-internal messages (snapshot switching, expression routing) that never leave the device toward external gear. User's external gear typically lives on channels 1-10.
4. **Document the allocation** — the compiled output includes a comment or metadata showing which CCs were auto-assigned, so the user can see what happened

Example: user defines buttons on channel 1 (CC 80, 81, 82) and channel 2 (PC 0-3). The compile tool assigns audio snapshot switching to channel 16, CC 0-2 — guaranteed no conflict.

**Principle:** auto-generated MIDI never interferes with user-defined MIDI. The compile tool is aware of the full configuration and avoids collisions deterministically.
