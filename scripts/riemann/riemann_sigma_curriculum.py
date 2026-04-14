"""
riemann_sigma_curriculum.py — Two-phase sigma curriculum for better H1 extrapolation.

Root-cause diagnosis:
  All jitter runs plateau at ~75/100 unique (38 H1 + 37 H2 at sep=0.8).
  H1 (t=146-236) has near_zero P≈0.09 nearly flat — no genuine peak signal.
  The 38/50 H1 unique come from Viterbi structural selection on noise, NOT from
  the model learning zero positions. Gram ghost injection fails because Gram
  points (mean error 0.92) are less accurate than the model's own residual peaks.

Root cause: sigma=0.4 gives a hard cliff at the training/holdout boundary.
  At t=147 (2 units past last training zero at t=145):
    sigma=0.4: exp(-(2²/(2*0.16))) = exp(-12.5) ≈ 0     → zero target
    sigma=0.8: exp(-(2²/(2*0.64))) = exp(-3.1)  ≈ 0.044  → soft tail

  With sigma=0.4, the model sees zero_target≈0 for ALL t>145 during 200 epochs.
  The backbone learns a hard suppression boundary at t≈145.

Fix: sigma curriculum.
  Phase 1 (200 ep, sigma=0.8, jitter=0.5): broad targets, soft boundary,
    backbone learns density profile including gentle tail into H1 region.
  Phase 2 (200 ep, sigma=0.4, jitter=0.3): sharpen to individual peaks,
    backbone retains density awareness from Phase 1.

Jitter scaling: jitter ≈ sigma/1.4 keeps the signal at jitter extremes ≈ 0.67.
  sigma=0.8, jitter=0.5: exp(-(0.5²/(2*0.64))) = exp(-0.195) ≈ 0.82 ✓
  sigma=0.4, jitter=0.3: exp(-(0.3²/(2*0.16))) = exp(-0.281) ≈ 0.76 ✓

Both phases use t_range=(10, 250) — showing H1 as negative territory consistently
is the original suppression problem, but the sigma=0.8 phase creates a SOFT
negative (target≈0.04 at t=147) instead of the HARD zero we had before.

Hypothesis: sigma curriculum → backbone with density-aware H1 features →
  H1 unique zeros improve from 38/50 toward 43+/50.
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
    sigma: float,
    jitter: float,
) -> torch.Tensor:
    jittered = [z + random.uniform(-jitter, jitter) for z in zeros_t]
    t  = t_batch.unsqueeze(1)
    z  = torch.tensor(jittered, dtype=torch.float32, device=t.device)
    sq = ((t - z) ** 2) / (2.0 * sigma ** 2)
    return torch.exp(-sq).max(dim=1).values


def train_phase(
    model: RiemannNavigator,
    zeros_t: list[float],
    epochs: int,
    sigma: float,
    jitter: float,
    near_lr: float,
    backbone_lr: float,
    t_range: tuple[float, float] = (10.0, 250.0),
    label: str = "Phase",
    log_every: int = 50,
) -> None:
    near_params     = [p for n, p in model.named_parameters() if "near_head" in n]
    backbone_params = [p for n, p in model.named_parameters() if "near_head" not in n]
    opt   = optim.AdamW([
        {"params": near_params,     "lr": near_lr},
        {"params": backbone_params, "lr": backbone_lr},
    ], weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    print(f"\n  {label}: sigma={sigma}  jitter=±{jitter}  "
          f"near_lr={near_lr}  backbone_lr={backbone_lr}  "
          f"t_range=({t_range[0]},{t_range[1]})  {epochs} ep")
    print(f"\n  {'Epoch':>6}  {'L_near':>10}  {'Gap_log':>9}  {'Gap_chk':>9}  "
          f"{'H1_P_mean':>10}  {'H1_P_std':>9}")
    print(f"  {'------':>6}  {'----------':>10}  {'---------':>9}  {'---------':>9}  "
          f"{'----------':>10}  {'---------':>9}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, _, _ = make_riemann_batch(zeros_t, batch_size=128, t_range=t_range)
        s = s.to(DEVICE)
        out    = model(s)
        target = near_gaussian_target_jittered(s[:, 1], zeros_t, sigma=sigma, jitter=jitter)
        loss   = 5.0 * F.mse_loss(out["near_zero"], target)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % log_every == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                # Gap_log (with jitter, measures in-distribution signal)
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

                # Gap_chk (exact positions, measures generalization)
                t_at_ck  = torch.tensor(
                    [[0.5, z] for z in zeros_t[:25]], dtype=torch.float32
                ).to(DEVICE)
                t_far_ck = torch.tensor(
                    [[0.5, z + 3.0] for z in zeros_t[:25]], dtype=torch.float32
                ).to(DEVICE)
                gap_chk  = (model(t_at_ck)["near_zero"].mean()
                            - model(t_far_ck)["near_zero"].mean()).item()

                # H1 landscape probe (key diagnostic)
                t_h1 = torch.tensor(
                    [[0.5, 160.0 + 2*i] for i in range(25)], dtype=torch.float32
                ).to(DEVICE)
                p_h1 = model(t_h1)["near_zero"].cpu()

                l_val = F.mse_loss(out["near_zero"], target).item()

            print(f"  {epoch:>6}  {l_val:>10.6f}  {gap_log:>+9.4f}  {gap_chk:>+9.4f}"
                  f"  {p_h1.mean():>10.4f}  {p_h1.std():>9.4f}")


def amplitude_check(model: RiemannNavigator, zeros_t: list[float]) -> tuple[float, float]:
    model.eval()
    t_at  = torch.tensor([[0.5, z]       for z in zeros_t[:25]], dtype=torch.float32).to(DEVICE)
    t_far = torch.tensor([[0.5, z + 3.0] for z in zeros_t[:25]], dtype=torch.float32).to(DEVICE)
    t_h1  = torch.tensor([[0.5, 160.0 + 2*i] for i in range(25)], dtype=torch.float32).to(DEVICE)
    t_h2  = torch.tensor([[0.5, 260.0 + 2*i] for i in range(25)], dtype=torch.float32).to(DEVICE)
    with torch.no_grad():
        p_at  = model(t_at)["near_zero"].cpu()
        p_far = model(t_far)["near_zero"].cpu()
        p_h1  = model(t_h1)["near_zero"].cpu()
        p_h2  = model(t_h2)["near_zero"].cpu()
    gap = (p_at.mean() - p_far.mean()).item()
    print(f"  P@train zero:          mean={p_at.mean():.4f}  std={p_at.std():.4f}")
    print(f"  P@3.0 from train zero: mean={p_far.mean():.4f}  std={p_far.std():.4f}")
    print(f"  Gap (check):           {gap:+.4f}")
    print(f"  H1 midpoints t=160-208: mean={p_h1.mean():.4f}  std={p_h1.std():.4f}")
    print(f"  H2 midpoints t=260-308: mean={p_h2.mean():.4f}  std={p_h2.std():.4f}")
    return gap, p_h1.std().item()


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
    print(f"RiemannNavigator  hidden={HIDDEN}  layers={LAYERS}  heads={HEADS}  "
          f"params={n_params:,}")
    print(f"Sigma curriculum: Phase1 sigma=0.8/jitter=0.5 (200ep) → "
          f"Phase2 sigma=0.4/jitter=0.3 (200ep)")
    print(f"Hypothesis: sigma=0.8 soft tail into H1 → backbone retains density")
    print(f"  awareness after fine-tuning → H1 unique improves from 38→43+")
    print(f"  (baseline: jitter-only 200ep → 38 H1 + 37 H2 = 75/100 unique)")

    # ── Phase 1: broad sigma, soft boundary ──────────────────────────────────
    print(f"\n{'='*68}")
    print(f"PHASE 1 — sigma=0.8, jitter=±0.5, 200 ep  (density warm-up)")
    print(f"{'='*68}")
    train_phase(
        model, TRAIN_ZEROS,
        epochs=200, sigma=0.8, jitter=0.5,
        near_lr=1e-3, backbone_lr=3e-4,
        t_range=(10.0, 250.0),
        label="Phase1",
        log_every=50,
    )

    print(f"\n{'='*68}")
    print(f"AMPLITUDE CHECK after Phase 1")
    print(f"{'='*68}")
    gap1, h1std1 = amplitude_check(model, TRAIN_ZEROS)
    print(f"\n  Gap_chk={gap1:+.4f}  H1_std={h1std1:.4f}")

    # ── Phase 2: sharpen to sigma=0.4 ────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"PHASE 2 — sigma=0.4, jitter=±0.3, 200 ep  (peak sharpening)")
    print(f"{'='*68}")
    train_phase(
        model, TRAIN_ZEROS,
        epochs=200, sigma=0.4, jitter=0.3,
        near_lr=3e-4, backbone_lr=1e-4,   # slower lr: preserve Phase 1 features
        t_range=(10.0, 250.0),
        label="Phase2",
        log_every=50,
    )

    print(f"\n{'='*68}")
    print(f"AMPLITUDE CHECK after Phase 2")
    print(f"{'='*68}")
    gap2, h1std2 = amplitude_check(model, TRAIN_ZEROS)
    print(f"\n  Gap_chk={gap2:+.4f}  H1_std={h1std2:.4f}")
    print(f"  Phase1→Phase2 H1_std: {h1std1:.4f}→{h1std2:.4f}  "
          f"({'improved' if h1std2 > h1std1 else 'degraded'})")

    # ── Holdout evaluation ────────────────────────────────────────────────────
    for sep in [0.8, 0.4]:
        print(f"\n{'='*68}")
        print(f"HOLDOUT EVALUATION  sep={sep}")
        print(f"{'='*68}")
        h1_hits, h1_ph, h1_miss = holdout_report_crf(
            model, "zeros 51-100", HOLD1_ZEROS,
            t_scan_lo=min(HOLD1_ZEROS) - 1.0, t_scan_hi=max(HOLD1_ZEROS),
            n_known_before=50, sep=sep,
        )
        h2_hits, h2_ph, h2_miss = holdout_report_crf(
            model, "zeros 101-150", HOLD2_ZEROS,
            t_scan_lo=min(HOLD2_ZEROS) - 1.0, t_scan_hi=max(HOLD2_ZEROS),
            n_known_before=100, sep=sep,
        )
        h1_unique = len(HOLD1_ZEROS) - h1_miss
        h2_unique = len(HOLD2_ZEROS) - h2_miss
        print(f"\n  sep={sep}:")
        print(f"    H1 {h1_hits}/50 ({h1_ph} ph, {h1_miss} missed) → {h1_unique}/50 unique")
        print(f"    H2 {h2_hits}/50 ({h2_ph} ph, {h2_miss} missed) → {h2_unique}/50 unique")
        print(f"    Combined: {h1_hits+h2_hits} hits / {h1_unique+h2_unique} unique"
              f" / {h1_ph+h2_ph} phantoms")
        print(f"  {'↑ IMPROVEMENT' if h1_unique+h2_unique > 75 else '= SAME' if h1_unique+h2_unique >= 74 else '↓ REGRESSION'}"
              f" vs baseline 75/100 unique")

    # ── Ablation: Phase 1 only (sigma=0.8, no sharpening) ────────────────────
    print(f"\n{'='*68}")
    print(f"ABLATION: Phase 1 ONLY checkpoint (sigma=0.8, before sharpening)")
    print(f"  (re-run holdout on phase-1-only model to isolate curriculum benefit)")
    print(f"{'='*68}")
    # Re-train phase 1 only on a fresh model
    model_p1 = RiemannNavigator(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)
    train_phase(
        model_p1, TRAIN_ZEROS,
        epochs=200, sigma=0.8, jitter=0.5,
        near_lr=1e-3, backbone_lr=3e-4,
        t_range=(10.0, 250.0),
        label="P1-only",
        log_every=200,  # just final snapshot
    )
    h1_hits_p1, h1_ph_p1, h1_miss_p1 = holdout_report_crf(
        model_p1, "zeros 51-100", HOLD1_ZEROS,
        t_scan_lo=min(HOLD1_ZEROS) - 1.0, t_scan_hi=max(HOLD1_ZEROS),
        n_known_before=50, sep=0.8, verbose=False,
    )
    h2_hits_p1, h2_ph_p1, h2_miss_p1 = holdout_report_crf(
        model_p1, "zeros 101-150", HOLD2_ZEROS,
        t_scan_lo=min(HOLD2_ZEROS) - 1.0, t_scan_hi=max(HOLD2_ZEROS),
        n_known_before=100, sep=0.8, verbose=False,
    )
    h1u_p1 = len(HOLD1_ZEROS) - h1_miss_p1
    h2u_p1 = len(HOLD2_ZEROS) - h2_miss_p1
    print(f"\n  Phase1-only (sigma=0.8, no sharpening)  sep=0.8:")
    print(f"    H1 {h1_hits_p1}/50 ({h1_ph_p1} ph, {h1_miss_p1} missed) → {h1u_p1}/50 unique")
    print(f"    H2 {h2_hits_p1}/50 ({h2_ph_p1} ph, {h2_miss_p1} missed) → {h2u_p1}/50 unique")
    print(f"    Combined: {h1_hits_p1+h2_hits_p1} hits / {h1u_p1+h2u_p1} unique"
          f" / {h1_ph_p1+h2_ph_p1} phantoms")

    # ── Summary table ─────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"SUMMARY")
    print(f"{'='*68}")
    print(f"  {'Run':40}  {'H1':>4}  {'H2':>4}  {'Total':>7}  {'Phantoms':>9}")
    print(f"  {'-'*40}  {'----':>4}  {'----':>4}  {'-------':>7}  {'---------':>9}")
    print(f"  {'Baseline (200ep jitter ±0.3)':40}  {'38':>4}  {'37':>4}  {'75/100':>7}  {'7':>9}")
    print(f"  {'Phase1 only (sigma=0.8, 200ep)':40}  {h1u_p1:>4}  {h2u_p1:>4}"
          f"  {h1u_p1+h2u_p1:>3}/100  {h1_ph_p1+h2_ph_p1:>9}")
    # Curriculum result at sep=0.8 (last evaluated)
    print(f"  (Curriculum sep=0.8 result above)")


if __name__ == "__main__":
    main()
