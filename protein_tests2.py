"""
Protein Science Tests — Part 2

Sections 7–10:
  7. Path search (folding routes, misfolding trap)
  8. Cross-domain analogy search (catalog nearest-neighbors to protein synthons)
  9. Varma probe on allosteric_domain (Φ_c candidacy scoring)
 10. Prediction table (testable consequences from the algebra)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from synthomnicon.models import (
    Synthon, Dimensionality, Topology, RecognitionMode, Polarity,
    Fidelity, KineticCharacter, Granularity, InteractionGrammar,
    CriticalityPhase, TopoIndex,
)
from synthomnicon.algebra import (
    tuple_distance, meet, join, tensor, find_path, CONFLICT,
)
from synthomnicon.varma_probe import (
    VarmaCorrelationData, score_phi_c_candidacy, degeneracy_strength,
    check_logarithmic_scaling,
)
from synthomnicon.registry import global_catalog

# ─────────────────────────────────────────────────────────────────────────────
# Rebuild the five core protein synthons (from Part 1)
# ─────────────────────────────────────────────────────────────────────────────

alpha_helix = Synthon(
    name="alpha_helix",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.LINEAR,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.SELF_COMPLEMENTARY_PSEUDO,
    fidelity=Fidelity.HIGH,
    kinetic_character=KineticCharacter.FAST,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_SEQ,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Alpha-helix",
)

beta_hairpin = Synthon(
    name="beta_hairpin",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.CYCLIC_BOWTIE,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.SELF_COMPLEMENTARY_SYM,
    fidelity=Fidelity.HIGH,
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Beta-hairpin",
)

active_site = Synthon(
    name="active_site",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.CYCLIC_BOWTIE,
    recognition_mode=RecognitionMode.DYNAMIC_CATALYTIC,
    polarity=Polarity.DONOR_ACCEPTOR,
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.MESOSCALE,
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Enzyme active site",
)

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
    description="Allosteric domain (Phi_c candidate)",
)

protein_complex = Synthon(
    name="protein_complex",
    dimensionality=Dimensionality.HYBRID_MOL_SUPRA,
    topology=Topology.NETWORK,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.SELF_COMPLEMENTARY_SYM,
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.SLOW,
    granularity=Granularity.GLOBAL,
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Protein complex",
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: PATH SEARCH
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("SECTION 7 — FOLDING PATHS (HotSwap BFS)")
print("=" * 70)

# ── 7A. Path through D_wedge + T_bowtie space ────────────────────────────────
# active_site and beta_hairpin share this class.
# Build intermediate states that are physically meaningful.

# Early folding nucleus: R_⊇, P_sym, F_med, K_mod (before catalytic specialization)
proto_active = Synthon(
    name="proto_active_fold",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.CYCLIC_BOWTIE,
    recognition_mode=RecognitionMode.NON_COVALENT,     # Not yet catalytic
    polarity=Polarity.SELF_COMPLEMENTARY_SYM,
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.LOCAL,                     # Not yet mesoscale
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Early folded nucleus — symmetric, non-catalytic cyclic motif",
)

# Misfolded trap: same D+T, but P_pm_pseudo → wrong symmetry, F_high (over-committed), K_trap
misfolded_beta = Synthon(
    name="misfolded_beta_aggregate",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.CYCLIC_BOWTIE,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.SELF_COMPLEMENTARY_PSEUDO,       # P mismatch — amyloid-like pseudo-symmetry
    fidelity=Fidelity.HIGH,                            # Over-committed — can't escape
    kinetic_character=KineticCharacter.TRAP,           # Trapped in misfolded state
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.BROAD_OR,   # Lost specificity
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    description="Misfolded beta-aggregate (amyloid precursor): trapped, F_high, specificity lost",
)

# Catalog for D_wedge + T_bowtie space
bowtie_catalog = [beta_hairpin, active_site, proto_active, misfolded_beta]

print("\n[D_wedge + T_bowtie space]")

# 7A-i: beta_hairpin → active_site (normal functional path)
p1 = find_path(beta_hairpin, active_site, catalog=bowtie_catalog, max_hops=6)
print(f"\nbeta_hairpin → active_site:")
print(f"  found: {p1.found}")
if p1.found:
    print(f"  path:  {' → '.join(p1.path)}")
    print(f"  hops:  {p1.n_hops}  |  total Δξ: {p1.total_delta:.2f}")
else:
    print(f"  notes: {p1.notes}")

# 7A-ii: beta_hairpin → misfolded_beta (misfolding)
p2 = find_path(beta_hairpin, misfolded_beta, catalog=bowtie_catalog, max_hops=6)
print(f"\nbeta_hairpin → misfolded_beta_aggregate (misfolding path):")
print(f"  found: {p2.found}")
if p2.found:
    print(f"  path:  {' → '.join(p2.path)}")
    print(f"  hops:  {p2.n_hops}  |  total Δξ: {p2.total_delta:.2f}")
else:
    print(f"  notes: {p2.notes}")

# 7A-iii: active_site → misfolded_beta (denaturation + trap)
p3 = find_path(active_site, misfolded_beta, catalog=bowtie_catalog, max_hops=6)
print(f"\nactive_site → misfolded_beta_aggregate (denaturation trap):")
print(f"  found: {p3.found}")
if p3.found:
    print(f"  path:  {' → '.join(p3.path)}")
    print(f"  hops:  {p3.n_hops}  |  total Δξ: {p3.total_delta:.2f}")
    print(f"  hop Δξ values: {[f'{x:.2f}' for x in p3.hop_deltas]}")
else:
    print(f"  notes: {p3.notes}")

# ── 7B. Path through D_hybrid + T_network space ──────────────────────────────
# allosteric_domain and protein_complex share this class.
# Intermediates: partial assembly states.

# Intermediate 1: signal committed, but G not yet global (G_mesoscale → G_global transition)
partial_assembly = Synthon(
    name="partial_assembly",
    dimensionality=Dimensionality.HYBRID_MOL_SUPRA,
    topology=Topology.NETWORK,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.DONOR_ACCEPTOR,                  # Still directional (signal mode)
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.MODERATE,       # Partially assembled
    granularity=Granularity.MESOSCALE,                 # G still mesoscale
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,  # AND (committed) not yet sequential
    criticality_phase=CriticalityPhase.CRITICAL,       # Phi_c propagates
    description="Partial assembly: committed AND grammar, G still mesoscale, Phi_c retained",
)

# Intermediate 2: fully assembled interface, lost sequential grammar, G now global
committed_interface = Synthon(
    name="committed_interface",
    dimensionality=Dimensionality.HYBRID_MOL_SUPRA,
    topology=Topology.NETWORK,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.SELF_COMPLEMENTARY_SYM,          # Interface symmetry locks in
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.SLOW,            # Slow (committed)
    granularity=Granularity.GLOBAL,                    # G_aleph: global function
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,    # Phi_c lost at assembly completion
    description="Committed interface: G_aleph, symmetric, slow, Phi_c lost",
)

network_catalog = [allosteric_domain, protein_complex, partial_assembly, committed_interface]

print(f"\n[D_hybrid_mol_supra + T_network space]")

# 7B-i: allosteric_domain → protein_complex (signaling → assembly)
p4 = find_path(allosteric_domain, protein_complex, catalog=network_catalog, max_hops=6)
print(f"\nallosteric_domain → protein_complex:")
print(f"  found: {p4.found}")
if p4.found:
    print(f"  path:  {' → '.join(p4.path)}")
    print(f"  hops:  {p4.n_hops}  |  total Δξ: {p4.total_delta:.2f}")
    print(f"  hop Δξ values: {[f'{x:.2f}' for x in p4.hop_deltas]}")
else:
    print(f"  notes: {p4.notes}")

# 7B-ii: protein_complex → allosteric_domain (disassembly / signal reinstatement)
p5 = find_path(protein_complex, allosteric_domain, catalog=network_catalog, max_hops=6)
print(f"\nprotein_complex → allosteric_domain (disassembly):")
print(f"  found: {p5.found}")
if p5.found:
    print(f"  path:  {' → '.join(p5.path)}")
    print(f"  hops:  {p5.n_hops}  |  total Δξ: {p5.total_delta:.2f}")
else:
    print(f"  notes: {p5.notes}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: CROSS-DOMAIN ANALOGY SEARCH
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 8 — CROSS-DOMAIN ANALOGIES (nearest catalog neighbors)")
print("=" * 70)

# Load the global catalog (populated from synthomnicon domains)
from synthomnicon.domains.molecular import register_molecular_synthons
from synthomnicon.domains.quantum import register_quantum_synthons
from synthomnicon.cross_domain import register_cross_domain_synthons
import synthomnicon  # triggers __init__ catalog population

register_molecular_synthons()
register_quantum_synthons()
register_cross_domain_synthons()

catalog_list = list(global_catalog._synthons.values())
print(f"\nCatalog loaded: {len(catalog_list)} synthons")

protein_synthons = [alpha_helix, beta_hairpin, active_site, allosteric_domain, protein_complex]

print("\nNearest catalog analogs (top 3 per protein synthon, symmetric distance):\n")

for ps in protein_synthons:
    scored = []
    for cs in catalog_list:
        if cs.name in {ps.name}:
            continue
        d = tuple_distance(ps, cs)
        scored.append((d, cs.name, cs.description[:60] if cs.description else ""))
    scored.sort(key=lambda x: x[0])

    print(f"{ps.name}:")
    for rank, (d, name, desc) in enumerate(scored[:3], 1):
        print(f"  {rank}. d={d:.2f}  {name}")
        if desc:
            print(f"       └─ {desc}")
    print()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9: VARMA PROBE ON ALLOSTERIC DOMAIN
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("SECTION 9 — VARMA PROBE: allosteric_domain Φ_c scoring")
print("=" * 70)

# The Varma probe expects correlation data (xi_r, xi_tau, delta).
# For the allosteric domain, we use NMR-analogous assignments:
# - Rex (µs-ms conformational exchange) ↔ xi_tau ~ 100-1000
# - Spatial allosteric propagation ~3-5 nm → xi_r ~ 30-50 (Å units)
# - delta = distance from critical signal threshold

scenarios = [
    ("allosteric_on_state",        VarmaCorrelationData(xi_r=40.0,  xi_tau=500.0, delta=0.05)),
    ("allosteric_off_state",       VarmaCorrelationData(xi_r=5.0,   xi_tau=20.0,  delta=0.50)),
    ("allosteric_cooperative_peak",VarmaCorrelationData(xi_r=35.0,  xi_tau=400.0, delta=0.02)),
]

for label, cdata in scenarios:
    report = score_phi_c_candidacy(allosteric_domain, correlation_data=cdata)
    s, stype = degeneracy_strength(allosteric_domain, correlation_data=cdata)
    is_log, ratio = check_logarithmic_scaling(cdata.xi_r, cdata.xi_tau)
    print(f"\n{label}:")
    print(f"  xi_r = {cdata.xi_r:.1f}, xi_tau = {cdata.xi_tau:.1f}, delta = {cdata.delta}")
    print(f"  ξ_r ≈ ln ξ_τ satisfied: {is_log}  (ratio = {ratio:.3f})")
    print(f"  degeneracy_strength (s): {s:.3f}  [{stype}]")
    print(f"  Φ_c score: {report.score:.3f}  → {report._candidacy_label()}")
    print(f"  G/D degenerate: {report.gd_degenerate}  ({report.gd_degeneracy_type})")
    if report.flags:
        print(f"  flags: {report.flags[:2]}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 10: PREDICTION TABLE
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 10 — TESTABLE PREDICTIONS FROM THE ALGEBRA")
print("=" * 70)

predictions = [
    {
        "id": "P-PROT-1",
        "source": "§2 distance matrix",
        "prediction": "Active site and beta-hairpin are structurally closer (d=2.80) than "
                      "active site and alpha-helix (d=5.40). Enzymes built from beta-sheet "
                      "scaffolds should show higher structural tolerance for active-site "
                      "residue substitution than helix-bundle enzymes.",
        "test": "Compare active-site RMSD after alanine scanning in TIM barrel (β) vs "
                "4-helix-bundle cytochrome.",
        "tier": "II",
    },
    {
        "id": "P-PROT-2",
        "source": "§4 tensor: K_slow bottleneck",
        "prediction": "The rate-limiting step in formation of a multi-domain allosteric "
                      "enzyme complex is set by the K_slow (quaternary assembly) component, "
                      "not by domain folding or active-site maturation. k_obs for full "
                      "complex assembly < k_obs for isolated domain folding.",
        "test": "Stopped-flow: compare k_fold for isolated domains vs k_assemble for full "
                "complex. Predict: k_assemble is slowest.",
        "tier": "II",
    },
    {
        "id": "P-PROT-3",
        "source": "§5 Φ_c on allosteric_domain; §9 Varma probe s≥0.7 in on-state",
        "prediction": "Allosteric domains near their critical switching point will show "
                      "power-law distributed conformational fluctuations (NMR Rex rates "
                      "spanning 3+ decades of frequency) in the ON state but not the OFF state.",
        "test": "CPMG relaxation dispersion experiments on a model two-state allosteric "
                "switch (e.g., CAP protein). Predict: Rex rates in ON state fit 1/τ spectrum; "
                "OFF state shows single Lorentzian.",
        "tier": "III",
    },
    {
        "id": "P-PROT-4",
        "source": "§6 directed distance: β→α (2.90) < α→β (3.40)",
        "prediction": "For a peptide in the α-helix / β-hairpin competition regime, "
                      "β→α conversion is kinetically preferred over α→β. The F-floor "
                      "ratchet predicts: alpha-nucleating conditions should rescue "
                      "amyloidogenic β-aggregates more easily than the reverse.",
        "test": "Add helix-stabilizing osmolytes (TMAO) to pre-formed β-aggregates vs "
                "add β-sheet-promoting conditions to α-helix. Measure conversion rate "
                "by CD/ThT fluorescence.",
        "tier": "II",
    },
    {
        "id": "P-PROT-5",
        "source": "§3 meet: allosteric_domain ⊓ protein_complex → 2 conflicts (P, Γ) + Φ_c",
        "prediction": "Chimeric proteins that fuse an allosteric domain with a protein "
                      "complex interface will retain criticality (Φ_c propagates in meet) "
                      "but will show P and Γ conflicts — manifesting as broken "
                      "cooperativity (Hill coeff → 1) without loss of binding.",
        "test": "Engineer a fusion of an allosteric regulatory domain onto a homodimer "
                "interface. Measure ITC (binding preserved) and Hill coefficient (cooperativity "
                "reduced toward 1).",
        "tier": "III",
    },
    {
        "id": "P-PROT-6",
        "source": "§4 tensor R-note: R_dagger ⊗ R_superset → R_superset (allosteric wins)",
        "prediction": "In an allosteric enzyme, the dominant recognition grammar at the "
                      "ensemble level is non-covalent (allosteric signal), not catalytic "
                      "(R_‡). Inhibitors that target the allosteric site at F_ℇ level "
                      "will be more selective than active-site competitive inhibitors "
                      "targeting R_‡, because F_ℇ < F_ℏ means lower off-target binding.",
        "test": "Compare selectivity profiles (Kd off-target / Kd on-target) of allosteric "
                "vs orthosteric inhibitors for the same enzyme family.",
        "tier": "II",
    },
]

for p in predictions:
    print(f"\n{p['id']} (Tier {p['tier']}) — source: {p['source']}")
    print(f"  PREDICTION: {p['prediction']}")
    print(f"  TEST:       {p['test']}")

print("\n" + "=" * 70)
print("DONE — Part 2")
print("=" * 70)
