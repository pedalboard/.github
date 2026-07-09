# Audio Integration Notes (2026-07-06)

## Working Setup

### Hardware
- CM5 (Cortex-A76 @ 2.4GHz, 4GB RAM, Debian Bookworm)
- Custom soundcard: PCM1863 ADC + PCM5242 DAC
- Overlay: `dtoverlay=hifiberry-dacplusadcpro` in `/boot/firmware/config.txt`

### Channel Mapping
- **Guitar input:** `system:capture_2` (right channel)
- **Audio output:** `system:playback_2` (right channel)
- Left channel (capture_1/playback_1) = unused/noise floor

### JACK Configuration
```bash
jackd -d alsa -d hw:3 -r 48000 -p 64 -n 2 -i 2 -o 2
```
**Critical:** Must use `-i 2 -o 2` to force 2-channel mode. Without this, the driver opens in 8-channel TDM mode and audio routes to non-existent hardware channels.

### ALSA Mixer Settings (must set after JACK starts)
```bash
amixer -c 3 set "Auto Mute Mono" off
amixer -c 3 set "Auto Mute" off
amixer -c 3 set Digital 80%        # DAC output level (-20.5dB)
amixer -c 3 set Analogue 100%
amixer -c 3 set ADC 40%            # +9dB preamp (40% avoids clipping)
```
**Critical:** Auto Mute must be disabled — the PCM5242 mutes output during silence between guitar strums.

### Performance
- Buffer: 64 frames @ 48kHz = **1.33ms** latency per direction
- Total roundtrip: ~2.7ms (ADC + processing + DAC)
- AIDA-X CPU: **3.4%** per instance

## AIDA-X Model Loading

### What works: jalv with LV2 state directory
```bash
mkdir -p /tmp/model-state
cp /home/laenzi/models/Marshall_JCM800.aidax /tmp/model-state/

cat > /tmp/model-state/state.ttl << 'EOF'
@prefix atom: <http://lv2plug.in/ns/ext/atom#> .
@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix pset: <http://lv2plug.in/ns/ext/presets#> .
@prefix state: <http://lv2plug.in/ns/ext/state#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<>
    a pset:Preset ;
    rdfs:label "Marshall" ;
    lv2:appliesTo <http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader> ;
    state:state [
        <http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader#json> <Marshall_JCM800.aidax>
    ] ;
    lv2:port [
        lv2:symbol "PREGAIN" ;
        pset:value 0.8
    ] , [
        lv2:symbol "MASTER" ;
        pset:value 0.7
    ] .
EOF

(tail -f /dev/null) | jalv -l /tmp/model-state -n AIDAX \
    http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader &
```

### What works: mod-host preset_load (preferred method)

mod-host supports AIDA-X model loading via `preset_load` when using a proper LV2 preset bundle.

**Requirements:**
1. Create an LV2 preset bundle (directory with `manifest.ttl` + `presets.ttl`)
2. Register it with `bundle_add`
3. Load presets by URI with `preset_load`

**Preset bundle structure:**

```
/etc/pedalboard/presets.lv2/
├── manifest.ttl
└── presets.ttl
```

`manifest.ttl`:
```turtle
@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix pset: <http://lv2plug.in/ns/ext/presets#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://pedalboard.local/presets#california-clean>
    a pset:Preset ;
    lv2:appliesTo <http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader> ;
    rdfs:seeAlso <presets.ttl> .

<http://pedalboard.local/presets#british-rhythm>
    a pset:Preset ;
    lv2:appliesTo <http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader> ;
    rdfs:seeAlso <presets.ttl> .
```

`presets.ttl`:
```turtle
@prefix atom: <http://lv2plug.in/ns/ext/atom#> .
@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix pset: <http://lv2plug.in/ns/ext/presets#> .
@prefix state: <http://lv2plug.in/ns/ext/state#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://pedalboard.local/presets#california-clean>
    a pset:Preset ;
    rdfs:label "California Clean" ;
    lv2:appliesTo <http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader> ;
    state:state [
        <http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader#json> </etc/pedalboard/models/tw40_california_clean_deerinkstudios.json>
    ] ;
    lv2:port [
        lv2:symbol "PREGAIN" ;
        pset:value 0.5
    ] , [
        lv2:symbol "MASTER" ;
        pset:value 0.8
    ] .

<http://pedalboard.local/presets#british-rhythm>
    a pset:Preset ;
    rdfs:label "British Rhythm" ;
    lv2:appliesTo <http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader> ;
    state:state [
        <http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader#json> </etc/pedalboard/models/tw40_british_rhythm_deerinkstudios.json>
    ] ;
    lv2:port [
        lv2:symbol "PREGAIN" ;
        pset:value 0.9
    ] , [
        lv2:symbol "MASTER" ;
        pset:value 0.6
    ] .
```

**mod-host commands:**
```
bundle_add /etc/pedalboard/presets.lv2       → resp 0
preset_load 0 http://pedalboard.local/presets#california-clean  → resp 0
preset_load 0 http://pedalboard.local/presets#british-rhythm    → resp 0
```

**To update presets at runtime** (e.g., after editing the TTL files):
```
bundle_remove /etc/pedalboard/presets.lv2 ""
bundle_add /etc/pedalboard/presets.lv2
```

**Key points:**
- Model path in `state:state` must be an **absolute path** to the .json/.aidax file
- Model files must be valid JSON (neural network weights), not HTML/binary
- The neural network reloads on each `preset_load` (~2 seconds on CM5)
- Parameters (PREGAIN, MASTER, etc.) are set atomically with the model load
- Only one TCP client can connect to mod-host at a time (bridge holds the connection)

### What doesn't work
- `param_set` for model file path (not a control port, it's atom:Path state)
- `state_set` (not a valid mod-host command)
- Setting PARAM1/PARAM2 to file path (these are numeric controls)

### State key for model file
```
URI: http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader#json
Type: atom:Path
```

## Available Models
```
/etc/pedalboard/models/tw40_california_clean_deerinkstudios.json
/etc/pedalboard/models/tw40_california_crunch_deerinkstudios.json
/etc/pedalboard/models/tw40_british_rhythm_deerinkstudios.json
/etc/pedalboard/models/tw40_blues_deluxe_deerinkstudios.json
/etc/pedalboard/models/tw40_blues_solo_deerinkstudios.json
```

Note: Models must be valid JSON files (neural network weights). Files downloaded
from GitHub web UI may be HTML pages — always verify with `file <path>`.

## mod-host Protocol Notes
- TCP socket on port 5555
- Commands are newline-terminated
- Responses are **null-byte terminated** (not newline!)
- `add <uri> <id>` → `resp 0\x00` on success
- `param_set <id> <symbol> <value>` → `resp 0\x00`
- `preset_load <id> <preset_uri>` → `resp 0\x00` (loads state including atom:Path)
- `bundle_add <path>` → `resp 0\x00` (registers LV2 bundle with preset definitions)
- `bundle_remove <path> ""` → `resp 0\x00` (unregisters bundle, allows re-add)
- `remove -1` removes all instances
- `bypass <id> <0|1>` toggles bypass
- **Only one TCP client at a time** — bridge holds the connection

## Bridge Integration (pedalboard-bridge)
- Detects MIDI Program Change from RP2040
- Sends mod-host commands via TCP
- Audio config: `audio-patches.json` (capture/playback ports, plugin chain per patch)
- On preset switch: `preset_load` for AIDA-X model + `param_set` for effects

## Architecture Decision (2026-07-10)

**Chosen stack:** mod-host + MOD UI + preset bundles

- **Design:** MOD UI (browser-based, localhost:8888) for plugin chain design
- **Runtime:** mod-host (headless, TCP API) for live plugin hosting
- **Model switching:** `preset_load` with LV2 preset bundles (validated working)
- **Bridge role:** JACK MIDI → program change → mod-host preset_load
- **Future migration path:** When/if mod-host becomes limiting, rewrite bridge
  as Rust in-process LV2 host (livi-rs + state support) or switch to Carla headless

### Why not alternatives?
- **jalv subprocesses:** Works but unwieldy for deep chains (one process per plugin)
- **Carla headless:** Great plugin host but poor external control API (no clean project switching)
- **livi-rs (Rust in-process):** Missing LV2 state support — can't load AIDA-X models
- **mod-host:** Clean TCP API, supports state/presets/worker, single process for all plugins ✅

### Recommended architecture: preset_load switching
```
Bridge preset config:
  preset 0 → bundle_add + preset_load california-clean
  preset 1 → bundle_add + preset_load british-rhythm
  preset 2 → bundle_add + preset_load blues-deluxe

Audio routing (static, set up once at boot):
  system:capture_2 → effect_0:in → effect_0:out → system:playback_2
```

- Single AIDA-X instance in mod-host, model swapped via `preset_load`
- Additional effects (reverb, delay) as separate mod-host instances
- Expression pedal CC → `param_set` on active instance
- ~2 seconds model reload time (acceptable for preset switching between songs)

### Implementation tasks (remaining)
1. Deploy preset bundle to `/etc/pedalboard/presets.lv2` on CM5
2. Bridge: `bundle_add` at startup, `preset_load` on program change
3. Bridge: `param_set` for expression pedal CC routing
4. MOD UI: design full chains (amp + effects), export as preset bundles

### MOD UI
- Installed at `/opt/mod-ui`, runs on port 8888
- Can load plugins and manage parameters via browser
- Useful for initial setup/experimentation
- Pedalboard .ttl files can be converted to preset bundles for mod-host

## Quick Test Commands

```bash
# Start everything
jackd -d alsa -d hw:3 -r 48000 -p 64 -n 2 -i 2 -o 2 &
sleep 2
amixer -c 3 set "Auto Mute" off
amixer -c 3 set "Auto Mute Mono" off
amixer -c 3 set ADC 40%

# Direct loopback (clean guitar test)
jack_connect system:capture_2 system:playback_2

# With mod-host (preferred)
# mod-host should already be running via systemd
# Connect via TCP:
python3 -c "
import socket
s = socket.socket(); s.connect(('localhost', 5555)); s.settimeout(10)
def cmd(c):
    s.sendall((c+'\n').encode())
    d=b''; 
    while b'\x00' not in d: d+=s.recv(4096)
    print(f'{c} => {d.replace(b\"\\x00\",b\"\").decode().strip()}')
cmd('add http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader 0')
cmd('bundle_add /etc/pedalboard/presets.lv2')
cmd('preset_load 0 http://pedalboard.local/presets#california-clean')
cmd('connect system:capture_2 effect_0:lv2_audio_in_1')
cmd('connect effect_0:lv2_audio_out_1 system:playback_2')
s.close()
"
```
