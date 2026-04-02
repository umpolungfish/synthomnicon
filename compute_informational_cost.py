"""
Compute actual informational cost between Taguchi-optimized and realized states.

Uses the actual tensor/meet/join operations from synthomnicon.algebra.
"""
import sys
sys.path.insert(0, '/home/mrnob0dy666/SynthOmnicon')

from synthomnicon.models import (
    Synthon, Fidelity, KineticChar, Criticality, Granularity, Topology,
    Dimensionality, Recognition, Polarity, Grammar, Protection, Stoichiometry, Chirality
)
from synthomnicon.algebra import primitive_mismatches, tuple_distance, meet, join

# Taguchi-optimized state (simulated criticality)
TAGUCHI_STATE = Synthon(
    name="taguchi_optimized",
    dimensionality=Dimensionality.D_cube,  # Supramolecular (simulation scope)
    topology=Topology.T_network,
    recognition_mode=Recognition.R_superset,  # Non-covalent
    polarity=Polarity.P_pm_pseudo,
    fidelity=Fidelity.F_hbar,  # High fidelity in simulation
    kinetic_character=KineticChar.K_fast,  # Clean transitions
    granularity=Granularity.G_beth,  # Local scope (simulation)
    grammar=Grammar.G_and,
    criticality_phase=Criticality.Phi_c,  # At criticality
    protection=Protection.Omega_0,
    stoichiometry=Stoichiometry.one_one,
    chirality=Chirality.H0,
)

# Realized market state (actual criticality with friction)
REALIZED_STATE = Synthon(
    name="realized_market",
    dimensionality=Dimensionality.D_cube,  # Supramolecular
    topology=Topology.T_network,
    recognition_mode=Recognition.R_superset,  # Non-covalent
    polarity=Polarity.P_pm_pseudo,
    fidelity=Fidelity.F_eth,  # Lower fidelity in real markets
    kinetic_character=KineticChar.K_mod,  # More friction
    granularity=Granularity.G_gimel,  # Mesoscale (real market scope)
    grammar=Grammar.G_and,
    criticality_phase=Criticality.Phi_c,
    protection=Protection.Omega_0,
    stoichiometry=Stoichiometry.one_one,
    chirality=Chirality.H0,
)

# Market friction state (slippage, impact, delay)
FRICTION_STATE = Synthon(
    name="market_friction",
    dimensionality=Dimensionality.D_infty,  # Global/temporal
    topology=Topology.T_linear,
    recognition_mode=Recognition.R_superset,  # Non-covalent
    polarity=Polarity.P_pm_pseudo,
    fidelity=Fidelity.F_ell,  # Low fidelity
    kinetic_character=KineticChar.K_slow,  # Slow execution
    granularity=Granularity.G_aleph,  # Global friction
    grammar=Grammar.G_and,
    criticality_phase=Criticality.Phi_sub,  # Subcritical
    protection=Protection.Omega_0,
    stoichiometry=Stoichiometry.one_one,
    chirality=Chirality.H0,
)

print("=" * 80)
print("ACTUAL TENSOR OPERATIONS: Informational Cost Analysis")
print("=" * 80)
print()

# 1. Canonical Hamming distance
print("1. CANONICAL HAMMING DISTANCE (primitive_mismatches)")
print("-" * 80)

d_taguchi_realized = primitive_mismatches(TAGUCHI_STATE, REALIZED_STATE)
print(f"d(Taguchi, Realized) = {d_taguchi_realized}/12 primitives")

d_taguchi_friction = primitive_mismatches(TAGUCHI_STATE, FRICTION_STATE)
print(f"d(Taguchi, Friction) = {d_taguchi_friction}/12 primitives")

d_realized_friction = primitive_mismatches(REALIZED_STATE, FRICTION_STATE)
print(f"d(Realized, Friction) = {d_realized_friction}/12 primitives")

print()

# 2. Weighted tuple distance
print("2. WEIGHTED TUPLE DISTANCE (tuple_distance)")
print("-" * 80)

w_taguchi_realized = tuple_distance(TAGUCHI_STATE, REALIZED_STATE)
print(f"w(Taguchi, Realized) = {w_taguchi_realized:.3f}")

w_taguchi_friction = tuple_distance(TAGUCHI_STATE, FRICTION_STATE)
print(f"w(Taguchi, Friction) = {w_taguchi_friction:.3f}")

w_realized_friction = tuple_distance(REALIZED_STATE, FRICTION_STATE)
print(f"w(Realized, Friction) = {w_realized_friction:.3f}")

print()

# 3. Meet operation (common core)
print("3. MEET OPERATION (common core)")
print("-" * 80)

meet_result = meet(TAGUCHI_STATE, REALIZED_STATE)
# Check for conflicts by looking at dimensionality (will be "CONFLICT" string if clash)
has_conflict = meet_result.dimensionality == "CONFLICT"
if has_conflict:
    conflicts = []
    for field in ['dimensionality', 'topology', 'recognition_mode', 'polarity', 'grammar', 
                  'criticality_phase', 'stoichiometry']:
        if getattr(meet_result, field) == "CONFLICT":
            conflicts.append(field)
    print(f"Meet conflicts: {conflicts}")
    print(f"Meet cost: {meet_result.xi_cp:.3f} nats")
else:
    print(f"Meet successful: {meet_result.s1_name} ∧ {meet_result.s2_name}")
    print(f"Meet fidelity: {meet_result.fidelity}")
    print(f"Meet kinetic: {meet_result.kinetic_character}")
    print(f"Meet granularity: {meet_result.granularity}")
print()

# 4. Join operation (maximal fusion)
print("4. JOIN OPERATION (maximal fusion)")
print("-" * 80)

join_result = join(TAGUCHI_STATE, REALIZED_STATE)
has_conflict = join_result.dimensionality == "CONFLICT"
if has_conflict:
    conflicts = []
    for field in ['dimensionality', 'topology', 'recognition_mode', 'polarity', 'grammar',
                  'criticality_phase', 'stoichiometry']:
        if getattr(join_result, field) == "CONFLICT":
            conflicts.append(field)
    print(f"Join conflicts: {conflicts}")
    print(f"Join cost: {join_result.xi_cp:.3f} nats")
else:
    print(f"Join successful: {join_result.s1_name} ∨ {join_result.s2_name}")
    print(f"Join fidelity: {join_result.fidelity}")
    print(f"Join kinetic: {join_result.kinetic_character}")
    print(f"Join granularity: {join_result.granularity}")
print()

# 5. Informational cost calculation
print("5. INFORMATIONAL COST CALCULATION")
print("-" * 80)

# Cost = weighted distance from optimal to realized
informational_cost = w_taguchi_realized
print(f"Informational cost (Taguchi → Realized): {informational_cost:.3f} nats")

# Convert to percentage loss
# Using the +2.303 nat criticality-lift cost as reference
reference_cost = 2.303  # ln(10)
predicted_loss_pct = (informational_cost / reference_cost) * 100
print(f"Reference cost (ln 10): {reference_cost:.3f} nats")
print(f"Predicted loss: {predicted_loss_pct:.1f}%")

# Actual observed loss
actual_loss_pct = ((51.4 - 37.82) / 51.4) * 100
print(f"Actual observed loss: {actual_loss_pct:.1f}%")

print()
print("=" * 80)
print("ANALYSIS")
print("=" * 80)

if abs(predicted_loss_pct - actual_loss_pct) < 10:
    print(f"✓ Framework prediction ({predicted_loss_pct:.1f}%) matches observation ({actual_loss_pct:.1f}%)")
else:
    print(f"✗ Framework prediction ({predicted_loss_pct:.1f}%) differs from observation ({actual_loss_pct:.1f}%)")

print()
print("Primitive mismatches driving the loss:")
print(f"  F: {TAGUCHI_STATE.fidelity} → {REALIZED_STATE.fidelity} (simulation → real)")
print(f"  K: {TAGUCHI_STATE.kinetic_character} → {REALIZED_STATE.kinetic_character} (fast → mod)")
print(f"  G: {TAGUCHI_STATE.granularity} → {REALIZED_STATE.granularity} (beth → gimel)")
print()
print("The 3 primitive mismatches (F, K, G) account for the informational cost.")
print("=" * 80)
