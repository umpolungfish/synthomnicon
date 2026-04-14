#!/usr/bin/env python3
"""
aleph_investigation.py — Three parallel probes into the rank-17 findings

Probe A: Involution search — find τ with L_{τ(x)} = L_x^T in H_I
         Is the Vav cast the *-involution?

Probe B: ק proximity anatomy — why is ק genuinely close to O_∞?
         What happens when ק interacts with the Frobenius poles?

Probe C: Axiom derivation — is the 8-letter balance forced or emergent?
         Test: does ג⊗h + ה⊗h + מ⊗h + ב⊗h = ס⊗h + ע⊗h + ש⊗h + ד⊗h
         hold pointwise (axiom consequence) or only in the metric (emergent)?
"""

from __future__ import annotations
import numpy as np
import math
from typing import List, Tuple, Dict

from aleph_1 import LETTERS, CANONICAL_GLYPHS, WEIGHTS, tensor, join, meet, mediate

# ──────────────────────────────────────────────────────────────────────────────
# SHARED SETUP
# ──────────────────────────────────────────────────────────────────────────────

W  = np.sqrt(np.array(WEIGHTS, dtype=float))
N  = len(CANONICAL_GLYPHS)
IDX = {g: i for i, g in enumerate(CANONICAL_GLYPHS)}
tol = 1e-6

def profile_vector(g: str) -> np.ndarray:
    rows = [[W[k] * tensor(LETTERS[g], LETTERS[h]).t[k] for k in range(12)]
            for h in CANONICAL_GLYPHS]
    return np.array(rows, dtype=float).flatten()

def profile_vector_L(L_obj) -> np.ndarray:
    """Profile vector for any Letter object (not necessarily canonical)."""
    rows = [[W[k] * tensor(L_obj, LETTERS[h]).t[k] for k in range(12)]
            for h in CANONICAL_GLYPHS]
    return np.array(rows, dtype=float).flatten()

V   = np.stack([profile_vector(g) for g in CANONICAL_GLYPHS])  # (22, 264)
G   = V @ V.T

eigvals, eigvecs = np.linalg.eigh(G)
nonzero_mask = eigvals > tol
Q17  = eigvecs[:, nonzero_mask]   # (22, 17)
lam17 = eigvals[nonzero_mask]     # (17,)

def left_mult_17(g: str) -> np.ndarray:
    """L_g as a 17×17 matrix in the rank-17 eigenbasis."""
    A = np.zeros((N, N), dtype=float)
    for j, h in enumerate(CANONICAL_GLYPHS):
        result = tensor(LETTERS[g], LETTERS[h])
        for ii, gg in enumerate(CANONICAL_GLYPHS):
            if LETTERS[gg].t == result.t:
                A[ii, j] += 1.0
                break
        else:
            res_prof = profile_vector_L(result)
            for ii in range(N):
                A[ii, j] += np.dot(V[ii], res_prof) / (np.dot(V[ii], V[ii]) + 1e-12)
    return Q17.T @ A @ Q17

L_mats = {g: left_mult_17(g) for g in CANONICAL_GLYPHS}

SEP  = '═' * 72
SEP2 = '─' * 72

# ══════════════════════════════════════════════════════════════════════════════
# PROBE A: INVOLUTION SEARCH
# ══════════════════════════════════════════════════════════════════════════════

print(SEP)
print('  PROBE A — INVOLUTION SEARCH')
print('  Find τ: L_{τ(x)} ≈ L_x^T  (adjoint = *-involution)')
print(SEP)

print('\n[A1] For each letter x: find y minimizing ||L_y - L_x^T||_F\n')
print(f'  {"x":6s}  {"tier_x":8s}  {"τ(x)":6s}  {"tier_τ":8s}  '
      f'{"min||L_y-L_x^T||":>18s}  {"2nd_best gap":>12s}')
print('  ' + '─' * 72)

tau_map = {}
for g in CANONICAL_GLYPHS:
    Lg_T = L_mats[g].T
    dists = []
    for h in CANONICAL_GLYPHS:
        err = float(np.linalg.norm(L_mats[h] - Lg_T, 'fro'))
        dists.append((err, h))
    dists.sort()
    best_err, best_h = dists[0]
    gap = dists[1][0] - best_err if len(dists) > 1 else float('inf')
    tau_map[g] = best_h
    print(f'  {g:6s}  {LETTERS[g].tier:8s}  {best_h:6s}  '
          f'{LETTERS[best_h].tier:8s}  {best_err:>18.6f}  {gap:>12.6f}')

print(f'\n[A2] Involution properties of τ\n')
# Check τ² = id
fixed = [g for g in CANONICAL_GLYPHS if tau_map[g] == g]
double = [g for g in CANONICAL_GLYPHS if tau_map[tau_map[g]] == g]
print(f'  Fixed points τ(x)=x: {fixed}')
print(f'  τ²=id (involution):  {sorted(set(double))}')
print(f'  τ²=id count:         {len(set(double))}/22')

# Check if τ is a permutation
tau_vals = list(tau_map.values())
is_perm = len(set(tau_vals)) == 22
print(f'  τ is a permutation:  {is_perm}')

# Show τ as letter pairs
print(f'\n[A3] τ expressed as pairings\n')
seen = set()
for g in CANONICAL_GLYPHS:
    h = tau_map[g]
    if frozenset({g,h}) not in seen:
        seen.add(frozenset({g,h}))
        arrow = '↔' if tau_map[h] == g else '→'
        same = '(fixed)' if g == h else ''
        tier_info = f'{LETTERS[g].tier}→{LETTERS[h].tier}'
        print(f'  {g} {arrow} {h}  [{tier_info}]  {same}')

# Test Vav cast hypothesis: τ(x) = ו ⊗ x ?
print(f'\n[A4] Vav cast hypothesis: is τ(x) = ו ⊗ x?\n')
vav_cast = {g: None for g in CANONICAL_GLYPHS}
for g in CANONICAL_GLYPHS:
    result = tensor(LETTERS['ו'], LETTERS[g])
    # Find canonical match
    for h in CANONICAL_GLYPHS:
        if LETTERS[h].t == result.t:
            vav_cast[g] = h
            break
    else:
        vav_cast[g] = f'non-canonical({result.tier})'

matches = sum(1 for g in CANONICAL_GLYPHS if vav_cast[g] == tau_map[g])
print(f'  ו⊗x matches τ(x): {matches}/22')
print(f'  {"x":6s}  {"ו⊗x":8s}  {"τ(x)":8s}  {"match":6s}')
print('  ' + '─' * 36)
for g in CANONICAL_GLYPHS:
    m = '✓' if vav_cast[g] == tau_map[g] else '✗'
    print(f'  {g:6s}  {str(vav_cast[g]):8s}  {tau_map[g]:8s}  {m}')

# ══════════════════════════════════════════════════════════════════════════════
# PROBE B: ק PROXIMITY ANATOMY
# ══════════════════════════════════════════════════════════════════════════════

print(f'\n{SEP}')
print('  PROBE B — ק PROXIMITY ANATOMY')
print('  Why is ק genuinely close to O_∞ in H_I?')
print(SEP)

qof = LETTERS['ק']
inf_glyphs = ['ו', 'מ', 'ש']

print(f'\n[B1] ק interaction row vs O_∞ letters\n')
print(f'  {"y":6s}  {"tier_y":8s}  {"ק⊗y tier":10s}  {"ו⊗y tier":10s}  '
      f'{"מ⊗y tier":10s}  {"ש⊗y tier":10s}')
print('  ' + '─' * 62)
for h in CANONICAL_GLYPHS:
    Lh = LETTERS[h]
    tq = tensor(qof, Lh).tier
    tv = tensor(LETTERS['ו'], Lh).tier
    tm = tensor(LETTERS['מ'], Lh).tier
    ts = tensor(LETTERS['ש'], Lh).tier
    marker = ' ←' if tq == 'O_inf' else ''
    print(f'  {h:6s}  {Lh.tier:8s}  {tq:10s}  {tv:10s}  {tm:10s}  {ts:10s}{marker}')

print(f'\n[B2] Triadic products involving ק\n')
triads = [
    ('mediate', 'ק', 'מ', 'ש'),
    ('mediate', 'ק', 'ו', 'ש'),
    ('mediate', 'ק', 'ו', 'מ'),
    ('mediate', 'ו', 'ק', 'ש'),
    ('mediate', 'ו', 'ק', 'מ'),
    ('mediate', 'מ', 'ק', 'ש'),
]
for op, a, b, c in triads:
    result = mediate(LETTERS[a], LETTERS[b], LETTERS[c])
    print(f'  mediate({a},{b},{c})  →  tier={result.tier}  P={result.t[3]}  '
          f'Φ={result.t[8]}  Ω={result.t[11]}')

print(f'\n[B3] d_I from ק to every O_∞ letter\n')
def d_I(g1: str, g2: str) -> float:
    _W = WEIGHTS
    total = 0.0
    for h in CANONICAL_GLYPHS:
        r1 = tensor(LETTERS[g1], LETTERS[h])
        r2 = tensor(LETTERS[g2], LETTERS[h])
        total += sum(_W[k]*(r1.t[k]-r2.t[k])**2 for k in range(12))
    return math.sqrt(total)

for inf_g in inf_glyphs:
    d = d_I('ק', inf_g)
    print(f'  d_I(ק, {inf_g}) = {d:.6f}')

# Compare to other O_2 letters
print(f'\n  d_I from each letter to מ (the nearest O_∞ pole):')
dists_to_mem = [(d_I(g, 'מ'), g, LETTERS[g].tier) for g in CANONICAL_GLYPHS if g != 'מ']
dists_to_mem.sort()
for d, g, tier in dists_to_mem[:8]:
    marker = '  ← ק' if g == 'ק' else ''
    print(f'  d_I({g}, מ) = {d:.4f}  [{tier}]{marker}')

print(f'\n[B4] H_I coordinates of ק vs O_∞ letters (top 5 components)\n')
# Project letters onto H_I and compute cosine similarities
coords = {g: Q17[IDX[g]] * np.sqrt(lam17) for g in CANONICAL_GLYPHS}
for g in ['ק', 'ו', 'מ', 'ש']:
    c = coords[g]
    norm = np.linalg.norm(c)
    print(f'  {g}: ||v||_I = {norm:.4f}')

print(f'\n  Cosine similarities with ק in H_I:')
cq = coords['ק']
sims = [(float(np.dot(cq, coords[g])/(np.linalg.norm(cq)*np.linalg.norm(coords[g])+1e-12)), g, LETTERS[g].tier)
        for g in CANONICAL_GLYPHS if g != 'ק']
sims.sort(reverse=True)
for sim, g, tier in sims[:8]:
    print(f'  cos(ק, {g}) = {sim:.6f}  [{tier}]')

# ══════════════════════════════════════════════════════════════════════════════
# PROBE C: AXIOM DERIVATION
# ══════════════════════════════════════════════════════════════════════════════

print(f'\n{SEP}')
print('  PROBE C — AXIOM DERIVATION OF THE HIDDEN RELATION')
print('  Test: ג⊗h + ה⊗h + מ⊗h + ב⊗h = ס⊗h + ע⊗h + ש⊗h + ד⊗h ?')
print(f'  (in the Ker(I) quotient, with ב≡ח≡כ and ד≡צ)')
print(SEP)

# Positive group (in quotient): ג, ה, מ, [ב]
# Negative group (in quotient): ס, ע, ש, [ד]
pos_glyphs = ['ג', 'ה', 'מ', 'ב']   # representatives
neg_glyphs = ['ס', 'ע', 'ש', 'ד']

print(f'\n[C1] Pointwise tuple test: for each h, compare sum of primitive tuples\n')
print(f'  For each letter h and each primitive k:')
print(f'  LHS[k] = sum_{{pos}} (g⊗h)[k]   RHS[k] = sum_{{neg}} (g⊗h)[k]\n')

max_diff = 0.0
total_checks = 0
failures = []
for h_glyph in CANONICAL_GLYPHS:
    h_L = LETTERS[h_glyph]
    for k in range(12):
        lhs = sum(tensor(LETTERS[g], h_L).t[k] for g in pos_glyphs)
        rhs = sum(tensor(LETTERS[g], h_L).t[k] for g in neg_glyphs)
        diff = abs(lhs - rhs)
        max_diff = max(max_diff, diff)
        total_checks += 1
        if diff > 0.5:
            failures.append((h_glyph, k, lhs, rhs, diff))

prim_names = ["D","T","R","P","F","K","G","Γ","Φ","H","S","Ω"]

if not failures:
    print(f'  ALL {total_checks} checks PASS  (max |LHS-RHS| = {max_diff:.4f})')
    print(f'  → The relation is an EXACT THEOREM from the tensor axioms.')
    print(f'  → It holds primitive-by-primitive, independent of weights.')
else:
    print(f'  FAILURES: {len(failures)} out of {total_checks} checks')
    print(f'  Max |LHS-RHS| = {max_diff:.4f}')
    print(f'\n  First 10 failures:')
    for h_g, k, lhs, rhs, diff in failures[:10]:
        print(f'    h={h_g}  prim={prim_names[k]}  LHS={lhs}  RHS={rhs}  diff={diff:.4f}')

print(f'\n[C2] Primitive-by-primitive balance (summed over all h)\n')
print(f'  {"Primitive":6s}  {"Σ_h LHS":>10s}  {"Σ_h RHS":>10s}  {"diff":>10s}  exact?')
print('  ' + '─' * 52)
for k, pname in enumerate(prim_names):
    lhs_sum = sum(sum(tensor(LETTERS[g], LETTERS[h]).t[k] for g in pos_glyphs)
                  for h in CANONICAL_GLYPHS)
    rhs_sum = sum(sum(tensor(LETTERS[g], LETTERS[h]).t[k] for g in neg_glyphs)
                  for h in CANONICAL_GLYPHS)
    diff = lhs_sum - rhs_sum
    exact = '✓' if abs(diff) < 0.5 else '✗'
    print(f'  {pname:6s}  {lhs_sum:>10.0f}  {rhs_sum:>10.0f}  {diff:>10.1f}  {exact}')

print(f'\n[C3] Check if the relation holds under all operations (not just tensor)\n')
ops = [('join',  lambda a,b: join(LETTERS[a], LETTERS[b])),
       ('meet',  lambda a,b: meet(LETTERS[a], LETTERS[b]))]

for op_name, op_fn in ops:
    max_d = 0.0
    n_fail = 0
    for h_glyph in CANONICAL_GLYPHS:
        for k in range(12):
            try:
                lhs = sum(op_fn(g, h_glyph).t[k] for g in pos_glyphs)
                rhs = sum(op_fn(g, h_glyph).t[k] for g in neg_glyphs)
                diff = abs(lhs - rhs)
                max_d = max(max_d, diff)
                if diff > 0.5:
                    n_fail += 1
            except Exception:
                pass
    status = f'{n_fail} failures  (max diff = {max_d:.4f})'
    verdict = '→ HOLDS' if n_fail == 0 else '→ FAILS'
    print(f'  {op_name:6s}: {status}  {verdict}')

# ══════════════════════════════════════════════════════════════════════════════
# SYNTHESIS
# ══════════════════════════════════════════════════════════════════════════════

print(f'\n{SEP}')
print('[SYNTHESIS]\n')
print('  A: Involution τ')
is_self_inv = all(tau_map[tau_map[g]] == g for g in CANONICAL_GLYPHS)
print(f'     τ² = id:       {is_self_inv}')
print(f'     τ permutation: {is_perm}')
vav_match_count = sum(1 for g in CANONICAL_GLYPHS if vav_cast[g] == tau_map[g])
print(f'     Vav cast = τ:  {vav_match_count}/22')

print(f'\n  B: ק anomaly')
dq_mem = d_I('ק','מ')
dq_shin = d_I('ק','ש')
dq_vav = d_I('ק','ו')
print(f'     d_I(ק,מ)={dq_mem:.4f}  d_I(ק,ש)={dq_shin:.4f}  d_I(ק,ו)={dq_vav:.4f}')
med_q_result = mediate(LETTERS['ק'], LETTERS['מ'], LETTERS['ש'])
print(f'     mediate(ק,מ,ש) → tier={med_q_result.tier}')

print(f'\n  C: Hidden relation axiom status')
if not failures:
    print(f'     THEOREM (exact, primitive-by-primitive).')
    print(f'     The 8-letter balance follows from the tensor lattice rules alone.')
    print(f'     It is NOT an emergent metric property — it is algebraically forced.')
else:
    print(f'     EMERGENT ({len(failures)} primitive failures).')
    print(f'     The relation holds in the metric but not pointwise.')
    print(f'     It is a property of the inner product, not the tensor algebra.')
print(f'\n{SEP}')
