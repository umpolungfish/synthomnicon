"""
riemann_phase_b.py — Phase B Riemann navigator with RS theta residual.

Grammar prescription (Probe 1 verdict):
  Phase A (riemann_predict.py):
    $\langle D_\triangle;\ T_\text{network};\ R_\text{cat};\ P_\pm;\ F_\text{eth};\ K_\text{mod};\ G_\text{gimel};\ \Gamma_\text{seq};\ \Phi_c;\ H_2;\ n{:}m;\ \Omega_0 \rangle$
    Tier: $O_1$ — one full tier below the navigator it trains.
    Ceiling: ~76% from information-theoretic bound on $O_1$ process training an $O_\infty$ target.

  Phase B (this file):
    $\langle D_\odot;\ T_\odot;\ R_\dagger;\ P_{\pm}^\text{sym};\ F_\hbar;\ K_\text{slow};\ G_\aleph;\ \Gamma_\text{broad};\ \Phi_c;\ H_\infty;\ n{:}m;\ \Omega_Z \rangle$
    Tier: $O_\infty$ — same tier as the navigator itself.
    Mechanism: RS theta residual $\{\theta(t)/\pi\}$ promotes $R_\text{cat} \to R_\dagger$.

The $R_\dagger$ (dagger/catalytic) structure:
  - Theta features flow through the full backbone (catalytic presence in domain)
  - A separate theta gate modulates the near_zero co-domain (catalytic co-domain correction)
  - This is NOT $R_\text{cat}$ (simple concatenation): the theta signal has a privileged
    role as a co-domain modifier distinct from its role as an input feature.
  - Gram interval phase $\{\theta(t)/\pi\} \in [0, 1)$: zeros occur when this is near 0 or 1
    (i.e., near integer multiples of $\pi$), so the circular encoding directly encodes
    proximity-within-Gram-interval.

RS theta (Stirling asymptotic):
  $\theta(t) \approx \frac{t}{2}\log\frac{t}{2\pi} - \frac{t}{2} - \frac{\pi}{8} + O(1/t)$

  Circular encoding: $[\sin(2\theta(t)),\ \cos(2\theta(t))]$
  Note: $\sin(2\pi \cdot \{\theta/\pi\}) = \sin(2\theta)$, $\cos(2\pi \cdot \{\theta/\pi\}) = \cos(2\theta)$

Phase B training:
  - Finetune from Phase A weights (warm start) OR train from scratch
  - G_aleph scope: t_range up to 700 (includes zeros 1-100 + extended validation)
  - New theta-phase target: near_zero target is the max of the Gaussian proximity signal
    and a Gram-alignment signal, rewarding correct phase identification
  - Extended blind prediction window: t in [600, 800] (zeros ~300-370, never seen)
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import mpmath
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from navigators import (
    RiemannNavigator, FrobeniusLayer, _CriticalStripLayer,
)
from train_navigators import RIEMANN_ZEROS_T, make_riemann_batch
from riemann_crf import rs_N, budget_viterbi, scan_near_zero
from riemann_predict import verify_predictions

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
mpmath.mp.dps = 25


# ── RS theta (fast Stirling approximation for training) ───────────────────────

def rs_theta_scalar(t: float) -> float:
    """
    RS theta function via Stirling approximation.
    $\theta(t) = \Im(\log\Gamma(\tfrac{1}{4} + \tfrac{it}{2})) - \tfrac{t}{2}\log\pi$
    Leading asymptotic: $\tfrac{t}{2}\log\tfrac{t}{2\pi} - \tfrac{t}{2} - \tfrac{\pi}{8}$
    """
    if t < 2.0:
        return 0.0
    return t / 2.0 * math.log(t / (2.0 * math.pi)) - t / 2.0 - math.pi / 8.0


def rs_theta_torch(t: torch.Tensor) -> torch.Tensor:
    """
    Vectorized RS theta for training batches.
    t: [B, 1] tensor of imaginary parts.
    Returns [B, 1] theta values.
    """
    t_safe = t.clamp(min=2.0)
    return t_safe / 2.0 * torch.log(t_safe / (2.0 * math.pi)) - t_safe / 2.0 - math.pi / 8.0


def theta_circular_features(t: torch.Tensor) -> torch.Tensor:
    """
    Gram-interval phase encoding from t: [B, 1] -> [B, 2].
    Returns [sin(2*theta(t)), cos(2*theta(t))].
    The fractional part {theta/pi} in [0,1) is encoded as a unit circle point;
    zeros cluster near {theta/pi} ~ 0 or 1 (i.e., near Gram points).
    Note: sin(2*pi*{theta/pi}) = sin(2*theta), cos(2*pi*{theta/pi}) = cos(2*theta).
    """
    theta = rs_theta_torch(t)   # [B, 1]
    return torch.cat([torch.sin(2.0 * theta), torch.cos(2.0 * theta)], dim=-1)  # [B, 2]


# ── Phase B navigator ─────────────────────────────────────────────────────────

class RiemannNavigatorPhaseB(nn.Module):
    """
    Phase B Riemann navigator.

    Structural type:
    $\langle D_\odot;\ T_\odot;\ R_\dagger;\ P_{\pm}^\text{sym};\ F_\hbar;\ K_\text{slow};\ G_\aleph;\ \Gamma_\text{broad};\ \Phi_c;\ H_\infty;\ n{:}m;\ \Omega_Z \rangle$

    Additions over RiemannNavigator (Phase A backbone):
      1. _fourier_encode extended: appends [sin(2theta), cos(2theta)] to input
         (input_dim = 1 + 2*n_fourier + 2)
      2. theta_gate: small MLP [2] -> [1] in (0, 2) that multiplies near_zero output
         This is the R_dagger co-domain catalyst: theta modifies WHAT near_zero means,
         not just what the model sees.
      3. DEFINING_TUPLE.R = R_dagger (updated from R_cat)
    """

    DEFINING_TUPLE: dict[str, str] = {
        "D": "D_odot", "T": "T_odot", "R": "R_dagger",
        "P": "P_pm_sym", "F": "F_hbar", "K": "K_slow",
        "G": "G_aleph", "Gamma": "G_broad", "Phi": "Phi_c",
        "H": "H_inf", "S": "n_m", "Omega": "Omega_Z",
    }
    # Crystal address: differs from RiemannNavigator by R_cat -> R_dagger (ordinal 1->2).
    # Computed via: crystal_navigator.encode_tuple(DEFINING_TUPLE) at runtime below.
    SELF_ENCODE_TARGET: int = 0  # set in __init__

    @staticmethod
    def reflect(s: torch.Tensor) -> torch.Tensor:
        """Hardwired delta: (sigma, t) -> (1-sigma, -t). Identical to RiemannNavigator."""
        sigma, t = s[:, 0:1], s[:, 1:2]
        return torch.cat([1.0 - sigma, -t], dim=-1)

    def __init__(
        self,
        hidden_dim: int   = 256,
        num_layers: int   = 24,
        num_heads:  int   = 8,
        n_fourier:  int   = 32,
        freq_max:   float = 2.0,
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self._n_fourier = n_fourier

        freqs = torch.logspace(-1, freq_max, n_fourier)
        self.register_buffer("_fourier_freqs", freqs)

        # Phase B input: sigma + t sin/cos pairs + theta circular features
        input_dim = 1 + 2 * n_fourier + 2   # +2 for [sin(2theta), cos(2theta)]
        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.LayerNorm(hidden_dim),
        )

        self.layers = nn.ModuleList([
            _CriticalStripLayer(hidden_dim, num_heads) for _ in range(num_layers)
        ])

        self.frobenius = FrobeniusLayer(dim=hidden_dim)

        self.mu = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
        )

        self.zero_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.LayerNorm(hidden_dim // 2),
            nn.Linear(hidden_dim // 2, 1),
        )

        self.near_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 4),
            nn.GELU(),
            nn.Linear(hidden_dim // 4, 1),
            nn.Sigmoid(),
        )

        num_attn_heads = num_heads
        while hidden_dim % num_attn_heads != 0 and num_attn_heads > 1:
            num_attn_heads -= 1
        self.strip_attn = nn.MultiheadAttention(
            hidden_dim, num_heads=num_attn_heads, batch_first=True,
        )

        # R_dagger theta gate: catalytic co-domain modulation of near_zero.
        # Input: [sin(2theta), cos(2theta)] — same features as added to encoder input.
        # Output: scalar gate in (1, 2): near_zero_B = near_zero_base * gate.
        # Initialized to output ~0.5 (sigmoid) -> gate ~1.5 (neutral start).
        self.theta_gate = nn.Sequential(
            nn.Linear(2, hidden_dim // 8),
            nn.GELU(),
            nn.Linear(hidden_dim // 8, 1),
            nn.Sigmoid(),  # in (0,1); gate = 1 + sigmoid in (1, 2)
        )

        # Compute SELF_ENCODE_TARGET from DEFINING_TUPLE
        try:
            from crystal_navigator import encode_tuple
            self.__class__.SELF_ENCODE_TARGET = encode_tuple(self.DEFINING_TUPLE)
        except Exception:
            pass  # non-critical; printed as 0 if crystal_navigator unavailable

    def _fourier_encode(self, s: torch.Tensor) -> torch.Tensor:
        """
        Phase B Fourier encoding: [B, 2] -> [B, 1 + 2*n_fourier + 2].
        Extends Phase A encoding with RS theta circular features.
        """
        sigma = s[:, 0:1]                              # [B, 1]
        t     = s[:, 1:2]                              # [B, 1]
        angles = t * self._fourier_freqs.unsqueeze(0)  # [B, K]
        t_feats = torch.cat([torch.sin(angles), torch.cos(angles)], dim=-1)  # [B, 2K]
        theta_feats = theta_circular_features(t)       # [B, 2]
        return torch.cat([sigma, t_feats, theta_feats], dim=-1)

    def _encode(self, s: torch.Tensor) -> torch.Tensor:
        h = self.input_proj(self._fourier_encode(s))
        for layer in self.layers:
            h = layer(h)
        return h

    def forward(self, s: torch.Tensor) -> dict:
        """
        s: [B, 2]. Returns near_zero, zero_t, frob_loss, sym_loss.
        near_zero is theta-gated (R_dagger co-domain catalyst).
        """
        h_s   = self._encode(s)
        h_ref = self._encode(self.reflect(s))

        frob_loss = self.frobenius.frobenius_loss(h_s)

        z_fwd = torch.cat([h_s, h_ref], dim=-1)
        h_merged_fwd = self.mu(z_fwd)

        z_rev = torch.cat([h_ref, h_s], dim=-1)
        h_merged_rev = self.mu(z_rev)

        zero_s   = self.zero_head(h_merged_fwd)
        zero_ref = self.zero_head(h_merged_rev)
        sym_loss = F.mse_loss(zero_s, zero_ref)

        near_base = self.near_head(h_merged_fwd)   # [B, 1] in (0, 1)

        # R_dagger theta gate: learned co-domain modulation
        t = s[:, 1:2]
        theta_feats = theta_circular_features(t)                   # [B, 2]
        gate = 1.0 + self.theta_gate(theta_feats)                  # [B, 1] in (1, 2)
        near_gated = (near_base * gate).clamp(0.0, 1.0)           # [B, 1] in (0, 1)

        return {
            "zero_t":    zero_s.squeeze(-1),
            "near_zero": near_gated.squeeze(-1),
            "embedding": h_merged_fwd,
            "frob_loss": frob_loss,
            "sym_loss":  sym_loss,
        }

    def compute_loss(
        self,
        out: dict,
        true_zero_t:   torch.Tensor | None = None,
        true_near:     torch.Tensor | None = None,
        lam_zero: float = 1.0,
        lam_frob: float = 0.5,
        lam_sym:  float = 1.0,
        lam_near: float = 5.0,   # higher than Phase A: near_zero is the primary signal
    ) -> dict:
        L_frob = out["frob_loss"]
        L_sym  = out["sym_loss"]

        L_zero = torch.zeros(1, device=L_frob.device)
        if true_zero_t is not None:
            L_zero = F.mse_loss(out["zero_t"], true_zero_t)

        L_near = torch.zeros(1, device=L_frob.device)
        if true_near is not None:
            L_near = F.binary_cross_entropy(out["near_zero"], true_near.float())

        total = lam_zero * L_zero + lam_frob * L_frob + lam_sym * L_sym + lam_near * L_near
        return {
            "loss":   total,
            "L_zero": L_zero.item(),
            "L_frob": L_frob.item(),
            "L_sym":  L_sym.item(),
            "L_near": L_near.item(),
        }


# ── Phase B training target ───────────────────────────────────────────────────

def near_theta_target(t_batch: torch.Tensor, zeros_t: list[float],
                      sigma: float = 0.4, jitter: float = 0.3,
                      theta_weight: float = 0.3) -> torch.Tensor:
    """
    Phase B near_zero target: combines Gaussian proximity signal with Gram-alignment.
    target = max(gaussian_proximity, theta_weight * gram_alignment)

    gaussian_proximity: standard jittered Gaussian from Phase A
    gram_alignment: cos^2(theta(t)) — peaks at Gram points where zeros cluster
      Normalized to [0,1]: (1 + cos(2*theta)) / 2

    theta_weight: how strongly Gram alignment contributes (default 0.3).
    Setting theta_weight=0 recovers Phase A target exactly.
    """
    # Gaussian proximity (Phase A component)
    jittered = [z + random.uniform(-jitter, jitter) for z in zeros_t]
    t  = t_batch.unsqueeze(1)                                        # [B, 1]
    z  = torch.tensor(jittered, dtype=torch.float32, device=t.device)
    sq = ((t - z) ** 2) / (2.0 * sigma ** 2)
    gauss = torch.exp(-sq).max(dim=1).values                        # [B]

    # Gram alignment (Phase B addition)
    theta = rs_theta_torch(t_batch.unsqueeze(1)).squeeze(1)         # [B]
    gram_align = (1.0 + torch.cos(2.0 * theta)) / 2.0              # [B] in [0,1]

    return torch.maximum(gauss, theta_weight * gram_align)


# ── Phase B training loop ─────────────────────────────────────────────────────

def train_phase_b(
    model:       RiemannNavigatorPhaseB,
    zeros_t:     list[float],
    epochs:      int   = 300,
    sigma:       float = 0.4,
    jitter:      float = 0.3,
    near_lr:     float = 1e-3,
    backbone_lr: float = 3e-4,
    t_range_hi:  float = 700.0,
    theta_weight: float = 0.3,
) -> None:
    """
    Phase B training: same structure as Phase A but with theta target.
    G_aleph scope: t_range extended to 700 (vs 260 in Phase A).
    """
    near_params     = [p for n, p in model.named_parameters()
                       if "near_head" in n or "theta_gate" in n]
    backbone_params = [p for n, p in model.named_parameters()
                       if "near_head" not in n and "theta_gate" not in n]
    opt   = optim.AdamW([
        {"params": near_params,     "lr": near_lr},
        {"params": backbone_params, "lr": backbone_lr},
    ], weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    t_lo = min(zeros_t) - 5.0
    print(f"  sigma={sigma} jitter=±{jitter} theta_weight={theta_weight}")
    print(f"  t_range=({t_lo:.0f}, {t_range_hi}) {epochs}ep  [G_aleph scope]")
    print(f"\n  {'Epoch':>6}  {'L_near':>10}  {'L_frob':>10}  {'Gap_log':>9}")
    print(f"  {'------':>6}  {'----------':>10}  {'----------':>10}  {'---------':>9}")

    for epoch in range(1, epochs + 1):
        model.train()
        s, _, _ = make_riemann_batch(zeros_t, batch_size=128,
                                     t_range=(t_lo, t_range_hi))
        s = s.to(DEVICE)
        out    = model(s)
        target = near_theta_target(s[:, 1], zeros_t, sigma, jitter, theta_weight)
        target = target.to(DEVICE)
        losses = model.compute_loss(out, true_near=target)
        losses["loss"].backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % 50 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                t_at  = torch.tensor(
                    [[0.5, z + random.uniform(-0.1, 0.1)] for z in zeros_t[:20]],
                    dtype=torch.float32).to(DEVICE)
                t_far = torch.tensor(
                    [[0.5, z + random.uniform(2.0, 4.0)] for z in zeros_t[:20]],
                    dtype=torch.float32).to(DEVICE)
                gap_log = (model(t_at)["near_zero"].mean()
                           - model(t_far)["near_zero"].mean()).item()
                l_near = losses.get("L_near", 0.0)
                l_frob = losses.get("L_frob", 0.0)
            print(f"  {epoch:>6}  {l_near:>10.6f}  {l_frob:>10.6f}  {gap_log:>+9.4f}")


# ── Phase B frozen-backbone training (Test 4) ────────────────────────────────

def train_phase_b_frozen(
    model:        RiemannNavigatorPhaseB,
    zeros_t:      list[float],
    epochs:       int   = 200,
    sigma:        float = 0.4,
    jitter:       float = 0.3,
    near_lr:      float = 3e-4,
    t_range_hi:   float = 700.0,
    theta_weight: float = 0.3,
) -> None:
    """
    Phase B frozen-backbone training: freeze all backbone parameters, train only
    near_head and theta_gate.

    Grammar prescription (Probe 1 / Probe 4):
      The theta_gate implements $R_\\dagger$ (dagger/catalytic): it is a co-domain
      modifier that multiplies the near_zero output, not an input-side feature.
      This is structurally distinct from $R_\\text{cat}$ (simple concatenation):
      the catalyst modifies WHAT near_zero means, without re-processing the backbone.

      Frozen training tests whether the theta_gate alone — without any backbone
      re-tuning — is sufficient to improve hit rate above 81.1%.

      Grammar prediction: yes, because the $R_\\dagger$ promotion is a co-domain
      change, not a domain change. The backbone's internal representations are
      already correct (Phase A achieves ~81.1% at $O_1$ ceiling). The theta_gate
      corrects the output co-domain by multiplicatively rescaling near_zero by the
      Gram-interval phase. This correction is orthogonal to backbone quality.

      If frozen training achieves > 81.1%: $R_\\dagger$ co-domain correction
      confirmed as the structural source of improvement.
      If frozen training stagnates: backbone re-tuning is also required, meaning
      the $R_\\dagger$ promotion requires domain adaptation, not only co-domain.

    Soft near_zero loss:
      Phase A uses BCE (binary cross-entropy), which treats near_zero prediction
      as binary classification. For frozen backbone, we use a softer distributional
      loss: BCE + KL divergence between predicted near_zero distribution and the
      theta-augmented target distribution. This allows the gate to modulate the
      full distribution shape, not just the point-wise values.

    Note on Phase A checkpoint:
      If riemann_phase_a.pt does not exist, training proceeds from the current
      model state (cold Phase B start). The frozen backbone test is meaningful
      in either case: it isolates whether the theta_gate can improve hit rate
      given a fixed backbone, regardless of backbone quality.
    """
    # Freeze all backbone params; unfreeze only near_head and theta_gate
    for name, param in model.named_parameters():
        is_head = "near_head" in name or "theta_gate" in name
        param.requires_grad = is_head

    trainable = [p for p in model.parameters() if p.requires_grad]
    frozen    = [p for p in model.parameters() if not p.requires_grad]
    n_train   = sum(p.numel() for p in trainable)
    n_frozen  = sum(p.numel() for p in frozen)

    print(f"  Phase B FROZEN-BACKBONE training")
    print(f"  Trainable (near_head + theta_gate): {n_train:,} params")
    print(f"  Frozen (backbone): {n_frozen:,} params")
    print(f"  Grammar prediction: theta_gate alone should lift hit rate > 81.1%")
    print(f"  sigma={sigma} jitter=±{jitter} theta_weight={theta_weight}")
    print(f"  t_range=({min(zeros_t) - 5.0:.0f}, {t_range_hi}) {epochs}ep\n")
    print(f"  {'Epoch':>6}  {'L_near':>10}  {'L_kl':>10}  {'Gap_log':>9}")
    print(f"  {'------':>6}  {'----------':>10}  {'----------':>10}  {'---------':>9}")

    opt   = optim.AdamW(trainable, lr=near_lr, weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    t_lo  = min(zeros_t) - 5.0

    for epoch in range(1, epochs + 1):
        model.train()

        s, _, _ = make_riemann_batch(zeros_t, batch_size=128,
                                     t_range=(t_lo, t_range_hi))
        s = s.to(DEVICE)

        with torch.no_grad():
            # Backbone forward: no grad through backbone
            # Must run full model.forward() but backbone grads are detached
            # by requires_grad=False — autograd will not backprop through them
            pass

        out    = model(s)
        target = near_theta_target(s[:, 1], zeros_t, sigma, jitter, theta_weight)
        target = target.to(DEVICE)

        # Soft distributional loss: BCE + KL
        # BCE on point predictions (standard near_zero loss)
        pred_near = out["near_zero"].clamp(1e-7, 1 - 1e-7)
        L_bce     = F.binary_cross_entropy(pred_near, target)

        # KL divergence: treat predicted and target as Bernoulli distributions
        # KL(target || pred) = target*log(target/pred) + (1-target)*log((1-target)/(1-pred))
        t_safe = target.clamp(1e-7, 1 - 1e-7)
        L_kl   = (t_safe * (t_safe / pred_near).log()
                  + (1 - t_safe) * ((1 - t_safe) / (1 - pred_near)).log()).mean()

        # Frobenius loss still computed (backbone is frozen but frob is part of model)
        L_frob = out["frob_loss"]

        total = L_bce + 0.3 * L_kl + 0.1 * L_frob
        total.backward()
        nn.utils.clip_grad_norm_(trainable, 1.0)
        opt.step(); opt.zero_grad(); sched.step()

        if epoch % 50 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                t_at  = torch.tensor(
                    [[0.5, z + random.uniform(-0.1, 0.1)] for z in zeros_t[:20]],
                    dtype=torch.float32).to(DEVICE)
                t_far = torch.tensor(
                    [[0.5, z + random.uniform(2.0, 4.0)] for z in zeros_t[:20]],
                    dtype=torch.float32).to(DEVICE)
                gap_log = (model(t_at)["near_zero"].mean()
                           - model(t_far)["near_zero"].mean()).item()
            print(f"  {epoch:>6}  {L_bce.item():>10.6f}  {L_kl.item():>10.6f}"
                  f"  {gap_log:>+9.4f}")

    # Re-enable all gradients for subsequent use
    for param in model.parameters():
        param.requires_grad = True

    print(f"\n  Frozen training complete. All params re-enabled for grad.")
    print(f"  Compare gap_log to full Phase B: if comparable, theta_gate alone suffices.")


# ── Warm-start from Phase A weights ──────────────────────────────────────────

def load_phase_a_weights(
    phase_b_model: RiemannNavigatorPhaseB,
    phase_a_path: str | Path,
) -> None:
    """
    Load Phase A (RiemannNavigator) weights into Phase B model.
    All layers match except input_proj (different input_dim).
    input_proj is re-initialized; all other weights are copied exactly.
    """
    ckpt = torch.load(phase_a_path, map_location=DEVICE)
    state = ckpt["state_dict"] if "state_dict" in ckpt else ckpt

    # Filter out input_proj (different size) and theta_gate (new)
    phase_b_state = phase_b_model.state_dict()
    compatible = {
        k: v for k, v in state.items()
        if k in phase_b_state and v.shape == phase_b_state[k].shape
    }
    skipped = [k for k in state if k not in compatible]
    phase_b_model.load_state_dict(compatible, strict=False)
    print(f"  Loaded {len(compatible)}/{len(state)} layers from Phase A checkpoint")
    if skipped:
        print(f"  Re-initialized (shape mismatch): {skipped}")


# ── Blind prediction (same as riemann_predict.py but uses Phase B model) ─────

def predict_blind_b(
    model: RiemannNavigatorPhaseB,
    t_scan_lo: float,
    t_scan_hi: float,
    sep: float = 0.8,
    label: str = "",
) -> list[tuple[float, float]]:
    """scan_near_zero reused from riemann_crf; model is Phase B."""
    n_pts = max(4000, int((t_scan_hi - t_scan_lo) * 30))
    raw_all, t_vals, p_nears = scan_near_zero(
        model, t_scan_lo - 0.5, t_scan_hi + 2.0, n_pts=n_pts
    )

    rs_lo  = rs_N(t_scan_lo)
    rs_hi  = rs_N(t_scan_hi + 1.0)
    budget = int(math.floor(rs_hi - rs_lo)) + 1

    raw_gated = [
        (t, p) for t, p in raw_all
        if t >= t_scan_lo - 0.5 and t <= t_scan_hi + 1.0
    ]
    selected = budget_viterbi(raw_gated, budget=budget, sep=sep)

    near_std = torch.tensor(p_nears).std().item()
    print(f"\n  {label}  t=[{t_scan_lo:.0f}, {t_scan_hi:.0f}]")
    print(f"  RS budget: {budget}  |  raw gated: {len(raw_gated)}"
          f"  |  selected: {len(selected)}  |  near_zero std: {near_std:.3e}")
    print(f"\n  {'#':>4}  {'t_pred':>12}  {'P(near)':>8}")
    print(f"  {'----':>4}  {'------------':>12}  {'--------':>8}")
    for i, (t, p) in enumerate(selected, 1):
        print(f"  {i:>4}  {t:>12.4f}  {p:>8.4f}")
    return selected


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    HIDDEN   = 240
    LAYERS   = 24
    HEADS    = 24
    NFOURIER = 48
    FREQ_MAX = 2.5

    model = RiemannNavigatorPhaseB(
        hidden_dim=HIDDEN, num_layers=LAYERS, num_heads=HEADS,
        n_fourier=NFOURIER, freq_max=FREQ_MAX,
    ).to(DEVICE)

    n_params = sum(p.numel() for p in model.parameters())
    print(f"RiemannNavigatorPhaseB  params={n_params:,}")
    print(f"SELF_ENCODE_TARGET = {model.SELF_ENCODE_TARGET:,}")
    print(f"DEFINING_TUPLE R = {model.DEFINING_TUPLE['R']}  (promoted from R_cat)")

    TRAIN_ZEROS = RIEMANN_ZEROS_T   # zeros 1-100

    # ── Optional: warm-start from Phase A ─────────────────────────────────────
    phase_a_ckpt = Path("riemann_phase_a.pt")
    if phase_a_ckpt.exists():
        print(f"\nWarm-starting from Phase A checkpoint: {phase_a_ckpt}")
        load_phase_a_weights(model, phase_a_ckpt)
        print("  (input_proj and theta_gate re-initialized from random)")
    else:
        print(f"\nNo Phase A checkpoint found — training from scratch")
        print(f"  (to warm-start: run riemann_predict.py and save model as {phase_a_ckpt})")

    # ── Phase B training ───────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"PHASE B TRAINING — G_aleph scope, theta-augmented target, R_dagger gate")
    print(f"{'='*68}")
    train_phase_b(
        model, TRAIN_ZEROS, epochs=300,
        t_range_hi=700.0, theta_weight=0.3,
    )

    # ── Blind predictions: extended window t=600-800 ───────────────────────────
    print(f"\n{'='*68}")
    print(f"BLIND PREDICTIONS (Phase B) — t=600-800, zeros ~300-370 (NEVER SEEN)")
    print(f"{'='*68}")

    preds_w3 = predict_blind_b(
        model, t_scan_lo=600.0, t_scan_hi=700.0,
        sep=0.8, label="Window 3 (t=600-700)",
    )
    preds_w4 = predict_blind_b(
        model, t_scan_lo=700.0, t_scan_hi=800.0,
        sep=0.8, label="Window 4 (t=700-800)",
    )

    # ── Verification ──────────────────────────────────────────────────────────
    print(f"\n{'='*68}")
    print(f"VERIFICATION — Phase B predictions vs mpmath ground truth")
    print(f"{'='*68}")

    n_w3_lo = int(math.floor(rs_N(600.0))) + 1
    n_w3_hi = int(math.ceil(rs_N(701.0)))
    n_w4_lo = int(math.floor(rs_N(700.0))) + 1
    n_w4_hi = int(math.ceil(rs_N(801.0)))

    print(f"\n  Window 3: RS predicts zeros #{n_w3_lo}-{n_w3_hi} in t=[600,700]")
    h3_hits, h3_ph, h3_miss = verify_predictions(
        preds_w3, n_start=n_w3_lo, n_end=n_w3_hi, label="Window 3"
    )

    print(f"\n  Window 4: RS predicts zeros #{n_w4_lo}-{n_w4_hi} in t=[700,800]")
    h4_hits, h4_ph, h4_miss = verify_predictions(
        preds_w4, n_start=n_w4_lo, n_end=n_w4_hi, label="Window 4"
    )

    n_w3 = n_w3_hi - n_w3_lo + 1
    n_w4 = n_w4_hi - n_w4_lo + 1
    h3u  = n_w3 - h3_miss
    h4u  = n_w4 - h4_miss

    print(f"\n{'='*68}")
    print(f"SUMMARY — Phase B vs Phase A comparison")
    print(f"{'='*68}")
    print(f"  Phase A (riemann_predict.py): 81.1% at t=400-600 (zeros 201-270)")
    print(f"  Phase B Window 3 (t=600-700): {h3u}/{n_w3} = {100*h3u/n_w3:.1f}%"
          f"  {h3_ph} phantoms  {h3_miss} missed")
    print(f"  Phase B Window 4 (t=700-800): {h4u}/{n_w4} = {100*h4u/n_w4:.1f}%"
          f"  {h4_ph} phantoms  {h4_miss} missed")
    pct = (h3u + h4u) / (n_w3 + n_w4) * 100
    print(f"  Phase B combined: {h3u+h4u}/{n_w3+n_w4} = {pct:.1f}%")
    print(f"\n  Theta gate effect: near_zero std should be HIGHER than Phase A (0.0943)")
    print(f"  If near_zero std > 0.09 and hit rate > 81%: theta gating is contributing")
    print(f"  If near_zero std flat and hit rate ~81%: RS structure dominates (no regression)")


if __name__ == "__main__":
    main()
