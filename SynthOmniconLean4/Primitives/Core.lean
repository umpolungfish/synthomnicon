-- SynthOmnicon/Primitives/Core.lean
-- Track 1, File 1: All 12 primitive types with lattice structure.
-- No algebra, no Synthon struct, no case studies.
-- Every derive and instance here must actually compile.

import Mathlib.Order.Lattice
import Mathlib.Order.BoundedOrder.Basic

namespace SynthOmnicon.Primitives

-- ============================================================
-- CATEGORICAL PRIMITIVES
-- These use meet = ⊓ with identity-required semantics:
-- mismatch in a categorical primitive → the meet is ⊥.
-- We model this as: the type has a LinearOrder, and
-- "categorical" means equality is required for non-⊥ meet.
-- ============================================================

-- 1. Dimensionality (D)
inductive Dimensionality : Type where
  | D_point   -- 0-dimensional, scalar
  | D_line    -- 1-dimensional, vectorial
  | D_wedge   -- 2-dimensional, areal
  | D_cube    -- 3-dimensional, volumetric
  | D_infty   -- ∞-dimensional, iterative/temporal
  | D_holo    -- holographic: boundary encodes bulk; requires D_infty substrate
  deriving DecidableEq, Repr, Ord

-- NOTE on D_holo ordering:
-- Derived Ord gives D_holo > D_infty, which is correct:
-- holographic encoding presupposes infinite-dimensional substrate.
-- D_holo is NOT simply "higher dimensional" — it is a different mode of
-- dimensionality where bulk degrees of freedom are encoded on a boundary.
-- Cross-primitive constraint: D_holo ↔ T_holo (see Axiom C below).

-- 2. Topology (T)
inductive Topology : Type where
  | T_linear      -- open chain
  | T_branched    -- tree/DAG
  | T_network     -- general graph
  | T_bowtie      -- cyclic closure (figure-8 / two loops)
  | T_torus       -- higher genus compact
  | T_holo        -- holographic: non-local boundary-bulk correspondence
  deriving DecidableEq, Repr, Ord

-- NOTE on T_holo ordering:
-- Derived Ord gives T_holo > T_torus, which is correct:
-- holographic topology is maximally non-local.
-- T_holo is the topological structure required for bulk-boundary duality
-- (AdS/CFT, error-correcting codes, Mochizuki IUT).
-- Cross-primitive constraint: T_holo ↔ D_holo (see Axiom C below).

-- 3. Recognition (R)
inductive Recognition : Type where
  | R_exact       -- identity match only
  | R_subset      -- subset recognition
  | R_superset    -- superset recognition
  | R_catalytic   -- state transformation
  | R_allosteric  -- conformational gating
  deriving DecidableEq, Repr, Ord

-- 4. Polarity (P)
inductive Polarity : Type where
  | P_neutral     -- no polarity
  | P_plus        -- positive only
  | P_minus       -- negative only
  | P_pm          -- bipolar (unsigned)
  | P_pm_sym      -- symmetric bipolar
  deriving DecidableEq, Repr, Ord

-- 5. Interaction Grammar (Γ)
-- Categorical: composition rule identity required
inductive Grammar : Type where
  | G_and    -- conjunctive / simultaneous
  | G_or     -- disjunctive / alternative
  | G_seq    -- sequential / ordered
  | G_xor    -- exclusive
  | G_impl   -- implicative / conditional
  deriving DecidableEq, Repr, Ord

-- ============================================================
-- ORDERED PRIMITIVES
-- These use meet = min, join = max over a linear order.
-- ============================================================

-- 6. Fidelity (F)
-- Ordered: higher = more reliable / quantum-protected
inductive Fidelity : Type where
  | F_noise   -- below threshold, lossy
  | F_ell     -- classical search fidelity (ℓ)
  | F_eth     -- HotSwap threshold (η)
  | F_hbar    -- quantum / high-fidelity (ℏ)
  deriving DecidableEq, Repr, Ord

-- 7. Kinetic Character (K)
-- Ordered: higher = more kinetically trapped
inductive KineticChar : Type where
  | K_fast    -- diffusion-limited, untrapped
  | K_mod     -- moderate barrier
  | K_slow    -- slow / thermally activated
  | K_trap    -- kinetically trapped / MBL-adjacent
  | K_MBL     -- many-body localized
  deriving DecidableEq, Repr, Ord

-- 8. Granularity (G)
-- Ordered: ℵ < ℶ < ℷ = increasing coarse-graining
inductive Granularity : Type where
  | G_aleph   -- fine-grained, atomic (ℵ)
  | G_beth    -- mesoscale local (ℶ)
  | G_gimel   -- coarse, collective (ℷ)
  deriving DecidableEq, Repr, Ord

-- 9. Criticality Phase (Φ)
-- Special: Φ_c is absorbing under meet (co-Heyting top of sublattice)
-- This is NOT a standard linear order — see note below.
inductive Criticality : Type where
  | Phi_sub   -- subcritical (stable, ordered)
  | Phi_c     -- critical point (absorbing under meet)
  | Phi_sup   -- supercritical (unstable)
  deriving DecidableEq, Repr, Ord

-- NOTE on Phi_c:
-- The standard Ord derivation gives Phi_sub < Phi_c < Phi_sup.
-- But the algebra spec says meet(Phi_c, Phi_sub) = Phi_c (absorbing),
-- which contradicts min semantics (min would give Phi_sub).
-- This means the meet operation on Criticality is NOT min.
-- We must define a custom MeetSemilattice instance. See Algebra.MeetJoin.

-- 10. Topological Index / Protection (Ω)
-- Ordered: higher = stronger topological protection
inductive Protection : Type where
  | Omega_0     -- no topological protection
  | Omega_Z2    -- Z₂ symmetry protection (requires H ≥ H1)
  | Omega_Z     -- integer winding number (requires H ≥ H2)
  | Omega_C     -- Chern number protection
  | Omega_NA    -- non-Abelian anyonic protection
  deriving DecidableEq, Repr, Ord

-- 11. Stoichiometry (S)
inductive Stoichiometry : Type where
  | one_one   -- 1:1
  | one_n     -- 1:n (one-to-many)
  | n_m       -- n:m (many-to-many)
  | cat       -- catalytic (consumed and regenerated)
  deriving DecidableEq, Repr, Ord

-- 12. Chirality / Temporal Memory (H)
-- Ordered: H0 < H1 < H2 < H_inf (protection strength)
inductive Chirality : Type where
  | H0      -- achiral, no temporal memory
  | H1      -- soft chiral, weak temporal asymmetry
  | H2      -- persistent chiral, strong temporal asymmetry
  | H_inf   -- topological chiral (implies K_trap)
  deriving DecidableEq, Repr, Ord

-- ============================================================
-- LE INSTANCES FOR ORDERED PRIMITIVES
-- Derived from Ord via compare. Required for ≥ notation in axioms.
-- ============================================================

instance instLEProtection : LE Protection :=
  ⟨fun a b => compare a b ≠ .gt⟩

instance instLEChirality : LE Chirality :=
  ⟨fun a b => compare a b ≠ .gt⟩

-- ============================================================
-- CROSS-PRIMITIVE AXIOMS
-- These are stated as Prop axioms (not derivable from the
-- individual primitive lattices — they are external constraints).
-- ============================================================

-- Axiom A: Topological chirality implies kinetic trapping
axiom H_inf_implies_K_trap (k : KineticChar) (h : Chirality) :
  h = Chirality.H_inf → k = KineticChar.K_trap

-- Axiom B: Integer winding number requires persistent chirality
-- (Chirality-Protection Axiom: Ω_Z requires H2, Ω_Z2 requires H1)
axiom Omega_Z_requires_H2 (p : Protection) (h : Chirality) :
  p ≥ Protection.Omega_Z → h ≥ Chirality.H2

-- Axiom C: Holographic dimensionality iff holographic topology
-- D_holo and T_holo are co-required: you cannot have one without the other.
-- Motivation: boundary encoding requires both the right dimensionality
-- (bulk-boundary split) and the right topology (non-local correspondence).
-- This is the structural correlate of AdS/CFT and holographic error correction.
axiom D_holo_iff_T_holo (d : Dimensionality) (t : Topology) :
  d = Dimensionality.D_holo ↔ t = Topology.T_holo

-- Axiom D: Non-Abelian anyonic protection requires holographic substrate
-- Omega_NA (non-Abelian anyons) requires D_holo — anyonic braiding statistics
-- are only topologically protected in a holographic/boundary-encoded system.
axiom Omega_NA_requires_D_holo (p : Protection) (d : Dimensionality) :
  p = Protection.Omega_NA → d = Dimensionality.D_holo

-- ============================================================
-- DECIDABILITY INSTANCES (needed for proof automation)
-- ============================================================

instance : DecidableEq Dimensionality := inferInstance
instance : DecidableEq Topology       := inferInstance
instance : DecidableEq Recognition    := inferInstance
instance : DecidableEq Polarity       := inferInstance
instance : DecidableEq Grammar        := inferInstance
instance : DecidableEq Fidelity       := inferInstance
instance : DecidableEq KineticChar    := inferInstance
instance : DecidableEq Granularity    := inferInstance
instance : DecidableEq Criticality    := inferInstance
instance : DecidableEq Protection     := inferInstance
instance : DecidableEq Stoichiometry  := inferInstance
instance : DecidableEq Chirality      := inferInstance

end SynthOmnicon.Primitives