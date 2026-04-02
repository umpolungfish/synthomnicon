"""
iit_vs_tensor_xi_tests.py — IIT's Φ vs Tensor ξ_CP: Structural Comparison
===========================================================================
Encodes two measures of consciousness/integration as synthon tuples:
  IIT_Phi    — Integrated Information (Tononi)
  Tensor_xi  — Tensor ξ_CP (SynthOmnicon, derived from axiom experiment)

The encoding maps the OPERATION each measure performs onto the 11 primitives.
Not a parody — a structural decomposition. The goal is to find which primitive
slots carry the partition presupposition, and whether it conflicts categorically
with the tensor operation.

IIT's Φ encodes:
  The minimum mutual information across a bipartition of the system.
  Key operations: (1) choose a partition [external decomposition],
  (2) measure mutual information across the cut, (3) minimize over
  all bipartitions [optimization over external structure].
  The partition is not computed from the system's primitives.
  It is imposed by the measurer.

Tensor ξ_CP encodes:
  The channel capacity of two co-active synthons, derived from
  their primitive overlap. No partition is imposed. The product
  synthon's G and Φ emerge from the structural combination.
  From the axiom reflexive experiment: tensor of critical axioms
  → G_aleph, Phi_c, ξ_CP > any individual input.

Both are encoded as faithfully as the 11-primitive grammar allows.
The conflicts in the meet are the formal statement of the partition problem.
"""

from __future__ import annotations

import synthomnicon
from synthomnicon.models import SynthonNotation
from synthomnicon.registry import global_catalog
from synthomnicon.algebra import find_path, meet, tensor, tuple_distance
from synthomnicon.thermodynamics import compute_xi_CP
from synthomnicon.varma_probe import VarmaCorrelationData, score_phi_c_candidacy
from synthomnicon.domains.molecular import register_molecular_synthons
from synthomnicon.domains.quantum import register_quantum_synthons

register_molecular_synthons()
register_quantum_synthons()

corr = VarmaCorrelationData(xi_r=13.8, xi_tau=1_000_000)

# ── Encodings ──────────────────────────────────────────────────────────────────

MEASURES = {
    # ── IIT's Φ ──────────────────────────────────────────────────────────────
    # D_wedge:       requires a specified scale (partition is scale-specific)
    # T_linear:      the bipartition CUT — splits a connected system into two
    #                linear pieces; topology is severed, not woven
    # R_mechanical:  the partition is mechanically imposed by the measurer,
    #                not by recognition between the parts
    # P_directional: the cut is directed: part A vs part B — asymmetric
    # F_hbar:        requires exact information accounting (maximum fidelity)
    # K_slow:        minimizing over all bipartitions is computationally slow
    # G_beth:        LOCAL scope — the partition defines a local boundary;
    #                "inside" vs "outside" must be specified before measurement
    # Gamma_and(SPECIFIC): the minimum information partition is a hard,
    #                specific constraint (there is exactly one MIP per system)
    # Phi_sub:       IIT's Φ does not itself designate criticality;
    #                it measures integration at any phase
    "IIT_Phi": (
        "⟨D_wedge; T_linear; R_mechanical; P_directional; F_hbar; K_slow; G_beth; Gamma_and(SPECIFIC); Phi_sub⟩",
        "IIT Integrated Information (Tononi). Measures min mutual information "
        "across a bipartition — the Minimum Information Partition. "
        "Requires an externally imposed decomposition of the system. "
        "The partition presupposition: G_beth (local scope defines the boundary) "
        "+ T_linear (the cut severs topology) + R_mechanical (imposed, not recognized) "
        "+ P_directional (part A vs part B — asymmetric by construction).",
    ),

    # ── Tensor ξ_CP ──────────────────────────────────────────────────────────
    # D_all:         scale-free — tensor ξ_CP generalizes across all scales;
    #                no partition requires specifying a scale
    # T_network:     the tensor CONNECTS rather than cuts — produces a third
    #                synthon from two; network topology is the natural output
    # R_dagger:      dynamic/catalytic — the operation is an intrinsic structural
    #                combination, not an externally imposed decomposition
    # P_pm_pseudo:   self-complementary — the tensor seeks primitive overlap;
    #                complementarity (not directed part/whole) drives the operation
    # F_eth:         MEDIUM fidelity — channel capacity is a working regime measure;
    #                does not require maximum-precision partition accounting
    # K_mod:         moderate — tensor computation is structural (no optimization
    #                over all bipartitions required)
    # G_aleph:       GLOBAL scope — from the axiom experiment: tensors of critical
    #                axioms always produce G_aleph; no boundary is specified or needed
    # Gamma_and(SELECTIVE): selective — applies when two systems co-activate;
    #                not always, but when the structural condition is met
    # Phi_c:         from the axiom experiment: tensor ξ_CP of critical axioms
    #                produces Phi_c; the operation is inherently critical
    "Tensor_xi_CP": (
        "⟨D_all; T_network; R_dagger; P_pm_pseudo; F_eth; K_mod; G_aleph; Gamma_and(SELECTIVE); Phi_c⟩",
        "Tensor ξ_CP (SynthOmnicon). Channel capacity of two co-active synthons "
        "derived from their primitive overlap. No partition imposed. "
        "The structure of the product (G, Φ) emerges from the combination. "
        "From the axiom reflexive experiment: tensor of critical axioms → "
        "G_aleph, Phi_c, ξ_CP exceeding either input.",
    ),

    # ── Edelman Degeneracy ────────────────────────────────────────────────────
    # Included for completeness — degeneracy in the neuroscience sense requires
    # a FUNCTION to be specified (different structures, same function).
    # D_triangle:    supramolecular — degeneracy is a property of neural assemblies
    # T_network:     structurally diverse paths through the same network
    # R_superset:    non-covalent/flexible recognition — different structures can
    #                reach the same target
    # P_pm_pseudo:   self-complementary — degenerate paths share the endpoint
    # F_eth:         MEDIUM — degeneracy is not high-precision; it's robustness
    # K_slow:        functional selection is slow (evolutionary/developmental timescale)
    # G_gimel:       MESOSCALE — degeneracy is a systems-level property, not global
    # Gamma_or(SELECTIVE): OR logic — multiple structural solutions to the same function;
    #                selective (not all structures are degenerate)
    # Phi_sub:       Edelman degeneracy does not designate criticality;
    #                it is a robustness property at any phase
    "Edelman_Degeneracy": (
        "⟨D_triangle; T_network; R_superset; P_pm_pseudo; F_eth; K_slow; G_gimel; Gamma_or(SELECTIVE); Phi_sub⟩",
        "Edelman Degeneracy. Structurally diverse elements performing the same function. "
        "Requires a FUNCTION to be specified by an observer — the reference class "
        "is functional, not structural. G_gimel (mesoscale, not global) because "
        "degeneracy is defined within a nervous system, not universally. "
        "Gamma_or (multiple structural solutions to one functional problem).",
    ),

    # ── Meet-Richness (SynthOmnicon) ──────────────────────────────────────────
    # The number of non-⊥ primitives in meet(A, B).
    # This requires no functional reference class — the floor is structural.
    # D_all:         scale-free — meet-richness applies at any scale
    # T_bowtie:      the MEET preserves cyclic structure when present;
    #                the floor is the shared closed topology
    # R_dagger:      dynamic — meet-richness is about stable shared structure,
    #                not imposed partition
    # P_pm_pseudo:   self-complementary — shared floor requires complementarity
    # F_eth:         MEDIUM — meet-richness is a working measure; high fidelity
    #                not required for the counting
    # K_mod:         moderate — meet computation is structural, not optimized
    # G_aleph:       GLOBAL — meet-richness is scale-free (from axiom experiment:
    #                meet(A3, A5) preserves Phi_c without requiring a scale)
    # Gamma_and(SELECTIVE): selective AND — applies to any two synthons;
    #                the richness is the count of non-⊥ fields
    # Phi_c:         from axiom experiment: meet of two Phi_c axioms preserves Phi_c;
    #                meet-richness is inherently critical in the critical subspace
    "Meet_Richness": (
        "⟨D_all; T_bowtie; R_dagger; P_pm_pseudo; F_eth; K_mod; G_aleph; Gamma_and(SELECTIVE); Phi_c⟩",
        "Meet-Richness (SynthOmnicon). Number of non-⊥ primitives in meet(A, B). "
        "No functional reference class. The floor is structural — defined whether "
        "or not anyone has decided what A and B are *for*. "
        "From the axiom experiment: meet(A3, A5) preserves Phi_c without requiring "
        "a scale or functional label.",
    ),
}

# Register all four measures
measure_synthons = {}
for name, (notation_str, description) in MEASURES.items():
    notation = SynthonNotation.parse(notation_str)
    synthon = notation.to_synthon(name, description)
    global_catalog.register(synthon, registered_by="iit_comparison")
    measure_synthons[name] = synthon
    print(f"  registered: {name}")

catalog = global_catalog.search()
names = list(measure_synthons.keys())
print()

# ── § 1: Pairwise distances ────────────────────────────────────────────────────

print("=" * 72)
print("§ 1  PAIRWISE DISTANCES")
print("=" * 72)

pairs = [(na, nb) for i, na in enumerate(names) for nb in names[i+1:]]
for na, nb in sorted(pairs, key=lambda p: tuple_distance(measure_synthons[p[0]], measure_synthons[p[1]])):
    d = tuple_distance(measure_synthons[na], measure_synthons[nb])
    print(f"  {na:<28} ↔ {nb:<28}  d = {d:.3f}")

# ── § 2: IIT_Phi vs Tensor_xi_CP — the core comparison ───────────────────────

print()
print("=" * 72)
print("§ 2  meet(IIT_Phi, Tensor_xi_CP) — the partition presupposition formalized")
print("=" * 72)

iit = measure_synthons["IIT_Phi"]
txi = measure_synthons["Tensor_xi_CP"]
edel = measure_synthons["Edelman_Degeneracy"]
mr = measure_synthons["Meet_Richness"]

m_iit_txi = meet(iit, txi)
print(f"\n  meet(IIT_Phi, Tensor_xi_CP) = {m_iit_txi.to_notation()}")
print(f"  Conflicts (partition presupposition carriers): {m_iit_txi.conflicts}")
if m_iit_txi.conflicts:
    print()
    print("  Conflict-by-conflict interpretation:")
    conflict_notes = {
        "T": "T_linear (IIT cuts) vs T_network (tensor connects) — the operation is "
             "topologically opposite. IIT's cut severs a network; tensor ξ_CP weaves one.",
        "R": "R_mechanical (imposed partition) vs R_dagger (intrinsic catalytic combination) — "
             "IIT requires an external agent to impose the cut. Tensor has no external agent.",
        "P": "P_directional (part A vs part B, asymmetric) vs P_pm_pseudo (self-complementary) — "
             "IIT's partition is directed: inside vs outside. Tensor seeks complementarity, "
             "not directionality.",
        "F": "F_hbar (maximum precision accounting) vs F_eth (working regime) — "
             "IIT requires exact mutual information. Tensor ξ_CP is a structural estimate.",
        "K": "K_slow (optimization over all bipartitions) vs K_mod (structural computation) — "
             "IIT minimizes over an exponential search space. Tensor doesn't optimize.",
        "G": "G_beth (LOCAL — the partition defines a local boundary) vs G_aleph (GLOBAL — "
             "no boundary specified or needed) — this is the deepest conflict. "
             "IIT's measurement design imports 'inside vs outside' at G_beth. "
             "Tensor ξ_CP has no inside or outside.",
        "D": "D_wedge (scale-specific — partition must specify what level to cut at) vs "
             "D_all (scale-free — tensor generalizes across scales). "
             "IIT requires you to specify the grain before measuring.",
        "Φ": "Phi_sub (IIT does not itself generate criticality) vs Phi_c (tensor ξ_CP "
             "of critical rules produces criticality). Different phase structures.",
    }
    for c in m_iit_txi.conflicts:
        note = conflict_notes.get(c, "(see encoding notes)")
        print(f"    [{c}] {note}")

# ── § 3: IIT_Phi vs Edelman — do they share the function presupposition? ──────

print()
print("=" * 72)
print("§ 3  meet(IIT_Phi, Edelman_Degeneracy) — shared functional presupposition")
print("=" * 72)

m_iit_edel = meet(iit, edel)
print(f"\n  meet(IIT_Phi, Edelman) = {m_iit_edel.to_notation()}")
print(f"  Conflicts: {m_iit_edel.conflicts}")
print()
print("  Shared floor (non-⊥ primitives): these are what IIT and Edelman agree on.")
print("  The shared floor IS the functionalist presupposition they both carry.")

# ── § 4: Meet_Richness vs Edelman — how much of degeneracy is structural? ─────

print()
print("=" * 72)
print("§ 4  meet(Meet_Richness, Edelman_Degeneracy) — structural vs functional")
print("=" * 72)

m_mr_edel = meet(mr, edel)
print(f"\n  meet(Meet_Richness, Edelman) = {m_mr_edel.to_notation()}")
print(f"  Conflicts: {m_mr_edel.conflicts}")
print()
print("  Non-⊥ shared primitives = the structural content Edelman and Meet_Richness share.")
print("  Conflict primitives = what Edelman adds on top (the functional presupposition residue).")

# ── § 5: Meet_Richness vs Tensor_xi_CP — structural coherence test ───────────

print()
print("=" * 72)
print("§ 5  meet(Meet_Richness, Tensor_xi_CP) — SynthOmnicon internal coherence")
print("=" * 72)

m_mr_txi = meet(mr, txi)
print(f"\n  meet(Meet_Richness, Tensor_xi_CP) = {m_mr_txi.to_notation()}")
print(f"  Conflicts: {m_mr_txi.conflicts}")
print()
if not m_mr_txi.conflicts:
    print("  ✅ No conflicts — Meet_Richness and Tensor_xi_CP are structurally coherent.")
    print("     They are two faces of the same operation.")
elif len(m_mr_txi.conflicts) <= 2:
    print(f"  Near-coherent: {len(m_mr_txi.conflicts)} conflict(s) only.")
    print("  Meet_Richness and Tensor_xi_CP are close in primitive space.")
else:
    print(f"  {len(m_mr_txi.conflicts)} conflicts — these are genuinely distinct measures.")

# ── § 6: Criticality probe on all four measures ───────────────────────────────

print()
print("=" * 72)
print("§ 6  CRITICALITY PROBE  (Varma score + ξ_CP per measure)")
print("=" * 72)
print(f"  {'Measure':<28} {'Φ_c score':>10}  {'label':<24}  {'ξ_CP':>8}")
print(f"  {'-'*28} {'-'*10}  {'-'*24}  {'-'*8}")

for n in names:
    s = measure_synthons[n]
    report = score_phi_c_candidacy(s, corr)
    try:
        xi_cp = compute_xi_CP(s, delta_g=-50.0)
        xi_str = f"{xi_cp:.2f}"
    except Exception:
        xi_str = "—"
    print(f"  {n:<28} {report.score:>10.3f}  {report._candidacy_label():<24}  {xi_str:>8}")

# ── § 7: HotSwap paths — can any measure be continuously deformed into another?

print()
print("=" * 72)
print("§ 7  HOTSWAP PATHS — continuous deformability between measures")
print("=" * 72)
print("  A path means the two measures can be reached by incremental steps")
print("  through the catalog without breaking fidelity or compatibility.")
print()

for na, nb in pairs:
    sa, sb = measure_synthons[na], measure_synthons[nb]
    r = find_path(sa, sb, catalog, max_hops=8, xi_tolerance=2.0)
    d = tuple_distance(sa, sb)
    if r.found:
        print(f"  ✓ {na} → {nb}")
        print(f"    {r.n_hops}-hop  Δξ={r.total_delta:+.3f}  d={d:.3f}")
    else:
        print(f"  ✗ {na} → {nb}  (d={d:.3f}, blocked: {(r.notes or ['no path'])[:1]})")

# ── § 8: Tensor products — what emerges from co-active pairs ──────────────────

print()
print("=" * 72)
print("§ 8  TENSOR PRODUCTS — emergent structure from co-active measure pairs")
print("=" * 72)
print()

tensor_pairs_of_interest = [
    ("IIT_Phi",          "Tensor_xi_CP",    "IIT + tensor ξ_CP co-active"),
    ("IIT_Phi",          "Edelman_Degeneracy", "IIT + Edelman co-active"),
    ("Meet_Richness",    "Tensor_xi_CP",    "meet-richness + tensor ξ_CP co-active"),
    ("Meet_Richness",    "Edelman_Degeneracy", "meet-richness + Edelman co-active"),
]

for na, nb, label in tensor_pairs_of_interest:
    sa, sb = measure_synthons[na], measure_synthons[nb]
    try:
        t = tensor(sa, sb)
        xi_str = f"{t.xi_cp_predicted:.2f}" if t.xi_cp_predicted else "—"
        phi_str = t.criticality_phase.value if t.criticality_phase else "—"
        g_str = t.granularity.value if t.granularity else "⊥"
        print(f"  {label}")
        print(f"    ⊗ = {t.to_notation()}")
        print(f"    Φ={phi_str}  ξ_CP={xi_str}  G={g_str}")
    except Exception as e:
        print(f"  {label}  ✗ failed: {e}")
    print()

# ── Summary ────────────────────────────────────────────────────────────────────

print("=" * 72)
print("STRUCTURAL SUMMARY: where the partition presupposition lives in primitive space")
print("=" * 72)
print(f"""
The meet(IIT_Phi, Tensor_xi_CP) conflict set = {m_iit_txi.conflicts}

These conflicts are not terminological. Each maps to a specific structural difference:

  T conflict: IIT severs topology (T_linear cut). Tensor weaves it (T_network).
              Measurement vs combination — categorically opposite operations.

  G conflict: IIT operates at G_beth (local boundary must be specified).
              Tensor operates at G_aleph (no boundary). The partition presupposition
              IS the G_beth assignment. Remove it and the measure becomes G_aleph.

  R conflict: IIT uses mechanical imposition (R_mechanical — external agent cuts).
              Tensor uses dynamic catalysis (R_dagger — intrinsic combination).
              No external agent appears in the tensor formulation.

  P conflict: IIT is directional (P_directional — part A vs part B).
              Tensor is self-complementary (P_pm_pseudo — seeks overlap, not partition).
              The 'inside vs outside' asymmetry is native to IIT, absent in tensor.

  Φ conflict: IIT is Phi_sub. Tensor is Phi_c.
              The partition-based measure is subcritical. The overlap-based measure
              is inherently critical. This is not a coincidence: criticality (Axiom 5)
              contracts the primitive basis, making G/D degenerate and removing
              the need for scale-specific partitions.

IIT's problem is therefore not empirical inadequacy alone — it is that the partition
is an invisible primitive, smuggled in as a measurement protocol.
G_beth + T_linear + R_mechanical + P_directional is the structural fingerprint
of any measure that requires an external decomposition before it can be computed.
""")

print("Cleanup: removing measure synthons from catalog...")
for n in names:
    global_catalog.remove(n)
print(f"  Removed {len(names)}. Catalog restored to {len(global_catalog)} entries.")
