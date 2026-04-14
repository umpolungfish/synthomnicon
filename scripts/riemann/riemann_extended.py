"""
riemann_extended.py — Two-stage holdout experiment for RiemannNavigator.

Train on zeros 1-50 (t <= 143.1).
Holdout 1: zeros 51-100  (t in [146.0, 236.5]) — reproduced from prior run.
Holdout 2: zeros 101-150 (t in [237.8, 318.9]) — never seen, never tested.

Uses exactly the same training setup as the 50/50 prior run:
  - make_riemann_batch with ZERO_T_SCALE=250
  - negatives from t_range=(10, 250)
  - same loss weights (lam_zero=1, lam_frob=0.5, lam_sym=1, lam_near=0.5)
  - AdamW + CosineAnnealingLR, grad clip 1.0

Architecture: hidden=240, layers=24, heads=24 (CrystalGNN_v11 winner config).
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

# ── Zeros 101-150 from mpmath (zetazero(n).imag, 15 sig figs) ───────────────
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

TRAIN_ZEROS = RIEMANN_ZEROS_T[:50]   # zeros 1-50
HOLD1_ZEROS = RIEMANN_ZEROS_T[50:]   # zeros 51-100
HOLD2_ZEROS = ZEROS_101_150          # zeros 101-150


# ── Utilities ────────────────────────────────────────────────────────────────

def nms(peaks: list[tuple[float, float]], sep: float) -> list[tuple[float, float]]:
    """Greedy NMS on (t, score) peaks, keeping highest-score within each window."""
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
) -> list[tuple[float, float, float]]:
    """
    Scan sigma=1/2 from t_min to t_max.
    Collect zero_t_pred VALUES as zero candidates (each scan point "votes" for
    the zero it thinks is nearest).  Also returns P(near) for diagnostics.

    Returns list of (zero_t_pred_denorm, p_near, scan_t) raw candidates.
    """
    model.eval()
    dev = next(model.parameters()).device

    t_raw = torch.linspace(t_min, t_max, n_pts)
    sigma = torch.full_like(t_raw, 0.5)
    s_in  = torch.stack([sigma, t_raw], dim=-1).to(dev)

    with torch.no_grad():
        out = model(s_in)

    t_vals    = t_raw.tolist()
    p_near    = out["near_zero"].cpu().tolist()
    zt_denorm = [v * ZERO_T_SCALE for v in out["zero_t"].cpu().tolist()]

    return list(zip(zt_denorm, p_near, t_vals))


def holdout_report(
    model: RiemannNavigator,
    label: str,
    known_zeros: list[float],
    t_scan_lo: float,
    t_scan_hi: float,
    t_result_lo: float,
    t_result_hi: float,
    nms_sep: float = 0.8,
    hit_thresh: float = 1.0,
) -> tuple[int, int, int]:
    n_pts = max(3000, int((t_scan_hi - t_scan_lo) * 20))
    raw_all = scan_critical_line(model, t_scan_lo, t_scan_hi, n_pts=n_pts)

    # Keep predictions that fall within the result window
    raw = [(zt, p) for zt, p, _ in raw_all if t_result_lo - 1.0 <= zt <= t_result_hi + 1.0]
    after_nms = nms(raw, sep=nms_sep)

    print(f"\n{'='*68}")
    print(f"HOLDOUT: {label}  (NEVER SEEN DURING TRAINING)")
    print(f"{'='*68}")
    # Diagnostics about the raw scan
    all_zt = [zt for zt, _, _ in raw_all]
    print(f"Scan: t in [{t_scan_lo:.0f}, {t_scan_hi:.0f}], {n_pts} pts")
    print(f"zero_t_pred range: [{min(all_zt):.1f}, {max(all_zt):.1f}]")
    print(f"Raw candidates in result window: {len(raw)}  "
          f"->  after NMS(sep={nms_sep}): {len(after_nms)}  (known: {len(known_zeros)})")
    print()
    print(f"  {'#':>4}  {'t_pred':>12}  {'P(near)':>9}  {'nearest zero':>14}"
          f"  {'delta':>8}  {'status':>8}")
    print(f"  {'----':>4}  {'------------':>12}  {'---------':>9}"
          f"  {'----------':>14}  {'--------':>8}  {'--------':>8}")

    hits, phantoms = 0, 0
    matched = set()
    for idx, (t_pred, p) in enumerate(after_nms, 1):
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
    print(f"\nRESULT: {hits}/{len(known_zeros)} zeros found"
          f"  |  {phantoms} phantoms  |  {len(missed)} missed")
    return hits, phantoms, len(missed)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    HIDDEN = 240
    LAYERS = 24
    HEADS  = 24
    EPOCHS = 800
    LR     = 3e-4
    BATCH  = 128

    model = RiemannNavigator(hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigator  hidden={HIDDEN}  layers={LAYERS}  heads={HEADS}"
          f"  params={n_params:,}")
    print(f"Train: zeros 1-50 (t <= {max(TRAIN_ZEROS):.1f})"
          f"   ZERO_T_SCALE={ZERO_T_SCALE}")
    print(f"Holdout 1: zeros 51-100  (t in [{min(HOLD1_ZEROS):.1f}, {max(HOLD1_ZEROS):.1f}])")
    print(f"Holdout 2: zeros 101-150 (t in [{min(HOLD2_ZEROS):.1f}, {max(HOLD2_ZEROS):.1f}])")
    print()

    opt   = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)

    print(f"  {'Epoch':>6}  {'L_frob':>10}  {'L_sym':>10}  {'L_near':>10}  {'Acc':>7}")
    print(f"  {'------':>6}  {'----------':>10}  {'----------':>10}"
          f"  {'----------':>10}  {'-------':>7}")

    for epoch in range(1, EPOCHS + 1):
        model.train()
        # Exact same batch function as the 50/50 working run:
        # zeros 1-50, negatives from t_range=(10, 250), ZERO_T_SCALE=250
        s, near, zero_t = make_riemann_batch(
            TRAIN_ZEROS,
            batch_size=BATCH,
            t_range=(10.0, 250.0),
        )
        s      = s.to(DEVICE)
        near   = near.to(DEVICE)
        zero_t = zero_t.to(DEVICE)

        out = model(s)
        losses = model.compute_loss(
            out,
            true_zero_t=zero_t,
            true_near=near,
            lam_zero=1.0, lam_frob=0.5, lam_sym=1.0, lam_near=0.5,
        )
        losses["loss"].backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        opt.zero_grad()
        sched.step()

        if epoch % 50 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                acc = ((out["near_zero"] > 0.5).float() == near).float().mean().item()
            print(f"  {epoch:>6}  {losses['L_frob']:>10.6f}  {losses['L_sym']:>10.6f}"
                  f"  {losses['L_near']:>10.6f}  {acc:>6.1%}")

    # ── Holdout 1: zeros 51-100 (reproduce prior 50/50) ─────────────────────
    # Scan from t=103 (end of dense training region) through holdout range
    h1_hits, h1_ph, h1_miss = holdout_report(
        model,
        label="zeros 51-100",
        known_zeros=HOLD1_ZEROS,
        t_scan_lo=103.0,
        t_scan_hi=238.0,
        t_result_lo=min(HOLD1_ZEROS),
        t_result_hi=max(HOLD1_ZEROS),
        nms_sep=0.8,
    )

    # ── Holdout 2: zeros 101-150 (new ground) ───────────────────────────────
    # Scan from t=230 (approaching holdout 2) through end
    h2_hits, h2_ph, h2_miss = holdout_report(
        model,
        label="zeros 101-150",
        known_zeros=HOLD2_ZEROS,
        t_scan_lo=230.0,
        t_scan_hi=322.0,
        t_result_lo=min(HOLD2_ZEROS),
        t_result_hi=max(HOLD2_ZEROS),
        nms_sep=0.8,
    )

    print(f"\n{'='*68}")
    print(f"SUMMARY")
    print(f"{'='*68}")
    print(f"  Holdout 1 (51-100):  {h1_hits}/50 found,  {h1_ph} phantoms,  {h1_miss} missed")
    print(f"  Holdout 2 (101-150): {h2_hits}/50 found,  {h2_ph} phantoms,  {h2_miss} missed")
    print(f"  Combined:            {h1_hits+h2_hits}/100 found")


if __name__ == "__main__":
    main()
