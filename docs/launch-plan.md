# Launch Plan

Internal plan for publishing the Open Pedalboard project as a kit.

## Architecture Decision (2026-07-05)

**Two kit tiers, same PCB:**

| Kit | Contents | Price target |
|-----|----------|-------------|
| **MIDI Controller** | RP2040 + buttons + encoders + LED rings + displays + USB-C + DIN MIDI | ~€100 |
| **Full (MIDI + Audio)** | Above + CM5 + soundcard + mod-host + AIDA-X | ~€200 |

**Audio stack:** Debian Bookworm + JACK + mod-host + AIDA-X LV2 (not ELK Audio OS).
Validated: 3.4% CPU, 1.3ms buffer latency, 64 frames @ 48kHz on CM5. See issue #88.

## Status

### Firmware ✅ Done
- [x] All button modes (momentary, toggle, radio group, long press, CcCycle)
- [x] LED rings (colors, animations, renderers, reactive CC, SetLed in sequences)
- [x] Encoders (absolute CC, relative CC, preset scroll)
- [x] Expression pedals (ADC with calibration)
- [x] MIDI clock + tap tempo
- [x] Triggers (incoming MIDI → state/action)
- [x] PE protocol with status codes
- [x] Flash versioning + lifecycle management
- [x] Device status query
- [x] Stale preset clearing
- [x] 14 integration tests passing

### Software ✅ Done
- [x] CLI: upload, read, status, monitor, flash, reboot, reset
- [x] Bridge: WebSocket↔MIDI on CM5
- [x] Config-as-code (YAML setlists)
- [x] Schema version + JSON schema for tooling
- [x] CONTRIBUTING.md + ADRs

### Hardware 🔧 Needs one KiCad revision
- [ ] ESD protection on expression inputs (#35)
- [ ] USB-C device connector (#36)
- [ ] Stacked dual USB-A from hub (#37)
- [ ] Tantalum → electrolytic caps (#32)
- [ ] Hirose DF40C connectors (#31)
- [ ] SOT-353 → SOT-23-5 (#30)
- [ ] Display board: BOOTSEL/RESET cutouts (display #3)

### Audio 🔧 Needs integration
- [x] AIDA-X builds and runs on CM5 (validated)
- [x] Soundcard detected and working at 64 frames
- [ ] mod-host integration in pedalboard-bridge (#89, #90)
- [ ] Preset → audio patch switching
- [ ] Model loading from file path
- [ ] Expression pedal → plugin parameter routing

### Documentation 📝 Not started
- [ ] Build guide with step-by-step photos (#91)
- [ ] BOM with supplier links + cost breakdown (#92)
- [ ] Getting started guide (#93)
- [ ] PCB testing / QC checklist (#94)
- [ ] Audio setup guide (CM5 + soundcard + mod-host + AIDA-X)

### Media 📷 Not started
- [ ] Demo video (30-60s): preset switching, LED animations, tap tempo
- [ ] Audio demo: clean → drive → high gain via AIDA-X
- [ ] Photos: finished unit, LED rings active, displays

## Kit v1 Critical Path

```
1. KiCad revision (all HW issues)     → 1 session
2. Order PCBs                          → 1-2 weeks lead time
3. Assemble (LumenPnP + through-hole)  → 1 day
4. Test + photograph                   → 1 day
5. Write build guide                   → 2-3 days
6. BOM + getting started docs          → 1-2 days
7. Demo video                          → 1 day
8. Publish                             → Hackaday + Reddit + Discord
```

**MIDI-only kit can ship as soon as step 6 is done.**
**Audio add-on** needs mod-host integration (bridge work, #89/#90) before it's user-ready.

## Launch Channels

| Channel | Audience | Angle |
|---------|----------|-------|
| Hackaday.io | Hardware makers | Open hardware, CERN-OHL, build-your-own |
| r/guitarpedals | Guitarists | MOD/Morningstar alternative, LED rings, €100 |
| r/diypedals | DIY builders | Kit, BOM, assembly guide |
| r/embedded | Embedded devs | Rust on RP2040, RTIC, no_std protocol design |
| r/linuxaudio | Audio devs | CM5 + JACK + AIDA-X at 1.3ms, no ELK needed |
| Discord | Early adopters | Build support, feedback, community |
| Tindie / Crowd Supply | Buyers | Kit sales |

## Messaging

**Hook:** "Open source guitar processor — MIDI controller + neural amp modeling, €200 in parts, fully FOSS"

**Key differentiators vs MOD Dwarf (€499):**
- Same audio engine (mod-host) + same plugins (AIDA-X, LV2)
- 6 buttons + LED rings + 2 encoders (vs 3 switches + 1 knob)
- Configuration as code (YAML, git-managed)
- Fully open hardware (CERN-OHL-P) — build it yourself
- Half the price as a kit

**Key differentiators vs Morningstar MC6 Pro (€450):**
- LED rings per button (12 RGB LEDs vs 1)
- Optional audio processing (amp modeling built-in)
- Open source everything
- One-third the price

**Target audience:**
1. Guitarists frustrated with closed/expensive controllers
2. Maker-musicians who want full control
3. Linux audio enthusiasts
4. Embedded Rust developers

## FOSS Stack

| Layer | Component | License |
|-------|-----------|---------|
| Hardware | PCBs + case | CERN-OHL-P |
| MIDI firmware | Rust/RTIC on RP2040 | GPL |
| Protocol | midi-controller | Apache/MIT |
| Bridge | Go on CM5 | GPL |
| Audio host | mod-host | GPL |
| Amp modeling | AIDA-X / RTNeural | GPL / BSD |
| Effects | LV2 plugins | GPL |
| Models | Community captures | CC |
| OS | Debian | FOSS |
| Audio | JACK / PipeWire | GPL / MIT |
