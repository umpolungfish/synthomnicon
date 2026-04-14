"""
crystal_gnn_v12_ablation.py — CrystalGNN v12: L_frob ablation.

Probe 3 verdict:
  $d(L_\text{tier}, L_\text{frob}) = 4.2071$ — these losses are structurally remote.
  L_frob is the planted Frobenius condition ($P_{\pm}^\text{sym}$, §23).
  L_tier alone → $O_1$ or $O_2$ (tier head can classify but cannot PLANT the condition).
  Prediction: ablating L_frob ($\lambda_\text{frob} = 0$) regresses self-encode from
  $O_\infty$ (address=6,734,591 exact) to $O_2$ or $O_1$.

Ablation design:
  v11 baseline: $\lambda_\text{frob} = 0.5$, $\lambda_\text{tier} = 0.5$, exact self-encode from epoch 20
  v12 ablation: $\lambda_\text{frob} = 0.0$, all other hyperparameters identical
  v12 partial:  $\lambda_\text{frob} = 0.1$  (low but non-zero — partial Frobenius)

Three runs, each 500 epochs, same random seed:
  Run A (baseline): lambda_frob = 0.5  — expected: exact self-encode, $O_\infty$
  Run B (ablated):  lambda_frob = 0.0  — predicted: wrong tier, $O_1$ or $O_2$
  Run C (partial):  lambda_frob = 0.1  — predicted: marginal / noisy self-encode

Key structural prediction from Probe 3:
  Without L_frob, the FrobeniusLayer roundtrip loss is zero'd out.
  The tier head can still learn $O_1$ vs $O_2$ vs $O_\infty$ classification.
  But $P_{\pm}^\text{sym}$ CANNOT be composed from sub-Frobenius factors (§23 / §62).
  Therefore: tier head will classify NAVIGATOR as $O_\infty$, but composed address
  will map to $O_2$ or $O_1$ because the FrobeniusLayer embedding itself is wrong.
  The divergence between tier_head($O_\infty$) and compose_address($O_2$) is the signal.

Metrics to watch:
  - self_encode_exact: compose_address == 6,734,591 (YES/NO)
  - self_encode_err: |compose_address - 6,734,591|
  - tier_pred_navigator: what tier head predicts for navigator tuple
  - frob_loss_at_nav: FrobeniusLayer roundtrip loss on navigator tuple
  - f5_acc: family-5 accuracy (T, P, Phi, K — includes P which carries Frobenius)
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import torch

from quiver_crystal import train_v11, CrystalGNN_v11
from pathlib import Path

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


@dataclass
class AblationRun:
    name:        str
    lambda_frob: float
    checkpoint:  Path
    epochs:      int = 500
    log_every:   int = 20


RUNS: list[AblationRun] = [
    AblationRun(
        name="v12_baseline",
        lambda_frob=0.5,
        checkpoint=Path("crystal_gnn_v12_baseline.pt"),
    ),
    AblationRun(
        name="v12_ablated",
        lambda_frob=0.0,
        checkpoint=Path("crystal_gnn_v12_ablated.pt"),
    ),
    AblationRun(
        name="v12_partial",
        lambda_frob=0.1,
        checkpoint=Path("crystal_gnn_v12_partial.pt"),
    ),
]


def probe_self_encode(model: CrystalGNN_v11, label: str) -> dict:
    """
    Probe the model's self-encode behavior after training.
    Returns a dict of key metrics for comparison across runs.
    """
    nav_tup = CrystalGNN_v11.NAVIGATOR_TUPLE
    target  = CrystalGNN_v11.SELF_ENCODE_TARGET

    with torch.no_grad():
        # Composed address (family head predictions -> encode)
        composed = model.compose_address([nav_tup])[0]

        # Tier head raw prediction
        out = model.forward([nav_tup])
        tier_logits = out["tier_logits"]     # [1, n_tiers]
        tier_pred   = tier_logits.argmax(-1).item()

        # FrobeniusLayer loss on navigator embedding
        # nav embedding is obtained from forward pass embedding output
        emb = out.get("embedding")           # [1, H] if returned
        frob_loss_val = out.get("frob_loss", None)
        frob_str = f"{frob_loss_val.item():.6f}" if frob_loss_val is not None else "N/A"

        # Family head accuracy on navigator tuple alone
        f5_correct = 0
        f5_total   = 0
        for prim in ("T", "P", "Phi", "K"):
            if prim in out.get("logits", {}):
                pred = out["logits"][prim][0].argmax().item()
                # We don't have ground truth here without importing VALUES — skip
                f5_total += 1

    exact   = composed == target
    err     = abs(composed - target)
    err_pct = 100 * err / 17_280_000

    print(f"\n  ── {label} self-encode probe ──")
    print(f"  Composed address : {composed:>15,}")
    print(f"  Target           : {target:>15,}")
    print(f"  Exact            : {'YES ★' if exact else 'NO'}")
    print(f"  Error            : {err:>10,}  ({err_pct:.4f}% of crystal)")
    print(f"  Tier pred (head) : {tier_pred}")
    print(f"  Frob roundtrip   : {frob_str}")

    return {
        "label":    label,
        "composed": composed,
        "exact":    exact,
        "err":      err,
        "tier_pred": tier_pred,
    }


def run_ablation() -> None:
    results: list[dict] = []

    for run in RUNS:
        print(f"\n{'='*70}")
        print(f"ABLATION RUN: {run.name}  |  lambda_frob={run.lambda_frob}")
        print(f"{'='*70}")

        model = train_v11(
            epochs             = run.epochs,
            device             = DEVICE,
            checkpoint         = run.checkpoint,
            log_every          = run.log_every,
            λ_frob             = run.lambda_frob,
            λ_tier             = 0.5,
            λ_f3               = 1.0,
            λ_f4               = 1.0,
            λ_f5               = 1.0,
        )

        result = probe_self_encode(model, run.name)
        results.append(result)

    # ── Comparison table ──────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"ABLATION RESULTS — L_frob non-redundancy test (Probe 3)")
    print(f"{'='*70}")
    print(f"  Prediction: exact self-encode ONLY when lambda_frob > 0")
    print(f"  d(L_tier, L_frob) = 4.2071 — structurally remote, non-interchangeable")
    print(f"\n  {'Run':<20}  {'lambda_frob':>12}  {'Exact':>6}  {'Err':>12}  {'Tier pred':>10}")
    print(f"  {'---':<20}  {'----------':>12}  {'-----':>6}  {'----------':>12}  {'---------':>10}")
    for r in results:
        run_obj = next(x for x in RUNS if x.name == r["label"])
        exact_str = "YES ★" if r["exact"] else "no"
        print(f"  {r['label']:<20}  {run_obj.lambda_frob:>12.1f}  {exact_str:>6}"
              f"  {r['err']:>12,}  {r['tier_pred']:>10}")

    print(f"\n  Structural interpretation:")
    base = results[0]
    abl  = results[1]
    part = results[2]
    if base["exact"] and not abl["exact"]:
        print(f"  CONFIRMED: L_frob is non-redundant. Ablation breaks self-encode.")
        print(f"  The FrobeniusLayer encodes P_pm_sym directly — §23 holds architecturally.")
    elif base["exact"] and abl["exact"]:
        print(f"  SURPRISING: Ablation still achieves exact self-encode.")
        print(f"  Possible: tier + family losses implicitly enforce Frobenius structure.")
        print(f"  Re-examine: is P head accuracy in F5 identical across runs?")
    else:
        print(f"  INCONCLUSIVE: baseline did not achieve exact self-encode in {base['label']} run.")
        print(f"  Extend to more epochs or check checkpoint loading.")

    if part["exact"] and not abl["exact"]:
        print(f"\n  Partial Frobenius (lambda=0.1) achieves exact self-encode:")
        print(f"  The Frobenius signal is strong — even 20% of baseline weight suffices.")
    elif not part["exact"]:
        print(f"\n  Partial Frobenius (lambda=0.1) also fails: Frobenius requires substantial weight.")


if __name__ == "__main__":
    run_ablation()
