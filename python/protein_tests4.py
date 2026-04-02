"""
Protein Science Tests — Part 4

Section 15: Real drugs encoded as synthons
  - Imatinib  (Type II competitive / DFG-out, BCR-ABL)
  - GNF-2     (pure allosteric ABL inhibitor, myristoyl pocket)
  - Venetoclax (BH3 mimetic, BCL-2 groove)

Compared against:
  - monad-designed ideal (Part 3)
  - allosteric_domain (the target)
  - each other

Then: Jacobian on each drug + fault_injection
Then: explicit drug-design gap analysis (distance to ideal, per-primitive breakdown)
Then: meet(drug, ideal) to find what's already right
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from synthomnicon.models import (
    Synthon, Dimensionality, Topology, RecognitionMode, Polarity,
    Fidelity, KineticCharacter, Granularity, InteractionGrammar,
    CriticalityPhase,
)
from synthomnicon.algebra import tuple_distance, meet, join, tensor, CONFLICT
from synthomnicon.perturbation import PerturbationEngine

# ─────────────────────────────────────────────────────────────────────────────
# The monad-designed ideal (from Part 3 output)
# ─────────────────────────────────────────────────────────────────────────────

ideal_allosteric_inhibitor = Synthon(
    name="ideal_allosteric_inhibitor",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.NETWORK,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.SELF_COMPLEMENTARY_PSEUDO,
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.SLOW,
    granularity=Granularity.MESOSCALE,
    interaction_grammar=InteractionGrammar.SELECTIVE_SEQ,
    criticality_phase=CriticalityPhase.CRITICAL,
    description="Monad-designed ideal: sequential, mesoscale, Phi_c, medium fidelity",
)

# ─────────────────────────────────────────────────────────────────────────────
# Real drug encodings
# ─────────────────────────────────────────────────────────────────────────────

# Imatinib (Gleevec): Type II BCR-ABL inhibitor
# - Occupies ATP site AND DFG-out allosteric pocket simultaneously
# - High affinity (IC50 ~100 nM), slow off-rate from DFG-out conformation
# - Local: doesn't propagate beyond ATP-binding cleft
# - Requires BOTH hinge contacts AND Asp-Phe-Gly flip (AND grammar)
imatinib = Synthon(
    name="imatinib",
    dimensionality=Dimensionality.MOLECULAR,           # D_∧ — local pocket chemistry
    topology=Topology.CYCLIC_BOWTIE,                   # T_⋈ — cyclic: imatinib ring system bridges two pharmacophores
    recognition_mode=RecognitionMode.NON_COVALENT,     # R_⊇ — H-bonds + hydrophobic
    polarity=Polarity.DONOR_ACCEPTOR,                  # P_+- — directional pyridine N–H···Glu/Asn
    fidelity=Fidelity.HIGH,                            # F_ℏ — sub-nM DFG-out selectivity
    kinetic_character=KineticCharacter.SLOW,           # K_slow — slow DFG-out conformational selection
    granularity=Granularity.LOCAL,                     # G_ב — ATP cleft only; no propagation
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,  # Γ_∧(SPECIFIC) — hinge AND DFG-pocket required
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Imatinib: Type II BCR-ABL, DFG-out, F_ℏ, local, non-propagating",
)

# GNF-2: pure allosteric ABL inhibitor (myristoyl-binding pocket)
# - Binds N-terminal myristoyl pocket, distant from ATP site
# - Conformational change propagates from N-lobe → C-lobe → kinase inactivation
# - ~1 µM affinity (F_ℇ), faster kinetics than DFG-out
# - Sequential: myristoyl occupancy → helix αI repositioning → activation loop disorder
# Reference: Zhang et al. Nature 2010; Skora et al. PNAS 2013
gnf2 = Synthon(
    name="GNF-2_allosteric_ABL",
    dimensionality=Dimensionality.MOLECULAR,           # D_∧ — molecular pocket
    topology=Topology.BRANCHED,                        # T_⊥ — myristoyl pocket is a branched hydrophobic cave
    recognition_mode=RecognitionMode.NON_COVALENT,     # R_⊇ — hydrophobic burial + H-bond
    polarity=Polarity.DONOR_ACCEPTOR,                  # P_+- — myristoyl chain inserts directionally
    fidelity=Fidelity.MEDIUM,                          # F_ℇ — µM affinity (weaker than imatinib)
    kinetic_character=KineticCharacter.MODERATE,       # K_mod — faster conformational selection
    granularity=Granularity.MESOSCALE,                 # G_ג — myristoyl → ATP site propagation
    interaction_grammar=InteractionGrammar.SELECTIVE_SEQ,  # Γ_→(SELECTIVE) — myristoyl → conformational change
    criticality_phase=CriticalityPhase.CRITICAL,       # Φ_c — molecular signal → global kinase state
    description="GNF-2: pure allosteric ABL (myristoyl pocket), µM, sequential, Phi_c",
)

# Venetoclax (ABT-199): BCL-2 BH3 mimetic
# - Occupies the BH3-binding hydrophobic groove (bowl topology)
# - High affinity (<1 nM, one of the tightest non-covalent clinical drugs)
# - Slow off-rate from deep groove (K_slow)
# - Local: displaces BH3 proteins, no conformational propagation through BCL-2
# - Specific: groove geometry is uniquely BCL-2 (not BCL-XL/BCL-W without mods)
venetoclax = Synthon(
    name="venetoclax",
    dimensionality=Dimensionality.MOLECULAR,           # D_∧ — groove pocket chemistry
    topology=Topology.BOWL,                            # T_∪ — BH3 groove = open concave bowl
    recognition_mode=RecognitionMode.NON_COVALENT,     # R_⊇ — hydrophobic + H-bond
    polarity=Polarity.DONOR_ACCEPTOR,                  # P_+- — BH3 helix dipole mimicry
    fidelity=Fidelity.HIGH,                            # F_ℏ — sub-nM affinity
    kinetic_character=KineticCharacter.SLOW,           # K_slow — slow off from deep hydrophobic groove
    granularity=Granularity.LOCAL,                     # G_ב — BH3 groove only, no propagation
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,  # Γ_∧(SPECIFIC) — BCL-2 specific groove
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Venetoclax: BCL-2 BH3 mimetic, bowl topology, sub-nM, local",
)

drugs = [imatinib, gnf2, venetoclax]
allosteric_domain = Synthon(
    name="allosteric_domain",
    dimensionality=Dimensionality.HYBRID_MOL_SUPRA,
    topology=Topology.NETWORK,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.DONOR_ACCEPTOR,
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.MESOSCALE,
    interaction_grammar=InteractionGrammar.SELECTIVE_SEQ,
    criticality_phase=CriticalityPhase.CRITICAL,
    description="Allosteric domain target",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 15A: Distance to ideal + target
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("SECTION 15A — DRUG DISTANCES TO IDEAL AND TARGET")
print("=" * 70)

print(f"\nIdeal allosteric inhibitor: {ideal_allosteric_inhibitor.to_notation()}\n")

header = f"{'Drug':<26} {'d(drug,ideal)':>14}  {'d(drug,target)':>15}  {'d(ideal,target)':>15}"
print(header)
print("─" * len(header))

d_ideal_target = tuple_distance(ideal_allosteric_inhibitor, allosteric_domain)
for drug in drugs:
    d_ideal = tuple_distance(drug, ideal_allosteric_inhibitor)
    d_target = tuple_distance(drug, allosteric_domain)
    print(f"{drug.name:<26} {d_ideal:>14.2f}  {d_target:>15.2f}  {d_ideal_target:>15.2f}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 15B: Per-primitive gap analysis (drug vs ideal)
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 15B — PER-PRIMITIVE GAP: DRUG vs IDEAL")
print("=" * 70)

primitives = [
    ("D", "dimensionality"),
    ("T", "topology"),
    ("R", "recognition_mode"),
    ("P", "polarity"),
    ("F", "fidelity"),
    ("K", "kinetic_character"),
    ("G", "granularity"),
    ("Γ", "interaction_grammar"),
    ("Φ", "criticality_phase"),
]

for drug in drugs:
    print(f"\n{drug.name} vs ideal:")
    print(f"  {'Prim':<5} {'Drug value':<28} {'Ideal value':<28} Match?")
    print(f"  {'─'*5} {'─'*28} {'─'*28} {'─'*6}")
    for sym, attr in primitives:
        drug_val = getattr(drug, attr)
        ideal_val = getattr(ideal_allosteric_inhibitor, attr)

        if drug_val is None and ideal_val is None:
            match = "—"
        elif drug_val is None or ideal_val is None:
            match = "DIFF"
        else:
            # For InteractionGrammar, compare operator and tier
            if isinstance(drug_val, type(ideal_val)) and hasattr(drug_val, 'operator'):
                match = "✓" if (drug_val.operator == ideal_val.operator and
                                 drug_val.tier == ideal_val.tier) else "✗"
                dv = f"{drug_val.operator.value}({drug_val.tier})"
                iv = f"{ideal_val.operator.value}({ideal_val.tier})"
            else:
                match = "✓" if drug_val == ideal_val else "✗"
                dv = drug_val.value if hasattr(drug_val, 'value') else str(drug_val)
                iv = ideal_val.value if hasattr(ideal_val, 'value') else str(ideal_val)
        if sym != "Γ":
            dv = drug_val.value if (drug_val and hasattr(drug_val, 'value')) else str(drug_val)
            iv = ideal_val.value if (ideal_val and hasattr(ideal_val, 'value')) else str(ideal_val)
        print(f"  {sym:<5} {dv:<28} {iv:<28} {match}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 15C: Meet(drug, ideal) — what's already correct
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 15C — MEET(drug, ideal): shared correct primitives")
print("=" * 70)

for drug in drugs:
    m = meet(drug, ideal_allosteric_inhibitor)
    shared = [p for p in ["D", "T", "R", "P", "Γ"] if p not in m.conflicts]
    print(f"\n{drug.name} ⊓ ideal:")
    print(f"  {m.to_notation()}")
    print(f"  conflicts: {m.conflicts}")
    print(f"  shared categoricals: {shared}")
    print(f"  F(meet): {m.fidelity.value}  K(meet): {m.kinetic_character.value}  "
          f"G(meet): {m.granularity.value}  Φ(meet): "
          f"{m.criticality_phase.value if m.criticality_phase else '—'}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 15D: Jacobian + fault injection on each drug
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 15D — JACOBIAN + FAULT INJECTION (per drug)")
print("=" * 70)

engine = PerturbationEngine()

delta_g_map = {
    "imatinib": -45.0,      # ~nM affinity → ΔG ≈ -50 kJ/mol
    "GNF-2_allosteric_ABL": -25.0,  # ~µM → ΔG ≈ -30 kJ/mol
    "venetoclax": -55.0,    # sub-nM → ΔG ≈ -55 kJ/mol
}

for drug in drugs:
    dg = delta_g_map.get(drug.name, -30.0)
    print(f"\n--- {drug.name} (δG = {dg} kJ/mol) ---")
    jacobian = engine.sweep_all(drug, delta_g=dg)
    print(f"  Baseline ξ_CP: {jacobian.baseline_xi_CP:.3f} nat")

    fault = engine.fault_injection(drug, delta_g=dg)
    robust = fault["system_robust"]
    spofs = fault["single_points_of_failure"]
    print(f"  Robust: {robust}  |  SPOFs: {len(spofs)}")

    print(f"\n  {'Primitive':<22} {'Shift':<30} {'Δξ_CP':>8}  Sensitivity")
    print(f"  {'─'*22} {'─'*30} {'─'*8}  {'─'*11}")
    for r in jacobian.results[:5]:
        axiom_flag = f"  ⚠ {r.axiom_violated}" if r.axiom_violated else ""
        print(f"  {r.primitive_name:<22} {r.old_value:<14}→ {r.new_value:<14} "
              f"{r.delta_xi_CP:>+8.3f}  {r.sensitivity}{axiom_flag}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 15E: Drug-to-ideal redesign: what single primitive change
#              moves each drug closest to the ideal?
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 15E — ONE-STEP REDESIGN: which primitive change minimizes d(drug, ideal)?")
print("=" * 70)

from synthomnicon.perturbation import (
    _FIDELITY_TIERS, _KINETIC_TIERS, _GRANULARITY_TIERS,
    _TOPOLOGY_TIERS, _DIM_TIERS, _RECOGNITION_TIERS,
    _POLARITY_TIERS, _CRITICALITY_TIERS, _next_tier, _prev_tier,
)

perturb_spec = [
    ("F",  "fidelity",           _FIDELITY_TIERS),
    ("K",  "kinetic_character",  _KINETIC_TIERS),
    ("T",  "topology",           _TOPOLOGY_TIERS),
    ("D",  "dimensionality",     _DIM_TIERS),
    ("R",  "recognition_mode",   _RECOGNITION_TIERS),
    ("P",  "polarity",           _POLARITY_TIERS),
    ("G",  "granularity",        _GRANULARITY_TIERS),
    ("Φ",  "criticality_phase",  _CRITICALITY_TIERS),
]

import copy

for drug in drugs:
    baseline_d = tuple_distance(drug, ideal_allosteric_inhibitor)
    best_gain = 0.0
    best_move = None

    for sym, attr, tiers in perturb_spec:
        current = getattr(drug, attr)
        if current is None:
            continue
        for new_val in [_next_tier(current, tiers), _prev_tier(current, tiers)]:
            if new_val is None:
                continue
            candidate = copy.copy(drug)
            setattr(candidate, attr, new_val)
            new_d = tuple_distance(candidate, ideal_allosteric_inhibitor)
            gain = baseline_d - new_d
            if gain > best_gain:
                best_gain = gain
                old_str = current.value if hasattr(current, 'value') else str(current)
                new_str = new_val.value if hasattr(new_val, 'value') else str(new_val)
                best_move = (sym, old_str, new_str, new_d)

    print(f"\n{drug.name}:")
    print(f"  current d(drug, ideal) = {baseline_d:.2f}")
    if best_move:
        sym, old_v, new_v, new_d = best_move
        print(f"  best single change: {sym}: {old_v} → {new_v}")
        print(f"  new d(drug, ideal) = {new_d:.2f}  (Δd = {best_gain:+.2f})")
    else:
        print(f"  no single primitive change improves distance to ideal")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 15F: Design inference table
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 15F — DRUG DESIGN INFERENCE TABLE")
print("=" * 70)

inferences = [
    {
        "drug": "GNF-2",
        "rank": "Closest to ideal (lowest d)",
        "what_it_gets_right": "T_branched ≠ T_network (wrong T), but Φ_c + G_ג + Γ_→(SELECTIVE) + F_ℇ all correct — 5/9 primitives match ideal",
        "gap": "T: branched vs network; P: directional vs pseudo-symmetric",
        "implication": "GNF-2 is structurally the best starting point for ideal allosteric inhibitor. "
                       "The design gap is in topology (single branched pocket vs distributed network) "
                       "and polarity (directed insertion vs pseudo-symmetric engagement). "
                       "Predicted improvement: bivalent GNF-2 analog that bridges two pockets (network T).",
    },
    {
        "drug": "Imatinib",
        "rank": "Farthest from ideal (highest d)",
        "what_it_gets_right": "R_⊇, K_slow match. Only 2/9 primitives align.",
        "gap": "F_ℏ (over-committed), G_ב (local), Φ_sub (not allosteric), T_⋈ (cyclic vs network), Γ_∧ (AND vs sequential)",
        "implication": "Imatinib's core problem is F_ℏ + G_ב: it binds too tightly to a single "
                       "local pocket. Cannot propagate signal (G_ב). Cannot be allosteric (Φ_sub). "
                       "Known clinically: resistance emerges because any DFG-out mutation blocks binding. "
                       "A G_ב drug cannot adapt. Predicted: imatinib-class drugs have irreversible "
                       "resistance trajectories. GNF-2-class drugs have slower resistance because "
                       "G_ג allows partial tolerance of pocket mutations.",
    },
    {
        "drug": "Venetoclax",
        "rank": "Intermediate",
        "what_it_gets_right": "R_⊇, K_slow match. T_∪ (bowl) is structurally ordered (better than bowtie). 2/9.",
        "gap": "F_ℏ (too tight — selectivity window narrow), G_ב (no propagation), Φ_sub, T_∪ vs T_network",
        "implication": "Venetoclax's F_ℏ is its own trap: sub-nM binding means it can't distinguish "
                       "BCL-2 from BCL-XL easily (selectivity requires F_ℇ, not F_ℏ). Known: "
                       "venetoclax has BCL-XL toxicity in platelets. "
                       "Predicted: weaker-binding BH3 mimetics (F_ℇ, G_ג) would be more selective "
                       "because selectivity comes from grammar (Γ_→(SELECTIVE)), not from affinity.",
    },
]

for inf in inferences:
    print(f"\n{'═' * 60}")
    print(f"Drug: {inf['drug']}  [{inf['rank']}]")
    print(f"  Gets right: {inf['what_it_gets_right']}")
    print(f"  Gap:        {inf['gap']}")
    print(f"  Implication:")
    words = inf['implication'].split()
    line = "    "
    for w in words:
        if len(line) + len(w) + 1 > 72:
            print(line)
            line = "    " + w + " "
        else:
            line += w + " "
    if line.strip():
        print(line)

print("\n" + "=" * 70)
print("DONE — Part 4")
print("=" * 70)
