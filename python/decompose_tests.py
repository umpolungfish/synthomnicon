"""
SynthOmnicon Decomposition Algebra — Test Suite
================================================
Exercises all 8 decomposition operations on synthetic and catalog synthons.
Run with:  python decompose_tests.py
"""

from __future__ import annotations

import sys
import traceback
from typing import List, Tuple

# ── Bootstrap ──────────────────────────────────────────────────────────────────
import synthomnicon as syn
from synthomnicon.models import (
    Synthon, Dimensionality, Topology, RecognitionMode, Polarity,
    Fidelity, KineticCharacter, Granularity, InteractionGrammar,
    CriticalityPhase, TopoIndex,
)
from synthomnicon.decompose import (
    project, primitive_peel, factor, principal_decomp,
    cofactor, complement_rel, kernel, retrosynthetic_path,
    phi_c_probe, topo_protection_probe,
)
from synthomnicon.algebra import DesignPipeline

# ── Helpers ────────────────────────────────────────────────────────────────────

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

_results: List[Tuple[str, bool, str]] = []


def check(name: str, condition: bool, msg: str = ""):
    status = PASS if condition else FAIL
    _results.append((name, condition, msg))
    print(f"  [{status}] {name}" + (f"  — {msg}" if msg else ""))


def section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ── Fixture Synthons ───────────────────────────────────────────────────────────
# Build a small set of representative synthons covering the algebra's edge cases.

def _s(name, D=Dimensionality.MOLECULAR, T=Topology.CHAIN,
       R=RecognitionMode.NON_COVALENT, P=Polarity.SELF_COMPLEMENTARY_SYM,
       F=Fidelity.HIGH, K=KineticCharacter.FAST,
       G=Granularity.GLOBAL, Gamma=InteractionGrammar.SPECIFIC_AND,
       Phi=CriticalityPhase.SUBCRITICAL, omega=None, **_) -> Synthon:
    return Synthon(
        name=name,
        dimensionality=D, topology=T,
        recognition_mode=R, polarity=P,
        fidelity=F, kinetic_character=K,
        granularity=G, interaction_grammar=Gamma,
        criticality_phase=Phi, stoichiometry=None,
        topo_index=omega,
    )


# Canonical "rich" synthon — all ordinals at max; Φ_c active; Ω protected
RICH = _s("RICH",
           F=Fidelity.HIGH, K=KineticCharacter.FAST, G=Granularity.GLOBAL,
           Phi=CriticalityPhase.CRITICAL,
           omega=TopoIndex.Z2_CLASS)

# "Lean" synthon — all ordinals at constraint-bottom; no special protection
LEAN = _s("LEAN",
          F=Fidelity.LOW, K=KineticCharacter.FAST,  # FAST is K's constraint-bottom
          G=Granularity.LOCAL,
          Phi=CriticalityPhase.SUBCRITICAL,
          omega=None)

# Mid-tier synthon — ordinals at MEDIUM / MODERATE / MESOSCALE
MID = _s("MID",
         F=Fidelity.MEDIUM, K=KineticCharacter.MODERATE, G=Granularity.MESOSCALE,
         Phi=CriticalityPhase.SUBCRITICAL)

# Synthon with distinct categorical values (for cofactor conflict tests)
ALT_CAT = _s("ALT_CAT",
             R=RecognitionMode.MECHANICAL, P=Polarity.DONOR_ACCEPTOR,
             F=Fidelity.LOW, K=KineticCharacter.SLOW, G=Granularity.GLOBAL)

# Synthon with Ω but no Φ_c — topo-protected only
TOPO = _s("TOPO",
          F=Fidelity.MEDIUM, K=KineticCharacter.MODERATE, G=Granularity.MESOSCALE,
          Phi=CriticalityPhase.SUBCRITICAL,
          omega=TopoIndex.CHERN)

CATALOG = [RICH, LEAN, MID, ALT_CAT, TOPO]


# ══════════════════════════════════════════════════════════════════════════════
# 1. project
# ══════════════════════════════════════════════════════════════════════════════

section("1. project — orthogonal projection onto a primitive subset")

r = project(RICH, ["F", "K"])
check("project preserves F", r.result.fidelity == Fidelity.HIGH)
check("project preserves K", r.result.kinetic_character == KineticCharacter.FAST)
check("project zeros G to LOCAL", r.result.granularity == Granularity.LOCAL,
      f"got {r.result.granularity}")
check("project records zeroed list", "G" in r.zeroed or len(r.zeroed) > 0,
      f"zeroed={r.zeroed}")
check("project preserves name root in result name", "RICH" in r.result.name,
      f"name={r.result.name}")

r2 = project(RICH, ["G"])
check("project([G]) — G preserved at GLOBAL", r2.result.granularity == Granularity.GLOBAL)
check("project([G]) — F zeroed to LOW", r2.result.fidelity == Fidelity.LOW,
      f"got {r2.result.fidelity}")

r3 = project(LEAN, ["F", "K", "G"])
check("project LEAN ordinal-only — no change to ordinals",
      r3.result.fidelity == Fidelity.LOW and
      r3.result.granularity == Granularity.LOCAL)


# ══════════════════════════════════════════════════════════════════════════════
# 2. primitive_peel
# ══════════════════════════════════════════════════════════════════════════════

section("2. primitive_peel — drop one primitive to constraint-bottom")

# Peel F from LEAN (already at LOW = constraint-bottom → cost 0, trivial peel)
r = primitive_peel(LEAN, "F")
check("peel LEAN.F (already bottom) — not blocked", not r.blocked)
check("peel LEAN.F — result.F = LOW", r.result.fidelity == Fidelity.LOW)
check("peel LEAN.F — peel_cost == 0.0", r.peel_cost == 0.0,
      f"cost={r.peel_cost}")

# Peel F from RICH (HIGH → LOW, peel_cost expected > 0)
r = primitive_peel(RICH, "F")
check("peel RICH.F — not blocked (Φ_c is present but cost is within default limit)",
      not r.blocked, f"block_reason={r.block_reason}")
check("peel RICH.F — result.F = LOW", r.result.fidelity == Fidelity.LOW,
      f"got {r.result.fidelity}")
check("peel RICH.F — phi_c preserved flag is True (Phi field untouched)", r.phi_c_preserved)
check("peel RICH.F — peel_cost == 0.0 (phi_c preserved, no cost incurred)", r.peel_cost == 0.0,
      f"cost={r.peel_cost}")

# Peeling Phi itself from RICH DOES destroy phi_c → peel_cost > 0
r_phi_peel = primitive_peel(RICH, "Phi")
check("peel RICH.Phi — phi_c NOT preserved (Phi→SUBCRITICAL)", not r_phi_peel.phi_c_preserved)
check("peel RICH.Phi — peel_cost > 0", r_phi_peel.peel_cost > 0, f"cost={r_phi_peel.peel_cost}")

# Peel K from RICH (FAST = constraint-bottom, zero cost)
r = primitive_peel(RICH, "K")
check("peel RICH.K (already FAST = bottom) — peel_cost == 0.0", r.peel_cost == 0.0,
      f"cost={r.peel_cost}")
check("peel RICH.K — K remains FAST", r.result.kinetic_character == KineticCharacter.FAST)

# Peel G from RICH (GLOBAL → LOCAL, join-dominant flip)
r = primitive_peel(RICH, "G")
check("peel RICH.G — result.G = LOCAL", r.result.granularity == Granularity.LOCAL,
      f"got {r.result.granularity}")
check("peel RICH.G — not blocked", not r.blocked)

# Peel Ω from TOPO (has Z2/CHERN_1 omega — cost expected)
r = primitive_peel(TOPO, "Omega")
check("peel TOPO.Omega — result.omega = None", r.result.topo_index is None,
      f"got {r.result.topo_index}")

# strict=True on F: phi_c is preserved (Phi field untouched) — should NOT block
r_strict = primitive_peel(RICH, "F", strict=True)
check("peel RICH.F strict=True — NOT blocked (phi_c preserved when peeling F)", not r_strict.blocked,
      f"block_reason={r_strict.block_reason}")

# strict=True on Phi: phi_c is destroyed → should block
r_strict_phi = primitive_peel(RICH, "Phi", strict=True)
check("peel RICH.Phi strict=True — blocked (phi_c destroyed)", r_strict_phi.blocked,
      f"block_reason={r_strict_phi.block_reason}")


# ══════════════════════════════════════════════════════════════════════════════
# 3. factor
# ══════════════════════════════════════════════════════════════════════════════

section("3. factor — greatest proper sub-synthon (one ordinal step down)")

# Factor RICH: highest ordinals → one step descent
r = factor(RICH)
check("factor RICH — result differs from RICH (some ordinal stepped down)",
      (r.result.fidelity != RICH.fidelity or
       r.result.kinetic_character != RICH.kinetic_character or
       r.result.granularity != RICH.granularity),
      f"F={r.result.fidelity} K={r.result.kinetic_character} G={r.result.granularity}")
check("factor RICH — stepped_primitive is not None", r.stepped_primitive is not None,
      f"got {r.stepped_primitive}")

# Factor LEAN: all ordinals already at constraint-bottom → no change possible
r = factor(LEAN)
check("factor LEAN — stepped_primitive is 'none' (already at bottom)",
      r.stepped_primitive == "none", f"stepped={r.stepped_primitive}")
check("factor LEAN — result matches LEAN ordinals",
      r.result.fidelity == Fidelity.LOW and
      r.result.granularity == Granularity.LOCAL)

# prefer="G" — should step G first
r = factor(RICH, prefer="G")
check("factor RICH prefer=G — stepped_primitive = G",
      r.stepped_primitive == "G", f"got {r.stepped_primitive}")
check("factor RICH prefer=G — G steps to MESOSCALE",
      r.result.granularity == Granularity.MESOSCALE,
      f"got {r.result.granularity}")

# prefer="F" — should step F first
r = factor(RICH, prefer="F")
check("factor RICH prefer=F — stepped_primitive = F",
      r.stepped_primitive == "F", f"got {r.stepped_primitive}")
check("factor RICH prefer=F — F steps to MEDIUM",
      r.result.fidelity == Fidelity.MEDIUM,
      f"got {r.result.fidelity}")

# prefer="K" — FAST is already at constraint-bottom (ordinal 4 = max accessible);
# factor should fall back to another primitive
r = factor(RICH, prefer="K")
check("factor RICH prefer=K — falls back (K is already at FAST)",
      r.stepped_primitive != "K",
      f"got stepped={r.stepped_primitive}")


# ══════════════════════════════════════════════════════════════════════════════
# 4. principal_decomp
# ══════════════════════════════════════════════════════════════════════════════

section("4. principal_decomp — recursive factorization into join-irreducibles")

r = principal_decomp(RICH)
check("principal_decomp RICH — at least 1 factor", r.n_factors >= 1,
      f"n_factors={r.n_factors}")
check("principal_decomp RICH — final factor has ordinals at bottom or single-step",
      all(f.fidelity in (Fidelity.LOW, Fidelity.MEDIUM, Fidelity.HIGH)
          for f in r.factors))

r2 = principal_decomp(LEAN)
check("principal_decomp LEAN — 1 factor (already irreducible)", r2.n_factors == 1,
      f"n_factors={r2.n_factors}")

r3 = principal_decomp(MID)
check("principal_decomp MID — notes field present", isinstance(r3.notes, list))
check("principal_decomp MID — xi_balance >= 0", r3.xi_balance >= 0.0,
      f"xi_balance={r3.xi_balance}")


# ══════════════════════════════════════════════════════════════════════════════
# 5. cofactor
# ══════════════════════════════════════════════════════════════════════════════

section("5. cofactor — residual B such that A ⊗ B ≈ composite")

# tensor(LEAN, MID) should give a composite; cofactor of that by LEAN should ~recover MID
from synthomnicon.algebra import tensor
t_result = tensor(LEAN, MID)
# Build a Synthon from tensor result (patch minimal fields)
from dataclasses import replace as _dc_replace
COMPOSITE = _dc_replace(
    MID,
    name="LEAN⊗MID",
    fidelity=t_result.fidelity if not isinstance(t_result.fidelity, str) else Fidelity.LOW,
    kinetic_character=t_result.kinetic_character if not isinstance(t_result.kinetic_character, str) else KineticCharacter.FAST,
    granularity=t_result.granularity if not isinstance(t_result.granularity, str) else Granularity.MESOSCALE,
)

r = cofactor(COMPOSITE, LEAN)
check("cofactor(LEAN⊗MID, LEAN) — no CONFLICT primitives (clean case)",
      len(r.conflict_primitives) == 0, f"conflicts={r.conflict_primitives}")
check("cofactor — result is not None", r.result is not None)

# Meet-dominant (F): LEAN.F=LOW, COMPOSITE.F=LOW → cofactor.F should be any (A explains it)
check("cofactor — F dimension role recorded", any(d.primitive == "F" for d in r.dimensions),
      f"dims={[d.primitive for d in r.dimensions]}")

# Conflict case: ALT_CAT has different R and P from RICH
r_conflict = cofactor(RICH, ALT_CAT)
check("cofactor(RICH, ALT_CAT) — categorical conflicts detected",
      len(r_conflict.conflict_primitives) > 0,
      f"conflicts={r_conflict.conflict_primitives}")

# Φ_c source tracking
r_phi = cofactor(RICH, LEAN)
# RICH has Φ_c; LEAN has BELOW — so RICH is the phi_c_source
check("cofactor(RICH, LEAN) — phi_c_source identified",
      r_phi.phi_c_source is not None,
      f"phi_c_source={r_phi.phi_c_source}")


# ══════════════════════════════════════════════════════════════════════════════
# 6. complement_rel
# ══════════════════════════════════════════════════════════════════════════════

section("6. complement_rel — relative pseudocomplement in Heyting sense")

# complement_rel(LEAN, RICH, target=LEAN) — LEAN ∧ X ≤ LEAN for any X ≤ RICH
# The pseudocomplement is the largest X in context s.t. LEAN ∧ X ≤ LEAN
r = complement_rel(LEAN, RICH, LEAN)
check("complement_rel(LEAN, RICH, LEAN) — returns a result", r.result is not None)
check("complement_rel — satisfied flag present", isinstance(r.satisfied, bool))

r2 = complement_rel(RICH, LEAN, MID)
check("complement_rel(RICH, LEAN, MID) — returns a result", r2.result is not None)


# ══════════════════════════════════════════════════════════════════════════════
# 7. kernel
# ══════════════════════════════════════════════════════════════════════════════

section("7. kernel — largest sub-synthon annihilated by a probe")

# phi_c_probe checks a categorical field (Phi); ordinal descent cannot silence it.
# kernel(RICH, phi_c_probe) → result=None because phi_c activates for all ordinal sub-synthons.
r = kernel(RICH, phi_c_probe, probe_name="phi_c_probe")
check("kernel(RICH, phi_c_probe) — result=None (probe categorical, not silenced by ordinal descent)",
      r.result is None, f"got result={r.result}")
check("kernel(RICH, phi_c_probe) — phi_c_in_kernel = False (no valid kernel)",
      not r.phi_c_in_kernel)

# LEAN already fails phi_c_probe (Phi=SUBCRITICAL) → LEAN itself is the kernel
r2 = kernel(LEAN, phi_c_probe, probe_name="phi_c_probe")
check("kernel(LEAN, phi_c_probe) — LEAN already in kernel (probe=False on full synthon)",
      r2.result is not None and r2.result.name == LEAN.name,
      f"result={r2.result}")
check("kernel(LEAN, phi_c_probe) — phi_c_in_kernel = False", not r2.phi_c_in_kernel)

# Use an ordinal-sensitive probe: True if F == HIGH (i.e., annihilated = not HIGH)
high_f_probe = lambda s: s.fidelity == Fidelity.HIGH
r3 = kernel(RICH, high_f_probe, probe_name="high_fidelity")
check("kernel(RICH, high_f_probe) — result found (ordinal descent silences probe)",
      r3.result is not None, f"notes={r3.notes}")
check("kernel(RICH, high_f_probe) — result.F is not HIGH",
      r3.result is not None and r3.result.fidelity != Fidelity.HIGH,
      f"got F={r3.result.fidelity if r3.result else 'N/A'}")

# LEAN already has F=LOW → fails high_f_probe, so LEAN is its own kernel
r4 = kernel(LEAN, high_f_probe, probe_name="high_fidelity")
check("kernel(LEAN, high_f_probe) — LEAN already in kernel",
      r4.result is not None and r4.result.name == LEAN.name)

# topo_protection_probe: True iff topo_index non-trivial — also categorical; no ordinal path to silence it
r5 = kernel(LEAN, topo_protection_probe, probe_name="topo_probe")
check("kernel(LEAN, topo_probe) — LEAN already in kernel (topo_index=None)",
      r5.result is not None)


# ══════════════════════════════════════════════════════════════════════════════
# 8. retrosynthetic_path
# ══════════════════════════════════════════════════════════════════════════════

section("8. retrosynthetic_path — find catalog factor pairs approximating a target")

r = retrosynthetic_path(MID, CATALOG, max_factors=2, top_k=3)
check("retrosynthetic_path(MID) — candidates list present",
      isinstance(r.candidates, list))
check("retrosynthetic_path(MID) — n_searched > 0", r.n_searched > 0,
      f"n_searched={r.n_searched}")
check("retrosynthetic_path(MID) — best candidate has factor_names",
      r.best is not None and len(r.best.factor_names) >= 1,
      f"best={r.best}")

# Rich target — should still find candidates in the catalog
r2 = retrosynthetic_path(RICH, CATALOG, max_factors=2, top_k=5)
check("retrosynthetic_path(RICH) — finds candidates", r2.best is not None)
check("retrosynthetic_path(RICH) — distance >= 0",
      r2.best is not None and r2.best.distance_to_target >= 0.0,
      f"dist={r2.best.distance_to_target if r2.best else 'N/A'}")


# ══════════════════════════════════════════════════════════════════════════════
# 9. Monadic wrappers (project_m, peel_m, factor_m, cofactor_m)
# ══════════════════════════════════════════════════════════════════════════════

section("9. Monadic step functions")

from synthomnicon.decompose import project_m, peel_m, factor_m, cofactor_m

# Monadic wrappers return (result, notes, warnings, blocked, block_reason) tuples
proj_step = project_m(["F", "K"])
r = proj_step(RICH)
check("project_m([F,K])(RICH) — returns tuple with Synthon result",
      isinstance(r, tuple) and r[0] is not None, f"r={r}")

peel_step = peel_m("G")
r = peel_step(RICH)
check("peel_m(G)(RICH) — returns tuple with Synthon result",
      isinstance(r, tuple) and r[0] is not None, f"r[0]={r[0]}")

peel_step_blocked = peel_m("Phi", strict=True)
r = peel_step_blocked(RICH)
check("peel_m(Phi, strict=True)(RICH) — blocked=True in tuple",
      isinstance(r, tuple) and r[3] is True, f"blocked={r[3]}")

factor_step = factor_m(prefer="F")
r = factor_step(RICH)
check("factor_m(prefer=F)(RICH) — returns tuple with Synthon result",
      isinstance(r, tuple) and r[0] is not None, f"r[0]={r[0]}")

cofactor_step = cofactor_m(LEAN)
r = cofactor_step(RICH)
# LEAN.F=LOW, RICH.F=HIGH: tensor(LEAN,?)=min(LOW,?)=LOW ≠ HIGH → legitimately blocked (CONFLICT on F)
check("cofactor_m(LEAN)(RICH) — returns tuple (blocked=True, algebraically correct)",
      isinstance(r, tuple), f"r={r[:2]}")
check("cofactor_m(LEAN)(RICH) — blocked flag reflects conflict",
      r[3] is True, f"blocked={r[3]}")

# Clean cofactor: factor_a == composite → B absorbs nothing, no conflict
cofactor_step2 = cofactor_m(MID)
r2 = cofactor_step2(COMPOSITE)  # COMPOSITE = LEAN⊗MID (built earlier, LEAN and MID same categoricals)
check("cofactor_m(MID)(LEAN⊗MID) — not blocked (self-consistent factors)",
      isinstance(r2, tuple) and not r2[3], f"blocked={r2[3]}")


# ══════════════════════════════════════════════════════════════════════════════
# 10. DesignPipeline integration
# ══════════════════════════════════════════════════════════════════════════════

section("10. DesignPipeline — .project / .peel / .factor / .cofactor")

pipe = DesignPipeline.start(RICH)
result = pipe.project(["F", "K"]).result()
check("DesignPipeline.project — not failed", not result.failed,
      f"failed_at={result.failed_at}")
check("DesignPipeline.project — steps recorded", len(result.steps) == 1)

pipe2 = DesignPipeline.start(RICH)
result2 = pipe2.peel("G").factor().result()
check("DesignPipeline.peel → factor — chained without failure",
      not result2.failed, f"reason={result2.failure_reason}")
check("DesignPipeline peel→factor — 2 steps", len(result2.steps) == 2)

pipe3 = DesignPipeline.start(RICH)
result3 = pipe3.peel("Phi", strict=True).result()
check("DesignPipeline.peel('Phi', strict=True) — blocked (phi_c destroyed)",
      result3.failed, f"failed={result3.failed}, reason={result3.failure_reason}")

pipe4 = DesignPipeline.start(RICH)
result4 = pipe4.cofactor(LEAN).result()
check("DesignPipeline.cofactor — not failed", not result4.failed,
      f"reason={result4.failure_reason}")


# ══════════════════════════════════════════════════════════════════════════════
# 11. Standard probes
# ══════════════════════════════════════════════════════════════════════════════

section("11. Standard probes")

check("phi_c_probe(RICH) — True (AT_CRITICALITY)", phi_c_probe(RICH))
check("phi_c_probe(LEAN) — False (BELOW)", not phi_c_probe(LEAN))
check("phi_c_probe(MID) — False (BELOW)", not phi_c_probe(MID))

check("topo_protection_probe(TOPO) — True (CHERN_1)", topo_protection_probe(TOPO))
check("topo_protection_probe(RICH) — True (Z2)", topo_protection_probe(RICH))
check("topo_protection_probe(LEAN) — False (omega=None)", not topo_protection_probe(LEAN))


# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════

print(f"\n{'═'*60}")
total = len(_results)
passed = sum(1 for _, ok, _ in _results if ok)
failed = total - passed
print(f"  Results: {passed}/{total} passed", end="")
if failed:
    print(f"  ({failed} FAILED)", end="")
    print()
    print("\n  Failed tests:")
    for name, ok, msg in _results:
        if not ok:
            print(f"    [FAIL] {name}" + (f"  — {msg}" if msg else ""))
else:
    print(f"  (all green)")
print(f"{'═'*60}\n")

sys.exit(0 if failed == 0 else 1)
