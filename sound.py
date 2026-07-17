import sounddevice as sd
import soundfile as sf
import numpy as np
from scipy import signal

class Sound:
    def __init__(self, name: str, filepath: str, target_fs: int = 44100):
        self.name = name
        self.data, self.fs = sf.read(filepath, dtype='float32')
        
        if self.fs != target_fs:
            num_samples = int(len(self.data) * target_fs / self.fs)
            self.data = signal.resample(self.data, num_samples)
            self.fs = target_fs

        if len(self.data.shape) > 1:
            self.data = np.mean(self.data, axis=1)

class SoundPlayer:
    def __init__(self, output_id: int):
        self.output_id = output_id

    def play(self, sound: Sound):
        sd.play(sound.data, samplerate=sound.fs, device=self.output_id)

    def stop(self):
        sd.stop()