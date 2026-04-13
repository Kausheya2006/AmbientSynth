import mido
import time


def _color(msg, code="36"):
    return f"\033[{code}m{msg}\033[0m"

class MidiKeyboard:
    def __init__(self):
        print(_color("[MIDI] Scanning for devices...", "96"))
        self.ports = mido.get_input_names()
        
        if not self.ports:
            raise Exception("No MIDI keyboards found! Plug one in.")
            
        # Default to the first keyboard found
        self.target_port = self.ports[0]
        print(_color(f"[MIDI] Connected to: {self.target_port}", "92"))

    def validate_connection(self):
        """Validate that the selected MIDI input can actually be opened."""
        try:
            with mido.open_input(self.target_port):
                pass
        except Exception as exc:
            raise Exception(f"Unable to open MIDI input '{self.target_port}': {exc}") from exc

    def listen(self, on_press, on_release, should_continue=lambda: True, on_error=None):
        """
        Opens the port and listens forever. 
        on_press and on_release are functions passed in from main.py
        """
        print(_color(f"\n[READY] Listening for input on {self.target_port}...\n", "94"))
        
        try:
            with mido.open_input(self.target_port) as inport:
                while should_continue():
                    for msg in inport.iter_pending():
                        if msg.type == 'note_on':
                            if msg.velocity > 0:
                                # Call the function provided by main.py
                                on_press(msg.note, msg.velocity)
                            else:
                                on_release(msg.note)

                        elif msg.type == 'note_off':
                            on_release(msg.note)

                    time.sleep(0.005)
        except Exception as exc:
            print(_color(f"[MIDI] Listen error on '{self.target_port}': {exc}", "91"))
            if on_error:
                on_error(exc)