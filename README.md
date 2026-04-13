# Ambient-Synth

This is a small Python-based software synthesizer for playing a SoundFont piano from a MIDI keyboard.

It uses:
- FluidSynth for audio rendering
- mido + python-rtmidi for MIDI input
- a simple terminal control panel for live sound shaping

The goal is to keep it minimal and easy to tweak while playing.

## Features

- Plug in a MIDI keyboard and play immediately
- Ambient piano voicing based on a SoundFont (`piano.sf2`)
- Live terminal sliders (no restart needed)
- Runtime controls for:
	- sustain pedal amount
	- release time
	- reverb send
	- chorus send
	- expression
	- volume

## Project Layout

- `main.py`: app entry point and terminal slider UI
- `midi_handler.py`: MIDI device detection and note event loop
- `synth_engine.py`: FluidSynth engine and sound control logic
- `piano.sf2`: SoundFont file used by the synth

## SoundFont Used

This project uses the **YDP Grand Piano** SoundFont from the FreePats project.

- Source: https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html
- License: Creative Commons Attribution 3.0 (CC BY 3.0)

Original samples are based on recordings from Zenph Studios and were adapted for FreePats by Roberto at zenvoid.org.

### Download and Prepare piano.sf2

1. Open the source page: https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html
2. Download the SF2 sound bank (36 MiB).
3. Extract it if downloaded as an archive.
4. Rename the extracted SoundFont file to `piano.sf2`.
5. Place `piano.sf2` in the project root (same folder as `main.py`).

## Requirements

- Python 3.10+
- A connected MIDI keyboard/controller
- FluidSynth installed on your system

macOS (Homebrew):

```bash
brew install fluid-synth
```

## Setup

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pyfluidsynth mido python-rtmidi
```

## Run

```bash
python3 main.py
```

If you want to be explicit about the project virtual environment:

```bash
.venv/bin/python main.py
```

## Terminal Controls

When the app starts, a control panel opens in the terminal.

- Up/Down: select a parameter
- Left/Right: decrease/increase the selected value
- q: quit

All slider updates are applied live while you play.

## Sound Tips

- For longer note tails, increase `Sustain Pedal` and `Release Time`
- For a softer, wider tone, increase `Reverb Send` slightly
- If the sound gets muddy, lower `Reverb Send` or `Chorus Send`

## Troubleshooting

No MIDI keyboard found:
- reconnect the device and restart the app
- make sure the OS sees your MIDI controller

No sound:
- check your output device and system volume
- verify `piano.sf2` exists in the project root
- confirm FluidSynth is installed (`fluidsynth --version`)

Import errors for `fluidsynth` or `mido`:
- activate your virtual environment
- reinstall dependencies:

```bash
pip install --upgrade pyfluidsynth mido python-rtmidi
```
