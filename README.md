# Ambient Synth

A lightweight terminal-based piano synthesizer for MIDI keyboards, built with Python and FluidSynth.

This project focuses on simple setup, low overhead, and live sound control while you play.

## Version

Current version: v0.0.2

## What Is Included in v0.0.2

- Real-time terminal control panel
- Live parameter updates without restarting the app
- Preset switching from the keyboard
- Soft pedal support
- Velocity curve for more natural playing response
- Velocity-dependent brightness shaping
- Safer reload and cleanup flow to reduce stuck notes
- Cleaner default piano voicing with reduced mud/harshness

## Features

- MIDI keyboard input via mido and python-rtmidi
- FluidSynth rendering with SoundFont playback
- Live controls for:
	- sustain pedal
	- soft pedal
	- release
	- reverb send
	- chorus send
	- expression
	- volume
- Presets:
	- ambient
	- studio
	- cinematic
- Reload key to reinitialize synth safely

## Project Layout

- main.py: app entry point and terminal UI
- midi_handler.py: MIDI device detection and event loop
- synth_engine.py: synth engine, presets, and runtime controls
- piano.sf2: SoundFont file (not tracked in git)

## SoundFont Used

YDP Grand Piano

- Version: 2016-08-04
- Built from the Zenph Studios Yamaha Disklavier Pro Piano multisamples for OLPC
- SoundFont and sample modifications produced by roberto@zenvoid.org for the FreePats project

Samples from the OLPC sound sample library were donated to Dr. Richard Boulanger at cSounds.com to support OLPC developers, students, XO users, and computer/electronic musicians.

The Disklavier Pro includes an internally controlled mechanism for precise performance capture. Original samples were performed by computer and recorded for OLPC by Dr. Mikhail Krishtal, Director of Music Research and Production, and the Zenph Studios team.

License: Creative Commons Attribution 3.0

Download:

- Source page: https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html
- Sound bank format: SF2
- Size: 36 MiB

Prepare piano.sf2:

1. Download the SF2 sound bank from the source page.
2. Extract it if it comes as an archive.
3. Rename the extracted file to piano.sf2.
4. Place piano.sf2 in the project root (same folder as main.py).

Note: Keep piano.sf2 out of git tracking to avoid GitHub file size limits.

## Requirements

- Python 3.10 or newer
- MIDI keyboard/controller
- FluidSynth installed on the system

macOS with Homebrew:

```bash
brew install fluid-synth
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pyfluidsynth mido python-rtmidi
```

## Run

```bash
python3 main.py
```

Or with explicit virtual environment interpreter:

```bash
.venv/bin/python main.py
```

## Terminal Controls

When the app starts, the control panel opens in the terminal.

- Up/Down: select parameter
- Left/Right: change value
- 1: ambient preset
- 2: studio preset
- 3: cinematic preset
- r: reload synth
- q: quit

All parameter changes are applied live.

## Troubleshooting

No MIDI keyboard found:

- reconnect the device
- confirm the OS detects it
- restart the app

No sound:

- check system output device and volume
- confirm piano.sf2 is present in the project root
- confirm FluidSynth is installed

Import errors for fluidsynth or mido:

- activate the virtual environment
- reinstall dependencies:

```bash
pip install --upgrade pyfluidsynth mido python-rtmidi
```
