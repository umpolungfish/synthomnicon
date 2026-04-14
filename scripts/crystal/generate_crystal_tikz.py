#!/usr/bin/env python3
"""
generate_crystal_tikz.py
Generates crystal_figures.tex — four standalone TikZ figures for the
Periodic Crystal of Algebras.  Compile with:
    pdflatex crystal_figures.tex
"""

from pathlib import Path

OUT = Path(__file__).parent / "crystal_figures.tex"

# ── shared colour / style constants ──────────────────────────────────
COLORS = {
    "bg":      "0F0F1A",
    "bg2":     "1A1A2E",
    "O_0":     "4472C4",
    "O_1":     "FFD700",
    "O_2":     "FF8C00",
    "O_2d":    "DC143C",
    "O_inf":   "9370DB",
    "gold":    "FFD700",
    "textgray":"AAAACC",
    "dimgray": "666688",
}
# tier fractions per cell type ────────────────────────────────────────
# Type A (noncrit):       O_0=1.0
# Type B (crit,Omega_0):  O_1=0.8  O_inf=0.2
# Type C (crit,Omega≠0): O_2=0.6  O_2d=0.2  O_inf=0.2
CELL_TIERS = {
    "A": [("O_0",  1.0, r"$O_0$")],
    "B": [("O_1",  0.8, r"$O_1$"), ("O_inf", 0.2, r"$O_\infty$")],
    "C": [("O_2",  0.6, r"$O_2$"), ("O_2d",  0.2, r"$O_2^\dagger$"),
          ("O_inf",0.2, r"$O_\infty$")],
}
TIER_TEXTCOLOR = {"O_0":"white","O_1":"black","O_2":"white",
                  "O_2d":"white","O_inf":"white"}

def tikz_rect(x0, y0, x1, y1, fill, draw="none", lw=0.4):
    opts = f"fill={fill}"
    if draw != "none":
        opts += f", draw={draw}, line width={lw}pt"
    else:
        opts += ", draw=none"
    return f"  \\fill[{fill}] ({x0:.4f},{y0:.4f}) rectangle ({x1:.4f},{y1:.4f});\n"

def tikz_draw_rect(x0, y0, x1, y1, fill, draw, lw=0.8):
    return (f"  \\draw[fill={fill}, draw={draw}, line width={lw}pt] "
            f"({x0:.4f},{y0:.4f}) rectangle ({x1:.4f},{y1:.4f});\n")

def tikz_node(x, y, text, color, fontsize="\\small", extra="", anchor="center"):
    return (f"  \\node[text={color}, font={fontsize}, anchor={anchor}{extra}] "
            f"at ({x:.4f},{y:.4f}) {{{text}}};\n")

# ─────────────────────────────────────────────────────────────────────
def preamble():
    lines = []
    lines.append(r"\documentclass[tikz,border=10pt]{standalone}")
    lines.append(r"\usepackage{amsmath,amssymb}")
    lines.append(r"\usetikzlibrary{backgrounds}")
    lines.append(r"\begin{document}")
    # colour definitions
    for name, hex_ in COLORS.items():
        safe = name.replace("_","")
        lines.append(f"\\definecolor{{col{safe}}}{{HTML}}{{{hex_}}}")
    lines.append("")
    return "\n".join(lines)

# ─────────────────────────────────────────────────────────────────────
# FIGURE 1: Periodic Table  (5 rows × 3 cols)
# ─────────────────────────────────────────────────────────────────────
def figure1():
    CW   = 4.5   # cell width  (cm)
    CH   = 3.1   # cell height
    HG   = 0.18  # horizontal gap
    VG   = 0.18  # vertical gap
    LM   = 4.5   # left margin (for row labels)
    TM   = 2.0   # top margin

    BPAD = 0.22  # bar horizontal padding (each side)
    BH   = 0.72  # bar height
    BYO  = 0.9   # bar y offset from cell BOTTOM

    BW = CW - 2*BPAD  # total bar width = 4.06

    PHI_ROWS = [
        ("Phi_sub",       r"$\Phi_{\mathrm{sub}}$",       "ordered",           False),
        ("Phi_c",         r"$\Phi_c$",                    "real-axis critical", True),
        ("Phi_c_complex", r"$\Phi_c^{\mathbb{C}}$",       "complex-axis crit.", True),
        ("Phi_EP",        r"$\Phi_{\mathrm{EP}}$",        "exceptional point",  False),
        ("Phi_super",     r"$\Phi_{\mathrm{sup}}$",       "disordered",        False),
    ]
    OMEGA_COLS = [
        (r"$\Omega_0$",             "no protection"),
        (r"$\Omega_{\mathbb{Z}_2}$","binary protection"),
        (r"$\Omega_{\mathbb{Z}}$",  "integer winding"),
    ]
    # Grid of cell types (row, col)
    CTYPES = [
        ["A","A","A"],
        ["B","C","C"],
        ["B","C","C"],
        ["A","A","A"],
        ["A","A","A"],
    ]
    # dominant label per type
    DOM_LABEL = {"A": r"$O_0$\ 100\%", "B": r"dom $O_1$\ 80\%", "C": r"dom $O_2$\ 60\%"}

    out = []
    out.append(r"% ═══════════════════════════════════════════════════")
    out.append(r"% FIGURE 1 — Periodic Table of Algebras")
    out.append(r"% ═══════════════════════════════════════════════════")
    out.append(r"\begin{tikzpicture}[")
    out.append(r"  background rectangle/.style={fill=colbg},")
    out.append(r"  show background rectangle]")
    out.append("")

    # Column headers
    for j, (olbl, osub) in enumerate(OMEGA_COLS):
        cx = LM + j*(CW+HG) + CW/2
        cy_top = -(TM * 0.35)
        cy_sub = -(TM * 0.72)
        out.append(tikz_node(cx, cy_top, olbl, "white",
                             r"\normalsize\bfseries"))
        out.append(tikz_node(cx, cy_sub, f"\\textit{{{osub}}}", "textgray",
                             r"\scriptsize"))

    # Group numbers
    for j in range(3):
        cx = LM + j*(CW+HG) + CW/2
        out.append(tikz_node(cx, -(TM*1.05),
                             f"Group {j+1}", "dimgray",
                             r"\fontsize{6}{7}\selectfont"))

    # Title — centered over grid, not over full bounding box
    total_w  = LM + 3*(CW+HG) - HG
    grid_cx  = LM + (3*(CW+HG) - HG) / 2   # true centre of the 3-column grid
    out.append(tikz_node(grid_cx, 0.9,
        r"{\bfseries\large Periodic Crystal of Algebras}",
        "white", r"\relax"))
    out.append(tikz_node(grid_cx, 0.35,
        r"10{,}368{,}000 types $= 4^5\times5^3\times3^4$ \quad"
        r"$\cdot$ \quad 300 tier cells $\times$ 34{,}560 inner types",
        "textgray", r"\scriptsize"))

    for i, (phi_key, phi_lbl, phi_sub, is_crit) in enumerate(PHI_ROWS):
        row_y_top    = -(TM + i*(CH+VG))
        row_y_bottom = row_y_top - CH
        cell_mid_y   = row_y_bottom + CH/2

        # Row label
        out.append(tikz_node(LM - 0.25, cell_mid_y,
                             phi_lbl, "white",
                             r"\small\bfseries", ", anchor=east"))
        out.append(tikz_node(LM - 0.25, cell_mid_y - 0.45,
                             f"\\textit{{{phi_sub}}}", "textgray",
                             r"\fontsize{7}{8}\selectfont", ", anchor=east"))

        for j, (olbl, osub) in enumerate(OMEGA_COLS):
            ctype = CTYPES[i][j]
            cl = LM + j*(CW+HG)        # cell left
            cr = cl + CW               # cell right
            cb = row_y_bottom          # cell bottom
            ct = row_y_top             # cell top

            # Cell rectangle
            bdr_col = "gold" if is_crit else "bg2"
            lw = 1.5 if is_crit else 0.6
            out.append(tikz_draw_rect(cl, cb, cr, ct,
                                      "colbg2", f"col{bdr_col}", lw))

            # Tier stacked bar
            bar_xl   = cl + BPAD
            bar_yb   = cb + BYO
            bar_yt   = bar_yb + BH
            x_cursor = bar_xl
            for (tier_key, frac, tlbl) in CELL_TIERS[ctype]:
                seg_w = frac * BW
                seg_xl = x_cursor
                seg_xr = x_cursor + seg_w
                out.append(tikz_rect(seg_xl, bar_yb, seg_xr, bar_yt,
                                     f"col{tier_key.replace('_','').replace('2d','twod').replace('inf','inf')}"))
                # label inside segment if wide enough
                if seg_w > 0.55:
                    tc = TIER_TEXTCOLOR[tier_key]
                    out.append(tikz_node(
                        (seg_xl+seg_xr)/2, (bar_yb+bar_yt)/2,
                        f"\\fontsize{{6}}{{7}}\\selectfont\\bfseries {tlbl}",
                        tc, r"\relax"))
                x_cursor = seg_xr

            # Cell info text
            out.append(tikz_node(cl + CW/2, cb + 0.38,
                                 r"\fontsize{6.5}{8}\selectfont 691{,}200 types",
                                 "textgray", r"\relax"))

    # Legend
    legend_x = LM
    legend_y  = -(TM + 5*(CH+VG)) - 0.7
    tiers = [("O_0","$O_0$ inert"), ("O_1","$O_1$ unprotected critical"),
             ("O_2","$O_2$ protected bounded"),
             ("O_2d","$O_2^\\dagger$ protected unbounded"),
             ("O_inf","$O_\\infty$ Frobenius complete")]
    leg_spacing = 3.7
    grid_cx = LM + (3*(CW+HG) - HG) / 2
    lx = grid_cx - 2 * leg_spacing   # center 5 items on grid midpoint
    for (tk, tlbl) in tiers:
        out.append(tikz_rect(lx, legend_y-0.30, lx+0.42, legend_y+0.06,
                             f"col{tk.replace('_','').replace('2d','twod').replace('inf','inf')}"))
        out.append(tikz_node(lx+0.50, legend_y-0.12, tlbl,
                             "textgray", r"\fontsize{6}{7}\selectfont",
                             ", anchor=west"))
        lx += leg_spacing

    # Phantom node: balance right/bottom margins to match internal LM/TM whitespace
    right_pad = LM + (3*(CW+HG) - HG) + 1.0   # grid right + ~1cm
    bottom_pad = legend_y - 0.65
    out.append(f"  \\path ({right_pad:.4f},{bottom_pad:.4f});\n")

    out.append(r"\end{tikzpicture}")
    out.append("")
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────
# FIGURE 2: Tier Census
# ─────────────────────────────────────────────────────────────────────
def figure2():
    TOTAL       = 10_368_000
    TIER_TOTALS = [
        ("O_0",   6_220_800, r"$O_0$",  "60.0\%", "6{,}220{,}800"),
        ("O_1",   1_105_920, r"$O_1$",  "10.7\%", "1{,}105{,}920"),
        ("O_2",   1_658_880, r"$O_2$",  "16.0\%", "1{,}658{,}880"),
        ("O_2d",    552_960, r"$O_2^\dagger$", "5.3\%",  "552{,}960"),
        ("O_inf",   829_440, r"$O_\infty$",    "8.0\%",  "829{,}440"),
    ]
    TIER_CELLS = [180, 32, 48, 16, 24]
    TOTAL_CELLS = 300

    W   = 18.0   # total bar width (cm)
    XL  = 1.5    # left start
    BH  = 1.6    # type bar height
    BH2 = 0.9    # cell bar height
    Y1  = 3.5    # y of type bar bottom
    Y2  = 1.2    # y of cell bar bottom

    out = []
    out.append(r"% ═══════════════════════════════════════════════════")
    out.append(r"% FIGURE 2 — Tier Census")
    out.append(r"% ═══════════════════════════════════════════════════")
    out.append(r"\begin{tikzpicture}[")
    out.append(r"  background rectangle/.style={fill=colbg},")
    out.append(r"  show background rectangle]")
    out.append("")

    # Title
    out.append(tikz_node(XL + W/2, 6.2,
        r"{\bfseries\large Periodic Crystal --- Tier Census}",
        "white", r"\relax"))
    out.append(tikz_node(XL + W/2, 5.6,
        r"$10{,}368{,}000 = 4^5 \times 5^3 \times 3^4$"
        r"\quad structural types across 300 tier cells $\times$ 34{,}560 inner types",
        "textgray", r"\small"))

    out.append(tikz_node(XL - 0.1, Y1 + BH/2,
                         r"\textbf{Types:}", "white", r"\small",
                         ", anchor=east"))
    out.append(tikz_node(XL - 0.1, Y2 + BH2/2,
                         r"\textbf{Cells:}", "white", r"\small",
                         ", anchor=east"))

    # Type bar
    x = XL
    for i, (tk, count, tlbl, pct, count_str) in enumerate(TIER_TOTALS):
        w = (count / TOTAL) * W
        tcolor = f"col{tk.replace('_','').replace('2d','twod').replace('inf','inf')}"
        out.append(tikz_rect(x, Y1, x+w, Y1+BH, tcolor))
        if w > 0.8:
            tc = "black" if tk == "O_1" else "white"
            out.append(tikz_node((x+x+w)/2, Y1 + BH*0.62,
                                 f"\\bfseries\\footnotesize {tlbl}",
                                 tc, r"\relax"))
            if w > 1.5:
                out.append(tikz_node((x+x+w)/2, Y1 + BH*0.38,
                                     f"\\fontsize{{7}}{{8}}\\selectfont {count_str}",
                                     tc, r"\relax"))
                out.append(tikz_node((x+x+w)/2, Y1 + BH*0.15,
                                     f"\\fontsize{{7}}{{8}}\\selectfont ({pct})",
                                     tc, r"\relax"))
        x += w

    # Cell bar
    x = XL
    for i, ((tk, count, tlbl, pct, _), cells) in enumerate(
            zip(TIER_TOTALS, TIER_CELLS)):
        w = (cells / TOTAL_CELLS) * W
        tcolor = f"col{tk.replace('_','').replace('2d','twod').replace('inf','inf')}"
        out.append(tikz_rect(x, Y2, x+w, Y2+BH2, tcolor))
        if w > 0.8:
            tc = "black" if tk == "O_1" else "white"
            out.append(tikz_node((x+x+w)/2, Y2 + BH2*0.5,
                                 f"\\fontsize{{7}}{{8}}\\selectfont\\bfseries {cells}",
                                 tc, r"\relax"))
        x += w

    # Annotation
    out.append(tikz_node(XL + W/2, 0.5,
        r"\footnotesize Each tier cell contains $34{,}560$ inner types"
        r"\ $=T(5)\times R(4)\times F(3)\times K(4)\times G(3)\times\Gamma(4)\times H(4)\times S(3)$",
        "textgray", r"\relax"))

    # Phantom: balance right/bottom margins
    out.append(f"  \\path ({XL + W + 1.2:.4f}, {0.0:.4f});\n")

    out.append(r"\end{tikzpicture}")
    out.append("")
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────
# FIGURE 3: P-axis Frobenius collapse
# ─────────────────────────────────────────────────────────────────────
def figure3():
    from itertools import product as iproduct

    CRITICAL = {"Phi_c", "Phi_c_complex"}
    BOUNDED_D = {"D_wedge", "D_triangle", "D_holo"}

    def tier(p, omega, d, phi="Phi_c"):
        if phi in CRITICAL and p == "P_pm_sym":
            return "O_inf"
        if phi not in CRITICAL:
            return "O_0"
        if omega == "Omega_0":
            return "O_1"
        if d in BOUNDED_D:
            return "O_2"
        return "O_2d"

    P_VALUES = ["P_asym", "P_psi", "P_pm", "P_sym", "P_pm_sym"]
    P_LABELS = [r"$P_{\mathrm{asym}}$", r"$P_\psi$",
                r"$P_{\pm}$", r"$P_{\mathrm{sym}}$",
                r"$P_{\pm}^{\mathrm{sym}}$ (Frobenius)"]

    # 5 (Omega, D) representative columns
    COLS = [
        ("Omega_0",  "D_wedge",    r"(any $D$)"+"\n"+r"$\Omega_0$"),
        ("Omega_Z2", "D_wedge",    r"$\Omega_{Z_2}$"+"\ bounded $D$"),
        ("Omega_Z2", "D_infty",    r"$\Omega_{Z_2}$"+"\ $D_\infty$"),
        ("Omega_Z",  "D_wedge",    r"$\Omega_{\mathbb{Z}}$"+"\ bounded $D$"),
        ("Omega_Z",  "D_infty",    r"$\Omega_{\mathbb{Z}}$"+"\ $D_\infty$"),
    ]
    TIER_DISPLAY = {
        "O_1":  r"$O_1$",
        "O_2":  r"$O_2$",
        "O_2d": r"$O_2^\dagger$",
        "O_inf":r"$O_\infty$",
    }

    CW  = 2.9
    CH  = 1.65
    HG  = 0.15
    VG  = 0.15
    LM  = 3.8
    TM  = 2.2

    out = []
    out.append(r"% ═══════════════════════════════════════════════════")
    out.append(r"% FIGURE 3 — P-axis Frobenius Collapse")
    out.append(r"% ═══════════════════════════════════════════════════")
    out.append(r"\begin{tikzpicture}[")
    out.append(r"  background rectangle/.style={fill=colbg},")
    out.append(r"  show background rectangle]")
    out.append("")

    total_w = LM + 5*(CW+HG) - HG
    out.append(tikz_node(total_w/2, 0.9,
        r"{\bfseries\large $P$-axis Frobenius Collapse}",
        "white", r"\relax"))
    out.append(tikz_node(total_w/2, 0.3,
        r"$P_{\pm}^{\mathrm{sym}}$ overrides all $\Omega$ and $D$ branching"
        r"\ $\to$\ $O_\infty$ regardless of group",
        "textgray", r"\small"))

    # Column headers
    for j, (_, _, clbl) in enumerate(COLS):
        cx = LM + j*(CW+HG) + CW/2
        # Split label at \n
        parts = clbl.split("\n")
        out.append(tikz_node(cx, -(TM*0.4),
                             parts[0], "white", r"\small\bfseries"))
        if len(parts) > 1:
            out.append(tikz_node(cx, -(TM*0.78),
                                 parts[1], "textgray", r"\fontsize{7}{8}\selectfont"))

    # Rows
    for i, (p_key, p_lbl) in enumerate(zip(P_VALUES, P_LABELS)):
        row_top    = -(TM + i*(CH+VG))
        row_bottom = row_top - CH
        row_mid    = (row_top + row_bottom) / 2

        is_frob = (p_key == "P_pm_sym")

        # Row label
        lbl_color = "colgold" if is_frob else "white"
        out.append(tikz_node(LM - 0.2, row_mid,
                             p_lbl, lbl_color,
                             r"\small\bfseries" if is_frob else r"\small",
                             ", anchor=east"))

        # Highlight box for P_pm_sym row
        if is_frob:
            box_xl = LM - 0.05
            box_xr = LM + 5*(CW+HG) - HG + 0.05
            out.append(f"  \\draw[draw=colgold, fill=none, line width=2pt, rounded corners=2pt] "
                       f"({box_xl:.4f},{row_bottom-0.08:.4f}) rectangle "
                       f"({box_xr:.4f},{row_top+0.08:.4f});\n")

        for j, (omega, d, _) in enumerate(COLS):
            t = tier(p_key, omega, d)
            cl = LM + j*(CW+HG)
            cr = cl + CW
            cb = row_bottom
            ct = row_top

            tcolor = f"col{t.replace('_','').replace('2d','twod').replace('inf','inf')}"
            out.append(tikz_draw_rect(cl, cb, cr, ct, tcolor, "colbg", 0.4))

            tc = "black" if t == "O_1" else "white"
            out.append(tikz_node((cl+cr)/2, (cb+ct)/2,
                                 f"\\bfseries\\normalsize {TIER_DISPLAY[t]}",
                                 tc, r"\relax"))

    # Rules annotation at bottom
    n_rows = len(P_VALUES)
    ann_y = -(TM + n_rows*(CH+VG)) - 0.6
    out.append(tikz_node(total_w/2, ann_y,
        r"R1: $\Phi_c + P_{\pm}^{\mathrm{sym}} \to O_\infty$ (priority\ 1)"
        r"\quad R3: $\Phi_c+\Omega_0 \to O_1$"
        r"\quad R4: bounded $D \to O_2$"
        r"\quad R5: $D_\infty \to O_2^\dagger$",
        "textgray", r"\fontsize{8}{9}\selectfont"))

    # Phantom: balance right/bottom margins
    out.append(f"  \\path ({total_w + 1.2:.4f}, {ann_y - 0.55:.4f});\n")

    out.append(r"\end{tikzpicture}")
    out.append("")
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────
# FIGURE 4: Inner Crystal
# ─────────────────────────────────────────────────────────────────────
def figure4():
    QW  = 5.5   # quad width
    QH  = 2.5   # quad height
    QG  = 0.35  # gap
    LM4 = 1.1   # left margin

    QUADS = [
        # (col, row, color_key, title, prims, size_eq, vals_line1, vals_line2, role)
        (0, 1,  "4472C4",
         "Geometric sub-group",
         r"$T \times R$",
         r"$5 \times 4 = \mathbf{20}$",
         r"$T$: network, in, bowtie, box, $\odot$",
         r"$R$: super, cat, dagger, lr",
         r"Topology $\times$ Relational mode"),

        (1, 1,  "225533",
         "Existence sub-group",
         r"$F \times K$",
         r"$3 \times 4 = \mathbf{12}$",
         r"$F$: $\ell$, $\eth$, $\hbar$",
         r"$K$: fast, mod, slow, trap",
         r"Fidelity $\times$ Kinetics"),

        (0, 0,  "552222",
         "Scope sub-group",
         r"$G \times \Gamma$",
         r"$3 \times 4 = \mathbf{12}$",
         r"$G$: $\beth$, $\gimel$, $\aleph$",
         r"$\Gamma$: and, or, seq, broad",
         r"Granularity $\times$ Interaction grammar"),

        (1, 0,  "442255",
         "Temporal sub-group",
         r"$H \times S$",
         r"$4 \times 3 = \mathbf{12}$",
         r"$H$: $H_0$, $H_1$, $H_2$, $H_\infty$",
         r"$S$: 1:1, $n$:$n$, $n$:$m$",
         r"Temporal depth $\times$ Stoichiometry"),
    ]

    out = []
    out.append(r"% ═══════════════════════════════════════════════════")
    out.append(r"% FIGURE 4 — Inner Crystal")
    out.append(r"% ═══════════════════════════════════════════════════")
    out.append(r"\begin{tikzpicture}[")
    out.append(r"  background rectangle/.style={fill=colbg},")
    out.append(r"  show background rectangle]")
    out.append("")

    total_w  = LM4 + 2*QW + QG
    total_h  = 2*QH + QG
    grid_cx4 = LM4 + (2*QW + QG) / 2

    out.append(tikz_node(grid_cx4, total_h + 1.4,
        r"{\bfseries\large Inner Crystal: 34{,}560 types per tier cell}",
        "white", r"\relax"))
    out.append(tikz_node(grid_cx4, total_h + 0.75,
        r"$34{,}560\ =\ \underbrace{5\times4}_{20\ [T,R]}\ \times"
        r"\ \underbrace{3\times4}_{12\ [F,K]}\ \times"
        r"\ \underbrace{3\times4}_{12\ [G,\Gamma]}\ \times"
        r"\ \underbrace{4\times3}_{12\ [H,S]}$",
        "textgray", r"\normalsize"))

    for (qcol, qrow, bg_hex, title, prims, size_eq,
         vals1, vals2, role) in QUADS:
        xl = LM4 + qcol*(QW+QG)
        yb = qrow*(QH+QG)
        xr = xl + QW
        yt = yb + QH

        # Box — colour name derived from hex (defined in main)
        qname = f"quad{bg_hex}"
        out.append(f"  \\fill[{qname}] "
                   f"({xl:.4f},{yb:.4f}) rectangle ({xr:.4f},{yt:.4f});\n")
        out.append(f"  \\draw[draw=textgray, line width=0.8pt] "
                   f"({xl:.4f},{yb:.4f}) rectangle ({xr:.4f},{yt:.4f});\n")

        cx = (xl+xr)/2
        # Title
        out.append(tikz_node(cx, yt - 0.27, f"\\bfseries\\normalsize {title}",
                             "white", r"\relax"))
        # Prims × size
        out.append(tikz_node(cx, yt - 0.60,
                             f"\\normalsize\\color{{colgold}}{prims}\\ $\\to$\\ {size_eq}",
                             "colgold", r"\relax"))
        # Values
        out.append(tikz_node(cx, yt - 0.95, vals1, "textgray", r"\small"))
        out.append(tikz_node(cx, yt - 1.27, vals2, "textgray", r"\small"))
        # Role
        out.append(tikz_node(cx, yb + 0.25, f"\\textit{{{role}}}",
                             "textgray", r"\small"))

    # Multiplication signs between quads
    for (mx, my) in [
        (LM4 + QW + QG/2,         QH/2),           # right gap, bottom row
        (LM4 + QW + QG/2,         QH + QG + QH/2), # right gap, top row
        (LM4 + QW/2,              QH + QG/2),       # between rows, left col
        (LM4 + QW + QG + QW/2,   QH + QG/2),       # between rows, right col
    ]:
        out.append(tikz_node(mx, my, r"{\LARGE\bfseries$\times$}",
                             "colgold", r"\relax"))

    # Phantoms: left bbox extension (creates left negative space) + right/bottom balance
    out.append(f"  \\path (0.0, {total_h/2:.4f});\n")           # left edge at x=0
    out.append(f"  \\path ({total_w + 1.0:.4f}, {-0.45:.4f});\n")  # right + bottom

    out.append(r"\end{tikzpicture}")
    out.append("")
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────
# Assemble and write
# ─────────────────────────────────────────────────────────────────────
# Map colour names to safe TikZ names
COLOR_MAP = {
    "O_0":   "colO0",
    "O_1":   "colO1",
    "O_2":   "colO2",
    "O_2d":  "colO2d",
    "O_inf": "colOinf",
}

def remap_colors(s):
    """Replace colOxx references with the correct definecolor names."""
    replacements = [
        ("colO0",        "colOzero"),
        ("colO1",        "colOone"),
        ("colO2d",       "colOtwod"),
        ("colO2",        "colOtwo"),
        ("colOinf",      "colOinf"),
        ("colOinf",      "colOinf"),
    ]
    for old, new in replacements:
        s = s.replace(old, new)
    return s

def main():
    # Color definitions (safe names)
    color_defs = [
        r"\definecolor{colbg}{HTML}{0F0F1A}",
        r"\definecolor{colbg2}{HTML}{1A1A2E}",
        r"\definecolor{colOzero}{HTML}{4472C4}",   # O_0 steel blue
        r"\definecolor{colOone}{HTML}{FFD700}",    # O_1 gold
        r"\definecolor{colOtwo}{HTML}{FF8C00}",    # O_2 dark orange
        r"\definecolor{colOtwod}{HTML}{DC143C}",   # O_2† crimson
        r"\definecolor{colOinf}{HTML}{9370DB}",    # O_inf purple
        r"\definecolor{colgold}{HTML}{FFD700}",
        r"\definecolor{textgray}{HTML}{AAAACC}",
        r"\definecolor{dimgray}{HTML}{666688}",
        # Inner-crystal quad backgrounds (Figure 4)
        r"\definecolor{quad4472C4}{HTML}{4472C4}",   # Geometric — steel blue
        r"\definecolor{quad225533}{HTML}{225533}",   # Existence — dark green
        r"\definecolor{quad552222}{HTML}{552222}",   # Scope     — dark red
        r"\definecolor{quad442255}{HTML}{442255}",   # Temporal  — dark purple
    ]

    tex = []
    tex.append(r"\documentclass[tikz,border=10pt]{standalone}")
    tex.append(r"\usepackage{amsmath,amssymb}")
    tex.append(r"\usetikzlibrary{backgrounds}")
    tex.append(r"\begin{document}")
    tex.extend(color_defs)
    tex.append("")

    # Build figures (with internal colour references using temporary names)
    figs_raw = [figure1(), figure2(), figure3(), figure4()]

    # Fix colour references: replace colO0/colO1 etc with colOzero/colOone etc
    def fix_tier_colors(s):
        # Must fix longest matches first (O_2d before O_2)
        s = s.replace("colO0",  "colOzero")
        s = s.replace("colO2d", "colOtwod")
        s = s.replace("colO2",  "colOtwo")
        s = s.replace("colO1",  "colOone")
        s = s.replace("colOinf","colOinf")
        return s

    for fig in figs_raw:
        tex.append(fix_tier_colors(fig))

    tex.append(r"\end{document}")

    content = "\n".join(tex)
    OUT.write_text(content)
    print(f"Written: {OUT}")
    print(f"Compile: pdflatex {OUT.name}")


if __name__ == "__main__":
    main()
