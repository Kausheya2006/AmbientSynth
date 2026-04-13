# Version Notes

## v0.0.0
- First local prototype.
- Basic FluidSynth piano playback from SoundFont.
- MIDI note input wiring with press/release handling.

## v0.0.1
- Initial public baseline of the lightweight synth project.
- Core app structure separated into `main.py`, `midi_handler.py`, and `synth_engine.py`.
- YDP Grand Piano SoundFont workflow introduced (`piano.sf2` in project root).

## v0.0.2
- Terminal live-control panel expanded and stabilized.
- Added controls for sustain, soft pedal, release, reverb send, chorus send, expression, and volume.
- Added preset switching from terminal keys (`1` ambient, `2` studio, `3` cinematic).
- Added runtime reload key (`r`) and safer synth reset paths for reload/cleanup.
- Added velocity curve shaping and velocity-based brightness control.
- Retuned default voicing for cleaner piano tone (less muddy/harsh).
- README updated with setup, controls, and SoundFont attribution details.
