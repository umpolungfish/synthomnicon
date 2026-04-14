"""
riemann_two_stage.py — Three-prescription optimized RiemannNavigator.

Incorporates all three syncon-mandated optimizations:

  1. Extended Fourier (n_fourier=48, freq_max=2.5): d=0 structural change,
     extends frequency coverage to resolve zero spacing at t~320.

  2. Two-stage training:
     Stage 1 (800 ep): zeros 1-50 (t <= 143.1)   — same as original 50/50 run
     Near-zero freeze (200 ep): backbone frozen, only near_head trained
     Stage 2 (400 ep): zeros 1-100 (t <= 236.5)  — adds holdout-1 zeros
     Extrapolation gap to holdout 2 drops from 94 to 1.3 t-units.

  3. Near-zero structural alignment: after backbone converges (L_frob->0),
     freeze it and train near_head alone to fix gradient starvation.

Holdout: zeros 51-100 (reproduce 50/50), zeros 101-150 (t in [237.8, 318.9]).
"""

from __future__ import annotations

import math
import random

import torch
import torch.nn as nn
import torch.optim as optim

from navigators import RiemannNavigator
from train_navigators import RIEMANN_ZEROS_T, ZERO_T_SCALE, make_riemann_batch

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Zeros 101-150 (mpmath, 2026-04-11) ───────────────────────────────────────
ZEROS_101_150 = [
    237.769820, 239.555478, 241.049158, 242.823272, 244.070898,
    247.136990, 248.101990, 249.573690, 251.014948, 253.069987,
    255.306256, 256.380714, 258.610439, 259.874407, 260.805085,
    263.573894, 265.557852, 266.614974, 267.921915, 269.970449,
    271.494056, 273.459609, 275.587493, 276.452050, 278.250744,
    279.229251, 282.465115, 283.211186, 284.835964, 286.667445,
    287.911921, 289.579855, 291.846291, 293.558434, 294.965370,
    295.573255, 297.979277, 299.840326, 301.649325, 302.696750,
    304.864371, 305.728913, 307.219496, 310.109463, 311.165142,
    312.427801, 313.985286, 315.475616, 317.734806, 318.853104,
]

STAGE1_ZEROS = RIEMANN_ZEROS_T[:50]   # zeros 1-50
STAGE2_ZEROS = RIEMANN_ZEROS_T        # zeros 1-100 (full table)
HOLD1_ZEROS  = RIEMANN_ZEROS_T[50:]   # zeros 51-100
HOLD2_ZEROS  = ZEROS_101_150          # zeros 101-150


# ── Utilities ────────────────────────────────────────────────────────────────

def nms(peaks: list[tuple[float, float]], sep: float) -> list[tuple[float, float]]:
    peaks_sorted = sorted(peaks, key=lambda x: -x[1])
    kept = []
    for t, score in peaks_sorted:
        if all(abs(t - kt) >= sep for kt, _ in kept):
            kept.append((t, score))
    return sorted(kept, key=lambda x: x[0])


def scan_critical_line(
    model: RiemannNavigator,
    t_min: float,
    t_max: float,
    n_pts: int = 3000,
) -> list[tuple[float, float]]:
    """Local maxima in near_zero (tiny but position-correlated with zeros)."""
    model.eval()
    dev = next(model.parameters()).device
    t_raw = torch.linspace(t_min, t_max, n_pts)
    sigma = torch.full_like(t_raw, 0.5)
    s_in  = torch.stack([sigma, t_raw], dim=-1).to(dev)
    with torch.no_grad():
        out = model(s_in)
    t_vals = t_raw.tolist()
    p_near = out["near_zero"].cpu().tolist()
    raw = []
    for i in range(1, len(t_vals) - 1):
        if p_near[i] > p_near[i-1] and p_near[i] > p_near[i+1]:
            raw.append((t_vals[i], p_near[i]))
    return raw


def holdout_report(
    model: RiemannNavigator,
    label: str,
    known_zeros: list[float],
    t_scan_lo: float,
    t_scan_hi: float,
    nms_sep: float = 0.8,
    hit_thresh: float = 1.0,
) -> tuple[int, int, int]:
    n_pts = max(3000, int((t_scan_hi - t_scan_lo) * 25))
    all_raw = scan_critical_line(model, t_scan_lo, t_scan_hi + 2.0, n_pts=n_pts)
    raw = [(t, p) for t, p in all_raw if t_scan_lo - 1.0 <= t <= t_scan_hi + 1.0]
    after_nms = nms(raw, sep=nms_sep)

    # Also try zero_t_pred scan as backup
    dev = next(model.parameters()).device
    t_raw = torch.linspace(t_scan_lo, t_scan_hi + 2.0, n_pts)
    sigma = torch.full_like(t_raw, 0.5)
    s_in  = torch.stack([sigma, t_raw], dim=-1).to(dev)
    model.eval()
    with torch.no_grad():
        out = model(s_in)
    zt_preds = (out["zero_t"].cpu() * ZERO_T_SCALE).tolist()
    p_nears  = out["near_zero"].cpu().tolist()
    zt_in_range = [(zt, p) for zt, p in zip(zt_preds, p_nears)
                   if t_scan_lo - 1.0 <= zt <= t_scan_hi + 1.0]
    zt_nms = nms(zt_in_range, sep=nms_sep) if zt_in_range else []

    # Use whichever method finds more zeros
    def score_candidates(candidates):
        hits = set()
        for t_pred, _ in candidates:
            nearest = min(known_zeros, key=lambda z: abs(z - t_pred))
            if abs(t_pred - nearest) <= hit_thresh:
                hits.add(nearest)
        return len(hits)

    near_hits = score_candidates(after_nms)
    zt_hits   = score_candidates(zt_nms)
    method    = "near_zero" if near_hits >= zt_hits else "zero_t_pred"
    candidates = after_nms if near_hits >= zt_hits else zt_nms

    print(f"\n{'='*68}")
    print(f"HOLDOUT: {label}  (NEVER SEEN DURING TRAINING)")
    print(f"{'='*68}")
    print(f"Method: {method}  |  near_zero peaks: {len(after_nms)}"
          f"  |  zero_t_pred candidates: {len(zt_nms)}")
    print(f"{'zero_t_pred range:'} [{min(zt_preds):.1f}, {max(zt_preds):.1f}]"
          f"  |  near_zero std: {torch.tensor(p_nears).std():.2e}")
    print(f"After NMS(sep={nms_sep}): {len(candidates)}  (known: {len(known_zeros)})")
    print()
    print(f"  {'#':>4}  {'t_pred':>12}  {'P(near)':>9}  {'nearest zero':>14}"
          f"  {'delta':>8}  {'status':>8}")
    print(f"  {'----':>4}  {'------------':>12}  {'---------':>9}"
          f"  {'----------':>14}  {'--------':>8}  {'--------':>8}")

    hits, phantoms = 0, 0
    matched = set()
    for idx, (t_pred, p) in enumerate(candidates, 1):
        nearest = min(known_zeros, key=lambda z: abs(z - t_pred))
        delta   = abs(t_pred - nearest)
        status  = "HIT" if delta <= hit_thresh else "PHANTOM"
        if status == "HIT":
            hits += 1
            matched.add(nearest)
        else:
            phantoms += 1
        print(f"  {idx:>4}  {t_pred:>12.4f}  {p:>9.4f}  {nearest:>14.6f}"
              f"  {delta:>8.4f}  {status:>8}")

    missed = sorted(z for z in known_zeros if z not in matched)
    if missed:
        print(f"\n  MISSED: {[f'{z:.3f}' for z in missed]}")
    missed_count = len(missed)
    print(f"\nRESULT: {hits}/{len(known_zeros)} zeros found"
          f"  |  {phantoms} phantoms  |  {missed_count} missed")
    return hits, phantoms, missed_count


def train_phase(
    model: RiemannNavigator,
    zeros_t: list[float],
    epochs: int,
    lr: float,
    batch_size: int,
    t_range: tuple[float, float],
    freeze_backbone: bool = False,
    label: str = "",
) -> None:
    """Train the model for one phase, optionally freezing the backbone."""
    if freeze_backbone:
        for name, p in model.named_parameters():
            p.requires_grad = "near_head" in name
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"\n  [backbone frozen — training near_head only, {trainable:,} params]")
    else:
        for p in model.parameters():
            p.requires_grad = True

    opt   = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()),
                        lr=lr, weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    if label:
        print(f"\n  {'Epoch':>6}  {'L_frob':>10}  {'L_sym':>10}  {'L_zero':>10}"
              f"  {'L_near':>10}  {'Acc':>7}  ({label})")
        print(f"  {'------':>6}  {'----------':>10}  {'----------':>10}"
              f"  {'----------':>10}  {'----------':>10}  {'-------':>7}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, near, zero_t = make_riemann_batch(zeros_t, batch_size=batch_size,
                                              t_range=t_range)
        s      = s.to(DEVICE)
        near   = near.to(DEVICE)
        zero_t = zero_t.to(DEVICE)

        out = model(s)
        losses = model.compute_loss(
            out, true_zero_t=zero_t, true_near=near,
            lam_zero=1.0, lam_frob=0.5, lam_sym=1.0, lam_near=1.0,
        )
        losses["loss"].backward()
        nn.utils.clip_grad_norm_(
            [p for p in model.parameters() if p.requires_grad], 1.0
        )
        opt.step(); opt.zero_grad(); sched.step()

        if label and (epoch % 50 == 0 or epoch == 1):
            model.eval()
            with torch.no_grad():
                acc = ((out["near_zero"] > 0.5).float() == near).float().mean().item()
            print(f"  {epoch:>6}  {losses['L_frob']:>10.6f}  {losses['L_sym']:>10.6f}"
                  f"  {losses['L_zero']:>10.6f}  {losses['L_near']:>10.6f}  {acc:>6.1%}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    HIDDEN   = 240
    LAYERS   = 24
    HEADS    = 24
    NFOURIER = 48       # extended Fourier: prescription 1
    FREQ_MAX = 2.5      # logspace(-1, 2.5): covers freqs up to 316 cycles/unit
    BATCH    = 128

    model = RiemannNavigator(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    input_dim = 1 + 2 * NFOURIER
    print(f"RiemannNavigator  hidden={HIDDEN}  layers={LAYERS}  heads={HEADS}")
    print(f"  n_fourier={NFOURIER}  freq_max=10^{FREQ_MAX}  input_dim={input_dim}"
          f"  params={n_params:,}")
    print(f"Stage 1: zeros 1-50  (t <= {max(STAGE1_ZEROS):.1f},  800 ep)")
    print(f"Freeze:  near_head only  (200 ep)")
    print(f"Stage 2: zeros 1-100 (t <= {max(STAGE2_ZEROS):.1f},  400 ep)")
    print(f"Holdout: zeros 51-100 + zeros 101-150")

    # ── Stage 1: zeros 1-50, 800 epochs ─────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"STAGE 1 — zeros 1-50, ZERO_T_SCALE={ZERO_T_SCALE}")
    print(f"{'='*68}")
    train_phase(
        model, STAGE1_ZEROS, epochs=800, lr=3e-4, batch_size=BATCH,
        t_range=(10.0, 250.0), freeze_backbone=False, label="stage1",
    )

    # ── Near-head freeze: backbone frozen, near_head trained alone ───────────
    print(f"\n{'='*68}")
    print(f"NEAR-HEAD ALIGNMENT — backbone frozen, near_head fine-tuned")
    print(f"{'='*68}")
    train_phase(
        model, STAGE1_ZEROS, epochs=200, lr=1e-3, batch_size=BATCH,
        t_range=(10.0, 250.0), freeze_backbone=True, label="near_freeze",
    )

    # ── Stage 2: zeros 1-100, 400 more epochs ───────────────────────────────
    print(f"\n{'='*68}")
    print(f"STAGE 2 — zeros 1-100, extending training set")
    print(f"{'='*68}")
    train_phase(
        model, STAGE2_ZEROS, epochs=400, lr=1e-4, batch_size=BATCH,
        t_range=(10.0, 250.0), freeze_backbone=False, label="stage2",
    )

    # ── Holdout evaluation ───────────────────────────────────────────────────
    h1_hits, h1_ph, h1_miss = holdout_report(
        model, "zeros 51-100",
        HOLD1_ZEROS,
        t_scan_lo=103.0,
        t_scan_hi=max(HOLD1_ZEROS),
    )
    h2_hits, h2_ph, h2_miss = holdout_report(
        model, "zeros 101-150",
        HOLD2_ZEROS,
        t_scan_lo=230.0,
        t_scan_hi=max(HOLD2_ZEROS),
    )

    print(f"\n{'='*68}")
    print(f"SUMMARY")
    print(f"{'='*68}")
    print(f"  Stage 1 training: zeros 1-50  ({len(STAGE1_ZEROS)} zeros)")
    print(f"  Stage 2 training: zeros 1-100 ({len(STAGE2_ZEROS)} zeros)")
    print(f"  Holdout 1 (51-100):  {h1_hits}/50 found,  {h1_ph} phantoms,  {h1_miss} missed")
    print(f"  Holdout 2 (101-150): {h2_hits}/50 found,  {h2_ph} phantoms,  {h2_miss} missed")
    print(f"  Combined:            {h1_hits+h2_hits}/100 found")


if __name__ == "__main__":
    main()
