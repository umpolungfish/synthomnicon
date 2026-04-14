"""
run_test4_frozen.py — Train Phase A, save checkpoint, then run frozen Phase B test.

Test 4 grammar claim: the theta_gate ($R_\\dagger$ co-domain catalyst) alone —
without backbone re-tuning — should lift hit rate above the 81.1% Phase A ceiling.

The frozen test is only meaningful if the backbone already carries useful xi(s)
representations. A cold backbone maps s to noise; theta_gate cannot lift noise.
This script:
  1. Trains RiemannNavigator (Phase A) for 200 epochs on zeros 1-100
  2. Saves to riemann_phase_a.pt
  3. Loads weights into RiemannNavigatorPhaseB (warm start)
  4. Runs train_phase_b_frozen() — only near_head + theta_gate trainable
  5. Reports gap_log before and after frozen training

Comparison baseline:
  Phase A alone (both backbone + near_head trained): gap_log ~ +0.5 at 200ep
  Frozen Phase B (only theta_gate added): grammar predicts gap_log improves
    beyond Phase A because theta corrects the co-domain, not the domain.
"""

import torch
from pathlib import Path

from navigators import RiemannNavigator
from riemann_predict import train as train_phase_a
from riemann_phase_b import (
    RiemannNavigatorPhaseB, train_phase_b_frozen, load_phase_a_weights, DEVICE,
)
from train_navigators import RIEMANN_ZEROS_T

PHASE_A_PATH = Path("riemann_phase_a.pt")

# Phase A uses RiemannNavigator defaults — smaller, faster to converge
HIDDEN   = 256
LAYERS   = 24
HEADS    = 8
NFOURIER = 32
FREQ_MAX = 2.0


def train_and_save_phase_a() -> RiemannNavigator:
    print("=" * 68)
    print("Step 1: Train Phase A (RiemannNavigator, 200 epochs)")
    print("=" * 68)

    model = RiemannNavigator(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)

    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigator  params={n_params:,}  device={DEVICE}")

    train_phase_a(
        model, RIEMANN_ZEROS_T,
        epochs=500, sigma=0.4, jitter=0.3,
        near_lr=1e-3, backbone_lr=3e-4,
        t_range_hi=260.0,
    )

    torch.save(model.state_dict(), PHASE_A_PATH)
    print(f"\nPhase A checkpoint saved → {PHASE_A_PATH}")
    return model


def run_frozen_phase_b():
    # Step 1: train Phase A
    phase_a = train_and_save_phase_a()

    # Measure Phase A gap_log before frozen Phase B
    import random
    phase_a.eval()
    with torch.no_grad():
        t_at  = torch.tensor(
            [[0.5, z + random.uniform(-0.1, 0.1)] for z in RIEMANN_ZEROS_T[:20]],
            dtype=torch.float32).to(DEVICE)
        t_far = torch.tensor(
            [[0.5, z + random.uniform(2.0, 4.0)] for z in RIEMANN_ZEROS_T[:20]],
            dtype=torch.float32).to(DEVICE)
        from navigators import RiemannNavigator
        gap_a = (phase_a(t_at)["near_zero"].mean()
                 - phase_a(t_far)["near_zero"].mean()).item()
    print(f"\nPhase A gap_log (baseline): {gap_a:+.4f}")

    # Step 2: load into Phase B, freeze backbone, train only theta_gate
    print("\n" + "=" * 68)
    print("Step 2: Frozen Phase B training (near_head + theta_gate only)")
    print("=" * 68)

    # Phase B must match Phase A architecture for layer-wise weight transfer.
    # input_proj will be re-initialized (different input_dim due to theta features).
    model_b = RiemannNavigatorPhaseB(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)
    n_b = sum(p.numel() for p in model_b.parameters())
    print(f"RiemannNavigatorPhaseB  params={n_b:,}")

    load_phase_a_weights(model_b, PHASE_A_PATH)

    train_phase_b_frozen(
        model_b, RIEMANN_ZEROS_T,
        epochs=200, sigma=0.4, jitter=0.3,
        near_lr=3e-4, t_range_hi=700.0,
        theta_weight=0.3,
    )

    # Measure final gap_log
    model_b.eval()
    with torch.no_grad():
        t_at_b  = torch.tensor(
            [[0.5, z + random.uniform(-0.1, 0.1)] for z in RIEMANN_ZEROS_T[:20]],
            dtype=torch.float32).to(DEVICE)
        t_far_b = torch.tensor(
            [[0.5, z + random.uniform(2.0, 4.0)] for z in RIEMANN_ZEROS_T[:20]],
            dtype=torch.float32).to(DEVICE)
        gap_b = (model_b(t_at_b)["near_zero"].mean()
                 - model_b(t_far_b)["near_zero"].mean()).item()

    print(f"\n{'='*68}")
    print(f"SUMMARY — Test 4 (frozen Phase B)")
    print(f"{'='*68}")
    print(f"  Phase A gap_log (baseline, full training):  {gap_a:+.4f}")
    print(f"  Frozen Phase B gap_log (theta_gate only):   {gap_b:+.4f}")
    delta = gap_b - gap_a
    print(f"  Delta:                                      {delta:+.4f}")
    print()
    if delta > 0.05:
        print(f"  CONFIRMED — theta_gate alone lifts gap_log above Phase A baseline.")
        print(f"  $R_\\dagger$ co-domain correction works without backbone re-tuning.")
    elif abs(delta) < 0.05:
        print(f"  NEUTRAL — theta_gate preserves Phase A performance without regression.")
        print(f"  $R_\\dagger$ promotion is cost-free but not independently sufficient.")
    else:
        print(f"  REGRESSION — frozen training hurt performance (theta_gate over-corrects).")
        print(f"  $R_\\dagger$ requires joint training, not pure co-domain replacement.")


if __name__ == "__main__":
    run_frozen_phase_b()
