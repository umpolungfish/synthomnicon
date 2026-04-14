#!/usr/bin/env python3
"""
conjecture_mds.py — Full-catalog MDS projection, conjecture-focused overlay

Uses the Mahalanobis metric on all 12 primitives to embed the full catalog,
then highlights only the conjectures/problems from the recent analysis sessions.
Everything else is shown as faint background.

This is the honest version: positions reflect true 12D structural distances,
no jitter, no axis selection — the MDS finds the best 2D projection.

Usage:
    uv run conjecture_mds.py
Output:
    conjecture_mds.png  (300 dpi)
"""

import json
import sys
import numpy as np
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from sklearn.manifold import MDS

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from space_search.primitives import (
    build_metric_tensor, mahalanobis_distance, to_vector, PRIMITIVE_ORDER
)

# ── Load catalog ──────────────────────────────────────────────────────────────
with open(ROOT / "syncon_catalog.json") as f:
    raw = json.load(f)

if isinstance(raw, dict):
    catalog = raw
else:
    catalog = {e["name"]: e for e in raw if "name" in e}

G = build_metric_tensor(str(ROOT / "syncon_catalog.json"))

# ── Build distance matrix for all catalog entries ────────────────────────────
names = list(catalog.keys())
n = len(names)

print(f"Computing {n}×{n} Mahalanobis distance matrix...")
vecs = []
valid_names = []
for nm in names:
    try:
        v = to_vector(catalog[nm])
        vecs.append(v)
        valid_names.append(nm)
    except (KeyError, TypeError):
        pass

vecs = np.array(vecs)  # (N, 12)
N = len(valid_names)

# Vectorised Mahalanobis: D_ij = sqrt((v_i - v_j)^T G (v_i - v_j))
diff = vecs[:, None, :] - vecs[None, :, :]          # (N, N, 12)
dist_sq = np.einsum("ijk,kl,ijl->ij", diff, G, diff) # (N, N)
dist_sq = np.maximum(dist_sq, 0)
D = np.sqrt(dist_sq)

print(f"Running MDS on {N} entries...")
mds = MDS(n_components=2, dissimilarity="precomputed",
          random_state=42, n_init=4, max_iter=500, normalized_stress="auto")
coords = mds.fit_transform(D)

name_to_idx = {nm: i for i, nm in enumerate(valid_names)}

# ── Problems to highlight ─────────────────────────────────────────────────────
O_COLOR = {
    "O_inf": "#F5A623",
    "O_2":   "#4CAF82",
    "O_1":   "#5B9BD5",
    "O_0":   "#C0392B",
}

HIGHLIGHT = {
    # catalog_name                    display_label           O_tier   proven
    "goldbach_conjecture":            ("Goldbach",            "O_inf",  False),
    "twin_prime_conjecture":          ("Twin Prime",          "O_1",    False),
    "prime_n2_plus_1":               ("n²+1",                "O_1",    False),
    "legendre_conjecture":            ("Legendre",            "O_1",    False),
    "grothendieck_A_lefschetz":       ("Groth A",             "O_2",    False),
    "grothendieck_B_hodge":           ("Groth B",             "O_2",    False),
    "grothendieck_C_kunneth":         ("Groth C",             "O_2",    False),
    "grothendieck_D_numerical_homological": ("Groth D",       "O_inf",  False),
    "hodge_conjecture":               ("Hodge",               "O_2",    False),
    "riemann_hypothesis":             ("RH",                  "O_inf",  False),
    "birch_swinnerton_dyer":          ("BSD",                 "O_2",    False),
    "yang_mills_mass_gap":            ("Yang-Mills",          "O_2",    False),
    "navier_stokes_regularity":       ("NS Regularity",       "O_1",    False),
    "gaussian_moat_problem":          ("Gaussian Moat",       "O_0",    False),
    "eilenberg_ganea_conjecture":     ("Eilenberg-Ganea",     "O_inf",  False),
    "grothendieck_ABCD_join":         ("ABCD join\n= motives","O_inf",  False),
    "sidorenko_conjecture":           ("Sidorenko",           "O_1",    False),
    "berry_tabor_conjecture":         ("Berry-Tabor",         "O_2",    False),
    "berry_tabor_proven":             ("Berry-Tabor\n(proved)","O_inf", True),
    "kusner_conjecture":              ("Kusner",              "O_2",    False),
    "kusner_theorem":                 ("Kusner (proved)",     "O_inf",  True),
    "erdos_faber_lovasz_conjecture":  ("EFL (proved)",        "O_2",    True),
    "IUG":                            ("IUG/abc",             "O_inf",  False),
    "poincare_conjecture":            ("Poincaré (proved)",   "O_2",    True),
}

# Fallback name variants (catalog keys vary)
ALIASES = {
    "prime_n2_plus_1":          ["n_squared_plus_one_primes", "prime_n_squared_plus_1",
                                  "n_squared_plus_1", "n2_plus_1", "prime_polynomial_n2_1"],
    "goldbach_conjecture":      ["goldbach"],
    "twin_prime_conjecture":    ["twin_prime", "twin_primes"],
    "legendre_conjecture":      ["legendre"],
    "riemann_hypothesis":       ["riemann_hypothesis", "rh", "RH"],
    "birch_swinnerton_dyer":    ["birch_swinnerton_dyer", "bsd", "BSD"],
    "yang_mills_mass_gap":      ["yang_mills", "yang_mills_gap",
                                  "yang_mills_mass_gap"],
    "navier_stokes_regularity": ["navier_stokes", "navier_stokes_regularity",
                                  "ns_regularity"],
    "gaussian_moat_problem":    ["gaussian_moat", "gaussian_moat_problem"],
    "sidorenko_conjecture":     ["sidorenko", "sidorenko_conjecture"],
}

def resolve(key):
    if key in name_to_idx:
        return key
    for alias in ALIASES.get(key, []):
        if alias in name_to_idx:
            return alias
    # substring search
    for nm in valid_names:
        if key.lower().replace("_", "") in nm.lower().replace("_", ""):
            return nm
    return None

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 9))
fig.patch.set_facecolor("#0A0A16")
ax.set_facecolor("#0A0A16")

# Background catalog points
bg_mask = np.ones(N, dtype=bool)
resolved_indices = set()
for key in HIGHLIGHT:
    rk = resolve(key)
    if rk and rk in name_to_idx:
        resolved_indices.add(name_to_idx[rk])
for i in resolved_indices:
    bg_mask[i] = False

ax.scatter(coords[bg_mask, 0], coords[bg_mask, 1],
           s=8, c="#2A2A3E", alpha=0.35, zorder=1, linewidths=0)

# Highlighted problems
plotted = {}
for key, (label, otier, proven) in HIGHLIGHT.items():
    rk = resolve(key)
    if rk is None or rk not in name_to_idx:
        print(f"  [not found] {key}")
        continue
    idx = name_to_idx[rk]
    x, y = coords[idx]
    color = O_COLOR[otier]
    size = 160 if otier == "O_inf" else 110 if otier == "O_2" else 90

    if otier == "O_0":  # Gaussian moat — star
        marker = "*"
        size = 350
    elif proven:
        marker = "D"
        size = size * 0.85
    else:
        marker = "o"

    if proven:
        ax.scatter(x, y, s=size, c=color, marker=marker,
                   edgecolors="white", linewidths=1.2, zorder=5, alpha=0.95)
    else:
        ax.scatter(x, y, s=size, facecolors="none", marker=marker,
                   edgecolors=color, linewidths=2.0, zorder=5, alpha=0.95)

    plotted[key] = (x, y, label, color, proven)

# Labels — with small offsets to reduce overlap
label_offsets = {
    "grothendieck_A_lefschetz":       ( 0.05,  0.12),
    "grothendieck_B_hodge":           ( 0.05, -0.15),
    "grothendieck_C_kunneth":         (-0.05,  0.12),
    "grothendieck_D_numerical_homological": (0.05, 0.12),
    "grothendieck_ABCD_join":         ( 0.05, -0.15),
    "eilenberg_ganea_conjecture":     ( 0.05,  0.12),
    "berry_tabor_proven":             ( 0.05,  0.12),
    "berry_tabor_conjecture":         (-0.05, -0.15),
    "kusner_theorem":                 ( 0.05,  0.12),
    "kusner_conjecture":              (-0.05, -0.15),
    "riemann_hypothesis":             ( 0.05,  0.12),
    "gaussian_moat_problem":          ( 0.05,  0.15),
    "navier_stokes_regularity":       ( 0.05,  0.12),
    "yang_mills_mass_gap":            ( 0.05, -0.15),
}

for key, (x, y, label, color, proven) in plotted.items():
    dx, dy = label_offsets.get(key, (0.05, 0.12))
    short = label.split("\n")[0]
    ax.text(x + dx, y + dy, short,
            color="white", fontsize=7, ha="left", va="bottom",
            fontfamily="monospace", zorder=6,
            bbox=dict(boxstyle="round,pad=0.12", fc="#0A0A16",
                      ec="none", alpha=0.75))

# Axes
ax.set_xlabel("MDS dimension 1  (Mahalanobis, 12-primitive full metric)",
              color="#AAAACC", fontsize=9)
ax.set_ylabel("MDS dimension 2", color="#AAAACC", fontsize=9)
ax.tick_params(colors="#555566")
for spine in ax.spines.values():
    spine.set_edgecolor("#333344")

ax.set_title(
    "SynthOmnicon · Full-Catalog MDS Projection  (Mahalanobis $g = \\Sigma^{-1}$, 12 primitives)\n"
    "Highlighted: conjectures and theorems from 2026-04-02 sessions",
    color="white", fontsize=11, pad=12,
)

# Legend
leg = [
    mpatches.Patch(fc=O_COLOR["O_inf"], label="$O_\\infty$ — Special Frobenius"),
    mpatches.Patch(fc=O_COLOR["O_2"],   label="$O_2$ — Critical + protected"),
    mpatches.Patch(fc=O_COLOR["O_1"],   label="$O_1$ — Critical, unprotected"),
    mpatches.Patch(fc=O_COLOR["O_0"],   label="$O_0$ (★) — Exceptional point"),
    Line2D([0],[0], color="none", label=""),
    Line2D([0],[0], marker="o", color="w", markerfacecolor="none",
           markeredgecolor="white", ms=8, lw=0, label="Open conjecture"),
    Line2D([0],[0], marker="D", color="w", markerfacecolor="white",
           markeredgecolor="white", ms=7, lw=0, label="Proven theorem (◆)"),
    Line2D([0],[0], color="none", label=""),
    Line2D([0],[0], marker="o", color="w", markerfacecolor="#2A2A3E",
           ms=6, lw=0, label=f"Other catalog entries ({N} total)"),
]
legend = ax.legend(handles=leg, loc="lower right", framealpha=0.85,
                   facecolor="#14142A", edgecolor="#444455",
                   labelcolor="white", fontsize=8,
                   title="Encoding key", title_fontsize=8.5)
legend.get_title().set_color("white")

plt.tight_layout()
out = "conjecture_mds.png"
plt.savefig(out, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Saved → {out}")
