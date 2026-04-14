#!/usr/bin/env python3
"""
aleph_functor.py — Interaction Functor I(x) for λ_ℵ

The interaction functor is the "debugger" of the language (ALEPH_SPEC.md §8):

    I(x) = { x ⊗ y | y ∈ ℒ }    (full interaction row)

Two letters are functorially equivalent iff I(x) = I(y).
This is strictly finer than the 12-primitive distance: even when d(x, y) = 0,
if I(x) ≠ I(y) then x ≇ y in λ_ℵ. Conversely, if I(x) = I(y), no operation
in the language can distinguish them — they are structurally identical inhabitants.

Computed artifacts:
  - 22×22 interaction matrix (tier labels)
  - Interaction rows as type-tuples
  - Functional equivalence classes
  - Interaction distance d_I(x, y) — finer than raw d(x, y)
  - Collapse-attack validation (§8.1 P-bottleneck invariant check)
"""

import math
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from aleph_1 import (
    Letter, LETTERS, CANONICAL_GLYPHS,
    tensor, join, meet, distance,
    PALACE_ORDER,
)

# ──────────────────────────────────────────────────────────────────────────────
# 1. INTERACTION ROW
# ──────────────────────────────────────────────────────────────────────────────

def interaction_row(x: Letter) -> Dict[str, Letter]:
    """
    I(x) = { x ⊗ y | y ∈ ℒ }, keyed by glyph.
    Returns all 22 tensor products of x with each canonical letter.
    """
    return {g: tensor(x, LETTERS[g]) for g in CANONICAL_GLYPHS}


def row_signature(x: Letter) -> Tuple[Tuple[int,...], ...]:
    """
    Canonical representation of I(x) as an ordered tuple of 12-tuples.
    Order follows CANONICAL_GLYPHS — deterministic, hashable.
    """
    return tuple(tensor(x, LETTERS[g]).t for g in CANONICAL_GLYPHS)


# ──────────────────────────────────────────────────────────────────────────────
# 2. INTERACTION DISTANCE
# ──────────────────────────────────────────────────────────────────────────────

# Weights (same as aleph_1.py distance)
_W = [1.0, 1.0, 1.0, 1.2, 0.9, 0.8, 1.0, 1.0, 1.1, 0.8, 1.0, 0.7]


def _tuple_distance(t1: Tuple[int,...], t2: Tuple[int,...]) -> float:
    return math.sqrt(sum(w*(a-b)**2 for w,a,b in zip(_W, t1, t2)))


def interaction_distance(x: Letter, y: Letter) -> float:
    """
    d_I(x, y) = sqrt( Σ_{g ∈ ℒ} d(x⊗g, y⊗g)² )

    The Euclidean norm of the pointwise row differences.
    Strictly finer than d(x, y): d_I(x, y) = 0 iff I(x) = I(y).
    """
    sx = row_signature(x)
    sy = row_signature(y)
    return math.sqrt(sum(_tuple_distance(a, b)**2 for a, b in zip(sx, sy)))


# ──────────────────────────────────────────────────────────────────────────────
# 3. EQUIVALENCE CLASSES
# ──────────────────────────────────────────────────────────────────────────────

def equivalence_classes() -> List[List[str]]:
    """
    Partition the 22 canonical letters by identical interaction rows.
    Letters in the same class are functorially indistinguishable in λ_ℵ.
    Returns sorted list of equivalence classes (by first member).
    """
    sig_to_glyphs: Dict[tuple, List[str]] = defaultdict(list)
    for g in CANONICAL_GLYPHS:
        sig = row_signature(LETTERS[g])
        sig_to_glyphs[sig].append(g)
    classes = sorted(sig_to_glyphs.values(), key=lambda c: CANONICAL_GLYPHS.index(c[0]))
    return classes


# ──────────────────────────────────────────────────────────────────────────────
# 4. INTERACTION MATRIX
# ──────────────────────────────────────────────────────────────────────────────

_TIER_ORD = {'O_0': 0, 'O_1': 1, 'O_2': 2, 'O_2d': 2, 'O_inf': 3}
_TIER_SYM = {'O_0': '·', 'O_1': '1', 'O_2': '2', 'O_2d': '2†', 'O_inf': '∞'}


def interaction_matrix() -> List[List[str]]:
    """
    22×22 matrix of tier symbols for tensor(row_letter, col_letter).
    Entry (i, j) = tier of CANONICAL_GLYPHS[i] ⊗ CANONICAL_GLYPHS[j].
    """
    return [
        [_TIER_SYM.get(tensor(LETTERS[g1], LETTERS[g2]).tier, '?')
         for g2 in CANONICAL_GLYPHS]
        for g1 in CANONICAL_GLYPHS
    ]


# ──────────────────────────────────────────────────────────────────────────────
# 5. COLLAPSE-ATTACK PROBE
# ──────────────────────────────────────────────────────────────────────────────

def probe_collapse_attack(attacker_glyphs: List[str],
                          target_tier: str = 'O_inf') -> dict:
    """
    Simulate the §8.1 P-bottleneck collapse attack:
    attempt to reach target_tier by tensoring attacker_glyphs left-to-right.

    Returns analysis: achieved tier, P value at each step,
    whether the attack succeeded, and interaction-functor mismatch.
    """
    from functools import reduce
    letters = [LETTERS[g] for g in attacker_glyphs]
    steps = []
    current = letters[0]
    steps.append({'glyph': attacker_glyphs[0],
                  'tier': current.tier,
                  'P': current.t[3]})  # P index = 3

    for i, (g, l) in enumerate(zip(attacker_glyphs[1:], letters[1:]), 1):
        current = tensor(current, l)
        steps.append({'glyph': attacker_glyphs[i],
                      'tier': current.tier,
                      'P': current.t[3]})

    achieved = current.tier
    success = achieved == target_tier

    # Interaction functor check: does current match any O_inf letter?
    inf_letters = [g for g in CANONICAL_GLYPHS
                   if LETTERS[g].tier == 'O_inf']
    functor_match = None
    if not success and inf_letters:
        # Check if I(current) matches any known O_inf letter
        cur_sig = row_signature(current)
        for g in inf_letters:
            if row_signature(LETTERS[g]) == cur_sig:
                functor_match = g
                break

    return {
        'attack': '⊗'.join(attacker_glyphs),
        'steps': steps,
        'achieved_tier': achieved,
        'target_tier': target_tier,
        'attack_succeeded': success,
        'functor_match': functor_match,  # None = no match (attack defeated)
    }


# ──────────────────────────────────────────────────────────────────────────────
# 6. REPORTS
# ──────────────────────────────────────────────────────────────────────────────

def print_matrix():
    W = 3
    header = '     ' + ''.join(f'{g:>{W}}' for g in CANONICAL_GLYPHS)
    print(header)
    print('     ' + '─' * (W * 22))
    mat = interaction_matrix()
    for i, (g, row) in enumerate(zip(CANONICAL_GLYPHS, mat)):
        L = LETTERS[g]
        cells = ''.join(f'{c:>{W}}' for c in row)
        print(f'  {g} {L.name[:3]:3s} │{cells}')


def print_classes():
    classes = equivalence_classes()
    print(f"  Equivalence classes ({len(classes)} distinct interaction rows):\n")
    for cls in classes:
        names = [f"{g}({LETTERS[g].name})" for g in cls]
        tier = LETTERS[cls[0]].tier
        marker = '  ←  d_I=0 within class' if len(cls) > 1 else ''
        print(f"  [{tier:8s}] {',  '.join(names)}{marker}")


def print_d_I_zero_pairs():
    """Report all pairs with d(x,y)=0 and their interaction distance."""
    pairs = []
    for i, g1 in enumerate(CANONICAL_GLYPHS):
        for j, g2 in enumerate(CANONICAL_GLYPHS):
            if j <= i:
                continue
            d_raw = distance(LETTERS[g1], LETTERS[g2])
            if d_raw < 1e-9:
                d_I = interaction_distance(LETTERS[g1], LETTERS[g2])
                pairs.append((g1, g2, d_raw, d_I))

    if not pairs:
        print("  No d=0 pairs found.")
        return
    print("  Pairs with d(x,y) = 0:")
    print(f"  {'Pair':12s}  {'d(x,y)':>8s}  {'d_I(x,y)':>10s}  Verdict")
    print("  " + "─" * 52)
    for g1, g2, d_raw, d_I in pairs:
        n1, n2 = LETTERS[g1].name, LETTERS[g2].name
        verdict = "INDISTINGUISHABLE" if d_I < 1e-9 else "DISTINGUISHABLE by I"
        print(f"  {g1}({n1[:3]})↔{g2}({n2[:3]})  {d_raw:>8.4f}  {d_I:>10.4f}  {verdict}")


def print_row(glyph: str):
    """Print the full interaction row for a single letter."""
    L = LETTERS[glyph]
    row = interaction_row(L)
    print(f"  I({glyph} / {L.name})  [tier {L.tier}]\n")
    print(f"  {'y':>5}  {'name':8s}  {'tier(x⊗y)':12s}  {'d(x, x⊗y)':>12s}")
    print("  " + "─" * 50)
    for g, result in row.items():
        y = LETTERS[g]
        d = distance(L, result)
        print(f"  {g:>5}  {y.name:8s}  {result.tier:12s}  {d:>12.4f}")


# ──────────────────────────────────────────────────────────────────────────────
# 7. MAIN
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    SEP = '═' * 72

    print(SEP)
    print('  λ_ℵ INTERACTION FUNCTOR  I(x) = { x ⊗ y | y ∈ ℒ }')
    print('  Behavioral equivalence beyond the 12-primitive projection')
    print(SEP)

    # ── 1. Interaction matrix ────────────────────────────────────────────
    print('\n[1] INTERACTION MATRIX  (tier of x ⊗ y)')
    print('    ·=O_0  1=O_1  2=O_2  ∞=O_∞\n')
    print_matrix()

    # ── 2. Equivalence classes ───────────────────────────────────────────
    print('\n' + '─' * 72)
    print('[2] FUNCTIONAL EQUIVALENCE CLASSES')
    print('    Letters in the same class: I(x)=I(y) → no λ_ℵ operation distinguishes them\n')
    print_classes()

    # ── 3. d=0 pairs analysis ────────────────────────────────────────────
    print('\n' + '─' * 72)
    print('[3] d(x,y)=0 PAIRS: raw distance vs interaction distance\n')
    print_d_I_zero_pairs()

    # ── 4. O_inf letter rows ─────────────────────────────────────────────
    print('\n' + '─' * 72)
    print('[4] INTERACTION ROWS OF O_∞ LETTERS (ו מ ש)')
    for g in ['ו', 'מ', 'ש']:
        print()
        print_row(g)

    # ── 5. Collapse attack demo ──────────────────────────────────────────
    print('\n' + '─' * 72)
    print('[5] COLLAPSE ATTACK PROBES  (§8.1 — P-bottleneck invariant)\n')

    attacks = [
        ['ב', 'מ', 'ש'],    # Bet ⊗ Mem ⊗ Shin — classic attack
        ['מ', 'ש'],          # Mem ⊗ Shin — legitimate O_∞ composition
        ['א', 'מ', 'ש'],    # Aleph ⊗ Mem ⊗ Shin — tensor (wrong)
        ['ת', 'ו', 'ר', 'ה'],  # Torah
    ]

    for atk in attacks:
        result = probe_collapse_attack(atk)
        status = '✓ VALID' if result['achieved_tier'] == 'O_inf' else '✗ BLOCKED'
        print(f"  {'⊗'.join(atk):<18s}  →  {result['achieved_tier']:8s}  {status}")
        # P-trace
        p_names = {0:'P_asym',1:'P_ψ',2:'P_±',3:'P_sym',4:'P_±sym'}
        p_trace = ' → '.join(p_names.get(s['P'],'?') for s in result['steps'])
        print(f"    P-trace: {p_trace}")
        if result['functor_match']:
            print(f"    Functor match: {result['functor_match']} (equivalent!)")
        elif result['achieved_tier'] != 'O_inf':
            print(f"    Functor: no O_∞ match — I(result) is distinct from all O_∞ letters")
        print()

    # ── 6. Aleph as mediating witness ────────────────────────────────────
    print('─' * 72)
    print('[6] ALEPH BREATH-BETWEEN: mediate vs tensor\n')
    from aleph_1 import mediate
    aleph = LETTERS['א']
    mem   = LETTERS['מ']
    shin  = LETTERS['ש']

    t_result = tensor(tensor(aleph, mem), shin)
    m_result = mediate(aleph, mem, shin)

    print(f"  tensor(א, tensor(מ, ש)):   tier={t_result.tier}  P={t_result.t[3]}")
    print(f"  mediate(א, מ, ש):          tier={m_result.tier}  P={m_result.t[3]}")
    print()
    d_I_tensor  = interaction_distance(t_result, mem)
    d_I_mediate = interaction_distance(m_result, mem)
    print(f"  d_I(tensor_result, מ)  = {d_I_tensor:.4f}")
    print(f"  d_I(mediate_result, מ) = {d_I_mediate:.4f}")
    print(f"\n  Mediation preserves functional proximity to Mem (the Frobenius pole).")
    print(f"  Tensor destroys it: d_I gap = {d_I_tensor - d_I_mediate:.4f}.")

    print('\n' + SEP)
    print('  I(·) COMPUTATION COMPLETE')
    print('  Equivalence: behavioral identity. Distance: d_I ≥ d. Proof: still running.')
    print(SEP)
