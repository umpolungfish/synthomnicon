"""
riemann_expanded.py — Expanded training set: zeros 1-100, holdouts 101-150 and 151-200.

Prior experiments trained on zeros 1-50 and plateaued at ~75/100 unique zeros
in the combined holdout (zeros 51-100 + 101-150).

Key diagnostic: the plateau is information-theoretic. Individual zero positions
beyond the training set cannot be deduced from the training zeros alone — they
require evaluating zeta(1/2 + it) directly (which is what mpmath.zetazero does).

This experiment doubles the training set to zeros 1-100 (t=14-237) and shifts
the holdouts to H1=101-150 (t=237-319) and H2=151-200 (t=321-396).

Expected outcome:
  H1 (101-150): was the "medium extrapolation" zone in prior runs where the model
    had P≈0.8-0.9 (well-confident). With those zeros now IN training, this holdout
    becomes the new near-extrapolation zone.
  H2 (151-200): t=321-396, true far extrapolation. Expect P≈0.09 flat (same as
    H1 was before), giving ~38/50 unique from Viterbi structural selection.

If the plateau holds at ~75-76/100 even with 100 training zeros, it confirms the
ceiling is structural (not solvable by expanding the training set within the same
Phase A framework). If it improves to ~85+, it suggests more data helps.

Training: jitter ±0.3, sigma=0.4, t_range=(10, 260), 200 ep (same best config).
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
from riemann_crf import ZEROS_101_150, rs_N, holdout_report_crf

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Zero sets ─────────────────────────────────────────────────────────────────

# Zeros 1-100: already in train_navigators.RIEMANN_ZEROS_T (all 100 values)
TRAIN_ZEROS = RIEMANN_ZEROS_T  # all 100

# H1: zeros 101-150 (from riemann_crf, mpmath-accurate)
HOLD1_ZEROS = ZEROS_101_150    # 50 zeros, t=237-319

# H2: zeros 151-200 (mpmath.zetazero(151..200), computed 2026-04-12)
ZEROS_151_200 = [
    321.160134, 322.144559, 323.466970, 324.862866, 327.443901,
    329.033072, 329.953240, 331.474468, 333.645379, 334.211355,
    336.841850, 338.339993, 339.858217, 341.042261, 342.054878,
    344.661703, 346.347871, 347.272678, 349.316261, 350.408419,
    351.878649, 353.488900, 356.017575, 357.151302, 357.952685,
    359.743755, 361.289362, 363.331331, 364.736024, 366.212710,
    367.993575, 368.968438, 370.050919, 373.061928, 373.864874,
    375.825913, 376.324092, 378.436680, 379.872975, 381.484469,
    383.443529, 384.956117, 385.861301, 387.222890, 388.846128,
    391.456084, 392.245083, 393.427744, 395.582870, 396.381854,
]
HOLD2_ZEROS = ZEROS_151_200    # 50 zeros, t=321-396


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
    t_range_hi: float = 260.0,
) -> None:
    near_params     = [p for n, p in model.named_parameters() if "near_head" in n]
    backbone_params = [p for n, p in model.named_parameters() if "near_head" not in n]
    opt   = optim.AdamW([
        {"params": near_params,     "lr": near_lr},
        {"params": backbone_params, "lr": backbone_lr},
    ], weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    t_lo = min(zeros_t) - 5.0
    print(f"\n  sigma={sigma}  jitter=±{jitter}  t_range=({t_lo:.0f},{t_range_hi})  {epochs}ep")
    print(f"\n  {'Epoch':>6}  {'L_near':>10}  {'Gap_log':>9}  {'Gap_chk':>9}  "
          f"{'H1zone_std':>11}  {'H2zone_std':>11}")
    print(f"  {'------':>6}  {'----------':>10}  {'---------':>9}  {'---------':>9}  "
          f"{'-----------':>11}  {'-----------':>11}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, _, _ = make_riemann_batch(zeros_t, batch_size=batch_size, t_range=(t_lo, t_range_hi))
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
                # H1 zone probe (zeros 101-150, t≈245-310, use midpoints)
                t_h1 = torch.tensor(
                    [[0.5, 260.0 + 3*i] for i in range(20)], dtype=torch.float32
                ).to(DEVICE)
                # H2 zone probe (zeros 151-200, t≈330-380, use midpoints)
                t_h2 = torch.tensor(
                    [[0.5, 340.0 + 3*i] for i in range(20)], dtype=torch.float32
                ).to(DEVICE)
                p_h1 = model(t_h1)["near_zero"].cpu()
                p_h2 = model(t_h2)["near_zero"].cpu()
                l_val = F.mse_loss(out["near_zero"], target).item()
            print(f"  {epoch:>6}  {l_val:>10.6f}  {gap_log:>+9.4f}  {gap_chk:>+9.4f}"
                  f"  {p_h1.std():>11.4f}  {p_h2.std():>11.4f}")


def main():
    HIDDEN   = 240
    LAYERS   = 24
    HEADS    = 24
    NFOURIER = 48
    FREQ_MAX = 2.5
    EPOCHS   = 200

    model = RiemannNavigator(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigator  hidden={HIDDEN}  layers={LAYERS}  heads={HEADS}  "
          f"params={n_params:,}")
    print(f"EXPANDED training set: zeros 1-100 ({len(TRAIN_ZEROS)} zeros, t=14-237)")
    print(f"H1 holdout: zeros 101-150 ({len(HOLD1_ZEROS)} zeros, t=237-319) [was H2]")
    print(f"H2 holdout: zeros 151-200 ({len(HOLD2_ZEROS)} zeros, t=321-396) [new far zone]")
    print(f"\nBaseline (train 1-50, holdout 51-100+101-150): 75/100 unique at sep=0.8")
    print(f"Hypothesis: doubling train set → H1 now in-distribution → H1≈47+/50")
    print(f"  H2 (true far extrapolation, t=321-396) → ~38/50 from Viterbi structural?")

    print(f"\n{'='*72}")
    print(f"PHASE A — jitter ±0.3, sigma=0.4, t_range=(10, 260), 200 ep")
    print(f"{'='*72}")
    train_phase_a(model, TRAIN_ZEROS, epochs=EPOCHS, t_range_hi=260.0)

    # ── Amplitude check ───────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print(f"AMPLITUDE CHECK")
    print(f"{'='*72}")
    model.eval()
    with torch.no_grad():
        t_at  = torch.tensor([[0.5, z] for z in TRAIN_ZEROS[:25]], dtype=torch.float32).to(DEVICE)
        t_far = torch.tensor([[0.5, z+3.0] for z in TRAIN_ZEROS[:25]], dtype=torch.float32).to(DEVICE)
        t_h1  = torch.tensor([[0.5, 260.0+3*i] for i in range(20)], dtype=torch.float32).to(DEVICE)
        t_h2  = torch.tensor([[0.5, 340.0+3*i] for i in range(20)], dtype=torch.float32).to(DEVICE)
        p_at  = model(t_at)["near_zero"].cpu()
        p_far = model(t_far)["near_zero"].cpu()
        p_h1  = model(t_h1)["near_zero"].cpu()
        p_h2  = model(t_h2)["near_zero"].cpu()
    print(f"  P@train zero:         mean={p_at.mean():.4f}  std={p_at.std():.4f}")
    print(f"  P@3.0 from zero:      mean={p_far.mean():.4f}  std={p_far.std():.4f}")
    print(f"  Gap (check):          {p_at.mean()-p_far.mean():+.4f}")
    print(f"  H1 zone (t=260-317):  mean={p_h1.mean():.4f}  std={p_h1.std():.4f}")
    print(f"  H2 zone (t=340-397):  mean={p_h2.mean():.4f}  std={p_h2.std():.4f}")

    # ── Holdout evaluation ────────────────────────────────────────────────────
    for sep in [0.8, 0.4]:
        print(f"\n{'='*72}")
        print(f"HOLDOUT EVALUATION  sep={sep}")
        print(f"{'='*72}")
        h1_hits, h1_ph, h1_miss = holdout_report_crf(
            model, "zeros 101-150 (H1)",
            HOLD1_ZEROS,
            t_scan_lo=min(HOLD1_ZEROS) - 1.0, t_scan_hi=max(HOLD1_ZEROS),
            n_known_before=100, sep=sep,
        )
        h2_hits, h2_ph, h2_miss = holdout_report_crf(
            model, "zeros 151-200 (H2)",
            HOLD2_ZEROS,
            t_scan_lo=min(HOLD2_ZEROS) - 1.0, t_scan_hi=max(HOLD2_ZEROS),
            n_known_before=150, sep=sep,
        )
        h1u = len(HOLD1_ZEROS) - h1_miss
        h2u = len(HOLD2_ZEROS) - h2_miss
        print(f"\n  sep={sep}:")
        print(f"    H1 (101-150): {h1_hits} hits / {h1u}/50 unique / {h1_ph} ph / {h1_miss} missed")
        print(f"    H2 (151-200): {h2_hits} hits / {h2u}/50 unique / {h2_ph} ph / {h2_miss} missed")
        print(f"    Combined: {h1_hits+h2_hits} hits / {h1u+h2u}/100 unique / {h1_ph+h2_ph} phantoms")
        # Compare to baseline
        if h1u + h2u > 76:
            print(f"    ↑ IMPROVEMENT over baseline 75/100")
        elif h1u + h2u >= 74:
            print(f"    = SAME as baseline (within noise)")
        else:
            print(f"    ↓ REGRESSION vs baseline")


if __name__ == "__main__":
    main()
