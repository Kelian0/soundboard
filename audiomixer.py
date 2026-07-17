import sounddevice as sd
from sound import Sound

class AudioMixer:
    def __init__(self, input_id: int, output_id: int, sample_rate: int = 44100):
        self.input_id = input_id
        self.output_id = output_id
        self.sample_rate = sample_rate
        self.current_sound = None
        self.sound_pos = 0

    def play_sound(self, sound: Sound):
        self.current_sound = sound
        self.sound_pos = 0

    def _callback(self, indata, outdata, frames, time, status):
        mixed = indata[:, 0].copy()
        
        if self.current_sound:
            chunk = self.current_sound.get_chunk(self.sound_pos, frames)
            chunk_len = len(chunk)
            
            if chunk_len > 0:
                mixed[:chunk_len] += chunk
                self.sound_pos += chunk_len
            else:
                self.current_sound = None
                
        outdata[:, 0] = mixed
        if outdata.shape[1] > 1:
            outdata[:, 1] = mixed

    def start(self):
        self.stream = sd.Stream(
            device=(self.input_id, self.output_id),
            samplerate=self.sample_rate,
            channels=(1, 2),
            callback=self._callback
        )
        self.stream.start()