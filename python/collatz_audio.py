import numpy as np
import sounddevice as sd
import argparse
from dataclasses import dataclass
from typing import List, Optional
import soundfile as sf  # optional: pip install soundfile


# ====================== SYNTHON CLASSIFICATION ======================

@dataclass
class SynthonState:
    n: int
    P: str          # Polarity: symmetric / asymmetric
    Phi: str        # Criticality: subcritical or Φ_c (attractor)
    Omega: str      # Topological protection
    O: str          # Ouroboricity (cyclic self-reference)

def classify(n: int) -> SynthonState:
    if n == 1:
        return SynthonState(n, "P_sym", "Phi_c", "Omega_Z", "O2")
    elif n % 2 == 0:
        return SynthonState(n, "P_sym", "Phi_sub", "Omega_0", "O0")
    else:
        return SynthonState(n, "P_asym", "Phi_sub", "Omega_0", "O0")

def collatz_step(n: int) -> int:
    return n // 2 if n % 2 == 0 else 3 * n + 1

def collatz_synthon_trace(n0: int, max_steps: int = 10000) -> List[SynthonState]:
    """Return full trace with synthon states. Safety cap for huge n."""
    trace: List[SynthonState] = []
    n = n0
    steps = 0

    while n != 1 and steps < max_steps:
        s = classify(n)
        trace.append(s)
        n = collatz_step(n)
        steps += 1

    # Always include the terminal 1
    trace.append(classify(1))
    return trace


# ====================== AUDIO ENGINE ======================

def tone(freq: float, duration: float = 0.25, sr: int = 44100,
         amp: float = 0.2, modulation: float = 0.0) -> np.ndarray:
    """Improved tone with optional light FM modulation for texture."""
    t = np.linspace(0, duration, int(sr * duration), False)
    wave = np.sin(2 * np.pi * freq * t)

    if modulation > 0:
        # subtle FM for "energetic" odd steps
        mod = modulation * np.sin(2 * np.pi * freq * 3.7 * t)  # inharmonic sidebands
        wave = np.sin(2 * np.pi * freq * t + mod)

    # Smooth fade to prevent clicks at note boundaries
    fade_len = int(0.008 * sr)  # ~8ms
    if len(wave) > 2 * fade_len:
        fade_in = np.linspace(0, 1, fade_len)
        fade_out = fade_in[::-1]
        wave[:fade_len] *= fade_in
        wave[-fade_len:] *= fade_out

    return (amp * wave).astype(np.float32)


def generate_collatz_audio(trace: List[SynthonState], base_freq: float = 110.0,
                           sr: int = 44100) -> np.ndarray:
    """Generate trajectory audio driven by synthon states."""
    signal = np.array([], dtype=np.float32)
    prev_n = trace[0].n

    for i, state in enumerate(trace[:-1]):  # exclude final 1 for now
        n = state.n

        # Log-scaled frequency for perceptual consistency across huge n
        log_n = np.log2(max(n, 2))
        freq = base_freq * (1.0 + (log_n % 12) / 6.0)   # spread over ~2 octaves

        # Duration reflects dynamics: longer on climbs, shorter on descents
        delta = n - prev_n
        duration = 0.18 + 0.12 * min(1.0, abs(delta) / max(n, 100))

        # Amplitude & modulation from synthon
        amp = 0.22
        mod = 0.0
        if state.P == "P_asym":          # odd → energetic
            amp *= 1.35
            mod = 0.8
        if state.Phi == "Phi_c":
            amp *= 1.1

        # Slight detuning based on Omega / O for "protection" feel
        if state.Omega == "Omega_Z":
            freq *= 1.005  # micro-detune at cycle

        sig = tone(freq, duration, sr, amp, mod)
        signal = np.concatenate([signal, sig])
        prev_n = n

    # Arrival chord at 1 (beautiful resolution)
    final_states = trace[-1]
    arrival = np.zeros(int(0.8 * sr), dtype=np.float32)
    for h in [1.0, 1.5, 2.0, 3.0]:  # simple just-ish intervals
        arrival += tone(base_freq * h, 0.8, sr, amp=0.15 / h)

    signal = np.concatenate([signal, arrival])

    # Global normalization of trajectory (prevents clipping)
    max_amp = np.max(np.abs(signal))
    if max_amp > 0:
        signal *= 0.92 / max_amp

    return signal


def harmonic_decay(base_freq: float, duration: float = 12.0,
                   trajectory_length: int = 0, max_n: int = 1,
                   sr: int = 44100) -> np.ndarray:
    """Enhanced Φ_c collapse tail — reacts to the journey."""
    t = np.linspace(0, duration, int(sr * duration), False)
    signal = np.zeros_like(t, dtype=np.float32)

    num_harmonics = 16
    stretch = 1.0 + 0.008 * np.log2(max(max_n, 2))  # slight inharmonicity for large journeys

    for i in range(1, num_harmonics + 1):
        freq = base_freq * i * (1 + (i-1)*0.002*stretch)
        harmonic = np.sin(2 * np.pi * freq * t)

        # Faster decay for higher harmonics + overall envelope shaped by trajectory
        decay_rate = 0.35 + i * 0.28 + (trajectory_length / 200.0)
        decay = np.exp(-t * decay_rate)

        # Gentle amplitude rolloff
        signal += harmonic * decay * (1.0 / i**0.85)

    # Soft overall envelope
    env = np.exp(-t * 0.12)
    signal *= env

    # Normalize
    max_val = np.max(np.abs(signal))
    if max_val > 0:
        signal *= 0.28 / max_val

    return signal.astype(np.float32)


# ====================== FULL PIPELINE ======================

def generate_collatz_with_decay(n_start: int, max_steps: int = 10000,
                                save_wav: Optional[str] = None) -> np.ndarray:
    print(f"Computing Collatz trajectory + synthon trace for n={n_start}...")

    trace = collatz_synthon_trace(n_start, max_steps)
    trajectory_length = len(trace)
    max_n = max(s.n for s in trace)

    print(f"→ {trajectory_length} steps, peak value reached: {max_n}")

    # Main sonic journey
    base = 110.0
    trajectory_audio = generate_collatz_audio(trace, base)

    # Φ_c absorbing tail — length and character influenced by journey
    tail_duration = 10.0 + min(8.0, trajectory_length / 80.0)
    decay = harmonic_decay(base, duration=tail_duration,
                           trajectory_length=trajectory_length, max_n=max_n)

    full_signal = np.concatenate([trajectory_audio, decay])

    # Very gentle overall fade-out
    fade_out_len = int(1.5 * 44100)
    fade = np.linspace(1.0, 0.0, fade_out_len)
    if len(full_signal) > fade_out_len:
        full_signal[-fade_out_len:] *= fade

    # Optional WAV export
    if save_wav:
        sf.write(save_wav, full_signal, 44100, subtype='FLOAT')
        print(f"Saved to {save_wav}")

    return full_signal.astype(np.float32)


# ====================== PLAYBACK ======================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collatz Synthon Audio Explorer")
    parser.add_argument("n", type=int, nargs="?", default=27,
                        help="Starting number (default: 27)")
    parser.add_argument("--max-steps", type=int, default=10000,
                        help="Safety limit on steps")
    parser.add_argument("--save", type=str, metavar="FILE.wav",
                        help="Save output as WAV file")
    parser.add_argument("--no-play", action="store_true",
                        help="Don't play audio (useful with --save)")

    args = parser.parse_args()

    audio = generate_collatz_with_decay(args.n, args.max_steps, args.save)

    if not args.no_play:
        print("Playing...")
        try:
            sd.play(audio, samplerate=44100, blocksize=8192)
            sd.wait()
            print("Playback finished.")
        except Exception as e:
            print(f"Playback error: {e}")
            print("Try saving with --save instead.")
    else:
        print("Audio generated (playback skipped).")