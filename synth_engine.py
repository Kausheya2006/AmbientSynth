import fluidsynth
import threading

class AmbientSynth:
    def __init__(self, soundfont_path):
        print("[Audio] Booting FluidSynth...")
        
        self.soundfont_path = soundfont_path
        self._lock = threading.Lock()
        self.live_controls = {
            "volume": 112,       # CC7
            "expression": 118,   # CC11
            "sustain": 110,      # CC64
            "release": 96,       # CC72
            "reverb_send": 84,   # CC91
            "chorus_send": 30,   # CC93
        }
        self._init_synth()

    def _init_synth(self):
        """Initialize synth properly (single source of truth)."""
        self.fs = fluidsynth.Synth()

        # Tone shaping before audio start (prevents clipping and harsh artifacts)
        self.fs.setting("synth.gain", 0.45)

        self.fs.setting("synth.reverb.active", 1)
        self.fs.setting("synth.reverb.room-size", 0.88)
        self.fs.setting("synth.reverb.damp", 0.55)
        self.fs.setting("synth.reverb.width", 0.9)
        self.fs.setting("synth.reverb.level", 0.33)

        self.fs.setting("synth.chorus.active", 1)
        self.fs.setting("synth.chorus.nr", 2)
        self.fs.setting("synth.chorus.speed", 0.3)
        self.fs.setting("synth.chorus.depth", 4.0)
        self.fs.setting("synth.chorus.level", 0.08)

        # Start audio engine
        self.fs.start(driver="coreaudio")

        # Load soundfont
        self.sfid = self.fs.sfload(self.soundfont_path)
        self.fs.program_select(0, self.sfid, 0, 0)

        self._apply_live_controls()

        print("[Audio] Synth ready.")

    def _apply_live_controls(self):
        """Apply runtime-tweakable MIDI controls."""
        self.fs.cc(0, 7, self.live_controls["volume"])
        self.fs.cc(0, 11, self.live_controls["expression"])
        self.fs.cc(0, 64, self.live_controls["sustain"])
        self.fs.cc(0, 72, self.live_controls["release"])
        self.fs.cc(0, 91, self.live_controls["reverb_send"])
        self.fs.cc(0, 93, self.live_controls["chorus_send"])

    def set_live_control(self, name, value):
        """Set one runtime control (0-127) and apply immediately."""
        if name not in self.live_controls:
            raise ValueError(f"Unknown control: {name}")

        value = max(0, min(127, int(value)))
        self.live_controls[name] = value

        cc_map = {
            "volume": 7,
            "expression": 11,
            "sustain": 64,
            "release": 72,
            "reverb_send": 91,
            "chorus_send": 93,
        }

        with self._lock:
            self.fs.cc(0, cc_map[name], value)

    def play_note(self, note, velocity=110):
        # Keep dynamic range: avoid forcing every note to a hard strike.
        velocity = max(35, min(118, velocity))
        with self._lock:
            self.fs.noteon(0, note, velocity)

    def stop_note(self, note):
        with self._lock:
            self.fs.noteoff(0, note)

    def reload(self):
        """Proper full reload."""
        print("[Audio] Reloading synth...")

        try:
            with self._lock:
                self.fs.delete()
        except Exception:
            pass  # avoid crash if already deleted

        self._init_synth()

        print("[Audio] Synth fully reloaded.")

    def cleanup(self):
        """Shutdown safely."""
        try:
            with self._lock:
                self.fs.cc(0, 64, 0)
                self.fs.delete()
        except Exception:
            pass
        print("[Audio] Engine shut down.")