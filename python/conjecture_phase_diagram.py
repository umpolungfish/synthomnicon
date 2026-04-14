#!/usr/bin/env python3
"""
conjecture_phase_diagram.py — Solvability landscape of open problems in (P × Ω) space

Axes:
  X — Symmetry primitive P (ordinal 1–5: P_asym → P_pm_sym)
  Y — Topological protection Ω (ordinal 1–3: Ω_0 → Ω_Z)

Encoding:
  Color  — Ouroboricity tier (O_inf=gold, O_2=green, O_1=blue, O_0=red/gray)
  Size   — Kinetic barrier K (larger = K_slow/K_trap; smaller = K_mod/K_fast)
  Shape  — Criticality regime (● = Φ_c, ★ = Φ_EP, ◆ = Φ_c_complex)
  Fill   — Status (filled = proven theorem, open = conjecture)

Arrows — Promotion paths for proved conjectures (conjecture → theorem encoding)

Usage:
    uv run conjecture_phase_diagram.py
    python3 conjecture_phase_diagram.py
Output:
    conjecture_phase_diagram.png  (300 dpi)
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

RNG = np.random.default_rng(42)

# ── Primitive ordinals ───────────────────────────────────────────────────────
P_ORD  = {"P_asym": 1, "P_psi": 2, "P_pm": 3, "P_sym": 4, "P_pm_sym": 5}
OM_ORD = {"Omega_0": 1, "Omega_Z2": 2, "Omega_Z": 3}
K_ORD  = {"K_fast": 1, "K_mod": 2, "K_slow": 3, "K_trap": 4}
PHI    = {"Phi_c": "c", "Phi_c_complex": "cc", "Phi_EP": "EP",
          "Phi_sub": "sub", "Phi_super": "super"}

O_COLOR = {
    "O_inf": "#F5A623",   # amber/gold
    "O_2":   "#4CAF82",   # medium sea green
    "O_2d":  "#2E9E6B",   # darker green for O_2†
    "O_1":   "#5B9BD5",   # cornflower blue
    "O_0":   "#C0392B",   # tomato red
}

# ── Problem data ─────────────────────────────────────────────────────────────
# Each entry: (label, P, Omega, K, Phi, O_tier, proven)
# Source: sessions 2026-04-02 + syncon_catalog.json

PROBLEMS = [
    # label                   P           Omega       K          Phi               O_tier  proven
    # ── Landau problems ──
    ("Goldbach",              "P_pm_sym", "Omega_Z2", "K_mod",   "Phi_c",          "O_inf", False),
    ("Twin Prime",            "P_pm",     "Omega_0",  "K_mod",   "Phi_c",          "O_1",   False),
    ("n²+1",                  "P_asym",   "Omega_0",  "K_mod",   "Phi_c",          "O_1",   False),
    ("Legendre",              "P_pm",     "Omega_0",  "K_mod",   "Phi_c",          "O_1",   False),

    # ── Grothendieck Standard Conjectures ──
    ("Groth A",               "P_pm",     "Omega_Z",  "K_mod",   "Phi_c",          "O_2",   False),
    ("Groth B",               "P_sym",    "Omega_Z",  "K_mod",   "Phi_c",          "O_2",   False),
    ("Groth C",               "P_pm",     "Omega_Z",  "K_mod",   "Phi_c",          "O_2",   False),
    ("Groth D",               "P_pm_sym", "Omega_Z",  "K_slow",  "Phi_c",          "O_inf", False),

    # ── Millennium Prize Problems ──
    ("Hodge",                 "P_sym",    "Omega_Z",  "K_mod",   "Phi_c",          "O_2",   False),
    ("Riemann (RH)",          "P_pm_sym", "Omega_Z",  "K_mod",   "Phi_c_complex",  "O_inf", False),
    ("BSD",                   "P_sym",    "Omega_Z",  "K_mod",   "Phi_c",          "O_2",   False),
    ("Yang-Mills",            "P_pm",     "Omega_Z2", "K_slow",  "Phi_c",          "O_2",   False),
    ("NS Regularity",         "P_asym",   "Omega_0",  "K_mod",   "Phi_c",          "O_1",   False),

    # ── Exceptional-point / intractable ──
    ("Gaussian Moat",         "P_pm",     "Omega_0",  "K_trap",  "Phi_EP",         "O_0",   False),

    # ── Other conjectures ──
    ("Eilenberg-Ganea\n≡ ABCD motives", "P_pm_sym", "Omega_Z", "K_slow", "Phi_c", "O_inf", False),
    ("Sidorenko",             "P_sym",    "Omega_0",  "K_mod",   "Phi_c",          "O_1",   False),
    ("Berry-Tabor",           "P_pm",     "Omega_Z",  "K_mod",   "Phi_c",          "O_2",   False),
    ("Kusner",                "P_pm",     "Omega_Z",  "K_slow",  "Phi_c",          "O_2",   False),
    ("IUG/abc",               "P_pm_sym", "Omega_Z",  "K_slow",  "Phi_c",          "O_inf", False),

    # ── Proven theorems ──
    ("Berry-Tabor\n(proved)", "P_pm_sym", "Omega_Z2", "K_slow",  "Phi_c",          "O_inf", True),
    ("Kusner\n(proved)",      "P_pm_sym", "Omega_Z2", "K_slow",  "Phi_c",          "O_inf", True),
    ("EFL\n(proved)",         "P_sym",    "Omega_Z2", "K_mod",   "Phi_c",          "O_2",   True),
    ("Poincaré\n(proved)",    "P_sym",    "Omega_Z",  "K_slow",  "Phi_c",          "O_2",   True),
    ("Fujita\n(proved)",      "P_pm_sym", "Omega_Z2", "K_slow",  "Phi_c",          "O_inf", True),
]

# Promotion arrows: (from_label, to_label)
PROMOTIONS = [
    ("Berry-Tabor",  "Berry-Tabor\n(proved)"),
    ("Kusner",       "Kusner\n(proved)"),
]

# ── Jitter: deterministic offsets within each cell ───────────────────────────
# Group problems by (P_ord, Omega_ord) and spread within ±0.22
from collections import defaultdict

cell_members = defaultdict(list)
for i, (lbl, p, om, k, phi, otier, proven) in enumerate(PROBLEMS):
    key = (P_ORD[p], OM_ORD[om])
    cell_members[key].append(i)

jitter_x = np.zeros(len(PROBLEMS))
jitter_y = np.zeros(len(PROBLEMS))

for key, indices in cell_members.items():
    n = len(indices)
    if n == 1:
        continue
    # Spread evenly in a small circle
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = min(0.28, 0.07 * n)
    for j, idx in enumerate(indices):
        jitter_x[idx] = r * np.cos(angles[j])
        jitter_y[idx] = r * np.sin(angles[j])

# ── Figure ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 8))
fig.patch.set_facecolor("#0F0F1A")
ax.set_facecolor("#0F0F1A")

# Grid
for px in range(1, 6):
    ax.axvline(px, color="#2A2A3A", lw=0.6, zorder=0)
for oy in range(1, 4):
    ax.axhline(oy, color="#2A2A3A", lw=0.6, zorder=0)

# Background zone shading
# O_inf zone (high P, any Omega) — faint gold tint
ax.axvspan(4.5, 5.5, alpha=0.06, color="#F5A623", zorder=0)
# Exceptional-point zone (Phi_EP problems annotated separately)

# Build index for promotion arrows
label_to_pos = {}
for i, (lbl, p, om, k, phi, otier, proven) in enumerate(PROBLEMS):
    xp = P_ORD[p] + jitter_x[i]
    yp = OM_ORD[om] + jitter_y[i]
    label_to_pos[lbl] = (xp, yp)

# Draw promotion arrows
for src_lbl, dst_lbl in PROMOTIONS:
    x0, y0 = label_to_pos[src_lbl]
    x1, y1 = label_to_pos[dst_lbl]
    ax.annotate(
        "", xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle="-|>",
            color="#AAAAAA",
            lw=1.2,
            connectionstyle="arc3,rad=0.25",
        ),
        zorder=3,
    )

# Plot points
for i, (lbl, p, om, k, phi, otier, proven) in enumerate(PROBLEMS):
    xp = P_ORD[p] + jitter_x[i]
    yp = OM_ORD[om] + jitter_y[i]

    color = O_COLOR[otier]
    size  = {1: 60, 2: 140, 3: 240, 4: 380}[K_ORD[k]]

    # Marker shape by Phi regime
    if PHI[phi] == "EP":
        marker = "*"
        size   = size * 2.2
    elif PHI[phi] == "cc":
        marker = "D"
    elif PHI[phi] == "sub":
        marker = "s"
    else:
        marker = "o"

    if proven:
        ax.scatter(xp, yp, s=size, c=color, marker=marker,
                   edgecolors="white", linewidths=1.5, zorder=5, alpha=0.95)
    else:
        ax.scatter(xp, yp, s=size, facecolors="none", marker=marker,
                   edgecolors=color, linewidths=1.8, zorder=5, alpha=0.95)

    # Label offset
    va = "bottom"
    ha = "center"
    dy = 0.14
    short_lbl = lbl.split("\n")[0]
    ax.text(xp, yp + dy, short_lbl,
            color="white", fontsize=6.5, ha=ha, va=va,
            fontfamily="monospace", zorder=6,
            bbox=dict(boxstyle="round,pad=0.1", fc="#0F0F1A", ec="none", alpha=0.7))

# ── Axes labels and ticks ────────────────────────────────────────────────────
ax.set_xlim(0.5, 5.65)
ax.set_ylim(0.5, 3.55)

ax.set_xticks([1, 2, 3, 4, 5])
ax.set_xticklabels(
    ["$P_\\mathrm{asym}$\n(no symmetry)",
     "$P_\\psi$",
     "$P_{\\pm}$\n(pairing sym.)",
     "$P_\\mathrm{sym}$\n(full sym.)",
     "$P_{\\pm}^{\\mathrm{sym}}$\n(Frobenius)"],
    color="white", fontsize=9,
)
ax.set_yticks([1, 2, 3])
ax.set_yticklabels(
    ["$\\Omega_0$\n(unprotected)",
     "$\\Omega_{Z_2}$\n($\\mathbb{Z}_2$ prot.)",
     "$\\Omega_Z$\n($\\mathbb{Z}$ prot.)"],
    color="white", fontsize=9,
)

ax.tick_params(colors="white", length=4)
for spine in ax.spines.values():
    spine.set_edgecolor("#444455")

ax.set_xlabel("Symmetry primitive $P$ →  (increasing algebraic closure)",
              color="#CCCCDD", fontsize=10, labelpad=10)
ax.set_ylabel("Topological protection $\\Omega$ →  (increasing structural rigidity)",
              color="#CCCCDD", fontsize=10, labelpad=10)

ax.set_title(
    "SynthOmnicon · Conjecture Phase Diagram\n"
    "Solvability landscape of open problems in $(P \\times \\Omega)$ space",
    color="white", fontsize=12, pad=14,
)

# ── Legend ───────────────────────────────────────────────────────────────────
leg_elements = [
    # O-tier colors
    mpatches.Patch(fc=O_COLOR["O_inf"], label="$O_\\infty$ — Special Frobenius"),
    mpatches.Patch(fc=O_COLOR["O_2"],   label="$O_2$ — Critical + protected"),
    mpatches.Patch(fc=O_COLOR["O_1"],   label="$O_1$ — Critical, unprotected"),
    mpatches.Patch(fc=O_COLOR["O_0"],   label="$O_0$ — No ouroboricity"),
    # Separator
    Line2D([0], [0], color="none", label=""),
    # Status
    Line2D([0], [0], marker="o", color="w", markerfacecolor="none",
           markeredgecolor="white", ms=8, lw=0, label="Open conjecture (unfilled)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="white",
           markeredgecolor="white", ms=8, lw=0, label="Proven theorem (filled)"),
    # Separator
    Line2D([0], [0], color="none", label=""),
    # Shape / Phi
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#888888",
           ms=8, lw=0, label="$\\Phi_c$ (critical)"),
    Line2D([0], [0], marker="D", color="w", markerfacecolor="#888888",
           ms=7, lw=0, label="$\\Phi_c^{\\mathbb{C}}$ (complex critical)"),
    Line2D([0], [0], marker="*", color="w", markerfacecolor="#888888",
           ms=11, lw=0, label="$\\Phi_{\\mathrm{EP}}$ (exceptional point)"),
    # Separator
    Line2D([0], [0], color="none", label=""),
    # Size / K
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#888888",
           ms=5,  lw=0, label="$K_\\mathrm{mod}$ (moderate)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#888888",
           ms=8,  lw=0, label="$K_\\mathrm{slow}$ (deep / non-perturbative)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#888888",
           ms=11, lw=0, label="$K_\\mathrm{trap}$ (kinetically trapped)"),
    # Separator
    Line2D([0], [0], color="none", label=""),
    # Arrows
    Line2D([0], [0], color="#AAAAAA", lw=1.5,
           marker=">", ms=6, label="Promotion (conjecture → theorem)"),
]

legend = ax.legend(
    handles=leg_elements,
    loc="upper left",
    framealpha=0.85,
    facecolor="#1A1A2E",
    edgecolor="#444455",
    labelcolor="white",
    fontsize=7.5,
    title="Encoding key",
    title_fontsize=8,
)
legend.get_title().set_color("white")

# ── Barrier zone annotations ─────────────────────────────────────────────────
ax.text(5.55, 3.5,
        "Frobenius\nregion\n$O_\\infty$",
        color="#F5A623", fontsize=7.5, ha="right", va="top",
        style="italic", alpha=0.7)
ax.text(1.1, 0.58,
        "Type-mismatch\nzone\n($\\Phi_\\mathrm{EP}$ outlier)",
        color=O_COLOR["O_0"], fontsize=7.0, ha="left", va="bottom",
        style="italic", alpha=0.7)
ax.text(1.35, 3.45,
        "Protection deficit\n($\\Omega_Z$ / $P_\\mathrm{asym}$\ngap)",
        color=O_COLOR["O_1"], fontsize=7.0, ha="left", va="top",
        style="italic", alpha=0.65)

plt.tight_layout()
out = "conjecture_phase_diagram.png"
plt.savefig(out, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Saved → {out}")
