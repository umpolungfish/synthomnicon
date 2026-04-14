"""
riemann_large.py — Phase A curriculum, hidden=360, layers=36, heads=36.

Same near-first curriculum as riemann_near_first.py:
  Phase A only (no Phase B): near_head only, Gaussian target, lam_near=5.
  Phase B is dropped — Frobenius training causes catastrophic forgetting that
  destroys the Phase A proximity signal (Gap collapses from +0.70 → 0.00).

Changes from baseline:
  hidden_dim: 240 → 360  (50% wider embeddings)
  num_layers:  24 → 36   (50% deeper K_slow stack)
  num_heads:   24 → 36   (36 heads, head_dim = 360/36 = 10)
  Phase A epochs: 200 → 400 (more training for larger model + better
                             extrapolation into t=153-170 and t=237-248
                             low-coverage zones identified in prior run)

Evaluated at sep=0.4 and sep=0.6 to diagnose cluster over-detections.
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

TRAIN_ZEROS = RIEMANN_ZEROS_T[:50]
HOLD1_ZEROS = RIEMANN_ZEROS_T[50:]
HOLD2_ZEROS = ZEROS_101_150


def near_gaussian_target(
    t_batch: torch.Tensor,
    zeros_t: list[float],
    sigma: float = 0.4,
) -> torch.Tensor:
    t = t_batch.unsqueeze(1)
    z = torch.tensor(zeros_t, dtype=torch.float32, device=t.device)
    sq = ((t - z) ** 2) / (2.0 * sigma ** 2)
    return torch.exp(-sq).max(dim=1).values


def train_phase_a(
    model: RiemannNavigator,
    zeros_t: list[float],
    epochs: int = 400,
    batch_size: int = 128,
    sigma: float = 0.4,
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

    print(f"\n  Phase A — near_head only, Gaussian target (sigma={sigma})")
    print(f"  near_lr={near_lr}, backbone_lr={backbone_lr}, {epochs} epochs")
    print(f"\n  {'Epoch':>6}  {'L_near':>10}  {'P@zero':>8}  {'P@far':>8}  {'Gap':>8}")
    print(f"  {'------':>6}  {'----------':>10}  {'--------':>8}  {'--------':>8}  {'--------':>8}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, _, _ = make_riemann_batch(zeros_t, batch_size=batch_size, t_range=(10.0, 250.0))
        s = s.to(DEVICE)

        out    = model(s)
        target = near_gaussian_target(s[:, 1], zeros_t, sigma=sigma)
        loss   = 5.0 * F.mse_loss(out["near_zero"], target)

        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % 50 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                t_at = torch.tensor(
                    [[0.5, z + random.uniform(-0.1, 0.1)] for z in zeros_t[:20]],
                    dtype=torch.float32,
                ).to(DEVICE)
                t_far = torch.tensor(
                    [[0.5, z + random.uniform(2.0, 4.0)] for z in zeros_t[:20]],
                    dtype=torch.float32,
                ).to(DEVICE)
                p_at  = model(t_at)["near_zero"].mean().item()
                p_far = model(t_far)["near_zero"].mean().item()
                l_val = F.mse_loss(
                    out["near_zero"],
                    near_gaussian_target(s[:, 1], zeros_t, sigma=sigma),
                ).item()
            print(f"  {epoch:>6}  {l_val:>10.6f}  {p_at:>8.4f}  {p_far:>8.4f}"
                  f"  {p_at - p_far:>+8.4f}")


def main():
    HIDDEN   = 360
    LAYERS   = 36
    HEADS    = 36
    NFOURIER = 48
    FREQ_MAX = 2.5
    BATCH    = 128
    SIGMA    = 0.4

    model = RiemannNavigator(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigator  hidden={HIDDEN}  layers={LAYERS}  heads={HEADS}")
    print(f"  n_fourier={NFOURIER}  freq_max=10^{FREQ_MAX}  params={n_params:,}")
    print(f"  Phase A only (no Phase B) — Gaussian proximity sigma={SIGMA}")
    print(f"  Baseline (hidden=240, layers=24): Phase A 97/100, 5 phantoms")

    print(f"\n{'='*68}")
    print(f"PHASE A — near_head only, 400 ep, hidden={HIDDEN}, layers={LAYERS}")
    print(f"{'='*68}")
    train_phase_a(
        model, TRAIN_ZEROS,
        epochs=400, batch_size=BATCH, sigma=SIGMA,
        near_lr=1e-3, backbone_lr=3e-4,
    )

    # ── Amplitude check ───────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"AMPLITUDE CHECK")
    print(f"{'='*68}")
    model.eval()
    t_at  = torch.tensor([[0.5, z] for z in TRAIN_ZEROS[:25]], dtype=torch.float32).to(DEVICE)
    t_far = torch.tensor([[0.5, z + 3.0] for z in TRAIN_ZEROS[:25]], dtype=torch.float32).to(DEVICE)
    with torch.no_grad():
        p_at  = model(t_at)["near_zero"].cpu()
        p_far = model(t_far)["near_zero"].cpu()
    print(f"  P(near | at zero):   mean={p_at.mean():.4f}  "
          f"min={p_at.min():.4f}  max={p_at.max():.4f}")
    print(f"  P(near | 3.0 away):  mean={p_far.mean():.4f}  "
          f"min={p_far.min():.4f}  max={p_far.max():.4f}")
    print(f"  Gap:                 {p_at.mean() - p_far.mean():+.4f}")

    # ── Holdout evaluation at sep=0.4 and sep=0.6 ────────────────────────────
    for sep in [0.4, 0.6]:
        print(f"\n{'='*68}")
        print(f"HOLDOUT EVALUATION  sep={sep}")
        print(f"{'='*68}")
        h1_hits, h1_ph, h1_miss = holdout_report_crf(
            model, "zeros 51-100",
            HOLD1_ZEROS,
            t_scan_lo=min(HOLD1_ZEROS) - 1.0,
            t_scan_hi=max(HOLD1_ZEROS),
            n_known_before=50,
            sep=sep,
        )
        h2_hits, h2_ph, h2_miss = holdout_report_crf(
            model, "zeros 101-150",
            HOLD2_ZEROS,
            t_scan_lo=min(HOLD2_ZEROS) - 1.0,
            t_scan_hi=max(HOLD2_ZEROS),
            n_known_before=100,
            sep=sep,
        )
        print(f"\n  sep={sep}:  H1 {h1_hits}/50 ({h1_ph} ph)  "
              f"H2 {h2_hits}/50 ({h2_ph} ph)  "
              f"combined {h1_hits+h2_hits}/100  "
              f"({h1_ph+h2_ph} phantoms total)")


if __name__ == "__main__":
    main()
