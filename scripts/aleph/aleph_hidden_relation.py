#!/usr/bin/env python3
"""
aleph_hidden_relation.py — Diagnose the rank-17 anomaly in H_I

The Gram matrix of interaction profiles has rank 17, not 18.
Ker(I) accounts for 4 null dimensions (the ב/ח/כ, ד/צ, ז/נ collapses).
There is exactly ONE extra null direction not explained by Ker(I).

DS's prescription:
  1. Extract the extra null eigenvector (not in span of Ker(I) indicators)
  2. Express it as a linear relation among the 22 letters
  3. Identify which letters carry non-zero coefficients
  4. Test if the 17-dim quotient (extra null factored out) restores *-structure
  5. Probe the ק anomaly: does ק have large projection onto the null direction?
"""

from __future__ import annotations
import numpy as np
from typing import List, Tuple

from aleph_1 import LETTERS, CANONICAL_GLYPHS, WEIGHTS, tensor

# ──────────────────────────────────────────────────────────────────────────────
# 0. REPRODUCE PROFILE VECTORS (same as aleph_gns.py)
# ──────────────────────────────────────────────────────────────────────────────

W = np.sqrt(np.array(WEIGHTS, dtype=float))

def profile_vector(g: str) -> np.ndarray:
    rows = []
    for h in CANONICAL_GLYPHS:
        result = tensor(LETTERS[g], LETTERS[h])
        rows.append([W[k] * result.t[k] for k in range(12)])
    return np.array(rows, dtype=float).flatten()

V = np.stack([profile_vector(g) for g in CANONICAL_GLYPHS])  # (22, 264)
G = V @ V.T  # Gram matrix (22, 22)

N = len(CANONICAL_GLYPHS)
IDX = {g: i for i, g in enumerate(CANONICAL_GLYPHS)}

# ──────────────────────────────────────────────────────────────────────────────
# 1. FULL NULL SPACE OF G
# ──────────────────────────────────────────────────────────────────────────────

eigvals, eigvecs = np.linalg.eigh(G)
tol = 1e-6
null_mask  = np.abs(eigvals) < tol
null_vecs  = eigvecs[:, null_mask]   # (22, 5)  — columns are null basis vectors

print('═' * 72)
print('  HIDDEN RELATION ANALYSIS — rank-17 anomaly in H_I')
print('═' * 72)
print(f'\n[1] NULL SPACE OF GRAM MATRIX\n')
print(f'  Null space dimension: {null_vecs.shape[1]}  (Ker(I) explains 4)')
print(f'  Eigenvalues of null vectors: {np.round(eigvals[null_mask], 2)}')

# ──────────────────────────────────────────────────────────────────────────────
# 2. KER(I) INDICATOR VECTORS (the "trivial" null directions)
# ──────────────────────────────────────────────────────────────────────────────

# These are difference vectors for letters with identical interaction profiles
ker_pairs = [
    ('ב', 'ח'),   # same profile
    ('ב', 'כ'),   # same profile (ב=ח=כ)
    ('ד', 'צ'),   # same profile
    ('ז', 'נ'),   # same profile
]

ker_indicators = []
for g1, g2 in ker_pairs:
    v = np.zeros(N)
    v[IDX[g1]] =  1.0
    v[IDX[g2]] = -1.0
    ker_indicators.append(v)
K = np.stack(ker_indicators)   # (4, 22)

print(f'\n[2] KER(I) INDICATOR VECTORS\n')
for (g1, g2), kv in zip(ker_pairs, ker_indicators):
    # Verify these are indeed null vectors of G
    residual = np.dot(G, kv)
    print(f'  {g1}↔{g2}:  ||G·(e_{g1}-e_{g2})|| = {np.linalg.norm(residual):.2e}  '
          f'(should be ≈0)')

# ──────────────────────────────────────────────────────────────────────────────
# 3. EXTRACT THE EXTRA NULL VECTOR
# ──────────────────────────────────────────────────────────────────────────────

print(f'\n[3] EXTRA NULL VECTOR (orthogonal complement of Ker(I) in null space)\n')

# Project each null vector onto the orthogonal complement of K
# First orthonormalize K
K_orth, _ = np.linalg.qr(K.T)   # (22, 4)
K_orth = K_orth[:, :4]

# For each null basis vector, subtract its K_orth component
extra_components = []
for i in range(null_vecs.shape[1]):
    nv = null_vecs[:, i]
    proj = K_orth @ (K_orth.T @ nv)   # projection onto Ker(I) span
    residual = nv - proj               # component orthogonal to Ker(I)
    extra_components.append((np.linalg.norm(residual), residual))

# The extra null vector is the one with the largest residual after Ker(I) projection
extra_components.sort(key=lambda x: -x[0])
extra_norm, extra_raw = extra_components[0]

print(f'  Max residual after Ker(I) projection: {extra_norm:.6f}')
print(f'  (If ≈0, the null space is entirely Ker(I) — no extra relation)')
print(f'  (If >0, there is a genuine hidden relation)')
print()

# Normalize
extra = extra_raw / (np.linalg.norm(extra_raw) + 1e-15)

# Also verify it's actually null
print(f'  ||G · extra||  = {np.linalg.norm(G @ extra):.2e}  (should be ≈0)')

# ──────────────────────────────────────────────────────────────────────────────
# 4. EXPRESS THE RELATION IN TERMS OF LETTERS
# ──────────────────────────────────────────────────────────────────────────────

print(f'\n[4] HIDDEN RELATION: coefficients per letter\n')
print(f'  The relation is:  sum_i  c_i · v_i = 0  in R^264\n')
print(f'  {"Letter":6s}  {"tier":8s}  {"c_i":>10s}  {"|c_i|":>8s}')
print('  ' + '─' * 40)

threshold = 0.05 * np.max(np.abs(extra))  # letters with |c| > 5% of max
significant = []
for i, g in enumerate(CANONICAL_GLYPHS):
    ci = extra[i]
    marker = ' ←' if abs(ci) > threshold else ''
    print(f'  {g:6s}  {LETTERS[g].tier:8s}  {ci:>10.5f}  {abs(ci):>8.5f}{marker}')
    if abs(ci) > threshold:
        significant.append((g, ci, LETTERS[g].tier))

print(f'\n  Significant letters (|c_i| > 5% of max):')
for g, ci, tier in sorted(significant, key=lambda x: -abs(x[1])):
    print(f'    {g} ({LETTERS[g].name[:8]:8s}  {tier:8s})   c = {ci:+.5f}')

# ──────────────────────────────────────────────────────────────────────────────
# 5. INTERPRET: WHAT IS THIS RELATION?
# ──────────────────────────────────────────────────────────────────────────────

print(f'\n[5] INTERPRETATION PROBES\n')

# 5a. Does the relation sum to zero? (Is sum c_i = 0?)
sum_c = np.sum(extra)
print(f'  5a. Sum of c_i = {sum_c:.6f}  (zero → "signed balance" relation)')

# 5b. Is the relation tier-respecting?
tier_sums = {}
for i, g in enumerate(CANONICAL_GLYPHS):
    t = LETTERS[g].tier
    tier_sums[t] = tier_sums.get(t, 0.0) + extra[i]
print(f'  5b. Tier-summed coefficients:')
for t, s in sorted(tier_sums.items()):
    print(f'      {t:8s}:  {s:+.6f}')

# 5c. Is the relation related to the O_inf letters (Frobenius)?
inf_coef = sum(extra[IDX[g]] for g in ['ו', 'מ', 'ש'])
print(f'  5c. Sum of c_i for O_inf letters (ו,מ,ש): {inf_coef:+.6f}')

# 5d. Does c correlate with any 12-primitive?
prim_names = ["D","T","R","P","F","K","G","Γ","Φ","H","S","Ω"]
tuples = np.array([list(LETTERS[g].t) for g in CANONICAL_GLYPHS], dtype=float)
print(f'  5d. Correlation of c_i with each primitive ordinal:')
for k, pname in enumerate(prim_names):
    prim_vals = tuples[:, k]
    corr = np.corrcoef(extra, prim_vals)[0, 1]
    if abs(corr) > 0.2:
        print(f'      {pname:4s}: r = {corr:+.4f}  ←')
    else:
        print(f'      {pname:4s}: r = {corr:+.4f}')

# ──────────────────────────────────────────────────────────────────────────────
# 6. ק ANOMALY PROBE
# ──────────────────────────────────────────────────────────────────────────────

print(f'\n[6] ק ANOMALY: projection onto null directions\n')

# For each letter, compute its projection onto the full null space
null_proj_norms = []
for i, g in enumerate(CANONICAL_GLYPHS):
    ei = np.zeros(N); ei[i] = 1.0
    proj_on_null = null_vecs @ (null_vecs.T @ ei)
    null_proj_norms.append((g, np.linalg.norm(proj_on_null), LETTERS[g].tier))

null_proj_norms.sort(key=lambda x: -x[1])
print(f'  Letters ranked by projection onto null space (how much is "hidden"):')
print(f'  {"Letter":6s}  {"tier":8s}  {"null proj norm":>15s}')
print('  ' + '─' * 38)
for g, npn, tier in null_proj_norms:
    marker = '  ←' if g == 'ק' else ''
    print(f'  {g:6s}  {tier:8s}  {npn:15.6f}{marker}')

# ──────────────────────────────────────────────────────────────────────────────
# 7. 17-DIM QUOTIENT: DOES *-STRUCTURE EMERGE?
# ──────────────────────────────────────────────────────────────────────────────

print(f'\n[7] 17-DIM QUOTIENT: recompute L_x, test self-adjointness\n')

# Build the 17-dim orthonormal basis (eigenvectors with nonzero eigenvalues)
nonzero_mask = eigvals > tol
lam17  = eigvals[nonzero_mask]      # (17,)
Q17    = eigvecs[:, nonzero_mask]   # (22, 17)

def left_mult_17(g: str) -> np.ndarray:
    """L_g as 17×17 matrix in the eigenbasis of rank-17 H_I."""
    A = np.zeros((N, N), dtype=float)
    for j, h in enumerate(CANONICAL_GLYPHS):
        result = tensor(LETTERS[g], LETTERS[h])
        for ii, gg in enumerate(CANONICAL_GLYPHS):
            if LETTERS[gg].t == result.t:
                A[ii, j] += 1.0
                break
        else:
            # Non-canonical result: project onto V via least-squares
            res_prof = np.array([
                [W[k] * tensor(result, LETTERS[h2]).t[k] for k in range(12)]
                for h2 in CANONICAL_GLYPHS
            ], dtype=float).flatten()
            for ii in range(N):
                A[ii, j] += np.dot(V[ii], res_prof) / (np.dot(V[ii], V[ii]) + 1e-12)
    return Q17.T @ A @ Q17  # (17, 17)

sa_count_17 = 0
print(f'  {"Letter":6s}  {"||L||":>8s}  {"self-adj?":>10s}  '
      f'{"||L-L^T||":>12s}  {"tr":>8s}')
print('  ' + '─' * 58)
for g in CANONICAL_GLYPHS:
    Lg = left_mult_17(g)
    sa_err = float(np.linalg.norm(Lg - Lg.T))
    sa = sa_err < 1e-4
    if sa:
        sa_count_17 += 1
    print(f'  {g:6s}  {np.linalg.norm(Lg, ord=2):8.4f}  {"yes" if sa else "no":>10s}  '
          f'{sa_err:12.6f}  {np.trace(Lg):8.4f}')

print(f'\n  Self-adjoint operators in 17-dim H_I: {sa_count_17}/22')
print(f'  (Was 0/22 in 18-dim space — change = {sa_count_17 - 0:+d})')

# ──────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────────────────────────────────────

print(f'\n{"═"*72}')
print('[SUMMARY]\n')
print(f'  Null space:         dim=5  (4 from Ker(I), 1 extra hidden relation)')
print(f'  Extra relation:     {"genuine" if extra_norm > 0.1 else "marginal"}  '
      f'(norm of Ker(I)-orthogonal component = {extra_norm:.4f})')
print(f'  Hidden relation:    sum_i c_i · v_i = 0')

top3 = sorted(significant, key=lambda x: -abs(x[1]))[:3]
if top3:
    letts = ', '.join(f'{g}({tier})' for g,ci,tier in top3)
    print(f'  Dominant letters:   {letts}')
print(f'  ק null projection:  {next(n for g,n,t in null_proj_norms if g=="ק"):.6f}')
print(f'  17-dim *-structure: {sa_count_17}/22 self-adjoint')
print(f'{"═"*72}')
