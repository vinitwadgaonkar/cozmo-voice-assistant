import numpy as np
import soundfile as sf
import os

def generate_sample_wav(filename, duration=2.0):
    sr = 16000
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Generate a simple sine wave to simulate "voice"
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(filename, audio, sr)

if not os.path.exists("samples"):
    os.makedirs("samples")

generate_sample_wav("samples/hindi_01.wav")
generate_sample_wav("samples/hindi_02.wav")

