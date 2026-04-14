import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import spectrogram

# ---------- AUDIO GENERATION (same as before, slightly improved) ----------

def tone(freq, duration=0.25, sr=44100):
    t = np.linspace(0, duration, int(sr*duration), False)
    return 0.2 * np.sin(2*np.pi*freq*t)

def collatz_audio_signal(n):
    base = 110
    signal = np.array([])

    while n != 1:
        if n % 2 == 0:
            freq = base * (1 + (n % 6))     # stable region
            sig = tone(freq)
        else:
            freq = base * (1 + (n % 10))    # more chaotic
            sig = tone(freq) * 1.5

        signal = np.concatenate([signal, sig])
        n = n//2 if n % 2 == 0 else 3*n+1

    # final Φ_c state → pure tone
    signal = np.concatenate([signal, tone(base, duration=1.0)])

    return signal

# ---------- ENTROPY COMPUTATION ----------

def spectral_entropy(S):
    # normalize each time slice
    S_norm = S / (np.sum(S, axis=0, keepdims=True) + 1e-12)
    entropy = -np.sum(S_norm * np.log(S_norm + 1e-12), axis=0)
    return entropy

# ---------- MAIN ANALYSIS ----------

signal = collatz_audio_signal(27)
fs = 44100

f, t, Sxx = spectrogram(signal, fs=fs)

entropy = spectral_entropy(Sxx)

# ---------- PLOTS ----------

plt.figure(figsize=(12,6))

# Spectrogram
plt.subplot(2,1,1)
plt.pcolormesh(t, f, Sxx, shading='gouraud')
plt.ylabel('Frequency')
plt.title('Spectrogram')

# Entropy over time
plt.subplot(2,1,2)
plt.plot(t, entropy)
plt.xlabel('Time')
plt.ylabel('Entropy')
plt.title('Spectral Entropy Over Time')

plt.tight_layout()
plt.show()