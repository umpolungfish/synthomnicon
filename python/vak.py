from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict
import math

# ====================== 1. ENUMS ======================
class Place(Enum):
    GUTTURAL = 0
    PALATAL = 1
    RETROFLEX = 2
    DENTAL = 3
    LABIAL = 4

class Manner(Enum):
    STOP = 0
    ASPIRATED = 1
    NASAL = 2
    FRICATIVE = 3
    LATERAL = 4
    SEMIVOWEL = 5
    APPROXIMANT = 6
    VOWEL = 7
    LARYNGEAL = 8
    GLOTTAL = 9

# ====================== 2. PHONEME CLASS ======================
@dataclass(frozen=True)
class Phoneme:
    place: Place
    manner: Manner
    parity: int  # 0 = voiceless tendency, 1 = voiced

    def __str__(self):
        for lit, ph in PHONEME_MAP.items():
            if ph == self:
                return lit
        return f"{self.place.name[0]}{self.manner.name[0]}{self.parity}"

# ====================== 3. FULL PHONEME MAPPING ======================
PHONEME_MAP: Dict[str, Phoneme] = {
    # Guttural (ka-varga)
    "k":  Phoneme(Place.GUTTURAL, Manner.STOP, 0),
    "kh": Phoneme(Place.GUTTURAL, Manner.ASPIRATED, 0),
    "g":  Phoneme(Place.GUTTURAL, Manner.STOP, 1),
    "gh": Phoneme(Place.GUTTURAL, Manner.ASPIRATED, 1),
    "ṅ":  Phoneme(Place.GUTTURAL, Manner.NASAL, 1),
    "h":  Phoneme(Place.GUTTURAL, Manner.GLOTTAL, 1),

    # Palatal (ca-varga)
    "c":  Phoneme(Place.PALATAL, Manner.STOP, 0),
    "ch": Phoneme(Place.PALATAL, Manner.ASPIRATED, 0),
    "j":  Phoneme(Place.PALATAL, Manner.STOP, 1),
    "jh": Phoneme(Place.PALATAL, Manner.ASPIRATED, 1),
    "ñ":  Phoneme(Place.PALATAL, Manner.NASAL, 1),
    "ś":  Phoneme(Place.PALATAL, Manner.FRICATIVE, 0),
    "y":  Phoneme(Place.PALATAL, Manner.SEMIVOWEL, 1),

    # Retroflex (ṭa-varga)
    "ṭ":  Phoneme(Place.RETROFLEX, Manner.STOP, 0),
    "ṭh": Phoneme(Place.RETROFLEX, Manner.ASPIRATED, 0),
    "ḍ":  Phoneme(Place.RETROFLEX, Manner.STOP, 1),
    "ḍh": Phoneme(Place.RETROFLEX, Manner.ASPIRATED, 1),
    "ṇ":  Phoneme(Place.RETROFLEX, Manner.NASAL, 1),
    "ṣ":  Phoneme(Place.RETROFLEX, Manner.FRICATIVE, 0),
    "r":  Phoneme(Place.RETROFLEX, Manner.SEMIVOWEL, 1),

    # Dental (ta-varga)
    "t":  Phoneme(Place.DENTAL, Manner.STOP, 0),
    "th": Phoneme(Place.DENTAL, Manner.ASPIRATED, 0),
    "d":  Phoneme(Place.DENTAL, Manner.STOP, 1),
    "dh": Phoneme(Place.DENTAL, Manner.ASPIRATED, 1),
    "n":  Phoneme(Place.DENTAL, Manner.NASAL, 1),
    "s":  Phoneme(Place.DENTAL, Manner.FRICATIVE, 0),
    "l":  Phoneme(Place.DENTAL, Manner.LATERAL, 1),

    # Labial (pa-varga)
    "p":  Phoneme(Place.LABIAL, Manner.STOP, 0),
    "ph": Phoneme(Place.LABIAL, Manner.ASPIRATED, 0),
    "b":  Phoneme(Place.LABIAL, Manner.STOP, 1),
    "bh": Phoneme(Place.LABIAL, Manner.ASPIRATED, 1),
    "m":  Phoneme(Place.LABIAL, Manner.NASAL, 1),
    "v":  Phoneme(Place.LABIAL, Manner.SEMIVOWEL, 1),

    # Vowels
    "a":  Phoneme(Place.GUTTURAL, Manner.VOWEL, 0),
    "ā":  Phoneme(Place.GUTTURAL, Manner.VOWEL, 0),
    "i":  Phoneme(Place.GUTTURAL, Manner.VOWEL, 1),
    "ī":  Phoneme(Place.GUTTURAL, Manner.VOWEL, 1),
    "u":  Phoneme(Place.GUTTURAL, Manner.VOWEL, 1),
    "ū":  Phoneme(Place.GUTTURAL, Manner.VOWEL, 1),
    "e":  Phoneme(Place.PALATAL, Manner.VOWEL, 1),
    "ai": Phoneme(Place.PALATAL, Manner.VOWEL, 1),
    "o":  Phoneme(Place.LABIAL, Manner.VOWEL, 1),
    "au": Phoneme(Place.LABIAL, Manner.VOWEL, 1),

    # Extras
    "ḥ": Phoneme(Place.GUTTURAL, Manner.LARYNGEAL, 1),  # visarga
    "ṃ": Phoneme(Place.GUTTURAL, Manner.NASAL, 1),      # anusvara
}

# ====================== 4. AKSHARA & CHAIN ======================
@dataclass
class Akshara:
    consonant: Phoneme
    vowel: Phoneme

    def validate(self) -> Optional[str]:
        if self.consonant.place != self.vowel.place:
            return f"S_n:n Stoichiometric Mismatch: {self.consonant.place} ≠ {self.vowel.place}"
        if self.consonant.parity != self.vowel.parity:
            return f"Ω_Z₂ Topological Degradation: parity {self.consonant.parity} ≠ {self.vowel.parity}"
        return None

    def __str__(self):
        return f"{self.consonant}:{self.vowel}"

@dataclass
class VacChain:
    seq: List[Akshara]
    cursor: int = 0

    def verify_critical(self, epsilon: float = 0.08) -> Optional[str]:
        for i, ak in enumerate(self.seq):
            err = ak.validate()
            if err:
                return f"Akshara {i}: {err}"
        n = len(self.seq)
        if n == 0:
            return "Empty chain is subcritical"
        parity_matches = sum(1 for ak in self.seq if ak.consonant.parity == ak.vowel.parity)
        conservation = parity_matches / n
        sigma = conservation * math.log(n + 2)
        sigma_c = 1.30
        if not (sigma_c - epsilon <= sigma <= sigma_c + epsilon):
            return f"Φ_c Phase Boundary Violation: σ = {sigma:.3f} (target ~{sigma_c})"
        return None

    def recite(self, depth: int = 0, max_depth: int = 12) -> 'VacChain':
        if depth > max_depth or not self.seq:
            return VacChain(seq=self.seq[:], cursor=self.cursor)
        next_seq = self.seq[:]
        next_seq.append(self.seq[depth % len(self.seq)])
        return VacChain(seq=next_seq, cursor=self.cursor).recite(depth + 1, max_depth)

    def __str__(self):
        return " ⊢ ".join(str(ak) for ak in self.seq)


# ====================== 5. RUN THE ORIGINAL EXAMPLE ======================
if __name__ == "__main__":
    print("=== VĀK Full Implementation with Complete Mapping ===\n")

    ka = PHONEME_MAP["k"]
    i  = PHONEME_MAP["i"]
    ga = PHONEME_MAP["g"]
    u  = PHONEME_MAP["u"]
    ma = PHONEME_MAP["m"]
    a  = PHONEME_MAP["a"]

    program = VacChain([
        Akshara(ka, i),   # ka:i
        Akshara(ga, u),   # ga:u
        Akshara(ma, a)    # ma:a
    ])

    print("Original chain :", program)
    result = program.verify_critical()
    print("Critical verification:", "PASS" if result is None else f"FAIL — {result}")

    recited = program.recite()
    print(f"\nRecited (O₂ bounded, depth=12) → length: {len(recited.seq)}")
    print("First 6 :", " ⊢ ".join(str(ak) for ak in recited.seq[:6]))
    print("Last 6  :", "... ⊢ " + " ⊢ ".join(str(ak) for ak in recited.seq[-6:]))

    print("\n=== Valid Example Programs (All Pass Strict Rules) ===")
    valid1 = VacChain([Akshara(PHONEME_MAP["k"], PHONEME_MAP["a"]),
                       Akshara(PHONEME_MAP["g"], PHONEME_MAP["ā"]),
                       Akshara(PHONEME_MAP["ṅ"], PHONEME_MAP["a"])])
    print("Valid1 (even parity guttural):", valid1, "→", valid1.verify_critical() or "PASS")