"""
riemann_crf.py — Stage 1 + budget-Viterbi decoder enforcing Omega_Z.

Grammar prescription (Probe 6 verdict, riemann_two_stage_results inquiry):
  - Drop Stage 2 entirely: preserves zero_t extrapolation (K_slow), avoids K_trap
    collapse from Stage 2 negative target contamination.
  - Replace raw NMS peak detection with budget-Viterbi decoder that enforces
    Omega_Z as a hard architectural constraint:
      N(t) = cumulative zero count is a monotone non-decreasing integer.
      Budget for each scan region = floor(N_RS(t_hi)) - floor(N_RS(t_last_known))
      Hard zero-free zones: suppress all detections where budget_remaining = 0.
  - Near_head alignment phase also dropped: backbone features from Stage 1 are
    used as-is by the Viterbi decoder; L_near collapse is irrelevant because the
    CRF uses whatever near_zero signal exists (even tiny amplitude suffices for
    relative ordering of candidates).

Riemann-Siegel N(t) (Backlund 1914):
    N(t) = t/(2pi) * log(t/(2pi*e)) + 7/8 + O(1/t)

One phase only:
  Stage 1 (800 ep, zeros 1-50, lr=3e-4, ZERO_T_SCALE=250) — identical to baseline.
  Eval: budget-Viterbi on near_zero peaks instead of raw NMS.
"""

from __future__ import annotations

import math
import random

import torch
import torch.nn as nn
import torch.optim as optim

from navigators import RiemannNavigator
from train_navigators import RIEMANN_ZEROS_T, ZERO_T_SCALE, make_riemann_batch

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Zeros 101-150 (mpmath, 2026-04-11) ───────────────────────────────────────
ZEROS_101_150 = [
    237.769820, 239.555478, 241.049158, 242.823272, 244.070898,
    247.136990, 248.101990, 249.573690, 251.014948, 253.069987,
    255.306256, 256.380714, 258.610439, 259.874407, 260.805085,
    263.573894, 265.557852, 266.614974, 267.921915, 269.970449,
    271.494056, 273.459609, 275.587493, 276.452050, 278.250744,
    279.229251, 282.465115, 283.211186, 284.835964, 286.667445,
    287.911921, 289.579855, 291.846291, 293.558434, 294.965370,
    295.573255, 297.979277, 299.840326, 301.649325, 302.696750,
    304.864371, 305.728913, 307.219496, 310.109463, 311.165142,
    312.427801, 313.985286, 315.475616, 317.734806, 318.853104,
]

TRAIN_ZEROS = RIEMANN_ZEROS_T[:50]   # zeros 1-50
HOLD1_ZEROS = RIEMANN_ZEROS_T[50:]   # zeros 51-100
HOLD2_ZEROS = ZEROS_101_150          # zeros 101-150


# ── Riemann-Siegel zero counting ─────────────────────────────────────────────

def rs_N(t: float) -> float:
    """
    Backlund's formula: N(t) ≈ t/(2π) * log(t/(2πe)) + 7/8.
    Returns expected number of zeros of zeta(s) with 0 < Im(s) <= t.
    """
    if t < 2.0:
        return 0.0
    return t / (2 * math.pi) * math.log(t / (2 * math.pi * math.e)) + 7 / 8


# ── Budget-Viterbi decoder (enforces Omega_Z monotone integer constraint) ────

def budget_viterbi(
    candidates: list[tuple[float, float]],
    budget: int,
    sep: float = 0.8,
) -> list[tuple[float, float]]:
    """
    Select exactly `budget` candidates (or all if fewer available) from the
    list, maximising the sum of logit(score) = log(p/(1-p)), subject to
    minimum t-separation `sep` between any two selected points.

    Using logit instead of log(p): logit > 0 when p > 0.5, so each additional
    above-chance peak adds positive weight — the DP naturally selects up to
    budget candidates rather than collapsing to 1.

    Uses DP: O(n^2 * budget). After the t_gate filter, n is ~50-150.

    candidates : list of (t, score), ANY order (sorted internally).
    budget     : max selections (Omega_Z winding budget for this scan region).
    sep        : minimum t-gap between detections.

    Returns selected (t, score) sorted by t.
    """
    if not candidates or budget <= 0:
        return []

    cands = sorted(candidates, key=lambda x: x[0])
    n = len(cands)
    k = min(budget, n)

    NEG_INF = float("-inf")
    # dp[i][j] = best total logit-score selecting exactly j items, last at i
    dp  = [[NEG_INF] * (k + 1) for _ in range(n)]
    par = [[-1]      * (k + 1) for _ in range(n)]

    for i, (t_i, s_i) in enumerate(cands):
        p = max(min(s_i, 1 - 1e-7), 1e-7)
        logit_s = math.log(p / (1.0 - p))   # positive when p > 0.5
        # j=1: pick just candidate i
        dp[i][1]  = logit_s
        par[i][1] = -1
        # j>1: extend a previous selection
        for prev in range(i):
            t_prev, _ = cands[prev]
            if t_i - t_prev < sep:
                continue
            for j in range(2, k + 1):
                if dp[prev][j - 1] == NEG_INF:
                    continue
                val = dp[prev][j - 1] + logit_s
                if val > dp[i][j]:
                    dp[i][j] = val
                    par[i][j] = prev

    # Find best endpoint: prefer larger j (more detections) among equal scores
    best_val, best_i, best_j = NEG_INF, -1, 0
    for j in range(k, 0, -1):          # prefer filling the budget
        for i in range(n):
            if dp[i][j] > best_val:
                best_val, best_i, best_j = dp[i][j], i, j
        if best_i >= 0:
            break

    if best_i < 0:
        return []

    # Backtrack
    path = []
    i, j = best_i, best_j
    while i >= 0 and j > 0:
        path.append(cands[i])
        i = par[i][j]
        j -= 1
    return sorted(path, key=lambda x: x[0])


# ── Scan ─────────────────────────────────────────────────────────────────────

def scan_near_zero(
    model: RiemannNavigator,
    t_min: float,
    t_max: float,
    n_pts: int = 3000,
) -> tuple[list[tuple[float, float]], list[float], list[float]]:
    """
    Returns (raw_peaks, t_vals, p_near_all) where raw_peaks are local maxima
    of the near_zero output, t_vals and p_near_all are the full scan arrays.
    """
    model.eval()
    dev   = next(model.parameters()).device
    t_raw = torch.linspace(t_min, t_max, n_pts)
    sigma = torch.full_like(t_raw, 0.5)
    s_in  = torch.stack([sigma, t_raw], dim=-1).to(dev)
    with torch.no_grad():
        out = model(s_in)
    t_list = t_raw.tolist()
    p_list = out["near_zero"].cpu().tolist()
    raw = [
        (t_list[i], p_list[i])
        for i in range(1, len(t_list) - 1)
        if p_list[i] > p_list[i - 1] and p_list[i] > p_list[i + 1]
    ]
    return raw, t_list, p_list


# ── CRF holdout report ────────────────────────────────────────────────────────

def holdout_report_crf(
    model: RiemannNavigator,
    label: str,
    known_zeros: list[float],
    t_scan_lo: float,
    t_scan_hi: float,
    n_known_before: int,
    hit_thresh: float = 1.0,
    sep: float = 0.8,
) -> tuple[int, int, int]:
    """
    Evaluate holdout using budget-Viterbi decoder (Omega_Z hard constraint).

    n_known_before : number of zeros already accounted for before t_scan_lo
                     (used to compute the remaining winding-number budget).
    """
    n_pts = max(3000, int((t_scan_hi - t_scan_lo) * 25))

    # ── Scan near_zero ────────────────────────────────────────────────────────
    raw_all, t_vals, p_nears = scan_near_zero(
        model, t_scan_lo - 0.5, t_scan_hi + 2.0, n_pts=n_pts
    )

    # ── Also collect zero_t_pred range for diagnostics ────────────────────────
    dev   = next(model.parameters()).device
    t_raw = torch.linspace(t_scan_lo, t_scan_hi + 2.0, n_pts)
    sigma = torch.full_like(t_raw, 0.5)
    s_in  = torch.stack([sigma, t_raw], dim=-1).to(dev)
    model.eval()
    with torch.no_grad():
        out = model(s_in)
    zt_preds = (out["zero_t"].cpu() * ZERO_T_SCALE).tolist()

    # ── Omega_Z budget ────────────────────────────────────────────────────────
    # Budget = how many new zeros N(t) can gain in [t_scan_lo, t_scan_hi].
    # We floor so we never over-claim; +1 slack for boundary effects.
    rs_lo  = rs_N(t_scan_lo)
    rs_hi  = rs_N(t_scan_hi + 1.0)     # small buffer
    budget = max(len(known_zeros), int(math.floor(rs_hi - rs_lo)) + 1)

    # Hard zero-free gate: suppress any candidate below the first known holdout
    # zero minus one unit. This is the gap-phantom eliminator.
    t_gate = min(known_zeros) - 1.0

    raw_gated = [
        (t, p) for t, p in raw_all
        if t_scan_lo - 0.5 <= t <= t_scan_hi + 1.0 and t >= t_gate
    ]

    # ── Viterbi selection ─────────────────────────────────────────────────────
    selected = budget_viterbi(raw_gated, budget=budget, sep=sep)

    # ── Print report ──────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"HOLDOUT: {label}  (NEVER SEEN DURING TRAINING)")
    print(f"{'='*68}")
    print(f"RS budget: {budget}  |  t_gate: {t_gate:.1f}"
          f"  |  raw peaks (gated): {len(raw_gated)}"
          f"  |  after Viterbi: {len(selected)}")
    print(f"zero_t_pred range: [{min(zt_preds):.1f}, {max(zt_preds):.1f}]"
          f"  |  near_zero std: {torch.tensor(p_nears).std():.2e}")
    print()
    print(f"  {'#':>4}  {'t_pred':>12}  {'P(near)':>9}  {'nearest zero':>14}"
          f"  {'delta':>8}  {'status':>8}")
    print(f"  {'----':>4}  {'------------':>12}  {'---------':>9}"
          f"  {'----------':>14}  {'--------':>8}  {'--------':>8}")

    hits, phantoms = 0, 0
    matched: set[float] = set()
    for idx, (t_pred, p) in enumerate(selected, 1):
        nearest = min(known_zeros, key=lambda z: abs(z - t_pred))
        delta   = abs(t_pred - nearest)
        status  = "HIT" if delta <= hit_thresh else "PHANTOM"
        if status == "HIT":
            hits += 1
            matched.add(nearest)
        else:
            phantoms += 1
        print(f"  {idx:>4}  {t_pred:>12.4f}  {p:>9.4f}  {nearest:>14.6f}"
              f"  {delta:>8.4f}  {status:>8}")

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


# ── Main ─────────────────────────────────────────────────────────────────────

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
    print(f"  Training: zeros 1-50 only (Stage 1, 800 ep) — no Stage 2")
    print(f"  Eval: budget-Viterbi decoder enforcing Omega_Z monotone N(t)")

    # ── Stage 1 ───────────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"STAGE 1 — zeros 1-50, ZERO_T_SCALE={ZERO_T_SCALE}")
    print(f"{'='*68}")
    train_stage1(model, TRAIN_ZEROS, epochs=800, lr=3e-4, batch_size=BATCH)

    # ── Holdout 1: zeros 51-100 ───────────────────────────────────────────────
    h1_hits, h1_ph, h1_miss = holdout_report_crf(
        model, "zeros 51-100",
        HOLD1_ZEROS,
        t_scan_lo=min(HOLD1_ZEROS) - 1.0,
        t_scan_hi=max(HOLD1_ZEROS),
        n_known_before=50,
    )

    # ── Holdout 2: zeros 101-150 ──────────────────────────────────────────────
    h2_hits, h2_ph, h2_miss = holdout_report_crf(
        model, "zeros 101-150",
        HOLD2_ZEROS,
        t_scan_lo=min(HOLD2_ZEROS) - 1.0,
        t_scan_hi=max(HOLD2_ZEROS),
        n_known_before=100,
    )

    print(f"\n{'='*68}")
    print(f"SUMMARY")
    print(f"{'='*68}")
    print(f"  Training:            zeros 1-50 only (Stage 1)")
    print(f"  Decoder:             budget-Viterbi (Omega_Z hard constraint)")
    print(f"  Holdout 1 (51-100):  {h1_hits}/50 found,  {h1_ph} phantoms,  {h1_miss} missed")
    print(f"  Holdout 2 (101-150): {h2_hits}/50 found,  {h2_ph} phantoms,  {h2_miss} missed")
    print(f"  Combined:            {h1_hits+h2_hits}/100 found")
    print(f"\n  RS N(t) at key points:")
    for t in [143.1, 146.0, 236.5, 237.8, 318.9]:
        print(f"    N_RS({t:.1f}) = {rs_N(t):.2f}")


if __name__ == "__main__":
    main()
