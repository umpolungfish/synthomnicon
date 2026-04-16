# SynthOmnicon — Index

*SynthOmnicon v0.4.46 · 12-primitive constraint algebra · Framework reference*

---

## Core Documents

These files are the canonical reference for the Synthonicon grammar and the Millennium barrier paper.

| File | Content |
| :--- | :--- |
| **[SYNTHONICON_TOPICS.md](SYNTHONICON_TOPICS.md)** | Formal grammar: 12 primitives, 7 axioms, composition operations, primitive space |
| **[SYNTHONICON_DIAPHORICS.md](SYNTHONICON_DIAPHORICS.md)** | Relational catalog: system encodings, distance matrices, cross-domain results, Millennium Problems |
| **[SYNTHONICON_ONTICS.md](SYNTHONICON_ONTICS.md)** | Ontological implications: consciousness theorems, cosmological arc, G-scope, generator recognition |
| **[SYNTHONICON_LANG.md](SYNTHONICON_LANG.md)** | Typed language for matter: Phase 3 grammar, compiler design, substrate expressions |
| **[SYNTHONICON_PRIMER.md](SYNTHONICON_PRIMER.md)** | Reader guide: first-principles introduction, tool overview, `syncon_inquiry.py` usage |
| **[PRIMITIVE_PREDICTIONS.md](PRIMITIVE_PREDICTIONS.md)** | Living ledger of predictions derived from primitive assignments (P-001 → P-114+) |
| **[PRIMITIVE_THEOREMS.md](PRIMITIVE_THEOREMS.md)** | Archive of primitive-derived theorems (confidence tiers, three-plane annotations) |
| **[THREE_PLANE_DEMONSTRATION.md](THREE_PLANE_DEMONSTRATION.md)** | Pedagogical example: Topics/Diaphorics/Ontics partition for a single system |
| **[MILLENNIUM_BARRIERS_PAPER.md](MILLENNIUM_BARRIERS_PAPER.md)** | Research paper: formal barrier taxonomy for Millennium Prize Problems in Lean 4 (v0.1.0) |

---

## Core Tools

| File | Purpose |
| :--- | :--- |
| **`syncon_inquiry.py`** | Two-phase agentic loop: grammatical analysis + speculation pass |
| **`synthon_tool.py`** | Primitive encoding, distance, meet/join, tensor operations |
| **`synthon_agent.py`** | Autonomous synthon generation agent |
| **`main.py`** | Primary entry point |
| **`syncon_catalog.json`** | Active synthon catalog (61 entries, inc. Millennium Problems) |

---

## Subdirectories

### `reports/`
Standalone analyses and papers.
- `IUG_NON_TRANSMISSIBILITY.md` / `.pdf` — structural non-transmissibility of Inter-Universal Geometer (12 sections, P-112/113/114)
- `REACTIONLESS_THRUST.md` / `.pdf` — reactionless thrust analysis
- `TENSOR_OPS.md` / `.pdf` — tensor operations reference
- `PROOF.md` — fossil record and synthon propagation
- `CHEMRXIV_OUTLINE.md` — ChemRxiv paper outline
- `SYNOPSIS.md` — framework overview
- Finance: `INVESTMENT_MEMORANDUM.md`, `PITCH_DECK.md`, `QUANTITATIVE_ROADMAP.md`, `EXTENDED_BACKTEST_REPORT.md`, `INSTITUTIONAL_BACKTEST_REPORT.md`, `PARAMETER_SWEEP_REPORT.md`, `TRADER_ONEPAGER.md`, `INFORMATIONAL_COST_ANALYSIS.md`
- Misc analyses: `CLU.md`, `ESOP.md`, `FORMOM.md`, `HOLOCOMP.md`, `SYNCON_SUGGESTED.md`

### `research/`
Domain research papers and applications.
- `METAPHYSICS.md` / `.pdf` — philosophical companion to the grammar
- `PROTEINS.md` — protein folding and drug design applications
- `EPILEPSY.md` — neural constraint analysis
- `MYXOZOANS.MD` — parasitic organism analysis
- `PROGRAMMABLE_MATTER.md` — programmable matter synthon catalog
- `PROGRAMMABLE_MIND.md` — mind-programming framework
- `SOLAR.md` — solar/energy domain analysis
- `THE_SELF-MADE_ARCHITECTONICS.md` — architectural analysis
- `SYNTHONICON.md` / `.pdf` — legacy main document (superseded by three-doc architecture)

### `applications/`
Synthonic operations and specialized capabilities.
- `SYNTHONIC_CROSS_DOMAIN.md` — cross-domain constraint propagation
- `SYNTHONIC_ENSEMBLER.md` — ensemble synthon operations
- `SYNTHONIC_HOTSWAP.md` — dynamic primitive substitution
- `SYNTHONIC_PERTURBATION.md` — perturbation analysis
- `SYNTHONIC_RETRODESIGN.md` — retrosynthetic design
- `SYNTHONIC_TRAJECTORY.md` — trajectory through primitive space
- `SYNTHONICON_PHASE_TRANSITION_DETECTOR.md` — phase transition detection
- `AUTONOMOUS_DISCOVERY.md` / `_SUMMARY.md` — autonomous discovery results

### `docs/`
Framework documentation, usage guides, integration references.
- `README.md` — main project guide
- `QUICKSTART.md` — quick start
- `USAGE.md` — full usage reference
- `AGENTS.md` / `AGENTS_README.md` — agent framework
- `LEAN_README.md` — Lean formalization guide
- `LLM_AUGMENTATION.md` / `LLM_REFERENCE.md` — LLM integration
- `METHODOLOGY.md` — methodology documentation
- HTML visualizations: primitive space, transformation map, seven primitives

### `archive/`
Superseded documents, orphaned PDFs, old backups.
- `IUT_NON_TRANSMISSIBILITY.pdf` — superseded by IUG version
- `PDW.pdf` / `PDW - Copy.pdf` — Pacific Depot Western
- External papers: *Catch a Rising Problem*, *A Study of Objectively Real Time*
- `QUANTSYNTHONICON.md.old.bkp` — old format backup

### `data/`
Catalogs, insights, reference data.
- `hv1_lattice_insights.json` — Hv1 channel lattice analysis
- `syncon_insights.json` — session insights cache
- `SYNTHON_LIST_001.txt` — synthon reference list
- `downloads/` — downloaded papers and datasets

### `syncon_outputs/`
All `syncon_inquiry.py` session outputs (200+ JSON files, timestamped).

### `space_search/`
Space observational pipeline — FRB, pulsar, spectral analysis code.

### `agents/`
Agent implementations and provider integrations.

### `framework/`
Core framework: base classes, LLM providers, orchestration.

### `examples/`
Demo scripts and exploration notebooks.

### `designs/`
Synthon design specifications (`.syn` files).

### `results/`
Analysis result JSONs and design summaries.

### `figures/`
Images: `SYNCHART.png`, `CRIT.svg`, `SYN_GROPPI.png`, phase diagram.

### `synthomnicon-lean/` / `Primitives/`
Lean 4 formalization: `OPN_2adic.lean`, `BSD_2adic.lean` — machine-verified constraint grammar.

### `SynthOmnicon/` — Lean package (main formalization)
Full Lean 4 package. Key modules:

**`SynthOmnicon/Primitives/`**
- `Synthon.lean` — 12-field `Synthon` structure; `primitiveMismatches` (Hamming distance); P-70 field-theoretic identities (inflaton≡Higgs≡axion proved by `rfl`); SM/QG distance = 9 by `decide`
- `TierCrossing.lean` — granularity separation, tier crossing cost; Higgs hierarchy + cosmological predictions; `grammar_physics_correspondence` axiom

**`SynthOmnicon/Millennium/`** — Seven-file Millennium Prize Problem library
| File | Barrier | Missing object |
| :--- | :--- | :--- |
| **`RH.lean`** | OpenProblem | `ZeroFreeStrip 0` — `rh_barrier` proves RH ↔ ZeroFreeStrip 0 by `norm_num` |
| **`Hodge.lean`** | OpenProblem | `AlgebraicCycleRep X p α` — cycle class surjectivity; p=1 (Lefschetz) is MathlibGap |
| **`NS.lean`** | OpenProblem | `GlobalRegularityCert u₀` — critical Sobolev gap $0 < \frac{1}{2} < 1$ proved by `norm_num` |
| **`PvsNP.lean`** | OpenProblem + MathlibGap | `CircuitLowerBound ε` — three meta-barriers (BGS/Razborov-Rudich/AW) as formal theorems |
| **`YM.lean`** | MissingFoundation | `PathIntegralMeasure 𝔤` — two stacked sorries; unique MissingFoundation problem |
| **`OPN.lean`** | MathlibGap → OpenProblem | `euler_opn_structure` (Euler 1747, MathlibGap) + `opn_nonexistence`; uses real Mathlib `Nat.Perfect` |
| **`BSD.lean`** | OpenProblem + 2×MathlibGap | `BSDRankCertificate` — three parallel sorries; rank≤1 proved (Kolyvagin); uses real `WeierstrassCurve` |
| **`Barriers.lean`** | Taxonomy | Seven typed axioms; `ym_is_unique_missing_foundation` by `decide` |
| **`PrimitiveBridge.lean`** | Bridge | Connects sorry boundaries to primitive field transitions; `ym_primitive_barrier_certificate`; `primitive_bridge_master` |

### `UNIFIED_SYNTHONICON/`
Unified three-document export: TOPOLOGOS, SCHESIAKOLOGOS, ONTOLOGOS (PDFs + TeX).

---

*Last updated: 2026-03-26 · `syncon_catalog.json`: 80 entries · Millennium Lean library: 9 files complete*
