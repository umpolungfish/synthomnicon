"""
riemann_phase_a_jitter_restricted.py — Phase A with jitter + restricted t_range.

Two independent fixes combined:
  1. jitter ±0.3: prevents position memorization → Gap_log ≈ Gap_chk
     (from riemann_phase_a_jitter.py: 0.637 vs 0.616, gap 0.021 vs prior 0.14)
  2. t_range=(10, 150): H1 territory never seen as "negative" space
     (from riemann_phase_a_restricted.py: H1 std 0.113→0.321)

Jitter alone: sep=0.8 → unique 39 H1 + 36 H2 = 75/100
Restricted alone: sep=0.4 → unique 29 H1 + 32 H2 = 61/100 but H1 std=0.321
Combined target: structured H1 landscape (H1 std > 0.25) + low overfitting
  (Gap_log ≈ Gap_chk) → unique > 40/50 per holdout.
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
    t_range_hi: float = 150.0,
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

    print(f"\n  Phase A — near_head + jitter ±{jitter} + restricted t_range")
    print(f"  sigma={sigma}  t_range=(10, {t_range_hi})  {epochs} ep")
    print(f"\n  {'Epoch':>6}  {'L_near':>10}  {'P@zero':>8}  {'P@far':>8}  {'Gap_log':>9}  {'Gap_chk':>9}")
    print(f"  {'------':>6}  {'----------':>10}  {'--------':>8}  {'--------':>8}  {'---------':>9}  {'---------':>9}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, _, _ = make_riemann_batch(
            zeros_t, batch_size=batch_size, t_range=(10.0, t_range_hi)
        )
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
                p_at_ck  = model(t_at_ck)["near_zero"].mean().item()
                p_far_ck = model(t_far_ck)["near_zero"].mean().item()
                gap_chk  = p_at_ck - p_far_ck

                l_val = F.mse_loss(out["near_zero"], target).item()
            print(f"  {epoch:>6}  {l_val:>10.6f}  {p_at_ck:>8.4f}  {p_far_ck:>8.4f}"
                  f"  {gap_log:>+9.4f}  {gap_chk:>+9.4f}")


def amplitude_check(model: RiemannNavigator, zeros_t: list[float]) -> None:
    model.eval()
    t_at  = torch.tensor([[0.5, z]        for z in zeros_t[:25]], dtype=torch.float32).to(DEVICE)
    t_far = torch.tensor([[0.5, z + 3.0]  for z in zeros_t[:25]], dtype=torch.float32).to(DEVICE)
    t_h1  = torch.tensor([[0.5, 160.0 + 2*i] for i in range(25)], dtype=torch.float32).to(DEVICE)
    t_h2  = torch.tensor([[0.5, 260.0 + 2*i] for i in range(25)], dtype=torch.float32).to(DEVICE)
    with torch.no_grad():
        p_at  = model(t_at)["near_zero"].cpu()
        p_far = model(t_far)["near_zero"].cpu()
        p_h1  = model(t_h1)["near_zero"].cpu()
        p_h2  = model(t_h2)["near_zero"].cpu()
    gap = p_at.mean() - p_far.mean()
    print(f"  P(near | at train zero):           mean={p_at.mean():.4f}  std={p_at.std():.4f}")
    print(f"  P(near | 3.0 from train zero):     mean={p_far.mean():.4f}  std={p_far.std():.4f}")
    print(f"  Gap (check):                       {gap:+.4f}")
    print(f"  H1 midpoints t=160-208:            mean={p_h1.mean():.4f}  std={p_h1.std():.4f}")
    print(f"  H2 midpoints t=260-308:            mean={p_h2.mean():.4f}  std={p_h2.std():.4f}")
    return gap.item(), p_h1.std().item()


def main():
    HIDDEN   = 240
    LAYERS   = 24
    HEADS    = 24
    NFOURIER = 48
    FREQ_MAX = 2.5
    BATCH    = 128
    SIGMA    = 0.4
    JITTER   = 0.3
    T_HI     = 150.0
    EPOCHS   = 200

    model = RiemannNavigator(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigator  hidden={HIDDEN}  layers={LAYERS}  heads={HEADS}")
    print(f"  n_fourier={NFOURIER}  freq_max=10^{FREQ_MAX}  params={n_params:,}")
    print(f"  Phase A jitter=±{JITTER} + restricted t_range=(10, {T_HI})  sigma={SIGMA}")
    print(f"  Jitter alone (t=10-250):  sep=0.8 → unique 39+36=75/100")
    print(f"  Restricted alone (t=10-150): H1 std 0.321 but unique 29+32=61/100")

    print(f"\n{'='*68}")
    print(f"PHASE A — jitter ±{JITTER}, t_range (10, {T_HI}), {EPOCHS} ep")
    print(f"{'='*68}")
    train_phase_a(
        model, TRAIN_ZEROS,
        epochs=EPOCHS, batch_size=BATCH,
        sigma=SIGMA, jitter=JITTER, t_range_hi=T_HI,
        near_lr=1e-3, backbone_lr=3e-4,
    )

    print(f"\n{'='*68}")
    print(f"AMPLITUDE CHECK")
    print(f"{'='*68}")
    gap_chk, h1_std = amplitude_check(model, TRAIN_ZEROS)
    print(f"\n  Gap_chk={gap_chk:+.4f}  H1_std={h1_std:.4f}")
    print(f"  Target: Gap_chk > 0.50 AND H1_std > 0.25")

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
        print(f"    H1 {h1_hits}/50 ({h1_ph} ph, {h1_miss} missed) → {h1_unique}/50 unique")
        print(f"    H2 {h2_hits}/50 ({h2_ph} ph, {h2_miss} missed) → {h2_unique}/50 unique")
        print(f"    Combined hits {h1_hits+h2_hits}/100  |  unique {h1_unique+h2_unique}/100  |  phantoms {h1_ph+h2_ph}")


if __name__ == "__main__":
    main()
