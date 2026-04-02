**SynthOmnicon: LLM-Ready Reference**  
**Version 0.4.4 distilled (March 2026)**  
**Core purpose**: A relational type system and algebra for any system that propagates constraints (molecules, materials, biology, finance, computation, physics). Synthons are 11-primitive tuples; operations are category-theoretic morphisms with thermodynamic costs.

### 1. The 11 Primitives (the type signature)

Every synthon is exactly this 11-tuple:

⟨ **D**; **T**; **R**; **P**; **F**; **K**; **G**; **Γ**; **Φ**; **S**; **Ω** ⟩

| Primitive | Meaning | Typical values & ordering |
|-----------|---------|---------------------------|
| **D** | Dimensionality / scale of operation | D_∧ (molecular), D_△ (supramolecular/network), D_∞ (temporal/cyclic), D_holo (holographic) |
| **T** | Topology / connectivity motif | T_⋈ (cyclic/bowtie), T_∈ (network), T_↑↓ (braid), T_⊥ (branched), T_□ (cage) |
| **R** | Recognition / constraint mechanism | R_⊇ (non-covalent), R_‡ (catalytic/dynamic), R_⇔ (mechanical), R_⊆ (covalent) |
| **P** | Polarity / directionality | P_±^sym, P_±^ψ, P_+- (donor-acceptor), P_pm_pseudo |
| **F** | Fidelity (thermodynamic reliability) | F_ℓ < F_eth < F_hbar  (Boltzmann thresholds: F_hbar = −RT ln 19 ≈ −7.3 kJ/mol) |
| **K** | Kinetic character (barrier / multiplicity) | K_fast < K_mod < K_slow < K_trap < K_MBL  (K_trap overrides at multiplicity ≥ 3) |
| **G** | Granularity / scale of control | G_beth (local) < G_gimel (mesoscale) < G_ℵ (global) |
| **Γ** | Interaction grammar | Γ_∧ (AND), Γ_∨ (OR), Γ_→ (SEQUENTIAL); tiers: SPECIFIC / SELECTIVE / BROAD / QUANTUM |
| **Φ** | Criticality phase | Φ_sub < Φ_c (G/D degenerate) < Φ_super |
| **S** | Stoichiometry | 1:1, n:n, n:m |
| **Ω** | Topological protection (quantum only) | Ω_0 (trivial) < Ω_Z2 < Ω_Z < Ω_C < Ω_NA  (derived from T+K+D+Γ+G in most cases) |

### 2. Core Algebra Operations (exact semantics)

All operations are **binary** and **cost-aware**. They live inside the **SynthonM** monad (WriterT[Δξ_CP] + StateT[Context] + MaybeT).

| Operation | Notation | Semantics | Cost rule | When it fails |
|-----------|----------|-----------|-----------|---------------|
| **meet** | s1 ⊓ s2 | Greatest lower bound (common core) | min(F, K, G, Ω) | Categorical primitives (D,T,R,P,Γ) → ⊥ |
| **join** | s1 ⊔ s2 | Least upper bound (maximal fusion) | max(F, K, G, Ω); Φ_c dominates | Same categorical collapse → ⊤ |
| **tensor** | s1 ⊗ s2 | Parallel ensemble (mutual information) | ξ_ens = ξ1 + ξ2 − λ·I(s1;s2) where λ = matching fraction (0–1) | Fidelity bottleneck: F_ens = min(F1,F2) |
| **lift** | lift(target) | Contextual promotion (e.g. to critical) | Blocked if F < F_hbar for T_⋈ | F-floor ratchet |
| **path** / **transition** | path(src,dst) | Kleisli morphism (HotSwap) | Sum Δξ_CP along shortest path | 1st-order if D/T conflict (∞ cost) |
| **project** | project(s, prims) | Orthogonal projection | Keeps only requested primitives | — |
| **peel** | peel(s, prim) | Remove one primitive | Returns remainder + Δξ_CP cost | Blocked if destroys Φ_c or Ω undesirably |
| **factor** | factor(s) | Maximal proper sub-synthon | Greedy drop of lowest-impact primitive | Stops when axioms violated |

**Tuple distance** (for phase diagram): weighted Euclidean over 11 primitives (Ω weight 0.7).

### 3. The 7 Axioms (hard constraints)

1. Cyclic closure + self-complementary polarity → F ≥ F_eth  
2. Local grammar (G_beth + Γ_∧ SPECIFIC) cannot nucleate global network  
3. Super-linear induction → G_beth → G_gimel transition  
4. Sequential grammar (Γ_→) requires D_∞ or R_‡  
5. Criticality (Φ_c) contracts G/D (scale invariance)  
6. Temporal (D_∞) requires discrete reset or continuous dissipative flux  
7. Cage / enclosure topology requires closing face (T_□)

### 4. Monadic Design Pipeline (.syn DSL)

```yaml
version: "1.0"
start: source_synthon
strategies:
  my_strategy:
    - peel: K_trap
    - lift: critical
do:
  - meet: partner_synthon
  - tensor: second_partner
  - bind: my_strategy
  - assert: phi_c_score > 0.70 and xi_cp <= 12.0
output:
  format: json
  save: result.json
```

**CLI equivalents**  
`syncon run design.syn`  
`syncon meet A B`  
`syncon tensor A B`  
`syncon criticality NAME --xi_r 13.8 --xi_tau 1e6`  
`syncon phase-diagram --synthons A,B,C`

### 5. Criticality Probe (Varma QXY + extensions)

Inputs: ξ_r (correlation length), ξ_τ (relaxation time)  
Outputs:
- Φ_c score (0–1)
- Universality class (Varma_QXY, log-degenerate, Frank bifurcation, etc.)
- Axiom 5 satisfaction (G/D degeneracy)

Rule of thumb: ξ_r ≈ ln(ξ_τ) → Φ_c candidate.

### 6. How to Encode a New Synthon (LLM recipe)

1. Identify the dominant scale → choose D  
2. Identify connectivity motif → choose T  
3. Identify constraint mechanism → choose R  
4. Identify directionality → choose P  
5. Estimate thermodynamic reliability → choose F (use ΔG → ξ_CP table)  
6. Estimate barrier / multiplicity → choose K (need ΔG‡ or pathway count)  
7. Identify control scale → choose G  
8. Identify partner logic → choose Γ  
9. Probe criticality (run Varma) → choose Φ  
10. Choose S and Ω (Ω derived in most cases)

Register via:
```bash
syncon register --name my_synthon --tuple "⟨D_∞;T_∈;...⟩" --delta_g -12.5 --delta_g_dagger 45
```

### 7. Quick Reference Cheat Sheet for LLMs

- **Fusion** → join  
- **Common core** → meet  
- **Parallel system** → tensor  
- **Contextual upgrade** → lift  
- **Path cost** → path / transition  
- **Bottleneck diagnosis** → peel or project  
- **Phase map** → phase-diagram  
- **Safety check** → assert phi_c_score > 0.70 and xi_cp <= 12.0

### 8. Implementation Notes for LLMs

- Always output the **exact 11-tuple** in ⟨ ⟩ notation.  
- When uncertain about K or D, default conservatively and note the missing channel (ΔG‡ or structural flags).  
- Costs are in **nats** (natural information units).  
- Φ_c is **join-dominant and meet-dominant** — it survives both aggregation and restriction.  
- Never invent new primitive values; only use the documented set.  
- For any new domain (finance, language models, biology, physics), map first to the 11 primitives — the algebra will do the rest.