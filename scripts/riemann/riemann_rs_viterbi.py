"""
riemann_rs_viterbi.py — RS-density prior Viterbi for gap-filling.

Diagnosis from all prior runs (jitter, restricted, combined):
  Unique zero coverage plateaus at ~75/100 (39 H1 + 36 H2 at sep=0.8).
  "Hard zeros" are consistently missed because the model's near_zero landscape
  is flat-low in H1 (P≈0.1) and produces no peaks at specific H2 positions.
  Budget-Viterbi can only select from scanner peaks — if no peak exists near a
  true zero, that zero is simply invisible.

Fix: augment Viterbi candidates with RS-density ghost positions.

The Backlund formula N(t) ≈ t/(2π)×log(t/(2πe)) + 7/8 gives the expected
cumulative zero count. Inverting gives the expected t-position of the k-th
zero. These "ghosts" are added to the candidate pool with P=p_ghost.

Viterbi scoring (logit):
  - Model peak at P=0.9  → logit = +2.20 (H2 typical) → always beats ghost
  - Model peak at P=0.5  → logit =  0.00  → ties ghost
  - Model peak at P=0.1  → logit = -2.20 (H1 typical) → always loses to ghost
  - Ghost at P=p_ghost=0.5 → logit = 0.0

Ghost placement: only insert ghost at expected position t_k if no model peak
is within ghost_radius (0.9). This ensures ghosts fill genuine gaps without
competing with existing model peaks.

ghost_radius = 0.9 ≈ half the mean RS spacing (~1.8), prevents double-counting.

Training: jitter ±0.3, t_range=(10, 250), 200 ep — best Gap_chk/Gap_log ratio.
"""

from __future__ import annotations

import math
import random

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from navigators import RiemannNavigator
from train_navigators import RIEMANN_ZEROS_T, ZERO_T_SCALE, make_riemann_batch
from riemann_crf import (
    ZEROS_101_150, rs_N, budget_viterbi, scan_near_zero, ZERO_T_SCALE
)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TRAIN_ZEROS = RIEMANN_ZEROS_T[:50]
HOLD1_ZEROS = RIEMANN_ZEROS_T[50:]
HOLD2_ZEROS = ZEROS_101_150

HIT_THRESH = 1.0


# ── RS ghost machinery ────────────────────────────────────────────────────────

def rs_invert(k: float, t_lo: float = 10.0, t_hi: float = 600.0) -> float:
    """Solve N(t) = k via bisection (60 iterations → ~1e-9 precision)."""
    for _ in range(60):
        t_mid = (t_lo + t_hi) / 2.0
        if rs_N(t_mid) < k:
            t_lo = t_mid
        else:
            t_hi = t_mid
    return (t_lo + t_hi) / 2.0


def augment_with_rs_ghosts(
    gated_peaks: list[tuple[float, float]],
    t_gate: float,
    t_hi: float,
    p_ghost: float = 0.5,
    ghost_radius: float = 0.9,
) -> tuple[list[tuple[float, float]], int]:
    """
    Add RS-semiclassical ghost candidates at predicted zero positions.

    A ghost at position t_k (where N(t_k) = k) is added only if no existing
    model peak falls within ghost_radius. Returns (augmented_list, n_ghosts).
    """
    k_lo = int(math.floor(rs_N(t_gate)))
    k_hi = int(math.ceil(rs_N(t_hi + 2.0))) + 2

    ghosts = []
    for k in range(k_lo, k_hi + 1):
        t_k = rs_invert(float(k))
        if t_k < t_gate:
            continue
        if t_k > t_hi + 2.0:
            break
        # Skip if any model peak is already within ghost_radius
        if any(abs(t_k - tp) < ghost_radius for tp, _ in gated_peaks):
            continue
        ghosts.append((t_k, p_ghost))

    augmented = sorted(gated_peaks + ghosts, key=lambda x: x[0])
    return augmented, len(ghosts)


# ── Holdout with RS Viterbi ───────────────────────────────────────────────────

def holdout_rs_viterbi(
    model: RiemannNavigator,
    label: str,
    known_zeros: list[float],
    t_scan_lo: float,
    t_scan_hi: float,
    n_known_before: int,
    sep: float = 0.8,
    p_ghost: float = 0.5,
    ghost_radius: float = 0.9,
    verbose: bool = True,
) -> tuple[int, int, int]:
    """
    Holdout evaluation with RS-density ghost augmentation.

    Workflow:
      1. Scan near_zero with model → raw scanner peaks
      2. Gate below t_gate = min(known_zeros) - 1.0
      3. Augment gated peaks with RS ghost candidates at semiclassical positions
         where model has no peaks (within ghost_radius)
      4. Budget-Viterbi on augmented candidates
      5. Score as HIT/PHANTOM; report unique zeros found
    """
    n_pts = max(3000, int((t_scan_hi - t_scan_lo) * 25))

    raw_all, t_vals, p_nears = scan_near_zero(
        model, t_scan_lo - 0.5, t_scan_hi + 2.0, n_pts=n_pts
    )

    rs_lo   = rs_N(t_scan_lo)
    rs_hi   = rs_N(t_scan_hi + 1.0)
    budget  = max(len(known_zeros), int(math.floor(rs_hi - rs_lo)) + 1)
    t_gate  = min(known_zeros) - 1.0

    raw_gated = [
        (t, p) for t, p in raw_all
        if t_scan_lo - 0.5 <= t <= t_scan_hi + 1.0 and t >= t_gate
    ]

    # ── Augment with RS ghosts ────────────────────────────────────────────────
    augmented, n_ghosts = augment_with_rs_ghosts(
        raw_gated, t_gate, t_scan_hi + 1.0,
        p_ghost=p_ghost, ghost_radius=ghost_radius,
    )

    selected = budget_viterbi(augmented, budget=budget, sep=sep)

    # Count ghosts vs model peaks in selected
    ghost_set = set(t for t, _ in augmented) - set(t for t, _ in raw_gated)
    n_ghost_selected = sum(1 for t, _ in selected if t in ghost_set)

    if verbose:
        near_std = torch.tensor(p_nears).std().item()
        print(f"\n{'='*68}")
        print(f"HOLDOUT: {label}  (NEVER SEEN DURING TRAINING)")
        print(f"{'='*68}")
        print(f"RS budget: {budget}  |  t_gate: {t_gate:.1f}"
              f"  |  raw gated: {len(raw_gated)}"
              f"  |  ghosts added: {n_ghosts}"
              f"  |  after Viterbi: {len(selected)}")
        print(f"near_zero std: {near_std:.2e}"
              f"  |  ghost selected: {n_ghost_selected}/{len(selected)}"
              f"  |  model selected: {len(selected)-n_ghost_selected}/{len(selected)}")
        print()
        print(f"  {'#':>4}  {'t_pred':>12}  {'P':>6}  {'src':>6}  "
              f"{'nearest zero':>14}  {'delta':>8}  {'status':>8}")
        print(f"  {'----':>4}  {'------------':>12}  {'------':>6}  {'------':>6}  "
              f"{'----------':>14}  {'--------':>8}  {'--------':>8}")

    hits, phantoms = 0, 0
    matched: set[float] = set()
    for idx, (t_pred, p) in enumerate(selected, 1):
        src = "GHOST" if t_pred in ghost_set else "MODEL"
        nearest = min(known_zeros, key=lambda z: abs(z - t_pred))
        delta   = abs(t_pred - nearest)
        status  = "HIT" if delta <= HIT_THRESH else "PHANTOM"
        if status == "HIT":
            hits += 1
            matched.add(nearest)
        else:
            phantoms += 1
        if verbose:
            print(f"  {idx:>4}  {t_pred:>12.4f}  {p:>6.4f}  {src:>6}  "
                  f"{nearest:>14.6f}  {delta:>8.4f}  {status:>8}")

    missed = sorted(z for z in known_zeros if z not in matched)
    if verbose and missed:
        print(f"\n  MISSED: {[f'{z:.3f}' for z in missed]}")
    unique = len(matched)
    if verbose:
        print(f"\nRESULT: {hits}/{len(known_zeros)} hits"
              f"  |  {unique}/{len(known_zeros)} unique zeros"
              f"  |  {phantoms} phantoms"
              f"  |  {len(missed)} missed")
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

    model = RiemannNavigator(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigator  hidden={HIDDEN}  layers={LAYERS}  heads={HEADS}  "
          f"params={n_params:,}")
    print(f"RS-density Viterbi: ghost P=0.5 (logit=0) fills model-silent gaps")
    print(f"  H1 (P≈0.1 everywhere): ghosts beat model peaks → RS-guided placement")
    print(f"  H2 (P≈0.9 everywhere): model peaks beat ghosts → model-guided")

    print(f"\n{'='*68}")
    print(f"PHASE A — jitter ±0.3, t_range=(10,250), 200 ep")
    print(f"{'='*68}")
    train_phase_a(model, TRAIN_ZEROS, epochs=200, jitter=0.3)

    # ── Sanity: check ghost positions vs known training zeros ─────────────────
    print(f"\n{'='*68}")
    print(f"RS GHOST SANITY CHECK (training zeros 1-50)")
    print(f"{'='*68}")
    k_start = int(math.floor(rs_N(TRAIN_ZEROS[0] - 1.0))) + 1
    k_end   = int(math.ceil(rs_N(TRAIN_ZEROS[-1] + 1.0)))
    rs_errors = []
    for k in range(k_start, k_end + 1):
        if k - 1 < len(TRAIN_ZEROS):
            t_rs  = rs_invert(float(k))
            t_true = TRAIN_ZEROS[k - 1]   # 1-indexed
            rs_errors.append(abs(t_rs - t_true))
    if rs_errors:
        import statistics
        print(f"  RS inversion error on training zeros:")
        print(f"  mean={statistics.mean(rs_errors):.4f}  "
              f"median={statistics.median(rs_errors):.4f}  "
              f"max={max(rs_errors):.4f}  "
              f"p90={sorted(rs_errors)[int(0.9*len(rs_errors))]:.4f}")
        frac_within_1 = sum(1 for e in rs_errors if e < 1.0) / len(rs_errors)
        print(f"  Fraction within hit_thresh=1.0: {frac_within_1:.1%}")

    # ── Holdout evaluation ────────────────────────────────────────────────────
    P_GHOST     = 0.5
    GHOST_RADIUS = 0.9

    for sep in [0.8, 0.4]:
        print(f"\n{'='*68}")
        print(f"HOLDOUT — RS Viterbi  sep={sep}  p_ghost={P_GHOST}  radius={GHOST_RADIUS}")
        print(f"{'='*68}")

        h1_hits, h1_ph, h1_miss = holdout_rs_viterbi(
            model, "zeros 51-100",
            HOLD1_ZEROS,
            t_scan_lo=min(HOLD1_ZEROS) - 1.0,
            t_scan_hi=max(HOLD1_ZEROS),
            n_known_before=50,
            sep=sep,
            p_ghost=P_GHOST,
            ghost_radius=GHOST_RADIUS,
        )
        h2_hits, h2_ph, h2_miss = holdout_rs_viterbi(
            model, "zeros 101-150",
            HOLD2_ZEROS,
            t_scan_lo=min(HOLD2_ZEROS) - 1.0,
            t_scan_hi=max(HOLD2_ZEROS),
            n_known_before=100,
            sep=sep,
            p_ghost=P_GHOST,
            ghost_radius=GHOST_RADIUS,
        )
        h1_unique = len(HOLD1_ZEROS) - h1_miss
        h2_unique = len(HOLD2_ZEROS) - h2_miss
        print(f"\n{'='*68}")
        print(f"SUMMARY  sep={sep}  p_ghost={P_GHOST}")
        print(f"  H1: {h1_hits} hits / {h1_unique} unique / {h1_ph} phantoms / {h1_miss} missed")
        print(f"  H2: {h2_hits} hits / {h2_unique} unique / {h2_ph} phantoms / {h2_miss} missed")
        print(f"  Combined: {h1_hits+h2_hits} hits / {h1_unique+h2_unique} unique"
              f" / {h1_ph+h2_ph} phantoms")

    # ── Also run without ghosts for comparison ────────────────────────────────
    from riemann_crf import holdout_report_crf
    print(f"\n{'='*68}")
    print(f"BASELINE (no RS ghosts)  sep=0.8  for comparison")
    print(f"{'='*68}")
    h1_hits_b, h1_ph_b, h1_miss_b = holdout_report_crf(
        model, "zeros 51-100",
        HOLD1_ZEROS,
        t_scan_lo=min(HOLD1_ZEROS) - 1.0,
        t_scan_hi=max(HOLD1_ZEROS),
        n_known_before=50,
        sep=0.8,
    )
    h2_hits_b, h2_ph_b, h2_miss_b = holdout_report_crf(
        model, "zeros 101-150",
        HOLD2_ZEROS,
        t_scan_lo=min(HOLD2_ZEROS) - 1.0,
        t_scan_hi=max(HOLD2_ZEROS),
        n_known_before=100,
        sep=0.8,
    )
    h1u_b = len(HOLD1_ZEROS) - h1_miss_b
    h2u_b = len(HOLD2_ZEROS) - h2_miss_b
    print(f"\n  Baseline  sep=0.8  (no RS ghosts):")
    print(f"  H1: {h1_hits_b} hits / {h1u_b} unique / {h1_ph_b} phantoms / {h1_miss_b} missed")
    print(f"  H2: {h2_hits_b} hits / {h2u_b} unique / {h2_ph_b} phantoms / {h2_miss_b} missed")
    print(f"  Combined: {h1_hits_b+h2_hits_b} hits / {h1u_b+h2u_b} unique"
          f" / {h1_ph_b+h2_ph_b} phantoms")


if __name__ == "__main__":
    main()
