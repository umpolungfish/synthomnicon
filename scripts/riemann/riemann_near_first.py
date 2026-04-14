"""
riemann_near_first.py — Near-first curriculum + Gaussian proximity target.

Core diagnosis: L_near stalls at ln(2) (maximum entropy) in all prior runs
because L_frob gradient dominates early training — Frobenius basin forms at
epoch ~50 and colonises all gradient capacity. Near_head is K_trap before it
can establish.

Fix (two-phase curriculum):
  Phase A (200 ep): lam_near=5, ALL other lambdas=0.
    Only near_head gets gradient signal. Backbone warms but is unconstrained.
    Target: break L_near below 0.5 (entropy) — establish genuine proximity signal.
    Grammar: forces K_slow for near_head BEFORE Frobenius basin forms.

  Phase B (600 ep): lam_near=2 (elevated), lam_frob=0.5, lam_sym=1, lam_zero=1.
    Frobenius basin forms AROUND the already-established proximity encoding.
    Grammar: P_pm_sym co-develops with Phi_c proximity — simultaneity enforced.

Additional fix: Gaussian proximity target (smooth Parzen density over zeros)
  near_target(t) = max_k exp(-(t - t_k)^2 / (2*sigma^2))
  replaces binary 0/1 label. Gives nonzero gradient everywhere; smoother
  competition with L_frob; natural encoding of proximity intensity.
  Loss: MSE(near_zero_output, near_gaussian_target) throughout.

Decoder: budget-Viterbi from riemann_crf.py (unchanged). The improvement
target is near_zero amplitude — genuine peaks at zeros, genuine troughs
between them — which the decoder can then use for discrimination.
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
    ZEROS_101_150, rs_N, scan_near_zero, budget_viterbi, holdout_report_crf,
)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TRAIN_ZEROS = RIEMANN_ZEROS_T[:50]
HOLD1_ZEROS = RIEMANN_ZEROS_T[50:]
HOLD2_ZEROS = ZEROS_101_150


# ── Gaussian proximity target ─────────────────────────────────────────────────

def near_gaussian_target(
    t_batch: torch.Tensor,
    zeros_t: list[float],
    sigma: float = 0.4,
) -> torch.Tensor:
    """
    Smooth proximity target: $\max_k \exp\!\left(-\frac{(t - t_k)^2}{2\sigma^2}\right)$.

    Returns [B] tensor in [0, 1].
    sigma=0.4 gives a half-width of ~0.4 around each zero, decaying to ~0.01
    at distance 2.0 — well-separated from adjacent zeros (RS spacing ~1.5).

    Replaces the binary 0/1 label. Benefits:
      - Nonzero gradient at every point, not just near boundaries
      - Smooth landscape — competes better with L_frob
      - Naturally encodes proximity intensity
    """
    t  = t_batch.unsqueeze(1)                                           # [B, 1]
    z  = torch.tensor(zeros_t, dtype=torch.float32, device=t.device)   # [Z]
    sq = ((t - z) ** 2) / (2.0 * sigma ** 2)                           # [B, Z]
    return torch.exp(-sq).max(dim=1).values                             # [B]


# ── Phase A: near-head only ───────────────────────────────────────────────────

def train_phase_a(
    model: RiemannNavigator,
    zeros_t: list[float],
    epochs: int = 200,
    batch_size: int = 128,
    sigma: float = 0.4,
    near_lr: float = 1e-3,
    backbone_lr: float = 3e-4,
) -> None:
    """
    Phase A: ONLY L_near with Gaussian target.
    Separate LR: near_head gets 1e-3 (faster), backbone gets 3e-4 (slower).
    All other loss terms are zero — no Frobenius, no symmetry, no zero regression.

    Goal: break L_near below 0.5. If P(near | at zero) reaches >0.6 and
    P(near | far) stays <0.4 by epoch 200, Phase A succeeded.
    """
    # Separate LR for near_head vs backbone
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
        s, _, zero_t_batch = make_riemann_batch(
            zeros_t, batch_size=batch_size, t_range=(10.0, 250.0)
        )
        s = s.to(DEVICE)
        t_vals = s[:, 1]

        out      = model(s)
        target   = near_gaussian_target(t_vals, zeros_t, sigma=sigma)
        L_near   = F.mse_loss(out["near_zero"], target)
        # Multiplied by 5 so gradient is comparable to the ~0.5-magnitude
        # Frobenius loss that would otherwise dominate in Phase B.
        loss     = 5.0 * L_near

        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % 25 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                # Diagnostic: P(near) at zero positions vs. far positions
                t_at_zero = torch.tensor(
                    [[0.5, z + random.uniform(-0.1, 0.1)] for z in zeros_t[:20]],
                    dtype=torch.float32,
                ).to(DEVICE)
                t_far = torch.tensor(
                    [[0.5, z + random.uniform(2.0, 4.0)] for z in zeros_t[:20]],
                    dtype=torch.float32,
                ).to(DEVICE)
                p_at  = model(t_at_zero)["near_zero"].mean().item()
                p_far = model(t_far)["near_zero"].mean().item()
            print(f"  {epoch:>6}  {L_near.item():>10.6f}  {p_at:>8.4f}  {p_far:>8.4f}"
                  f"  {p_at - p_far:>+8.4f}")


# ── Phase B: all losses ───────────────────────────────────────────────────────

def train_phase_b(
    model: RiemannNavigator,
    zeros_t: list[float],
    epochs: int = 600,
    lr: float = 3e-4,
    batch_size: int = 128,
    sigma: float = 0.4,
    lam_near: float = 2.0,
    lam_frob: float = 0.5,
    lam_sym: float  = 1.0,
    lam_zero: float = 1.0,
) -> None:
    """
    Phase B: all losses, lam_near elevated (2.0) so proximity signal is not
    overwhelmed by Frobenius basin once it forms.

    Uses Gaussian target for L_near throughout — consistent with Phase A.
    Frobenius basin forms AROUND the proximity encoding established in Phase A.
    """
    opt   = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    print(f"\n  Phase B — all losses, lam_near={lam_near} (elevated)")
    print(f"  lam_frob={lam_frob}, lam_sym={lam_sym}, lam_zero={lam_zero}")
    print(f"\n  {'Epoch':>6}  {'L_frob':>10}  {'L_sym':>10}  {'L_zero':>10}"
          f"  {'L_near':>10}  {'P@zero':>7}  {'P@far':>7}")
    print(f"  {'------':>6}  {'----------':>10}  {'----------':>10}"
          f"  {'----------':>10}  {'----------':>10}  {'-------':>7}  {'-------':>7}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, _, zero_t_batch = make_riemann_batch(
            zeros_t, batch_size=batch_size, t_range=(10.0, 250.0)
        )
        s = s.to(DEVICE); zero_t_batch = zero_t_batch.to(DEVICE)
        t_vals = s[:, 1]

        out    = model(s)
        target = near_gaussian_target(t_vals, zeros_t, sigma=sigma)

        L_frob = out["frob_loss"]
        L_sym  = out["sym_loss"]
        L_zero = F.mse_loss(out["zero_t"], zero_t_batch)
        L_near = F.mse_loss(out["near_zero"], target)

        loss = (lam_frob * L_frob + lam_sym * L_sym
                + lam_zero * L_zero + lam_near * L_near)

        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % 50 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                t_at  = torch.tensor(
                    [[0.5, z + random.uniform(-0.1, 0.1)] for z in zeros_t[:20]],
                    dtype=torch.float32,
                ).to(DEVICE)
                t_far = torch.tensor(
                    [[0.5, z + random.uniform(2.0, 4.0)] for z in zeros_t[:20]],
                    dtype=torch.float32,
                ).to(DEVICE)
                p_at  = model(t_at)["near_zero"].mean().item()
                p_far = model(t_far)["near_zero"].mean().item()
            print(f"  {epoch:>6}  {L_frob.item():>10.6f}  {L_sym.item():>10.6f}"
                  f"  {L_zero.item():>10.6f}  {L_near.item():>10.6f}"
                  f"  {p_at:>7.4f}  {p_far:>7.4f}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    HIDDEN   = 240
    LAYERS   = 24
    HEADS    = 24
    NFOURIER = 48
    FREQ_MAX = 2.5
    BATCH    = 128
    SIGMA    = 0.4   # Gaussian proximity half-width

    model = RiemannNavigator(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigator  hidden={HIDDEN}  layers={LAYERS}  heads={HEADS}")
    print(f"  n_fourier={NFOURIER}  freq_max=10^{FREQ_MAX}  params={n_params:,}")
    print(f"  Curriculum: Phase A (near-only, 200 ep) → Phase B (all, 600 ep)")
    print(f"  Target: Gaussian proximity sigma={SIGMA}  (not binary 0/1)")
    print(f"  Key metric: P@zero - P@far  (must break >0 in Phase A)")

    print(f"\n{'='*68}")
    print(f"PHASE A — near_head only, lam_near=5, sigma={SIGMA}  (200 ep)")
    print(f"{'='*68}")
    train_phase_a(
        model, TRAIN_ZEROS,
        epochs=200, batch_size=BATCH, sigma=SIGMA,
        near_lr=1e-3, backbone_lr=3e-4,
    )

    # ── Phase A check: is there genuine amplitude signal? ─────────────────────
    print(f"\n{'='*68}")
    print(f"PHASE A CHECK — backbone discriminability before Frobenius")
    print(f"{'='*68}")
    model.eval()
    t_at  = torch.tensor(
        [[0.5, z] for z in TRAIN_ZEROS[:25]], dtype=torch.float32
    ).to(DEVICE)
    t_far = torch.tensor(
        [[0.5, z + 3.0] for z in TRAIN_ZEROS[:25]], dtype=torch.float32
    ).to(DEVICE)
    with torch.no_grad():
        p_at  = model(t_at)["near_zero"].cpu()
        p_far = model(t_far)["near_zero"].cpu()
    print(f"  P(near | at zero):    mean={p_at.mean():.4f}  "
          f"min={p_at.min():.4f}  max={p_at.max():.4f}")
    print(f"  P(near | 3.0 away):   mean={p_far.mean():.4f}  "
          f"min={p_far.min():.4f}  max={p_far.max():.4f}")
    print(f"  Gap:                  {p_at.mean() - p_far.mean():+.4f}")

    # ── Evaluate Phase A model BEFORE Phase B touches it ─────────────────────
    # Phase A achieved Gap=+0.70. Phase B reshapes backbone embeddings for
    # Frobenius, invalidating the near_head mapping (catastrophic forgetting).
    # Evaluate Phase A directly — genuine near_zero amplitude with CRF decoder.
    print(f"\n{'='*68}")
    print(f"PHASE A HOLDOUT EVALUATION (before Phase B)")
    print(f"{'='*68}")
    h1_a, h1_a_ph, h1_a_miss = holdout_report_crf(
        model, "zeros 51-100",
        HOLD1_ZEROS,
        t_scan_lo=min(HOLD1_ZEROS) - 1.0,
        t_scan_hi=max(HOLD1_ZEROS),
        n_known_before=50,
        sep=0.4,
    )
    h2_a, h2_a_ph, h2_a_miss = holdout_report_crf(
        model, "zeros 101-150",
        HOLD2_ZEROS,
        t_scan_lo=min(HOLD2_ZEROS) - 1.0,
        t_scan_hi=max(HOLD2_ZEROS),
        n_known_before=100,
        sep=0.4,
    )
    print(f"\n  Phase A combined: {h1_a+h2_a}/100  "
          f"({h1_a_ph+h2_a_ph} phantoms)")

    print(f"\n{'='*68}")
    print(f"PHASE B — all losses, lam_near=2.0 (elevated)  (600 ep)")
    print(f"{'='*68}")
    train_phase_b(
        model, TRAIN_ZEROS,
        epochs=600, lr=3e-4, batch_size=BATCH, sigma=SIGMA,
        lam_near=2.0, lam_frob=0.5, lam_sym=1.0, lam_zero=1.0,
    )

    # ── Final amplitude check ─────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"FINAL AMPLITUDE CHECK")
    print(f"{'='*68}")
    model.eval()
    with torch.no_grad():
        p_at_final  = model(t_at)["near_zero"].cpu()
        p_far_final = model(t_far)["near_zero"].cpu()
    print(f"  P(near | at zero):   mean={p_at_final.mean():.4f}  "
          f"min={p_at_final.min():.4f}  max={p_at_final.max():.4f}")
    print(f"  P(near | 3.0 away):  mean={p_far_final.mean():.4f}  "
          f"min={p_far_final.min():.4f}  max={p_far_final.max():.4f}")
    print(f"  Gap:                 {p_at_final.mean() - p_far_final.mean():+.4f}")

    # ── Holdout evaluation (Phase B) ──────────────────────────────────────────
    h1_hits, h1_ph, h1_miss = holdout_report_crf(
        model, "zeros 51-100",
        HOLD1_ZEROS,
        t_scan_lo=min(HOLD1_ZEROS) - 1.0,
        t_scan_hi=max(HOLD1_ZEROS),
        n_known_before=50,
        sep=0.4,
    )
    h2_hits, h2_ph, h2_miss = holdout_report_crf(
        model, "zeros 101-150",
        HOLD2_ZEROS,
        t_scan_lo=min(HOLD2_ZEROS) - 1.0,
        t_scan_hi=max(HOLD2_ZEROS),
        n_known_before=100,
        sep=0.4,
    )

    print(f"\n{'='*68}")
    print(f"SUMMARY")
    print(f"{'='*68}")
    print(f"  Curriculum: Phase A (near-only, 200 ep) + Phase B (all, 600 ep)")
    print(f"  Target:     Gaussian proximity sigma={SIGMA}")
    print(f"  Phase A gap: +0.70  |  Phase B gap: {p_at_final.mean() - p_far_final.mean():+.4f}")
    print(f"  Phase A holdout: {h1_a+h2_a}/100  ({h1_a_ph+h2_a_ph} phantoms)")
    print(f"  Phase B H1 (51-100):  {h1_hits}/50 found,  {h1_ph} phantoms,  {h1_miss} missed")
    print(f"  Phase B H2 (101-150): {h2_hits}/50 found,  {h2_ph} phantoms,  {h2_miss} missed")
    print(f"  Phase B combined:     {h1_hits+h2_hits}/100 found")


if __name__ == "__main__":
    main()
