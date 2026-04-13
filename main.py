import sys
import threading
import curses
import time
import os
from datetime import datetime
import mido
from synth_engine import AmbientSynth
from midi_handler import MidiKeyboard


ASCII_BANNER = r"""
    _              _     _            _       ____              _   _
   / \   _ __ ___ | |__ (_) ___ _ __ | |_    / ___| _   _ _ __ | |_| |__
  / _ \ | '_ ` _ \| '_ \| |/ _ \ '_ \| __|___\___ \| | | | '_ \| __| '_ \
 / ___ \| | | | | | |_) | |  __/ | | | ||_____|__) | |_| | | | | |_| | | |
/_/   \_\_| |_| |_|_.__/|_|\___|_| |_|\__|   |____/ \__, |_| |_|\__|_| |_|
                                                    |___/
"""
BANNER_LINES = [line.rstrip() for line in ASCII_BANNER.strip("\n").splitlines()]


def print_startup_banner():
    print("\033[96m" + ASCII_BANNER + "\033[0m")
    print()


def _draw_slider(stdscr, row, label, value, selected, width=26):
    _, max_x = stdscr.getmaxyx()

    # Keep a safe right margin so tiny terminals don't throw curses ERR.
    max_bar_width = max(8, max_x - 36)
    width = max(8, min(width, max_bar_width))

    filled = int((value / 127.0) * width)
    bar = "#" * filled + "-" * (width - filled)
    marker = ">" if selected else " "
    attr = curses.color_pair(4) if selected else curses.color_pair(2)
    line = f"{marker} {label:<22} [{bar}] {value:>3}"
    _safe_addstr(stdscr, row, 2, line[: max(0, max_x - 3)], attr)


def _safe_addstr(stdscr, y, x, text, attr=0):
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        # Tiny terminals can throw when writing near borders.
        pass


class SessionRecorder:
    def __init__(self):
        self._lock = threading.Lock()
        self.recording = False
        self.paused = False
        self.events = []
        self._start_time = None
        self._last_time = None

    def start(self):
        with self._lock:
            now = time.monotonic()
            self.events = []
            self.recording = True
            self.paused = False
            self._start_time = now
            self._last_time = now

    def stop(self):
        with self._lock:
            self.recording = False
            self.paused = False

    def pause(self):
        with self._lock:
            if self.recording:
                self.paused = True

    def resume(self):
        with self._lock:
            if self.recording and self.paused:
                self.paused = False
                self._last_time = time.monotonic()

    def _delta(self):
        now = time.monotonic()
        delta = now - self._last_time
        self._last_time = now
        return max(0.0, delta)

    def add_note_on(self, note, velocity):
        with self._lock:
            if not self.recording or self.paused:
                return
            self.events.append((self._delta(), mido.Message("note_on", note=note, velocity=velocity, channel=0)))

    def add_note_off(self, note):
        with self._lock:
            if not self.recording or self.paused:
                return
            self.events.append((self._delta(), mido.Message("note_off", note=note, velocity=0, channel=0)))

    def add_control_change(self, control, value):
        with self._lock:
            if not self.recording or self.paused:
                return
            self.events.append((
                self._delta(),
                mido.Message("control_change", control=int(control), value=max(0, min(127, int(value))), channel=0),
            ))

    def event_count(self):
        with self._lock:
            return len(self.events)

    def _default_path(self, ext=".mid"):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"recordings/take_{stamp}{ext}"

    def _ensure_parent_dir(self, out_path):
        out_dir = os.path.dirname(out_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    def export_midi(self, out_path=None):
        with self._lock:
            if not self.events:
                return None

            ticks_per_beat = 480
            tempo = 500000
            mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
            track = mido.MidiTrack()
            mid.tracks.append(track)
            track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))

            for delta_seconds, message in self.events:
                ticks = int(mido.second2tick(delta_seconds, ticks_per_beat, tempo))
                msg = message.copy(time=max(0, ticks))
                track.append(msg)

            if out_path is None:
                out_path = self._default_path(".mid")

            self._ensure_parent_dir(out_path)

            mid.save(out_path)
            return out_path

    def export_named_take(self, take_name=""):
        # Save named takes only in recordings/, always as .mid.
        cleaned = take_name.strip().replace("/", "_").replace("\\", "_")
        if not cleaned:
            return self.export_midi()

        if not cleaned.lower().endswith(".mid"):
            cleaned += ".mid"

        out_path = os.path.join("recordings", cleaned)
        return self.export_midi(out_path)


class LiveActivityMeter:
    """Tracks realtime note activity for a simple CLI level meter."""

    def __init__(self):
        self._lock = threading.Lock()
        self._active_notes = {}
        self._level = 0.0
        self._last_update = time.monotonic()

    def note_on(self, note, velocity):
        with self._lock:
            self._active_notes[int(note)] = max(1, min(127, int(velocity)))

    def note_off(self, note):
        with self._lock:
            self._active_notes.pop(int(note), None)

    def level(self):
        with self._lock:
            now = time.monotonic()
            dt = max(0.001, now - self._last_update)
            self._last_update = now

            if self._active_notes:
                peak = max(self._active_notes.values()) / 127.0
                target = min(1.0, 0.25 + peak * 0.85)
                attack = min(1.0, dt * 18.0)
                self._level += (target - self._level) * attack
            else:
                release = min(1.0, dt * 5.5)
                self._level += (0.0 - self._level) * release

            self._level = max(0.0, min(1.0, self._level))
            return self._level


def _draw_activity_meter(stdscr, row, label, level, width=44):
    filled = int(width * max(0.0, min(1.0, level)))
    _safe_addstr(stdscr, row, 2, f"{label:<12}", curses.color_pair(2) | curses.A_BOLD)

    for i in range(width):
        if i < filled:
            if i < int(width * 0.7):
                attr = curses.color_pair(3) | curses.A_BOLD
            elif i < int(width * 0.9):
                attr = curses.color_pair(6) | curses.A_BOLD
            else:
                attr = curses.color_pair(5) | curses.A_BOLD
            ch = "#"
        else:
            attr = curses.color_pair(2)
            ch = "-"
        _safe_addstr(stdscr, row, 15 + i, ch, attr)

    _safe_addstr(stdscr, row, 15 + width + 2, f"{int(level * 100):>3}%", curses.color_pair(2))


def _prompt_take_name(stdscr):
    h, _ = stdscr.getmaxyx()
    prompt = "Take name (saved in recordings/, .mid): "
    _safe_addstr(stdscr, h - 2, 2, " " * 120, curses.color_pair(2))
    _safe_addstr(stdscr, h - 2, 2, prompt, curses.color_pair(3) | curses.A_BOLD)
    stdscr.refresh()

    curses.echo()
    curses.curs_set(1)
    stdscr.nodelay(False)
    stdscr.timeout(-1)
    try:
        value = stdscr.getstr(h - 2, len(prompt) + 2, 200)
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore").strip()
        return str(value).strip()
    finally:
        curses.noecho()
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(100)


def run_terminal_controls(synth, recorder, meter):
    controls = [
        ("sustain", "Sustain Pedal"),
        ("soft_pedal", "Soft Pedal"),
        ("release", "Release Time"),
        ("reverb_send", "Reverb Send"),
        ("chorus_send", "Chorus Send"),
        ("expression", "Expression"),
        ("volume", "Volume"),
    ]

    def _panel(stdscr):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)    # title
        curses.init_pair(2, curses.COLOR_WHITE, -1)   # normal text
        curses.init_pair(3, curses.COLOR_GREEN, -1)   # help/status
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)  # selected row
        curses.init_pair(5, curses.COLOR_RED, -1)     # recording
        curses.init_pair(6, curses.COLOR_YELLOW, -1)  # warning/info

        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(100)
        selected = 0
        status = "Ready"
        rec_anim = ["[=   ]", "[==  ]", "[=== ]", "[====]", "[ ===]", "[  ==]", "[   =]"]
        rec_big = [
            "[●      ]",
            "[●●     ]",
            "[●●●    ]",
            "[●●●●   ]",
            "[ ●●●●  ]",
            "[  ●●●  ]",
            "[   ●●  ]",
            "[    ●  ]",
        ]
        frame = 0

        while True:
            stdscr.erase()
            for i, line in enumerate(BANNER_LINES):
                _safe_addstr(stdscr, 1 + i, 2, line, curses.color_pair(1) | curses.A_BOLD)

            base_row = 1 + len(BANNER_LINES) + 1
            _safe_addstr(stdscr, base_row, 2, "Ambient-Synth Console", curses.color_pair(1) | curses.A_BOLD)
            _safe_addstr(stdscr, base_row + 1, 2, "Arrows=Adjust  1/2/3=Preset  r=Reload  space=Rec  p=Pause  e=Export  q=Quit", curses.color_pair(3))

            if recorder.recording:
                if recorder.paused:
                    _safe_addstr(stdscr, base_row + 2, 2, f"PAUSED [ |||||| ]  events={recorder.event_count()}", curses.color_pair(6) | curses.A_BOLD)
                else:
                    rec_text = f"REC {rec_big[frame % len(rec_big)]} {rec_anim[frame % len(rec_anim)]}  events={recorder.event_count()}"
                    _safe_addstr(stdscr, base_row + 2, 2, rec_text, curses.color_pair(5) | curses.A_BOLD)
                    frame += 1
            else:
                _safe_addstr(stdscr, base_row + 2, 2, f"IDLE  events={recorder.event_count()}", curses.color_pair(6))

            current_level = meter.level()
            _draw_activity_meter(stdscr, base_row + 3, "Output L", current_level)
            _draw_activity_meter(stdscr, base_row + 4, "Output R", current_level * 0.96)

            for i, (key, label) in enumerate(controls):
                value = synth.live_controls[key]
                _draw_slider(stdscr, base_row + 6 + i, label, value, selected == i)

            _safe_addstr(stdscr, base_row + 14, 2, f"Status: {status}", curses.color_pair(2))

            stdscr.refresh()
            key = stdscr.getch()

            if key == -1:
                continue

            if key in (ord("q"), ord("Q")):
                return
            if key == ord(" "):
                if recorder.recording:
                    recorder.stop()
                    status = "Recording stopped"
                else:
                    recorder.start()
                    status = "Recording started"
                continue
            if key in (ord("p"), ord("P")):
                if not recorder.recording:
                    status = "Start recording first"
                elif recorder.paused:
                    recorder.resume()
                    status = "Recording resumed"
                else:
                    recorder.pause()
                    status = "Recording paused"
                continue
            if key in (ord("e"), ord("E")):
                take_name = _prompt_take_name(stdscr)
                out_path = recorder.export_named_take(take_name)
                status = f"Exported: {out_path}" if out_path else "No events to export"
                continue
            if key == ord("1"):
                synth.apply_preset("ambient")
                for control, value in synth.PRESETS["ambient"].items():
                    recorder.add_control_change(synth.CC_MAP[control], value)
                status = "Preset: ambient"
                continue
            if key == ord("2"):
                synth.apply_preset("studio")
                for control, value in synth.PRESETS["studio"].items():
                    recorder.add_control_change(synth.CC_MAP[control], value)
                status = "Preset: studio"
                continue
            if key == ord("3"):
                synth.apply_preset("cinematic")
                for control, value in synth.PRESETS["cinematic"].items():
                    recorder.add_control_change(synth.CC_MAP[control], value)
                status = "Preset: cinematic"
                continue
            if key in (ord("r"), ord("R")):
                synth.reload()
                status = "Synth reloaded"
                continue
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(controls)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(controls)
            elif key == curses.KEY_LEFT:
                ctrl_key = controls[selected][0]
                synth.set_live_control(ctrl_key, synth.live_controls[ctrl_key] - 2)
                recorder.add_control_change(synth.CC_MAP[ctrl_key], synth.live_controls[ctrl_key])
                status = f"{ctrl_key}={synth.live_controls[ctrl_key]}"
            elif key == curses.KEY_RIGHT:
                ctrl_key = controls[selected][0]
                synth.set_live_control(ctrl_key, synth.live_controls[ctrl_key] + 2)
                recorder.add_control_change(synth.CC_MAP[ctrl_key], synth.live_controls[ctrl_key])
                status = f"{ctrl_key}={synth.live_controls[ctrl_key]}"

    curses.wrapper(_panel)

def main():
    print_startup_banner()

    # 1. Initialize our modules
    soundfont_file = "piano.sf2" # Make sure this file is in your folder!
    
    try:
        synth = AmbientSynth(soundfont_file)
        keyboard = MidiKeyboard()
        keyboard.validate_connection()
    except Exception as e:
        print(f"\033[91mStartup Error:\033[0m {e}")
        print("\033[93m[Hint]\033[0m Connect your MIDI device and retry.")
        sys.exit(1)

    recorder = SessionRecorder()
    meter = LiveActivityMeter()

    # 2. Define the bridge functions
    def handle_note_press(note, velocity):
        # You could add visual CLI print statements here later!
        synth.play_note(note, velocity)
        recorder.add_note_on(note, velocity)
        meter.note_on(note, velocity)

    def handle_note_release(note):
        synth.stop_note(note)
        recorder.add_note_off(note)
        meter.note_off(note)

    running = True
    startup_midi_error = {"error": None}

    def _midi_error_callback(exc):
        startup_midi_error["error"] = exc

    # 3. Start MIDI listener in background and keep terminal free for live sliders
    midi_thread = threading.Thread(
        target=keyboard.listen,
        kwargs={
            "on_press": handle_note_press,
            "on_release": handle_note_release,
            "should_continue": lambda: running,
            "on_error": _midi_error_callback,
        },
        daemon=True,
    )
    midi_thread.start()

    # Fail before showing the control panel if listener can't open/connect.
    time.sleep(0.15)
    if startup_midi_error["error"] is not None:
        running = False
        midi_thread.join(timeout=1.0)
        print(f"\033[91mStartup Error:\033[0m MIDI listener failed: {startup_midi_error['error']}")
        print("\033[93m[Hint]\033[0m Verify MIDI cable/power and selected device in OS MIDI settings.")
        synth.cleanup()
        sys.exit(1)

    try:
        run_terminal_controls(synth, recorder, meter)
    except KeyboardInterrupt:
        print("\n> Ctrl+C detected. Shutting down gracefully...")
    finally:
        running = False
        midi_thread.join(timeout=1.0)
        # Always clean up the audio engine so it doesn't crash the OS audio daemon
        synth.cleanup()

if __name__ == "__main__":
    main()