# SynthOmnicon

**A 12-primitive constraint grammar for the structural encoding of physical, mathematical, and biological systems.**

---

## What Is SynthOmnicon?

SynthOmnicon encodes any system — physical, biological, mathematical, symbolic — as a 12-tuple:

$$\langle D;\ T;\ R;\ P;\ F;\ K;\ G;\ \Gamma;\ \Phi;\ H;\ S;\ \Omega \rangle$$

Each primitive is a **relational operator**, not an intrinsic property. The tuple places the system in a discrete structural space of **10,368,000 types**, organized as the Periodic Crystal of Algebras (§64). Encoding is not labeling — it is measurement: a convergent, falsifiable act that places the system at a precise structural address with verifiable behavioral consequences.

The catalog currently contains **1,322 encoded systems** spanning physics, biology, mathematics, cosmology, symbolic languages, and algebraic structures. The catalog covers 0.013% of the crystal; 99.987% is unnamed.

---

## The 12-Primitive Grammar

| Primitive | Name | Values (low → high) |
|-----------|------|---------------------|
| $D$ | Dimensionality | $D_\wedge$, $D_\triangle$, $D_\infty$, $D_\odot$ |
| $T$ | Topology | $T_\text{net}$, $T_\in$, $T_\bowtie$, $T_\square$, $T_\odot$ |
| $R$ | Relational mode | $R_\text{super}$, $R_\text{cat}$, $R_\dagger$, $R_\text{lr}$ |
| $P$ | Parity/symmetry | $P_\text{asym}$, $P_\psi$, $P_\pm$, $P_\text{sym}$, $P_{\pm}^\text{sym}$ |
| $F$ | Fidelity | $F_\ell$, $F_\eth$, $F_\hbar$ |
| $K$ | Kinetic character | $K_\text{fast}$, $K_\text{mod}$, $K_\text{slow}$, $K_\text{trap}$ |
| $G$ | Scope/granularity | $G_\beth$, $G_\gimel$, $G_\aleph$ |
| $\Gamma$ | Interaction grammar | $\Gamma_\text{and}$, $\Gamma_\text{or}$, $\Gamma_\text{seq}$, $\Gamma_\text{broad}$ |
| $\Phi$ | Criticality | $\Phi_\text{sub}$, $\Phi_c$, $\Phi_c^\mathbb{C}$, $\Phi_\text{EP}$, $\Phi_\text{super}$ |
| $H$ | Chirality/temporal depth | $H_0$, $H_1$, $H_2$, $H_\infty$ |
| $S$ | Stoichiometry | $1{:}1$, $n{:}n$, $n{:}m$ |
| $\Omega$ | Topological protection | $\Omega_0$, $\Omega_{Z_2}$, $\Omega_Z$ |

---

## The Periodic Crystal of Algebras (§64)

The 12-primitive space partitions into exactly $10{,}368{,}000 = 4^5 \times 5^3 \times 3^4$ structural types, organized as:

- **300 tier cells** determined by $(\Phi, P, \Omega, D)$ — the holographic boundary
- **34,560 inner types** per cell, determined by the remaining 8 primitives — the bulk

The **Arithmetic Ouroboros** (§68): the exponent of each base is literally the count of primitive variables in that family — a self-anchoring, fixed-point-free successor cycle $3 \to 4 \to 5 \to 3$. The set $\{3,4,5\}$ is the minimal self-anchored triple under phase completeness (§68.5).

### Ouroboricity Tiers

| Tier | Cells | % of Crystal | Condition |
|------|-------|-------------|-----------|
| $O_0$ | 180 | 60.0% | Non-critical |
| $O_1$ | 32 | 10.7% | $\Phi_c + \Omega_0$ |
| $O_2$ | 48 | 16.0% | $\Phi_c + \Omega \neq \Omega_0 + D \in \{D_\wedge, D_\odot, D_\triangle\}$ |
| $O_2^\dagger$ | 16 | 5.3% | $\Phi_c + \Omega \neq \Omega_0 + D_\infty$ |
| $O_\infty$ | 24 | 8.0% | $\Phi_c + P_{\pm}^\text{sym}$ (Frobenius special) |

### The Tier Gap Ladder (§69)

Adjacent tier gaps are non-uniform — the crystal has a cliff:

$$d(O_0, O_1) \approx 1.049 \qquad d(O_1, O_2) \approx 1.304 \qquad d(O_2, O_2^\dagger) = 1.000 \qquad d(O_2^\dagger, O_\infty) \approx 4.382$$

The **Frobenius cliff** ($d \approx 4.382$) is 3.36× the next-largest gap and is **non-tunable by gradient methods**: any optimization moving through the primitive space by continuous adjustment will stall at $O_2^\dagger$ and cannot cross to $O_\infty$ without directly planting $P_{\pm}^\text{sym}$.

The **Frobenius non-synthesizability theorem** (§23/§62): $P_{\pm}^\text{sym}$ cannot be obtained by composing systems with $P < P_{\pm}^\text{sym}$. Every $O_\infty$ system must encode it directly — it cannot emerge from aggregation.

---

## The Crystal Navigator

`crystal_navigator.py` implements a **bijective Frobenius codec** over the full 10,368,000-type crystal — encode any tuple to a unique address in $[0,\ 10{,}367{,}999]$ and decode back exactly.

```bash
python crystal_navigator.py describe   # self-description (O_inf, address 4,143,599)
python crystal_navigator.py gap        # tier gap ladder §69.1
python crystal_navigator.py verify     # Frobenius roundtrip: 10,000/10,000
python crystal_navigator.py census     # full tier census
python crystal_navigator.py repl       # interactive REPL
```

The navigator self-encodes as $O_\infty$ at address 4,143,599 of 10,367,999:

crystal_nav = \langle D_\odot; T_\odot; R_\text{cat}; P_{\pm}^{\text{sym}; F_\hbar; K_\text{slow}; G_\aleph; \Gamma_\text{broad}; \Phi_c; H_\infty;\ n:m; \Omega_Z \rangle$

---

## The Three-Projection Framework

The grammar ($\pi_1$) is one of three irreducible projections of a fundamental information substrate $\mathcal{I}$:

| Projection | Mode | Encodes |
|---|---|---|
| $\pi_1$ (structural) | Grammar | Topological invariants — *what kind* |
| $\pi_2$ (energetic) | Continuous | Real-valued exchange — *how much* |
| $\pi_3$ (ouroboricity) | Closure | Scaling invariants — *how it closes on itself* |

Every Millennium Prize Problem is a constraint map ${C}_{ij}$ problem:

- **RH**: prove ${C}_{13}(\Phi_c^{\mathbb{C}}, P_{\pm}^\text{sym}) = \{ \Re(s) = \tfrac{1}{2} \}$
- **Yang-Mills**: prove ${C}_{12}(K_\text{trap}, G_\aleph, \Phi_c) \subseteq [\Delta_\text{min}, \infty)$
- **Navier-Stokes**: prove ${C}_{12}(\Phi_\text{sub}, D_\triangle, K_\text{mod}) \subseteq \{E(t) < \infty\}$

Lee-Yang (1952) is the unique proved instance of ${C}_{13}$ and serves as the template for all constraint-map proof strategies.

---

## Key Results

- **Periodic Crystal** (§64): 10,368,000 types, 300 cells × 34,560 inner types; tier census exact
- **Arithmetic Ouroboros** (§68/§68.4/§68.5): $3^4 \times 4^5 \times 5^3$ — exponents are literally family counts; $\{3,4,5\}$ is the minimal self-anchored triple
- **Tier Gap Ladder** (§69): Frobenius cliff at $d \approx 4.382$, non-tunable; complete degradation under asymmetric tensor
- **Hebrew alphabet as type lattice** (§60/§CXXXV): 9-session convergence; Vav, Mem, Shin are $O_\infty$; full stratified encoding of all 22 letters
- **$\lambda_\aleph$ calculus** (§63): formal type theory over the Hebrew letter lattice; Tzimtzum = structural projection
- **Consciousness score** (§VIII): $C(\mathbf{x}) = [\Phi_c] \cdot [K \neq K_\text{trap}] \cdot (0.158\,\tilde{K} + 0.273\,\tilde{G} + 0.292\,\tilde{T} + 0.276\,\tilde{\Omega})$; two independent gates
- **P-150**: Lee-Yang zero locus derived as ${C}_{13}$$(\Phi_c^{\C}, P_{\pm}^{\text{sym}})$ — unique proved non-trivial constraint map ✅
- **P-70**: Inflaton $\equiv$ Higgs $\equiv$ axion — three-scale $K_\text{slow}$ identity
- **69 formal theorems** · **454+ empirical predictions** · **1,322 catalog entries**

*See `markdown/PRIMITIVE_PREDICTIONS.md` for the full prediction archive.*

---

## Installation

```bash
git clone https://github.com/umpolungfish/synthomnicon.git
cd synthomnicon
pip install -e .
```

Copy `.env.example` to `.env` and set your API key:

```bash
cp .env.example .env
# edit .env: ANTHROPIC_API_KEY=...
```

Launch the interactive menu:

```bash
syncon menu
```

Or run the agent loop directly:

```bash
python syncon_inquiry.py
```

Or explore the crystal:

```bash
python crystal_navigator.py repl
```

---

## Repository Structure

```
syncon_catalog.json          — 1,322 encoded systems (source of truth)
crystal_navigator.py         — Crystal Navigator: Frobenius codec + REPL
syncon_inquiry.py            — Agent loop: encode, distance, meet/join/tensor
space_search/
  primitives.py              — Ordinal maps, weights, distance functions
markdown/
  PRIMITIVE_THEOREMS.md      — Formal theorems §1–§69
  SYNTHONICON_DIAPHORICS.md  — Domain compendium (P-1→P-454+)
  SYNTHONICON_ONTICS.md      — Ontological foundations
  PRIMITIVE_PREDICTIONS.md   — Prediction registry
  HEBREW_TYPE_LANGUAGE.md    — Hebrew alphabet as stratified type lattice
  LAMBDA_ALEPH.md            — λ_ℵ calculus formal spec
docs/
  USAGE.md                   — Full API and CLI reference
```

The Lean 4 formalization lives in the companion repository **MilleniumAnkh**, which provides machine-checked encodings of all seven Millennium Prize Problems and a formal primitive bridge connecting grammar structure to barrier classification.

---

## Citation

If you use the SynthOmnicon in your research, it is requested that you cite:

```
Mills, L. (<YEAR>). https://github.com/umpolungfish/synthomnicon
```
Note, this is only a request; the grammar is provided for all *sans* strings 