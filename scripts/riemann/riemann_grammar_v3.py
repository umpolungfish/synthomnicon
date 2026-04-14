"""
riemann_grammar_v3.py — Grammar-distance Viterbi with fixed K computation.

Bug in v2: non-coarse raw peaks have nearest coarse peak = their NMS suppressor
(distance < 0.5), giving k_ratio << 1 → K_slow for ALL suppressed peaks.
Intent was inverted: suppressed peaks (weaker signal) all look like true zeros.

Fix: compute K from coarse-peak spacing ONLY, then propagate to nearby raw peaks.

Corrected K logic:
  For each COARSE peak c_i, compute spacing to nearest other COARSE peak c_j.
  k_ratio = spacing / rs_mean_spacing(c_i).
  k_ratio ∈ [0.60, 1.40] → K_fast  (near-RS-mean spacing: rhythmic, phantom)
  k_ratio ∈ [0.40, 0.60) or (1.40, 1.60] → K_mod
  k_ratio < 0.40 or > 1.60 → K_slow  (compressed pair or isolated: GUE, zero)

  Each raw peak inherits K of its nearest coarse peak.

GUE level-repulsion observability:
  - Phantom clusters in gaps: coarse-coarse spacing ≈ RS mean → K_fast
  - Close zero pairs: coarse-coarse spacing << RS mean → K_slow
  - Isolated zeros (wide gap before): coarse-coarse spacing >> RS mean → K_slow

Phi: unchanged (peak sharpness above local baseline).

sep=0.35: allows GUE close pairs through; grammar score suppresses regular phantoms.
"""

from __future__ import annotations

import math
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
    if t < 4.0:
        return 2.0
    return 2.0 * math.pi / math.log(t / (2.0 * math.pi))


def nms_coarsen(
    candidates: list[tuple[float, float]],
    window_frac: float = 0.45,
) -> list[tuple[float, float]]:
    """NMS: for each local maximum in window = window_frac * rs_mean(t), keep highest p."""
    if not candidates:
        return []
    cands = sorted(candidates, key=lambda x: x[0])
    suppressed = [False] * len(cands)
    for i in range(len(cands)):
        if suppressed[i]:
            continue
        t_i, p_i = cands[i]
        win = rs_mean_spacing(t_i) * window_frac
        for j in range(i + 1, len(cands)):
            t_j, p_j = cands[j]
            if t_j - t_i > win:
                break
            if p_j <= p_i:
                suppressed[j] = True
            else:
                suppressed[i] = True
                break
    return [(t, p) for (t, p), s in zip(cands, suppressed) if not s]


def _coarse_k_assign(
    coarse: list[tuple[float, float]],
    k_fast_tight: float = 0.40,   # |k_ratio-1| < this → K_fast
    k_fast_mid: float  = 0.60,    # |k_ratio-1| < this → K_mod
) -> list[str]:
    """
    For each coarse peak, assign K primitive from spacing to nearest OTHER coarse peak.

    k_ratio = nearest_coarse_distance / rs_mean_spacing(t)
    |k_ratio - 1| <  k_fast_tight → K_fast  (regular: phantom)
    |k_ratio - 1| <  k_fast_mid  → K_mod
    |k_ratio - 1| >= k_fast_mid  → K_slow   (irregular: GUE zero)
    """
    n = len(coarse)
    if n == 0:
        return []
    ts = [c[0] for c in coarse]
    k_vals = []
    for i, (t_i, _) in enumerate(coarse):
        delta_rs = rs_mean_spacing(t_i)
        # Distance to nearest coarse neighbor (not self)
        best = min(
            abs(t_i - ts[j]) for j in range(n) if j != i
        ) if n > 1 else 999.0
        k_ratio = best / delta_rs
        dev = abs(k_ratio - 1.0)
        if dev < k_fast_tight:
            k_vals.append("K_fast")
        elif dev < k_fast_mid:
            k_vals.append("K_mod")
        else:
            k_vals.append("K_slow")
    return k_vals


def grammar_score_v3(
    candidates: list[tuple[float, float]],
    t_vals: list[float],
    p_vals: list[float],
    nms_frac: float = 0.45,
    phi_threshold: float = 0.003,
    k_fast_tight: float = 0.40,
    k_fast_mid: float   = 0.60,
    logit_weight: float = 0.05,
) -> list[tuple[float, float, float]]:
    """
    Fixed grammar scoring:
    1. Coarsen candidates via NMS.
    2. Assign K to each coarse peak from inter-COARSE-peak spacing.
    3. Each raw peak inherits K of its nearest coarse peak.
    4. Phi from local sharpness (unchanged).
    5. grammar_score = d(cand_type, PHANTOM) - d(cand_type, ZERO) + logit_weight*logit(p).
    """
    if not candidates:
        return []

    coarse   = nms_coarsen(candidates, window_frac=nms_frac)
    k_assign = _coarse_k_assign(coarse, k_fast_tight=k_fast_tight, k_fast_mid=k_fast_mid)
    coarse_t = [c[0] for c in coarse]

    scored = []
    for t_i, p_i in candidates:
        # ── K: inherited from nearest coarse peak ─────────────────────────────
        if coarse_t:
            ci = min(range(len(coarse_t)), key=lambda j: abs(t_i - coarse_t[j]))
            k_val = k_assign[ci]
        else:
            k_val = "K_slow"

        # ── Phi: peak sharpness above local baseline ───────────────────────────
        delta_rs = rs_mean_spacing(t_i)
        window   = delta_rs * 0.9
        nbr_ps   = [pv for tv, pv in zip(t_vals, p_vals)
                    if 0.08 < abs(tv - t_i) < window]
        nbr_mean = sum(nbr_ps) / len(nbr_ps) if nbr_ps else p_i
        phi_val  = "Phi_c" if (p_i - nbr_mean) > phi_threshold else "Phi_sub"

        # ── Grammar score ──────────────────────────────────────────────────────
        cand_type         = dict(TRUE_ZERO_TYPE)
        cand_type["K"]    = k_val
        cand_type["Phi"]  = phi_val
        d_zero    = tuple_distance(cand_type, TRUE_ZERO_TYPE)
        d_phantom = tuple_distance(cand_type, PHANTOM_TYPE)
        gscore    = d_phantom - d_zero

        p_clip  = max(min(p_i, 1 - 1e-7), 1e-7)
        logit_p = math.log(p_clip / (1.0 - p_clip))
        total   = gscore + logit_weight * logit_p

        scored.append((t_i, p_i, total))

    return scored


def grammar_viterbi(
    scored_candidates: list[tuple[float, float, float]],
    budget: int,
    sep: float = 0.35,
) -> list[tuple[float, float, float]]:
    if not scored_candidates or budget <= 0:
        return []
    cands = sorted(scored_candidates, key=lambda x: x[0])
    n, k  = len(cands), min(budget, len(cands))
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


def holdout_report_v3(
    model: RiemannNavigator,
    label: str,
    known_zeros: list[float],
    t_scan_lo: float,
    t_scan_hi: float,
    n_known_before: int,
    hit_thresh: float = 1.0,
    sep: float = 0.35,
    nms_frac: float = 0.45,
    phi_threshold: float = 0.003,
    k_fast_tight: float = 0.40,
    k_fast_mid: float   = 0.60,
) -> tuple[int, int, int]:

    n_pts   = max(3000, int((t_scan_hi - t_scan_lo) * 30))
    raw_all, t_vals, p_nears = scan_near_zero(
        model, t_scan_lo - 0.5, t_scan_hi + 2.0, n_pts=n_pts
    )

    rs_lo   = rs_N(t_scan_lo)
    rs_hi   = rs_N(t_scan_hi + 1.0)
    budget  = max(len(known_zeros), int(math.floor(rs_hi - rs_lo)) + 1)
    t_gate  = min(known_zeros) - 1.0

    raw_gated = [(t, p) for t, p in raw_all
                 if t_scan_lo - 0.5 <= t <= t_scan_hi + 1.0 and t >= t_gate]

    coarse   = nms_coarsen(raw_gated, window_frac=nms_frac)
    k_assign = _coarse_k_assign(coarse, k_fast_tight=k_fast_tight,
                                 k_fast_mid=k_fast_mid)

    scored   = grammar_score_v3(
        raw_gated, t_vals, p_nears,
        nms_frac=nms_frac, phi_threshold=phi_threshold,
        k_fast_tight=k_fast_tight, k_fast_mid=k_fast_mid,
    )
    selected = grammar_viterbi(scored, budget=budget, sep=sep)

    # Diagnostics: K distribution of COARSE peaks
    k_coarse_dist = {"K_fast": 0, "K_mod": 0, "K_slow": 0}
    for kv in k_assign:
        k_coarse_dist[kv] += 1

    # K distribution of ALL GATED peaks (inherited from nearest coarse)
    k_gated_dist = {"K_fast": 0, "K_mod": 0, "K_slow": 0}
    coarse_t = [c[0] for c in coarse]
    for t_i, _ in raw_gated:
        if coarse_t:
            ci = min(range(len(coarse_t)), key=lambda j: abs(t_i - coarse_t[j]))
            k_gated_dist[k_assign[ci]] += 1

    gscore_all = [s[2] for s in scored]
    gscore_sel = [s[2] for s in selected]

    print(f"\n{'='*68}")
    print(f"HOLDOUT: {label}  (NEVER SEEN DURING TRAINING)")
    print(f"{'='*68}")
    print(f"RS budget: {budget}  |  t_gate: {t_gate:.1f}"
          f"  |  raw gated: {len(raw_gated)}"
          f"  |  coarse: {len(coarse)}"
          f"  |  after Viterbi: {len(selected)}")
    print(f"  K (coarse peaks): K_fast={k_coarse_dist['K_fast']}"
          f"  K_mod={k_coarse_dist['K_mod']}"
          f"  K_slow={k_coarse_dist['K_slow']}")
    print(f"  K (all gated, inherited): K_fast={k_gated_dist['K_fast']}"
          f"  K_mod={k_gated_dist['K_mod']}"
          f"  K_slow={k_gated_dist['K_slow']}")
    if gscore_all:
        print(f"  grammar (all gated): mean={sum(gscore_all)/len(gscore_all):+.3f}"
              f"  min={min(gscore_all):+.3f}  max={max(gscore_all):+.3f}")
    if gscore_sel:
        unique_scores = sorted(set(f"{s:.3f}" for s in gscore_sel))
        print(f"  grammar (selected):  mean={sum(gscore_sel)/len(gscore_sel):+.3f}"
              f"  unique_vals={unique_scores[:5]}")
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
            hits += 1; matched.add(nearest)
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


def train_stage1(model, zeros_t, epochs=800, lr=3e-4, batch_size=128):
    opt   = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    print(f"\n  {'Epoch':>6}  {'L_frob':>10}  {'L_sym':>10}  {'L_zero':>10}"
          f"  {'L_near':>10}  {'Acc':>7}")
    print(f"  {'------':>6}  {'----------':>10}  {'----------':>10}"
          f"  {'----------':>10}  {'----------':>10}  {'-------':>7}")
    for epoch in range(1, epochs + 1):
        model.train()
        s, near, zero_t = make_riemann_batch(zeros_t, batch_size=batch_size,
                                              t_range=(10.0, 250.0))
        s = s.to(DEVICE); near = near.to(DEVICE); zero_t = zero_t.to(DEVICE)
        out = model(s)
        losses = model.compute_loss(out, true_zero_t=zero_t, true_near=near,
                                    lam_zero=1.0, lam_frob=0.5,
                                    lam_sym=1.0, lam_near=1.0)
        losses["loss"].backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(); sched.step()
        if epoch % 50 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                acc = ((out["near_zero"] > 0.5).float() == near).float().mean().item()
            print(f"  {epoch:>6}  {losses['L_frob']:>10.6f}  {losses['L_sym']:>10.6f}"
                  f"  {losses['L_zero']:>10.6f}  {losses['L_near']:>10.6f}  {acc:>6.1%}")


def main():
    HIDDEN = 240; LAYERS = 24; HEADS = 24; NFOURIER = 48; FREQ_MAX = 2.5; BATCH = 128
    model = RiemannNavigator(hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
                              n_fourier=NFOURIER, freq_max=FREQ_MAX).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigator  hidden={HIDDEN}  layers={LAYERS}  heads={HEADS}")
    print(f"  n_fourier={NFOURIER}  freq_max=10^{FREQ_MAX}  params={n_params:,}")
    print(f"  Decoder: grammar-distance Viterbi v3 (K from coarse-peak spacing)")
    print(f"  K logic: k_ratio~1.0 → K_fast (phantom); far from 1.0 → K_slow (zero)")
    print(f"  d(zero, phantom) = {_D_ARCHETYPES:.3f}")

    print(f"\n{'='*68}")
    print(f"STAGE 1 — zeros 1-50, ZERO_T_SCALE={ZERO_T_SCALE}")
    print(f"{'='*68}")
    train_stage1(model, TRAIN_ZEROS, epochs=800, lr=3e-4, batch_size=BATCH)

    h1_hits, h1_ph, h1_miss = holdout_report_v3(
        model, "zeros 51-100", HOLD1_ZEROS,
        t_scan_lo=min(HOLD1_ZEROS) - 1.0, t_scan_hi=max(HOLD1_ZEROS),
        n_known_before=50, sep=0.35,
    )
    h2_hits, h2_ph, h2_miss = holdout_report_v3(
        model, "zeros 101-150", HOLD2_ZEROS,
        t_scan_lo=min(HOLD2_ZEROS) - 1.0, t_scan_hi=max(HOLD2_ZEROS),
        n_known_before=100, sep=0.35,
    )

    print(f"\n{'='*68}")
    print(f"SUMMARY")
    print(f"{'='*68}")
    print(f"  Decoder:    grammar-distance Viterbi v3 (fixed K from coarse peaks)")
    print(f"  K map:      coarse spacing, k_ratio~1.0=K_fast, far=K_slow")
    print(f"  sep:        0.35 (GUE close pairs)")
    print(f"  H1 (51-100):  {h1_hits}/50 found,  {h1_ph} phantoms,  {h1_miss} missed")
    print(f"  H2 (101-150): {h2_hits}/50 found,  {h2_ph} phantoms,  {h2_miss} missed")
    print(f"  Combined:     {h1_hits+h2_hits}/100 found")


if __name__ == "__main__":
    main()
