# Open Pedalboard Hardware and Software Platform

![Logo](img/pedalboard-logo-large.png)

An open source platform for building pedalboard components.

More and more pedalboards are having components that offer MIDI capabilities. However, reality shows that they are often incompatible
or require some additional processing. 

There are many commercial products around which offer MIDI foot controller capablities. However these are often expensive solutions.
Also due to chip shortage smaller suppliers of such (very good) solutions are out of stock.

Given the low technical complexity of building a MIDI foot controller: an open source hard- and software platform could solve many
of these issues in a pretty simple way. 

But wait. Does it have to stop there? Wouldn't it be great to also add some Audio Processing Unit inside the box? 
That would open endless possibilities for custom stomp boxes and pedalboards.

This is not a new idea, there are some projects and platforms already around. But this project is different to most of them because it aims to be:

- completely Free & Open Source (hardware and software) GPL Licensed
- modular: if you only want MIDI, you can just not add the audio processing units. This also has some reliability advantages. Even with problems on the audio system, the Midi controller will still work independently. 
- builder friendly (can be produced with simple tools available nearly everywhere)
- re-use popular hardware modules that can be purchased worldwide.
- the form factor of the hardware is slightly bigger than most of the other projects allowing for more controllers and more processing power. The design is targeting a 180x120x35mm box.
- less than a concrete product, this project offers a platform to build pedals on top.
- the goal ist to build a useful tool for life performance, its not intended to be a playground to fiddle around on stage.

## Discussion

Please join us on the [community Discord server](https://discord.gg/ncyKyryHAc).

## Architecture

As mentioned above hardware architecture is modular. There are two independen processors for the MIDI processing and the Audio processing. They are connected over USB-MIDI.

![Architecture Overview](diagram/architecture.drawio.svg)

### Hardware Components

| Component                                                         | Description                                         | Image |
|-------------------------------------------------------------------|-----------------------------------------------------|-------|
| [Main Boaard](https://github.com/pedalboard/pedalboard-hw)        | Carrier for other modules and Midi Controller       | ![30 deg View](https://pedalboard.github.io/pedalboard-hw-site/latest/3D/pedalboard-hw-3D_blender_30deg.png)  |
| [Sound Card](https://github.com/pedalboard/pedalboard-soundcard)  | ADC / DAC board                                     | ![30 deg View](https://pedalboard.github.io/pedalboard-soundcard-site/latest/3D/pedalboard-soundcard-3D_blender_30deg.png)       |
| [RGB LED Ring](https://github.com/pedalboard/pedalboard-led-ring) | RGB LED ring around foot button                     |<img src="https://github.com/pedalboard/pedalboard-led-ring-site/blob/main/latest/3D/pedalboard-led-ring-3D_blender_30deg.png"  alt="led-ring" height="150">     |
| [Mechanical Parts](https://github.com/pedalboard/pedalboard-case) | 3D printable mechanical parts for building the case |       |     


## Radically Open Source
The Open Pedalboard Platform is fully Open Source. That means everything you need to build or modify the machine can be found on this GitHub page. All tools that are used are also Open Source: 
- [KiCad](https://www.kicad.org) to design the PCBs
- [OpenSCAD](https://openscad.org/) to design 3d printable parts
- [LumenPnP](https://www.opulo.io/) to assemble the PCBs
- [Rust](https://www.rust-lang.org/) to develop the MIDI controller firmware
- [ELK audio OS](https://www.elk.audio/how-elk-audio-os-works) as real-time audio processor

Without all these tools, also this project would not be possible. Great thanks to all contributors!


