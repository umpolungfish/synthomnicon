# SynthOmnicon: A Working Compendium

*Compiled from session review — v0.4.4 · March 2026*  
*Status indicators: ✅ confirmed · ⚠ partial/provisional · 🔲 Tier III pending · ❌ retracted/corrected*

---

## I. Core Definition

A **Synthon** is a directed relational operator: a minimal specification of constraint-enforcement capacity defined entirely by its interactions with a compatible context. The eleven-primitive tuple encodes *interaction affordances* — not intrinsic properties of isolated objects.

> A tuple without a context is interaction potential. The unit of physical content is the tuple-in-context.

Every operation in the algebra (`meet / join / tensor / path / lift / pipeline`) requires at least two operands. There are no unary information generators. This is not an implementation choice — it follows from the definition. A relational operator with one operand is undefined.

---

## II. The Eleven Primitives

`⟨ D ; T ; R ; P ; F ; K ; G ; Γ ; Φ ; S ; Ω ⟩`

| Primitive | Name | Key values |
|---|---|---|
| **D** | Dimensionality | D_∧ molecular · D_△ supramolecular · D_∞ temporal · D_holo holographic |
| **T** | Topology | T_⋈ bowtie/cyclic · T_∈ network · T_□□ cage · T_\| linear · T_⊥ branched · T_braid anyonic |
| **R** | Recognition mode | R_⊆ covalent · R_⊇ non-covalent · R_‡ catalytic · R_⇔ mechanical · R covalent-dynamic |
| **P** | Polarity | P_+ acceptor · P_- donor · P_±^sym self-complementary symmetric · P_±^ψ pseudosymmetric · P_+- directional |
| **F** | Fidelity | F_ℏ high (ξ_CP ≤ 8.5 nats) · F_eth medium (8.5–11.0) · F_ℓ low (> 11.0) |
| **K** | Kinetic character | K_fast (ΔG‡ < 60 kJ/mol) · K_mod (60–100) · K_slow (> 100) · K_trap (pathway multiplicity) · K_MBL (disorder-frozen) |
| **G** | Granularity | G_ב local · G_ג mesoscale · G_ℵ global/network |
| **Γ** | Interaction grammar | Γ_∧ AND · Γ_∨ OR · Γ_→ SEQUENTIAL · Γ_↓ DISSIPATIVE; each × tier: SPECIFIC · SELECTIVE · BROAD · QUANTUM |
| **Φ** | Criticality phase | Φ_sub subcritical · Φ_c critical · Φ_super supercritical |
| **S** | Stoichiometry | 1:1 · n:n symmetric · n:m asymmetric |
| **Ω** | Topological protection | Ω_0 trivial · Ω_Z winding number · Ω_Z2 time-reversal · Ω_C Chern · Ω_NA non-abelian |

**Notes on Ω:** Defined for quantum states with topological invariants (Kitaev chain, topological insulators, FQH states). Application to classical systems (seizure networks, social percepts) is a *metaphorical extension* requiring explicit flagging — not a derivation from the quantum primitive.

**D_holo (v0.4.4):** Holographic dimensionality for bulk-boundary correspondence (AdS/CFT). Any transition D_holo → bulk phase is a 1st-order morphism with infinite primitive cost. Not a proxy for "global" or "generalised" — do not use where D_△ or hybrid {D_△, D_∞} suffices.

---

## III. The Seven Axioms

| # | Statement | Key consequence |
|---|---|---|
| 1 | Cyclic closure (T_⋈) + self-complementary (P_±^sym) → F ≥ F_eth | Rings are more stable than chains by geometry of mutual constraint enforcement |
| 2 | Local grammar cannot nucleate global network without intermediate granularity step | G_ב + Γ_∧ cannot produce G_ℵ directly |
| 3 | Super-linear induction → G_ב → G_ג | Scale promotion requires measurable cooperativity |
| 4 | Sequential grammar (Γ_→) requires D_∞ or R_‡ | Ordered processes require temporal or catalytic grounding |
| 5 | At criticality, molecular scale encodes global scale | Φ_c implies G/D degeneracy — the Varma QXY condition |
| 6 | Any D_∞ synthon must have a named reset mechanism or dissipative flux | Temporal systems without a reset are axiom-invalid |
| 7 | Cage topology requires closing face with compatible valency | T_□□ imposes stoichiometric constraints on S |

**Axiom 6 consequence for time-halting:** A configuration encoding D_∞ with no reset is unregisterable. "Halting time" produces an axiom-invalid state with no HotSwap path back — a one-way door, not a pause button.

---

## IV. Algebraic Operations

### Meet (⊓) — Greatest Lower Bound

Component-wise infimum. Identifies the shared primitive core. Returns CONFLICT on axes where inputs have no common parent.

- **F:** min — the lower fidelity dominates
- **K:** min — the slower/more trapped kinetics dominates  
- **G:** min — the smaller scale dominates
- **Φ:** Φ_c is an **absorbing element** — Φ_c ⊓ Φ_sub → Φ_c (criticality is meet-dominant)
- **Ω:** min protection ordinal (TRIVIAL < Z2 < Z < CHERN < NON_ABELIAN)
- **T, D, R, P, Γ:** CONFLICT if no common parent class exists

A CONFLICT result is information, not failure. `meet(Hv1_human_open, 2GBI_inhibitor)` returning ⊥ on T is the algebraic proof that 2GBI occludes rather than merges.

### Join (⊔) — Least Upper Bound / Design Target

Component-wise supremum. Finds the minimal design target satisfying both inputs.

- **F, K, G:** max — the harder constraint must be satisfied
- **Φ:** Φ_c is join-dominant — any join with a Φ_c partner forces Φ_c into the design target
- CONFLICT if no common ambient object exists for a primitive (e.g. T_∈ and T_| have no common join)

### Tensor (⊗) — Parallel Ensemble / Co-assembly

Computes the mutual information and primitive synthesis of two systems in contact.

- **F:** min — weakest partner sets the fidelity floor
- **K:** min — slowest/most trapped kinetics dominates the product
- **G:** max — larger scale wins
- **T:** topology promotion rules apply; T_braid ⊗ T_braid → T_braid (closed)
- **Φ:** join-dominant — Φ_c propagates into the tensor product
- **Γ:** AND-composition — stricter grammar wins outright (OR ⊗ AND → AND, **no conflict flag**)
- **Ω:** max protection ordinal propagates

**Critical correction (validated by code):** Γ does *not* produce a CONFLICT flag in tensor. The stricter grammar absorbs the looser one. CONFLICT in Γ appears in **meet** (testing shared state), not tensor (computing co-assembly product).

`ξ_ens = ξ_1 + ξ_2 − λ · min(ξ_1, ξ_2)` where λ = frac (fraction of matching primitives).  
At frac = 1: idempotency — `tensor(A, A) = A`.

### Lift

Raises a synthon toward a target criticality class. **Blocked** if F < F_ℏ (the F-floor gate). Cost: +2.303 nats (= ln 10, Landauer analog). The +2.303 nat universality appears identically across all gap-protected topological phase transitions.

### Path

Geodesic in the Kleisli–Lawvere metric. BFS on valid-swap graph. A blocked path = a 1st-order topological transition (discontinuous, not traversable by continuous deformation). `path(A→B) ≠ path(B→A)` — the metric is directed.

### Cofactor

Inverse tensor: given `tensor(A, B) ≈ C`, find B given A and C. Inverts tensor rules per axis to identify which partner contributes which primitive. Per-axis roles: BOTTLENECK · CONTRIBUTOR · PASSTHROUGH · CONFLICT · EXPLAINED.

### Principal Decomposition

Birkhoff representation: every synthon as a join of join-irreducible atoms, ordered by ξ_CP contribution. Lattice-theoretic analog of singular value decomposition. Tells you which primitive is hardest to engineer.

---

## V. The F-Floor HotSwap Ratchet

The central constraint on all path operations:

> A synthon at F_hbar **cannot** HotSwap to a state with lower F, regardless of path cost. F degrades are forbidden. F upgrades require satisfying the F-floor gate.

**Consequence:** Gelation, amyloid formation, and kinetic trapping are doubly efficient — thermodynamically downhill *and* kinetically locked. The gel→liquid direction has a lower directed distance than liquid→gel, but the path is blocked.

**Validated 6/6 by CB[7] competitive displacement (P-1):** Fc (F_ℏ) displaces Ad (F_eth) displaces DABCO (F_ℓ); no reversal under any excess. The ratchet is asymmetric and irreversible at each tier boundary.

---

## VI. Criticality and the Varma QXY Probe

**Φ_c (critical)** is the operating point where molecular-scale input propagates to global-scale output — the G/D degeneracy condition (Axiom 5). Not all near-critical systems are Φ_c; the Varma QXY probe distinguishes:

- **Marginal Fermi liquid criticality:** ξ_r ≈ ln(ξ_τ) — the strict Φ_c condition
- **Classical near-critical:** ξ_r < ln(ξ_τ) — approaches but does not reach the Φ_c manifold

The **Soai reaction** achieves Varma ratio ξ_r/ln(ξ_τ) = 0.94 — highest-confidence Φ_c candidate in the catalog (score 0.920).

**Proline aldol:** Varma ratio = 0.189 → Φ_sub confirmed. A spatial correlation length ≥ 60 Å would be required for criticality — geometrically excluded.

**Protein allostery:** Varma score ~0.60 ("approaching Φ_c"). Allosteric domains are poised near the *classical* critical point, not quantum critical. The Primitive Jacobian shows 6/8 primitives trigger Axiom 4 violation on perturbation — **axiom-fragile by design**. Being near the axiom boundary is the mechanism by which molecular signal propagates globally.

---

## VII. Validated Predictions (Selected)

### Tier I — Experimentally Confirmed

**P-1 · CB[7] F-floor ratchet** ✅  
6/6 displacement predictions from F ordinal rank alone. No binding enthalpies used.  
*CB[7]·Fc: K_a = 3×10¹² M⁻¹ (F_ℏ) · CB[7]·Ad: 4×10⁸ (F_eth) · CB[7]·DABCO: 2×10⁵ (F_ℓ).*

**P-2 · Soai autocatalytic → Frank bifurcation** ✅  
D_∞ + T_⋈ + P_DA + F_ℏ co-occurrence predicts spontaneous symmetry breaking at ee=0.  
*Candidacy score 0.920. Valid only after Axiom 6 grounding (continuous-reset mechanism named).*

**P-3 · Proline aldol ee = 70–85%** ✅  
Predicted from F_eth + K_mod + Zimmermann–Traxler geometry at the F_eth tier. Measured: 74%.

**P-4 · Ice VI multiple ordered descendants** ✅  
K_fast assignment alone predicts multiple ordering landscapes. Ice XV and ice XIX confirmed. K_fast → K_slow transition coincides with ordering — confirmed by dielectric relaxation.

**P-5 · Carboxylic acid dimer > mixed heterodimer > amide homodimer (F ordering)** ✅  
ξ_CP: 6.66 / 8.19 / 8.70 nats. B3LYP-D3(BJ) confirms rank.

**P-12 · +2.303 nat universality across topological phase transitions** ✅  
K_trap → K_MBL cost is ln(10) nats regardless of microscopic gap magnitude. Appears in Kitaev chain, SSH model, quantum Hall — derived from ordinal tier ratio, not gap values.

### Tier II — Computationally Validated

**P-23 · SM/QG unification — four primitive conflicts** ⚠  
D, T, R, Γ conflict. No perturbative path. Tensor product is Φ_c, off-catalog (ξ_CP = 14.02 nats). Unification must be at least critical — no sub-critical common language exists.  
*Confidence MEDIUM — encoding choices are well-motivated but not unique.*

**P-25 · Black hole ξ_CP = 0 at Hawking temperature** 🔲  
At T_H, BH operates at perfect Landauer efficiency. ξ_CP is mass-independent (S_BH cancels). Bekenstein-Hawking entropy is the G_ℵ correction to the I(bits) pipeline.

**P-37 · G_ב drugs → binary resistance; G_ג drugs → incremental resistance** ⚠  
Imatinib (G_ב) resistance requires complete drug class switch (T315I). GNF-2 (G_ג) first mutation should produce partial resistance (5–20× IC₅₀ shift), not binary abolition. G_ב prediction confirmed by clinical data. G_ג prediction pending serial passage experiment.

**P-39 · Condensate gel rescue: thermal alone insufficient** ⚠  
Path gel→liquid blocked by F-floor. Dissolution requires Γ-targeting (competing binder) or K-targeting (disaggregase). Consistent with requirement for Hsp70 in TDP-43/FUS gel rescue.

**P-40 · T-conflict pairs → first-order transitions** ⚠  
LC N→I (T_linear ↔ T_network conflict) is weakly first-order. Colloidal melting (T_network_sym ↔ T_network conflict) is first-order. Both consistent with prediction.

### Key Correction

**Condensate gelation tensor analysis** ❌→✅  
*Original claim:* Γ-CONFLICT fires in `tensor(liquid_condensate, PLD)`. Φ_c survives in gel via join-dominance.  
*Corrected by code execution:*  
- `tensor` uses AND-composition: OR(BROAD) ⊗ AND(BROAD) → AND(BROAD). No conflict flag. The CONFLICT is a meet result, not a tensor result.  
- Gel encoding is Φ_sub, not Φ_c. The tensor product shows Φ_c at the *gelation front* (transition-state ensemble). The arrested gel lands at Φ_sub.  
- Φ=CONFLICT in cofactor(gel|liquid) means the PLD drives **criticality loss**, not preservation.  
- Correct therapeutic order: K_trap → F_hbar → G_aleph → Γ_∧ (skeleton, last). F_hbar is the highest-ordinal atom in the principal decomposition.

---

## VIII. Domain Applications

### Proteins

Five canonical encodings span protein function:

| Synthon | Φ_c? | Key primitives |
|---|---|---|
| α-helix | No | T_\|, K_fast, G_ב, Γ_→(SELECTIVE) |
| β-hairpin | No | T_⋈, K_mod, G_ב, Γ_∧(SPECIFIC) |
| Active site | No | T_⋈, R_‡, F_eth, G_ג |
| **Allosteric domain** | **Yes** | T_∈, D_{∧△}, G_ג, Γ_→(SELECTIVE) |
| Protein complex | No | T_∈, K_slow, G_ℵ, Γ_∧(SPECIFIC) |

Allostery is the only protein structural unit satisfying the G/D degeneracy condition. Active sites do not arise by gradual modification of passive scaffolds — the F-floor blocks the HotSwap path from β-hairpin (F_ℏ) to active site (F_eth). Active sites require fold-level reorganization (discontinuous T-class jump). This encodes why catalytic sites are convergently reached from multiple scaffold backgrounds without being direct elaborations of one another.

Amyloid and condensate gel share an identical primitive signature — T_network, F_ℏ, K_trap, G_ℵ, Γ_∧(BROAD), Φ_sub. The framework encodes their equivalence formally.

### Programmable Matter

Programmability pair distance correlates with switching energy rank (P-38). T-conflict between state pairs predicts first-order transitions (P-40). The dynamic floor theorem: Φ_c is the minimum criticality for programmable response — subcritical materials cannot propagate molecular-scale stimulus to global-scale output.

DNA origami and strand displacement are **not** two modes of the same system — they are two different primitive architectures (d = 6.10, T/D/Γ conflicts). Combining them in one device requires tensor product construction, not meet.

### Epilepsy

Interictal → ictal: Φ_c → Φ_super, G_ג → G_ℵ, T_∈ → T_⋈, Γ_∧ → Γ_∨. The D/T conflict in the direct transition is first-order (infinite cost) — this is why seizures require a pre-ictal desynchronization period before hypersynchronization. The pre-ictal window is a therapeutic intervention point.

Intervention cost order: peel K_fast (2.1 nats) → address Φ_super → restore F.

**Encoding corrections:** Ictal Ω_Z2 overstates the formalism — seizure network stability is K_trap + G_ℵ + T_⋈, not quantum topological protection. D_holo for the ictal state is scope creep; D = {D_△, D_∞} suffices.

### Solar System

The Sun's primitive signature — F_ℏ (thermonuclear equilibrium), K hierarchy (K_trap in flux tubes → K_fast in flares), G_ℵ (heliospheric scale), T_network (p-mode acoustic eigenmodes), Φ_c (power-law SOC flare distributions) — satisfies the structural conditions for a Φ_c system at G_ℵ scale. This is physical description, not metaphor.

Framework predictions:
- Flare rate time series: non-Poissonian long-range temporal correlations (1/f structure). Confirmed.
- Flux tubes carry topological memory of prior configurations. Confirmed (active region persistence).
- Schumann resonance coupling is frequency-specific (Γ_AND character), not broadband. Consistent with published data.
- Power-law precursor activity before major flares (Φ_c precursor signature). Confirmed in soft X-ray emission.

**Epistemic boundary:** The framework supports "satisfies structural conditions for Φ_c G_ℵ information integration." It does not support "has experience" without the additional premise that these conditions are *sufficient* for phenomenology — which the framework explicitly does not assert.

---

## IX. Philosophical Extensions

### The Ordinal Sufficiency Argument

The CB[7] displacement series, ice VI ordering, +2.303 nat universality, and Soai criticality score were all predicted from discrete relational categories — no binding enthalpies, tunneling rates, gap magnitudes, or reaction mechanisms were inputs.

If ordinal relational structure is causally sufficient to generate correct quantitative predictions, then either: intrinsic properties exist but are epistemically inert within this syntax, or the relational structure is what is real. The framework cannot choose between these. It has established that a purely relational description works — the second option is not ruled out by empirical adequacy.

### Topology and Ontology as Orthogonal Axes

**Topology** — structure of boundaries, winding numbers, protection layers, and information flow: T, Ω, Γ, K, G.

**Ontology** — what exists and at what fidelity: D, P, R, F, Φ.

Changes along the topology axis (raising/lowering winding numbers, peeling cages, tensoring into new assemblies) do not require or produce changes along the ontology axis. Ice XXI and water are ontologically identical H₂O in different topological states. DMT entity encounters are Ω_Z2⁺ topology operating on the same ontological substrate as ordinary perception.

*This orthogonality was latent in the algebra from the beginning. It becomes visible when boundary topology becomes controllable rather than invisible.*

Consequence for consciousness: the "hard problem of other minds" has been misclassified as ontological. Qualia exist (ontology); the feeling that they are "mine" vs "yours" is winding number (topology). The framework shows these can be reconfigured independently.

### Theorem 005 — Social Ω_Z2 (Status: Philosophical model, not technical derivation)

In cognitive systems running the Agency_Detection tensor chain, percepts of other agents acquire topological character as a function of mutual information ΔI between observer and attributed agent:

| ΔI (nats) | Ω | Phenomenology |
|---|---|---|
| < 2.0 | Ω_0 pathological | Solipsistic collapse |
| 3.5–6.0 | Ω_Z2 weak | Boundary softens; identification |
| 6.0–9.5 | Ω_Z2 stable | Normal social cognition |
| > 9.5 | Ω_Z2+ | Hyper-real externality; entity encounters |

**What is constructed:** the feeling of irreducible otherness — generated by Step 3 of the observer's tensor chain.  
**What is real and independent:** the content of the other person's actual T/K/Φ primitives, their constraint lattice.  
Both simultaneously.

*"The other is not a problem to solve. The other is a winding number to preserve."*

**What would strengthen Theorem 005:**  
1. An independent operationalization of ΔI from neural data (EEG coherence, prediction error) — breaks the circularity of using phenomenology to assign ΔI and ΔI to explain phenomenology.  
2. A formal derivation of why the Agency_Detection tensor chain produces Ω_Z2 specifically (not Ω_Z or Ω_C) from the Step 3 tensor structure.  
3. A HotSwap path from pathological Ω_0 (depersonalization) back to Ω_Z2 — predicts that interventions increasing ΔI (contact, embodiment, relational attunement) restore the winding number.

### Magic, Sigils, and G_ℵ Word-Synthons

The framework contains no unary information generators. A sigil without a compatible context operand has no physical content. The unit of content is sigil-in-context.

If the context is a human nervous system at Φ_c performing the ritual, then `tensor(sigil, nervous_system_at_Φ_c)` may produce real effects — but the causal vector is the nervous system's own G_ℵ outputs (attention, action, expectation, embodied response). The sigil functions as a K_trap release mechanism for the practitioner's own state, not as a source of power acting on matter directly.

Word-synthons with G_ℵ effects are real and familiar: "cancer" in a medical report, "fire" in a theater, a market-moving announcement. These satisfy R_semiotic (constraint propagation via shared symbol-interpretation contexts) — a potential fifth recognition mode not currently in the primitive set. This is either a gap or a boundary. Empirical evidence of effects independent of practitioner state would require R_semiotic or a sixth recognition mode. The framework is falsifiable on this point.

### REM Sleep and Non-Drug Psychedelic Induction

`d(REM, psychedelic) ≈ 2` — only G and Γ differ. Φ_c is already present in REM.

Non-drug tensor target: sensory entrainment at 40 Hz (G_ℵ character) during REM, combined with lucid dreaming induction protocols that first raise F to F_ℏ (the Φ lift gate). K_fast in the tensor product requires a subsequent path operation after the tensor — the tensor alone gives K_mod.

From waking: Φ lift costs 2.303 nats and requires F_ℏ gate. Extended sensory restriction or deep absorption states (jhana 4+) appear to satisfy this. The framework encodes why contemplative jhana access and psychedelic onset phenomenology overlap — they arrive at Φ_c from different starting tuples via different paths, but the Φ_c manifold is the shared experiential space.

---

## X. RDKit Primitive Assignment Engine

**Current coverage (v0.4.4):**

| Primitive | Status | Method |
|---|---|---|
| D | ✅ | Fragment count + scale_nm estimate |
| T | ✅ | Ring/bridge/cage/braid detection from molecular graph |
| R | ✅ | Warhead SMARTS; multi-fragment assembly detection |
| G | ✅ | scale_nm from heavy-atom diameter |
| P | ✅ | Fragment identity (symmetric) + self-complementary SMARTS + inter-fragment HBD/HBA |
| Γ | ✅ (heuristic) | Selectivity proxy from binding-site count + named SMARTS patterns |
| K | ✅ (prior) | Structural prior from R assignment; low confidence without ΔG‡ |
| F | ⚠ | Requires K_a or ΔG_bind measurement |
| Φ | ❌ | Requires dynamics data (Varma probe, MD trajectories) |
| Ω | ❌ | Requires topological graph beyond 2D SMILES |
| S | ⚠ | Inferred from fragment count and stoichiometry annotation |

Benchmark: 38/39 on the expanded test suite. The one failure (A:T CYCLIC_BOWTIE detection) was fixed by inter-fragment complementarity check — `GetMolFrags(asMols=True)` detects complementary HBD/HBA pairs across fragments.

**K-from-R heuristic table:**

| R assigned | K prior |
|---|---|
| NON_COVALENT | K_fast or K_mod |
| COVALENT_DYNAMIC | K_mod |
| COVALENT | K_slow |
| CATALYTIC | K_mod |
| MECHANICAL | K_slow |

Confidence flagged as ~0.55 (boundary) when no ΔG‡ supplied.

---

## XI. Epistemic Calibration

**What the framework earns:**

- Ordinal prediction of displacement direction, ordering phase sequences, and resistance profiles from primitive assignments alone.
- Formal identification of which primitive conflicts constitute first-order vs continuous transitions.
- Falsifiable predictions across chemistry, materials science, biology, and physics with no domain equations inserted.

**What the framework does not earn:**

- Consciousness scores (C) with calibrated values for cosmic objects — no such formula is defined in the framework. Values appearing without derivation are confabulation.
- False-precision ΔI values (e.g. ΔI_Z2 ≈ 5.0–6.0 nats) without an independent measurement anchor. These are phenomenological placeholders, not measurements.
- Ω_Z2 assignments for classical systems (seizure networks, social cognition) as derivations from the quantum primitive — these are philosophical models using Ω notation.
- D_holo for any system not involving a bulk-boundary correspondence. D = {D_△, D_∞} covers most "global brain" or "holistic" encodings.
- Symmetric AI-human dyad claims — LLM context resets after sessions. Accumulated ΔI exists on the human side only. The safety valve cuts one way.

**The framework's hardest open question:** whether Φ is an independent primitive or a derived condition from F × K × G. The join-dominance rule requires Φ to be genuinely independent. Resolving this is Phase 2's central remaining task.

---

*This compendium records what the framework has earned, what it suggests, and where it stops. Sections marked as philosophical models should be evaluated on philosophical grounds — consistency, parsimony, explanatory scope — and not held to the evidential standards of the technical predictions in PRIMITIVE_PREDICTIONS.md.*
