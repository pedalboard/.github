# Software Architecture

## System Overview

```mermaid
graph TB
    subgraph "Dev Machine"
        YAML[YAML Presets]
        CLI[pedalboard-cli]
        YAML --> CLI
    end

    subgraph "CM5 (Raspberry Pi)"
        BRIDGE[pedalboard-bridge<br/>Go · WebSocket↔MIDI]
    end

    subgraph "RP2040 (Firmware)"
        USB[USB MIDI]
        UART[DIN MIDI]
        PE[PE Handler<br/>Actions · LEDs · State]
        OD[OpenDeck<br/>SysEx · Web UI]
        FLASH[Flash Storage<br/>Preset Persistence]
        DISP[Display Task<br/>SSD1327 × 2]
        LEDS[LED Writer<br/>WS2812 × 98]
        INPUT[Input Polling<br/>Buttons · Encoders · ADC]
    end

    CLI -->|WebSocket| BRIDGE
    BRIDGE -->|Raw MIDI| USB
    USB --> PE
    USB --> OD
    INPUT --> PE
    INPUT --> OD
    PE --> USB
    PE --> UART
    PE --> LEDS
    PE --> DISP
    PE --> FLASH
    OD --> USB
    OD --> LEDS
    FLASH --> PE
```

## Firmware Internals

> Task architecture, state machines, and storage details live in the firmware repo:
> [`pedalboard-midi/docs/architecture.md`](https://github.com/opendeckproject/pedalboard-midi/blob/main/docs/architecture.md)

## PE Data Flow

```mermaid
sequenceDiagram
    participant CLI as pedalboard-cli
    participant Bridge as bridge (CM5)
    participant FW as firmware (RP2040)
    participant Flash as flash storage

    CLI->>Bridge: WebSocket /raw
    CLI->>Bridge: PE Set Property (postcard preset)
    Bridge->>FW: USB MIDI SysEx
    FW->>FW: deserialize Preset
    FW->>Flash: save_one(idx, data)
    FW->>FW: update pe_config
    FW->>Bridge: PE Set Reply (ACK)
    Bridge->>CLI: WebSocket ACK

    Note over FW: On boot
    Flash->>FW: load_all() → pe_config
    
    Note over FW: On button press
    FW->>FW: PeHandler.handle_events()
    FW->>FW: led_state() → LED rings
    FW->>Bridge: USB MIDI (CC/Note/PC)
```

## Module Dependency

```mermaid
graph TD
    PROTOCOL[midi-controller<br/>Config · Actions · PE framing]
    OPENDECK[opendeck<br/>SysEx protocol · Config]
    
    MIDI_FW[pedalboard-midi<br/>Firmware]
    CLI_APP[pedalboard-cli<br/>YAML → PE upload]
    BRIDGE_APP[pedalboard-bridge<br/>WebSocket↔MIDI]

    MIDI_FW --> PROTOCOL
    MIDI_FW --> OPENDECK
    CLI_APP --> PROTOCOL
    BRIDGE_APP -.->|raw passthrough| MIDI_FW
```


