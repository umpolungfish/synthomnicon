"""
riemann_contrastive.py — Stage 1 + contrastive near_head + budget-Viterbi.

Grammar prescription (Probe 6 verdict + Probe 1d):
  Phase 1 — Stage 1 (800 ep, zeros 1-50, lam_near=0 — excluded to prevent
             gradient competition that starves the Frobenius basin).
             Achieves L_frob→0, L_sym→0, L_zero→small.
             The zero_t head learns zero positions; backbone encodes zero locus.

  Phase 2 — Contrastive near_head (400 ep, backbone FROZEN):
             L_contrastive = mean(max(0, margin - (near_zero(t_pos) - near_zero(t_neg))))
             t_pos: within eps=0.5 of a training zero (near_zero should be HIGH)
             t_neg: more than 2.0 from all zeros (near_zero should be LOW)
             The backbone already encodes zero proximity (zero_t proves it).
             The near_head just needs to learn to read it — a trivial 14k-param task
             once gradient competition from L_frob/L_sym is eliminated.

  Eval — budget-Viterbi decoder (Omega_Z hard constraint on N(t)).
         Now with genuine amplitude signal: P(near)≈0.9 at zeros, ≈0.1 elsewhere.
         Viterbi resolves closely-spaced zero pairs via score discrimination.

Target: 50/50 on both holdouts, 0 phantoms.
"""

from __future__ import annotations

import math
import random

import torch
import torch.nn as nn
import torch.optim as optim

from navigators import RiemannNavigator
from train_navigators import RIEMANN_ZEROS_T, ZERO_T_SCALE, make_riemann_batch
from riemann_crf import (
    ZEROS_101_150, rs_N, budget_viterbi, scan_near_zero, holdout_report_crf
)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TRAIN_ZEROS = RIEMANN_ZEROS_T[:50]
HOLD1_ZEROS = RIEMANN_ZEROS_T[50:]
HOLD2_ZEROS = ZEROS_101_150


# ── Contrastive batch generator ───────────────────────────────────────────────

def make_contrastive_batch(
    zeros_t: list[float],
    batch_size: int = 128,
    eps: float = 0.5,           # positive: within eps of a zero
    margin_far: float = 2.0,    # negative: at least margin_far from all zeros
    t_range: tuple[float, float] = (10.0, 250.0),
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Returns (s_pos, s_neg) each of shape [batch_size//2, 2].
    s_pos: on critical line (sigma=0.5) within eps of a zero.
    s_neg: on critical line more than margin_far from every zero.
    """
    half = batch_size // 2

    # Positives
    pos_t = []
    for _ in range(half):
        z = random.choice(zeros_t)
        t = z + random.uniform(-eps, eps)
        t = max(t_range[0], min(t_range[1], t))
        pos_t.append(t)

    # Negatives — rejection sample
    neg_t = []
    for _ in range(half * 200):
        if len(neg_t) >= half:
            break
        t = random.uniform(t_range[0], t_range[1])
        if all(abs(t - z) > margin_far for z in zeros_t):
            neg_t.append(t)
    # Pad if rejection sampling is slow (dense zero regions)
    while len(neg_t) < half:
        t = random.uniform(t_range[0], t_range[1])
        neg_t.append(t)

    s_pos = torch.tensor([[0.5, t] for t in pos_t], dtype=torch.float32)
    s_neg = torch.tensor([[0.5, t] for t in neg_t], dtype=torch.float32)
    return s_pos, s_neg


# ── Training phases ───────────────────────────────────────────────────────────

def train_stage1_no_near(
    model: RiemannNavigator,
    zeros_t: list[float],
    epochs: int = 800,
    lr: float = 3e-4,
    batch_size: int = 128,
) -> None:
    """
    Stage 1: train all losses EXCEPT L_near (lam_near=0).
    Eliminates gradient competition so Frobenius basin forms cleanly.
    The zero_t head encodes zero locus in the backbone.
    """
    opt   = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    print(f"\n  {'Epoch':>6}  {'L_frob':>10}  {'L_sym':>10}  {'L_zero':>10}  {'L_near':>10}  {'Acc':>7}")
    print(f"  {'------':>6}  {'----------':>10}  {'----------':>10}  {'----------':>10}  {'----------':>10}  {'-------':>7}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, near, zero_t = make_riemann_batch(
            zeros_t, batch_size=batch_size, t_range=(10.0, 250.0)
        )
        s = s.to(DEVICE); near = near.to(DEVICE); zero_t = zero_t.to(DEVICE)

        out = model(s)
        losses = model.compute_loss(
            out, true_zero_t=zero_t, true_near=near,
            lam_zero=1.0, lam_frob=0.5, lam_sym=1.0, lam_near=0.0,
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


def train_contrastive_near_head(
    model: RiemannNavigator,
    zeros_t: list[float],
    epochs: int = 400,
    lr: float = 1e-3,
    batch_size: int = 128,
    margin: float = 0.5,
    eps: float = 0.5,
    margin_far: float = 2.0,
) -> None:
    """
    Phase 2: freeze backbone, train near_head only with margin contrastive loss.
    Forces near_zero(near_zero_point) - near_zero(far_point) > margin.
    The backbone already encodes proximity (zero_t head proof); near_head
    just needs to learn to read it.
    """
    # Freeze backbone
    trainable_names = []
    for name, p in model.named_parameters():
        if "near_head" in name:
            p.requires_grad = True
            trainable_names.append(name)
        else:
            p.requires_grad = False
    n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n  [backbone frozen — near_head only: {n_trainable:,} params]")
    print(f"  [margin={margin}, eps={eps}, margin_far={margin_far}]")
    print(f"\n  {'Epoch':>6}  {'L_contrast':>12}  {'P(pos)':>8}  {'P(neg)':>8}  {'Gap':>8}")
    print(f"  {'------':>6}  {'------------':>12}  {'--------':>8}  {'--------':>8}  {'--------':>8}")

    opt = optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=lr, weight_decay=1e-4
    )
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    for epoch in range(1, epochs + 1):
        model.train()
        s_pos, s_neg = make_contrastive_batch(
            zeros_t, batch_size=batch_size, eps=eps,
            margin_far=margin_far, t_range=(10.0, 250.0),
        )
        s_pos = s_pos.to(DEVICE)
        s_neg = s_neg.to(DEVICE)

        with torch.no_grad():
            h_pos = model._encode(s_pos)   # frozen backbone
            h_neg = model._encode(s_neg)
        # Only near_head is trainable
        p_pos = model.near_head(h_pos).squeeze(-1)
        p_neg = model.near_head(h_neg).squeeze(-1)

        loss = torch.clamp(margin - (p_pos - p_neg), min=0.0).mean()
        loss.backward()
        nn.utils.clip_grad_norm_(
            [p for p in model.parameters() if p.requires_grad], 1.0
        )
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % 50 == 0 or epoch == 1:
            gap = (p_pos - p_neg).mean().item()
            print(f"  {epoch:>6}  {loss.item():>12.6f}  {p_pos.mean().item():>8.4f}"
                  f"  {p_neg.mean().item():>8.4f}  {gap:>8.4f}")

    # Unfreeze
    for p in model.parameters():
        p.requires_grad = True


# ── Main ──────────────────────────────────────────────────────────────────────

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
    print(f"  Phase 1: Stage 1 zeros 1-50 (800 ep, lam_near=0)")
    print(f"  Phase 2: contrastive near_head (400 ep, backbone frozen)")
    print(f"  Eval:    budget-Viterbi (Omega_Z)")

    # ── Phase 1 ───────────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"PHASE 1 — Stage 1, zeros 1-50, lam_near=0  (ZERO_T_SCALE={ZERO_T_SCALE})")
    print(f"{'='*68}")
    train_stage1_no_near(model, TRAIN_ZEROS, epochs=800, lr=3e-4, batch_size=BATCH)

    # ── Phase 2 ───────────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"PHASE 2 — contrastive near_head, backbone frozen")
    print(f"{'='*68}")
    train_contrastive_near_head(
        model, TRAIN_ZEROS,
        epochs=400, lr=1e-3, batch_size=BATCH,
        margin=0.5, eps=0.5, margin_far=2.0,
    )

    # ── Probe backbone discriminability ───────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"BACKBONE DISCRIMINABILITY CHECK")
    print(f"{'='*68}")
    model.eval()
    test_near = [z + random.uniform(-0.3, 0.3) for z in TRAIN_ZEROS[:10]]
    test_far  = [z + random.uniform(3.0, 5.0)  for z in TRAIN_ZEROS[:10]]
    s_near = torch.tensor([[0.5, t] for t in test_near], dtype=torch.float32).to(DEVICE)
    s_far  = torch.tensor([[0.5, t] for t in test_far],  dtype=torch.float32).to(DEVICE)
    with torch.no_grad():
        p_near_vals = model(s_near)["near_zero"].cpu().tolist()
        p_far_vals  = model(s_far) ["near_zero"].cpu().tolist()
    print(f"  P(near | within 0.3 of zero): mean={sum(p_near_vals)/len(p_near_vals):.4f}"
          f"  min={min(p_near_vals):.4f}  max={max(p_near_vals):.4f}")
    print(f"  P(near | 3-5 from zero):      mean={sum(p_far_vals)/len(p_far_vals):.4f}"
          f"  min={min(p_far_vals):.4f}  max={max(p_far_vals):.4f}")

    # ── Holdout 1 ─────────────────────────────────────────────────────────────
    h1_hits, h1_ph, h1_miss = holdout_report_crf(
        model, "zeros 51-100",
        HOLD1_ZEROS,
        t_scan_lo=min(HOLD1_ZEROS) - 1.0,
        t_scan_hi=max(HOLD1_ZEROS),
        n_known_before=50,
        sep=0.4,    # tighter sep: genuine scores can resolve closely-spaced pairs
    )

    # ── Holdout 2 ─────────────────────────────────────────────────────────────
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
    print(f"  Phase 1: Stage 1 zeros 1-50 (lam_near=0, 800 ep)")
    print(f"  Phase 2: contrastive near_head (margin=0.5, 400 ep, backbone frozen)")
    print(f"  Decoder: budget-Viterbi sep=0.4 (Omega_Z hard constraint)")
    print(f"  Holdout 1 (51-100):  {h1_hits}/50 found,  {h1_ph} phantoms,  {h1_miss} missed")
    print(f"  Holdout 2 (101-150): {h2_hits}/50 found,  {h2_ph} phantoms,  {h2_miss} missed")
    print(f"  Combined:            {h1_hits+h2_hits}/100 found")


if __name__ == "__main__":
    main()
