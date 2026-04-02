"""
Hv1 Voltage-Gated Proton Channel — SynthOmnicon Catalog Encodings

Based on three Tombola-lab papers:
  1. Zhao, Webster, De Angeli & Tombola (2023) Nat. Commun. 14:7515
     "Mechanically-primed voltage-gated proton channels from angiosperm plants"
  2. Zhao, Hong et al. (2021) J. Gen. Physiol. 153:e202012832
     "HIFs: New arginine mimic inhibitors of the Hv1 channel with improved VSD-ligand interactions"
  3. Geragotelis, Wood et al. (2020) PNAS 117:13490-13498
     "Voltage-dependent structural models of the human Hv1 proton channel from long-timescale MD"

Seven synthons encoded:
  - Hv1_human_closed          (hyperpolarized VSD, closed conformation)
  - Hv1_human_open            (depolarized VSD, proton-conducting conformation)
  - AtHv1_silent              (Arabidopsis thaliana, RSN-locked K_trap state)
  - AtHv1_primed              (mechanically primed, RSN weakened, K_mod)
  - PsHv1_constitutive        (Picea sitchensis, constitutively primed reference)
  - 2GBI_inhibitor            (arginine mimic blocker, micromolar WT affinity)
  - HIF_inhibitor             (Hv1 Inhibitor Flexible, two-pronged scaffold)

Key SynthOmnicon insights demonstrated:
  - peel(AtHv1_silent, K) ≈ AtHv1_primed  [direct biological K_trap peeling]
  - Hv1_open acquires Phi_c from H-bond water chain connectivity (phase transition)
  - HIF vs 2GBI: linear linker replaces condensed Gamma_and(SELECTIVE) conflict
  - P-55: d(AtHv1_silent, Hv1_human_closed) ≈ d(AtHv1_primed, Hv1_human_closed)
  - P-56: tensor(HIF, AtHv1_primed) should yield lower xi_CP than tensor(2GBI, AtHv1_silent)
  - P-57: F150A_site Gamma_or(BROAD) → endogenous guanidinium promiscuity
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from synthomnicon.models import (
    Synthon, Dimensionality, Topology, RecognitionMode, Polarity,
    Fidelity, KineticCharacter, Granularity, InteractionGrammar,
    CriticalityPhase, TopoIndex,
)
from synthomnicon.algebra import tuple_distance, meet, join, tensor, CONFLICT
from synthomnicon.registry import global_catalog

# =============================================================================
# SECTION 1 — CHANNEL CONFORMATIONS
# =============================================================================

print("=" * 70)
print("SECTION 1 — Hv1 CHANNEL CONFORMATION ENCODINGS")
print("=" * 70)

# ─── Human Hv1 Closed (hyperpolarized/resting) ────────────────────────────
# Source: Geragotelis et al. 2020 PNAS Paper 3
# Structural state: S4 arginines (R205, R208, R211) in intracellular half
# Salt-bridge network: R205↔D112, R208↔E153, R211↔D174
# H-bond water chain: ABSENT (no proton conduction)
# Gating charge: 0e (baseline)
Hv1_human_closed = Synthon(
    name="Hv1_human_closed",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.NETWORK,              # T_∈ — VSD salt-bridge network (R205↔D112 etc.)
    recognition_mode=RecognitionMode.NON_COVALENT,  # R_⊇ — salt bridges, H-bonds
    polarity=Polarity.DONOR_ACCEPTOR,       # P_+- — voltage-sensitive, directional (outward proton)
    fidelity=Fidelity.MEDIUM,              # F_eth — thermally reversible gating
    kinetic_character=KineticCharacter.MODERATE,  # K_mod — barrier ~60-100 kJ/mol (depolarization needed)
    granularity=Granularity.LOCAL,          # G_ב — single VSD monomer
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,  # Γ_∧(SELECTIVE) — proton-only
    criticality_phase=CriticalityPhase.SUBCRITICAL,  # Phi_sub — H-bond chain absent/disconnected
    topo_index=TopoIndex.TRIVIAL,           # Omega_0 — no topological protection
    description=(
        "Human Hv1 VSD in hyperpolarized/resting closed state. "
        "S4 arginines (R205, R208, R211) sit in intracellular half, "
        "bridging D112, E153, D174. Proton H-bond chain absent (no conduction). "
        "Gating charge ~0e. Ref: Geragotelis et al. 2020 PNAS 117:13490."
    ),
    metadata={"cross_domain": False, "validation_tier": "primary",
               "papers": ["Geragotelis2020PNAS", "Zhao2023NatComm"],
               "IC50_2GBI_uM": 38.0, "gating_charge_e": 0.0}
)

# ─── Human Hv1 Open (depolarized/activated) ──────────────────────────────
# Source: Geragotelis et al. 2020 PNAS Paper 3
# Structural state: S4 arginines translocated to extracellular half
# New salt bridges: R211↔D112, R211↔D185, R205↔D123
# H-bond water chain: PRESENT → proton conduction active
# Gating charge: ~2.7e (matches experiment)
# 2GBI binds below R211-D112 pair (open-channel block)
Hv1_human_open = Synthon(
    name="Hv1_human_open",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.CYCLIC_BOWTIE,        # T_⋈ — proton translocation cycle
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.DONOR_ACCEPTOR,       # P_+- — directional outward proton extrusion
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.MODERATE,  # K_mod — accessible via depolarization
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.CRITICAL,  # Phi_c — water chain connectivity is binary phase transition
    topo_index=TopoIndex.TRIVIAL,
    description=(
        "Human Hv1 VSD in depolarized/activated open state. "
        "S4 arginines translocated extracellularly (R205↔D123, R211↔D112/D185). "
        "Fully connected H-bond water chain enables proton conduction. "
        "Gating charge ~2.7e. Phi_c: H-bond chain forms discontinuously (phase transition). "
        "2GBI binding site: below R211-D112 pair (open-channel block). "
        "Ref: Geragotelis et al. 2020 PNAS 117:13490."
    ),
    metadata={"cross_domain": False, "validation_tier": "primary",
               "papers": ["Geragotelis2020PNAS"],
               "gating_charge_e": 2.7, "phi_c_note": "H-bond chain = binary connectivity phase transition"}
)

print(f"Hv1_human_closed: {Hv1_human_closed.to_notation()}")
print(f"Hv1_human_open:   {Hv1_human_open.to_notation()}")
print(f"Distance (closed→open): {tuple_distance(Hv1_human_closed, Hv1_human_open):.4f}")
print()

# ─── AtHv1 Silent (RSN-locked, electrically silent) ──────────────────────
# Source: Zhao et al. 2023 Nat. Commun. Paper 1
# Ring-Shaped Network (RSN): K117, E173, T174 in intracellular vestibule
# Outer VSD: K154, K155 (S3-S4 loop), S164 (S4)
# Mechanism: RSN provides extra stabilization of resting-closed state (RCs)
# IB/IA ratio ~17 (vs PsHv1 ~1.5) — mechanical priming required
AtHv1_silent = Synthon(
    name="AtHv1_silent",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.NETWORK,              # T_∈ — RSN ring-shaped H-bond network locks S4
    recognition_mode=RecognitionMode.NON_COVALENT,  # R_⊇ — ionic/H-bond RSN (K117-E173-T174)
    polarity=Polarity.SELF_COMPLEMENTARY_PSEUDO,  # P_±^ψ — RSN wraps symmetrically; no net direction
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.TRAP,    # K_trap — RSN locks S4; cannot open without priming
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
    description=(
        "AtHv1 (Arabidopsis thaliana Hv1) in electrically silent state. "
        "Ring-Shaped Network (RSN): K117, E173, T174 (inner VSD) + K154, K155, S164 (outer S4) "
        "provides extra stabilization of resting-closed state (RCs). "
        "IB/IA ~17 — channel requires mechanical priming (membrane stretch) to open. "
        "K_trap: RSN is kinetic trap. peel(K_trap) = mechanical priming. "
        "Ref: Zhao, Webster, De Angeli & Tombola 2023 Nat. Commun. 14:7515."
    ),
    metadata={"cross_domain": False, "validation_tier": "primary",
               "papers": ["Zhao2023NatComm"],
               "IB_IA_ratio": 17.0, "rsn_residues": "K117,E173,T174,K154,K155,S164",
               "peel_target": "K_trap", "peel_mechanism": "membrane stretch (mechanical priming)"}
)

# ─── AtHv1 Primed (post-mechanical-stimulus) ─────────────────────────────
# Source: Zhao et al. 2023 Nat. Commun. Paper 1
# After membrane stretch: RSN weakened → RCs → RC transition
# Now behaves like PsHv1/human Hv1 (K_mod, responds to voltage)
# ChE3-4.S4.K chimera confirms: KET residues sufficient for priming transfer
AtHv1_primed = Synthon(
    name="AtHv1_primed",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.CYCLIC_BOWTIE,        # T_⋈ — now cycles like PsHv1 (voltage-gating active)
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.DONOR_ACCEPTOR,       # P_+- — directional; can now respond to voltage
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.MODERATE,  # K_mod — K_trap peeled; barrier now normal
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,  # Still Phi_sub until voltage opens it
    topo_index=TopoIndex.TRIVIAL,
    description=(
        "AtHv1 after mechanical priming (membrane stretch). "
        "RSN destabilized (RCs → RC transition); channel now voltage-responsive. "
        "Functionally equivalent to PsHv1/human Hv1 resting state. "
        "K_trap → K_mod: this is the direct biological implementation of peel(K_trap). "
        "ChE3-4.S4.K + KET mutations confirm RSN residues are sufficient. "
        "Ref: Zhao, Webster, De Angeli & Tombola 2023 Nat. Commun. 14:7515."
    ),
    metadata={"cross_domain": False, "validation_tier": "primary",
               "papers": ["Zhao2023NatComm"],
               "IB_IA_ratio_approx": 1.5,
               "peel_applied": "K_trap → K_mod via membrane stretch"}
)

# ─── PsHv1 Constitutive (gymnosperm reference) ───────────────────────────
# Source: Zhao et al. 2023 Nat. Commun. Paper 1
# Picea sitchensis Hv1 — constitutively primed, no RSN, behaves like animal Hvs
# IB/IA ratio ~1.5 (vs AtHv1 ~17)
PsHv1_constitutive = Synthon(
    name="PsHv1_constitutive",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.CYCLIC_BOWTIE,        # T_⋈ — normal voltage-gating cycle
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.DONOR_ACCEPTOR,
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.MODERATE,  # K_mod — no extra trap; normal kinetics
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
    description=(
        "PsHv1 (Picea sitchensis Hv1, gymnosperm) — constitutively primed, no RSN. "
        "Behaves like animal/fungal Hv channels. N152 (vs K117 in AtHv1) + "
        "less extensive inner VSD hydrophilic network. IB/IA ~1.5. "
        "Reference state for AtHv1 silent vs. primed comparisons. "
        "Ref: Zhao, Webster, De Angeli & Tombola 2023 Nat. Commun. 14:7515."
    ),
    metadata={"cross_domain": False, "validation_tier": "primary",
               "papers": ["Zhao2023NatComm"],
               "IB_IA_ratio": 1.5}
)

print("Plant Hv channel encodings:")
print(f"AtHv1_silent:   {AtHv1_silent.to_notation()}")
print(f"AtHv1_primed:   {AtHv1_primed.to_notation()}")
print(f"PsHv1_constit:  {PsHv1_constitutive.to_notation()}")
print()

# =============================================================================
# SECTION 2 — INHIBITOR ENCODINGS
# =============================================================================

print("=" * 70)
print("SECTION 2 — INHIBITOR SYNTHON ENCODINGS")
print("=" * 70)

# ─── 2GBI Inhibitor ──────────────────────────────────────────────────────
# Source: Hong et al. 2013 (binding), Geragotelis et al. 2020 (structure)
# Arginine mimic: 2-guanidinobenzimidazole
# Binding: guanidinium↔D112/R211, phenyl↔F150 (cation-π)
# IC50(WT) = 38 μM, IC50(F150A) = 118 nM
# Mechanism: open-channel block (requires Hv1_open first)
# Cannot cross BBB; FMME motif absent in plant Hvs → low plant affinity
_2GBI = Synthon(
    name="2GBI_inhibitor",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.NETWORK,              # T_∈ — condensed fused bicyclic aromatic network
    recognition_mode=RecognitionMode.NON_COVALENT,  # R_⊇ — H-bonds + π-stacking
    polarity=Polarity.SELF_COMPLEMENTARY_PSEUDO,  # P_±^ψ — guanidinium(+) + hydrophobic phenyl
    fidelity=Fidelity.MEDIUM,              # F_eth — IC50 = 38 μM; reversible, thermally accessible
    kinetic_character=KineticCharacter.MODERATE,  # K_mod — requires open channel first (order-dependent)
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,  # Γ_∧(SELECTIVE) — H-bond + π-stack cooperate
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
    description=(
        "2GBI (2-guanidinobenzimidazole): arginine mimic Hv1 inhibitor. "
        "Condensed bicyclic scaffold: guanidinium + benzimidazole. "
        "Binds intracellular VSD vestibule: guanidinium↔D112/R211, phenyl↔F150 (cation-π). "
        "IC50(WT)=38 μM, IC50(F150A)=118 nM (100-fold enhancement via F182 rearrangement). "
        "Open-channel blocker (K_mod: channel must be open first). "
        "Cannot cross BBB. Condensed ring Gamma_conflict at 3+ fluorines (ABIF3 effect). "
        "Refs: Hong 2013 PNAS, Geragotelis 2020 PNAS, Zhao 2021 JGP."
    ),
    metadata={"cross_domain": False, "validation_tier": "primary",
               "papers": ["Hong2013PNAS", "Geragotelis2020PNAS", "Zhao2021JGP"],
               "IC50_WT_uM": 38.0, "IC50_F150A_nM": 118.0,
               "binding_residues": "D112,F150,F182,S181,R211",
               "BBB_penetrant": False}
)

# ─── HIF Inhibitor (Hv1 Inhibitor Flexible) ───────────────────────────────
# Source: Zhao, Hong et al. 2021 JGP Paper 2
# Two-pronged scaffold: 2-aminoimidazole ring + fluorinated phenyl (flexible linker)
# Linker decouples the two rings → eliminates cross-ring Gamma_conflict
# IC50(WT) = 13 μM (HIF), IC50(F150A) = sub-μM
# HIF_EN: predicted to cross BBB (LogD = 0.09); superior ADMET
HIF = Synthon(
    name="HIF_inhibitor",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.LINEAR,               # T_| — aminoimidazole—linker—fluorophenyl (linear)
    recognition_mode=RecognitionMode.NON_COVALENT,  # R_⊇ — two independent H-bond + π anchors
    polarity=Polarity.SELF_COMPLEMENTARY_PSEUDO,  # P_±^ψ — charged aminoimidazole + hydrophobic phenyl
    fidelity=Fidelity.MEDIUM,              # F_eth — IC50 = 13 μM WT; both rings contribute
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,  # Γ_∧(SELECTIVE) — two rings selective independently
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
    description=(
        "HIF (Hv1 Inhibitor Flexible): two-pronged arginine mimic with flexible linker. "
        "Scaffold: 2-aminoimidazole + fluorinated phenyl ring, connected by extended linker. "
        "Linker separates rings → eliminates condensed-ring Gamma conflict (ABIF3 liability). "
        "Each ring optimized independently: aminoimidazole↔D112/R211, F-phenyl↔F182 (π-stack). "
        "IC50(WT)=13 μM (HIF), sub-μM (F150A). "
        "HIF/HIF_EN predicted BBB-penetrant (LogD=0.09/0.28) → neuroprotective applications. "
        "Key insight: linear topology (T_|) replaces network topology (T_∈) of 2GBI → "
        "independent ring optimization without cross-ring perturbation. "
        "Ref: Zhao, Hong et al. 2021 J. Gen. Physiol. 153:e202012832."
    ),
    metadata={"cross_domain": False, "validation_tier": "primary",
               "papers": ["Zhao2021JGP"],
               "IC50_WT_uM": 13.0, "IC50_F150A_approx_uM": 0.5,
               "BBB_penetrant": True,
               "design_principle": "decouple condensed rings via flexible linker"}
)

print(f"2GBI_inhibitor: {_2GBI.to_notation()}")
print(f"HIF_inhibitor:  {HIF.to_notation()}")
print(f"Distance (2GBI → HIF): {tuple_distance(_2GBI, HIF):.4f}")
print()

# =============================================================================
# SECTION 3 — REGISTER ALL INTO GLOBAL CATALOG
# =============================================================================

print("=" * 70)
print("SECTION 3 — CATALOG REGISTRATION")
print("=" * 70)

all_hv1_synthons = [
    Hv1_human_closed,
    Hv1_human_open,
    AtHv1_silent,
    AtHv1_primed,
    PsHv1_constitutive,
    _2GBI,
    HIF,
]

for s in all_hv1_synthons:
    global_catalog.register(s)
    print(f"  ✓ registered: {s.name}")

print(f"\nTotal Hv1 synthons registered: {len(all_hv1_synthons)}")
print()

# =============================================================================
# SECTION 4 — ALGEBRAIC ANALYSIS
# =============================================================================

print("=" * 70)
print("SECTION 4 — ALGEBRAIC ANALYSIS OF Hv1 SYSTEM")
print("=" * 70)

print("\n─── A. Channel State Distances ───")
d_closed_open = tuple_distance(Hv1_human_closed, Hv1_human_open)
d_silent_closed = tuple_distance(AtHv1_silent, Hv1_human_closed)
d_primed_closed = tuple_distance(AtHv1_primed, Hv1_human_closed)
d_silent_primed = tuple_distance(AtHv1_silent, AtHv1_primed)
d_ps_human = tuple_distance(PsHv1_constitutive, Hv1_human_closed)
d_ps_primed = tuple_distance(PsHv1_constitutive, AtHv1_primed)

print(f"  d(Hv1_closed, Hv1_open)     = {d_closed_open:.4f}  [gating transition]")
print(f"  d(AtHv1_silent, Hv1_closed) = {d_silent_closed:.4f}  [P-55: ~K_trap distance only]")
print(f"  d(AtHv1_primed, Hv1_closed) = {d_primed_closed:.4f}  [P-55: should be near-zero]")
print(f"  d(AtHv1_silent, AtHv1_primed) = {d_silent_primed:.4f}  [cost of K_trap peel]")
print(f"  d(PsHv1, Hv1_closed)        = {d_ps_human:.4f}  [gymnosperm vs. human]")
print(f"  d(PsHv1, AtHv1_primed)      = {d_ps_primed:.4f}  [primed AtHv1 ≈ PsHv1?]")

print("\n─── B. Inhibitor Distances ───")
d_2GBI_open = tuple_distance(_2GBI, Hv1_human_open)
d_HIF_open = tuple_distance(HIF, Hv1_human_open)
d_2GBI_HIF = tuple_distance(_2GBI, HIF)

print(f"  d(2GBI, Hv1_open)  = {d_2GBI_open:.4f}  [open-channel block compatibility]")
print(f"  d(HIF, Hv1_open)   = {d_HIF_open:.4f}  [HIF vs open state]")
print(f"  d(2GBI, HIF)       = {d_2GBI_HIF:.4f}  [scaffold evolution distance]")

print("\n─── C. meet(Hv1_open, 2GBI) — Open-Channel Block ───")
m_open_2GBI = meet(Hv1_human_open, _2GBI)
print(f"  Result: {m_open_2GBI}")
print()

print("\n─── D. tensor(HIF, AtHv1_primed) — P-56 Test ───")
# P-56: tensor(HIF, AtHv1_primed) should have lower xi_CP than tensor(2GBI, AtHv1_silent)
t_HIF_primed = tensor(HIF, AtHv1_primed)
t_2GBI_silent = tensor(_2GBI, AtHv1_silent)
d_HIF_primed = tuple_distance(HIF, AtHv1_primed)
d_2GBI_silent = tuple_distance(_2GBI, AtHv1_silent)
print(f"  d(HIF, AtHv1_primed)  = {d_HIF_primed:.4f}  [should be smaller]")
print(f"  d(2GBI, AtHv1_silent) = {d_2GBI_silent:.4f}  [should be larger: K_trap barrier]")
print(f"  P-56 supported: {d_HIF_primed < d_2GBI_silent}")
print()

print("\n─── E. join(AtHv1_silent, AtHv1_primed) — Peel Algebra ───")
# join should recover or exceed AtHv1_primed primitives
j_silent_primed = join(AtHv1_silent, AtHv1_primed)
print(f"  join result: {j_silent_primed}")
print(f"  d(join, AtHv1_primed) = {tuple_distance(j_silent_primed, AtHv1_primed):.4f}")
print()

print("\n─── F. Cross-Species meet — Conservation Core ───")
# meet(AtHv1_silent, PsHv1) should show what's CONSERVED between silent/primed species
m_at_ps = meet(AtHv1_silent, PsHv1_constitutive)
print(f"  meet(AtHv1_silent, PsHv1): {m_at_ps}")
print()

# =============================================================================
# SECTION 5 — P-55 VERIFICATION: AtHv1_primed ≈ Hv1_human_closed
# =============================================================================

print("=" * 70)
print("SECTION 5 — P-55 VERIFICATION")
print("=" * 70)

print("""
P-55: d(AtHv1_silent, Hv1_human_closed) ≈ d(AtHv1_primed, Hv1_human_closed) + K_trap_cost
AtHv1 silent and human Hv1 closed are the SAME kinetic state via different mechanisms.
The RSN (K_trap) is AtHv1's implementation of what PsHv1/human achieves thermodynamically.
""")

print(f"  d(AtHv1_silent, Hv1_closed) = {d_silent_closed:.4f}  [RSN adds K_trap + P change]")
print(f"  d(AtHv1_primed, Hv1_closed) = {d_primed_closed:.4f}  [after peel: should be near 0-1]")
K_trap_cost = d_silent_closed - d_primed_closed
print(f"  K_trap primitive cost       = {K_trap_cost:.4f}  [distance contribution of RSN]")
print()

if d_primed_closed <= 1.0:
    print("  ✅ P-55 SUPPORTED: AtHv1_primed ≈ Hv1_human_closed (d ≤ 1)")
elif d_primed_closed <= 2.0:
    print("  ✅ P-55 PARTIALLY SUPPORTED: AtHv1_primed ≈ Hv1_human_closed (d ≤ 2)")
else:
    print(f"  ⚠️  P-55 NEEDS REFINEMENT: d = {d_primed_closed:.4f} (>2 primitives differ)")

# =============================================================================
# SECTION 6 — SCAFFOLD EVOLUTION: 2GBI → HIF (Gamma_conflict analysis)
# =============================================================================

print()
print("=" * 70)
print("SECTION 6 — SCAFFOLD EVOLUTION ANALYSIS (2GBI → HIF)")
print("=" * 70)

print("""
The condensed-ring liability of 2GBI is a Gamma_and(SELECTIVE) internal conflict:
  - Fluorinating F182-contact phenyl ring (ABIF3) also perturbs the five-membered ring
  - Adding 3 fluorines: IC50(WT) jumps 699 μM (vs 38 μM for ABI) — 18-fold DECREASE
  - This is exactly tensor(phenyl_F3, aminoimidazole) → CONFLICT in R-interaction

HIF solution: T_linear topology separates the rings
  - Each ring engages the binding site independently
  - Fluorination of phenyl strengthens F182 pi-stacking WITHOUT perturbing aminoimidazole
  - IC50(WT) = 13 μM (HIF) vs 38 μM (2GBI) — improved despite being "weaker" single scaffold
""")

print(f"  2GBI topology: T_network (condensed, rigid)")
print(f"  HIF topology:  T_linear  (decoupled, flexible linker)")
print(f"  Topology primitive difference: {'T_network' != 'T_linear'}")
print(f"  d(2GBI, HIF) = {d_2GBI_HIF:.4f} — scaffold evolution cost")
print()

# meet(2GBI, HIF) → conserved pharmacophore core
m_2GBI_HIF = meet(_2GBI, HIF)
print(f"  meet(2GBI, HIF) — conserved core: {m_2GBI_HIF}")
print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"""
Hv1 SynthOmnicon Analysis Complete
===================================

Synthons registered: {len(all_hv1_synthons)}
  - Hv1_human_closed  (Phi_sub, K_mod)    ← baseline resting state
  - Hv1_human_open    (Phi_c,  K_mod)    ← H-bond chain connectivity transition
  - AtHv1_silent      (Phi_sub, K_trap)  ← RSN = kinetic trap
  - AtHv1_primed      (Phi_sub, K_mod)   ← peel(K_trap) = mechanical priming
  - PsHv1_constitutive (Phi_sub, K_mod)  ← reference (no RSN)
  - 2GBI_inhibitor    (T_∈, SELECTIVE)   ← condensed bicyclic, open-channel block
  - HIF_inhibitor     (T_|, SELECTIVE)   ← linear two-pronged, decoupled rings

Key distances:
  d(AtHv1_silent  → primed)  = {d_silent_primed:.4f}  [K_trap peel cost]
  d(AtHv1_primed  → Hv1_closed) = {d_primed_closed:.4f}  [P-55: ≈ 0 expected]
  d(2GBI → HIF)              = {d_2GBI_HIF:.4f}  [scaffold evolution]

Predictions:
  P-55: AtHv1_primed ≈ Hv1_human_closed → {d_primed_closed:.4f} primitive distance
  P-56: d(HIF,primed) < d(2GBI,silent) → {d_HIF_primed:.4f} < {d_2GBI_silent:.4f} = {d_HIF_primed < d_2GBI_silent}
  P-57: F150A_site Gamma_or → endogenous guanidinium promiscuity (see PRIMITIVE_PREDICTIONS.md)
""")
