import keyboard
from audiomixer import AudioMixer
from sound import Sound

class SoundboardApp:
    def __init__(self, mixer: AudioMixer):
        self.mixer = mixer
        self.sounds = {}

    def bind_sound(self, hotkey: str, sound: Sound):
        self.sounds[hotkey] = sound
        keyboard.add_hotkey(hotkey, lambda: self.mixer.play_sound(self.sounds[hotkey]))

    def run(self):
        self.mixer.start()
        keyboard.wait('esc')

if __name__ == "__main__":
    mixer = AudioMixer(input_id=0, output_id=1)
    app = SoundboardApp(mixer)