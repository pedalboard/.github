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

### What doesn't work
- `mod-host` TCP `param_set` for model file path (not supported)
- `mod-host` TCP `preset_load` with state.ttl (error -104)
- `mod-host` TCP `state_set` (not a valid command)
- Setting PARAM1/PARAM2 to file path (these are numeric controls, not file params)

### State key for model file
```
URI: http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader#json
Type: atom:Path
```

## Available Models
```
/home/laenzi/models/JC120-Clean.aidax      (147KB, Roland JC120 clean)
/home/laenzi/models/Fender_Twin_Clean.aidax (300KB, Fender Twin clean)
/home/laenzi/models/Marshall_JCM800.aidax   (300KB, Marshall crunch/gain)
```

## mod-host Protocol Notes
- TCP socket on port 5555
- Commands are newline-terminated
- Responses are **null-byte terminated** (not newline!)
- `add <uri> <id>` → `resp 0\x00` on success
- `param_set <id> <symbol> <value>` → `resp 0\x00`
- `remove -1` removes all instances
- `bypass <id> <0|1>` toggles bypass

## Bridge Integration (pedalboard-bridge)
- Detects MIDI Program Change from RP2040
- Sends mod-host commands via TCP
- Audio config: `audio-patches.json` (capture/playback ports, plugin chain per patch)
- Current issue: remove+add causes audio click on switch

## Next Steps (Issue #89)

### Recommended architecture: parallel instances with bypass
```
                    ┌─ effect_0 (Clean model)    ─┐
capture_2 ──┬──────┼─ effect_1 (Crunch model)   ─┼────── playback_2
             │      └─ effect_2 (High Gain model) ─┘
             │
             └── Only ONE instance un-bypassed at a time
```

- Start 3 jalv instances at boot (each with own state dir + model)
- All connected in parallel: capture → all inputs, all outputs → playback  
- Bridge switches by toggling JACK connections (disconnect old, connect new)
- Or: use bypass parameter on AIDA-X (NETBYPASS symbol)
- Zero audio gap on switch

### Implementation tasks
1. Create state directories per model (state.ttl + .aidax file)
2. Start multiple jalv instances on boot (systemd service or bridge startup)
3. Bridge manages which instance is active (JACK connect/disconnect)
4. PC message from RP2040 → bridge selects instance
5. Expression pedal CC → bridge forwards to active instance's PREGAIN/MASTER

### MOD UI
- Installed at `/opt/mod-ui`, runs on port 8888
- Can load plugins and manage parameters via browser
- Useful for initial setup/experimentation
- Not needed for live switching (bridge handles it)

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

# With AIDA-X (via jalv + model)
(tail -f /dev/null) | jalv -l /tmp/model-state -n AIDAX \
    http://aidadsp.cc/plugins/aidadsp-bundle/rt-neural-loader &
sleep 3
jack_connect system:capture_2 AIDAX:lv2_audio_in_1
jack_connect AIDAX:lv2_audio_out_1 system:playback_2

# Kill everything
killall jalv tail jackd
```
