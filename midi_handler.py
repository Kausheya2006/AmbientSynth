import mido
import time

class MidiKeyboard:
    def __init__(self):
        print("[MIDI] Scanning for devices...")
        self.ports = mido.get_input_names()
        
        if not self.ports:
            raise Exception("No MIDI keyboards found! Plug one in.")
            
        # Default to the first keyboard found
        self.target_port = self.ports[0]
        print(f"[MIDI] Connected to: {self.target_port}")

    def listen(self, on_press, on_release, should_continue=lambda: True):
        """
        Opens the port and listens forever. 
        on_press and on_release are functions passed in from main.py
        """
        print(f"\n[READY] Listening for input on {self.target_port}...\n")
        
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