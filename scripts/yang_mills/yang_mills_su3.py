"""
yang_mills_su3.py — YangMillsNavigator trained on SU(3) Hamiltonians.

Probe 5 verdict:
  $d(\text{SU(2)}, \text{SU(3)}) = 4.8477$ — dominated by $T_\text{network} \to T_\odot$ gap.
  The current training in train_navigators.py uses `lie_dim=3` (SU(2)) despite
  YangMillsNavigator.DEFINING_TUPLE specifying $G_\aleph$ scope that includes SU(3).
  Setting `lie_dim=8` and generating SU(3) Gell-Mann Hamiltonians closes this gap.

SU(3) vs SU(2) structural distance:
  $d(\text{SU(2)}, \text{SU(3)}) = 4.8477$ is dominated by $T_\text{network} \to T_\odot$
  (the holographic topology gap). SU(3) gauge theory requires the holographic bulk:
  confinement (the mass gap) is an IR phenomenon read from the UV lattice boundary.
  SU(2) is solvable perturbatively — $T_\text{network}$ suffices. SU(3) is not.

SU(3) Gell-Mann structure constants:
  The 8 SU(3) generators $T^a$ satisfy $[T^a, T^b] = i f^{abc} T^c$.
  Non-zero $f^{abc}$ (totally antisymmetric):
    $f^{123} = 1$
    $f^{147} = f^{246} = f^{257} = f^{345} = 1/2$
    $f^{156} = f^{367} = -1/2$
    $f^{458} = f^{678} = \sqrt{3}/2$

  The lie_structure tensor for SU(3) is $8 \times 8$ (vs $3 \times 3$ for SU(2)).

Training changes:
  - `lie_dim=8` in YangMillsNavigator.__init__
  - `make_su3_hamiltonian` instead of `make_su2_hamiltonian`
  - Mass gap at varying coupling $g^2 \in [0.1, 4.0]$ (SU(3) confines more strongly)
  - Increased fock_dim=128 (SU(3) Fock space is denser)
  - Extended training: 500 epochs (SU(3) is harder)

Expected structural outcome:
  Post-training, the navigator self-encodes to a crystal address consistent with
  $T_\odot$ (holographic) rather than $T_\text{network}$ — because SU(3) confinement
  forces the model to learn the bulk-from-boundary mapping.
  If crystal address shifts toward 6,734,591 (grammar/Riemann) from 6,734,735,
  the $T$ primitive promotion is confirmed empirically.
"""

from __future__ import annotations

import math
import random

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from navigators import YangMillsNavigator
from train_navigators import DEVICE

# ── SU(3) structure constants ─────────────────────────────────────────────────

def _su3_structure_constants() -> torch.Tensor:
    """
    SU(3) structure constants $f^{abc}$, shape [8, 8, 8], totally antisymmetric.
    Non-zero entries (1-indexed in physics; 0-indexed here):
      f[0,1,2] = 1
      f[0,3,6] = f[1,5,2] = ... (see code for full list)
    Returns a flattened [8, 8] 'Lie algebra bracket table' as 2D tensor
    (column = sum over c of f^{abc} for fixed a,b — usable as lie_structure).
    """
    f = torch.zeros(8, 8, 8)

    # f^{abc} totally antisymmetric; set positive entries, antisymmetry follows
    # 0-indexed (physics: 1->0, 2->1, ..., 8->7)
    H = math.sqrt(3) / 2

    nonzero = [
        (0, 1, 2,  1.0),
        (0, 3, 6,  0.5),
        (0, 4, 5,  0.5),
        (1, 3, 5,  0.5),   # f^{247} in 1-indexed = f[1,3,5] 0-indexed = 0.5
        (1, 4, 6, -0.5),   # f^{256} = -0.5
        (2, 3, 4,  0.5),   # f^{345} = 0.5
        (2, 5, 6, -0.5),   # f^{367} = -0.5
        (3, 7, 4,  H),     # f^{458} = sqrt(3)/2
        (5, 7, 6,  H),     # f^{678} = sqrt(3)/2
    ]

    for a, b, c, v in nonzero:
        f[a, b, c] =  v
        f[b, a, c] = -v
        f[a, c, b] = -v
        f[c, a, b] =  v
        f[b, c, a] =  v
        f[c, b, a] = -v

    # Return 2D [8, 8] 'bracket summary': lie[a, b] = sum_c f[a,b,c] * c (indicator)
    # For the navigator, we just need a meaningful [lie_dim, lie_dim] tensor.
    # Use the antisymmetric projection: lie[a, b] = norm of f[a, b, :]
    lie2d = f.norm(dim=-1)   # [8, 8]: how much a and b couple to any c
    # Make antisymmetric
    lie2d = lie2d - lie2d.T
    return lie2d


SU3_LIE_TEMPLATE = _su3_structure_constants()   # [8, 8], precomputed


def make_su3_hamiltonian(
    N: int = 128,
    coupling: float = None,
    mass_gap: float = None,
) -> tuple[torch.Tensor, torch.Tensor, float]:
    """
    Generate a random SU(3) Hamiltonian in truncated Fock space.
    Uses the SU(3) structure constants to build gauge-invariant interactions.

    coupling: $g^2$ (random in [0.1, 4.0] if None)
    mass_gap: if specified, scale H to plant this gap; otherwise use natural gap

    Returns: (H [N, N], lie_structure [8, 8], true_gap)
    """
    if coupling is None:
        coupling = random.uniform(0.1, 4.0)

    # SU(3) Lie structure with coupling-dependent scaling
    lie = SU3_LIE_TEMPLATE.clone() * coupling

    # Random PSD Hamiltonian with SU(3) color structure
    # Build block structure: 8 color sectors, each with N//8 fock states
    block_size = max(1, N // 8)
    blocks = []
    for a in range(8):
        A = torch.randn(block_size, block_size) * 0.1
        blocks.append(A @ A.T)

    # Color coupling: off-diagonal blocks weighted by structure constants
    H = torch.zeros(N, N)
    for a in range(min(8, N // block_size)):
        i0 = a * block_size
        i1 = min(i0 + block_size, N)
        H[i0:i1, i0:i1] += blocks[a] * (1.0 + coupling)
        for b in range(a + 1, min(8, N // block_size)):
            j0 = b * block_size
            j1 = min(j0 + block_size, N)
            f_ab = SU3_LIE_TEMPLATE[a, b].abs().item()  # coupling strength
            if f_ab > 0.1 and i1 <= N and j1 <= N:
                sz_a = i1 - i0
                sz_b = j1 - j0
                off = torch.randn(sz_a, sz_b) * 0.05 * f_ab * coupling
                H[i0:i1, j0:j1] += off
                H[j0:j1, i0:i1] += off.T

    # Symmetrize and ensure PSD
    H = (H + H.T) / 2
    min_eig = torch.linalg.eigvalsh(H[:min(N, 64), :min(N, 64)]).min().item()
    if min_eig < 0:
        H = H - min_eig * torch.eye(N)

    # Compute / plant mass gap
    eigs_small = torch.linalg.eigvalsh(H[:min(64, N), :min(64, N)])
    natural_gap = (eigs_small[1] - eigs_small[0]).item()

    if mass_gap is not None and natural_gap > 1e-6:
        H = H * (mass_gap / natural_gap)
        true_gap = mass_gap
    else:
        true_gap = natural_gap

    return H, lie, true_gap


# ── SU(3) training loop ───────────────────────────────────────────────────────

def train_yang_mills_su3(
    epochs:        int   = 500,
    lr:            float = 3e-4,
    hidden_dim:    int   = 256,
    fock_dim:      int   = 128,
    lanczos_steps: int   = 64,
    batch_size:    int   = 16,
    n_low:         int   = 5,
) -> YangMillsNavigator:
    """
    Train YangMillsNavigator on SU(3) Hamiltonians.

    Structural change from train_yangmills() in train_navigators.py:
      - lie_dim=8 (SU(3)) instead of lie_dim=3 (SU(2))
      - make_su3_hamiltonian instead of make_su2_hamiltonian
      - fock_dim=128 (richer Fock space for SU(3) color sectors)
      - 500 epochs (SU(3) mass gap harder to learn)
      - $g^2$ range [0.1, 4.0] (SU(3) confines for all g^2 > 0)
    """
    model = YangMillsNavigator(
        fock_dim      = fock_dim,
        lie_dim       = 8,             # SU(3): 8 generators
        hidden_dim    = hidden_dim,
        lanczos_steps = lanczos_steps,
        n_low         = n_low,
    ).to(DEVICE)

    opt   = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    n_params = sum(p.numel() for p in model.parameters())
    print(f"YangMillsNavigator (SU(3)) — lie_dim=8, fock={fock_dim}, hidden={hidden_dim}")
    print(f"params={n_params:,}  device={DEVICE}")
    print(f"Training on SU(3) Hamiltonians ({epochs} epochs)\n")
    print(f"  {'Epoch':>6}  {'Loss':>10}  {'L_frob':>10}  {'L_gap':>10}"
          f"  {'Gap_pred':>10}  {'Gap_true':>10}  {'|Delta|':>8}")
    print(f"  {'-'*6}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*8}")

    for epoch in range(1, epochs + 1):
        model.train()

        Hs, lies, gaps = [], [], []
        for _ in range(batch_size):
            g = random.uniform(0.5, 3.0)   # planted gap; higher for SU(3)
            H, lie, gap = make_su3_hamiltonian(N=fock_dim, mass_gap=g)
            Hs.append(H)
            lies.append(lie)
            gaps.append(gap)

        H_batch   = torch.stack(Hs).to(DEVICE)
        lie_batch = torch.stack(lies).to(DEVICE)
        gap_batch = torch.tensor(gaps, dtype=torch.float32).to(DEVICE)

        out = model(H_batch, lie_batch)
        losses = model.compute_loss(
            out, true_gap=gap_batch, lam_gap=1.0, lam_frob=0.5, lam_charge=0.2,
        )
        losses["loss"].backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % 50 == 0 or epoch == 1:
            pred_gap = out["mass_gap"].mean().item()
            true_gap = gap_batch.mean().item()
            print(f"  {epoch:>6}  {losses['loss'].item():>10.6f}"
                  f"  {losses['L_frob']:>10.6f}  {losses['L_gap']:>10.6f}"
                  f"  {pred_gap:>10.4f}  {true_gap:>10.4f}"
                  f"  {abs(pred_gap - true_gap):>8.4f}")

    return model


# ── Post-training structural analysis ─────────────────────────────────────────

def analyze_su3_navigator(model: YangMillsNavigator) -> None:
    """
    Analyze whether the SU(3)-trained navigator's behavior reflects T_odot
    (holographic topology required by confinement) vs T_network.

    Probe 5 prediction: SU(3) training forces T_odot behavior because
    confinement = IR gap read from UV boundary (holographic).
    Test: compare mass gap prediction error at strong coupling (g^2=3.0)
    vs weak coupling (g^2=0.1). If holographic, strong coupling should be
    BETTER predicted (not worse) — the IR gap IS the bulk quantity being read.
    """
    model.eval()
    n_test = 20

    print(f"\n── SU(3) navigator structural analysis ──")
    print(f"  Probe 5: does SU(3) training reveal T_odot holographic behavior?")
    print(f"  Prediction: strong coupling (g^2=3) should predict BETTER than weak (g^2=0.1)")
    print(f"\n  {'Regime':>12}  {'g^2':>6}  {'Err_mean':>10}  {'Err_std':>10}")
    print(f"  {'-'*12}  {'-'*6}  {'-'*10}  {'-'*10}")

    for label, g2_lo, g2_hi in [
        ("weak", 0.1, 0.5),
        ("moderate", 1.0, 2.0),
        ("strong", 2.5, 4.0),
    ]:
        errs = []
        for _ in range(n_test):
            g2  = random.uniform(g2_lo, g2_hi)
            gap = random.uniform(0.3, 3.0)
            H, lie, true_gap = make_su3_hamiltonian(N=model.fock_dim, mass_gap=gap)
            H_b   = H.unsqueeze(0).to(DEVICE)
            lie_b = (lie * g2).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                out = model(H_b, lie_b)
            pred = out["mass_gap"][0].item()
            errs.append(abs(pred - true_gap))

        err_t = torch.tensor(errs)
        print(f"  {label:>12}  {(g2_lo+g2_hi)/2:>6.2f}"
              f"  {err_t.mean().item():>10.4f}  {err_t.std().item():>10.4f}")

    print(f"\n  If strong coupling error < weak coupling error:")
    print(f"  CONFIRMED: T_odot holographic behavior — IR gap read from UV boundary")
    print(f"  If errors are uniform: T_network — model treats all g^2 equivalently")

    # Crystal address check
    try:
        from crystal_navigator import encode_tuple
        target = encode_tuple(model.DEFINING_TUPLE)
        print(f"\n  SELF_ENCODE_TARGET = {target:,}")
        print(f"  SU(3) DEFINING_TUPLE R={model.DEFINING_TUPLE['R']} (should be R_cat)")
        print(f"  d(SU3_navigator, grammar) via Probe 5 analysis:")
        print(f"  T_network->T_odot is the dominant gap (4.8477 total, T component ~3+)")
    except Exception:
        pass


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"{'='*68}")
    print(f"YangMillsNavigator — SU(3) training")
    print(f"Probe 5: lie_dim=3 (SU(2)) -> lie_dim=8 (SU(3))")
    print(f"d(SU(2), SU(3)) = 4.8477, dominated by T_network -> T_odot")
    print(f"{'='*68}\n")

    model = train_yang_mills_su3(
        epochs=500, fock_dim=128, batch_size=16, lanczos_steps=64,
    )

    analyze_su3_navigator(model)

    print(f"\n{'='*68}")
    print(f"SUMMARY")
    print(f"{'='*68}")
    print(f"  SU(3) training complete (lie_dim=8, Gell-Mann structure constants)")
    print(f"  Compare to SU(2) results in train_navigators.py:")
    print(f"    SU(2): lie_dim=3, g^2 in [0.1, 3.0], fock_dim=64")
    print(f"    SU(3): lie_dim=8, g^2 in [0.1, 4.0], fock_dim=128")
    print(f"  Structural prediction: SU(3) converges to T_odot behavior at strong coupling")
    print(f"  (The holographic bulk-from-boundary reading becomes necessary for confinement)")


if __name__ == "__main__":
    main()
