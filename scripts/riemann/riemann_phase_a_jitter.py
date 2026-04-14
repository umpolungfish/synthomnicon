"""
riemann_phase_a_jitter.py — Phase A with per-epoch zero position jitter.

Problem diagnosed from all prior runs:
  check Gap (+0.574) << training log Gap (+0.715)  → model memorized exact
  training zero positions rather than learning generalizable local features.
  H1 and H2 unique zeros ≈ 30/50 each — the "hits" metric hid this; cluster
  duplicates filled the budget while 20 zeros were invisible per holdout.

  The 97/100 baseline was exceptional: check Gap ≈ training log Gap (+0.705
  vs +0.686) → low overfitting → structured per-zero peaks → ~48 unique H1
  zeros. Current runs give check Gap ≈ 0.57 regardless of sigma/epoch count.

Fix: jitter Gaussian target centers by ±jitter_delta each epoch. The model
  cannot memorize positions that shift every epoch; it must learn LOCAL
  FEATURES that generalize across the jitter range (and thereby to holdout
  zeros). Target is to close the check-Gap / training-Gap discrepancy.

  jitter_delta=0.3: model sees each training zero at positions ±0.3 each
  epoch. At sigma=0.4 this means the Gaussian is still strong (exp(-0.09/0.32)
  = 0.76 at 0.3 offset) — gradient still informative — but position memory
  is broken.

Hypothesis: with jitter, check Gap ≈ training log Gap → structured H1/H2
  landscape → 45+/50 unique zeros per holdout.
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


def near_gaussian_target_jittered(
    t_batch: torch.Tensor,
    zeros_t: list[float],
    sigma: float = 0.4,
    jitter: float = 0.3,
) -> torch.Tensor:
    """Gaussian target with per-call position jitter — breaks position memorization."""
    jittered = [z + random.uniform(-jitter, jitter) for z in zeros_t]
    t  = t_batch.unsqueeze(1)
    z  = torch.tensor(jittered, dtype=torch.float32, device=t.device)
    sq = ((t - z) ** 2) / (2.0 * sigma ** 2)
    return torch.exp(-sq).max(dim=1).values


def near_gaussian_target(
    t_batch: torch.Tensor,
    zeros_t: list[float],
    sigma: float = 0.4,
) -> torch.Tensor:
    """Clean target (no jitter) — for evaluation and amplitude check only."""
    t  = t_batch.unsqueeze(1)
    z  = torch.tensor(zeros_t, dtype=torch.float32, device=t.device)
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

    print(f"\n  Phase A — near_head only, Gaussian + jitter")
    print(f"  sigma={sigma}  jitter=±{jitter}  near_lr={near_lr}  backbone_lr={backbone_lr}  {epochs} ep")
    print(f"\n  {'Epoch':>6}  {'L_near':>10}  {'P@zero':>8}  {'P@far':>8}  {'Gap_log':>9}  {'Gap_chk':>9}")
    print(f"  {'------':>6}  {'----------':>10}  {'--------':>8}  {'--------':>8}  {'---------':>9}  {'---------':>9}")

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

        if epoch % 25 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                # Training log Gap: small jitter ±0.1 (as before — noisy but in-distribution)
                t_at  = torch.tensor(
                    [[0.5, z + random.uniform(-0.1, 0.1)] for z in zeros_t[:20]],
                    dtype=torch.float32,
                ).to(DEVICE)
                t_far = torch.tensor(
                    [[0.5, z + random.uniform(2.0, 4.0)] for z in zeros_t[:20]],
                    dtype=torch.float32,
                ).to(DEVICE)
                p_at_log  = model(t_at)["near_zero"].mean().item()
                p_far_log = model(t_far)["near_zero"].mean().item()
                gap_log   = p_at_log - p_far_log

                # Check Gap: EXACT zero positions (no jitter) — measures generalization
                t_at_ck  = torch.tensor(
                    [[0.5, z] for z in zeros_t[:25]], dtype=torch.float32
                ).to(DEVICE)
                t_far_ck = torch.tensor(
                    [[0.5, z + 3.0] for z in zeros_t[:25]], dtype=torch.float32
                ).to(DEVICE)
                p_at_ck  = model(t_at_ck)["near_zero"].mean().item()
                p_far_ck = model(t_far_ck)["near_zero"].mean().item()
                gap_chk  = p_at_ck - p_far_ck

                l_val = F.mse_loss(out["near_zero"], target).item()
            print(f"  {epoch:>6}  {l_val:>10.6f}  {p_at_log:>8.4f}  {p_far_log:>8.4f}"
                  f"  {gap_log:>+9.4f}  {gap_chk:>+9.4f}")


def amplitude_check(model: RiemannNavigator, zeros_t: list[float]) -> tuple[float, float]:
    model.eval()
    t_at  = torch.tensor([[0.5, z]        for z in zeros_t[:25]], dtype=torch.float32).to(DEVICE)
    t_far = torch.tensor([[0.5, z + 3.0]  for z in zeros_t[:25]], dtype=torch.float32).to(DEVICE)
    t_mid = torch.tensor([[0.5, z + 0.6]  for z in zeros_t[:25]], dtype=torch.float32).to(DEVICE)
    # Probe midpoints in H1 and H2 to diagnose landscape quality
    t_h1  = torch.tensor([[0.5, 160.0 + 2*i] for i in range(25)], dtype=torch.float32).to(DEVICE)
    t_h2  = torch.tensor([[0.5, 260.0 + 2*i] for i in range(25)], dtype=torch.float32).to(DEVICE)
    with torch.no_grad():
        p_at  = model(t_at)["near_zero"].cpu()
        p_far = model(t_far)["near_zero"].cpu()
        p_mid = model(t_mid)["near_zero"].cpu()
        p_h1  = model(t_h1)["near_zero"].cpu()
        p_h2  = model(t_h2)["near_zero"].cpu()
    print(f"  P(near | at train zero):           mean={p_at.mean():.4f}  std={p_at.std():.4f}")
    print(f"  P(near | 0.6 from train zero):     mean={p_mid.mean():.4f}  std={p_mid.std():.4f}")
    print(f"  P(near | 3.0 from train zero):     mean={p_far.mean():.4f}  std={p_far.std():.4f}")
    print(f"  Gap (at - 3.0 away):               {p_at.mean() - p_far.mean():+.4f}")
    print(f"  H1 midpoints t=160-208 (unlabeled):mean={p_h1.mean():.4f}  std={p_h1.std():.4f}")
    print(f"  H2 midpoints t=260-308 (unlabeled):mean={p_h2.mean():.4f}  std={p_h2.std():.4f}")
    return (p_at.mean() - p_far.mean()).item(), p_h1.std().item()


def main():
    HIDDEN   = 240
    LAYERS   = 24
    HEADS    = 24
    NFOURIER = 48
    FREQ_MAX = 2.5
    BATCH    = 128
    SIGMA    = 0.4
    JITTER   = 0.3   # ±0.3 per-epoch zero position jitter
    EPOCHS   = 200

    model = RiemannNavigator(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigator  hidden={HIDDEN}  layers={LAYERS}  heads={HEADS}")
    print(f"  n_fourier={NFOURIER}  freq_max=10^{FREQ_MAX}  params={n_params:,}")
    print(f"  Phase A + zero jitter ±{JITTER}  sigma={SIGMA}  epochs={EPOCHS}")
    print(f"  Baseline 97/100: check Gap ≈ train Gap (+0.705 vs +0.686) — low overfitting")
    print(f"  Current typical: check Gap +0.574 vs train Gap +0.715 — overfitting → 30/50 unique zeros")

    print(f"\n{'='*68}")
    print(f"PHASE A — jitter=±{JITTER}, sigma={SIGMA}, {EPOCHS} ep")
    print(f"{'='*68}")
    train_phase_a(
        model, TRAIN_ZEROS,
        epochs=EPOCHS, batch_size=BATCH, sigma=SIGMA, jitter=JITTER,
        near_lr=1e-3, backbone_lr=3e-4,
    )

    print(f"\n{'='*68}")
    print(f"AMPLITUDE CHECK  (Gap_chk is the generalization metric)")
    print(f"{'='*68}")
    gap_chk, h1_std = amplitude_check(model, TRAIN_ZEROS)
    print(f"\n  → Gap_chk={gap_chk:+.4f}  H1_std={h1_std:.4f}")
    print(f"    Target: Gap_chk > 0.65 with H1_std > 0.25 for good holdout coverage")

    for sep in [0.4, 0.8]:
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
        h1_unique = len(HOLD1_ZEROS) - h1_miss
        h2_unique = len(HOLD2_ZEROS) - h2_miss
        print(f"\n  sep={sep}:")
        print(f"    H1 {h1_hits}/50 ({h1_ph} ph, {h1_miss} missed) → {h1_unique}/50 unique zeros")
        print(f"    H2 {h2_hits}/50 ({h2_ph} ph, {h2_miss} missed) → {h2_unique}/50 unique zeros")
        print(f"    Combined hits {h1_hits+h2_hits}/100  |  unique {h1_unique+h2_unique}/100  |  phantoms {h1_ph+h2_ph}")


if __name__ == "__main__":
    main()
