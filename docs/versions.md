# Version Notes

## v0.0.0

- Initial public baseline of the lightweight synth project.
- Core app structure separated into `main.py`, `midi_handler.py`, and `synth_engine.py`.
- YDP Grand Piano SoundFont workflow introduced (`piano.sf2` in project root).

## v0.0.1
- Terminal live-control panel expanded and stabilized.
- Added controls for sustain, soft pedal, release, reverb send, chorus send, expression, and volume.
- Added preset switching from terminal keys (`1` ambient, `2` studio, `3` cinematic).
- Added runtime reload key (`r`) and safer synth reset paths for reload/cleanup.
- Added velocity curve shaping and velocity-based brightness control.
- Retuned default voicing for cleaner piano tone (less muddy/harsh).
- README updated with setup, controls, and SoundFont attribution details.

## v0.0.2
- Added persistent ASCII banner rendering inside the live terminal UI.
- Added larger recording animation with clearer REC and PAUSED states.
- Added realtime output activity histogram bars (L/R) that respond while playing.
- Kept named take export in `recordings/` as `.mid` by default.

## v0.0.3
- Added OS-based FluidSynth backend selection defaults (`coreaudio`, `pulseaudio`, `dsound`, fallback `alsa`).
- Added backend fallback attempts when preferred audio driver is not available.
- Added clearer audio startup logs for detected OS and selected driver.
- Added MIDI input connection preflight validation before control panel launch.
- Added listener-start failure handling so startup exits with clear errors instead of opening UI.
- Fixed terminal UI slider rendering to avoid `_curses.error` on narrow terminals.
