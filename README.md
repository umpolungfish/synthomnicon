# SynthOmnicon

**A 12-primitive constraint grammar for the structural encoding of physical, mathematical, and biological systems.**

---

## Primitive Space

The grammar encodes any system as a 12-tuple $\langle D;T;R;P;F;K;G;\Gamma;\Phi;H;S;\Omega \rangle$ spanning dimensionality, topology, recognition, polarity, fidelity, kinetics, granularity, logical structure, criticality, chirality, stoichiometry, and symmetry breaking. 318 catalog entries spanning physics, biology, mathematics, and cosmology are projected into primitive space via Classical MDS over Hamming distance.

### SynthOmnicon Reference Sheet

![SynthOmnicon Reference Sheet](SYNCON_REF.png)

---

## The Three-Projection Framework

The grammar ($\pi_1$) is one of three irreducible projections of a fundamental information substrate $\mathcal{I}$:

| Projection | Mode | Encodes |
|---|---|---|
| $\pi_1$ (structural) | Grammar | Topological invariants — *what kind* |
| $\pi_2$ (energetic) | Continuous | Real-valued exchange — *how much* |
| $\pi_3$ (ouroboricity) | Closure | Scaling invariants — *how it closes on itself* |

Inter-projection constraint maps $\mathcal{C}_{ij}$ define what values in projection $j$ are compatible with a given value in projection $i$. Every Millennium Prize Problem is a constraint map problem:

- **RH**: prove $\mathcal{C}_{13}(\Phi_c^{\mathbb{C}}, P_\text{neutral}) = \{ \Re(s) = \tfrac{1}{2} \}$
- **Yang-Mills**: prove $\mathcal{C}_{12}(K_\text{trap}, G_\aleph, \Phi_c) \subseteq [\Delta_\text{min}, \infty)$
- **Navier-Stokes**: prove $\mathcal{C}_{12}(\Phi_\text{sub}, D_\text{cube}, K_\text{mod}) \subseteq \{E(t) < \infty\}$

Lee-Yang (1952) is the unique proved instance of $\mathcal{C}_{13}$ and serves as the template for all constraint-map proof strategies.

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

---

## Citation

If you use SynthOmnicon in your research, please cite:

```
Mills, L. (2026). On the Structural Non-Transmissibility of Mochizuki's
Inter-Universal Geometer. Preprint.
```

---

## Repository Structure

```
syncon_catalog.json          — 318 encoded systems
syncon_inquiry.py            — Interactive query interface
syncon_primitive_map.py      — Visualization (MDS + network)
space_search/
  primitives.py              — Ordinal maps for all 12 primitives
PRIMITIVE_PREDICTIONS.md     — 155 predictions (P-1 — P-155)
SYNTHONICON_DIAPHORICS.md    — Domain encoding compendium
SYNTHONICON_ONTICS.md        — Ontological foundations
PRIMITIVE_THEOREMS.md        — Formal theorems §1–§23
```

The Lean 4 formalization lives in the companion repository **MilleniumAnkh**, which provides machine-checked encodings of all seven Millennium Prize Problems and a formal primitive bridge connecting grammar structure to barrier classification.

---

## Key Results

- **P-150**: Lee-Yang zero locus derived as $\mathcal{C}_{13}(\Phi_c^{\mathbb{C}}, P_{\pm}^{\text{sym}})$ — the only known proved non-trivial constraint map instance ✅
- **P-149**: Ouroboricity $\mathcal{O} \geq 3$ is necessary for modeling completeness of $\mathcal{O}_2$ systems (structural Gödel)
- **P-70**: Inflaton $\equiv$ Higgs $\equiv$ axion — three-scale $K_\text{slow}$ identity
- **Theorem 001–005**: Consciousness encoding; stellar phenomenology; cosmological arc as experience
- **RH–Lee-Yang correspondence** (machine-checked in Lean): shared $\Phi_c^{\mathbb{C}}$ encoding; structural distance 5; $P$ mismatch identified as the key gap

*See `PRIMITIVE_PREDICTIONS.md` for the full prediction archive.*
