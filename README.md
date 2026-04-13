# Ambient Synth

A lightweight terminal-based piano synthesizer for MIDI keyboards, built with Python and FluidSynth.

This project focuses on simple setup, low overhead, and live sound control while you play.

## Version

Current version: v0.0.3

## What Is Included in v0.0.3

- Dynamic audio backend selection by OS (CoreAudio/PulseAudio/DirectSound defaults)
- Audio driver fallback attempts when preferred backend is unavailable
- Clear startup logs for detected OS and selected audio backend
- MIDI connection preflight validation before launching control panel
- Fail-fast startup behavior with user-friendly error and hint messages
- Terminal slider rendering made width-safe to avoid curses crashes on small windows

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
- Record and export MIDI takes


## Project Layout

- main.py: app entry point and terminal UI
- midi_handler.py: MIDI device detection and event loop
- synth_engine.py: synth engine, presets, and runtime controls
- piano.sf2: SoundFont file (not tracked in git)

## Setup SoundFont

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

## Want to Contribute?

Contributions are welcome! If you have ideas for improvements, bug fixes, or new features, please open an issue or submit a pull request.

## SoundFont Attribution

This project uses the **YDP Grand Piano** SoundFont from the FreePats project.

- Source: https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html
- License: Creative Commons Attribution 3.0 (CC BY 3.0)
- Author: FreePats (zenvoid.org)

Original samples are based on recordings from Zenph Studios and adapted for FreePats.

## LICENSE

This project is licensed under the MIT License. See the LICENSE file for details.

