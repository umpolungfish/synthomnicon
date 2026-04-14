"""
riemann_predict.py — Blind prediction of not-yet-described Riemann zeros.

Workflow:
  1. Train on zeros 1-100 (jitter ±0.3, sigma=0.4, 200 ep)
  2. Scan t=400-600 WITHOUT knowing ground truth (approximately zeros 201-270)
  3. Record model predictions via budget-Viterbi
  4. Verify blind against mpmath.zetazero(201..N)
  5. Report: hit rate, missed, phantoms

This is genuine prediction — the model has never seen any zero at t>237.
The RS budget + sep structure provides the scaffold; the model's near_zero
signal guides placement within that scaffold.

Expected from H2 observations: ~76% hit rate (38/50 per 50-zero window).
"""

from __future__ import annotations

import math
import random

import mpmath
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from navigators import RiemannNavigator
from train_navigators import RIEMANN_ZEROS_T, make_riemann_batch
from riemann_crf import ZEROS_101_150, rs_N, budget_viterbi, scan_near_zero

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

mpmath.mp.dps = 25

TRAIN_ZEROS = RIEMANN_ZEROS_T          # zeros 1-100
HIT_THRESH  = 1.0


# ── Training ──────────────────────────────────────────────────────────────────

def near_gaussian_target_jittered(t_batch, zeros_t, sigma=0.4, jitter=0.3):
    jittered = [z + random.uniform(-jitter, jitter) for z in zeros_t]
    t  = t_batch.unsqueeze(1)
    z  = torch.tensor(jittered, dtype=torch.float32, device=t.device)
    sq = ((t - z) ** 2) / (2.0 * sigma ** 2)
    return torch.exp(-sq).max(dim=1).values


def train(model, zeros_t, epochs=200, sigma=0.4, jitter=0.3,
          near_lr=1e-3, backbone_lr=3e-4, t_range_hi=260.0):
    near_params     = [p for n, p in model.named_parameters() if "near_head" in n]
    backbone_params = [p for n, p in model.named_parameters() if "near_head" not in n]
    opt   = optim.AdamW([
        {"params": near_params,     "lr": near_lr},
        {"params": backbone_params, "lr": backbone_lr},
    ], weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    t_lo = min(zeros_t) - 5.0
    print(f"  sigma={sigma} jitter=±{jitter} t_range=({t_lo:.0f},{t_range_hi}) {epochs}ep")
    print(f"\n  {'Epoch':>6}  {'L_near':>10}  {'Gap_log':>9}  {'Gap_chk':>9}")
    print(f"  {'------':>6}  {'----------':>10}  {'---------':>9}  {'---------':>9}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, _, _ = make_riemann_batch(zeros_t, batch_size=128,
                                     t_range=(t_lo, t_range_hi))
        s = s.to(DEVICE)
        out    = model(s)
        target = near_gaussian_target_jittered(s[:, 1], zeros_t, sigma, jitter)
        loss   = 5.0 * F.mse_loss(out["near_zero"], target)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % 50 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                t_at  = torch.tensor(
                    [[0.5, z + random.uniform(-0.1, 0.1)] for z in zeros_t[:20]],
                    dtype=torch.float32).to(DEVICE)
                t_far = torch.tensor(
                    [[0.5, z + random.uniform(2.0, 4.0)] for z in zeros_t[:20]],
                    dtype=torch.float32).to(DEVICE)
                gap_log = (model(t_at)["near_zero"].mean()
                           - model(t_far)["near_zero"].mean()).item()
                t_at2  = torch.tensor(
                    [[0.5, z] for z in zeros_t[:25]], dtype=torch.float32).to(DEVICE)
                t_far2 = torch.tensor(
                    [[0.5, z + 3.0] for z in zeros_t[:25]], dtype=torch.float32).to(DEVICE)
                gap_chk = (model(t_at2)["near_zero"].mean()
                           - model(t_far2)["near_zero"].mean()).item()
                l_val = F.mse_loss(out["near_zero"], target).item()
            print(f"  {epoch:>6}  {l_val:>10.6f}  {gap_log:>+9.4f}  {gap_chk:>+9.4f}")


# ── Blind prediction scan ─────────────────────────────────────────────────────

def predict_blind(
    model: RiemannNavigator,
    t_scan_lo: float,
    t_scan_hi: float,
    n_known_before: int,
    sep: float = 0.8,
    label: str = "",
) -> list[tuple[float, float]]:
    """
    Scan [t_scan_lo, t_scan_hi], apply budget-Viterbi, return predictions.
    Does NOT use any ground-truth zero positions — pure model output.
    """
    n_pts = max(4000, int((t_scan_hi - t_scan_lo) * 30))
    raw_all, t_vals, p_nears = scan_near_zero(
        model, t_scan_lo - 0.5, t_scan_hi + 2.0, n_pts=n_pts
    )

    rs_lo  = rs_N(t_scan_lo)
    rs_hi  = rs_N(t_scan_hi + 1.0)
    budget = int(math.floor(rs_hi - rs_lo)) + 1

    raw_gated = [
        (t, p) for t, p in raw_all
        if t >= t_scan_lo - 0.5 and t <= t_scan_hi + 1.0
    ]
    selected = budget_viterbi(raw_gated, budget=budget, sep=sep)

    near_std = torch.tensor(p_nears).std().item()
    print(f"\n  {label}  t=[{t_scan_lo:.0f}, {t_scan_hi:.0f}]")
    print(f"  RS budget: {budget}  |  raw gated: {len(raw_gated)}"
          f"  |  selected: {len(selected)}  |  near_zero std: {near_std:.3e}")
    print(f"\n  {'#':>4}  {'t_pred':>12}  {'P(near)':>8}")
    print(f"  {'----':>4}  {'------------':>12}  {'--------':>8}")
    for i, (t, p) in enumerate(selected, 1):
        print(f"  {i:>4}  {t:>12.4f}  {p:>8.4f}")

    return selected


# ── Blind verification ────────────────────────────────────────────────────────

def verify_predictions(
    predictions: list[tuple[float, float]],
    n_start: int,
    n_end: int,
    label: str = "",
) -> tuple[int, int, int]:
    """
    Compute ground-truth zeros n_start..n_end via mpmath, then score predictions.
    This is the ONLY place mpmath is called — predictions were made without it.
    """
    print(f"\n  Computing ground truth: zeros {n_start}-{n_end} via mpmath...")
    true_zeros = [float(mpmath.im(mpmath.zetazero(n))) for n in range(n_start, n_end + 1)]
    print(f"  Range: [{true_zeros[0]:.3f}, {true_zeros[-1]:.3f}]  "
          f"({len(true_zeros)} zeros)")

    hits, phantoms = 0, 0
    matched: set[float] = set()
    print(f"\n  {'#':>4}  {'t_pred':>12}  {'P':>6}  {'nearest true':>14}"
          f"  {'delta':>8}  {'status':>8}")
    print(f"  {'----':>4}  {'------------':>12}  {'------':>6}  {'------------':>14}"
          f"  {'--------':>8}  {'--------':>8}")

    for idx, (t_pred, p) in enumerate(predictions, 1):
        if not true_zeros:
            break
        nearest = min(true_zeros, key=lambda z: abs(z - t_pred))
        delta   = abs(t_pred - nearest)
        status  = "HIT" if delta <= HIT_THRESH else "PHANTOM"
        if status == "HIT":
            hits += 1
            matched.add(nearest)
        else:
            phantoms += 1
        print(f"  {idx:>4}  {t_pred:>12.4f}  {p:>6.4f}  {nearest:>14.6f}"
              f"  {delta:>8.4f}  {status:>8}")

    missed_zeros = [z for z in true_zeros if z not in matched]
    unique = len(matched)
    if missed_zeros:
        print(f"\n  MISSED ({len(missed_zeros)}): {[f'{z:.3f}' for z in missed_zeros[:10]]}"
              + (" ..." if len(missed_zeros) > 10 else ""))

    print(f"\n  {label} RESULT: {hits}/{len(true_zeros)} hits"
          f"  |  {unique}/{len(true_zeros)} unique zeros"
          f"  |  {phantoms} phantoms  |  {len(missed_zeros)} missed")
    return hits, phantoms, len(missed_zeros)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    HIDDEN   = 240
    LAYERS   = 24
    HEADS    = 24
    NFOURIER = 48
    FREQ_MAX = 2.5

    model = RiemannNavigator(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigator  params={n_params:,}")
    print(f"Training on zeros 1-100 (t=14-237)")
    print(f"Prediction target: zeros ~201-270 (t≈400-600) — NEVER SEEN, NO GROUND TRUTH USED")

    # ── Train ─────────────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"TRAINING — zeros 1-100, jitter ±0.3, sigma=0.4, 200 ep")
    print(f"{'='*68}")
    train(model, TRAIN_ZEROS, epochs=200, t_range_hi=260.0)

    # ── Blind predictions (no ground truth used) ──────────────────────────────
    print(f"\n{'='*68}")
    print(f"BLIND PREDICTIONS — model scans t=400-600, no ground truth consulted")
    print(f"{'='*68}")

    # Window 1: t=400-500 (~zeros 201-235)
    preds_w1 = predict_blind(
        model, t_scan_lo=400.0, t_scan_hi=500.0,
        n_known_before=200, sep=0.8,
        label="Window 1 (t=400-500)",
    )

    # Window 2: t=500-600 (~zeros 236-270)
    preds_w2 = predict_blind(
        model, t_scan_lo=500.0, t_scan_hi=600.0,
        n_known_before=235, sep=0.8,
        label="Window 2 (t=500-600)",
    )

    # ── Verification (mpmath called HERE for the first time on this range) ────
    print(f"\n{'='*68}")
    print(f"VERIFICATION — now calling mpmath to check predictions against truth")
    print(f"{'='*68}")

    # Determine true zero indices from RS formula
    n_w1_lo = int(math.floor(rs_N(400.0))) + 1
    n_w1_hi = int(math.ceil(rs_N(501.0)))
    n_w2_lo = int(math.floor(rs_N(500.0))) + 1
    n_w2_hi = int(math.ceil(rs_N(601.0)))

    print(f"\n  Window 1: RS predicts zeros #{n_w1_lo}-{n_w1_hi} in t=[400,500]")
    h1_hits, h1_ph, h1_miss = verify_predictions(
        preds_w1, n_start=n_w1_lo, n_end=n_w1_hi, label="Window 1"
    )

    print(f"\n  Window 2: RS predicts zeros #{n_w2_lo}-{n_w2_hi} in t=[500,600]")
    h2_hits, h2_ph, h2_miss = verify_predictions(
        preds_w2, n_start=n_w2_lo, n_end=n_w2_hi, label="Window 2"
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    n_w1 = n_w1_hi - n_w1_lo + 1
    n_w2 = n_w2_hi - n_w2_lo + 1
    h1u  = n_w1 - h1_miss
    h2u  = n_w2 - h2_miss

    print(f"\n{'='*68}")
    print(f"SUMMARY — blind prediction vs ground truth")
    print(f"{'='*68}")
    print(f"  Window 1 (t=400-500, zeros ~#{n_w1_lo}-{n_w1_hi}): "
          f"{h1u}/{n_w1} unique  {h1_ph} phantoms  {h1_miss} missed")
    print(f"  Window 2 (t=500-600, zeros ~#{n_w2_lo}-{n_w2_hi}): "
          f"{h2u}/{n_w2} unique  {h2_ph} phantoms  {h2_miss} missed")
    print(f"  Combined: {h1u+h2u}/{n_w1+n_w2} unique  "
          f"{h1_ph+h2_ph} phantoms  {h1_miss+h2_miss} missed")
    pct = (h1u + h2u) / (n_w1 + n_w2) * 100
    print(f"  Hit rate: {pct:.1f}%")
    print(f"\n  Baseline (RS uniform grid, no model): ~64-76% expected")
    print(f"  Training range ended at t≈237 (zero #100)")
    print(f"  Prediction range t=400-600 is {400-237:.0f}-{600-237:.0f} units beyond training")


if __name__ == "__main__":
    main()
