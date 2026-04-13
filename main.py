import sys
import threading
import curses
from synth_engine import AmbientSynth
from midi_handler import MidiKeyboard


def _draw_slider(stdscr, row, label, value, selected, width=26):
    filled = int((value / 127.0) * width)
    bar = "#" * filled + "-" * (width - filled)
    marker = ">" if selected else " "
    stdscr.addstr(row, 2, f"{marker} {label:<22} [{bar}] {value:>3}")


def run_terminal_controls(synth):
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
        curses.curs_set(0)
        stdscr.nodelay(False)
        selected = 0

        while True:
            stdscr.erase()
            stdscr.addstr(1, 2, "Ambient Controls (live)")
            stdscr.addstr(2, 2, "UP/DOWN: select  LEFT/RIGHT: adjust  1/2/3: presets")
            stdscr.addstr(3, 2, "1=ambient  2=studio  3=cinematic  r=reload  q=quit")

            for i, (key, label) in enumerate(controls):
                value = synth.live_controls[key]
                _draw_slider(stdscr, 5 + i, label, value, selected == i)

            stdscr.refresh()
            key = stdscr.getch()

            if key in (ord("q"), ord("Q")):
                return
            if key == ord("1"):
                synth.apply_preset("ambient")
                continue
            if key == ord("2"):
                synth.apply_preset("studio")
                continue
            if key == ord("3"):
                synth.apply_preset("cinematic")
                continue
            if key in (ord("r"), ord("R")):
                synth.reload()
                continue
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(controls)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(controls)
            elif key == curses.KEY_LEFT:
                ctrl_key = controls[selected][0]
                synth.set_live_control(ctrl_key, synth.live_controls[ctrl_key] - 2)
            elif key == curses.KEY_RIGHT:
                ctrl_key = controls[selected][0]
                synth.set_live_control(ctrl_key, synth.live_controls[ctrl_key] + 2)

    curses.wrapper(_panel)

def main():
    # 1. Initialize our modules
    soundfont_file = "piano.sf2" # Make sure this file is in your folder!
    
    try:
        synth = AmbientSynth(soundfont_file)
        keyboard = MidiKeyboard()
    except Exception as e:
        print(f"Startup Error: {e}")
        sys.exit(1)

    # 2. Define the bridge functions
    def handle_note_press(note, velocity):
        # You could add visual CLI print statements here later!
        synth.play_note(note, velocity)

    def handle_note_release(note):
        synth.stop_note(note)

    running = True

    # 3. Start MIDI listener in background and keep terminal free for live sliders
    midi_thread = threading.Thread(
        target=keyboard.listen,
        kwargs={
            "on_press": handle_note_press,
            "on_release": handle_note_release,
            "should_continue": lambda: running,
        },
        daemon=True,
    )
    midi_thread.start()

    try:
        run_terminal_controls(synth)
    except KeyboardInterrupt:
        print("\n> Ctrl+C detected. Shutting down gracefully...")
    finally:
        running = False
        midi_thread.join(timeout=1.0)
        # Always clean up the audio engine so it doesn't crash the OS audio daemon
        synth.cleanup()

if __name__ == "__main__":
    main()