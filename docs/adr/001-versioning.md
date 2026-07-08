# ADR: Versioning Strategy

## Status

Accepted (2026-07-04)

## Context

The pedalboard platform has multiple interfaces where version compatibility matters:

1. **Flash storage** — presets serialized by one firmware version, read by another after OTA update
2. **YAML setlist schema** — user-authored files consumed by CLI, future web UI, or third-party tools
3. **PE wire protocol** — MIDI-CI Property Exchange messages between CLI/bridge and firmware
4. **Rust crate API** — `pedalboard-protocol` consumed by firmware and CLI at compile time

Each has different consumers, change frequencies, and compatibility requirements.

## Decision

Use **two independent version numbers** with different semantics:

### 1. Flash Format Version (integer, per-blob prefix)

**What:** A single `u8` stored as the first byte of every serialized preset/config blob in flash.

**Where:** Defined as `PRESET_SCHEMA_VERSION` in `pedalboard-protocol/src/config.rs`. Checked by firmware on boot.

**When to bump:** Whenever the postcard-serialized layout of `Preset` or `GlobalConfig` changes (added/removed/reordered fields, changed types).

**Behavior on mismatch:**
- Firmware logs "preset N: flash format vX, firmware expects vY — skipped"
- Preset is not loaded (treated as empty)
- No crash, no migration, no data corruption
- User re-uploads setlist via CLI (< 2 seconds)

**Why not semver:** This is a binary compatibility check between a single writer (past firmware) and a single reader (current firmware). There's no negotiation, no partial compatibility — either the bytes decode or they don't. A single integer is sufficient.

### 2. Setlist Schema Version (semver-style, in YAML file)

**What:** A `version` field in the setlist YAML that declares which schema edition the file uses.

```yaml
version: 1
global: ...
presets: ...
```

**Where:** Parsed by CLI and future tools. Validated on load.

**When to bump:**
- **Major** (1 → 2): Breaking changes — removed fields, renamed keys, changed semantics. Old tools cannot parse the file correctly.
- **Minor** (1.0 → 1.1): Additive changes — new optional fields. Old tools can still parse the file (unknown fields ignored via `#[serde(default)]`).

**Behavior on mismatch:**
- Tool sees version > supported: error with "this file requires pedalboard-cli >= X.Y"
- Tool sees version < supported: parse normally (backwards compatible)

**Why semver:** Multiple independent consumers (CLI, web UI, third-party editors) at different release cadences need a clear compatibility signal. Semver communicates "can I parse this?" without coupling to a specific tool version.

### 3. PE Protocol (no separate version — coupled to firmware)

The Property Exchange protocol (MIDI-CI SysEx framing) is not independently versioned because:
- CLI and firmware are always deployed together (flash implies matching CLI)
- Bridge is a raw passthrough (version-agnostic)
- There are no third-party PE consumers

If this changes (e.g., third-party control apps), version negotiation can be added via MIDI-CI Discovery (already part of the spec).

### 4. Rust Crate (`pedalboard-protocol`)

Uses standard Cargo semver for source API compatibility. This is separate from the serialization format — the crate can have a minor version bump (new public API) without changing the flash format, or vice versa.

## Consequences

- **Flash version prefix** adds 1 byte per stored blob. Negligible overhead.
- **Setlist version** is optional in v1 (omitted = v1 assumed). Required from v2 onward.
- **No migration code** for flash — stale presets are simply dropped. This is acceptable because re-upload is fast and setlists are version-controlled in git.
- **Future web UI** can declare "supports schema 1.0–1.3" and reject files it can't handle, without knowing anything about firmware versions.
- **PRESET_SCHEMA_VERSION must only be bumped when serialization actually changes** — adding a `#[serde(default)]` field to the end of a struct does NOT require a bump (postcard tolerates trailing data). Reordering or removing fields DOES.

## Summary Table

| Interface | Version Type | Stored Where | Bumped When | Mismatch Behavior |
|-----------|-------------|--------------|-------------|-------------------|
| Flash blobs | `u8` prefix | First byte in flash | Serialization layout changes | Skip + log warning |
| YAML setlist | semver (major.minor) | `version:` field in file | Schema changes (see rules above) | Error with upgrade hint |
| PE protocol | None (coupled) | N/A | N/A | Always in sync via flash |
| Rust crate | Cargo semver | `Cargo.toml` | Public API changes | Compile error |
