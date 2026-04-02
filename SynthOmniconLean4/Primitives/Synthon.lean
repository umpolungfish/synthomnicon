-- SynthOmnicon/Primitives/Synthon.lean
-- Track 1, File 2: Synthon struct, primitive distance, and field-theoretic instances.
-- Proves P-70 (higgs = axion = inflaton) by rfl, and SM/QG barrier by decide.

import SynthOmnicon.Primitives.Core

namespace SynthOmnicon.Primitives

open Dimensionality Topology Recognition Polarity Grammar
     Fidelity KineticChar Granularity Criticality Protection
     Stoichiometry Chirality

-- ============================================================
-- SYNTHON STRUCT
-- A Synthon is a 12-tuple over the primitive types.
-- Note: 'rec' is a reserved word in Lean 4; we use 'recog'.
-- @[ext] generates Synthon.ext and Synthon.ext_iff.
-- ============================================================

@[ext]
structure Synthon : Type where
  dim   : Dimensionality
  top   : Topology
  recog : Recognition      -- 'rec' is reserved; using 'recog'
  pol   : Polarity
  gram  : Grammar
  fid   : Fidelity
  kin   : KineticChar
  gran  : Granularity
  crit  : Criticality
  prot  : Protection
  stoi  : Stoichiometry
  chir  : Chirality
  deriving DecidableEq, Repr

-- ============================================================
-- PRIMITIVE DISTANCE (HAMMING)
-- Count of component mismatches. Zero iff tuples are identical.
-- Computable: all fields have DecidableEq.
-- ============================================================

def primitiveMismatches (a b : Synthon) : Nat :=
  (if a.dim   = b.dim   then 0 else 1) +
  (if a.top   = b.top   then 0 else 1) +
  (if a.recog = b.recog then 0 else 1) +
  (if a.pol   = b.pol   then 0 else 1) +
  (if a.gram  = b.gram  then 0 else 1) +
  (if a.fid   = b.fid   then 0 else 1) +
  (if a.kin   = b.kin   then 0 else 1) +
  (if a.gran  = b.gran  then 0 else 1) +
  (if a.crit  = b.crit  then 0 else 1) +
  (if a.prot  = b.prot  then 0 else 1) +
  (if a.stoi  = b.stoi  then 0 else 1) +
  (if a.chir  = b.chir  then 0 else 1)

theorem primitiveMismatches_self (a : Synthon) : primitiveMismatches a a = 0 := by
  simp [primitiveMismatches]

theorem primitiveMismatches_symm (a b : Synthon) :
    primitiveMismatches a b = primitiveMismatches b a := by
  simp only [primitiveMismatches, eq_comm]

-- Each if-then-else term is at most 1.
private lemma ite_mismatch_le_one (p : Prop) [Decidable p] :
    (if p then 0 else 1) ≤ 1 := by split_ifs <;> omega

theorem primitiveMismatches_le_12 (a b : Synthon) :
    primitiveMismatches a b ≤ 12 := by
  unfold primitiveMismatches
  have h1  := ite_mismatch_le_one (a.dim   = b.dim)
  have h2  := ite_mismatch_le_one (a.top   = b.top)
  have h3  := ite_mismatch_le_one (a.recog = b.recog)
  have h4  := ite_mismatch_le_one (a.pol   = b.pol)
  have h5  := ite_mismatch_le_one (a.gram  = b.gram)
  have h6  := ite_mismatch_le_one (a.fid   = b.fid)
  have h7  := ite_mismatch_le_one (a.kin   = b.kin)
  have h8  := ite_mismatch_le_one (a.gran  = b.gran)
  have h9  := ite_mismatch_le_one (a.crit  = b.crit)
  have h10 := ite_mismatch_le_one (a.prot  = b.prot)
  have h11 := ite_mismatch_le_one (a.stoi  = b.stoi)
  have h12 := ite_mismatch_le_one (a.chir  = b.chir)
  omega

theorem primitiveMismatches_zero_iff (a b : Synthon) :
    primitiveMismatches a b = 0 ↔ a = b := by
  constructor
  · intro h
    unfold primitiveMismatches at h
    ext
    all_goals {
      by_contra hne
      have hterm : (if _ = _ then 0 else 1) = 1 := if_neg hne
      simp only [hterm] at h
      omega
    }
  · rintro rfl; exact primitiveMismatches_self a

-- ============================================================
-- FIELD-THEORETIC INSTANCES
-- ============================================================

-- ── Scalar K_slow template ──────────────────────────────────
-- Common structure for Higgs, axion, inflaton:
-- spin-0 field, double-well potential topology, catalytic mass generation,
-- symmetric potential (φ → -φ), simultaneous universal coupling,
-- quantum coherent, K_slow (slow-roll / SSB relaxation — THE defining feature),
-- mesoscale description level, critical point (SSB is a phase transition),
-- no topological protection, one-to-many coupling, soft temporal asymmetry.
def scalarField_Kslow : Synthon := {
  dim   := D_point,
  top   := T_bowtie,
  recog := R_catalytic,
  pol   := P_pm_sym,
  gram  := G_and,
  fid   := F_hbar,
  kin   := K_slow,
  gran  := G_beth,
  crit  := Phi_c,
  prot  := Omega_0,
  stoi  := one_n,
  chir  := H1
}

-- ── P-70: Three-scale K_slow identity ──────────────────────
-- Higgs (electroweak), axion (QCD), and inflaton (cosmic) all encode
-- the SAME primitive 12-tuple. Their energy scale differences are NOT
-- a primitive distinction — they reflect tier-crossing cost (TierCrossing.lean),
-- not a change in structural identity.
def higgs    : Synthon := scalarField_Kslow
def axion    : Synthon := scalarField_Kslow
def inflaton : Synthon := scalarField_Kslow

-- ── P-70 Theorems (provable by rfl) ────────────────────────

/-- P-70a: Higgs and axion are structurally identical as primitive 12-tuples. -/
theorem P70a_higgs_axion_identity : higgs = axion := rfl

/-- P-70b: Axion and inflaton are structurally identical. -/
theorem P70b_axion_inflaton_identity : axion = inflaton := rfl

/-- P-70 (full): Three-scale K_slow symmetry. -/
theorem P70_three_scale_Kslow_symmetry :
    higgs = axion ∧ axion = inflaton ∧ higgs = inflaton :=
  ⟨rfl, rfl, rfl⟩

-- ── Standard Model ──────────────────────────────────────────
def standard_model : Synthon := {
  dim   := D_cube,
  top   := T_network,
  recog := R_allosteric,
  pol   := P_pm,
  gram  := G_and,
  fid   := F_eth,
  kin   := K_mod,
  gran  := G_aleph,
  crit  := Phi_c,
  prot  := Omega_Z,
  stoi  := n_m,
  chir  := H2
}

-- ── Quantum Gravity ─────────────────────────────────────────
-- D_holo and T_holo are co-required (Axiom C ✓).
-- Omega_NA requires D_holo (Axiom D ✓).
-- H_inf implies K_trap (Axiom A ✓).
def quantum_gravity : Synthon := {
  dim   := D_holo,
  top   := T_holo,
  recog := R_exact,
  pol   := P_neutral,
  gram  := G_impl,
  fid   := F_hbar,
  kin   := K_trap,
  gran  := G_aleph,
  crit  := Phi_c,
  prot  := Omega_NA,
  stoi  := n_m,
  chir  := H_inf
}

-- ── General Relativity ──────────────────────────────────────
def general_relativity : Synthon := {
  dim   := D_cube,
  top   := T_network,
  recog := R_catalytic,
  pol   := P_neutral,
  gram  := G_and,
  fid   := F_hbar,
  kin   := K_slow,
  gran  := G_gimel,
  crit  := Phi_sub,
  prot  := Omega_0,
  stoi  := one_n,
  chir  := H1
}

-- ── Asymptotic Safety ───────────────────────────────────────
-- Same spacetime structure as GR; differs in K (moderate at UV fixed point),
-- G (fine-grained: Planck scale), and Φ (critical: UV fixed point IS a QCP).
def asymptotic_safety : Synthon := {
  dim   := D_cube,
  top   := T_network,
  recog := R_catalytic,
  pol   := P_neutral,
  gram  := G_and,
  fid   := F_hbar,
  kin   := K_mod,
  gran  := G_aleph,
  crit  := Phi_c,
  prot  := Omega_0,
  stoi  := one_n,
  chir  := H1
}

-- ============================================================
-- STRUCTURAL THEOREMS
-- ============================================================

/-- The exact SM/QG primitive distance is 9 (mismatches on D, T, R, P, Γ, F, K, Ω, H). -/
theorem sm_qg_distance_exact :
    primitiveMismatches standard_model quantum_gravity = 9 := by decide

/-- SM/QG barrier: at least 4 primitive mismatches (actually 9). -/
theorem sm_qg_barrier :
    primitiveMismatches standard_model quantum_gravity ≥ 4 := by decide

/-- GR→AS UV completion: exactly 3 primitive changes (K: slow→mod, G: gimel→aleph, Φ: sub→c). -/
theorem gr_as_morphism_cost :
    primitiveMismatches general_relativity asymptotic_safety = 3 := by decide

/-- GR and SM share D and T: both operate in 3+1D spacetime with network interactions. -/
theorem gr_sm_same_DT_cluster :
    general_relativity.dim = standard_model.dim ∧
    general_relativity.top = standard_model.top := by decide

/-- Asymptotic safety sits at a quantum critical point. -/
theorem as_is_QCP : asymptotic_safety.crit = Criticality.Phi_c := rfl

/-- The Higgs field is K_slow by construction. -/
theorem higgs_is_Kslow : higgs.kin = KineticChar.K_slow := rfl

/-- All scalar K_slow fields are at a critical point (SSB is a phase transition). -/
theorem scalar_Kslow_at_Phi_c : scalarField_Kslow.crit = Criticality.Phi_c := rfl

/-- QG synthon is consistent with Axiom D (Omega_NA ↔ D_holo). -/
theorem qg_satisfies_axiom_D :
    quantum_gravity.prot = Protection.Omega_NA →
    quantum_gravity.dim = Dimensionality.D_holo := by decide

/-- QG synthon is consistent with Axiom A (H_inf → K_trap). -/
theorem qg_satisfies_axiom_A :
    quantum_gravity.chir = Chirality.H_inf →
    quantum_gravity.kin = KineticChar.K_trap := by decide

theorem primitiveMismatches_le_of_eq {a b : Synthon} (h : a = b) :
    primitiveMismatches a b = 0 := by subst h; exact primitiveMismatches_self a

end SynthOmnicon.Primitives
