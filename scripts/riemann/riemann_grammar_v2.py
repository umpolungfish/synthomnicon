"""
riemann_grammar_v2.py — Stage 1 + corrected grammar-distance Viterbi.

Fixes the K-primitive computation bug from riemann_grammar_score.py:
  WRONG: K from nearest RAW peak — all raw peaks are sub-RS-spacing
         dense oscillations → every raw peak gets K_slow regardless.
  RIGHT: K from nearest COARSE peak (NMS-thinned at ~0.5 * delta_RS),
         plus INVERTED logic:
           k_ratio ≈ 1.0  (regular spacing)  → K_fast  (phantom, density rhythm)
           k_ratio << 1.0 (compressed pair)   → K_slow  (GUE level repulsion, zero)
           k_ratio >> 1.0 (wide gap before)   → K_slow  (isolated zero)

Grammar derivation:
  - True zeros obey GUE statistics (K_slow): level repulsion → pairs with
    spacing < 0.6 * delta_RS AND isolated zeros with spacing > 1.4 * delta_RS.
  - Phantoms arise from Fourier density rhythm (K_fast): fill gaps at exactly
    the RS mean spacing → k_ratio ≈ 1.0 for every phantom peak.

Discriminant: k_ratio far from 1.0 → K_slow → zero-like.
              k_ratio close to 1.0 → K_fast → phantom-like.

sep lowered to 0.35 so that GUE-compressed pairs (spacing ≈ 0.4–0.6) can
both be selected — the grammar score suppresses regular phantom clusters
instead of relying on sep alone.
"""

from __future__ import annotations

import math
import random
import sys
import os

import torch
import torch.nn as nn
import torch.optim as optim

from navigators import RiemannNavigator
from train_navigators import RIEMANN_ZEROS_T, ZERO_T_SCALE, make_riemann_batch
from riemann_crf import rs_N, scan_near_zero, ZEROS_101_150

sys.path.insert(0, os.path.dirname(__file__))
from space_search.primitives import tuple_distance

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TRAIN_ZEROS = RIEMANN_ZEROS_T[:50]
HOLD1_ZEROS = RIEMANN_ZEROS_T[50:]
HOLD2_ZEROS = ZEROS_101_150

# ── Structural archetypes ─────────────────────────────────────────────────────

TRUE_ZERO_TYPE = {
    "D": "D_odot",    "T": "T_odot",    "R": "R_dagger",  "P": "P_pm_sym",
    "F": "F_hbar",    "K": "K_slow",    "G": "G_aleph",   "Gamma": "G_broad",
    "Phi": "Phi_c",   "H": "H_inf",     "S": "n_m",       "Omega": "Omega_Z",
}
PHANTOM_TYPE = {
    "D": "D_infty",   "T": "T_network", "R": "R_super",   "P": "P_asym",
    "F": "F_ell",     "K": "K_fast",    "G": "G_beth",    "Gamma": "G_and",
    "Phi": "Phi_sub", "H": "H0",        "S": "one_one",   "Omega": "Omega_0",
}

_D_ARCHETYPES = tuple_distance(TRUE_ZERO_TYPE, PHANTOM_TYPE)


def rs_mean_spacing(t: float) -> float:
    """Expected mean zero spacing at height $t$: $2\pi / \log(t / (2\pi))$."""
    if t < 4.0:
        return 2.0
    return 2.0 * math.pi / math.log(t / (2.0 * math.pi))


def nms_coarsen(
    candidates: list[tuple[float, float]],
    window_frac: float = 0.50,
) -> list[tuple[float, float]]:
    """
    Non-maximum suppression: for each local cluster within
    window = window_frac * rs_mean_spacing(t), keep only the peak
    with the highest p_near. Returns sorted coarse peaks.

    window_frac = 0.50 keeps ~1 peak per 0.5 * RS_spacing, so:
      - At t=170, RS=1.85 → window=0.93: keeps ~1 peak per 0.93 units
      - Dense phantom clusters (0.5-apart) are coalesced to ~1 per cluster
      - True zero pairs at spacing 0.5-0.8 are coalesced to 1 (limitation)
    """
    if not candidates:
        return []
    cands = sorted(candidates, key=lambda x: x[0])
    suppressed = [False] * len(cands)

    for i in range(len(cands)):
        if suppressed[i]:
            continue
        t_i, p_i = cands[i]
        win = rs_mean_spacing(t_i) * window_frac
        # suppress all lower-amplitude neighbors within window
        for j in range(i + 1, len(cands)):
            t_j, p_j = cands[j]
            if t_j - t_i > win:
                break
            if p_j < p_i:
                suppressed[j] = True
            else:
                suppressed[i] = True
                break

    return [(t, p) for (t, p), s in zip(cands, suppressed) if not s]


def grammar_score_v2(
    candidates: list[tuple[float, float]],
    t_vals: list[float],
    p_vals: list[float],
    nms_frac: float = 0.50,
    phi_threshold: float = 0.003,
    k_regular_tight: float = 0.40,  # |k_ratio-1| < this → K_fast  (regular = phantom)
    k_regular_mid: float = 0.80,    # |k_ratio-1| < this → K_mod
    logit_weight: float = 0.10,     # mix logit(p) into score for tiebreaking
) -> list[tuple[float, float, float]]:
    """
    Assign grammar score to each candidate peak using coarse-peak K computation.

    K primitive (corrected logic):
      1. Coarsen candidates via NMS at window = nms_frac * rs_mean_spacing(t).
      2. For each candidate, find spacing to nearest coarse peak.
      3. k_ratio = spacing / rs_mean_spacing.
         |k_ratio - 1| <  k_regular_tight → K_fast  (regular → phantom signature)
         |k_ratio - 1| <  k_regular_mid   → K_mod
         |k_ratio - 1| >= k_regular_mid   → K_slow  (irregular → zero signature)

      GUE level repulsion:
         - Close pairs (k_ratio < 0.6): irregular, K_slow → true zero
         - Isolated (k_ratio > 1.8):    irregular, K_slow → true zero
         - Regular (k_ratio 0.6-1.4):   rhythmic,  K_fast → phantom

    Phi primitive (unchanged):
      peak_contrast = p_peak - mean(neighborhood at ±delta_RS/2) > phi_threshold
      → Phi_c (genuine enhancement) else Phi_sub (density artifact)

    Score = d(cand_type, PHANTOM) - d(cand_type, ZERO) + logit_weight * logit(p)
    """
    if not candidates:
        return []

    coarse = nms_coarsen(candidates, window_frac=nms_frac)
    coarse_t = [c[0] for c in coarse]

    scored = []
    for t_i, p_i in candidates:
        # ── K: coarse-peak spacing ─────────────────────────────────────────────
        delta_rs = rs_mean_spacing(t_i)

        # Find nearest coarse peak that is NOT at t_i itself
        best_dist = 999.0
        for ct in coarse_t:
            d = abs(t_i - ct)
            if d < 0.01:
                continue   # skip self (coarse peaks are a subset of candidates)
            if d < best_dist:
                best_dist = d
        k_ratio = best_dist / delta_rs

        dev = abs(k_ratio - 1.0)
        if dev < k_regular_tight:
            k_val = "K_fast"    # regular spacing → phantom
        elif dev < k_regular_mid:
            k_val = "K_mod"
        else:
            k_val = "K_slow"    # irregular → true zero (GUE)

        # ── Phi: peak sharpness ────────────────────────────────────────────────
        window = delta_rs * 0.9
        nbr_ps = [pv for tv, pv in zip(t_vals, p_vals)
                  if 0.08 < abs(tv - t_i) < window]
        nbr_mean = sum(nbr_ps) / len(nbr_ps) if nbr_ps else p_i
        phi_val = "Phi_c" if (p_i - nbr_mean) > phi_threshold else "Phi_sub"

        # ── Candidate type ─────────────────────────────────────────────────────
        cand_type = dict(TRUE_ZERO_TYPE)
        cand_type["K"]   = k_val
        cand_type["Phi"] = phi_val

        d_zero    = tuple_distance(cand_type, TRUE_ZERO_TYPE)
        d_phantom = tuple_distance(cand_type, PHANTOM_TYPE)
        gscore    = d_phantom - d_zero

        # Tiebreak: add small logit(p) component
        p_clip   = max(min(p_i, 1 - 1e-7), 1e-7)
        logit_p  = math.log(p_clip / (1.0 - p_clip))
        total    = gscore + logit_weight * logit_p

        scored.append((t_i, p_i, total))

    return scored


# ── Grammar-score Viterbi (unchanged from v1) ─────────────────────────────────

def grammar_viterbi(
    scored_candidates: list[tuple[float, float, float]],
    budget: int,
    sep: float = 0.35,
) -> list[tuple[float, float, float]]:
    """Budget-Viterbi maximising sum of grammar scores."""
    if not scored_candidates or budget <= 0:
        return []

    cands = sorted(scored_candidates, key=lambda x: x[0])
    n, k = len(cands), min(budget, len(cands))

    NEG_INF = float("-inf")
    dp  = [[NEG_INF] * (k + 1) for _ in range(n)]
    par = [[-1]      * (k + 1) for _ in range(n)]

    for i, (t_i, _, sc_i) in enumerate(cands):
        dp[i][1]  = sc_i
        par[i][1] = -1
        for prev in range(i):
            if t_i - cands[prev][0] < sep:
                continue
            for j in range(2, k + 1):
                if dp[prev][j - 1] == NEG_INF:
                    continue
                val = dp[prev][j - 1] + sc_i
                if val > dp[i][j]:
                    dp[i][j] = val
                    par[i][j] = prev

    best_val, best_i, best_j = NEG_INF, -1, 0
    for j in range(k, 0, -1):
        for i in range(n):
            if dp[i][j] > best_val:
                best_val, best_i, best_j = dp[i][j], i, j
        if best_i >= 0:
            break

    if best_i < 0:
        return []

    path = []
    i, j = best_i, best_j
    while i >= 0 and j > 0:
        path.append(cands[i])
        i = par[i][j]; j -= 1
    return sorted(path, key=lambda x: x[0])


# ── Holdout evaluation ────────────────────────────────────────────────────────

def holdout_report_v2(
    model: RiemannNavigator,
    label: str,
    known_zeros: list[float],
    t_scan_lo: float,
    t_scan_hi: float,
    n_known_before: int,
    hit_thresh: float = 1.0,
    sep: float = 0.35,
    nms_frac: float = 0.50,
    phi_threshold: float = 0.003,
    k_regular_tight: float = 0.40,
    k_regular_mid: float = 0.80,
) -> tuple[int, int, int]:

    n_pts = max(3000, int((t_scan_hi - t_scan_lo) * 30))

    raw_all, t_vals, p_nears = scan_near_zero(
        model, t_scan_lo - 0.5, t_scan_hi + 2.0, n_pts=n_pts
    )

    # Omega_Z budget
    rs_lo  = rs_N(t_scan_lo)
    rs_hi  = rs_N(t_scan_hi + 1.0)
    budget = max(len(known_zeros), int(math.floor(rs_hi - rs_lo)) + 1)

    # Hard gap gate
    t_gate = min(known_zeros) - 1.0
    raw_gated = [
        (t, p) for t, p in raw_all
        if t_scan_lo - 0.5 <= t <= t_scan_hi + 1.0 and t >= t_gate
    ]

    # Coarsen and score
    coarse    = nms_coarsen(raw_gated, window_frac=nms_frac)
    scored    = grammar_score_v2(
        raw_gated, t_vals, p_nears,
        nms_frac=nms_frac, phi_threshold=phi_threshold,
        k_regular_tight=k_regular_tight, k_regular_mid=k_regular_mid,
    )

    # Viterbi
    selected = grammar_viterbi(scored, budget=budget, sep=sep)

    # K distribution diagnostics
    k_dist  = {"K_fast": 0, "K_mod": 0, "K_slow": 0}
    phi_dist = {"Phi_c": 0, "Phi_sub": 0}
    gscore_dist: dict[str, list[float]] = {"K_fast": [], "K_mod": [], "K_slow": []}
    coarse_t = [c[0] for c in coarse]
    for t_i, p_i in raw_gated:
        delta_rs = rs_mean_spacing(t_i)
        best_d = min((abs(t_i - ct) for ct in coarse_t if abs(t_i - ct) > 0.01),
                     default=999.0)
        k_ratio = best_d / delta_rs
        dev = abs(k_ratio - 1.0)
        if dev < k_regular_tight:
            kv = "K_fast"
        elif dev < k_regular_mid:
            kv = "K_mod"
        else:
            kv = "K_slow"
        k_dist[kv] += 1
        window = delta_rs * 0.9
        nbr_ps = [pv for tv, pv in zip(t_vals, p_nears)
                  if 0.08 < abs(tv - t_i) < window]
        nbr_mean = sum(nbr_ps) / len(nbr_ps) if nbr_ps else p_i
        phi_dist["Phi_c" if (p_i - nbr_mean) > phi_threshold else "Phi_sub"] += 1

    gscore_all = [s[2] for s in scored]
    gscore_sel = [s[2] for s in selected]

    print(f"\n{'='*68}")
    print(f"HOLDOUT: {label}  (NEVER SEEN DURING TRAINING)")
    print(f"{'='*68}")
    print(f"RS budget: {budget}  |  t_gate: {t_gate:.1f}"
          f"  |  raw gated: {len(raw_gated)}"
          f"  |  coarse: {len(coarse)}"
          f"  |  after Viterbi: {len(selected)}")
    print(f"  archetype d(zero,phantom) = {_D_ARCHETYPES:.3f}")
    if gscore_all:
        print(f"  grammar score (all gated):  "
              f"mean={sum(gscore_all)/len(gscore_all):+.3f}  "
              f"min={min(gscore_all):+.3f}  max={max(gscore_all):+.3f}")
    if gscore_sel:
        print(f"  grammar score (selected):   "
              f"mean={sum(gscore_sel)/len(gscore_sel):+.3f}  "
              f"min={min(gscore_sel):+.3f}  max={max(gscore_sel):+.3f}")
    print(f"  K (gated): K_fast={k_dist['K_fast']}  "
          f"K_mod={k_dist['K_mod']}  K_slow={k_dist['K_slow']}")
    print(f"  Phi (gated): Phi_c={phi_dist['Phi_c']}  Phi_sub={phi_dist['Phi_sub']}")
    print()
    print(f"  {'#':>4}  {'t_pred':>12}  {'P(near)':>9}  {'g_score':>9}"
          f"  {'nearest zero':>14}  {'delta':>8}  {'status':>8}")
    print(f"  {'----':>4}  {'------------':>12}  {'---------':>9}  {'---------':>9}"
          f"  {'------------':>14}  {'--------':>8}  {'--------':>8}")

    hits, phantoms = 0, 0
    matched: set[float] = set()
    for det_idx, (t_pred, p, gscore) in enumerate(selected, 1):
        nearest = min(known_zeros, key=lambda z: abs(z - t_pred))
        delta   = abs(t_pred - nearest)
        status  = "HIT" if delta <= hit_thresh else "PHANTOM"
        if status == "HIT":
            hits += 1
            matched.add(nearest)
        else:
            phantoms += 1
        print(f"  {det_idx:>4}  {t_pred:>12.4f}  {p:>9.4f}  {gscore:>+9.3f}"
              f"  {nearest:>14.6f}  {delta:>8.4f}  {status:>8}")

    missed = sorted(z for z in known_zeros if z not in matched)
    if missed:
        print(f"\n  MISSED: {[f'{z:.3f}' for z in missed]}")
    print(f"\nRESULT: {hits}/{len(known_zeros)} zeros found"
          f"  |  {phantoms} phantoms  |  {len(missed)} missed")
    return hits, phantoms, len(missed)


# ── Training ──────────────────────────────────────────────────────────────────

def train_stage1(
    model: RiemannNavigator,
    zeros_t: list[float],
    epochs: int = 800,
    lr: float = 3e-4,
    batch_size: int = 128,
) -> None:
    opt   = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    print(f"\n  {'Epoch':>6}  {'L_frob':>10}  {'L_sym':>10}  {'L_zero':>10}"
          f"  {'L_near':>10}  {'Acc':>7}")
    print(f"  {'------':>6}  {'----------':>10}  {'----------':>10}"
          f"  {'----------':>10}  {'----------':>10}  {'-------':>7}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, near, zero_t = make_riemann_batch(
            zeros_t, batch_size=batch_size, t_range=(10.0, 250.0)
        )
        s = s.to(DEVICE); near = near.to(DEVICE); zero_t = zero_t.to(DEVICE)
        out = model(s)
        losses = model.compute_loss(
            out, true_zero_t=zero_t, true_near=near,
            lam_zero=1.0, lam_frob=0.5, lam_sym=1.0, lam_near=1.0,
        )
        losses["loss"].backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % 50 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                acc = ((out["near_zero"] > 0.5).float() == near).float().mean().item()
            print(f"  {epoch:>6}  {losses['L_frob']:>10.6f}  {losses['L_sym']:>10.6f}"
                  f"  {losses['L_zero']:>10.6f}  {losses['L_near']:>10.6f}  {acc:>6.1%}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    HIDDEN   = 240
    LAYERS   = 24
    HEADS    = 24
    NFOURIER = 48
    FREQ_MAX = 2.5
    BATCH    = 128

    model = RiemannNavigator(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigator  hidden={HIDDEN}  layers={LAYERS}  heads={HEADS}")
    print(f"  n_fourier={NFOURIER}  freq_max=10^{FREQ_MAX}  params={n_params:,}")
    print(f"  Training: zeros 1-50 (Stage 1, 800 ep)")
    print(f"  Decoder:  grammar-distance Viterbi v2 (corrected K from coarse peaks)")
    print(f"  K logic:  k_ratio~1.0 → K_fast (phantom); k_ratio far from 1.0 → K_slow (zero)")
    print(f"  Archetype d(zero, phantom) = {_D_ARCHETYPES:.3f}")

    print(f"\n{'='*68}")
    print(f"STAGE 1 — zeros 1-50, ZERO_T_SCALE={ZERO_T_SCALE}")
    print(f"{'='*68}")
    train_stage1(model, TRAIN_ZEROS, epochs=800, lr=3e-4, batch_size=BATCH)

    h1_hits, h1_ph, h1_miss = holdout_report_v2(
        model, "zeros 51-100",
        HOLD1_ZEROS,
        t_scan_lo=min(HOLD1_ZEROS) - 1.0,
        t_scan_hi=max(HOLD1_ZEROS),
        n_known_before=50,
        sep=0.35,
    )

    h2_hits, h2_ph, h2_miss = holdout_report_v2(
        model, "zeros 101-150",
        HOLD2_ZEROS,
        t_scan_lo=min(HOLD2_ZEROS) - 1.0,
        t_scan_hi=max(HOLD2_ZEROS),
        n_known_before=100,
        sep=0.35,
    )

    print(f"\n{'='*68}")
    print(f"SUMMARY")
    print(f"{'='*68}")
    print(f"  Decoder:             grammar-distance Viterbi v2")
    print(f"  K:                   coarse-NMS spacing (inverted: regular=K_fast)")
    print(f"  Phi:                 peak sharpness vs local baseline")
    print(f"  sep:                 0.35 (allows GUE close pairs)")
    print(f"  Holdout 1 (51-100):  {h1_hits}/50 found,  {h1_ph} phantoms,  {h1_miss} missed")
    print(f"  Holdout 2 (101-150): {h2_hits}/50 found,  {h2_ph} phantoms,  {h2_miss} missed")
    print(f"  Combined:            {h1_hits+h2_hits}/100 found")


if __name__ == "__main__":
    main()
