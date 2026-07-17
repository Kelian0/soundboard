import sounddevice as sd
import soundfile as sf
import numpy as np
from scipy import signal

class Sound:
    def __init__(self, name: str, filepath: str, target_fs: int = 48000):
        self.name = name
        self.data, self.fs = sf.read(filepath, dtype='float32')

        if self.fs != target_fs:
            num_samples = int(len(self.data) * target_fs / self.fs)
            self.data = signal.resample(self.data, num_samples)
            self.fs = target_fs

        if len(self.data.shape) > 1:
            self.data = np.mean(self.data, axis=1)
        
        self.original_data = self.data.copy()
        self.volume = 1.0

    def apply_settings(self, start_sec: float, end_sec: float, vol_pct: int):
        start_idx = int(start_sec * self.fs)
        
        if end_sec > 0:
            end_idx = int(end_sec * self.fs)
            self.data = self.original_data[start_idx:end_idx]
        else:
            self.data = self.original_data[start_idx:]
            
        self.data = self.data * (vol_pct / 100.0)

class SoundPlayer:
    def __init__(self, output_id: int):
        self.output_id = output_id

    def play(self, sound: Sound):
        sd.play(sound.data, samplerate=sound.fs, device=self.output_id)

    def stop(self):
        sd.stop()