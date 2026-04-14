import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy.signal import spectrogram


# ---------- BASIC TONE ----------

def tone(freq, duration=0.25, sr=44100):
    t = np.linspace(0, duration, int(sr*duration), False)
    wave = np.sin(2*np.pi*freq*t)

    # fade to avoid clicks
    fade_len = int(0.01 * sr)
    fade = np.linspace(0, 1, fade_len)
    wave[:fade_len] *= fade
    wave[-fade_len:] *= fade[::-1]

    return 0.2 * wave


# ---------- COLLATZ ----------

def collatz_step(n):
    return n//2 if n % 2 == 0 else 3*n + 1


def collatz_audio(n_start):
    base = 110
    signal = np.array([], dtype=np.float32)

    n = n_start

    while n != 1:
        if n % 2 == 0:
            freq = base * (1 + (n % 6))
            sig = tone(freq, duration=0.22)
        else:
            freq = base * (1 + (n % 10))
            sig = tone(freq, duration=0.22) * 1.3

        signal = np.concatenate([signal, sig.astype(np.float32)])
        n = collatz_step(n)

    return signal


# ---------- DECAY MODES ----------

# A: harmonic collapse (REAL structure)
def harmonic_decay(base_freq, duration=10.0, sr=44100):
    t = np.linspace(0, duration, int(sr*duration), False)
    signal = np.zeros_like(t, dtype=np.float32)

    for i in range(1, 12):
        harmonic = np.sin(2*np.pi*base_freq*i*t)
        decay = np.exp(-t * (0.4 + i*0.35))
        signal += harmonic * decay

    signal *= 0.2 / np.max(np.abs(signal))
    return signal.astype(np.float32)


# B: amplitude fade (FAKE resolution)
def amplitude_decay(base_freq, duration=10.0, sr=44100):
    t = np.linspace(0, duration, int(sr*duration), False)
    wave = np.sin(2*np.pi*base_freq*t)

    envelope = np.exp(-t * 0.5)

    return (0.2 * wave * envelope).astype(np.float32)


# ---------- ENTROPY ----------

def spectral_entropy(signal, sr=44100):
    f, t, Sxx = spectrogram(signal, fs=sr)

    S_norm = Sxx / (np.sum(Sxx, axis=0, keepdims=True) + 1e-12)
    entropy = -np.sum(S_norm * np.log(S_norm + 1e-12), axis=0)

    return t, entropy


# ---------- MAIN ----------

if __name__ == "__main__":
    base = 110
    n = 27

    print("Generating signals...")

    core = collatz_audio(n)

    # build both versions
    real = np.concatenate([core, harmonic_decay(base)])
    fake = np.concatenate([core, amplitude_decay(base)])

    # ---------- PLAY ----------
    print("Playing REAL collapse...")
    sd.play(real, 44100, blocksize=8192)
    sd.wait()

    print("Playing FAKE collapse...")
    sd.play(fake, 44100, blocksize=8192)
    sd.wait()

    # ---------- ANALYZE ----------
    print("Computing entropy...")

    t1, e1 = spectral_entropy(real)
    t2, e2 = spectral_entropy(fake)

    # ---------- PLOT ----------
    plt.figure(figsize=(10,5))
    plt.plot(t1, e1, label="Harmonic Collapse (Real)")
    plt.plot(t2, e2, label="Amplitude Fade (Fake)", linestyle='dashed')

    plt.xlabel("Time")
    plt.ylabel("Spectral Entropy")
    plt.title("Entropy Comparison")
    plt.legend()
    plt.tight_layout()
    plt.show()