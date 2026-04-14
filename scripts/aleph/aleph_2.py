"""
ALEPH Language Implementation (Final Fix)
Computes d(source ⊗ ו, target) correctly with proper thresholds.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ----------------------------------------------------------------------
# 12 Primitives (ordered values)
# ----------------------------------------------------------------------

class Dimensionality(Enum):
    D_WEDGE = 0
    D_TRIANGLE = 1
    D_INFINITY = 2
    D_CIRCLE = 3

class Topology(Enum):
    T_NETWORK = 0
    T_IN = 1
    T_BOWTIE = 2
    T_BOX = 3
    T_CIRCLE = 4

class RelationalMode(Enum):
    R_SUPER = 0
    R_CAT = 1
    R_DAGGER = 2
    R_LR = 3

class ParitySymmetry(Enum):
    P_ASYM = 0
    P_PSI = 1
    P_PM = 2
    P_SYM = 3
    P_PM_SYM = 4

class Fidelity(Enum):
    F_ELL = 0
    F_ETH = 1
    F_HBAR = 2

class Kinetic(Enum):
    K_FAST = 0
    K_MOD = 1
    K_SLOW = 2
    K_TRAP = 3

class Scope(Enum):
    G_BETH = 0
    G_GIMEL = 1
    G_ALEPH = 2

class Interaction(Enum):
    GAMMA_AND = 0
    GAMMA_OR = 1
    GAMMA_SEQ = 2
    GAMMA_BROAD = 3

class Criticality(Enum):
    PHI_SUB = 0
    PHI_C = 1
    PHI_C_C = 2
    PHI_EP = 3
    PHI_SUPER = 4

class Chirality(Enum):
    H0 = 0
    H1 = 1
    H2 = 2
    H_INF = 3

class Stoichiometry(Enum):
    S_1_1 = 0
    S_N_N = 1
    S_N_M = 2

class TopoProtection(Enum):
    OMEGA_0 = 0
    OMEGA_Z2 = 1
    OMEGA_Z = 2


@dataclass(frozen=True)
class LetterType:
    D: Dimensionality
    T: Topology
    R: RelationalMode
    P: ParitySymmetry
    F: Fidelity
    K: Kinetic
    G: Scope
    Gamma: Interaction
    Phi: Criticality
    H: Chirality
    S: Stoichiometry
    Omega: TopoProtection

    def distance(self, other: LetterType) -> float:
        diffs = [
            (self.D.value - other.D.value) ** 2,
            (self.T.value - other.T.value) ** 2,
            (self.R.value - other.R.value) ** 2,
            (self.P.value - other.P.value) ** 2,
            (self.F.value - other.F.value) ** 2,
            (self.K.value - other.K.value) ** 2,
            (self.G.value - other.G.value) ** 2,
            (self.Gamma.value - other.Gamma.value) ** 2,
            (self.Phi.value - other.Phi.value) ** 2,
            (self.H.value - other.H.value) ** 2,
            (self.S.value - other.S.value) ** 2,
            (self.Omega.value - other.Omega.value) ** 2,
        ]
        return math.sqrt(sum(diffs))

    def join(self, other: LetterType) -> LetterType:
        return LetterType(
            D=max(self.D, other.D, key=lambda x: x.value),
            T=max(self.T, other.T, key=lambda x: x.value),
            R=max(self.R, other.R, key=lambda x: x.value),
            P=min(self.P, other.P, key=lambda x: x.value),  # bottleneck
            F=min(self.F, other.F, key=lambda x: x.value),  # bottleneck
            K=min(self.K, other.K, key=lambda x: x.value),  # bottleneck
            G=max(self.G, other.G, key=lambda x: x.value),
            Gamma=max(self.Gamma, other.Gamma, key=lambda x: x.value),
            Phi=max(self.Phi, other.Phi, key=lambda x: x.value),
            H=max(self.H, other.H, key=lambda x: x.value),
            S=max(self.S, other.S, key=lambda x: x.value),
            Omega=max(self.Omega, other.Omega, key=lambda x: x.value),
        )

    def tensor(self, other: LetterType) -> LetterType:
        return self.join(other)

    def ouroboricity_tier(self) -> str:
        if self.Phi == Criticality.PHI_C and self.P == ParitySymmetry.P_PM_SYM:
            return "O_inf"
        if (self.Phi == Criticality.PHI_C and self.Omega != TopoProtection.OMEGA_0 and
            self.D in (Dimensionality.D_WEDGE, Dimensionality.D_CIRCLE, Dimensionality.D_TRIANGLE)):
            return "O_2"
        if self.Phi == Criticality.PHI_C and self.Omega != TopoProtection.OMEGA_0 and self.D == Dimensionality.D_INFINITY:
            return "O_2"
        if self.Phi == Criticality.PHI_C and self.Omega == TopoProtection.OMEGA_0:
            return "O_1"
        return "O_0"

    def __repr__(self) -> str:
        tiers = {"O_0": "⚫O₀", "O_1": "🟢O₁", "O_2": "🔵O₂", "O_inf": "🟣O_∞"}
        return f"<LetterType {tiers[self.ouroboricity_tier()]}>"


# ----------------------------------------------------------------------
# Canonical encodings
# ----------------------------------------------------------------------

_LETTERS: Dict[str, LetterType] = {}

def _init_letters():
    _LETTERS["aleph"] = LetterType(
        D=Dimensionality.D_WEDGE, T=Topology.T_BOX, R=RelationalMode.R_SUPER,
        P=ParitySymmetry.P_SYM, F=Fidelity.F_HBAR, K=Kinetic.K_SLOW,
        G=Scope.G_ALEPH, Gamma=Interaction.GAMMA_AND, Phi=Criticality.PHI_C,
        H=Chirality.H_INF, S=Stoichiometry.S_1_1, Omega=TopoProtection.OMEGA_Z
    )
    _LETTERS["bet"] = LetterType(
        D=Dimensionality.D_TRIANGLE, T=Topology.T_BOX, R=RelationalMode.R_CAT,
        P=ParitySymmetry.P_PM, F=Fidelity.F_ETH, K=Kinetic.K_MOD,
        G=Scope.G_GIMEL, Gamma=Interaction.GAMMA_AND, Phi=Criticality.PHI_SUB,
        H=Chirality.H1, S=Stoichiometry.S_N_N, Omega=TopoProtection.OMEGA_Z2
    )
    _LETTERS["gimel"] = LetterType(
        D=Dimensionality.D_WEDGE, T=Topology.T_BOWTIE, R=RelationalMode.R_LR,
        P=ParitySymmetry.P_ASYM, F=Fidelity.F_ELL, K=Kinetic.K_FAST,
        G=Scope.G_BETH, Gamma=Interaction.GAMMA_SEQ, Phi=Criticality.PHI_SUB,
        H=Chirality.H0, S=Stoichiometry.S_1_1, Omega=TopoProtection.OMEGA_0
    )
    _LETTERS["dalet"] = LetterType(
        D=Dimensionality.D_WEDGE, T=Topology.T_IN, R=RelationalMode.R_LR,
        P=ParitySymmetry.P_ASYM, F=Fidelity.F_ELL, K=Kinetic.K_FAST,
        G=Scope.G_BETH, Gamma=Interaction.GAMMA_SEQ, Phi=Criticality.PHI_SUB,
        H=Chirality.H0, S=Stoichiometry.S_1_1, Omega=TopoProtection.OMEGA_0
    )
    _LETTERS["hei"] = LetterType(
        D=Dimensionality.D_CIRCLE, T=Topology.T_CIRCLE, R=RelationalMode.R_DAGGER,
        P=ParitySymmetry.P_SYM, F=Fidelity.F_HBAR, K=Kinetic.K_SLOW,
        G=Scope.G_ALEPH, Gamma=Interaction.GAMMA_BROAD, Phi=Criticality.PHI_C,
        H=Chirality.H_INF, S=Stoichiometry.S_N_M, Omega=TopoProtection.OMEGA_Z
    )
    _LETTERS["vav"] = LetterType(
        D=Dimensionality.D_WEDGE, T=Topology.T_NETWORK, R=RelationalMode.R_LR,
        P=ParitySymmetry.P_PM_SYM, F=Fidelity.F_ELL, K=Kinetic.K_SLOW,
        G=Scope.G_GIMEL, Gamma=Interaction.GAMMA_AND, Phi=Criticality.PHI_C,
        H=Chirality.H1, S=Stoichiometry.S_1_1, Omega=TopoProtection.OMEGA_0
    )
    _LETTERS["zayin"] = LetterType(
        D=Dimensionality.D_WEDGE, T=Topology.T_NETWORK, R=RelationalMode.R_LR,
        P=ParitySymmetry.P_ASYM, F=Fidelity.F_ELL, K=Kinetic.K_FAST,
        G=Scope.G_BETH, Gamma=Interaction.GAMMA_SEQ, Phi=Criticality.PHI_SUB,
        H=Chirality.H0, S=Stoichiometry.S_1_1, Omega=TopoProtection.OMEGA_0
    )
    _LETTERS["chet"] = LetterType(
        D=Dimensionality.D_TRIANGLE, T=Topology.T_BOX, R=RelationalMode.R_CAT,
        P=ParitySymmetry.P_PM, F=Fidelity.F_ETH, K=Kinetic.K_MOD,
        G=Scope.G_GIMEL, Gamma=Interaction.GAMMA_AND, Phi=Criticality.PHI_SUB,
        H=Chirality.H1, S=Stoichiometry.S_N_N, Omega=TopoProtection.OMEGA_Z2
    )
    _LETTERS["tet"] = LetterType(
        D=Dimensionality.D_TRIANGLE, T=Topology.T_IN, R=RelationalMode.R_LR,
        P=ParitySymmetry.P_ASYM, F=Fidelity.F_ELL, K=Kinetic.K_SLOW,
        G=Scope.G_BETH, Gamma=Interaction.GAMMA_SEQ, Phi=Criticality.PHI_SUB,
        H=Chirality.H1, S=Stoichiometry.S_1_1, Omega=TopoProtection.OMEGA_0
    )
    _LETTERS["yod"] = LetterType(
        D=Dimensionality.D_WEDGE, T=Topology.T_BOX, R=RelationalMode.R_SUPER,
        P=ParitySymmetry.P_SYM, F=Fidelity.F_HBAR, K=Kinetic.K_SLOW,
        G=Scope.G_ALEPH, Gamma=Interaction.GAMMA_AND, Phi=Criticality.PHI_SUB,
        H=Chirality.H1, S=Stoichiometry.S_1_1, Omega=TopoProtection.OMEGA_0
    )
    _LETTERS["kaf"] = LetterType(
        D=Dimensionality.D_TRIANGLE, T=Topology.T_BOX, R=RelationalMode.R_CAT,
        P=ParitySymmetry.P_PM, F=Fidelity.F_ETH, K=Kinetic.K_MOD,
        G=Scope.G_GIMEL, Gamma=Interaction.GAMMA_AND, Phi=Criticality.PHI_SUB,
        H=Chirality.H1, S=Stoichiometry.S_N_N, Omega=TopoProtection.OMEGA_Z2
    )
    _LETTERS["lamed"] = LetterType(
        D=Dimensionality.D_INFINITY, T=Topology.T_NETWORK, R=RelationalMode.R_LR,
        P=ParitySymmetry.P_ASYM, F=Fidelity.F_ELL, K=Kinetic.K_MOD,
        G=Scope.G_BETH, Gamma=Interaction.GAMMA_SEQ, Phi=Criticality.PHI_C,
        H=Chirality.H2, S=Stoichiometry.S_N_M, Omega=TopoProtection.OMEGA_0
    )
    _LETTERS["mem"] = LetterType(
        D=Dimensionality.D_TRIANGLE, T=Topology.T_IN, R=RelationalMode.R_DAGGER,
        P=ParitySymmetry.P_PM_SYM, F=Fidelity.F_HBAR, K=Kinetic.K_SLOW,
        G=Scope.G_ALEPH, Gamma=Interaction.GAMMA_BROAD, Phi=Criticality.PHI_C,
        H=Chirality.H2, S=Stoichiometry.S_N_N, Omega=TopoProtection.OMEGA_Z
    )
    _LETTERS["nun"] = LetterType(
        D=Dimensionality.D_WEDGE, T=Topology.T_NETWORK, R=RelationalMode.R_LR,
        P=ParitySymmetry.P_ASYM, F=Fidelity.F_ELL, K=Kinetic.K_FAST,
        G=Scope.G_BETH, Gamma=Interaction.GAMMA_SEQ, Phi=Criticality.PHI_SUB,
        H=Chirality.H0, S=Stoichiometry.S_1_1, Omega=TopoProtection.OMEGA_0
    )
    _LETTERS["samech"] = LetterType(
        D=Dimensionality.D_TRIANGLE, T=Topology.T_BOX, R=RelationalMode.R_CAT,
        P=ParitySymmetry.P_SYM, F=Fidelity.F_ETH, K=Kinetic.K_MOD,
        G=Scope.G_GIMEL, Gamma=Interaction.GAMMA_AND, Phi=Criticality.PHI_SUB,
        H=Chirality.H1, S=Stoichiometry.S_N_N, Omega=TopoProtection.OMEGA_Z2
    )
    _LETTERS["ayin"] = LetterType(
        D=Dimensionality.D_CIRCLE, T=Topology.T_CIRCLE, R=RelationalMode.R_DAGGER,
        P=ParitySymmetry.P_PM, F=Fidelity.F_HBAR, K=Kinetic.K_SLOW,
        G=Scope.G_ALEPH, Gamma=Interaction.GAMMA_BROAD, Phi=Criticality.PHI_C,
        H=Chirality.H2, S=Stoichiometry.S_N_M, Omega=TopoProtection.OMEGA_Z
    )
    _LETTERS["pei"] = LetterType(
        D=Dimensionality.D_WEDGE, T=Topology.T_NETWORK, R=RelationalMode.R_LR,
        P=ParitySymmetry.P_ASYM, F=Fidelity.F_ELL, K=Kinetic.K_FAST,
        G=Scope.G_BETH, Gamma=Interaction.GAMMA_BROAD, Phi=Criticality.PHI_SUB,
        H=Chirality.H1, S=Stoichiometry.S_N_M, Omega=TopoProtection.OMEGA_0
    )
    _LETTERS["tzadi"] = LetterType(
        D=Dimensionality.D_WEDGE, T=Topology.T_IN, R=RelationalMode.R_LR,
        P=ParitySymmetry.P_ASYM, F=Fidelity.F_ELL, K=Kinetic.K_FAST,
        G=Scope.G_BETH, Gamma=Interaction.GAMMA_SEQ, Phi=Criticality.PHI_SUB,
        H=Chirality.H0, S=Stoichiometry.S_1_1, Omega=TopoProtection.OMEGA_0
    )
    _LETTERS["kuf"] = LetterType(
        D=Dimensionality.D_TRIANGLE, T=Topology.T_BOX, R=RelationalMode.R_CAT,
        P=ParitySymmetry.P_SYM, F=Fidelity.F_ETH, K=Kinetic.K_SLOW,
        G=Scope.G_GIMEL, Gamma=Interaction.GAMMA_AND, Phi=Criticality.PHI_C,
        H=Chirality.H2, S=Stoichiometry.S_N_N, Omega=TopoProtection.OMEGA_Z2
    )
    _LETTERS["resh"] = LetterType(
        D=Dimensionality.D_WEDGE, T=Topology.T_BOX, R=RelationalMode.R_CAT,
        P=ParitySymmetry.P_ASYM, F=Fidelity.F_ELL, K=Kinetic.K_MOD,
        G=Scope.G_BETH, Gamma=Interaction.GAMMA_AND, Phi=Criticality.PHI_SUB,
        H=Chirality.H1, S=Stoichiometry.S_1_1, Omega=TopoProtection.OMEGA_0
    )
    _LETTERS["shin"] = LetterType(
        D=Dimensionality.D_TRIANGLE, T=Topology.T_BOWTIE, R=RelationalMode.R_DAGGER,
        P=ParitySymmetry.P_PM_SYM, F=Fidelity.F_HBAR, K=Kinetic.K_SLOW,
        G=Scope.G_ALEPH, Gamma=Interaction.GAMMA_BROAD, Phi=Criticality.PHI_C,
        H=Chirality.H_INF, S=Stoichiometry.S_N_N, Omega=TopoProtection.OMEGA_Z
    )
    _LETTERS["tav"] = LetterType(
        D=Dimensionality.D_TRIANGLE, T=Topology.T_BOX, R=RelationalMode.R_CAT,
        P=ParitySymmetry.P_SYM, F=Fidelity.F_ETH, K=Kinetic.K_SLOW,
        G=Scope.G_GIMEL, Gamma=Interaction.GAMMA_AND, Phi=Criticality.PHI_C,
        H=Chirality.H_INF, S=Stoichiometry.S_N_N, Omega=TopoProtection.OMEGA_Z
    )

_init_letters()


# ----------------------------------------------------------------------
# Vav‑cast with correct distance check
# ----------------------------------------------------------------------

def vav_cast(source: LetterType, target: LetterType, proof_term: Any) -> bool:
    """Validate Vav‑cast using d(source ⊗ ו, target)."""
    if proof_term is None:
        return False
    
    vav_type = _LETTERS["vav"]
    source_with_vav = source.tensor(vav_type)
    distance = source_with_vav.distance(target)
    
    # Determine threshold based on target's Omega (since cast result has target's protection)
    min_omega = target.Omega
    if min_omega == TopoProtection.OMEGA_Z:
        threshold = 4.0
    elif min_omega == TopoProtection.OMEGA_Z2:
        threshold = 3.0
    else:  # OMEGA_0
        threshold = 1.5
    
    # Debug output
    print(f"  Vav‑cast: {source.ouroboricity_tier()} ⊗ ו → {target.ouroboricity_tier()}, distance={distance:.3f}, threshold={threshold}")
    
    if distance >= threshold:
        return False
    
    # Cannot gain Frobenius parity via cast
    if source_with_vav.P != target.P and target.P == ParitySymmetry.P_PM_SYM:
        return False
    
    return True


# ----------------------------------------------------------------------
# Palace definitions
# ----------------------------------------------------------------------

class Palace(Enum):
    EARTHLY = 1
    BARRIER = 2
    ANGELIC = 3
    MIDPOINT = 4
    FIRE_LIGHTNING = 5
    PURE_LIGHT = 6
    THRONE = 7

def can_cross_barrier(from_palace: Palace, to_palace: Palace, typ: LetterType) -> bool:
    if from_palace == to_palace:
        return True
    # O_0 -> O_1 requires phi_c_probe
    if from_palace.value <= Palace.BARRIER.value and to_palace == Palace.ANGELIC:
        return typ.Phi == Criticality.PHI_C
    # O_1 -> O_2 requires topo_protection_probe
    if from_palace == Palace.ANGELIC and to_palace.value >= Palace.MIDPOINT.value:
        return typ.Omega != TopoProtection.OMEGA_0
    # O_2 -> O_inf requires frobenius_probe
    if from_palace.value >= Palace.MIDPOINT.value and to_palace == Palace.THRONE:
        return typ.P == ParitySymmetry.P_PM_SYM
    return False


# ----------------------------------------------------------------------
# ALEPH Interpreter
# ----------------------------------------------------------------------

class ALEPHValue:
    def __init__(self, typ: LetterType, data: Any = None):
        self.typ = typ
        self.data = data
    def __repr__(self):
        return f"<{self.typ} data={self.data!r}>"

class ALEPHEnvironment:
    def __init__(self, parent: Optional['ALEPHEnvironment'] = None):
        self.bindings = {}
        self.parent = parent
    def get(self, name: str) -> Optional[ALEPHValue]:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        return None
    def set(self, name: str, value: ALEPHValue):
        self.bindings[name] = value

class ALEPHInterpreter:
    def __init__(self):
        self.globals = ALEPHEnvironment()
        self.current_palace = Palace.EARTHLY
        self._load_stdlib()
        self.verbose = True
    
    def _load_stdlib(self):
        for name, typ in _LETTERS.items():
            self.globals.set(name, ALEPHValue(typ, data=name))
    
    def evaluate(self, expr: Any, env: Optional[ALEPHEnvironment] = None) -> ALEPHValue:
        if env is None:
            env = self.globals
        if isinstance(expr, str):
            val = env.get(expr)
            if val is None:
                raise NameError(f"Unknown: {expr}")
            return val
        if isinstance(expr, tuple):
            op = expr[0]
            if op == 'tensor':
                left = self.evaluate(expr[1], env)
                right = self.evaluate(expr[2], env)
                result_type = left.typ.tensor(right.typ)
                return ALEPHValue(result_type, data=(left.data, right.data))
            elif op == 'vav_cast':
                source_val = self.evaluate(expr[1], env)
                target_name = expr[2]
                proof = expr[3] if len(expr) > 3 else None
                target_typ = _LETTERS.get(target_name)
                if target_typ is None:
                    raise TypeError(f"Unknown target type: {target_name}")
                if vav_cast(source_val.typ, target_typ, proof):
                    return ALEPHValue(target_typ, data=source_val.data)
                else:
                    raise TypeError(f"Vav‑cast from {source_val.typ} to {target_typ} failed")
            elif op == 'palace':
                palace_num = expr[1]
                new_palace = Palace(palace_num)
                old_palace = self.current_palace
                if self.verbose:
                    print(f"  Entering palace {new_palace.name} from {old_palace.name}")
                self.current_palace = new_palace
                try:
                    result = self.evaluate(expr[2], env)
                finally:
                    self.current_palace = old_palace
                if not can_cross_barrier(old_palace, new_palace, result.typ):
                    raise RuntimeError(f"Barrier crossing {old_palace}→{new_palace} not allowed for {result.typ}")
                return result
            else:
                raise NotImplementedError(f"Unknown op: {op}")
        raise NotImplementedError(f"Cannot eval: {expr}")
    
    def run_example(self, program: List[Tuple], env: Optional[ALEPHEnvironment] = None) -> List[ALEPHValue]:
        results = []
        for stmt in program:
            if stmt[0] == 'def':
                name = stmt[1]
                value = self.evaluate(stmt[2], env)
                (env or self.globals).set(name, value)
                results.append(value)
            else:
                results.append(self.evaluate(stmt, env))
        return results


# ----------------------------------------------------------------------
# Example Programs
# ----------------------------------------------------------------------

def example1_safe_computation():
    interp = ALEPHInterpreter()
    interp.verbose = False
    result = interp.evaluate(('tensor', 'bet', 'gimel'))
    print("Example 1: bet ⊗ gimel =", result)
    assert result.typ.ouroboricity_tier() == "O_0"

def example2_self_reference():
    interp = ALEPHInterpreter()
    interp.verbose = False
    result = interp.evaluate(('tensor', 'aleph', 'aleph'))
    print("Example 2: aleph ⊗ aleph =", result)
    assert result.typ.ouroboricity_tier() == "O_2"

def example3_vav_cast():
    interp = ALEPHInterpreter()
    interp.verbose = False
    interp.globals.set("proof", ALEPHValue(interp.globals.get("vav").typ, data="vav_proof"))
    cast_expr = ('vav_cast', 'aleph', 'tav', 'proof')
    result = interp.evaluate(cast_expr)
    print("Example 3: vav_cast[aleph, tav] succeeded:", result)
    assert result.typ.ouroboricity_tier() == "O_2"

def example4_palace_ascent():
    interp = ALEPHInterpreter()
    interp.verbose = True
    interp.globals.set("phi_probe", ALEPHValue(interp.globals.get("vav").typ, data="phi_probe"))
    interp.globals.set("topo_probe", ALEPHValue(interp.globals.get("vav").typ, data="topo_probe"))
    program = [
        ('def', 'earthly', ('palace', 1, 'bet')),
        ('def', 'angelic', ('palace', 3, ('vav_cast', 'bet', 'lamed', 'phi_probe'))),
        ('def', 'fire_lightning', ('palace', 5, ('vav_cast', 'lamed', 'aleph', 'topo_probe'))),
        ('def', 'throne', ('palace', 7, 'mem')),
        ('throne',)
    ]
    results = interp.run_example(program)
    final = results[-1]
    print("Example 4: Full ascent result =", final)
    assert final.typ.ouroboricity_tier() == "O_inf"

def example5_join_meet():
    aleph = _LETTERS["aleph"]
    bet = _LETTERS["bet"]
    join_typ = aleph.join(bet)
    meet_typ = aleph.meet(bet)
    print("Example 5: aleph ∨ bet =", join_typ)
    print("         aleph ∧ bet =", meet_typ)
    assert join_typ.ouroboricity_tier() == "O_2"
    assert meet_typ.ouroboricity_tier() == "O_0"

def example6_frobenius_composition():
    interp = ALEPHInterpreter()
    interp.verbose = False
    mem_shin = interp.evaluate(('tensor', 'mem', 'shin'))
    mem_aleph = interp.evaluate(('tensor', 'mem', 'aleph'))
    print("Example 6: mem ⊗ shin =", mem_shin, "tier:", mem_shin.typ.ouroboricity_tier())
    print("         mem ⊗ aleph =", mem_aleph, "tier:", mem_aleph.typ.ouroboricity_tier())
    assert mem_shin.typ.ouroboricity_tier() == "O_inf"
    assert mem_aleph.typ.ouroboricity_tier() == "O_2"


if __name__ == "__main__":
    print("=== ALEPH Language Implementation (Final) ===\n")
    example1_safe_computation()
    example2_self_reference()
    example3_vav_cast()
    example4_palace_ascent()
    example5_join_meet()
    example6_frobenius_composition()
    print("\nAll examples completed successfully.")