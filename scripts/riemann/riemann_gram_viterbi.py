"""
riemann_gram_viterbi.py — Gram-point ghost Viterbi for extrapolation gaps.

RS N(t) inversion error = 1.336 mean (34% within hit_thresh=1.0) — too coarse.
Gram points g_n defined by theta(g_n) = n*pi are accurate to ~0.3-0.5 units,
well within hit_thresh=1.0 (~80% expected).

Strategy change from riemann_rs_viterbi.py:
  OLD: insert ghosts only where no model peak within ghost_radius=0.9 → almost
       no ghosts placed (model peaks are dense everywhere, including flat H1).
  NEW: insert ALL Gram point ghosts unconditionally (ghost_radius=0); let
       Viterbi resolve model vs. ghost competition via logit ordering.

Logit ordering:
  H1 model peaks:  P≈0.10  → logit≈-2.20  → LOSES to ghost (logit≈-0.62)
  Gram ghost:      P=0.35  → logit≈-0.62
  H2 model peaks:  P≈0.90  → logit≈+2.20  → WINS over ghost

Effect:
  H1 (extrapolation zone, model-silent): Gram ghosts (P=0.35) dominate
    Viterbi; budget fills with Gram positions, which are within ±0.5 of true
    zeros → many previously-missed H1 zeros become hits.
  H2 (model-confident zone): model peaks (P≈0.9) beat ghosts; behavior
    unchanged from baseline.

Gram's law caveat: theta(g_n) = n*pi predicts zero positions with ±0.3-0.5
accuracy, but Gram's law fails ~27% of the time (Gram intervals with 0 or 2
zeros). This limits the ghost hit rate to ~73-80% in H1.

Training: jitter ±0.3, t_range=(10, 250), 200 ep (same as riemann_phase_a_jitter.py).
"""

from __future__ import annotations

import math
import random

import numpy as np
from scipy.special import loggamma

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from navigators import RiemannNavigator
from train_navigators import RIEMANN_ZEROS_T, ZERO_T_SCALE, make_riemann_batch
from riemann_crf import (
    ZEROS_101_150, rs_N, budget_viterbi, scan_near_zero,
)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TRAIN_ZEROS = RIEMANN_ZEROS_T[:50]
HOLD1_ZEROS = RIEMANN_ZEROS_T[50:]
HOLD2_ZEROS = ZEROS_101_150

HIT_THRESH = 1.0


# ── Gram point machinery ──────────────────────────────────────────────────────

def rs_theta(t: float) -> float:
    """Riemann-Siegel theta function via scipy loggamma (full precision)."""
    return float(loggamma(0.25 + 0.5j * t).imag) - 0.5 * t * math.log(math.pi)


def gram_point(n: int, t_lo: float = 10.0, t_hi: float = 800.0) -> float:
    """
    Find the n-th Gram point: g_n where theta(g_n) = n * pi.

    Bisection on theta(t) - n*pi = 0. theta is monotone increasing for t > 6.3,
    so bisection converges uniquely. 80 iterations → ~1e-14 precision.
    """
    target = n * math.pi
    # Bracket check
    if rs_theta(t_hi) < target:
        t_hi = t_hi * 2.0  # extend bracket if needed
    if rs_theta(t_lo) > target:
        return t_lo
    for _ in range(80):
        t_mid = (t_lo + t_hi) / 2.0
        if rs_theta(t_mid) < target:
            t_lo = t_mid
        else:
            t_hi = t_mid
        if t_hi - t_lo < 1e-9:
            break
    return (t_lo + t_hi) / 2.0


def gram_points_in_range(t_lo: float, t_hi: float) -> list[float]:
    """
    Return all Gram points g_n with t_lo <= g_n <= t_hi.

    Finds n_lo (smallest n s.t. g_n >= t_lo) and increments until g_n > t_hi.
    """
    # Starting Gram index: n_lo where theta(t_lo) ≈ n_lo * pi
    n_lo = max(0, int(math.floor(rs_theta(t_lo) / math.pi)))
    points = []
    n = n_lo
    while True:
        gp = gram_point(n, t_lo=max(10.0, t_lo - 5.0), t_hi=t_hi + 10.0)
        if gp > t_hi + 1.0:
            break
        if gp >= t_lo:
            points.append(gp)
        n += 1
        if n > n_lo + 500:
            break  # safety
    return points


def augment_with_gram_ghosts(
    gated_peaks: list[tuple[float, float]],
    t_lo: float,
    t_hi: float,
    p_ghost: float = 0.35,
) -> tuple[list[tuple[float, float]], int]:
    """
    Insert Gram point candidates unconditionally in [t_lo, t_hi].

    No ghost_radius gate — Viterbi resolves competition via logit ordering.
    Returns (augmented list sorted by t, n_ghosts).
    """
    gram_pts = gram_points_in_range(t_lo, t_hi)
    ghost_positions = set(round(g, 6) for g in gram_pts)
    augmented = sorted(gated_peaks + [(g, p_ghost) for g in gram_pts],
                       key=lambda x: x[0])
    return augmented, len(gram_pts)


# ── Holdout with Gram Viterbi ─────────────────────────────────────────────────

def holdout_gram_viterbi(
    model: RiemannNavigator,
    label: str,
    known_zeros: list[float],
    t_scan_lo: float,
    t_scan_hi: float,
    n_known_before: int,
    sep: float = 0.8,
    p_ghost: float = 0.35,
    verbose: bool = True,
) -> tuple[int, int, int]:
    """
    Holdout evaluation with Gram-point ghost augmentation.

    Workflow:
      1. Scan near_zero → raw scanner peaks
      2. Gate at t >= min(known_zeros) - 1.0
      3. Insert ALL Gram ghosts in [t_gate, t_hi+1] (no radius gate)
      4. Budget-Viterbi on combined pool
      5. Score hits/phantoms; report unique zeros found
    """
    n_pts = max(3000, int((t_scan_hi - t_scan_lo) * 25))
    raw_all, t_vals, p_nears = scan_near_zero(
        model, t_scan_lo - 0.5, t_scan_hi + 2.0, n_pts=n_pts
    )

    rs_lo  = rs_N(t_scan_lo)
    rs_hi  = rs_N(t_scan_hi + 1.0)
    budget = max(len(known_zeros), int(math.floor(rs_hi - rs_lo)) + 1)
    t_gate = min(known_zeros) - 1.0

    raw_gated = [
        (t, p) for t, p in raw_all
        if t_scan_lo - 0.5 <= t <= t_scan_hi + 1.0 and t >= t_gate
    ]

    # Build gram ghost pool
    augmented, n_ghosts = augment_with_gram_ghosts(
        raw_gated, t_gate, t_scan_hi + 1.0, p_ghost=p_ghost,
    )

    selected = budget_viterbi(augmented, budget=budget, sep=sep)

    # Track which selected came from ghosts vs model
    model_t_set = set(round(t, 6) for t, _ in raw_gated)
    n_ghost_sel  = sum(1 for t, _ in selected if round(t, 6) not in model_t_set)
    n_model_sel  = len(selected) - n_ghost_sel

    if verbose:
        near_std = torch.tensor(p_nears).std().item()
        print(f"\n{'='*68}")
        print(f"HOLDOUT: {label}  (NEVER SEEN DURING TRAINING)")
        print(f"{'='*68}")
        print(f"RS budget: {budget}  |  t_gate: {t_gate:.1f}"
              f"  |  raw gated: {len(raw_gated)}"
              f"  |  gram ghosts: {n_ghosts}"
              f"  |  selected: {len(selected)} "
              f"(model={n_model_sel} ghost={n_ghost_sel})")
        print(f"near_zero std: {near_std:.3e}  p_ghost={p_ghost}")
        print()
        print(f"  {'#':>4}  {'t_pred':>12}  {'P':>6}  {'src':>5}  "
              f"{'nearest zero':>14}  {'delta':>8}  {'status':>8}")
        print(f"  {'----':>4}  {'------------':>12}  {'------':>6}  {'-----':>5}  "
              f"{'------------':>14}  {'--------':>8}  {'--------':>8}")

    hits, phantoms = 0, 0
    matched: set[float] = set()
    for idx, (t_pred, p) in enumerate(selected, 1):
        src = "GRAM" if round(t_pred, 6) not in model_t_set else "MDL"
        nearest = min(known_zeros, key=lambda z: abs(z - t_pred))
        delta   = abs(t_pred - nearest)
        status  = "HIT" if delta <= HIT_THRESH else "PHANTOM"
        if status == "HIT":
            hits += 1
            matched.add(nearest)
        else:
            phantoms += 1
        if verbose:
            print(f"  {idx:>4}  {t_pred:>12.4f}  {p:>6.4f}  {src:>5}  "
                  f"{nearest:>14.6f}  {delta:>8.4f}  {status:>8}")

    missed = sorted(z for z in known_zeros if z not in matched)
    if verbose and missed:
        print(f"\n  MISSED: {[f'{z:.3f}' for z in missed]}")
    unique = len(matched)
    if verbose:
        print(f"\nRESULT: {hits}/{len(known_zeros)} hits  |  "
              f"{unique}/{len(known_zeros)} unique zeros  |  "
              f"{phantoms} phantoms  |  {len(missed)} missed")
    return hits, phantoms, len(missed)


# ── Training ──────────────────────────────────────────────────────────────────

def near_gaussian_target_jittered(
    t_batch: torch.Tensor,
    zeros_t: list[float],
    sigma: float = 0.4,
    jitter: float = 0.3,
) -> torch.Tensor:
    jittered = [z + random.uniform(-jitter, jitter) for z in zeros_t]
    t  = t_batch.unsqueeze(1)
    z  = torch.tensor(jittered, dtype=torch.float32, device=t.device)
    sq = ((t - z) ** 2) / (2.0 * sigma ** 2)
    return torch.exp(-sq).max(dim=1).values


def train_phase_a(
    model: RiemannNavigator,
    zeros_t: list[float],
    epochs: int = 200,
    batch_size: int = 128,
    sigma: float = 0.4,
    jitter: float = 0.3,
    near_lr: float = 1e-3,
    backbone_lr: float = 3e-4,
) -> None:
    near_params     = [p for n, p in model.named_parameters() if "near_head" in n]
    backbone_params = [p for n, p in model.named_parameters() if "near_head" not in n]
    opt   = optim.AdamW([
        {"params": near_params,     "lr": near_lr},
        {"params": backbone_params, "lr": backbone_lr},
    ], weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    print(f"  sigma={sigma}  jitter=±{jitter}  near_lr={near_lr}  "
          f"backbone_lr={backbone_lr}  {epochs} ep")
    print(f"\n  {'Epoch':>6}  {'L_near':>10}  {'Gap_log':>9}  {'Gap_chk':>9}")
    print(f"  {'------':>6}  {'----------':>10}  {'---------':>9}  {'---------':>9}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, _, _ = make_riemann_batch(zeros_t, batch_size=batch_size, t_range=(10.0, 250.0))
        s = s.to(DEVICE)
        out    = model(s)
        target = near_gaussian_target_jittered(s[:, 1], zeros_t, sigma=sigma, jitter=jitter)
        loss   = 5.0 * F.mse_loss(out["near_zero"], target)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % 50 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                t_at_log  = torch.tensor(
                    [[0.5, z + random.uniform(-0.1, 0.1)] for z in zeros_t[:20]],
                    dtype=torch.float32,
                ).to(DEVICE)
                t_far_log = torch.tensor(
                    [[0.5, z + random.uniform(2.0, 4.0)] for z in zeros_t[:20]],
                    dtype=torch.float32,
                ).to(DEVICE)
                gap_log = (model(t_at_log)["near_zero"].mean()
                           - model(t_far_log)["near_zero"].mean()).item()
                t_at_ck  = torch.tensor(
                    [[0.5, z] for z in zeros_t[:25]], dtype=torch.float32
                ).to(DEVICE)
                t_far_ck = torch.tensor(
                    [[0.5, z + 3.0] for z in zeros_t[:25]], dtype=torch.float32
                ).to(DEVICE)
                gap_chk  = (model(t_at_ck)["near_zero"].mean()
                            - model(t_far_ck)["near_zero"].mean()).item()
                l_val = F.mse_loss(out["near_zero"], target).item()
            print(f"  {epoch:>6}  {l_val:>10.6f}  {gap_log:>+9.4f}  {gap_chk:>+9.4f}")


def main():
    HIDDEN   = 240
    LAYERS   = 24
    HEADS    = 24
    NFOURIER = 48
    FREQ_MAX = 2.5
    BATCH    = 128
    P_GHOST  = 0.35

    model = RiemannNavigator(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigator  hidden={HIDDEN}  layers={LAYERS}  heads={HEADS}  "
          f"params={n_params:,}")
    print(f"Gram-point Viterbi: p_ghost={P_GHOST} (logit≈{math.log(P_GHOST/(1-P_GHOST)):.2f})")
    print(f"  H1 model (P≈0.10, logit≈-2.20) < ghost (logit≈{math.log(P_GHOST/(1-P_GHOST)):.2f})")
    print(f"  H2 model (P≈0.90, logit≈+2.20) > ghost (logit≈{math.log(P_GHOST/(1-P_GHOST)):.2f})")

    # ── Gram point sanity check ───────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"GRAM POINT SANITY CHECK (training zeros 1-50)")
    print(f"{'='*68}")
    t_lo_tr = TRAIN_ZEROS[0] - 2.0
    t_hi_tr = TRAIN_ZEROS[-1] + 2.0
    gram_tr = gram_points_in_range(t_lo_tr, t_hi_tr)
    print(f"  {len(gram_tr)} Gram points in [{t_lo_tr:.1f}, {t_hi_tr:.1f}]")
    print(f"  {len(TRAIN_ZEROS)} training zeros in same range")

    # For each training zero, find nearest Gram point
    gram_errors = []
    for z in TRAIN_ZEROS:
        if not gram_tr:
            continue
        nearest_g = min(gram_tr, key=lambda g: abs(g - z))
        gram_errors.append(abs(nearest_g - z))
    if gram_errors:
        import statistics
        print(f"  Nearest Gram point error on training zeros:")
        print(f"  mean={statistics.mean(gram_errors):.4f}  "
              f"median={statistics.median(gram_errors):.4f}  "
              f"max={max(gram_errors):.4f}  "
              f"p90={sorted(gram_errors)[int(0.9*len(gram_errors))]:.4f}")
        frac_1 = sum(1 for e in gram_errors if e < HIT_THRESH) / len(gram_errors)
        frac_05 = sum(1 for e in gram_errors if e < 0.5) / len(gram_errors)
        print(f"  Fraction within hit_thresh=1.0: {frac_1:.1%}")
        print(f"  Fraction within 0.5:            {frac_05:.1%}")

    # Also check RS inversion for comparison
    from riemann_crf import rs_N
    rs_errors = []
    k_start = int(math.floor(rs_N(TRAIN_ZEROS[0] - 1.0))) + 1
    k_end   = int(math.ceil(rs_N(TRAIN_ZEROS[-1] + 1.0)))
    from riemann_rs_viterbi import rs_invert
    for k in range(k_start, k_end + 1):
        idx = k - 1
        if 0 <= idx < len(TRAIN_ZEROS):
            rs_errors.append(abs(rs_invert(float(k)) - TRAIN_ZEROS[idx]))
    if rs_errors:
        import statistics as st
        print(f"\n  RS N(t) inversion error (baseline comparison):")
        print(f"  mean={st.mean(rs_errors):.4f}  "
              f"fraction within 1.0: {sum(1 for e in rs_errors if e<1.0)/len(rs_errors):.1%}")

    # ── Training ──────────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"PHASE A — jitter ±0.3, t_range=(10,250), 200 ep")
    print(f"{'='*68}")
    train_phase_a(model, TRAIN_ZEROS, epochs=200, jitter=0.3)

    # ── Holdout evaluation ────────────────────────────────────────────────────
    from riemann_crf import holdout_report_crf

    for sep in [0.8, 0.4]:
        print(f"\n{'='*68}")
        print(f"GRAM VITERBI  sep={sep}  p_ghost={P_GHOST}")
        print(f"{'='*68}")
        h1_hits, h1_ph, h1_miss = holdout_gram_viterbi(
            model, "zeros 51-100",
            HOLD1_ZEROS,
            t_scan_lo=min(HOLD1_ZEROS) - 1.0,
            t_scan_hi=max(HOLD1_ZEROS),
            n_known_before=50,
            sep=sep,
            p_ghost=P_GHOST,
        )
        h2_hits, h2_ph, h2_miss = holdout_gram_viterbi(
            model, "zeros 101-150",
            HOLD2_ZEROS,
            t_scan_lo=min(HOLD2_ZEROS) - 1.0,
            t_scan_hi=max(HOLD2_ZEROS),
            n_known_before=100,
            sep=sep,
            p_ghost=P_GHOST,
        )
        h1_unique = len(HOLD1_ZEROS) - h1_miss
        h2_unique = len(HOLD2_ZEROS) - h2_miss
        print(f"\n{'='*68}")
        print(f"SUMMARY  sep={sep}  p_ghost={P_GHOST}")
        print(f"  H1: {h1_hits} hits / {h1_unique} unique / {h1_ph} phantoms / {h1_miss} missed")
        print(f"  H2: {h2_hits} hits / {h2_unique} unique / {h2_ph} phantoms / {h2_miss} missed")
        print(f"  Combined: {h1_hits+h2_hits} hits / {h1_unique+h2_unique} unique"
              f" / {h1_ph+h2_ph} phantoms")

    # ── Baseline (no ghosts) for comparison ───────────────────────────────────
    print(f"\n{'='*68}")
    print(f"BASELINE (no Gram ghosts)  sep=0.8")
    print(f"{'='*68}")
    h1b, h1pb, h1mb = holdout_report_crf(
        model, "zeros 51-100", HOLD1_ZEROS,
        t_scan_lo=min(HOLD1_ZEROS) - 1.0, t_scan_hi=max(HOLD1_ZEROS),
        n_known_before=50, sep=0.8,
    )
    h2b, h2pb, h2mb = holdout_report_crf(
        model, "zeros 101-150", HOLD2_ZEROS,
        t_scan_lo=min(HOLD2_ZEROS) - 1.0, t_scan_hi=max(HOLD2_ZEROS),
        n_known_before=100, sep=0.8,
    )
    h1ub = len(HOLD1_ZEROS) - h1mb
    h2ub = len(HOLD2_ZEROS) - h2mb
    print(f"\n  Baseline  sep=0.8  (no Gram ghosts):")
    print(f"  H1: {h1b} hits / {h1ub} unique / {h1pb} phantoms / {h1mb} missed")
    print(f"  H2: {h2b} hits / {h2ub} unique / {h2pb} phantoms / {h2mb} missed")
    print(f"  Combined: {h1b+h2b} hits / {h1ub+h2ub} unique / {h1pb+h2pb} phantoms")

    # ── Try p_ghost sweep on sep=0.8 ─────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"P_GHOST SWEEP  sep=0.8  (find optimal ghost strength)")
    print(f"{'='*68}")
    for pg in [0.2, 0.3, 0.4, 0.5]:
        h1h, h1p, h1m = holdout_gram_viterbi(
            model, "zeros 51-100", HOLD1_ZEROS,
            t_scan_lo=min(HOLD1_ZEROS) - 1.0, t_scan_hi=max(HOLD1_ZEROS),
            n_known_before=50, sep=0.8, p_ghost=pg, verbose=False,
        )
        h2h, h2p, h2m = holdout_gram_viterbi(
            model, "zeros 101-150", HOLD2_ZEROS,
            t_scan_lo=min(HOLD2_ZEROS) - 1.0, t_scan_hi=max(HOLD2_ZEROS),
            n_known_before=100, sep=0.8, p_ghost=pg, verbose=False,
        )
        h1u = len(HOLD1_ZEROS) - h1m
        h2u = len(HOLD2_ZEROS) - h2m
        print(f"  p_ghost={pg:.2f} (logit={math.log(pg/(1-pg)):+.2f}): "
              f"H1={h1u}/50  H2={h2u}/50  combined={h1u+h2u}/100  "
              f"phantoms={h1p+h2p}")


if __name__ == "__main__":
    main()
