# Software Architecture

## System Overview

```mermaid
graph TB
    subgraph "Dev Machine"
        YAML[YAML Presets]
        CLI[pedalboard-cli]
        SIM[pedalboard-sim<br/>Virtual pedalboard]
        YAML --> CLI
    end

    subgraph "CM5 (Raspberry Pi)"
        JACK[JACK Audio/MIDI Server]
        BRIDGE[pedalboard-bridge<br/>Rust · JACK MIDI client]
        MODHOST[mod-host<br/>LV2 plugin host]
        MODUI[MOD UI<br/>Plugin chain designer]
        JACK --> BRIDGE
        BRIDGE -->|TCP| MODHOST
        MODUI -->|TCP| MODHOST
    end

    subgraph "RP2040 (Firmware)"
        USB[USB MIDI]
        PE[PE Handler<br/>Actions · LEDs · State]
        FLASH[Flash Storage<br/>Preset Persistence]
        DISP[Display Task<br/>SSD1327 × 2]
        LEDS[LED Writer<br/>WS2812 × 98]
        INPUT[Input Polling<br/>Buttons · Encoders · ADC]
    end

    CLI -->|WebSocket| BRIDGE
    SIM -->|JACK MIDI| JACK
    USB -->|a2jmidid| JACK
    INPUT --> PE
    PE --> USB
    PE --> LEDS
    PE --> DISP
    PE --> FLASH
    FLASH --> PE
```

## MIDI Routing (JACK MIDI)

All MIDI flows through JACK — same routing graph as audio.

```mermaid
graph LR
    subgraph "MIDI Sources"
        RP[RP2040 USB<br/>via a2jmidid]
        SIM[pedalboard-sim<br/>JACK client]
    end

    subgraph "JACK MIDI"
        IN[pedalboard-bridge:midi_in]
        OUT[pedalboard-bridge:midi_out]
    end

    subgraph "Consumers"
        BRIDGE[Bridge logic<br/>Program Change → snapshot switch<br/>CC → expression routing<br/>SysEx → WebSocket]
        MODHOST[mod-host:midi_in<br/>Plugin MIDI control]
    end

    RP -->|auto-connect<br/>pattern: pedalboard| IN
    SIM -->|auto-connect<br/>pattern: pedalboard| IN
    IN --> BRIDGE
    OUT --> RP
```

### Auto-connect

The bridge uses `--midi <pattern>` to auto-connect any JACK MIDI port whose alias matches the pattern (case-insensitive). Uses JACK's port registration callback for instant detection (~100ms) and reconnects after device reboot.

```bash
# On CM5:
pedalboard-bridge-rust --midi pedalboard-midi --addr 0.0.0.0:8080 --audio /etc/pedalboard/audio-rig.yaml --modhost localhost:5555
```

### CM5 setup

The RP2040 appears as a raw ALSA MIDI device (`/dev/snd/midiC*D*`). JACK exposes it as a JACK MIDI port via one of:

- **`-Xalsarawmidi`** flag on jackd (built-in, no extra daemon)
- **`a2jmidid -e`** (separate daemon, more control)

### Docker dev setup

The simulator is a native JACK MIDI client — no bridging needed. Both the simulator and bridge register as JACK clients on the same JACK server inside the container.

## Firmware Internals

> Task architecture, state machines, and storage details live in the firmware repo:
> [`pedalboard-midi/docs/architecture.md`](https://github.com/pedalboard/pedalboard-midi/blob/main/docs/architecture.md)

## PE Data Flow

```mermaid
sequenceDiagram
    participant CLI as pedalboard-cli
    participant Bridge as bridge (CM5)
    participant FW as firmware (RP2040)
    participant Flash as flash storage

    CLI->>Bridge: WebSocket /raw
    CLI->>Bridge: PE Set Property (postcard preset)
    Bridge->>FW: JACK MIDI out → USB
    FW->>FW: deserialize Preset
    FW->>Flash: save_one(idx, data)
    FW->>FW: update pe_config
    FW->>Bridge: USB → JACK MIDI in
    Bridge->>CLI: WebSocket ACK

    Note over FW: On boot
    Flash->>FW: load_all() → pe_config
    
    Note over FW: On button press
    FW->>FW: PeHandler.handle_events()
    FW->>FW: led_state() → LED rings
    FW->>Bridge: USB → JACK MIDI (CC/Note/PC)
```

## Module Dependency

```mermaid
graph TD
    PROTOCOL[midi-controller<br/>Config · Actions · PE framing]
    
    MIDI_FW[pedalboard-midi<br/>Firmware]
    CLI_APP[pedalboard-cli<br/>YAML → PE upload]
    SIM_APP[pedalboard-sim<br/>Virtual pedalboard]
    BRIDGE_APP[pedalboard-bridge<br/>JACK MIDI + WebSocket + mod-host]

    MIDI_FW --> PROTOCOL
    CLI_APP --> PROTOCOL
    SIM_APP --> PROTOCOL
    BRIDGE_APP -.->|JACK MIDI| MIDI_FW
    CLI_APP -->|WebSocket| BRIDGE_APP
```
