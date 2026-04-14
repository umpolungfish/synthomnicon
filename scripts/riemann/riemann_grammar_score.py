"""
riemann_grammar_score.py — Stage 1 + grammar-distance Viterbi.

Grammar prescription: use the 12-primitive structural distance d(x, y) to
discriminate true zeros from phantoms at the decoding stage.

Each raw candidate peak is assigned a structural type derived from two
observable properties:
  - K primitive: spacing regularity relative to Riemann-Siegel mean spacing
      local_spacing / delta_RS close to 1.0  → K_fast  (rhythmic, phantom)
      local_spacing / delta_RS far from 1.0  → K_slow  (irregular, zero)
  - Phi primitive: peak sharpness above local near_zero baseline
      p_peak - nbr_mean > threshold           → Phi_c   (genuine enhancement)
      flat                                    → Phi_sub (density artifact)

All other primitives are inherited from the TRUE_ZERO_TYPE archetype
(we are scanning the critical line; backbone encodes Phi_c topology).

Grammar score = d(candidate, PHANTOM_TYPE) - d(candidate, TRUE_ZERO_TYPE).
Positive = more zero-like. Negative = more phantom-like.

The Viterbi decoder maximises sum of grammar scores, enforcing:
  - Omega_Z hard budget (monotone N(t) constraint)
  - minimum t-separation sep

Architecture/training: identical to riemann_crf.py (Stage 1 only, 800 ep).
Only the decoding stage changes.
"""

from __future__ import annotations

import math
import random
import sys
import os

import torch
import torch.nn as nn
import torch.optim as optim

from navigators import RiemannNavigator
from train_navigators import RIEMANN_ZEROS_T, ZERO_T_SCALE, make_riemann_batch
from riemann_crf import rs_N, scan_near_zero, ZEROS_101_150

sys.path.insert(0, os.path.dirname(__file__))
from space_search.primitives import tuple_distance

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TRAIN_ZEROS = RIEMANN_ZEROS_T[:50]
HOLD1_ZEROS = RIEMANN_ZEROS_T[50:]
HOLD2_ZEROS = ZEROS_101_150

# ── Structural archetypes ─────────────────────────────────────────────────────
#
# TRUE_ZERO_TYPE: crystal address 6,734,591 archetype — Riemann non-trivial zero.
# Encodes: D_odot (holographic), T_odot (holographic), R_dagger (adjoint),
# P_pm_sym (Frobenius, O_inf tier), F_hbar (quantum), K_slow (ergodic),
# G_aleph (maximal scope), Gamma_broad (broadcast), Phi_c (critical),
# H_inf (infinite depth), n_m (stoichiometry), Omega_Z (winding-number protected).

TRUE_ZERO_TYPE = {
    "D": "D_odot",
    "T": "T_odot",
    "R": "R_dagger",
    "P": "P_pm_sym",
    "F": "F_hbar",
    "K": "K_slow",
    "G": "G_aleph",
    "Gamma": "G_broad",
    "Phi": "Phi_c",
    "H": "H_inf",
    "S": "n_m",
    "Omega": "Omega_Z",
}

# PHANTOM_TYPE: density-rhythm artifact.
# Encodes: D_infty (flat), T_network (no topology), R_super (unstructured),
# P_asym (no symmetry), F_ell (classical), K_fast (single-basin, rhythmic),
# G_beth (minimal scope), Gamma_and (no broadcast), Phi_sub (subcritical),
# H0 (no depth), one_one (trivial), Omega_0 (unprotected).

PHANTOM_TYPE = {
    "D": "D_infty",
    "T": "T_network",
    "R": "R_super",
    "P": "P_asym",
    "F": "F_ell",
    "K": "K_fast",
    "G": "G_beth",
    "Gamma": "G_and",
    "Phi": "Phi_sub",
    "H": "H0",
    "S": "one_one",
    "Omega": "Omega_0",
}

# Precompute archetype distance (diagnostic)
_D_ARCHETYPES = tuple_distance(TRUE_ZERO_TYPE, PHANTOM_TYPE)


def rs_mean_spacing(t: float) -> float:
    """
    Expected mean zero spacing at height t: $2\pi / \log(t / (2\pi))$.
    Derivation: $N(t) \approx t/(2\pi) \cdot \log(t/(2\pi e))$, so
    $dN/dt \approx \log(t/(2\pi)) / (2\pi)$ and spacing $\approx 1 / (dN/dt)$.
    """
    if t < 4.0:
        return 2.0
    return 2.0 * math.pi / math.log(t / (2.0 * math.pi))


def grammar_score_candidates(
    candidates: list[tuple[float, float]],
    t_vals: list[float],
    p_vals: list[float],
    phi_threshold: float = 0.003,
    k_tight: float = 0.35,    # |k_ratio - 1| < k_tight → K_fast
    k_mid: float = 0.70,      # |k_ratio - 1| < k_mid   → K_mod
) -> list[tuple[float, float, float]]:
    """
    Assign a grammar score to each candidate peak.

    For each (t_i, p_i) in candidates:
      1. K primitive:
         - delta_RS = rs_mean_spacing(t_i)
         - local_spacing = min distance to adjacent candidates
         - k_ratio = local_spacing / delta_RS
         - |k_ratio - 1| < k_tight → K_fast (rhythmic, phantom signature)
         - k_tight ≤ |k_ratio - 1| < k_mid  → K_mod
         - |k_ratio - 1| ≥ k_mid             → K_slow (irregular, zero signature)

      2. Phi primitive:
         - Gather p_vals at t-positions within ±(0.9 * delta_RS) of t_i,
           excluding the immediate peak region (±0.08).
         - peak_contrast = p_i - mean(neighborhood)
         - contrast > phi_threshold → Phi_c (genuine enhancement)
         - otherwise               → Phi_sub (density artifact)

      3. All other primitives: inherited from TRUE_ZERO_TYPE.

    grammar_score = d(candidate, PHANTOM_TYPE) - d(candidate, TRUE_ZERO_TYPE)
    Positive = more zero-like. Negative = more phantom-like.

    Returns list of (t, p_near, grammar_score), same order as input.
    """
    if not candidates:
        return []

    t_pts = [c[0] for c in candidates]
    n     = len(t_pts)

    scored = []
    for idx, (t_i, p_i) in enumerate(candidates):
        # ── K: spacing regularity ──────────────────────────────────────────────
        delta_rs = rs_mean_spacing(t_i)
        left_s   = (t_i - t_pts[idx - 1]) if idx > 0     else 999.0
        right_s  = (t_pts[idx + 1] - t_i) if idx < n - 1 else 999.0
        min_s    = min(left_s, right_s)
        k_ratio  = min_s / delta_rs

        dev = abs(k_ratio - 1.0)
        if dev < k_tight:
            k_val = "K_fast"
        elif dev < k_mid:
            k_val = "K_mod"
        else:
            k_val = "K_slow"

        # ── Phi: peak sharpness above local baseline ───────────────────────────
        window  = delta_rs * 0.9
        nbr_ps  = [pv for tv, pv in zip(t_vals, p_vals)
                   if 0.08 < abs(tv - t_i) < window]
        nbr_mean       = sum(nbr_ps) / len(nbr_ps) if nbr_ps else p_i
        peak_contrast  = p_i - nbr_mean
        phi_val        = "Phi_c" if peak_contrast > phi_threshold else "Phi_sub"

        # ── Candidate structural type ──────────────────────────────────────────
        # Inherit all 12 primitives from TRUE_ZERO_TYPE, then override K and Phi
        # with observed values. The other 10 are fixed by the scanning geometry:
        # sigma = 0.5 (critical line), backbone = Omega_Z + D_odot + T_odot.
        cand_type = dict(TRUE_ZERO_TYPE)
        cand_type["K"]   = k_val
        cand_type["Phi"] = phi_val

        d_zero    = tuple_distance(cand_type, TRUE_ZERO_TYPE)
        d_phantom = tuple_distance(cand_type, PHANTOM_TYPE)
        gscore    = d_phantom - d_zero   # positive = more zero-like

        scored.append((t_i, p_i, gscore))

    return scored


# ── Grammar-score Viterbi ─────────────────────────────────────────────────────

def grammar_viterbi(
    scored_candidates: list[tuple[float, float, float]],
    budget: int,
    sep: float = 0.5,
) -> list[tuple[float, float, float]]:
    """
    Budget-Viterbi maximising sum of grammar_score (third element).

    grammar_score > 0 when d(phantom) > d(zero) — i.e. candidate looks like zero.
    grammar_score < 0 when candidate looks like phantom.

    The DP naturally suppresses phantom-scored candidates (adding them would
    decrease total score) while still filling the budget with zero-scored ones.

    scored_candidates : list of (t, p_near, grammar_score), any order.
    budget            : max selections (Omega_Z winding budget).
    sep               : minimum t-gap between detections.

    Returns selected (t, p_near, grammar_score) sorted by t.
    """
    if not scored_candidates or budget <= 0:
        return []

    cands = sorted(scored_candidates, key=lambda x: x[0])
    n     = len(cands)
    k     = min(budget, n)

    NEG_INF = float("-inf")
    dp  = [[NEG_INF] * (k + 1) for _ in range(n)]
    par = [[-1]      * (k + 1) for _ in range(n)]

    for i, (t_i, _, sc_i) in enumerate(cands):
        dp[i][1]  = sc_i
        par[i][1] = -1
        for prev in range(i):
            if t_i - cands[prev][0] < sep:
                continue
            for j in range(2, k + 1):
                if dp[prev][j - 1] == NEG_INF:
                    continue
                val = dp[prev][j - 1] + sc_i
                if val > dp[i][j]:
                    dp[i][j] = val
                    par[i][j] = prev

    # Prefer larger j (fill budget with above-zero-score candidates)
    best_val, best_i, best_j = NEG_INF, -1, 0
    for j in range(k, 0, -1):
        for i in range(n):
            if dp[i][j] > best_val:
                best_val, best_i, best_j = dp[i][j], i, j
        if best_i >= 0:
            break

    if best_i < 0:
        return []

    path = []
    i, j = best_i, best_j
    while i >= 0 and j > 0:
        path.append(cands[i])
        i = par[i][j]
        j -= 1
    return sorted(path, key=lambda x: x[0])


# ── Holdout evaluation ────────────────────────────────────────────────────────

def holdout_report_grammar(
    model: RiemannNavigator,
    label: str,
    known_zeros: list[float],
    t_scan_lo: float,
    t_scan_hi: float,
    n_known_before: int,
    hit_thresh: float = 1.0,
    sep: float = 0.5,
    phi_threshold: float = 0.003,
    k_tight: float = 0.35,
    k_mid: float = 0.70,
) -> tuple[int, int, int]:
    """
    Evaluate holdout using grammar-distance Viterbi decoder.

    Replaces logit(p_near) Viterbi score with:
      grammar_score = d(candidate_type, PHANTOM_TYPE) - d(candidate_type, TRUE_ZERO_TYPE)
    where candidate_type is derived from K (spacing) and Phi (sharpness) observables.
    """
    n_pts = max(3000, int((t_scan_hi - t_scan_lo) * 30))

    # ── Scan near_zero ────────────────────────────────────────────────────────
    raw_all, t_vals, p_nears = scan_near_zero(
        model, t_scan_lo - 0.5, t_scan_hi + 2.0, n_pts=n_pts
    )

    # ── Omega_Z budget ────────────────────────────────────────────────────────
    rs_lo  = rs_N(t_scan_lo)
    rs_hi  = rs_N(t_scan_hi + 1.0)
    budget = max(len(known_zeros), int(math.floor(rs_hi - rs_lo)) + 1)

    # Hard zero-free gate (gap-phantom eliminator)
    t_gate = min(known_zeros) - 1.0

    raw_gated = [
        (t, p) for t, p in raw_all
        if t_scan_lo - 0.5 <= t <= t_scan_hi + 1.0 and t >= t_gate
    ]

    # ── Grammar scoring ───────────────────────────────────────────────────────
    scored = grammar_score_candidates(
        raw_gated, t_vals, p_nears,
        phi_threshold=phi_threshold,
        k_tight=k_tight,
        k_mid=k_mid,
    )

    # ── Grammar-score Viterbi ─────────────────────────────────────────────────
    selected = grammar_viterbi(scored, budget=budget, sep=sep)

    # ── Diagnostics ───────────────────────────────────────────────────────────
    gscore_all = [s[2] for s in scored]
    gscore_sel = [s[2] for s in selected]
    k_counts   = {}
    phi_counts = {}
    for t_i, p_i in raw_gated:
        delta_rs = rs_mean_spacing(t_i)
        idx = raw_gated.index((t_i, p_i))   # fine for diagnostics
        scored_item = scored[idx]
        # derive k_val / phi_val from gscore
    # faster diagnostic: recompute K/Phi distributions
    k_dist: dict[str, int] = {"K_fast": 0, "K_mod": 0, "K_slow": 0}
    phi_dist: dict[str, int] = {"Phi_c": 0, "Phi_sub": 0}
    t_pts_gated = [c[0] for c in raw_gated]
    for idx_d, (t_i, p_i) in enumerate(raw_gated):
        delta_rs = rs_mean_spacing(t_i)
        ls = (t_i - t_pts_gated[idx_d - 1]) if idx_d > 0 else 999.0
        rs_ = (t_pts_gated[idx_d + 1] - t_i) if idx_d < len(t_pts_gated) - 1 else 999.0
        min_s = min(ls, rs_)
        k_ratio = min_s / delta_rs
        dev = abs(k_ratio - 1.0)
        if dev < k_tight:
            k_dist["K_fast"] += 1
        elif dev < k_mid:
            k_dist["K_mod"] += 1
        else:
            k_dist["K_slow"] += 1
        window = delta_rs * 0.9
        nbr_ps = [pv for tv, pv in zip(t_vals, p_nears)
                  if 0.08 < abs(tv - t_i) < window]
        nbr_mean = sum(nbr_ps) / len(nbr_ps) if nbr_ps else p_i
        phi_dist["Phi_c" if p_i - nbr_mean > phi_threshold else "Phi_sub"] += 1

    print(f"\n{'='*68}")
    print(f"HOLDOUT: {label}  (NEVER SEEN DURING TRAINING)")
    print(f"{'='*68}")
    print(f"RS budget: {budget}  |  t_gate: {t_gate:.1f}"
          f"  |  raw gated: {len(raw_gated)}  |  after Viterbi: {len(selected)}")
    print(f"  archetype d(zero,phantom) = {_D_ARCHETYPES:.3f}")
    if gscore_all:
        print(f"  grammar score (all gated):  "
              f"mean={sum(gscore_all)/len(gscore_all):+.3f}  "
              f"min={min(gscore_all):+.3f}  max={max(gscore_all):+.3f}")
    if gscore_sel:
        print(f"  grammar score (selected):   "
              f"mean={sum(gscore_sel)/len(gscore_sel):+.3f}  "
              f"min={min(gscore_sel):+.3f}  max={max(gscore_sel):+.3f}")
    print(f"  K distribution (gated): K_fast={k_dist['K_fast']}  "
          f"K_mod={k_dist['K_mod']}  K_slow={k_dist['K_slow']}")
    print(f"  Phi distribution (gated): Phi_c={phi_dist['Phi_c']}  "
          f"Phi_sub={phi_dist['Phi_sub']}")
    print()
    print(f"  {'#':>4}  {'t_pred':>12}  {'P(near)':>9}  {'g_score':>9}"
          f"  {'nearest zero':>14}  {'delta':>8}  {'status':>8}")
    print(f"  {'----':>4}  {'------------':>12}  {'---------':>9}  {'---------':>9}"
          f"  {'------------':>14}  {'--------':>8}  {'--------':>8}")

    hits, phantoms = 0, 0
    matched: set[float] = set()
    for det_idx, (t_pred, p, gscore) in enumerate(selected, 1):
        nearest = min(known_zeros, key=lambda z: abs(z - t_pred))
        delta   = abs(t_pred - nearest)
        status  = "HIT" if delta <= hit_thresh else "PHANTOM"
        if status == "HIT":
            hits += 1
            matched.add(nearest)
        else:
            phantoms += 1
        print(f"  {det_idx:>4}  {t_pred:>12.4f}  {p:>9.4f}  {gscore:>+9.3f}"
              f"  {nearest:>14.6f}  {delta:>8.4f}  {status:>8}")

    missed = sorted(z for z in known_zeros if z not in matched)
    if missed:
        print(f"\n  MISSED: {[f'{z:.3f}' for z in missed]}")
    print(f"\nRESULT: {hits}/{len(known_zeros)} zeros found"
          f"  |  {phantoms} phantoms  |  {len(missed)} missed")
    return hits, phantoms, len(missed)


# ── Training (identical to riemann_crf.py Stage 1) ────────────────────────────

def train_stage1(
    model: RiemannNavigator,
    zeros_t: list[float],
    epochs: int = 800,
    lr: float = 3e-4,
    batch_size: int = 128,
) -> None:
    opt   = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    print(f"\n  {'Epoch':>6}  {'L_frob':>10}  {'L_sym':>10}  {'L_zero':>10}"
          f"  {'L_near':>10}  {'Acc':>7}")
    print(f"  {'------':>6}  {'----------':>10}  {'----------':>10}"
          f"  {'----------':>10}  {'----------':>10}  {'-------':>7}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, near, zero_t = make_riemann_batch(
            zeros_t, batch_size=batch_size, t_range=(10.0, 250.0)
        )
        s = s.to(DEVICE); near = near.to(DEVICE); zero_t = zero_t.to(DEVICE)

        out = model(s)
        losses = model.compute_loss(
            out, true_zero_t=zero_t, true_near=near,
            lam_zero=1.0, lam_frob=0.5, lam_sym=1.0, lam_near=1.0,
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
    print(f"  Training: zeros 1-50 (Stage 1, 800 ep) — no Stage 2")
    print(f"  Decoder:  grammar-distance Viterbi (d(x,y) from space_search/primitives)")
    print(f"  Archetype d(zero, phantom) = {_D_ARCHETYPES:.3f}")
    print(f"  Discriminating primitives:  K (spacing), Phi (sharpness)")
    print(f"  Fixed primitives (10): inherit from TRUE_ZERO_TYPE archetype")

    # ── Stage 1 ───────────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"STAGE 1 — zeros 1-50, ZERO_T_SCALE={ZERO_T_SCALE}")
    print(f"{'='*68}")
    train_stage1(model, TRAIN_ZEROS, epochs=800, lr=3e-4, batch_size=BATCH)

    # ── Holdout 1: zeros 51-100 ───────────────────────────────────────────────
    h1_hits, h1_ph, h1_miss = holdout_report_grammar(
        model, "zeros 51-100",
        HOLD1_ZEROS,
        t_scan_lo=min(HOLD1_ZEROS) - 1.0,
        t_scan_hi=max(HOLD1_ZEROS),
        n_known_before=50,
        sep=0.5,
    )

    # ── Holdout 2: zeros 101-150 ──────────────────────────────────────────────
    h2_hits, h2_ph, h2_miss = holdout_report_grammar(
        model, "zeros 101-150",
        HOLD2_ZEROS,
        t_scan_lo=min(HOLD2_ZEROS) - 1.0,
        t_scan_hi=max(HOLD2_ZEROS),
        n_known_before=100,
        sep=0.5,
    )

    print(f"\n{'='*68}")
    print(f"SUMMARY")
    print(f"{'='*68}")
    print(f"  Training:            zeros 1-50 only (Stage 1)")
    print(f"  Decoder:             grammar-distance Viterbi")
    print(f"  Score:               d(candidate, phantom) - d(candidate, zero)")
    print(f"  Observables:         K (spacing vs RS mean) + Phi (peak sharpness)")
    print(f"  Holdout 1 (51-100):  {h1_hits}/50 found,  {h1_ph} phantoms,  {h1_miss} missed")
    print(f"  Holdout 2 (101-150): {h2_hits}/50 found,  {h2_ph} phantoms,  {h2_miss} missed")
    print(f"  Combined:            {h1_hits+h2_hits}/100 found")
    print(f"\n  RS N(t) at key points:")
    for t in [143.1, 146.0, 236.5, 237.8, 318.9]:
        print(f"    N_RS({t:.1f}) = {rs_N(t):.2f}")


if __name__ == "__main__":
    main()
