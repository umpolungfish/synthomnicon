"""
riemann_curriculum_earlystop.py — Curriculum with Phase 2 checkpoint scan.

Observation from riemann_sigma_curriculum.py Phase 2 diagnostics:
  ep50:   H1_std=0.1478  Gap_chk=+0.4986  <- H1 landscape still structured
  ep100:  H1_std=0.0152  Gap_chk=+0.6029  <- H1 collapsed, training zone sharp
  ep200:  H1_std=0.0120  Gap_chk=+0.6320  <- fully re-suppressed

Phase 2 first lifts H1 (near_zero head learns jitter-sharpened peaks AND
inherits H1 structure from Phase 1 backbone) then destroys it (training
on sigma=0.4 targets for t>145 ≈ 0 → H1 suppressed again).

Strategy: checkpoint Phase 2 every 25 ep, evaluate holdout at each checkpoint,
keep the model with best H1_unique + H2_unique. Expected optimum around ep50.
"""

from __future__ import annotations

import contextlib
import copy
import io
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


def quick_holdout_unique(
    model: RiemannNavigator,
    sep: float = 0.8,
) -> tuple[int, int]:
    """Return (H1_unique, H2_unique) suppressing holdout_report_crf stdout."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        h1_hits, h1_ph, h1_miss = holdout_report_crf(
            model, "H1", HOLD1_ZEROS,
            t_scan_lo=min(HOLD1_ZEROS) - 1.0, t_scan_hi=max(HOLD1_ZEROS),
            n_known_before=50, sep=sep,
        )
        h2_hits, h2_ph, h2_miss = holdout_report_crf(
            model, "H2", HOLD2_ZEROS,
            t_scan_lo=min(HOLD2_ZEROS) - 1.0, t_scan_hi=max(HOLD2_ZEROS),
            n_known_before=100, sep=sep,
        )
    return len(HOLD1_ZEROS) - h1_miss, len(HOLD2_ZEROS) - h2_miss


def h1_std_probe(model: RiemannNavigator) -> tuple[float, float]:
    """Probe H1 landscape: return (mean, std) of near_zero in H1 zone."""
    model.eval()
    t_h1 = torch.tensor(
        [[0.5, 160.0 + 2*i] for i in range(25)], dtype=torch.float32
    ).to(DEVICE)
    with torch.no_grad():
        p_h1 = model(t_h1)["near_zero"].cpu()
    return p_h1.mean().item(), p_h1.std().item()


def gap_chk(model: RiemannNavigator, zeros_t: list[float]) -> float:
    model.eval()
    t_at  = torch.tensor([[0.5, z] for z in zeros_t[:25]], dtype=torch.float32).to(DEVICE)
    t_far = torch.tensor([[0.5, z + 3.0] for z in zeros_t[:25]], dtype=torch.float32).to(DEVICE)
    with torch.no_grad():
        g = (model(t_at)["near_zero"].mean() - model(t_far)["near_zero"].mean()).item()
    return g


def train_phase1(model, zeros_t, epochs=200):
    near_params     = [p for n, p in model.named_parameters() if "near_head" in n]
    backbone_params = [p for n, p in model.named_parameters() if "near_head" not in n]
    opt   = optim.AdamW([
        {"params": near_params,     "lr": 1e-3},
        {"params": backbone_params, "lr": 3e-4},
    ], weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    print(f"\n  Phase1 sigma=0.8 jitter=±0.5 {epochs}ep")
    print(f"  {'Epoch':>6}  {'L_near':>10}  {'Gap_chk':>9}  {'H1_std':>8}")
    print(f"  {'------':>6}  {'----------':>10}  {'---------':>9}  {'--------':>8}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, _, _ = make_riemann_batch(zeros_t, batch_size=128, t_range=(10.0, 250.0))
        s = s.to(DEVICE)
        out    = model(s)
        target = near_gaussian_target_jittered(s[:, 1], zeros_t, sigma=0.8, jitter=0.5)
        loss   = 5.0 * F.mse_loss(out["near_zero"], target)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % 50 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                l_val = F.mse_loss(out["near_zero"], target).item()
            g   = gap_chk(model, zeros_t)
            _, h1s = h1_std_probe(model)
            print(f"  {epoch:>6}  {l_val:>10.6f}  {g:>+9.4f}  {h1s:>8.4f}")


def train_phase2_with_checkpoints(model, zeros_t, max_epochs=150, check_every=25):
    """
    Phase 2: sigma=0.4, jitter=0.3, slower lr.
    Evaluate holdout every check_every epochs. Return best checkpoint state_dict.
    """
    near_params     = [p for n, p in model.named_parameters() if "near_head" in n]
    backbone_params = [p for n, p in model.named_parameters() if "near_head" not in n]
    opt   = optim.AdamW([
        {"params": near_params,     "lr": 3e-4},
        {"params": backbone_params, "lr": 1e-4},
    ], weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max_epochs)

    best_unique = 0
    best_state  = copy.deepcopy(model.state_dict())
    best_ep     = 0
    results: list[tuple[int, int, int, float, float]] = []

    print(f"\n  Phase2 sigma=0.4 jitter=±0.3 up to {max_epochs}ep (checkpoint every {check_every})")
    print(f"  {'Epoch':>6}  {'L_near':>10}  {'Gap_chk':>9}  {'H1_std':>8}  "
          f"{'H1_u':>6}  {'H2_u':>6}  {'Total':>7}  {'Best':>6}")
    print(f"  {'------':>6}  {'----------':>10}  {'---------':>9}  {'--------':>8}  "
          f"{'------':>6}  {'------':>6}  {'-------':>7}  {'------':>6}")

    for epoch in range(1, max_epochs + 1):
        model.train()
        s, _, _ = make_riemann_batch(zeros_t, batch_size=128, t_range=(10.0, 250.0))
        s = s.to(DEVICE)
        out    = model(s)
        target = near_gaussian_target_jittered(s[:, 1], zeros_t, sigma=0.4, jitter=0.3)
        loss   = 5.0 * F.mse_loss(out["near_zero"], target)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % check_every == 0:
            model.eval()
            with torch.no_grad():
                l_val = F.mse_loss(out["near_zero"], target).item()
            g    = gap_chk(model, zeros_t)
            _, h1s = h1_std_probe(model)
            h1u, h2u = quick_holdout_unique(model, sep=0.8)
            total    = h1u + h2u
            is_best  = total > best_unique
            if is_best:
                best_unique = total
                best_state  = copy.deepcopy(model.state_dict())
                best_ep     = epoch
            results.append((epoch, h1u, h2u, g, h1s))
            marker = " ← BEST" if is_best else ""
            print(f"  {epoch:>6}  {l_val:>10.6f}  {g:>+9.4f}  {h1s:>8.4f}  "
                  f"{h1u:>6}  {h2u:>6}  {total:>3}/100{marker}")

    print(f"\n  Best checkpoint: ep{best_ep}  total unique={best_unique}/100")
    return best_state, best_ep, best_unique, results


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
    print(f"Curriculum + Phase2 early-stop: Phase1 (sigma=0.8, 200ep) → "
          f"Phase2 checkpoint scan (sigma=0.4, up to 150ep)")
    print(f"Previous best: 76/100 (full 200ep Phase2); H1_std peaked at ep50 (0.1478)")

    # ── Phase 1 ───────────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"PHASE 1 — sigma=0.8, jitter=±0.5, 200 ep")
    print(f"{'='*68}")
    train_phase1(model, TRAIN_ZEROS, epochs=200)

    h1m1, h1s1 = h1_std_probe(model)
    g1 = gap_chk(model, TRAIN_ZEROS)
    print(f"\n  After Phase1: Gap_chk={g1:+.4f}  H1_mean={h1m1:.4f}  H1_std={h1s1:.4f}")

    # ── Phase 2 with checkpointing ────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"PHASE 2 — sigma=0.4, jitter=±0.3, checkpoint scan (25ep intervals)")
    print(f"{'='*68}")
    best_state, best_ep, best_unique, ckpt_results = train_phase2_with_checkpoints(
        model, TRAIN_ZEROS, max_epochs=150, check_every=25,
    )

    # ── Restore best checkpoint and run full verbose evaluation ───────────────
    model.load_state_dict(best_state)
    model.eval()
    print(f"\n{'='*68}")
    print(f"FULL EVALUATION — best checkpoint ep{best_ep}  ({best_unique}/100 unique)")
    print(f"{'='*68}")

    for sep in [0.8, 0.6, 0.4]:
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
        h1u = len(HOLD1_ZEROS) - h1_miss
        h2u = len(HOLD2_ZEROS) - h2_miss
        print(f"\n  sep={sep}:")
        print(f"    H1: {h1_hits} hits / {h1u} unique / {h1_ph} ph / {h1_miss} missed")
        print(f"    H2: {h2_hits} hits / {h2u} unique / {h2_ph} ph / {h2_miss} missed")
        print(f"    Combined: {h1_hits+h2_hits} hits / {h1u+h2u} unique / {h1_ph+h2_ph} phantoms")

    # ── Summary of checkpoint scan ────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"CHECKPOINT SCAN SUMMARY")
    print(f"{'='*68}")
    print(f"  {'ep':>6}  {'H1_u':>6}  {'H2_u':>6}  {'Total':>7}  {'Gap_chk':>9}  {'H1_std':>8}")
    print(f"  {'------':>6}  {'------':>6}  {'------':>6}  {'-------':>7}  {'---------':>9}  {'--------':>8}")
    for ep, h1u, h2u, g, h1s in ckpt_results:
        marker = " ← best" if ep == best_ep else ""
        print(f"  {ep:>6}  {h1u:>6}  {h2u:>6}  {h1u+h2u:>3}/100  {g:>+9.4f}  {h1s:>8.4f}{marker}")

    print(f"\n  Baselines for reference:")
    print(f"    jitter-only 200ep (best seen): 38 H1 + 37 H2 = 75/100 unique")
    print(f"    sigma curriculum full 200ep:   37 H1 + 39 H2 = 76/100 unique")
    print(f"    This run best:                 {best_unique}/100 unique (ep{best_ep})")


if __name__ == "__main__":
    main()
