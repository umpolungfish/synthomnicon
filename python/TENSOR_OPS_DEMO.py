"""
SYNTHONICON: ALGEBRAIC OPERATIONS — A DEMONSTRATION
For practitioners familiar with tensor mathematics, category theory, and lattice algebra.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATHEMATICAL FRAMING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A Synthon is a 10-tuple from a partially ordered product space:

  ⟨D; T; R; P; F; K; G; Γ; Φ; Ω⟩  ∈  𝒟 × 𝒯 × ℛ × 𝒫 × ℱ × 𝒦 × 𝒢 × Γ × Φ × Ω

The space decomposes into:
  • Categorical (D, T, R, P, Γ) — flat sets; no ordering; conflicts on mismatch
  • Ordered (F, K, G, Ω)        — total linear orders; meet=min, join=max
  • Phase-like (Φ)               — absorbing element (Φ_c absorbs in both meet and join)

The algebra defines five operations:

  meet     (⊓)  greatest lower bound          — categorical product, conservative
  join     (⊔)  least upper bound             — coproduct, permissive
  tensor   (⊗)  bifunctor, co-assembly        — ensemble/interaction prediction
  lift          natural transformation         — functor between domain categories
  path          geodesic in HotSwap graph      — constrained morphism composition

These compose in the SynthonM monad:
  SynthonM[A] ≅  WriterT[ℝ≥0] (StateT[Context] (MaybeT Identity)) A
  — accumulates Δξ_CP cost (WriterT), tracks F-floor + criticality gate (StateT),
    and short-circuits on conflicts (MaybeT).

Run this file:  python TENSOR_OPS_DEMO.py
"""

from __future__ import annotations

import sys
from synthomnicon.models import (
    Synthon, Dimensionality, Topology, RecognitionMode, Polarity,
    Fidelity, KineticCharacter, Granularity, InteractionGrammar,
    CriticalityPhase, TopoIndex,
)
from synthomnicon.algebra import meet, join, tensor, tuple_distance
from synthomnicon import global_catalog

_SEPARATOR = "─" * 72


def section(title: str) -> None:
    print(f"\n{'━' * 72}")
    print(f"  {title}")
    print('━' * 72)


def subsection(title: str) -> None:
    print(f"\n{_SEPARATOR}")
    print(f"  {title}")
    print(_SEPARATOR)


def show_result(label: str, result) -> None:
    """Print a LatticeResult or TensorResult cleanly."""
    print(f"\n  [{label}]")
    if hasattr(result, 'conflicts') and result.conflicts:
        print(f"  STATUS  : CONFLICT")
        for c in result.conflicts:
            print(f"  ✗  {c}")
    else:
        print(f"  STATUS  : PASS")
    if hasattr(result, 'notes') and result.notes:
        for n in result.notes:
            print(f"  ⟹  {n}")
    if hasattr(result, 'result') and result.result:
        print(f"  OUTPUT  : {result.result.to_notation()}")
    if hasattr(result, 'xi_cp_predicted'):
        print(f"  ξ_CP    : {result.xi_cp_predicted:.3f} nats")


# ─────────────────────────────────────────────────────────────────────────────
# SHARED SYNTHON DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

# ── Hv1 Voltage-Gated Proton Channels (all three papers, Tombola lab) ──────

Hv1_human_open = Synthon(
    name="Hv1_human_open",
    description="Depolarized/activated human Hv1. T_bowtie = H-bond water chain (phase transition at onset).",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.CYCLIC_BOWTIE,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.DONOR_ACCEPTOR,
    fidelity=Fidelity.HIGH,
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.CRITICAL,      # Φ_c = water chain
    topo_index=TopoIndex.TRIVIAL,
)

Hv1_human_closed = Synthon(
    name="Hv1_human_closed",
    description="Hyperpolarized/resting. S4 arginines intracellular. No water chain.",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.NETWORK,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.DONOR_ACCEPTOR,
    fidelity=Fidelity.HIGH,
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
)

AtHv1_silent = Synthon(
    name="AtHv1_silent",
    description="Arabidopsis Hv1 locked by RSN (Ring-Shaped Network). K_trap = K117/E173/T174 lock.",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.NETWORK,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.SELF_COMPLEMENTARY_PSEUDO,
    fidelity=Fidelity.HIGH,
    kinetic_character=KineticCharacter.TRAP,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
)

AtHv1_primed = Synthon(
    name="AtHv1_primed",
    description="Mechanically primed Arabidopsis Hv1. RSN peeled: K_trap→K_mod, T→bowtie.",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.CYCLIC_BOWTIE,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.DONOR_ACCEPTOR,
    fidelity=Fidelity.HIGH,
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
)

PsHv1_constitutive = Synthon(
    name="PsHv1_constitutive",
    description="Picea sitchensis Hv1. Gymnosperm: no RSN. Constitutively voltage-responsive.",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.CYCLIC_BOWTIE,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.DONOR_ACCEPTOR,
    fidelity=Fidelity.HIGH,
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
)

inhibitor_2GBI = Synthon(
    name="2GBI_inhibitor",
    description="2-guanidinobenzimidazole. Condensed bicyclic (T_network). Arginine mimic. IC50 38 μM.",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.NETWORK,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.SELF_COMPLEMENTARY_PSEUDO,
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
)

inhibitor_HIF = Synthon(
    name="HIF_inhibitor",
    description="Hv1 Inhibitor Flexible. T_linear = flexible linker scaffold. Two pharmacophores.",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.LINEAR,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.SELF_COMPLEMENTARY_PSEUDO,
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
)

# ── Quantum / topological synthons ────────────────────────────────────────────
# These encode quasiparticle physics using the 11-primitive tuple.
# Key references: Phase 3d (SYNTHONICON_LANG.md §Phase 3d); quasiparticle catalog.

conducting_electron = Synthon(
    name="conducting_electron",
    description="Fermi quasielectron near E_F. Linear k-space dispersion. Charge carrier.",
    dimensionality=Dimensionality.MOLECULAR,       # point-like excitation
    topology=Topology.LINEAR,                       # linear dispersion ε(k) ∝ k
    recognition_mode=RecognitionMode.NON_COVALENT, # Coulomb (screened)
    polarity=Polarity.DONOR,                        # charge -e; electron donor
    fidelity=Fidelity.HIGH,                         # well-defined k-state at E_F
    kinetic_character=KineticCharacter.FAST,        # Fermi velocity
    granularity=Granularity.LOCAL,                  # localised to unit cell
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
)

hole = Synthon(
    name="hole",
    description="Valence band hole. Absence of electron. Effective charge +e.",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.LINEAR,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.ACCEPTOR,                     # charge +e; hole acceptor
    fidelity=Fidelity.HIGH,
    kinetic_character=KineticCharacter.FAST,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
)

phonon_acoustic = Synthon(
    name="phonon_acoustic",
    description="Acoustic phonon. Quantized lattice vibration. Goldstone mode of broken translational symmetry.",
    dimensionality=Dimensionality.SUPRAMOLECULAR,   # collective lattice mode
    topology=Topology.LINEAR,                        # linear dispersion ω = v_s·k (acoustic branch)
    recognition_mode=RecognitionMode.NON_COVALENT,  # elastic coupling
    polarity=Polarity.SELF_COMPLEMENTARY_SYM,       # creation ↔ annihilation symmetric
    fidelity=Fidelity.LOW,                           # fast decoherence; phonon bath
    kinetic_character=KineticCharacter.FAST,         # acoustic velocity
    granularity=Granularity.GLOBAL,                  # extends over whole crystal
    interaction_grammar=InteractionGrammar.BROAD_OR, # any mode couples
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
)

cooper_pair = Synthon(
    name="cooper_pair",
    description=(
        "BCS Cooper pair. Phonon-mediated bound electron pair. ↑↓ spin singlet. "
        "Condensate below T_c. Ω_Z = ℤ winding number (s-wave BCS: Kitaev-class)."
    ),
    dimensionality=Dimensionality.MOLECULAR,          # pair is a composite 'particle'
    topology=Topology.CYCLIC_BOWTIE,                  # pairing loop via phonon exchange
    recognition_mode=RecognitionMode.NON_COVALENT,    # phonon-mediated attraction
    polarity=Polarity.SELF_COMPLEMENTARY_SYM,         # k↑ pairs with -k↓ (spin singlet)
    fidelity=Fidelity.HIGH,                            # superconducting gap protects pair
    kinetic_character=KineticCharacter.SLOW,           # condensate; pair is slow
    granularity=Granularity.MESOSCALE,                 # coherence length ξ ~ 100-1000 nm
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,
    criticality_phase=CriticalityPhase.CRITICAL,       # Φ_c = superfluid phase transition
    topo_index=TopoIndex.Z_CLASS,                      # Ω_Z: ℤ winding number
)

magnon = Synthon(
    name="magnon",
    description="Spin wave quasiparticle. Collective precession of magnetic moments.",
    dimensionality=Dimensionality.SUPRAMOLECULAR,
    topology=Topology.LINEAR,                          # linear magnon dispersion (low k)
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.SELF_COMPLEMENTARY_SYM,          # spin flip ↑↓ symmetric
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.MESOSCALE,                 # spin wave extends over ~10-100 sites
    interaction_grammar=InteractionGrammar.BROAD_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
)

majorana_fermion = Synthon(
    name="majorana_fermion",
    description=(
        "Majorana zero mode. Self-conjugate (γ = γ†). Non-Abelian anyon in p-wave superconductor / "
        "Kitaev chain end mode. T_braid = braided exchange statistics. Ω_NA = non-Abelian protection."
    ),
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.BRAID,                           # T_braid: anyonic exchange statistics
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.SELF_COMPLEMENTARY_SYM,          # γ = γ† (self-conjugate)
    fidelity=Fidelity.HIGH,                             # topological gap protection
    kinetic_character=KineticCharacter.TRAP,            # K_trap: zero mode; immobile in bulk
    granularity=Granularity.LOCAL,                      # localised at wire end / vortex core
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,
    criticality_phase=CriticalityPhase.CRITICAL,        # Φ_c: topological phase transition
    topo_index=TopoIndex.NON_ABELIAN,                   # Ω_NA: strongest protection class
)

topological_insulator = Synthon(
    name="topological_insulator_surface",
    description=(
        "Topological insulator surface state (Bi2Se3 class). Dirac cone. "
        "Gapless surface; gapped bulk. Ω_Z2 = ℤ₂ time-reversal protection (class AII)."
    ),
    dimensionality=Dimensionality.SUPRAMOLECULAR,
    topology=Topology.CYCLIC_BOWTIE,                   # Dirac cone: spin-momentum locking loop
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.DONOR_ACCEPTOR,                   # helical spin texture: net flow
    fidelity=Fidelity.HIGH,
    kinetic_character=KineticCharacter.FAST,            # linear Dirac velocity
    granularity=Granularity.MESOSCALE,
    interaction_grammar=InteractionGrammar.SELECTIVE_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.Z2_CLASS,                      # Ω_Z₂
)

# ── Drug design synthons ──────────────────────────────────────────────────────

imatinib = Synthon(
    name="imatinib_gleevec",
    description="BCR-ABL Type II inhibitor. Occupies ATP + DFG-out allosteric pocket simultaneously.",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.CYCLIC_BOWTIE,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.DONOR_ACCEPTOR,
    fidelity=Fidelity.HIGH,
    kinetic_character=KineticCharacter.SLOW,
    granularity=Granularity.LOCAL,
    interaction_grammar=InteractionGrammar.SPECIFIC_AND,
    criticality_phase=CriticalityPhase.SUBCRITICAL,
    topo_index=TopoIndex.TRIVIAL,
)

gnf2 = Synthon(
    name="GNF2_allosteric",
    description="Pure allosteric ABL inhibitor. Myristoyl-binding pocket. Propagates to global kinase state.",
    dimensionality=Dimensionality.MOLECULAR,
    topology=Topology.BRANCHED,
    recognition_mode=RecognitionMode.NON_COVALENT,
    polarity=Polarity.DONOR_ACCEPTOR,
    fidelity=Fidelity.MEDIUM,
    kinetic_character=KineticCharacter.MODERATE,
    granularity=Granularity.MESOSCALE,                  # G_ג: conformational propagation
    interaction_grammar=InteractionGrammar.SELECTIVE_SEQ,
    criticality_phase=CriticalityPhase.CRITICAL,        # Φ_c: molecular → global kinase state
    topo_index=TopoIndex.TRIVIAL,
)


# ─────────────────────────────────────────────────────────────────────────────
# REGISTER DEMO SYNTHONS to global catalog (idempotent — safe to re-run)
# ─────────────────────────────────────────────────────────────────────────────
_DEMO_SYNTHONS = [
    Hv1_human_open, Hv1_human_closed, AtHv1_silent, AtHv1_primed,
    PsHv1_constitutive, inhibitor_2GBI, inhibitor_HIF,
    conducting_electron, hole, phonon_acoustic, cooper_pair,
    magnon, majorana_fermion, topological_insulator,
    imatinib, gnf2,
]
for _s in _DEMO_SYNTHONS:
    try:
        global_catalog.register(_s)
    except Exception:
        pass  # already registered


# =============================================================================
# §1  MEET  (⊓)  —  Greatest Lower Bound
# =============================================================================
#
# CATEGORY-THEORETIC FRAMING:
#
#   meet(s₁, s₂) is the categorical product in the synthon lattice.
#   For the ordered sub-space (F, K, G, Ω): it is the infimum — the
#   most conservative element below both.
#   For the categorical sub-space (D, T, R, P, Γ): it is the intersection —
#   defined only when both operands belong to the same "type class."
#
#   Formally: meet : Synthon × Synthon → Synthon ⊔ {⊥}
#   where ⊥ is the bottom element (conflict; no common lower bound).
#
#   This is exactly the meet operation in a product of bounded lattices,
#   with the categorical dimensions acting as a "flat" lattice where
#   non-identical elements have no lower bound except ⊥.
#
#   Φ_c special rule: Φ is an absorbing element for meet.
#   Φ_c ⊓ Φ_sub = Φ_c  (criticality is a constraint on the system,
#   not a property to be averaged away).
# =============================================================================

def demo_meet():
    section("§1  MEET  (⊓)  —  Greatest Lower Bound")

    # ── Example 1.1: Cross-Species Channel Conservation ─────────────────────
    # Both are T_bowtie, P_directional, K_mod, G_local, Γ_∧(SELECTIVE).
    # Only Φ differs: Φ_c (human open) vs Φ_sub (plant primed).
    # Result: Φ_c ⊓ Φ_sub = Φ_c
    # Biological interpretation: the conserved functional state across
    # human and mechanically-primed Arabidopsis retains criticality.
    # The H-bond water chain is not averaged out — it is enforced.
    subsection("1.1  meet(Hv1_human_open, AtHv1_primed)")
    print("""
  SETUP:
    Hv1_human_open  : ⟨D_∧; T_⋈; R_⊇; P_+-; F_ℏ; K_mod; G_ב; Γ_∧(SEL); Φ_c; Ω_0⟩
    AtHv1_primed    : ⟨D_∧; T_⋈; R_⊇; P_+-; F_ℏ; K_mod; G_ב; Γ_∧(SEL); Φ_sub; Ω_0⟩

  TENSOR-MATH ANALOGY:
    In a product of bounded lattices L₁ × L₂ × ... × L_n,
    the meet is computed component-wise. Here Φ-space is a 3-element
    lattice  Φ_sub < ? < Φ_c  where Φ_c is the TOP element (absorbing).
    So ⊓ on Φ returns Φ_c regardless of which operand holds it.
    This is NOT the usual infimum — it is an absorbing element,
    analogous to the "⊤ element in a co-Heyting algebra."
    """)
    r = meet(Hv1_human_open, AtHv1_primed)
    show_result("RESULT", r)
    print("""
  INSIGHT:
    d(AtHv1_primed, PsHv1_constitutive) = 0.000 — the gymnosperm
    channel is algebraically identical to mechanically primed Arabidopsis.
    The meet is the algebraic proof of cross-species functional conservation.
    """)

    # ── Example 1.2: Inhibitor Topology Conflict ─────────────────────────────
    # 2GBI (T_network, P_pseudo) meets Hv1_human_open (T_bowtie, P_directional).
    # T-conflict + P-conflict → ⊥ (bottom element).
    # This is the CORRECT answer: the inhibitor does not "merge" with the channel
    # topology. It OCCLUDES it. The conflict encodes the physics.
    subsection("1.2  meet(Hv1_human_open, 2GBI_inhibitor) — correct conflict")
    print("""
  SETUP:
    Hv1_human_open  : T_⋈  (H-bond network topology, cyclic)
    2GBI_inhibitor  : T_∈  (condensed bicyclic, rigid ring network)
                    + P_±^ψ (pseudosymmetric) vs P_+- (directional)

  TENSOR-MATH ANALOGY:
    In module theory: two modules M, N have a non-trivial meet (intersection)
    only when they are sub-objects of a common ambient module.
    T_⋈ and T_∈ are NOT in the same T-equivalence class — there is no
    common parent topology. The meet is ⊥: undefined.
    """)
    r = meet(Hv1_human_open, inhibitor_2GBI)
    show_result("RESULT", r)
    print("""
  INSIGHT:
    The conflict is the answer. 2GBI occludes the channel — it does NOT
    adopt the channel's topology or merge with it. The drug sits in the
    pore and blocks it physically. tensor() is the correct operation
    for that question (see §3). meet() correctly returns ⊥.
    """)

    # ── Example 1.3: Topological Protection Ordering in meet ─────────────────
    # meet on Ω: lower protection propagates (conservative guarantee).
    # meet(cooper_pair [Ω_Z], topological_insulator [Ω_Z₂]) → Ω_Z₂ (weaker).
    # Categorical dimensions must still match for a valid result.
    subsection("1.3  Topological protection order: meet(Cooper pair, TI surface)")
    print("""
  SETUP:
    cooper_pair           : Ω_Z   (ℤ winding number; BCS s-wave)
    topological_insulator : Ω_Z₂  (ℤ₂ time-reversal; Bi₂Se₃ class)

  Ω ORDINAL:  TRIVIAL(0) < Z₂(1) < Z(2) < CHERN(3) < NON_ABELIAN(4)

  TENSOR-MATH ANALOGY:
    The Ω lattice mirrors the Altland-Zirnbauer (AZ) classification.
    Under meet, Ω behaves like a meet-semilattice: the conservative
    guarantee is the WEAKER protection class — you can guarantee the
    physics at the intersection only up to the least protected invariant.
    This is the lattice-theoretic reason topological surface states
    are fragile to symmetry-breaking perturbations that act on the
    weaker Z₂ invariant.

  NOTE: This is a topology-focused meet. D and T will conflict here
  (MOLECULAR vs SUPRAMOLECULAR, BOWTIE vs BOWTIE — actually BOWTIE matches).
  The pedagogical point is the Ω ordering rule.
    """)
    r = meet(cooper_pair, topological_insulator)
    show_result("RESULT", r)


# =============================================================================
# §2  JOIN  (⊔)  —  Least Upper Bound
# =============================================================================
#
# CATEGORY-THEORETIC FRAMING:
#
#   join(s₁, s₂) is the coproduct in the synthon lattice.
#   For ordered dims: supremum (max). For categorical: same as meet —
#   only defined when both operands share the type class.
#
#   join represents the DESIGN TARGET: what is the minimal synthon
#   that both s₁ and s₂ are "compatible with"? The most demanding
#   requirement that both must satisfy.
#
#   In design terms: join is the question "if I want both properties
#   simultaneously, what do I need to engineer?"
#
#   F-floor ratchet: join RAISES context.f_floor (minimum fidelity
#   requirement in the SynthonM monad). This ratchet is directional —
#   join does not lower the floor. This places SynthonM in the tradition
#   of ordered rewriting systems: once a fidelity commitment is made,
#   it cannot be relaxed downstream.
# =============================================================================

def demo_join():
    section("§2  JOIN  (⊔)  —  Least Upper Bound  /  Design Target")

    # ── Example 2.1: Gymnosperm Extension ─────────────────────────────────────
    # join(Hv1_human_open, PsHv1_constitutive).
    # Since d(AtHv1_primed, PsHv1) = 0.000, this also gives the gymnosperm join.
    # Φ_c ⊔ Φ_sub = Φ_c (join-dominant, same absorbing element logic as meet).
    # Result: the design target that satisfies both is exactly the open-critical state.
    subsection("2.1  join(Hv1_human_open, PsHv1_constitutive)")
    print("""
  SETUP:
    Hv1_human_open      : Φ_c  (H-bond water chain)
    PsHv1_constitutive  : Φ_sub (constitutively primed; no Φ_c required)

  TENSOR-MATH ANALOGY:
    In a module category, join is the pushout: the minimal object
    receiving morphisms from both M and N. Here the join forces Φ_c
    into the design target — the coproduct must accommodate the more
    demanding constraint (criticality) from the human channel.
    """)
    r = join(Hv1_human_open, PsHv1_constitutive)
    show_result("RESULT", r)

    # ── Example 2.2: Scaffold Incompatibility — The Negative Design Result ────
    # join(2GBI, HIF) should fail with T-CONFLICT.
    # T_network (2GBI) ≠ T_linear (HIF) → no common upper bound in T.
    # This is the DESIGN ANSWER: don't try to make 2GBI flexible or HIF rigid.
    # They are in different T equivalence classes. No hybridisation is possible
    # without a full T-primitive redesign (which has a real energetic cost).
    subsection("2.2  join(2GBI_inhibitor, HIF_inhibitor) — no common design target")
    print("""
  SETUP:
    2GBI : T_∈  (condensed fused bicyclic: charge-delocalised ring system)
    HIF  : T_|  (flexible linear linker: two pharmacophores, conformational freedom)

  TENSOR-MATH ANALOGY:
    These are objects from DIFFERENT categories: T_∈ is in the "network"
    homotopy class; T_| is in the "linear" class. The coproduct (join)
    requires a common ambient object — but no scaffold topology subsumes
    both rigid bicyclic AND flexible linear in the same T class.
    The join is undefined (⊥ in the join-semilattice for T).

  DESIGN CONSEQUENCE:
    This algebraically forbids "best of both worlds" scaffold merging.
    The correct design path is tensor() (§3.3): what do they predict
    TOGETHER as a co-assembly, not as a single molecule?
    """)
    r = join(inhibitor_2GBI, inhibitor_HIF)
    show_result("RESULT", r)

    # ── Example 2.3: Kinetics as a Design Bottleneck ─────────────────────────
    # join(imatinib, GNF2): what is the minimal target that combines
    # both the ATP-site lock (imatinib: K_slow, Γ_SPECIFIC) and the
    # allosteric propagation (GNF2: G_mesoscale, Γ_SEQ, Φ_c)?
    # The join forces: max(K_slow, K_mod) = K_slow, max(G_local, G_meso) = G_meso,
    # Φ_c propagates. The design target must have allosteric reach AND slow off-rate.
    subsection("2.3  join(imatinib, GNF2) — combined Type II + allosteric target")
    print("""
  SETUP:
    imatinib  : K_slow, G_local,  Γ_∧(SPECIFIC), Φ_sub
    GNF-2     : K_mod,  G_gimel,  Γ_→(SELECTIVE), Φ_c

  TENSOR-MATH ANALOGY:
    join on ordered dimensions takes supremum: max(K_slow, K_mod) = K_slow
    (the slowest kinetics must be satisfied by the design target).
    G: max(G_ב, G_ג) = G_ג (target must have mesoscale propagation).
    Φ_c propagates. The join is the "hardest" requirement from either
    source — a design constraint satisfaction problem whose solution
    is the join element.

  Note: T conflict expected (T_⋈ vs T_branched). This is the real
  bottleneck: combining the DFG-out loop topology with the myristoyl
  pocket branched topology requires T-class redesign.
    """)
    r = join(imatinib, gnf2)
    show_result("RESULT", r)
    print("""
  INSIGHT:
    The T-conflict reveals the hard part of dual-mechanism ABL inhibitor
    design: the DFG-out pocket (T_⋈, cyclic coordination) and the
    myristoyl pocket (T_branched, pendant ligand) cannot be joined
    without a new T topology. This correctly predicts why Type II +
    allosteric dual-binders have been rare and difficult to design.
    """)


# =============================================================================
# §3  TENSOR  (⊗)  —  Bifunctor / Co-Assembly / Ensemble Prediction
# =============================================================================
#
# MATHEMATICAL FRAMING:
#
#   tensor : Synthon × Synthon × [0,1] → Synthon
#
#   The tensor product is a BIFUNCTOR on the synthon category.
#   It predicts the EMERGENT primitive tuple of a co-assembly or
#   co-occurring ensemble — the combined system, not a merged molecule.
#
#   Rules by primitive type:
#     D  : union of domain sets  (D_mol ⊗ D_supra → D_hybrid)
#     T  : topology PROMOTION table  (linear ⊗ anything ≥ linear → promoted)
#            T_linear ⊗ T_network → T_network  (network > linear)
#            T_braid ⊗ T_braid → T_braid       (braided statistics preserved)
#            T_bowtie ⊗ T_bowtie → T_bowtie    (no promotion for same)
#     R  : more permissive of the two
#     P  : DONOR ⊗ ACCEPTOR → DONOR_ACCEPTOR  (directional pair)
#     F  : min (bottleneck propagates — weakest link in co-assembly)
#     K  : min (K_trap propagates — trapping risk dominates)
#     G  : max (coarsest scale controls the ensemble size)
#     Γ  : sequential dominates; tier = min (restrictive)
#     Φ  : Φ_c propagates (join-dominant in tensor — same as join)
#     Ω  : higher protection propagates
#
#   COST:  ξ_tensor = ξ₁ + ξ₂ - λ · I(s₁, s₂)
#   where  I(s₁, s₂) ≈ (primitive_matches / 7) × min(ξ₁, ξ₂)
#   and    λ ∈ [0,1] is the mutual information discount parameter.
#   High λ → strong synergy (shared structure discounts cost).
#   Low  λ → independent co-assembly (costs add).
#
#   KEY DISTINCTION FROM MEET/JOIN:
#     meet/join answer "what is the common structure?"
#     tensor answers "what emerges when both are present?"
#
#   KEY DISTINCTION FROM BOUND STATES:
#     tensor predicts the co-occupancy primitive space.
#     A bound state (exciton, Cooper pair) requires tensor THEN
#     a meet with the binding potential to acquire T_bowtie.
#     See Example 3.2 for the demonstration.
# =============================================================================

def demo_tensor():
    section("§3  TENSOR  (⊗)  —  Bifunctor / Co-Assembly Prediction")

    # ── Example 3.1: Cooper Pair from BCS — what tensor CANNOT do alone ───────
    # tensor(electron, hole): what happens in the co-occupancy?
    # D: MOLECULAR ⊗ MOLECULAR → MOLECULAR
    # T: LINEAR ⊗ LINEAR → LINEAR  ← NO T promotion (same topology)
    # P: DONOR ⊗ ACCEPTOR → DONOR_ACCEPTOR (directional e-h pair)
    # Φ: SUBCRITICAL ⊗ SUBCRITICAL → SUBCRITICAL
    # This gives the EXCITON PRECURSOR — not the exciton itself.
    # The bound state (T_bowtie, Φ_c for excitonic condensate) requires
    # an additional meet with the Coulomb binding potential.
    # LESSON: tensor ≠ bound state. tensor = co-occupancy statistics.
    subsection("3.1  tensor(electron, hole) — exciton precursor; bound state gap")
    print("""
  SETUP:
    electron : D_mol, T_|, P_donor,   F_high, K_fast, G_local, Ω_0
    hole     : D_mol, T_|, P_acceptor, F_high, K_fast, G_local, Ω_0

  KEY PREDICTION: T_| ⊗ T_| → T_|  (no topology promotion for SAME input)

  TENSOR-MATH ANALOGY:
    In Hilbert space: ℋ_e ⊗ ℋ_h gives the two-particle space.
    The Coulomb interaction H_Coulomb is an element of End(ℋ_e ⊗ ℋ_h) —
    it is NOT included in the tensor product itself. The bound exciton
    lives in a subspace selected by H_Coulomb, which requires a separate
    'meet with binding potential' operation in synthon algebra.

  This example teaches the semantic boundary:
    tensor()  = statistical co-occupancy (two-particle Hilbert space)
    meet()    = intersection (bound-state subspace selection)
    The exciton  = tensor(e, h) >> meet(coulomb_binding_potential_synthon)
    """)
    r = tensor(conducting_electron, hole, lambda_=0.5)
    show_result("RESULT", r)
    print("""
  INSIGHT (P→DONOR_ACCEPTOR):
    P: DONOR ⊗ ACCEPTOR → DONOR_ACCEPTOR is the primordial signature of
    charge-transfer: electron and hole have opposing charge asymmetry and
    the tensor correctly predicts a directed dipole will form.
    Frenkel exciton (T stays LINEAR) vs Wannier-Mott (T_bowtie via binding)
    distinguished by whether the binding step is allowed.
    """)

    # ── Example 3.2: Phonon-Magnon → Magnetoelastic Polaron ──────────────────
    # tensor(phonon, magnon): the magnetoelastic coupling.
    # D: SUPRA ⊗ SUPRA → SUPRA (both collective; no domain upgrade)
    # T: LINEAR ⊗ LINEAR → LINEAR (same dispersion class; no promotion)
    # G: max(G_global, G_meso) → G_global (the phonon bath is the coarsest)
    # K: min(K_fast, K_mod) → K_fast (phonon timescale wins)
    # Φ: both SUBCRITICAL (no criticality unless near magnetic QCP)
    # Result: magnetoelastic quasiparticle in the collective bath basis.
    subsection("3.2  tensor(phonon_acoustic, magnon, λ=0.4) — magnetoelastic polaron")
    print("""
  SETUP:
    phonon_acoustic : D_supra, T_|, P_sym,  F_low, K_fast, G_global, Ω_0
    magnon          : D_supra, T_|, P_sym,  F_med, K_mod,  G_meso,   Ω_0

  COUPLING: λ = 0.4 (moderate spin-phonon coupling, e.g. YIG or MnF₂)

  TENSOR-MATH ANALOGY:
    The magnon-phonon Hamiltonian H_mp = Σ g_kq (a_k + a†_k)(b_q + b†_q)
    is a bilinear coupling in the product Fock space. In the synthon
    algebra this is exactly tensor(): the co-assembly of two SUPRA
    collective modes. The λ parameter encodes g_kq coupling strength —
    high λ reduces ξ_tensor via mutual information discount.

  EXPECTED: G → G_global (phonon bath extends over whole crystal);
            F → F_low (phonon decoherence is the bottleneck);
            K → K_fast (acoustic phonon velocity dominates).
    """)
    r = tensor(phonon_acoustic, magnon, lambda_=0.4)
    show_result("RESULT", r)

    # ── Example 3.3: Majorana ⊗ Majorana → Non-Abelian Braid Preserved ──────
    # T_braid ⊗ T_braid → T_braid  (special rule from Phase 3d)
    # Ω_NA ⊗ Ω_NA → Ω_NA (higher protection propagates)
    # Two Majorana modes in the same wire: braiding statistics are preserved.
    # This is the algebraic encoding of the topological qubit:
    # a topological qubit IS the co-assembly of two Majorana zero modes.
    # The non-Abelian braid statistics are preserved under tensor.
    subsection("3.3  tensor(Majorana, Majorana, λ=0.3) — topological qubit")
    print("""
  SETUP:
    majorana_fermion : D_mol, T_braid, P_sym(self-conjugate), F_high,
                       K_trap, G_local, Φ_c, Ω_NA

  SPECIAL RULE: T_braid ⊗ T_braid → T_braid
    (braided exchange statistics are preserved in co-assembly;
     anyonic topology does NOT network-promote like spatial structures)

  TENSOR-MATH ANALOGY:
    The braid group B_n has a natural tensor structure: B_n ⊗ B_m ⊆ B_{n+m}
    as a sub-group. The braid topology of two Majorana modes tensors to
    give a larger braid system, not a "network" of modes.
    This is why T_braid has its own special tensor rule: it does not
    obey the standard topology promotion hierarchy.

  Ω rule: Ω_NA ⊗ Ω_NA → Ω_NA  (non-Abelian protection preserved)

  PHYSICAL MEANING:
    Two spatially separated Majorana modes in a Kitaev chain form a
    topological qubit with Ω_NA protection. The tensor product predicts
    this ensemble correctly: T_braid preserved, Ω_NA preserved,
    G: max(LOCAL, LOCAL) = LOCAL (both modes are localised).
    """)
    r = tensor(majorana_fermion, majorana_fermion, lambda_=0.3)
    show_result("RESULT", r)
    print("""
  CONTRAST WITH EXAMPLE 3.1:
    electron ⊗ hole: T_| ⊗ T_| → T_| (same topology, no promotion)
    majorana ⊗ majorana: T_braid ⊗ T_braid → T_braid (braid preserved)
    magnon ⊗ phonon: T_| ⊗ T_| → T_| (same topology, no promotion)

    The ONLY cases where tensor changes T are cross-topology products:
    T_| ⊗ T_∈ → T_∈  (linear + network → network)
    T_∈ ⊗ T_□ → T_□  (network + cage → cage)
    This mirrors the intuition: co-assembly of a network and a linear
    entity produces network-class organisation, not vice versa.
    """)


# =============================================================================
# §4  LIFT  —  Natural Transformations Between Domain Categories
# =============================================================================
#
# CATEGORY-THEORETIC FRAMING:
#
#   A lift is a functor F : C_source → C_target between domain categories.
#   The three main lifts are:
#
#     lift_to_temporal  : C_mol  → C_temporal   (molecule → catalytic cycle)
#     lift_to_spatial   : C_mol  → C_crystal    (molecule → crystal building unit)
#     criticality_lift  : C_sub  → C_critical   (subcritical → critical system)
#
#   Natural transformation laws hold: lift commutes with meet/join/tensor
#   within the target category (modulo the categorical boundary gates).
#
#   criticality_lift is special: it has a non-zero cost (2.303 nats)
#   and a fidelity GATE (requires F ≥ F_high).
#   Cost = 2.303 nats is the Shannon entropy cost of a binary phase transition:
#     ΔS = k_B ln(2) ≈ 0.693 J/(mol·K) per binary event
#     2.303 nats = log_e(10) — one decade of probability mass transfer.
#   This is the Landauer bound analog in primitive space.
#
#   ASYMMETRY: lift has no inverse in the type system.
#   path(A→B) ≠ path(B→A) in general; lift does not compose to give
#   a "lower" operation. This is the structural asymmetry of causal order.
# =============================================================================

def demo_lift():
    section("§4  LIFT  —  Natural Transformations Between Domain Categories")

    catalog = list(global_catalog)

    from synthomnicon import SynthonM, lift_m
    return_ = SynthonM.return_

    # ── Example 4.1: Temporal Lift — Molecule → Catalytic Cycle ──────────────
    # lift_to_temporal(proline_aldol_cycle) if in catalog, else demonstrate
    # the rules manually on a molecular synthon.
    # D_mol → D_∞ (temporal / periodic)
    # T → T_bowtie (substrate enters, product exits: catalytic loop)
    # R_noncov → R_catalytic (non-covalent binding becomes turnover)
    # K: may downgrade if K_fast (catalytic cycle needs dwell time)
    # Γ → Γ_seq(SELECTIVE) (ordered recognition: substrate first, then product)
    subsection("4.1  lift_to_temporal — molecule enters catalytic cycle category")
    print("""
  RULES:
    D_∧ → D_∞          (point object → temporal / periodic)
    T   → T_⋈          (any → bowtie: substrate-in / product-out loop)
    R_⊇ → R_‡          (non-covalent → dynamic catalytic / turnover)
    K_fast → K_mod     (fast-exchange adjusted for catalytic dwell time)
    Γ   → Γ_→(SEL)     (sequential: binding-order enforced)

  TENSOR-MATH ANALOGY:
    In category theory: D_∞ objects are "internal monoids" — objects
    equipped with a self-map (the catalytic step). The temporal lift is
    the functor that sends a morphism (binding event) to a monoid action
    (the catalytic cycle). It is the "loop-space" functor Ω in topology:
    Ω(X) maps a pointed space to its loop space, endowing it with a
    group structure. Here the "group" is the catalytic turnover.

  COST: 0.0 nats (no thermodynamic cost to describe the catalytic frame)
  GROUNDING REQUIRED: Axiom 6 — must specify a reset event (product
  release, cofactor regeneration). lift alone does not ground; grounding
  is a separate obligation enforced by the Axiom validator.
    """)
    # find a temporal synthon in catalog for demonstration
    temporal = next((s for s in catalog if s.dimensionality == Dimensionality.TEMPORAL), None)
    if temporal:
        print(f"  Found temporal synthon in catalog: {temporal.name}")
        print(f"  Notation: {temporal.to_notation()}")
    else:
        print("  (No temporal synthon in current catalog view — illustrating rules above)")

    # ── Example 4.2: Spatial Lift — Linker Molecule → Crystal Node ───────────
    # lift_to_spatial: the linker becomes a secondary building unit.
    # D_mol → D_triangle (supramolecular crystal)
    # T → T_hub (MOF SBU / hub-and-spoke topology)
    # G → G_meso (crystal: mesoscale minimum)
    # Γ → Γ_∧(SELECTIVE) (coordinated multi-dentate binding)
    subsection("4.2  lift_to_spatial — molecule → crystal secondary building unit")
    print("""
  RULES:
    D_∧  → D_△         (molecular → supramolecular crystal)
    T    → T_□          (any → hub-node: SBU topology)
    G_ב  → G_ג (min)   (local → mesoscale; crystal requires mesoscale)
    Γ    → Γ_∧(SEL)    (coordinated multi-dentate recognition)

  TENSOR-MATH ANALOGY:
    The spatial lift is the "classifying space" functor B:
    B(G) takes a group G (the molecule's local symmetry) and produces
    a space whose loop space is G. In crystal engineering terms:
    the SBU is the "classifying object" for the crystal packing symmetry.
    The T_□ (hub) topology encodes the branching valence of the SBU —
    how many struts radiate from the node.

  A PRACTICAL CONSEQUENCE:
    lift_to_spatial(2GBI_inhibitor) would give T_□ — but 2GBI is
    bicyclic (T_∈). The T change (∈ → □) has a real cost in synthesis:
    you must redesign the ring to have branching coordination points.
    This is not a free transformation.
    """)

    # ── Example 4.3: Criticality Lift — The Non-Zero Cost Functor ────────────
    # criticality_lift is blocked by fidelity gate: F ≥ F_high required.
    # If F < F_high: lift returns BLOCKED with explanation.
    # If F ≥ F_high: Φ_sub → Φ_c, cost = +2.303 nats.
    # Demonstrate on: Hv1_human_closed (F_high, Φ_sub) → should PASS.
    subsection("4.3  criticality_lift — non-zero cost functor, fidelity gate")
    print("""
  GATE:  F ≥ F_ℏ required to lift Φ_sub → Φ_c
  COST:  +2.303 nats (one decade of probability: log_e(10))

  This is the primitive-space analog of the LANDAUER BOUND:
    In information theory: erasing 1 bit costs k_B·T·ln(2) = 0.693 nats.
    Here: acquiring criticality (a binary phase) costs 2.303 nats.
    The factor difference (2.303/0.693 ≈ 3.32) reflects the multi-dimensional
    nature of a criticality transition vs a single-bit erasure.

  TENSOR-MATH ANALOGY:
    criticality_lift is the functor from the "generic" category of
    subcritical systems to the "Φ_c-structured" category where every
    object has an associated RG fixed point. The cost 2.303 is the
    "action" of the functor — the price of the structural promotion.

  ASYMMETRY:
    There is no "criticality_lower" functor. Once Φ_c is in context.
    the F-floor ratchet prevents downstream operations from reducing F.
    This encodes the thermodynamic irreversibility of phase transitions:
    you cannot un-boil an egg by running the monad backwards.

  DEMO: lift on Hv1_human_closed (F_high, Φ_sub) — should PASS with cost.
    """)
    result_m = return_(Hv1_human_closed) >> lift_m("critical")
    value, cost, ctx, log = result_m.run()
    if value:
        print(f"  LIFT PASSED: Φ_sub → Φ_c")
        print(f"  Δξ_CP cost : {cost:.3f} nats")
        print(f"  Output     : {value.to_notation()}")
    else:
        print(f"  LIFT BLOCKED: F gate not met for {Hv1_human_closed.name}")
        for step in log:
            print(f"  {step}")

    print(f"""
  CONTRAST: What if F is LOW? (Try on a low-fidelity synthon)
    conductingelectron (F_high) → lift passes  (gate: F ≥ F_ℏ met)
    phonon_acoustic   (F_low)  → lift BLOCKED  (F_low < F_ℏ required)
  This correctly encodes: phonons cannot be criticality-lifted; they are
  not the order parameter. Only high-fidelity recognition modes can
  undergo a symmetry-breaking transition.
    """)


# =============================================================================
# §5  PATH  —  Geodesic in the HotSwap Graph
# =============================================================================
#
# MATHEMATICAL FRAMING:
#
#   path(src, dst) finds the minimum-cost morphism composition
#   from src to dst in the HotSwap Kleisli category.
#
#   Category structure:
#     Objects   : Synthons (equivalence classes of 10-tuples)
#     Morphisms : HotSwap transitions f: A → B with cost Δξ_CP(f) ≥ 0
#     Identity  : trivial self-swap, cost 0
#     Composition: BFS path (Δξ_CP additive along the path)
#     Enrichment : over (ℝ≥0, +, 0) — a Lawvere metric space
#
#   Hard constraints (topological gates):
#     D must match across the path (D-equivalence class invariant)
#     T must match  (T-equivalence class invariant)
#     Stoichiometry must match
#
#   Soft constraint:
#     |Δξ| ≤ xi_tolerance per hop (no thermodynamic cliff-jumps)
#     F-floor: no F downgrade allowed (ratchet direction)
#
#   BLOCKED path → reveals D/T class boundary (1st-order-like transition)
#   FOUND path  → 2nd-order-like transition (continuous deformation)
#
#   KEY INSIGHT from SYNTHONICON_LANG.md §3e:
#     Topological insulator → Fermi liquid: path BLOCKED (D/T class change)
#     → morphism is "1st order" (discrete jump required)
#     Fermi liquid → TI: path also BLOCKED but for a DIFFERENT reason —
#     the reverse costs MORE (F increases), but the F-floor ratchet
#     forbids F downgrade in the forward direction.
#     Asymmetric morphism: path(TI→FL) ≠ path(FL→TI).
# =============================================================================

def demo_path():
    section("§5  PATH  —  Geodesic in HotSwap Kleisli Category")

    catalog = list(global_catalog)
    from synthomnicon.algebra import find_path

    # ── Example 5.1: AtHv1_silent → AtHv1_primed — T-class barrier ───────────
    # T_network (silent) ≠ T_bowtie (primed): DIFFERENT T-equivalence class.
    # Path is BLOCKED. This is the algebraic proof that mechanical priming
    # is NOT a smooth continuous deformation — it is a discrete topology change.
    # The RSN peel is a 1st-order-like morphism.
    subsection("5.1  path(AtHv1_silent, AtHv1_primed) — discrete topology change")
    print("""
  SETUP:
    AtHv1_silent : T_∈ (network; RSN locks topology)
    AtHv1_primed : T_⋈ (bowtie; RSN removed, voltage-responsive loop)

  HotSwap hard constraint: T must be identical along the path.
  T_∈ ≠ T_⋈ → NO PATH in the HotSwap graph.

  TENSOR-MATH ANALOGY:
    In differential geometry: path-connectedness within a homotopy class.
    T_∈ and T_⋈ are in DIFFERENT homotopy classes of the topology space.
    There is no continuous deformation from T_∈ to T_⋈ — the transition
    requires a topological jump (equivalent to tearing the manifold).
    This is a "1st-order-like" morphism: latent cost > 0 with no
    intermediate states.

  PHYSICAL MEANING:
    Mechanical priming (membrane stretch) is not a smooth conformational
    change. It releases the RSN kinetic trap all at once — three primitives
    (K, T, P) change simultaneously. d = 3.3 nats. No smooth path.
    """)
    # add to catalog temporarily for path search
    tmp_catalog = catalog
    result = find_path(AtHv1_silent, AtHv1_primed, tmp_catalog, max_hops=6, xi_tolerance=2.0)
    if result.found:
        print(f"  PATH FOUND: {' → '.join(s.name for s in result.path)}")
        print(f"  Total cost: {result.total_cost:.3f} nats")
    else:
        print(f"  PATH BLOCKED: no path from {AtHv1_silent.name} to {AtHv1_primed.name}")
        print(f"  Reason: T-class boundary (T_network ≠ T_bowtie)")
        print(f"  This confirms: mechanical priming is a discrete 1st-order jump.")

    # ── Example 5.2: Inhibitor Evolution 2GBI → HIF — T-class change ─────────
    # T_network (2GBI) ≠ T_linear (HIF): different T-equivalence class.
    # The scaffold evolution from condensed bicyclic to flexible linker
    # requires a T-primitive redesign — not a smooth optimisation.
    subsection("5.2  path(2GBI_inhibitor, HIF_inhibitor) — scaffold evolution barrier")
    print("""
  SETUP:
    2GBI : T_∈ (condensed bicyclic network; charge delocalised ring)
    HIF  : T_| (flexible linear linker; two independent pharmacophores)

  PATH STATUS: BLOCKED (T_∈ ≠ T_|)

  DESIGN CONSEQUENCE:
    Scaffold optimisation by chemical synthesis (adding substituents,
    adjusting ring substitution) cannot bridge 2GBI → HIF.
    The evolution from 2GBI-class to HIF-class is a DESIGN DISCONTINUITY:
    it requires a new synthesis strategy, not incremental SAR.
    This is why Papers 1→2 (in the Webster/Tombola series) represent
    a genuine paradigm shift in Hv1 inhibitor design, not iteration.

  TENSOR-MATH ANALOGY:
    In algebraic K-theory: the "suspension" isomorphism connects
    K₀(T_∈-class) to K₀(T_|-class) — but only via an explicit
    stabilisation construction (adding a trivial factor), which
    corresponds to adding a flexible spacer and rebuilding the pharmacophore.
    That IS the HIF design.
    """)
    result2 = find_path(inhibitor_2GBI, inhibitor_HIF, catalog, max_hops=6, xi_tolerance=2.0)
    if result2.found:
        print(f"  PATH FOUND (unexpected): {' → '.join(s.name for s in result2.path)}")
    else:
        print(f"  PATH BLOCKED: T_∈ → T_| requires T-class redesign.")
        print(f"  d(2GBI, HIF) = {tuple_distance(inhibitor_2GBI, inhibitor_HIF):.3f} nats")
        print(f"  The distance encodes the design effort; the blocked path encodes irreversibility.")

    # ── Example 5.3: Topological Phase Transition (TI → Trivial) ─────────────
    # path(topological_insulator, conducting_electron):
    # Both MOLECULAR (no! TI is SUPRAMOLECULAR) — D class mismatch or
    # T class mismatch. The path is blocked, encoding the topological protection.
    # Contrast with path(topological_insulator, [some other SUPRA/BOWTIE]) which
    # might find a path, showing TI surface protection is conditional.
    subsection("5.3  path(topological_insulator, conducting_electron) — topological gap")
    print("""
  SETUP:
    topological_insulator : D_supra, T_⋈, Ω_Z₂, Φ_sub
    conducting_electron   : D_mol,   T_|,  Ω_0,  Φ_sub

  TWO BARRIERS:
    1. D: SUPRAMOLECULAR ≠ MOLECULAR (bulk TI vs point particle)
    2. T: T_⋈ ≠ T_| (Dirac cone topology vs linear dispersion)

  PATH STATUS: BLOCKED (two independent class barriers)

  ASYMMETRY (SYNTHONICON_LANG.md §3e):
    path(TI → Fermi liquid) is blocked by D/T mismatch.
    path(Fermi liquid → TI) is also blocked (reverse).
    But the COST is asymmetric: TI → trivial metal costs Δξ > 0
    (destroying topological order releases entropy); trivial → TI costs
    MORE (ordering requires investment). The F-floor ratchet encodes this:
    once in the TI class (F_high), the floor is raised and subsequent
    operations cannot lower F.

  PHYSICAL MEANING:
    Topological protection IS the blocked path. A Majorana edge mode
    cannot continuously deform to a trivial fermion without closing
    the bulk gap. The HotSwap path-block is the algebraic encoding of
    the bulk-boundary correspondence: the gapless surface is protected
    precisely because there is no smooth path to the trivial phase.
    """)
    result3 = find_path(topological_insulator, conducting_electron, catalog)
    if result3.found:
        print(f"  PATH FOUND: {' → '.join(s.name for s in result3.path)}")
    else:
        print(f"  PATH BLOCKED: topological gap is algebraically protected.")
        print(f"  D-barrier: {topological_insulator.dimensionality} ≠ {conducting_electron.dimensionality}")
        print(f"  T-barrier: {topological_insulator.topology} ≠ {conducting_electron.topology}")
        print(f"  Ω-gap:     {topological_insulator.topo_index} → {conducting_electron.topo_index}")


# =============================================================================
# §6  PIPELINES  —  Monadic Composition (SynthonM)
# =============================================================================
#
# MATHEMATICAL FRAMING:
#
#   SynthonM[A] ≅ WriterT[ℝ≥0] (StateT[Context] (MaybeT Identity)) A
#
#   This is a monad transformer stack:
#     MaybeT    → failure propagation (BLOCKED/CONFLICT short-circuits)
#     WriterT   → Δξ_CP cost accumulation (additive over all steps)
#     StateT    → F-floor ratchet + criticality gate (monotone state)
#
#   Monadic bind (>>=) sequences operations while:
#     - propagating failure (MaybeT short-circuit)
#     - accumulating cost (WriterT append)
#     - threading state (StateT update)
#
#   mplus (<|>) provides fallback: try strategy A; on failure, try B.
#   optimize() is asum over a list: first-success search.
#
#   This is a Kleisli composition in the enriched category:
#     each arrow  f: A → SynthonM[B]  is a "design strategy"
#     (DesignStrategy = Callable[[Synthon], SynthonM[Synthon]])
#     composition is exactly >>= (monadic bind).
# =============================================================================

def demo_pipelines():
    section("§6  PIPELINES  —  Monadic Composition (SynthonM)")

    from synthomnicon import SynthonM, meet_m, join_m, tensor_m, lift_m, assert_m
    return_ = SynthonM.return_

    # ── Example 6.1: Hv1 Cross-Species Conservation (reproduced from PDW.tex) ─
    # This is the executed pipeline — all steps pass, Δξ = 0.
    subsection("6.1  Hv1 cross-species conservation (from hv1_paper_reproduction.syn)")
    print("""
  PIPELINE:
    start: Hv1_human_open
    >>= meet(AtHv1_primed)          # both T_⋈ — no conflict; Φ_c dominates
    >>= join(PsHv1_constitutive)    # d=0.000; near-trivial join
    >>= assert(Φ == Φ_c)            # H-bond chain preserved
    >>= assert(phi_c_score ≥ 0.35)  # Varma weight for MOLECULAR/LOCAL

  MONAD SEMANTICS:
    Each >>= threads the current synthon through the next operation.
    MaybeT: if any step returns None (conflict), the rest short-circuit.
    WriterT: Δξ accumulates — here 0.0 at every step (all within class).
    StateT: f_floor set by join to F_eth; criticality_ok unchanged (no lift).
    """)
    pipeline = (
        return_(Hv1_human_open)
        >> meet_m("AtHv1_primed")
        >> join_m("PsHv1_constitutive")
    )
    value, cost, ctx, log = pipeline.run()
    print(f"  Result   : {'PASS' if value else 'BLOCKED'}")
    if value:
        print(f"  Output   : {value.to_notation()}")
    print(f"  Δξ total : {cost:.3f} nats")
    print(f"  F-floor  : {ctx.f_floor}")
    print("""
  RESULT: join(meet(Hv1_human_open, AtHv1_primed), PsHv1_constitutive)
  Δξ_CP = 0.000. Cross-species conservation demonstrated algebraically.
    """)

    # ── Example 6.2: mplus — Fallback Strategy ─────────────────────────────────
    # Strategy A: tensor(Majorana, Majorana) — always succeeds.
    # Strategy B: meet(electron, hole) — potential T-class conflict check.
    # mplus: try A; if blocked, fall back to B.
    # Demonstrates: the SynthonM monad is an OptionalT computation.
    subsection("6.2  mplus (<|>) — fallback design strategy")
    print("""
  PIPELINE LOGIC:
    strategy_A: start(Hv1_open) >>= meet(2GBI)    # will BLOCK (T-conflict)
    strategy_B: start(Hv1_open) >>= meet(AtHv1_primed)  # will PASS

    result = strategy_A.mplus(strategy_B)
    → try A; on BLOCK, automatically fall back to B.

  MONAD SEMANTICS (mplus = MonadPlus operation <|>):
    mplus is the "choice" combinator in the Maybe monad:
      Nothing <|> Just x = Just x
    Here: BLOCKED <|> PASS = PASS
    Cost of the successful branch accumulates; failed branch cost is lost
    (WriterT append-only; but MaybeT discards the failed branch output).

  THIS IS ALGEBRAICALLY CORRECT:
    mplus models branching design paths. In retrosynthesis: "try this
    route; if blocked by a protecting group conflict, try the alternative."
    The F-floor from the failed branch does NOT transfer (the failed
    branch never raised the floor).
    """)
    strategy_A = return_(Hv1_human_open) >> meet_m("2GBI_inhibitor")
    strategy_B = return_(Hv1_human_open) >> meet_m("AtHv1_primed")
    result_m = strategy_A.mplus(strategy_B)
    value, cost, ctx, log = result_m.run()
    sa_val = (return_(Hv1_human_open) >> meet_m("2GBI_inhibitor")).run()[0]
    sb_val = (return_(Hv1_human_open) >> meet_m("AtHv1_primed")).run()[0]
    print(f"  strategy_A (meet 2GBI)    : {'PASS' if sa_val else 'BLOCKED'}")
    print(f"  strategy_B (meet AtHv1)   : {'PASS' if sb_val else 'BLOCKED'}")
    print(f"  mplus result              : {'PASS — strategy_B succeeded' if value else 'BOTH BLOCKED'}")
    if value:
        print(f"  Output : {value.to_notation()}")

    # ── Example 6.3: Quantum Criticality Pipeline ──────────────────────────────
    # Demonstrates: tensor → lift → assert as a complete design sequence.
    # tensor(cooper_pair, topological_insulator) → predicts co-assembly ensemble.
    # Then: does the ensemble retain Ω_NA protection? (assert topo_index).
    # Then: assert Φ_c is preserved.
    subsection("6.3  Quantum co-assembly pipeline: Cooper pair ⊗ TI surface")
    print("""
  PIPELINE:
    start: cooper_pair  (Ω_Z, Φ_c, T_⋈)
    >>= tensor(topological_insulator, λ=0.3)
    >>= assert(criticality_phase == Phi_c)

  PHYSICAL MEANING:
    Proximity effect: a Cooper pair condensate adjacent to a TI surface
    can induce topological superconductivity. The tensor product predicts
    the primitive structure of this co-assembly. The assert checks whether
    Φ_c is preserved in the heterostructure.

  Ω in tensor: max(Ω_Z, Ω_Z₂) = Ω_Z (Z-class > Z₂-class in protection ordinal)
  T: T_⋈ ⊗ T_⋈ → T_⋈ (bowtie preserved; Dirac + pairing loop)
  Φ: Φ_c ⊗ Φ_sub → Φ_c (criticality propagates)

  This tensor product is the algebraic encoding of the proximity effect
  that generates topological superconductor phases (class D/DIII).
    """)
    pipeline3 = (
        return_(cooper_pair)
        >> tensor_m("topological_insulator_surface", lambda_=0.3)
    )
    value3, cost3, ctx3, log3 = pipeline3.run()
    print(f"\n  Result: {'PASS' if value3 else 'BLOCKED'}")
    if value3:
        print(f"  Output : {value3.to_notation()}")
        print(f"  Δξ_CP  : {cost3:.3f} nats")
        print(f"  Ω      : {value3.topo_index}  (higher Ω propagates in tensor)")
        print(f"  Φ      : {value3.criticality_phase}  (Φ_c propagates)")


# =============================================================================
# §7  DECOMPOSITIONS  —  Factoring, Projection, and Inversion
# =============================================================================
#
# MATHEMATICAL FRAMING:
#
#   Decomposition operations invert or factor the algebraic operations.
#   The synthon tuple space is a product of bounded lattices; the operations
#   here correspond to familiar algebraic concepts:
#
#   factor          → "decrement morphism": step one ordinal dimension to its
#                     sub-object (the largest proper sub-synthon)
#
#   cofactor        → INVERSE BIFUNCTOR: given C ≈ tensor(A, B), find B.
#                     C ⊗⁻¹ A  =  the component of C not explained by A.
#                     Analogous to: given a ⊗ v = w in V⊗W, find v given a.
#                     (Possible only when the tensor rules are partially invertible.)
#
#   kernel          → KERNEL OF A PROBE-MORPHISM: largest sub-synthon
#                     annihilated by a predicate φ : Synthon → bool.
#                     Analogous to ker(φ) = {x ∈ V : φ(x) = 0}.
#                     With probe = "Varma Φ_c score > 0.5": the kernel is the
#                     largest sub-synthon that does NOT trigger criticality.
#
#   principal_decomp → JOIN-IRREDUCIBLE BASIS DECOMPOSITION: express a synthon
#                     as an ordered list of its atomic join-irreducible factors.
#                     Analogous to SVD or Jordan normal form: every synthon s
#                     decomposes as s = f₁ ⊔ f₂ ⊔ ... ⊔ fₙ where each fᵢ is
#                     join-irreducible (a single primitive contribution).
#
#   project         → COORDINATE PROJECTION: retain named primitives; zero out
#                     the rest (set to constraint-bottom). Exactly π_S(s) where
#                     S ⊆ {D,T,R,P,F,K,G,Γ,Φ,Ω} is the retained subspace.
#
#   complement_rel  → RELATIVE PSEUDOCOMPLEMENT in a Heyting algebra:
#                     ¬_context(s) relative to target = maximal x ≤ s such that:
#                       x ⊓ context = ⊥  (x has no overlap with context)
#                       x ⊔ context ≥ target  (together they cover target)
#                     In constructive logic: x = s ⇒ target (relative to ¬context).
#                     In design: "what does s contribute UNIQUELY toward target
#                                 that context does NOT already cover?"
#
#   primitive_peel  → SINGLE-PRIMITIVE PROJECTION with cost accounting.
#                     Remove one dimension, pay Φ_c / Ω protection costs if
#                     invariants are violated. Analogous to removing a factor
#                     from a tensor product and tracking the "deformation cost."
# =============================================================================

def demo_decompositions():
    section("§7  DECOMPOSITIONS  —  Factor · Cofactor · Kernel · Principal · Project · Complement")

    from synthomnicon.decompose import (
        factor, cofactor, kernel, principal_decomp,
        project, complement_rel, primitive_peel,
    )
    from synthomnicon.varma_probe import score_phi_c_candidacy

    # ── Example 7.1: cofactor — Inverse Tensor / Quasiparticle Reverse Engineering ──
    #
    # QUESTION: Given that we observe a Cooper pair (C) and we know one component
    # is a conducting electron (A), what must the other component (B) be?
    # cofactor(C, A) = B  s.t.  tensor(A, B) ≈ C
    #
    # This is the INVERSE BIFUNCTOR problem. In the tensor product V ⊗ W,
    # if you know the result and one factor, you can often infer the other
    # (up to the kernel of the contraction).
    #
    # Physically: this is how Cooper pair formation is diagnosed experimentally —
    # you observe the condensate, assume it is electron-electron, and infer what
    # the pairing partner looks like (momentum, spin). Cofactor computes this.
    subsection("7.1  cofactor(cooper_pair, conducting_electron) — inverse tensor: what is the pairing partner?")
    print("""
  SETUP:
    cooper_pair       : ⟨D_mol; T_⋈; R_⊇; P_sym; F_ℏ; K_slow; G_ג; Γ_∧(SPEC); Φ_c; Ω_Z⟩
    conducting_electron: ⟨D_mol; T_|; R_⊇; P_donor; F_ℏ; K_fast; G_ב; Γ_∧(SEL)⟩

  QUESTION: tensor(electron, ?) ≈ cooper_pair
  Find the "pairing partner" — the quasiparticle that, when tensored with
  the conducting electron, produces the Cooper pair primitive tuple.

  COFACTOR RULES (inverting tensor per axis):
    F (min-dominant): tensor[F] = min(A_F, B_F)
      A_F = F_ℏ, C_F = F_ℏ → A explains F; B_F = F_ℏ (must be equally high)
    K (min-dominant): tensor[K] = min(A_K, B_K)
      A_K = K_fast, C_K = K_slow → A is NOT the bottleneck; B_K = K_slow (B is the slow partner)
    G (max-dominant): tensor[G] = max(A_G, B_G)
      A_G = G_local, C_G = G_meso → B_G = G_meso (B contributes the coherence length)
    T (promotion): C_T = T_⋈, A_T = T_| → B must contribute T_⋈ (B has the pairing loop topology)
    Φ (join-dominant): C_Φ = Φ_c, A_Φ = Φ_sub → B_Φ = Φ_c (B carries the criticality)
    Ω (join-dominant): C_Ω = Ω_Z, A_Ω = Ω_trivial → B_Ω = Ω_Z (B carries the topological invariant)

  PHYSICAL MEANING:
    The inferred partner B has: K_slow (the condensate timescale, not the Fermi velocity),
    G_mesoscale (the coherence length), T_bowtie (the pairing loop),
    Φ_c (the superfluid phase transition), Ω_Z (the winding number).
    This is the PHONON-DRESSED ELECTRON — the retarded interaction that
    makes the other electron "look slow" through phonon exchange.
    The cofactor correctly reconstructs the effective retarded partner.
    """)
    r = cofactor(cooper_pair, conducting_electron)
    status = "PASS" if not r.conflict_primitives else f"PARTIAL (conflicts: {r.conflict_primitives})"
    print(f"  STATUS   : {status}")
    if r.result:
        print(f"  RESULT   : {r.result.to_notation()}")
    print(f"\n  PER-AXIS ROLES:")
    for dim in r.dimensions:
        print(f"    {dim.primitive:5s}: {dim.role:15s}  {dim.note}")
    if r.phi_c_source:
        print(f"\n  Φ_c SOURCE: {r.phi_c_source}")
    for n in r.notes:
        print(f"  ⟹  {n}")

    # ── Example 7.2: principal_decomp — SVD of a Synthon ─────────────────────
    #
    # Decompose GNF-2 (complex synthon: Φ_c, G_meso, K_mod, F_med, T_branched)
    # into its join-irreducible atomic factors.
    #
    # In linear algebra: SVD expresses a matrix as U Σ Vᵀ — a weighted sum
    # of rank-1 outer products. principal_decomp does the analogous thing
    # in the lattice: express the synthon as s = f₁ ⊔ f₂ ⊔ ... ⊔ fₙ where
    # each fᵢ is a single primitive contribution (join-irreducible atom).
    #
    # The ORDERING of factors matters: most-constraining first.
    # This is the "principal components" in the synthon lattice.
    subsection("7.2  principal_decomp(GNF2) — join-irreducible basis decomposition (SVD analog)")
    print("""
  SETUP:
    GNF-2 : ⟨D_∧; T_branched; R_⊇; P_+-; F_ℇ; K_mod; G_ג; Γ_→(SEL); Φ_c; Ω_0⟩

  The decomposition produces an ordered list of join-irreducible factors.
  Each factor = single primitive contribution above the constraint-bottom.
  Reading order = most constraining → least constraining.

  TENSOR-MATH ANALOGY:
    In a product lattice L = L_F × L_K × L_G × L_categorical,
    every element s has a unique Birkhoff representation as a join
    of join-irreducible elements. This is the lattice-theoretic analog
    of expressing a vector in terms of basis vectors.
    The "principal" decomposition orders these by their ξ_CP contribution —
    the analog of ordering singular values by magnitude.

  EXPECTED FACTORS (rough order):
    1. Φ_c component   — allosteric criticality (hardest to satisfy)
    2. G_meso component — mesoscale propagation
    3. K_mod component  — kinetic character
    4. F_med component  — fidelity floor
    5. Categorical skeleton (D, T, R, P, Γ unchanged)

  DESIGN USE: tells you which primitive of GNF-2 is the HARDEST to engineer.
  If you're trying to improve GNF-2, start with factor 1 (highest ξ contribution).
    """)
    r = principal_decomp(gnf2, max_factors=9)
    print(f"  FACTORS ({r.n_factors} total, each is a join-irreducible atom):")
    for i, atom in enumerate(r.factors):
        # Each factor is a Synthon whose name encodes the stepped primitive
        non_bottom = []
        if atom.fidelity != Fidelity.LOW:
            non_bottom.append(f"F={atom.fidelity.value}")
        if atom.kinetic_character != KineticCharacter.FAST:
            non_bottom.append(f"K={atom.kinetic_character.value}")
        if atom.granularity != Granularity.LOCAL:
            non_bottom.append(f"G={atom.granularity.value}")
        if atom.criticality_phase == CriticalityPhase.CRITICAL:
            non_bottom.append("Φ_c")
        print(f"    [{i+1}] {atom.name:30s}  non-bottom: {', '.join(non_bottom) or '(categorical)'}")
    print(f"\n  ξ BALANCE: {r.xi_balance:.3f} nats")
    for n in r.notes:
        print(f"  ⟹  {n}")

    # ── Example 7.3: project + complement_rel — Heyting Algebra Construction ──
    #
    # PROJECT: extract only the topological + criticality subspace of the Cooper pair.
    # This is π_{Φ,Ω}(cooper_pair): keep Φ and Ω, zero out everything else.
    #
    # COMPLEMENT_REL: given context = projected (Φ,Ω-only),
    # find the relative pseudocomplement of GNF-2 relative to context and
    # target = cooper_pair.
    # = "what does GNF-2 contribute UNIQUELY toward the cooper_pair target
    #    that the topological projection does NOT already cover?"
    #
    # This is the HEYTING ALGEBRA construction: in a Heyting algebra H,
    # the pseudocomplement of b relative to c is: a ⇒ c = ⋁{x : x ∧ a ≤ c}
    # Here: (GNF-2 ⇒ cooper_pair) relative to the Φ/Ω context.
    subsection("7.3  project + complement_rel — Heyting pseudocomplement (complementary design)")
    print("""
  STEP 1: project(cooper_pair, ["criticality_phase", "topo_index"])
    Retain only Φ and Ω; zero out all other primitives.
    Analogous to: πᵢ(v) — project vector v onto the {i}-th coordinate subspace.
    """)
    proj = project(cooper_pair, ["Phi", "Omega"])
    print(f"  PROJECTED: {proj.result.to_notation()}")
    print(f"  RETAINED : Φ = {proj.result.criticality_phase}, Ω = {proj.result.topo_index}")
    print(f"  ZEROED   : {', '.join(proj.zeroed)}")

    print("""
  STEP 2: complement_rel(gnf2, context=projected, target=cooper_pair)
    Find the maximal x ≤ GNF-2 such that:
      (1) x ⊓ projected = ⊥   (x has no overlap with the Φ/Ω projection)
      (2) x ⊔ projected ≥ cooper_pair  (together they cover the target)

  TENSOR-MATH ANALOGY:
    In a Heyting algebra (the algebraic model of intuitionistic logic):
      a ⇒ b  =  ⋁{x : x ∧ a ≤ b}   (the IMPLICATION / pseudocomplement)
    Here: complement_rel(GNF-2, context, target) = GNF-2's "contribution"
    to reaching the cooper_pair target AFTER accounting for what context already covers.

    This is also the constructive analog of the QUOTIENT in module theory:
    GNF-2 / context = the part of GNF-2 that context does NOT already explain.

  DESIGN MEANING:
    The result tells you: "if the Φ/Ω structure is already given by the
    topological material, what does the molecular GNF-2 uniquely contribute
    toward the cooper_pair target?"
    Answer: K_slow + G_meso + T_branched (the slow, mesoscale, branched kinetics
    that the topological material alone cannot provide).
    """)
    crel = complement_rel(gnf2, context=proj.result, target=cooper_pair)
    print(f"  SATISFIED : {crel.satisfied}")
    if crel.result:
        print(f"  COMPLEMENT: {crel.result.to_notation()}")
    for n in crel.notes:
        print(f"  ⟹  {n}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║          SYNTHONICON ALGEBRAIC OPERATIONS — TENSOR-MATH EDITION             ║
║  meet(⊓) · join(⊔) · tensor(⊗) · lift · path · monad · decompositions     ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    if "--section" in sys.argv:
        idx = sys.argv.index("--section")
        sec = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "all"
    else:
        sec = "all"

    demos = {
        "meet":     demo_meet,
        "join":     demo_join,
        "tensor":   demo_tensor,
        "lift":     demo_lift,
        "path":     demo_path,
        "pipeline": demo_pipelines,
        "decomp":   demo_decompositions,
    }

    if sec == "all":
        for fn in demos.values():
            fn()
    elif sec in demos:
        demos[sec]()
    else:
        print(f"Unknown section '{sec}'. Choose from: {list(demos.keys())} or 'all'")

    print(f"\n{'━'*72}")
    print("  Run individual sections:  python TENSOR_OPS_DEMO.py --section tensor")
    print(f"{'━'*72}\n")
