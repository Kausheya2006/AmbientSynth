import fluidsynth
import threading
import os
import sys


def _color(msg, code="36"):
    return f"\033[{code}m{msg}\033[0m"

class AmbientSynth:
    CC_MAP = {
        "volume": 7,
        "expression": 11,
        "sustain": 64,
        "release": 72,
        "reverb_send": 91,
        "chorus_send": 93,
        "soft_pedal": 67,
    }

    PRESETS = {
        "ambient": {"reverb_send": 82, "chorus_send": 6, "sustain": 98, "release": 88},
        "studio": {"reverb_send": 44, "chorus_send": 0, "sustain": 84, "release": 72},
        "cinematic": {"reverb_send": 102, "chorus_send": 16, "sustain": 108, "release": 96},
    }

    def __init__(self, soundfont_path, preferred_driver=None):
        print(_color("[Audio] Booting FluidSynth...", "96"))
        
        self.soundfont_path = soundfont_path
        self.preferred_driver = preferred_driver or os.environ.get("AMBIENT_SYNTH_AUDIO_DRIVER")
        self.active_driver = None
        self._lock = threading.Lock()
        self.velocity_curve_exp = 1.5
        self.live_controls = {
            "volume": 108,       # CC7
            "expression": 112,   # CC11
            "sustain": 88,       # CC64
            "release": 78,       # CC72
            "reverb_send": 60,   # CC91
            "chorus_send": 0,    # CC93
            "soft_pedal": 0,     # CC67
        }
        self._init_synth()

    def _default_audio_driver(self):
        # Simple OS-based driver mapping.
        if sys.platform == "darwin":
            return "coreaudio"
        if sys.platform.startswith("linux"):
            return "pulseaudio"
        if sys.platform == "win32":
            return "dsound"
        return "alsa"

    def _start_audio_engine(self):
        preferred = (self.preferred_driver or self._default_audio_driver()).strip()
        print(_color(f"[Audio] OS detected: {sys.platform} | preferred driver: {preferred}", "96"))
        fallback_map = {
            "coreaudio": ["portaudio", "pulseaudio", "alsa"],
            "pulseaudio": ["alsa", "jack", "portaudio"],
            "dsound": ["wasapi", "winmme", "portaudio"],
            "alsa": ["pulseaudio", "jack", "portaudio"],
        }

        candidates = [preferred] + fallback_map.get(preferred, ["portaudio", "pulseaudio", "alsa"])

        attempted = []
        for driver in candidates:
            attempted.append(driver)
            try:
                self.fs.start(driver=driver)
                self.active_driver = driver
                print(_color(f"[Audio] Using driver: {driver}", "92"))
                return
            except Exception as exc:
                print(_color(f"[Audio] Driver '{driver}' failed: {exc}", "93"))

        joined = ", ".join(attempted)
        raise RuntimeError(f"Could not start FluidSynth audio driver. Tried: {joined}")

    def _init_synth(self):
        """Initialize synth properly (single source of truth)."""
        self.fs = fluidsynth.Synth()

        # Tone shaping before audio start (prevents clipping and harsh artifacts)
        self.fs.setting("synth.gain", 0.7)

        self.fs.setting("synth.reverb.active", 1)
        self.fs.setting("synth.reverb.room-size", 0.72)
        self.fs.setting("synth.reverb.damp", 0.68)
        self.fs.setting("synth.reverb.width", 0.85)
        self.fs.setting("synth.reverb.level", 0.22)

        self.fs.setting("synth.chorus.active", 0)
        self.fs.setting("synth.chorus.nr", 1)
        self.fs.setting("synth.chorus.speed", 0.3)
        self.fs.setting("synth.chorus.depth", 2.0)
        self.fs.setting("synth.chorus.level", 0.0)

        # Start audio engine with platform-aware fallback.
        self._start_audio_engine()

        # Load soundfont
        self.sfid = self.fs.sfload(self.soundfont_path)
        self.fs.program_select(0, self.sfid, 0, 0)

        self._apply_live_controls()

        print(_color("[Audio] Synth ready.", "92"))

    def switch_audio_driver(self, driver):
        """Switch FluidSynth backend driver and reload audio safely."""
        driver = (driver or "").strip()
        if not driver:
            raise ValueError("Driver name cannot be empty")

        self.preferred_driver = driver
        self.reload()

    def _apply_live_controls(self):
        """Apply runtime-tweakable MIDI controls."""
        self.fs.cc(0, 7, self.live_controls["volume"])
        self.fs.cc(0, 11, self.live_controls["expression"])
        self.fs.cc(0, 64, self.live_controls["sustain"])
        self.fs.cc(0, 72, self.live_controls["release"])
        self.fs.cc(0, 91, self.live_controls["reverb_send"])
        self.fs.cc(0, 93, self.live_controls["chorus_send"])
        self.fs.cc(0, 67, self.live_controls["soft_pedal"])

    def set_live_control(self, name, value):
        """Set one runtime control (0-127) and apply immediately."""
        if name not in self.live_controls:
            raise ValueError(f"Unknown control: {name}")

        value = max(0, min(127, int(value)))
        self.live_controls[name] = value

        with self._lock:
            self.fs.cc(0, self.CC_MAP[name], value)

    def apply_preset(self, name):
        """Apply one of the predefined live-control presets."""
        if name not in self.PRESETS:
            raise ValueError(f"Unknown preset: {name}")

        for control, value in self.PRESETS[name].items():
            self.set_live_control(control, value)

    def _velocity_curve(self, velocity):
        velocity = max(1, min(127, int(velocity)))
        curved = int(((velocity / 127.0) ** self.velocity_curve_exp) * 127)
        return max(1, min(127, curved))

    def _update_brightness(self, velocity):
        # Keep timbre shifts subtle to avoid brittle attacks.
        brightness = int(50 + (velocity / 127.0) * 18)
        self.fs.cc(0, 74, max(0, min(127, brightness)))

    def play_note(self, note, velocity=110):
        velocity = self._velocity_curve(velocity)
        with self._lock:
            self._update_brightness(velocity)
            self.fs.noteon(0, note, velocity)

    def stop_note(self, note):
        with self._lock:
            self.fs.noteoff(0, note)

    def reload(self):
        """Proper full reload."""
        print(_color("[Audio] Reloading synth...", "93"))

        try:
            with self._lock:
                self.fs.system_reset()
                self.fs.delete()
        except Exception:
            pass  # avoid crash if already deleted

        self._init_synth()

        print(_color("[Audio] Synth fully reloaded.", "92"))

    def cleanup(self):
        """Shutdown safely."""
        try:
            with self._lock:
                self.fs.system_reset()
                self.fs.cc(0, 64, 0)
                self.fs.delete()
        except Exception:
            pass
        print(_color("[Audio] Engine shut down.", "90"))