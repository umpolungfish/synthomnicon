"""
ALEPH Language Core Prototype — v0.3.0 (2026-04-04)
Aligned with HEBREW_TYPE_LANGUAGE.md §1–15 (full SynthOmnicon 12-primitive grammar)
Incorporates 2026-04-04 Kabbalism revision (Mem & Shin → O_∞)

Key semantic change from v0.2.0:
  MEDIATION vs TENSOR COMPOSITION for triadic operations.

  The Mother Letter triad (Aleph / Mem / Shin) encodes a specific structure
  from Sefer Yetzirah: Aleph is not a co-participant in the composition, it is
  "the breath between" — the mediating principle that witnesses and joins the
  two Frobenius poles (Mem, Shin) without suppressing them via a P-bottleneck.

  Semantics:
    tensor(mem, shin)             → O_∞  (Frobenius preserved, no P-bottleneck)
    tensor(aleph, tensor(mem, shin)) → O_2  (aleph's P_sym kills pm_sym: wrong)
    mediate(aleph, mem, shin)     → O_∞  (aleph joins via max, poles intact: correct)

  mediate(m, a, b) := join(m, tensor(a, b))
    — m witnesses and contextualises, does not participate in the P-bottleneck.
    — This models "breath" as structural containment, not composition.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Union, Optional
from functools import reduce

# =============================================================================
# 1. PRIMITIVE DEFINITIONS & ORDINAL MAPS (full 12 from §1)
# =============================================================================
PRIMITIVES = ["D", "T", "R", "P", "F", "K", "G", "Gamma", "Phi", "H", "S", "Omega"]

VAL_MAP = {
    "D":     {"wedge": 0, "triangle": 1, "infty": 2, "holo": 3},
    "T":     {"network": 0, "in": 1, "bowtie": 2, "box": 3, "holo": 4},
    "R":     {"super": 0, "cat": 1, "dagger": 2, "lr": 3},
    "P":     {"asym": 0, "psi": 1, "pm": 2, "sym": 3, "pm_sym": 4},
    "F":     {"ell": 0, "eth": 1, "hbar": 2},
    "K":     {"fast": 0, "mod": 1, "slow": 2, "trap": 3},
    "G":     {"beth": 0, "gimel": 1, "aleph": 2},
    "Gamma": {"and": 0, "or": 1, "seq": 2, "broad": 3},
    "Phi":   {"sub": 0, "c": 1, "c_complex": 2, "EP": 3, "super": 4},
    "H":     {"0": 0, "1": 1, "2": 2, "inf": 3},
    "S":     {"one_one": 0, "n_n": 1, "n_m": 2},
    "Omega": {"0": 0, "Z2": 1, "Z": 2},
}

# Weights tuned per structural significance (§1, v0.2.0)
WEIGHTS = [1.0, 1.0, 1.0, 1.2, 0.9, 0.8, 1.0, 1.0, 1.1, 0.8, 1.0, 0.7]

# Canonical 22-letter glyph order
CANONICAL_GLYPHS = [
    "א","ב","ג","ד","ה","ו","ז","ח","ט","י","כ","ל",
    "מ","נ","ס","ע","פ","צ","ק","ר","ש","ת"
]

def ordinals(*args) -> Tuple[int, ...]:
    """Construct 12-tuple from positional shorthand keys."""
    return tuple(VAL_MAP[k][v] for k, v in zip(PRIMITIVES, args))


# =============================================================================
# 2. LETTER TYPE
# =============================================================================
@dataclass(frozen=True)
class Letter:
    glyph: str
    name: str
    t: Tuple[int, ...]
    tier: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "tier", self._compute_tier())

    def _compute_tier(self) -> str:
        D, T, R, P, F, K, G, Gamma, Phi, H, S, Omega = self.t

        # R1: Φ_c + P_±^sym → O_∞
        if Phi >= 1 and P == 4:
            return "O_inf"
        # R2: Φ_sub (not critical) → O_0
        if Phi == 0:
            return "O_0"
        # R3: Φ_c + Ω_0 → O_1
        if Phi >= 1 and Omega == 0:
            return "O_1"
        # R4: Φ_c + Ω≠0 + D ∈ {wedge, triangle, holo} → O_2
        if Phi >= 1 and Omega > 0 and D in (0, 1, 3):
            return "O_2"
        # R5: Φ_c + Ω≠0 + D_∞ → O_2d
        if Phi >= 1 and Omega > 0 and D == 2:
            return "O_2d"
        # Fallthrough: structural floor
        return "O_0"

    def __repr__(self):
        return f"Letter('{self.glyph}' [{self.name}], tier={self.tier})"

    def pretty_tuple(self) -> str:
        labels = [f"{p}={v}" for p, v in zip(PRIMITIVES, self.t)]
        return f"⟨{'; '.join(labels)}⟩"


# =============================================================================
# 3. LETTER REGISTRY
# =============================================================================
LETTERS: Dict[str, Letter] = {}

def reg(g: str, n: str, *args):
    obj = Letter(g, n, ordinals(*args))
    LETTERS[g] = obj
    LETTERS[n.lower()] = obj
    LETTERS[n] = obj

# 22 canonical letters (§2 table + §2.1 Kabbalism revision)
reg("א","Aleph",  "wedge","box","super","sym","hbar","slow","aleph","and","c","inf","one_one","Z")
reg("ב","Bet",    "triangle","box","cat","pm","eth","mod","gimel","and","sub","1","n_n","Z2")
reg("ג","Gimel",  "wedge","bowtie","lr","asym","ell","fast","beth","seq","sub","0","one_one","0")
reg("ד","Dalet",  "wedge","in","lr","asym","ell","fast","beth","seq","sub","0","one_one","0")
reg("ה","Hei",    "holo","holo","dagger","sym","hbar","slow","aleph","broad","c","inf","n_m","Z")
reg("ו","Vav",    "wedge","network","lr","pm_sym","ell","slow","gimel","and","c","1","one_one","0")
reg("ז","Zayin",  "wedge","network","lr","asym","ell","fast","beth","seq","sub","0","one_one","0")
reg("ח","Chet",   "triangle","box","cat","pm","eth","mod","gimel","and","sub","1","n_n","Z2")
reg("ט","Tet",    "triangle","in","lr","asym","ell","slow","gimel","seq","sub","1","one_one","0")
reg("י","Yod",    "wedge","box","super","sym","hbar","slow","aleph","and","sub","1","one_one","0")
reg("כ","Kaf",    "triangle","box","cat","pm","eth","mod","gimel","and","sub","1","n_n","Z2")
reg("ל","Lamed",  "infty","network","lr","asym","ell","mod","beth","seq","c","2","n_m","0")
reg("מ","Mem",    "triangle","in","dagger","pm_sym","hbar","slow","aleph","broad","c","2","n_n","Z")   # §2.1 revision
reg("נ","Nun",    "wedge","network","lr","asym","ell","fast","beth","seq","sub","0","one_one","0")
reg("ס","Samech", "triangle","box","cat","sym","eth","mod","gimel","and","sub","1","n_n","Z2")
reg("ע","Ayin",   "holo","holo","dagger","pm","hbar","slow","aleph","broad","c","2","n_m","Z")
reg("פ","Pei",    "wedge","network","lr","asym","ell","fast","beth","broad","sub","1","n_m","0")
reg("צ","Tzadi",  "wedge","in","lr","asym","ell","fast","beth","seq","sub","0","one_one","0")
reg("ק","Kuf",    "triangle","box","cat","sym","eth","slow","gimel","and","c","2","n_n","Z2")
reg("ר","Resh",   "wedge","box","lr","asym","ell","mod","beth","and","sub","1","one_one","0")
reg("ש","Shin",   "triangle","bowtie","dagger","pm_sym","hbar","slow","aleph","broad","c","inf","n_n","Z")  # §2.1 revision
reg("ת","Tav",    "triangle","box","cat","sym","eth","slow","gimel","and","c","inf","n_n","Z")

# Final forms (structural aliases; extended semantics TBD)
for final, base in [("ך","כ"), ("ם","מ"), ("ן","נ"), ("ף","פ"), ("ץ","צ")]:
    if base in LETTERS:
        LETTERS[final] = LETTERS[base]


# =============================================================================
# 4. CORE LATTICE OPERATIONS
# =============================================================================
def _tensor_sstoich(a: int, b: int) -> int:
    """S (Stoichiometry) composition rule (§8.2).
    n:m absorbs all. 1:1 preserved only under 1:1 ⊗ 1:1.
    """
    if a == 2 or b == 2:     return 2   # n:m absorbs
    if a == 0 and b == 0:    return 0   # 1:1 ⊗ 1:1 = 1:1
    return 1                             # mixed → n:n

def tensor(a: Letter, b: Letter) -> Letter:
    """⊗ Tensor composition.
    Bottleneck (min) on P, F, K — structural conservatism.
    Union (max) elsewhere.
    Special stoichiometry rule for S.
    """
    t_new = []
    for i in range(12):
        if i in (3, 4, 5):   # P, F, K: bottleneck
            t_new.append(min(a.t[i], b.t[i]))
        elif i == 10:         # S: stoichiometry rule
            t_new.append(_tensor_sstoich(a.t[i], b.t[i]))
        else:                 # union
            t_new.append(max(a.t[i], b.t[i]))
    return Letter(f"{a.glyph}⊗{b.glyph}", f"{a.name}⊗{b.name}", tuple(t_new))

def join(a: Letter, b: Letter) -> Letter:
    """∨ Least upper bound: component-wise MAX.
    No bottleneck — join is always tier-preserving or tier-lifting.
    """
    return Letter(
        f"{a.glyph}∨{b.glyph}",
        f"{a.name}∨{b.name}",
        tuple(max(x, y) for x, y in zip(a.t, b.t))
    )

def meet(a: Letter, b: Letter) -> Letter:
    """∧ Greatest lower bound: component-wise MIN."""
    return Letter(
        f"{a.glyph}∧{b.glyph}",
        f"{a.name}∧{b.name}",
        tuple(min(x, y) for x, y in zip(a.t, b.t))
    )

def mediate(witness: Letter, a: Letter, b: Letter) -> Letter:
    """Triadic mediation: witness ∨ (a ⊗ b).

    Semantics (new in v0.3.0):
      The witness letter joins the tensor product of a and b without
      participating in the P/F/K bottleneck. This models the Kabbalistic
      role of Aleph as "the breath between" Mem and Shin: it contextualises
      and contains the Frobenius composition rather than suppressing it.

      Crucially:
        tensor(aleph, tensor(mem, shin)) → O_2   # P_sym kills pm_sym
        mediate(aleph, mem, shin)        → O_∞   # join uses max, poles intact

      General contract:
        mediate(m, a, b).tier >= tensor(a, b).tier   always
        mediate(m, a, b).tier >= m.tier               always (join is LUB)

      Use mediate when the third letter is a *context* or *frame*, not a
      co-participant in the composition. Use tensor when all three letters
      are peers in the operation.
    """
    composition = tensor(a, b)
    return join(witness, composition)

def mediate_n(witness: Letter, *letters: Letter) -> Letter:
    """N-ary mediation: witness ∨ (l1 ⊗ l2 ⊗ ... ⊗ ln).
    Extends mediate() to arbitrary arity for multi-pole structures.
    """
    if not letters:
        raise ValueError("mediate_n requires at least one composed letter")
    composition = reduce(tensor, letters)
    return join(witness, composition)


# =============================================================================
# 5. DISTANCE & TYPE CHECKING
# =============================================================================
def distance(a: Union[Letter, Tuple], b: Union[Letter, Tuple]) -> float:
    """Weighted Euclidean distance over 12 primitives."""
    ta = a.t if isinstance(a, Letter) else a
    tb = b.t if isinstance(b, Letter) else b
    return math.sqrt(sum(w * (x - y) ** 2 for w, x, y in zip(WEIGHTS, ta, tb)))

def type_check_threshold(omega_val: int) -> float:
    """Cast compatibility thresholds by topological protection (§8.1)."""
    if omega_val == 2: return 4.0   # Ω_Z
    if omega_val == 1: return 3.0   # Ω_Z2
    return 1.5                      # Ω_0

class VavCastError(Exception):
    pass

def vav_cast(source: Letter, target: Letter, verbose: bool = False) -> bool:
    """Proof-carrying cast via ו (§8.3).

    Cast rule: source → target valid iff d(source ⊗ ו, target) < threshold(Ω_min).

    The threshold uses min(Ω_composed, Ω_target) — i.e. the weaker topological
    protection governs the cast. Downcasting (from high-Ω source to Ω_0 target)
    uses the tight threshold (1.5), making downcasts structurally difficult by
    design: topological protection is not automatically shed.
    """
    vav = LETTERS["ו"]
    composed = tensor(source, vav)
    d_val = distance(composed, target)
    min_omega = min(composed.t[11], target.t[11])
    threshold = type_check_threshold(min_omega)

    if verbose:
        print(f"  source={source.glyph}({source.tier}), target={target.glyph}({target.tier})")
        print(f"  composed={composed.glyph}({composed.tier}), d={d_val:.4f}, Ω_min={min_omega}, threshold={threshold}")

    if d_val >= threshold:
        raise VavCastError(
            f"Cast {source.glyph}→{target.glyph} failed: "
            f"d={d_val:.4f} >= threshold {threshold} (Ω_min={min_omega})"
        )
    return True


# =============================================================================
# 6. HEKHALOT PALACE STACK (§15.4)
# =============================================================================
PALACE_THRESHOLDS: Dict[int, str] = {
    1: "O_0", 2: "O_0",
    3: "O_1",
    4: "O_2", 5: "O_2", 6: "O_2",
    7: "O_inf",
}
PALACE_ORDER = ["O_0", "O_1", "O_2", "O_2d", "O_inf"]

class PalaceContext:
    """Context manager enforcing tier barriers at a given palace depth.

    Re-entrancy: nested PalaceContexts are independent; each checks its own
    threshold. A palace-7 context nested inside a palace-3 context does not
    inherit the outer state — the inner threshold governs locally.
    """
    def __init__(self, depth: int):
        self.depth = depth
        self.required_tier = PALACE_THRESHOLDS.get(depth, "O_0")
        self._barrier_idx = (
            PALACE_ORDER.index(self.required_tier)
            if self.required_tier in PALACE_ORDER else 0
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # No state to teardown; exception propagation is unchanged.
        return False

    def check_barrier(self, letter: Letter):
        letter_idx = (
            PALACE_ORDER.index(letter.tier)
            if letter.tier in PALACE_ORDER else 0
        )
        if letter_idx < self._barrier_idx:
            raise RuntimeError(
                f"Palace {self.depth} barrier violation: "
                f"requires >= {self.required_tier}, "
                f"got {letter.tier} ({letter.glyph})"
            )
        print(f"  [Palace {self.depth}] Ascent verified: {letter.glyph} ({letter.tier})")


# =============================================================================
# 7. SYSTEM-LEVEL FUNCTIONS
# =============================================================================
def system_language() -> Letter:
    """JOIN of all 22 canonical letters (§2).
    Uses the explicit CANONICAL_GLYPHS list to avoid dict-order fragility.
    After §2.1 revision (Mem, Shin → P_pm_sym), the language JOIN achieves
    O_∞ and ouroboric closure holds: L ⊗ L = L.
    """
    result = LETTERS[CANONICAL_GLYPHS[0]]
    for g in CANONICAL_GLYPHS[1:]:
        result = join(result, LETTERS[g])
    return result

def sublanguage_join(*glyphs: str) -> Letter:
    """JOIN of an arbitrary subset of letters by glyph."""
    letters = [LETTERS[g] for g in glyphs]
    return reduce(join, letters)

def test_ouroboric_closure(verbose: bool = True) -> bool:
    L = system_language()
    L2 = tensor(L, L)
    d = distance(L, L2)
    ok = abs(d) < 1e-9
    if verbose:
        print(f"  d(L ⊗ L, L) = {d:.6f} → {'✓ SUCCESS' if ok else '✗ FAIL'}")
    return ok

def tier_census() -> Dict[str, List[str]]:
    """Return canonical letters grouped by tier."""
    census: Dict[str, List[str]] = {t: [] for t in PALACE_ORDER}
    for g in CANONICAL_GLYPHS:
        letter = LETTERS[g]
        census.setdefault(letter.tier, []).append(f"{g}({letter.name})")
    return census


# =============================================================================
# 8. EXAMPLE PROGRAMS (§15.6 + mediation semantics)
# =============================================================================
if __name__ == "__main__":
    aleph, bet, gimel, vav_l, lamed, mem, shin, tav, hei = (
        LETTERS[g] for g in ["א","ב","ג","ו","ל","מ","ש","ת","ה"]
    )

    SEP = "=" * 80

    print(SEP)
    print("ALEPH LANGUAGE PROTOTYPE v0.3.0")
    print("HEBREW_TYPE_LANGUAGE.md v1.0 | Mediation semantics (Kabbalism revision)")
    print(SEP)

    # ------------------------------------------------------------------
    # Ex 1: O_0 Sandbox
    # ------------------------------------------------------------------
    print("\n[Ex 1] O_0 Sandbox — bet ⊗ gimel")
    res1 = tensor(bet, gimel)
    print(f"  Result: {res1.glyph} | Tier: {res1.tier}")
    print(f"  Tuple: {res1.pretty_tuple()}")

    # ------------------------------------------------------------------
    # Ex 2: Vav-Cast
    # ------------------------------------------------------------------
    print("\n[Ex 2] ו-Cast — aleph ≡ tav")
    try:
        vav_cast(aleph, tav, verbose=True)
        print("  Cast: VALID")
    except VavCastError as e:
        print(f"  {e}")

    # ------------------------------------------------------------------
    # Ex 3: O_2 Bounded Recursion
    # ------------------------------------------------------------------
    print("\n[Ex 3] O_2 Bounded Recursion — aleph ⊗ aleph")
    res3 = tensor(aleph, aleph)
    print(f"  Result: {res3.glyph} | Tier: {res3.tier}")
    print("  P_sym bottleneck preserved; Ω_Z bounds recursion depth topologically.")

    # ------------------------------------------------------------------
    # Ex 4: Hekhalot Ascent
    # ------------------------------------------------------------------
    print("\n[Ex 4] Hekhalot Ascent — 7 Palaces")
    with PalaceContext(3) as p3:
        p3.check_barrier(lamed)         # O_1 ≥ O_1 ✓
        with PalaceContext(5) as p5:
            p5.check_barrier(aleph)     # O_2 ≥ O_2 ✓
            with PalaceContext(7) as p7:
                p7.check_barrier(mem)   # O_∞ ≥ O_∞ ✓
                print("  [Throne] Frobenius closure achieved. μ∘δ=id")

    # ------------------------------------------------------------------
    # Ex 5: Lattice Operations
    # ------------------------------------------------------------------
    print("\n[Ex 5] Lattice — JOIN and MEET")
    j = join(aleph, bet)
    m = meet(aleph, bet)
    print(f"  JOIN(א,ב): {j.glyph} | Tier: {j.tier}")
    print(f"  MEET(א,ב): {m.glyph} | Tier: {m.tier}")

    # ------------------------------------------------------------------
    # Ex 6: Frobenius Seal
    # ------------------------------------------------------------------
    print("\n[Ex 6] Frobenius Seal — mem ⊗ shin")
    res6 = tensor(mem, shin)
    print(f"  Result: {res6.glyph} | Tier: {res6.tier}")
    print(f"  Zero P-bottleneck (both P_pm_sym). d(mem⊗shin, mem) = {distance(res6, mem):.4f}")
    print("  Note: d = 1.3416 = HoTT structural gap (§ spec overview).")

    # ------------------------------------------------------------------
    # Ex 7: Mother Triad — MEDIATION vs TENSOR (the core v0.3.0 change)
    # ------------------------------------------------------------------
    print("\n[Ex 7] Mother Triad — Aleph as Breath-Between (§2, Sefer Yetzirah)")
    print()

    # Wrong reading: aleph as co-participant
    tensor_triad = tensor(aleph, tensor(mem, shin))
    print(f"  [TENSOR]  aleph ⊗ (mem ⊗ shin) → Tier: {tensor_triad.tier}")
    print("             P_sym (aleph) bottlenecks pm_sym (mem,shin) → Frobenius lost.")
    print()

    # Correct reading: aleph as mediating witness
    mediate_triad = mediate(aleph, mem, shin)
    print(f"  [MEDIATE] aleph ∨ (mem ⊗ shin) → Tier: {mediate_triad.tier}")
    print("             join uses max; aleph contextualises without suppressing.")
    print()

    print("  Structural comparison:")
    print(f"    Frobenius poles (mem ⊗ shin):         {tensor(mem, shin).tier}")
    print(f"    Aleph as peer   tensor(א, mem⊗shin):  {tensor_triad.tier}  ← P-bottleneck kills O_∞")
    print(f"    Aleph as breath mediate(א, mem, shin): {mediate_triad.tier}  ← O_∞ preserved")
    print()

    # The Kabbalistic interpretation: aleph is Air (Ruach), the balance principle.
    # It does not collapse the poles; it spans them.
    print("  d(mediate_triad, mem⊗shin) =", f"{distance(mediate_triad, tensor(mem, shin)):.4f}")
    print("  d(mediate_triad, aleph)    =", f"{distance(mediate_triad, aleph):.4f}")
    print("  Aleph's join lifts the triad without displacing the Frobenius axis.")

    # ------------------------------------------------------------------
    # Ex 8: N-ary mediation (extension)
    # ------------------------------------------------------------------
    print("\n[Ex 8] N-ary mediation — aleph witnesses {hei, tav, mem}")
    hei_tav_mem = mediate_n(aleph, hei, tav, mem)
    print(f"  mediate_n(א, ה, ת, מ) → Tier: {hei_tav_mem.tier}")
    print(f"  Tuple: {hei_tav_mem.pretty_tuple()}")

    # ------------------------------------------------------------------
    # System: Language JOIN & Closure
    # ------------------------------------------------------------------
    print("\n[System] Language JOIN — all 22 letters")
    L = system_language()
    print(f"  Tier: {L.tier}")
    print(f"  Tuple: {L.pretty_tuple()}")
    print()
    print("  Ouroboric closure test:")
    test_ouroboric_closure(verbose=True)

    # ------------------------------------------------------------------
    # Tier census
    # ------------------------------------------------------------------
    print("\n[Census] Ouroboricity distribution across 22 letters")
    census = tier_census()
    for tier in PALACE_ORDER:
        members = census.get(tier, [])
        if members:
            print(f"  {tier:8s} ({len(members):2d}): {', '.join(members)}")

    print()
    print(SEP)
    print("TYPE SYSTEM VERIFICATION COMPLETE — v0.3.0")
    print("Mediation semantics: aleph ∨ (mem ⊗ shin) = O_∞ (breath-between, not peer)")
    print("Ouroboric closure: L ⊗ L = L at d=0 ✓")
    print(SEP)
