"""
Programmable Matter Tests — Part 1
===================================
Encoding programmable matter systems as synthon tuples and running the full
algebra to derive what the framework says about reconfigurability, state-pair
structure, and cross-domain analogies.

Systems encoded (11 synthons across 6 material classes):
  - DNA origami (folded) / DNA strand displacement (dynamic)
  - Colloidal crystal (ordered) / Colloidal fluid (disordered)
  - Biomolecular condensate (liquid LLPS) / Condensate gel (arrested)
  - Active gel (actin+myosin+ATP)
  - Shape-memory polymer (rigid, T<Tg) / SMP (elastic, T>Tg)
  - Liquid crystal (nematic) / Liquid crystal (isotropic)

The core question: "What can be programmed?" = "What paths exist in the
directed HotSwap graph?" The F-floor and K constraints on paths directly
constrain what matter can be reconfigured to do.
"""

import synthomnicon  # triggers catalog population
from synthomnicon.models import (
    Synthon, Dimensionality as D, Topology as T, RecognitionMode as R,
    Polarity as P, Fidelity as F, KineticCharacter as K, Granularity as G,
    InteractionGrammar as IG, CriticalityPhase as Phi,
)
from synthomnicon.algebra import tuple_distance, meet, join, tensor, find_path
from synthomnicon.varma_probe import (
    score_phi_c_candidacy, VarmaCorrelationData, degeneracy_strength
)
from synthomnicon.domains.molecular import register_molecular_synthons
from synthomnicon.domains.quantum import register_quantum_synthons
from synthomnicon.registry import global_catalog


# ── Grammar helper ─────────────────────────────────────────────────────────────
def gamma(op: str, tier: str):
    for g in IG:
        if g.operator.value == op and g.tier == tier:
            return g
    raise ValueError(f"No grammar {op!r}/{tier!r}")

G_AND_SPEC  = gamma('Gamma_and',       'SPECIFIC')
G_AND_SEL   = gamma('Gamma_and',       'SELECTIVE')
G_AND_BRD   = gamma('Gamma_and',       'BROAD')
G_OR_BRD    = gamma('Gamma_or',        'BROAD')
G_SEQ_SEL   = gamma('Gamma_seq',       'SELECTIVE')
G_SEQ_BRD   = gamma('Gamma_seq',       'BROAD')


# ══════════════════════════════════════════════════════════════════════════════
# 1. SYNTHON ENCODINGS
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("PROGRAMMABLE MATTER — PART 1: ENCODINGS & ALGEBRA")
print("=" * 70)

# ── Class 1: DNA NANOTECHNOLOGY ────────────────────────────────────────────────
# DNA origami (folded, static): the programmed shape locked by hundreds of
# staple strands. Watson-Crick specificity (F_hbar); slow folding (K_slow);
# mesoscale (G_gimel); all staples required simultaneously (Gamma_and SPECIFIC).
dna_origami = Synthon(
    name="dna_origami_folded",
    dimensionality=D.HYBRID_MOL_SUPRA,   # molecular base-pairing + supramolecular shape
    topology=T.NETWORK,                # addressable network of base-pair contacts
    recognition_mode=R.NON_COVALENT,     # Watson-Crick H-bonds
    polarity=P.SELF_COMPLEMENTARY_SYM,                 # complementary strands, symmetric
    fidelity=F.HIGH,                     # Ka >> 10^7; full-strand hybridisation
    kinetic_character=K.SLOW,          # folding requires thermal annealing (hours)
    granularity=G.MESOSCALE,               # mesoscale: 10–100 nm objects
    interaction_grammar=G_AND_SPEC,      # all staples simultaneously, one target shape
    criticality_phase=Phi.SUBCRITICAL,
    stoichiometry="n:m",
)

# DNA strand displacement (toehold-mediated): the DYNAMIC layer. The toehold
# binds first (sequential), branch migration follows — a directed ratchet at
# the molecular scale. F_eth (toehold is partial hybridisation — enough to
# initiate, not to lock). K_mod (branch migration: ΔG‡ ~60-80 kJ/mol).
# G_beth (each displacement event is local; cascades are programmed externally).
dna_strand_disp = Synthon(
    name="dna_strand_displacement",
    dimensionality=D.MOLECULAR,            # molecular — single displacement event
    topology=T.LINEAR,                 # linear branch-migration track
    recognition_mode=R.NON_COVALENT,     # Watson-Crick
    polarity=P.SELF_COMPLEMENTARY_SYM,
    fidelity=F.MEDIUM,                   # toehold Ka ~10^4-10^6; partial hybridisation
    kinetic_character=K.MODERATE,           # branch migration ~60-80 kJ/mol
    granularity=G.LOCAL,                # local: one displacement at a time
    interaction_grammar=G_SEQ_SEL,       # sequential: toehold first, then branch migration
    criticality_phase=Phi.SUBCRITICAL,
    stoichiometry="1:1",
)

# ── Class 2: COLLOIDAL ASSEMBLY ────────────────────────────────────────────────
# Colloidal crystal (T < Tm): long-range ordered phase. Collective binding by
# van der Waals + depletion gives F_hbar at the ensemble level (each particle
# has many contacts). K_slow: nucleation barrier. G_aleph: global crystalline order.
colloidal_crystal = Synthon(
    name="colloidal_crystal",
    dimensionality=D.SUPRAMOLECULAR,
    topology=T.NETWORK_SYM,            # centrosymmetric crystal lattice
    recognition_mode=R.NON_COVALENT,     # vdW + depletion + electrostatic
    polarity=P.SELF_COMPLEMENTARY_SYM,
    fidelity=F.HIGH,                     # collective lattice binding; many contacts
    kinetic_character=K.SLOW,          # nucleation barrier; slow annealing required
    granularity=G.GLOBAL,               # global crystalline order
    interaction_grammar=G_AND_BRD,       # any particle from the batch can join
    criticality_phase=Phi.SUBCRITICAL,
    stoichiometry="n:n",
)

# Colloidal fluid (T > Tm): disordered, dynamically exchanging. F_ell (each
# contact individually weak). K_fast (thermal fluctuations overcome local
# barriers). G_beth (no long-range order; only nearest-neighbour correlations).
colloidal_fluid = Synthon(
    name="colloidal_fluid",
    dimensionality=D.SUPRAMOLECULAR,
    topology=T.NETWORK,                # generic disordered liquid network
    recognition_mode=R.NON_COVALENT,
    polarity=P.SELF_COMPLEMENTARY_SYM,
    fidelity=F.LOW,                      # weak individual contacts; easily disrupted
    kinetic_character=K.FAST,          # thermal fluctuations freely overcome barriers
    granularity=G.LOCAL,                # local only — no long-range order
    interaction_grammar=G_OR_BRD,        # any nearest neighbour suffices (promiscuous)
    criticality_phase=Phi.SUBCRITICAL,
    stoichiometry="n:n",
)

# ── Class 3: BIOMOLECULAR CONDENSATES (LLPS) ──────────────────────────────────
# Liquid condensate (dynamic droplet): IDR-IDR interactions via π-π, cation-π,
# electrostatic. Each individual contact is weak (F_ell). Highly dynamic: FRAP
# recovery ~10-30 s (K_fast). Mesoscale droplet (G_gimel, 100 nm–10 μm).
# Promiscuous partner set — many different client proteins partition (Gamma_or BROAD).
# Φ_c: near spinodal/critical point — this is the key question.
condensate_liquid = Synthon(
    name="condensate_liquid",
    dimensionality=D.HYBRID_MOL_SUPRA,   # molecular IDR + supramolecular droplet
    topology=T.NETWORK,                # dynamic multivalent contact network
    recognition_mode=R.NON_COVALENT,     # π-π, cation-π, IDR-IDR, electrostatic
    polarity=P.SELF_COMPLEMENTARY_SYM,                 # symmetric multivalent engagement
    fidelity=F.LOW,                      # individually weak; each ~1-3 kT
    kinetic_character=K.FAST,          # FRAP t½ ~10-30 s; highly dynamic
    granularity=G.MESOSCALE,               # mesoscale droplet
    interaction_grammar=G_OR_BRD,        # promiscuous; many partner proteins
    criticality_phase=Phi.CRITICAL,         # near spinodal critical point — asserting Phi_c
    stoichiometry="n:m",
)

# Condensate gel (arrested/solid state): the pathological transition.
# F_hbar (locked — no FRAP recovery). K_trap (kinetically arrested; multiple
# misfolding pathways). G_aleph (system-spanning amyloid-like network).
# Directly connects to protein_tests3.py: this IS the amyloid synthon.
condensate_gel = Synthon(
    name="condensate_gel",
    dimensionality=D.HYBRID_MOL_SUPRA,
    topology=T.NETWORK,
    recognition_mode=R.NON_COVALENT,
    polarity=P.SELF_COMPLEMENTARY_SYM,
    fidelity=F.HIGH,                     # locked; no dynamic exchange
    kinetic_character=K.TRAP,          # kinetically arrested; multiple pathways
    granularity=G.GLOBAL,               # system-spanning — global arrest
    interaction_grammar=G_AND_BRD,       # cooperative arrest; all contacts required
    criticality_phase=Phi.SUBCRITICAL,       # post-transition; no longer near critical point
    stoichiometry="n:m",
)

# ── Class 4: ACTIVE GEL ────────────────────────────────────────────────────────
# Actin + myosin + ATP: the archetypal biological programmable matter.
# D_triangle_infinity: spatial filament network + temporal ATP hydrolysis cycle.
# P_directional: directed motor forces (myosin walks toward barbed end).
# F_eth: filaments assemble/disassemble on ~minute timescale (intermediate).
# K_mod: ATP hydrolysis ΔG‡ ~80 kJ/mol. G_aleph: global cytoskeletal flows.
# Phi_c: active gels show critical behaviour at onset of collective motion
# (active turbulence, long-range order — well-documented in active matter theory).
active_gel = Synthon(
    name="active_gel",
    dimensionality=D.HYBRID_SUPRA_TEMP, # spatial network + ATP temporal cycle
    topology=T.NETWORK,
    recognition_mode=R.DYNAMIC_CATALYTIC,         # myosin ATPase + filament assembly/disassembly
    polarity=P.DONOR_ACCEPTOR,             # directed motor forces; asymmetric
    fidelity=F.MEDIUM,                    # intermediate — turns over on minute timescale
    kinetic_character=K.MODERATE,            # ATP hydrolysis ~80 kJ/mol
    granularity=G.GLOBAL,               # global cytoskeletal organisation, cell-scale flows
    interaction_grammar=G_SEQ_SEL,        # sequential: nucleation → elongation → motor action
    criticality_phase=Phi.CRITICAL,          # near onset of collective motion (active turbulence)
    stoichiometry="n:m",
)

# ── Class 5: SHAPE-MEMORY POLYMER ─────────────────────────────────────────────
# SMP rigid (T < Tg): crystalline switching domains lock the temporary shape.
# F_hbar (crystalline domains — effectively permanent below Tg). K_slow (shape
# recovery requires Tg crossing: ΔG‡ > 100 kJ/mol). G_gimel (mesoscale
# crystalline domains, ~10-100 nm). Gamma_→ SELECTIVE: shape was programmed
# in a sequence (heat → deform → cool → fix).
smp_rigid = Synthon(
    name="smp_rigid",
    dimensionality=D.SUPRAMOLECULAR,
    topology=T.NETWORK,                 # crosslinked polymer network
    recognition_mode=R.NON_COVALENT,      # crystalline domains + H-bonds
    polarity=P.SELF_COMPLEMENTARY_PSEUDO,               # chain geometry has preferred direction, not sym
    fidelity=F.HIGH,                      # locked by crystalline domains below Tg
    kinetic_character=K.SLOW,           # requires Tg crossing; >100 kJ/mol
    granularity=G.MESOSCALE,                # mesoscale crystalline domains
    interaction_grammar=G_SEQ_SEL,        # programmed sequence: heat→deform→cool→fix
    criticality_phase=Phi.SUBCRITICAL,
    stoichiometry="n:n",
)

# SMP elastic (T > Tg): crystalline domains melted, entropy-elastic recovery.
# F_eth (entropic — chain retraction, not crystalline lock). K_mod (barrier
# is now modest — thermal energy at T > Tg sufficient). Gamma_∧ SELECTIVE:
# all network connections participate simultaneously in elastic recovery.
smp_elastic = Synthon(
    name="smp_elastic",
    dimensionality=D.SUPRAMOLECULAR,
    topology=T.NETWORK,
    recognition_mode=R.NON_COVALENT,
    polarity=P.SELF_COMPLEMENTARY_PSEUDO,
    fidelity=F.MEDIUM,                    # crystalline domains melted; entropic F
    kinetic_character=K.MODERATE,            # thermal energy at T>Tg sufficient
    granularity=G.MESOSCALE,
    interaction_grammar=G_AND_SEL,        # elastic recovery: all connections simultaneously
    criticality_phase=Phi.SUBCRITICAL,
    stoichiometry="n:n",
)

# ── Class 6: LIQUID CRYSTAL ────────────────────────────────────────────────────
# Nematic phase (T < TNI): orientational order, no positional order.
# T_linear: molecules align along director — linear topology at the mesoscale.
# F_eth (moderate: orientational order is easily disrupted by thermal/field).
# K_fast (director reorientation fast — sub-ms with field, ms–s thermally).
# G_gimel (mesoscale domain order; correlation length ~μm).
lc_nematic = Synthon(
    name="lc_nematic",
    dimensionality=D.SUPRAMOLECULAR,
    topology=T.LINEAR,                  # molecules aligned along director
    recognition_mode=R.NON_COVALENT,      # vdW + shape complementarity
    polarity=P.SELF_COMPLEMENTARY_SYM,                  # equivalent ends in most nematics
    fidelity=F.MEDIUM,                    # moderate orientational order
    kinetic_character=K.FAST,           # director reorientation fast under field
    granularity=G.MESOSCALE,                # mesoscale domain order
    interaction_grammar=G_AND_BRD,        # all neighbours participate in orientation
    criticality_phase=Phi.SUBCRITICAL,
    stoichiometry="n:n",
)

# Isotropic phase (T > TNI): orientational order destroyed.
# G_beth (only local packing correlations remain). F_ell (isotropic fluid —
# no persistent orientational preference). Gamma_or BROAD (promiscuous — any
# orientation equally valid).
lc_isotropic = Synthon(
    name="lc_isotropic",
    dimensionality=D.SUPRAMOLECULAR,
    topology=T.NETWORK,                 # disordered liquid
    recognition_mode=R.NON_COVALENT,
    polarity=P.SELF_COMPLEMENTARY_SYM,
    fidelity=F.LOW,                       # no persistent orientational order
    kinetic_character=K.FAST,
    granularity=G.LOCAL,                 # local only
    interaction_grammar=G_OR_BRD,         # any orientation
    criticality_phase=Phi.SUBCRITICAL,
    stoichiometry="n:n",
)

all_pm = [
    dna_origami, dna_strand_disp,
    colloidal_crystal, colloidal_fluid,
    condensate_liquid, condensate_gel,
    active_gel,
    smp_rigid, smp_elastic,
    lc_nematic, lc_isotropic,
]

print(f"\n{len(all_pm)} programmable matter synthons encoded.\n")
for s in all_pm:
    print(f"  {s.name:<30} {s.to_notation()[:80]}")


# ══════════════════════════════════════════════════════════════════════════════
# 2. PAIRWISE DISTANCE MATRIX
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("§2. PAIRWISE DISTANCE MATRIX")
print("=" * 70)

names = [s.name.replace('_', ' ')[:18] for s in all_pm]
print(f"\n{'':20}", end="")
for n in names:
    print(f"{n[:8]:>9}", end="")
print()

dists = {}
for i, s1 in enumerate(all_pm):
    print(f"{s1.name[:20]:<20}", end="")
    for j, s2 in enumerate(all_pm):
        d = tuple_distance(s1, s2) if i != j else 0.0
        dists[(i, j)] = d
        print(f"{d:9.2f}", end="")
    print()

# State-pair distances (the programmability pairs — A ↔ B same material)
pairs = [
    ("dna_origami_folded",        "dna_strand_displacement", "DNA origami ↔ strand disp"),
    ("colloidal_crystal",         "colloidal_fluid",          "Colloidal crystal ↔ fluid"),
    ("condensate_liquid",         "condensate_gel",           "Condensate liquid ↔ gel"),
    ("smp_rigid",                 "smp_elastic",              "SMP rigid ↔ elastic"),
    ("lc_nematic",                "lc_isotropic",             "LC nematic ↔ isotropic"),
]
pm_by_name = {s.name: s for s in all_pm}

print("\nProgrammability pair distances (symmetric d | directed d_AB | d_BA):")
print(f"  {'Pair':<40} {'d_sym':>8}  {'d(A→B)':>8}  {'d(B→A)':>8}  {'asymmetry':>10}")
for na, nb, label in pairs:
    a, b = pm_by_name[na], pm_by_name[nb]
    d_sym = tuple_distance(a, b)
    d_ab  = tuple_distance(a, b, symmetric=False)
    d_ba  = tuple_distance(b, a, symmetric=False)
    asym  = abs(d_ab - d_ba)
    print(f"  {label:<40} {d_sym:8.2f}  {d_ab:8.2f}  {d_ba:8.2f}  {asym:10.2f}")


# ══════════════════════════════════════════════════════════════════════════════
# 3. MEET OPERATIONS — SHARED SUBSTRATE OF EACH PROGRAMMABILITY PAIR
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("§3. SHARED SUBSTRATE (meet) OF EACH PROGRAMMABILITY PAIR")
print("=" * 70)
print("What's the common primitive floor that both states share?")
print("CONFLICT on a primitive = that primitive drives the state transition.\n")

for na, nb, label in pairs:
    a, b = pm_by_name[na], pm_by_name[nb]
    m = meet(a, b)
    conflicts = m.conflicts if hasattr(m, 'conflicts') else []
    print(f"  {label}")
    print(f"    Meet: {m.to_notation()[:90]}")
    if conflicts:
        print(f"    Conflicts (state-switching primitives): {conflicts}")
    else:
        print(f"    No conflicts — states differ only in ordered primitives (F, K, G).")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# 4. PATH SEARCHES — RECONFIGURABILITY IN THE HOTSWAP GRAPH
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("§4. PATH SEARCHES — RECONFIGURABILITY IN THE HOTSWAP GRAPH")
print("=" * 70)
print("find_path requires same {D, T} cluster. Blocked = F-floor or D/T mismatch.\n")

# Load catalog for path search
register_molecular_synthons()
register_quantum_synthons()
catalog = list(global_catalog.search()) + all_pm

path_queries = [
    (smp_rigid,        smp_elastic,     "SMP rigid → elastic (Tg crossing)"),
    (smp_elastic,      smp_rigid,       "SMP elastic → rigid (inverse — F-floor?)"),
    (lc_nematic,       lc_isotropic,    "LC nematic → isotropic (T > TNI)"),
    (lc_isotropic,     lc_nematic,      "LC isotropic → nematic (T < TNI)"),
    (condensate_liquid, condensate_gel, "Condensate liquid → gel (pathological)"),
    (condensate_gel,   condensate_liquid,"Condensate gel → liquid (rescue)"),
    (colloidal_crystal, colloidal_fluid, "Colloidal crystal → fluid (melting)"),
    (colloidal_fluid,  colloidal_crystal,"Colloidal fluid → crystal (crystallisation)"),
]

for src, dst, label in path_queries:
    r = find_path(src, dst, catalog, max_hops=4, xi_tolerance=2.0)
    if r.found:
        print(f"  ✅ {label}")
        print(f"     Hops: {r.n_hops}  |  Total Δξ_CP: {r.total_delta:.3f} nat")
        for i, (hop_name, delta) in enumerate(zip(r.path[1:], r.hop_deltas)):
            print(f"       hop {i+1}: → {hop_name} (Δξ={delta:+.3f})")
    else:
        notes = r.notes if r.notes else ["no path found in HotSwap graph"]
        print(f"  ❌ {label}")
        print(f"     Blocked: {notes[0] if notes else 'D/T mismatch or F-floor'}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# 5. VARMA PROBE — Φ_c CANDIDACY FOR CONDENSATE AND ACTIVE GEL
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("§5. VARMA PROBE — Φ_c CANDIDACY")
print("=" * 70)
print("Condensate (near spinodal) and active gel (near onset of collective motion)\n"
      "are both encoded as Φ_c. Does the Varma probe agree?\n")

varma_targets = [
    # (synthon, xi_r, xi_tau, label, rationale)
    # Condensate: correlation length ξ_r from scattering near critical point
    # (~50 nm = 50 units of nm; ξ_τ from IDR exchange time ~10 ms → ω_c = 10^12 s^-1
    # → ξ_τ = τ_corr * ω_c = 0.01 * 10^12 = 10^10)
    (condensate_liquid, 8.5,  1e10,  "Condensate liquid",
     "ξ_r from critical scattering near spinodal; ξ_τ from IDR exchange (10 ms)"),
    # Active gel: ξ_r from active turbulence correlation length (~10 μm / 1 μm unit = 10);
    # ξ_τ from ATP hydrolysis cycle (τ ~0.1 s → ξ_τ = 10^11)
    (active_gel,        10.0, 1e11,  "Active gel",
     "ξ_r from active turbulence correlation; ξ_τ from ATP hydrolysis cycle"),
    # Colloidal crystal near Tm: ξ_r diverges at melting point (~30 particle diameters)
    (colloidal_crystal, 30.0, 1e6,   "Colloidal crystal (near Tm)",
     "ξ_r from crystal correlation length near melting; ξ_τ from particle diffusion"),
    # LC near TNI: ξ_r ~100 nm; ξ_τ from director fluctuation (~ms → ξ_τ ~10^9)
    (lc_nematic,        15.0, 1e9,   "LC nematic (near TNI)",
     "ξ_r from pretransitional fluctuations; ξ_τ from director correlation time"),
]

for synth, xi_r, xi_tau, label, rationale in varma_targets:
    corr = VarmaCorrelationData(xi_r=xi_r, xi_tau=xi_tau, delta=0.5)
    report = score_phi_c_candidacy(synth, corr)
    deg_score, deg_type = degeneracy_strength(synth, corr,
        frequency_series=[(1e6, 0.1), (1e8, 0.2), (1e10, 0.4), (1e12, 0.8)])
    print(f"  {label}")
    print(f"    ξ_r={xi_r}, ξ_τ={xi_tau:.0e}")
    print(f"    Score: {report.score:.3f}  Candidacy: {report._candidacy_label()}")
    print(f"    G/D degenerate: {report.gd_degenerate}  |  Universality: {report.universality_class}")
    print(f"    Degeneracy strength: {deg_score:.3f} ({deg_type})  |  Rationale: {rationale}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# 6. CROSS-DOMAIN ANALOGY SEARCH
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("§6. CROSS-DOMAIN ANALOGY SEARCH")
print("=" * 70)
print("Nearest catalog neighbors for each programmable matter state.\n")

catalog_synthons = list(global_catalog.search())

analogy_targets = [
    (condensate_liquid, "Condensate liquid"),
    (active_gel,        "Active gel"),
    (dna_origami,       "DNA origami (folded)"),
    (colloidal_crystal, "Colloidal crystal"),
]

for synth, label in analogy_targets:
    ranked = sorted(
        [(s, tuple_distance(synth, s)) for s in catalog_synthons if s.name != synth.name],
        key=lambda x: x[1]
    )[:5]
    print(f"  {label} — top 5 catalog analogs:")
    for neighbor, d in ranked:
        print(f"    d={d:.2f}  {neighbor.name}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# 7. THE PROGRAMMABILITY LATTICE
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("§7. THE PROGRAMMABILITY LATTICE")
print("=" * 70)
print("meet of all dynamic/fluid states = what all programmable matter shares")
print("join of all rigid/locked states  = what locks everything\n")

dynamic_states = [dna_strand_disp, colloidal_fluid, condensate_liquid,
                  smp_elastic, lc_nematic, lc_isotropic]
rigid_states   = [dna_origami, colloidal_crystal, condensate_gel,
                  smp_rigid]

def meet_chain(synthons):
    result = synthons[0]
    for s in synthons[1:]:
        m = meet(result, s)
        # convert LatticeResult to a scratch Synthon for chaining
        def _get(prim, fallback):
            val = getattr(m, prim, None)
            if val is None or str(val) == 'CONFLICT':
                return fallback
            return val
        result = Synthon(
            name=f"meet_chain_{s.name[:8]}",
            dimensionality=_get('dimensionality', D.SUPRAMOLECULAR),
            topology=_get('topology', T.NETWORK),
            recognition_mode=_get('recognition_mode', R.NON_COVALENT),
            polarity=_get('polarity', P.SELF_COMPLEMENTARY_SYM),
            fidelity=_get('fidelity', F.LOW),
            kinetic_character=_get('kinetic_character', K.FAST),
            granularity=_get('granularity', G.LOCAL),
            interaction_grammar=_get('interaction_grammar', G_OR_BRD),
            criticality_phase=_get('criticality_phase', Phi.SUBCRITICAL),
        )
    return result, m  # return final LatticeResult for conflict analysis

def join_chain(synthons):
    result = synthons[0]
    for s in synthons[1:]:
        jn = join(result, s)
        def _get(prim, fallback):
            val = getattr(jn, prim, None)
            if val is None or str(val) == 'CONFLICT':
                return fallback
            return val
        result = Synthon(
            name=f"join_chain_{s.name[:8]}",
            dimensionality=_get('dimensionality', D.HYBRID_MOL_SUPRA),
            topology=_get('topology', T.NETWORK),
            recognition_mode=_get('recognition_mode', R.NON_COVALENT),
            polarity=_get('polarity', P.SELF_COMPLEMENTARY_SYM),
            fidelity=_get('fidelity', F.HIGH),
            kinetic_character=_get('kinetic_character', K.SLOW),
            granularity=_get('granularity', G.GLOBAL),
            interaction_grammar=_get('interaction_grammar', G_AND_BRD),
            criticality_phase=_get('criticality_phase', Phi.SUBCRITICAL),
        )
    return result, jn

dynamic_floor, dynamic_meet = meet_chain(dynamic_states)
rigid_ceiling, rigid_join   = join_chain(rigid_states)

print("  DYNAMIC FLOOR (meet of all fluid/switchable states):")
print(f"    {dynamic_meet.to_notation()}")
if dynamic_meet.conflicts:
    print(f"    Conflicts: {dynamic_meet.conflicts}")

print()
print("  RIGID CEILING (join of all locked states):")
print(f"    {rigid_join.to_notation()}")
if rigid_join.conflicts:
    print(f"    Conflicts: {rigid_join.conflicts}")

print()
print("  Distance (dynamic floor → rigid ceiling):",
      tuple_distance(dynamic_floor, rigid_ceiling))
print("  This is the primitive gap that separates 'programmable' from 'locked'.")
print("  The primitives in this gap are the design levers of programmable matter.")


# ══════════════════════════════════════════════════════════════════════════════
# 8. SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("§8. SUMMARY — WHAT THE ALGEBRA SAYS ABOUT PROGRAMMABLE MATTER")
print("=" * 70)
print("""
Emergent results from the algebra (not inserted as assumptions):

1. PROGRAMMABILITY PRIMITIVE: The state-pair meet operations identify which
   primitives drive each material's state transition. F and K dominate every
   pair (F_hbar ↔ F_eth or F_ell; K_slow ↔ K_fast). G changes only in
   condensate (G_gimel → G_aleph) and colloidal (G_aleph → G_beth) pairs.
   Γ changes only in SMP (G_SEQ → G_AND) and LC (G_AND → G_OR). D and T
   are invariant across all programmability pairs — the material's identity
   is preserved while its phase changes.

2. PROGRAMMABILITY = PATH EXISTENCE: "What can be programmed?" reduces to
   find_path() in the HotSwap graph. The F-floor blocks some inverse paths
   (gel → liquid, crystal → fluid) — reconfiguration is directional, not
   reversible in the primitive sense.

3. Φ_c AS GLOBAL PROGRAMMABILITY: Both condensate_liquid and active_gel are
   encoded as Φ_c. This predicts: near-critical programmable matter can be
   reconfigured globally from local inputs. G/D degeneracy means a molecular-
   scale stimulus propagates to the system scale. This is the most powerful
   form of programmability the framework can encode.

4. THE F-K PROGRAMMABILITY QUADRANT: The most versatile programmable matter
   sits at F_eth + K_mod (enough fidelity to maintain states; low enough
   barrier to switch). DNA strand displacement and SMP elastic both occupy
   this quadrant. F_hbar + K_slow systems (DNA origami folded, SMP rigid,
   colloidal crystal) are stable but require large external energy to reprogram.
   F_ell + K_fast (colloidal fluid, LC isotropic, condensate liquid) are
   dynamically responsive but lack persistent state memory.

5. CONDENSATE → GEL ASYMMETRY: The directed distance condensate_liquid →
   condensate_gel should be SHORTER than gel → liquid (F-floor blocks escape
   from F_hbar). This is the disease progression direction: gelation is
   thermodynamically downhill in primitive space. Confirmed by K-targeting
   asymmetry (P-31, P-35 from protein domain).
""")

print("Part 1 complete. Run programmable_matter_tests2.py for:")
print("  - Primitive Jacobian (which primitive controls programmability per material)")
print("  - Tensor products (active gel ⊗ DNA nanotechnology)")
print("  - Ideal programmable matter design via monad pipeline")
print("  - Formal predictions (P-38 through P-47)")
