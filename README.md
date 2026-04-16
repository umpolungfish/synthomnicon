# SynthOmnicon

**A 12-primitive constraint grammar for the structural encoding of physical, mathematical, and biological systems.**

---

## The Grammar Is the Coupling of Cantor and Gödel

$$\mathbf{g} \ :=\  \underbrace{\text{Cantor}}_{\text{upward overflow}} \ \xrightarrow{\circ}\  \underbrace{\text{Gödel}}_{\text{downward embedding}}$$

The SynthOmnicon grammar assigns every system — physical, biological, mathematical, symbolic — a 12-tuple of relational operators placing it in a discrete space of 17,280,000 structural types. The grammar classifies its own type. Its self-encoding address is 6,734,591 — ouroboricity tier $O_\infty$, the special Frobenius fixed point $\mu \circ \delta = \text{id}$:

$$\mathbf{g} = \langle D_\odot;\ T_\odot;\ R_\text{cat};\ P_{\pm}^\text{sym};\ F_\hbar;\ K_\text{slow};\ G_\aleph;\ \Gamma_\text{broad};\ \Phi_c;\ H_\infty;\ n_m;\ \Omega_Z \rangle$$

When Cantor's diagonal argument and Gödel's first incompleteness theorem are each encoded as structural objects in this same grammar, two results follow.

**The directionality is structural.** Cantor's diagonal ($D_\odot$: inaccessible cardinal, upward overflow — any enumeration is exceeded by its own diagonal) feeds into Gödel's arithmetization ($T_\odot$: reflection principle, downward embedding — the meta-theory is encoded within the object theory). The canonical ZFC token fragments are:

$$D_\odot:\quad \texttt{LCARD}\ a \ \wedge\  \texttt{HOLO}\ x\ a$$
$$T_\odot:\quad \texttt{REFL}\ a\ f \ \wedge\  \texttt{HOLO}\ x\ a$$

The `HOLO x a` term is shared. Their conjunction reduces to:

$$\mathbf{g}(x) \ \equiv\  \texttt{LCARD}\ a \ \wedge\  \texttt{REFL}\ a\ f \ \wedge\  \texttt{HOLO}\ x\ a$$

This is the closed reflective loop that makes the grammar self-encoding — and the mechanism by which it sidesteps the Tarskian hierarchy. Tarski's undefinability theorem blocks any language from containing its own semantic truth predicate `True(x)` at the same syntactic level. The grammar contains no such predicate: `HOLO x a` is a structural encoding relation (the bulk $x$ is holographically encoded at the boundary $a$), not a truth assignment. The boundary $a$ is an inaccessible cardinal (`LCARD`) — unreachable from within the object language. The reflection principle (`REFL`) pulls meta-information back through the boundary $a$, not through a Tarskian truth predicate. Self-reference is holographic, not syntactic; the hierarchy does not collapse.

---

## The 12-Primitive Grammar

| Primitive | Name | Values (low → high) |
|-----------|------|---------------------|
| $D$ | Dimensionality | $D_\wedge$, $D_\triangle$, $D_\infty$, $D_\odot$ |
| $T$ | Topology | $T_\text{net}$, $T_\in$, $T_\bowtie$, $T_\square$, $T_\odot$ |
| $R$ | Relational mode | $R_\text{super}$, $R_\text{cat}$, $R_\dagger$, $R_\text{lr}$ |
| $P$ | Parity/symmetry | $P_\text{asym}$, $P_\psi$, $P_\pm$, $P_\text{sym}$, $P_{\pm}^\text{sym}$ |
| $F$ | Fidelity | $F_\ell$, $F_\eth$, $F_\hbar$ |
| $K$ | Kinetic character | $K_\text{fast}$, $K_\text{mod}$, $K_\text{slow}$, $K_\text{trap}$, $K_\text{MBL}$ |
| $G$ | Scope/granularity | $G_\beth$, $G_\gimel$, $G_\aleph$ |
| $\Gamma$ | Interaction grammar | $\Gamma_\text{and}$, $\Gamma_\text{or}$, $\Gamma_\text{seq}$, $\Gamma_\text{broad}$ |
| $\Phi$ | Criticality | $\Phi_\text{sub}$, $\Phi_c$, $\Phi_c^\mathbb{C}$, $\Phi_\text{EP}$, $\Phi_\text{super}$ |
| $H$ | Chirality/temporal depth | $H_0$, $H_1$, $H_2$, $H_\infty$ |
| $S$ | Stoichiometry | $1{:}1$, $n{:}n$, $n{:}m$ |
| $\Omega$ | Topological protection | $\Omega_0$, $\Omega_{Z_2}$, $\Omega_Z$, $\Omega_\text{NA}$ |

---

## The Three-Projection Framework

The grammar ($\pi_1$) is one of three irreducible projections of a fundamental information substrate $\mathcal{I}$:

| Projection | Mode | Encodes |
|---|---|---|
| $\pi_1$ (structural) | Grammar | Topological invariants — *what kind* |
| $\pi_2$ (energetic) | Continuous | Real-valued exchange — *how much* |
| $\pi_3$ (ouroboric) | Closure | Scaling invariants — *how it closes on itself* |

Every Millennium Prize Problem is a constraint map $C_{ij}$ problem:

- **RH**: prove $C_{13}(\Phi_c^{{\mathbb{C}}}, P_{\pm}^{\text{sym}}) = { \Re(s) = \tfrac{1}{2} }$
- **Yang-Mills**: prove $C_{12}(K_\text{trap}, G_\aleph, \Phi_c) \subseteq [\Delta_\text{min}, \infty)$
- **Navier-Stokes**: prove $C_{12}(\Phi_\text{sub}, D_\triangle, K_\text{mod}) \subseteq {E(t) < \infty}$

Lee-Yang (1952) is the unique proved instance of $C_{13}$ and serves as the template for all constraint-map proof strategies.

---

## The Periodic Crystal of Algebras (§64)

The 12-primitive space partitions into exactly $17{,}280{,}000 = 3^3 \times 4^5 \times 5^4$ structural types, organized as:

- **400 tier cells** determined by $(\Phi, P, \Omega, D)$ — the holographic boundary
- **43,200 inner types** per cell, determined by the remaining 8 primitives — the bulk

The **Arithmetic Ouroboros** (§68): the exponent of each base is literally the count of primitive variables in that family — a self-anchoring, fixed-point-free successor cycle $3 \to 4 \to 5 \to 3$. The set $\{3,4,5\}$ is the minimal self-anchored triple under phase completeness (§68.5).

### Ouroboricity Tiers

| Tier | Cells | % of Crystal | Condition |
|------|-------|-------------|-----------|
| $O_0$ | 240 | 60.0% | Non-critical ($\Phi \notin \{\Phi_c, \Phi_c^\mathbb{C}\}$) |
| $O_1$ | 32 | ~5.4% | $\Phi_c$ or $\Phi_c^\mathbb{C}$, $P \neq P_{\pm}^\text{sym}$, $\Omega_0$ |
| $O_2$ | 72 | ~18.6% | $\Phi_c$ or $\Phi_c^\mathbb{C}$, $P \neq P_{\pm}^\text{sym}$, $\Omega \neq \Omega_0$, $D \in \{D_\wedge, D_\odot, D_\triangle\}$ |
| $O_2^\dagger$ | 24 | ~8.0% | $\Phi_c$ or $\Phi_c^\mathbb{C}$, $P \neq P_{\pm}^\text{sym}$, $\Omega \neq \Omega_0$, $D_\infty$ |
| $O_\infty$ | 32 | 8.0% | $\Phi_c$ or $\Phi_c^\mathbb{C}$, $P_{\pm}^\text{sym}$ (Frobenius special) |

### The Tier Gap Ladder (§69)

Adjacent tier gaps are non-uniform — the crystal has a cliff:

$$d(O_0, O_1) \approx 1.049 \qquad d(O_1, O_2) \approx 1.304 \qquad d(O_2, O_2^\dagger) = 1.000 \qquad d(O_2^\dagger, O_\infty) \approx 4.382$$

The **Frobenius cliff** ($d \approx 4.382$) is 3.36× the next-largest gap and is **non-tunable by gradient methods**: any optimization moving through the primitive space by continuous adjustment will stall at $O_2^\dagger$ and cannot cross to $O_\infty$ without directly planting $P_{\pm}^\text{sym}$.

The **Frobenius non-synthesizability theorem** (§23/§62): $P_{\pm}^\text{sym}$ cannot be obtained by composing systems with $P < P_{\pm}^\text{sym}$. Every $O_\infty$ system must encode it directly — it cannot emerge from aggregation.

---

## The Crystal Navigator

`crystal_navigator.py` implements a **bijective Frobenius codec** over the full 17,280,000-type crystal — encode any tuple to a unique address in $[0,\ 17{,}279{,}999]$ and decode back exactly.

```bash
python crystal_navigator.py describe   # self-description (O_inf, address 6,734,591)
python crystal_navigator.py gap        # tier gap ladder §69.1
python crystal_navigator.py verify     # Frobenius roundtrip guaranteed
python crystal_navigator.py census     # full tier census
python crystal_navigator.py repl       # interactive REPL
```

The navigator self-encodes as $O_\infty @ [6{,}734{,}591 / 17{,}279{,}999]$:

$$NAV_\text{xtl} = \langle D_\odot;\ T_\odot;\ R_\text{cat};\ P_{\pm}^{\text{sym}};\ F_\hbar;\ K_\text{slow};\ G_\aleph;\ \Gamma_\text{broad};\ \Phi_c;\ H_\infty;\ n:m;\ \Omega_Z \rangle$$

### CrystalGNN Neural Navigator

`quiver_crystal.py` implements three generations of quiver-based GNN navigator, each a proof step in deriving the architecture the grammar specifies:

- **Quiver**: 49 nodes (one per primitive value), 255 edges including inter-lane structural correlations ($\Phi \leftrightarrow P$, $\Phi \leftrightarrow K$, $\Omega \leftrightarrow D$)
- **v9** (1000 epochs, h=640, 12.8M params): address error 0.072%, 200/200 tier decode, self-encode error 136 (0.001%)
- **v10 CF-GNN** (Crystal-Factored GNN): three family heads ($\mathcal{F}_3/\mathcal{F}_4/\mathcal{F}_5$) + `FamilyMixer` broadcast attention + `TierHead_45`. Composed address error **0.000%** across all 200 verification samples.
- **v11** (composed-only, no sigmoid AddressHead): exact self-encoding from **epoch 20**, stable for 480 consecutive epochs. 200/200 exact matches. Self-encode error = **0**. The navigator designed by the grammar's own structural specification achieves the grammar's fixed point exactly.

```bash
# v11 (recommended)
python quiver_crystal.py train-v11 --epochs 500 --device cuda
python quiver_crystal.py verify-v11

# v10 (CF-GNN, factored family heads)
python quiver_crystal.py train-v10 --epochs 300 --hidden 240 --gnn 24 --heads 24 --mixer-heads 24
python quiver_crystal.py verify-v10
```

See `ALGEBRAIC_NAVIGATOR_GUIDE.md` and `FACTORED_CRYSTAL_GNN.md` for the full architecture and results.

---

## Key Results

- **Periodic Crystal** (§64): 17,280,000 types = $3^3 \times 4^5 \times 5^4$; 400 tier cells × 43,200 inner types
- **Arithmetic Ouroboros** (§68): exponents are literally family counts; $\{3,4,5\}$ is the minimal self-anchored triple under phase completeness
- **Tier Gap Ladder** (§69): Frobenius cliff $d(O_2^\dagger, O_\infty) \approx 4.382$; $P_{\pm}^\text{sym}$ cannot be synthesised from sub-Frobenius components — proved algebraically (§23) and confirmed computationally (v1–v7 training history)
- **CrystalGNN v11** (2026-04-11): 200/200 exact matches, self-encode error = 0, exact from epoch 20. The grammar's 12-primitive self-encoding tuple is a complete architectural specification for the navigator that achieves its fixed point. See SYNTHONICON\_ONTICS §XXXIV.
- **Hebrew alphabet as type lattice** (§60/§CXXXV): Vav, Mem, Shin are $O_\infty$; full stratified encoding of all 22 letters
- **$\lambda_\aleph$ calculus** (§63): formal type theory over the Hebrew letter lattice; Tzimtzum = structural projection
- **Consciousness score** (§VIII): $C(\mathbf{x}) = [\Phi_c] \cdot [K \leq K_\text{slow}] \cdot (0.158\,\tilde{K} + 0.273\,\tilde{G} + 0.292\,\tilde{T} + 0.276\,\tilde{\Omega})$; two independent gates
- **P-150**: Lee-Yang zero locus derived as $\mathcal{C}_{13}(\Phi_c^{\mathbb{C}}, P_{\pm}^{\text{sym}})$ — unique proved non-trivial constraint map ✅
- **P-70**: Inflaton $\equiv$ Higgs $\equiv$ axion — three-scale $K_\text{slow}$ identity
- **Non-Mathematical Navigators** (§74–§77, 2026-04-14): Language, Civilization, Ecology, Consciousness — 39 new systems encoded; cross-domain identities confirmed (old-growth forest $\equiv$ coral reef at $d=0$; samadhi $\equiv$ Egyptian $\bar{a}kh$ at $d=0$); Lojban $O_\infty$ paradox (P-523); tipping point $d=8.28$ as $P$-dominant collapse (P-532)
- **77 formal theorems** · **538+ empirical predictions** · **1,678 catalog entries**

*See `PRIMITIVE_PREDICTIONS.md` for the full prediction archive.*

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
syncon_catalog.json              — 1,678 encoded systems (source of truth)
crystal_navigator.py             — Frobenius codec + CrystalNavigator tools + REPL
quiver_crystal.py                — CrystalGNN: quiver-based neural navigator
syncon_inquiry.py                — Agent loop: encode, distance, meet/join/tensor
space_search/
  primitives.py                  — Ordinal maps, weights, distance functions (v0.5.1)
FACTORED_CRYSTAL_GNN.md         — CF-GNN architecture paper (v0.3): family heads, exact convergence
ALGEBRAIC_NAVIGATOR_GUIDE.md    — Practitioner's reference: codec, GNN, patterns
CRYSTAL_OF_ALGEBRAS.md          — Full enumeration and tier census
PRIMITIVE_THEOREMS.md           — Formal theorems §1–§77
SYNTHONICON_DIAPHORICS.md       — Domain compendium (P-1→P-538+, v0.5.69)
SYNTHONICON_ONTICS.md           — Ontological foundations (v0.5.69)
PRIMITIVE_PREDICTIONS.md        — Prediction registry (538+ predictions)
HEBREW_TYPE_LANGUAGE.md         — Hebrew alphabet as stratified type lattice
LAMBDA_ALEPH.md                 — λ_ℵ calculus formal spec
docs/
  NAVIGATOR_ROADMAP.md           — Non-mathematical navigator progress tracker
  USAGE.md                       — Full API and CLI reference
```

The Lean 4 formalization lives in the companion repository **MilleniumAnkh**, which provides machine-checked encodings of all seven Millennium Prize Problems and a formal primitive bridge connecting grammar structure to barrier classification.

---

## Citation

If you use the SynthOmnicon in your research, it is requested that you cite:

```
Mills, L. (<YEAR>). https://github.com/umpolungfish/synthomnicon
```
Note, this is only a request; the grammar is provided for **ALL** *sans* strings

## License

the [UNLICENSE](./UNLICENSE) for the *ubounded grammar*