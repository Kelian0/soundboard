import soundfile as sf
import numpy as np

class Sound:
    def __init__(self, name: str, filepath: str):
        self.name = name
        self.data, self.fs = sf.read(filepath, dtype='float32')
        
        if len(self.data.shape) > 1:
            self.data = np.mean(self.data, axis=1)

    def get_chunk(self, start_idx: int, size: int) -> np.ndarray:
        return self.data[start_idx:start_idx + size]