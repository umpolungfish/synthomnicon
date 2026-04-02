"""
Protein Science Encoding Tests — SynthOmnicon

Five structural units encoded as synthons; run algebra operations
to extract structural relationships, conflicts, and criticality signals.

Units (from DSCONVo.txt encoding table):
  1. alpha_helix       — backbone H-bond ratchet
  2. beta_hairpin      — antiparallel sheet pair
  3. active_site       — enzyme catalytic pocket
  4. allosteric_domain — long-range conformational signal transducer
  5. protein_complex   — quaternary interface assembly
"""

import sys
import os

# Ensure local package takes precedence
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from synthomnicon.models import (
    Synthon, Dimensionality, Topology, RecognitionMode, Polarity,
    Fidelity, KineticCharacter, Granularity, InteractionGrammar,
    CriticalityPhase, TopoIndex,
)
from synthomnicon.algebra import (
    tuple_distance, meet, join, tensor, CONFLICT,
)
from synthomnicon.criticality import analyze_criticality

# ─────────────────────────────────────────────────────────────────────────────
# ENCODE THE FIVE PROTEIN SYNTHONS
# ─────────────────────────────────────────────────────────────────────────────

alpha_helix = Synthon(
    name="alpha_helix",
    dimensionality=Dimensionality.MOLECULAR,           # D_∧ — backbone H-bonds, local geometry
    topology=Topology.LINEAR,                          # T_| — sequential N→C directionality
    recognition_mode=RecognitionMode.NON_COVALENT,     # R_⊇ — backbone N-H···O=C H-bonds
    polarity=Polarity.SELF_COMPLEMENTARY_PSEUDO,       # P_±^ψ — i→i+4, pseudo-periodic
    fidelity=Fidelity.HIGH,                            # F_ℏ — helical H-bonds reliable, geometry-enforcing
    kinetic_character=KineticCharacter.FAST,           # K_fast — helix nucleation ~ns
    granularity=Granularity.LOCAL,                     # G_ב — single-turn H-bond local constraint
    interaction_grammar=InteractionGrammar.SELECTIVE_SEQ,  # Γ_→(SELECTIVE) — sequential N→C
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Alpha-helical backbone: i→i+4 N-H···O=C H-bond ratchet, 3.6 residues/turn",
)

beta_hairpin = Synthon(
    name="beta_hairpin",
    dimensionality=Dimensionality.MOLECULAR,           # D_∧ — strand-strand contacts
    topology=Topology.CYCLIC_BOWTIE,                   # T_⋈ — turn + two antiparallel strands = cyclic-like closure
    recognition_mode=RecognitionMode.NON_COVALENT,     # R_⊇ — cross-strand H-bonds
    polarity=Polarity.SELF_COMPLEMENTARY_SYM,          # P_±^sym — strand-strand true complementarity
    fidelity=Fidelity.HIGH,                            # F_ℏ — β-sheet H-bonds strong
    kinetic_character=KineticCharacter.MODERATE,       # K_mod — β-hairpin folding µs range
    granularity=Granularity.LOCAL,                     # G_ב — pair of strands, local constraint
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,   # Γ_∧(SPECIFIC) — both strands required
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Beta-hairpin: antiparallel strand pair with loop; self-complementary H-bond pattern",
)

active_site = Synthon(
    name="active_site",
    dimensionality=Dimensionality.MOLECULAR,           # D_∧ — chemical transformation at single locus
    topology=Topology.CYCLIC_BOWTIE,                   # T_⋈ — catalytic cycle: substrate in → product out
    recognition_mode=RecognitionMode.DYNAMIC_CATALYTIC, # R_‡ — transition state stabilization
    polarity=Polarity.DONOR_ACCEPTOR,                  # P_+- — directional: substrate → TS → product
    fidelity=Fidelity.MEDIUM,                          # F_ℇ — context-dependent on substrate fit
    kinetic_character=KineticCharacter.MODERATE,       # K_mod — enzyme k_cat 10¹–10⁶ s⁻¹
    granularity=Granularity.MESOSCALE,                 # G_ג — pocket geometry affects full substrate
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,   # Γ_∧(SPECIFIC) — substrate AND cofactor required
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Enzyme active site: transition-state stabilizer, directional substrate→product cycle",
)

allosteric_domain = Synthon(
    name="allosteric_domain",
    dimensionality=Dimensionality.HYBRID_MOL_SUPRA,    # {D_∧, D_△} — signal crosses length scales
    topology=Topology.NETWORK,                         # T_∈ — network of contacts carries perturbation
    recognition_mode=RecognitionMode.NON_COVALENT,     # R_⊇ — non-covalent signal propagation
    polarity=Polarity.DONOR_ACCEPTOR,                  # P_+- — allosteric site → active site (directed)
    fidelity=Fidelity.MEDIUM,                          # F_ℇ — conditional on signal molecule present
    kinetic_character=KineticCharacter.MODERATE,       # K_mod — conformational rearrangement ms range
    granularity=Granularity.MESOSCALE,                 # G_ג — mesoscale: signal spans domain
    interaction_grammar=InteractionGrammar.SELECTIVE_SEQ,  # Γ_→(SELECTIVE) — effector → conform. change → activity
    criticality_phase=CriticalityPhase.CRITICAL,       # Φ_c — G/D degeneracy candidate: molecular signal → global effect
    description="Allosteric domain: non-covalent long-range signal transducer; Phi_c candidate (molecular → global scale)",
)

protein_complex = Synthon(
    name="protein_complex",
    dimensionality=Dimensionality.HYBRID_MOL_SUPRA,    # {D_∧, D_△} — interface chemistry + 3D assembly
    topology=Topology.NETWORK,                         # T_∈ — interface network of buried contacts
    recognition_mode=RecognitionMode.NON_COVALENT,     # R_⊇ — hydrophobic + H-bond + electrostatic
    polarity=Polarity.SELF_COMPLEMENTARY_SYM,          # P_±^sym — shape + charge complementarity across interface
    fidelity=Fidelity.MEDIUM,                          # F_ℇ — weaker than covalent; can dissociate
    kinetic_character=KineticCharacter.SLOW,            # K_slow — quaternary assembly slow, seconds–minutes
    granularity=Granularity.GLOBAL,                    # G_א — whole complex function determined globally
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,   # Γ_∧(SPECIFIC) — specific subunit:subunit recognition
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Protein complex: quaternary interface assembly; global function from specific subunit recognition",
)

synthons = [alpha_helix, beta_hairpin, active_site, allosteric_domain, protein_complex]

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: NOTATION
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("SECTION 1 — SYNTHON NOTATION")
print("=" * 70)
for s in synthons:
    print(f"\n{s.name}:")
    print(f"  {s.to_notation()}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: PAIRWISE DISTANCES
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 2 — PAIRWISE TUPLE DISTANCES")
print("=" * 70)

names = [s.name for s in synthons]
print(f"\n{'':20s}", end="")
for n in names:
    print(f"{n[:12]:>13s}", end="")
print()

for s1 in synthons:
    print(f"{s1.name[:20]:20s}", end="")
    for s2 in synthons:
        d = tuple_distance(s1, s2)
        print(f"{d:>13.2f}", end="")
    print()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: MEET AND JOIN
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 3 — MEET AND JOIN")
print("=" * 70)

# Key pairs
pairs = [
    (alpha_helix, beta_hairpin, "secondary structure meet"),
    (active_site, allosteric_domain, "function-level meet (signaling ∩ catalysis)"),
    (allosteric_domain, protein_complex, "domain-level meet"),
    (alpha_helix, active_site, "structure ∩ function"),
]

for s1, s2, label in pairs:
    m = meet(s1, s2)
    j = join(s1, s2)

    def _val(x):
        if x == CONFLICT:
            return "CONFLICT"
        return x.value if hasattr(x, "value") else str(x)

    print(f"\n--- {label} ---")
    print(f"  {s1.name} ⊓ {s2.name}:")
    print(f"    {m.to_notation()}")
    print(f"    F: {_val(m.fidelity)}  K: {_val(m.kinetic_character)}  G: {_val(m.granularity)}  conflicts: {m.conflicts}")
    print(f"  {s1.name} ⊔ {s2.name}:")
    print(f"    {j.to_notation()}")
    print(f"    F: {_val(j.fidelity)}  K: {_val(j.kinetic_character)}  G: {_val(j.granularity)}  conflicts: {j.conflicts}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: TENSOR PRODUCTS (ENSEMBLE)
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 4 — TENSOR PRODUCTS (ENSEMBLE ENCODING)")
print("=" * 70)

def tensor_chain(*syns):
    """Chain tensor left-associatively across >2 synthons, returning a TensorResult."""
    from synthomnicon.models import (
        Synthon, Dimensionality, Topology, RecognitionMode, Polarity,
        Fidelity, KineticCharacter, Granularity, InteractionGrammar,
        CriticalityPhase,
    )
    result = tensor(syns[0], syns[1])
    for s in syns[2:]:
        # Wrap the TensorResult as a scratch Synthon so tensor() can consume it
        # Use the primitives from result, falling back to defaults for None/CONFLICT
        def _safe(x, default):
            return x if (x is not None and x != CONFLICT) else default
        tmp = Synthon(
            name=f"{result.s1_name}_{result.s2_name}_tensor",
            dimensionality=_safe(result.dimensionality, Dimensionality.HYBRID_ALL),
            topology=_safe(result.topology, Topology.NETWORK),
            recognition_mode=_safe(result.recognition_mode, RecognitionMode.NON_COVALENT),
            polarity=_safe(result.polarity, Polarity.SELF_COMPLEMENTARY_PSEUDO),
            fidelity=_safe(result.fidelity, Fidelity.LOW),
            kinetic_character=_safe(result.kinetic_character, KineticCharacter.SLOW),
            granularity=_safe(result.granularity, Granularity.GLOBAL),
            interaction_grammar=_safe(result.interaction_grammar, InteractionGrammar.BROAD_OR),
            criticality_phase=_safe(result.criticality_phase, CriticalityPhase.SUBCRITICAL),
        )
        result = tensor(tmp, s)
    return result

# active_site ⊗ allosteric_domain: allosteric enzyme
t1 = tensor(active_site, allosteric_domain)
print(f"\nactive_site ⊗ allosteric_domain (allosteric enzyme):")
print(f"  {t1.to_notation()}")
print(f"  notes: {t1.notes[:3] if t1.notes else 'none'}")

# alpha_helix ⊗ beta_hairpin: mixed secondary structure
t2 = tensor(alpha_helix, beta_hairpin)
print(f"\nalpha_helix ⊗ beta_hairpin (mixed secondary structure motif):")
print(f"  {t2.to_notation()}")
print(f"  notes: {t2.notes[:3] if t2.notes else 'none'}")

# full protein: all five ⊗ chained
t_all = tensor_chain(alpha_helix, beta_hairpin, active_site, allosteric_domain, protein_complex)
print(f"\nAll five ⊗ (full allosteric enzyme complex):")
print(f"  {t_all.to_notation()}")
print(f"  notes: {t_all.notes[:4] if t_all.notes else 'none'}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: CRITICALITY ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 5 — CRITICALITY ANALYSIS")
print("=" * 70)

for s in synthons:
    analysis = analyze_criticality(s)
    print(f"\n{s.name}:")
    print(f"  is_critical: {analysis.is_critical}")
    print(f"  confidence:  {analysis.confidence:.2f}")
    print(f"  indicators:  {analysis.indicators}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: DIRECTED DISTANCES (HOTSWAP PATHS)
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 6 — DIRECTED DISTANCES (design direction)")
print("=" * 70)

# Misfolding: alpha_helix → beta_hairpin direction (F/K uphill or downhill?)
d_helix_to_beta = tuple_distance(alpha_helix, beta_hairpin, symmetric=False)
d_beta_to_helix = tuple_distance(beta_hairpin, alpha_helix, symmetric=False)
print(f"\nalpha_helix → beta_hairpin (directed): {d_helix_to_beta:.2f}")
print(f"beta_hairpin → alpha_helix (directed): {d_beta_to_helix:.2f}")
print(f"  (asymmetry = {abs(d_helix_to_beta - d_beta_to_helix):.2f} nats — misfolding has a direction)")

# Folding: unfolded (low F, fast K, local G) → active_site
unfolded_state = Synthon(
    name="unfolded_polypeptide",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.CHAIN,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.SELF_COMPLEMENTARY_PSEUDO,
    fidelity=Fidelity.LOW,
    kinetic_character=KineticCharacter.FAST,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.BROAD_OR,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Unfolded/denatured polypeptide chain — high conformational entropy, no committed structure",
)

d_unfold_to_active = tuple_distance(unfolded_state, active_site, symmetric=False)
d_active_to_unfold = tuple_distance(active_site, unfolded_state, symmetric=False)
print(f"\nunfolded → active_site (directed): {d_unfold_to_active:.2f}")
print(f"active_site → unfolded (directed): {d_active_to_unfold:.2f}")
print(f"  (folding requires F↑, K↓, G↑ — thermodynamically uphill in kinetics, downhill in F)")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
