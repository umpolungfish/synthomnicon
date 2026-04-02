-- SynthOmnicon/Classical/OPN_2adic.lean
-- Track 2, File 1: Classical number theory — 2-adic valuation for OPN.
-- This file is INDEPENDENT of the Synthonicon type system.
-- It uses Mathlib directly. Every sorry is an honest open problem marker.

import Mathlib.NumberTheory.ArithmeticFunction
import Mathlib.Data.Nat.Factorization.Basic
import Mathlib.Data.Nat.GCD.Basic
import Mathlib.RingTheory.Multiplicity
import Mathlib.Data.Nat.Parity
import Mathlib.Algebra.GeomSum               -- geom_sum_eq, for σ(p^k) formula
import Mathlib.Data.Nat.Multiplicity         -- emultiplicity / v₂ lemmas

open Nat ArithmeticFunction

namespace SynthOmnicon.Classical.OPN

-- ============================================================
-- HELPER LEMMAS
-- ============================================================

-- Helper: (p-1) divides (p^n - 1) for any n, via geometric sum.
-- Used in both Lemma 1 and Lemma 2.
private lemma pred_dvd_pow_sub_one (p n : ℕ) (hp : 1 ≤ p) :
    (p - 1) ∣ (p ^ n - 1) := by
  use ∑ i in Finset.range n, p ^ i
  -- Lift to ℤ to use the ring identity (p-1) * ∑pⁱ = pⁿ - 1
  zify [hp, Nat.one_le_pow n p (by omega)]
  -- geom_sum_mul : (∑ i in range n, x^i) * (x - 1) = x^n - 1
  linear_combination geom_sum_mul (p : ℤ) n

-- Helper: For n divisible by (p-1), v₂(n / (p-1)) = v₂(n) - v₂(p-1).
-- Follows from Nat.factorization_div.
private lemma v2_div_of_dvd {a b : ℕ} (h : b ∣ a) (hb : b ≠ 0) :
    v₂ (a / b) = v₂ a - v₂ b := by
  simp only [v₂]
  rw [Nat.factorization_div h]
  simp [Finsupp.sub_apply]

-- Helper: If n % 4 = 2 then v₂(n) = 1.
-- Proof: 2 | n (so v₂ ≥ 1) and 4 ∤ n (so v₂ < 2).
private lemma v2_eq_one_of_mod4_eq2 {n : ℕ} (hn : n % 4 = 2) : v₂ n = 1 := by
  have hpos : n ≠ 0 := by omega
  have h2 : 2 ∣ n := ⟨n / 2, by omega⟩
  have h4 : ¬ (2 ^ 2 ∣ n) := by norm_num; exact fun ⟨k, hk⟩ => by omega
  simp only [v₂]
  apply Nat.le_antisymm
  · -- v₂(n) ≤ 1: 4 ∤ n means 2^2 ∤ n means factorization 2 < 2
    by_contra hgt
    push_neg at hgt
    have : 2 ^ 2 ∣ n := by
      rw [← Nat.factorization_le_iff_pow_dvd_of_ne_zero hpos]
      · omega
      · norm_num
    exact h4 this
  · -- v₂(n) ≥ 1: 2 | n means factorization 2 ≥ 1
    rw [Nat.one_le_iff_ne_zero]
    intro heq
    rw [Nat.factorization_eq_zero_iff] at heq
    rcases heq with h | h | h
    · exact absurd (by norm_num : Nat.Prime 2) h
    · exact h h2
    · exact hpos h

-- Helper: Sum of (2e+1) copies of (q^i mod 2 = 1) gives sum ≡ 1 (mod 2).
-- This is the core parity argument for Lemma 2.
private lemma geom_sum_odd_mod2 (q e : ℕ) (hq_odd : q % 2 = 1) :
    (∑ i in Finset.range (2 * e + 1), q ^ i) % 2 = 1 := by
  have hqi : ∀ i, q ^ i % 2 = 1 := fun i => by
    rw [Nat.pow_mod]; simp [hq_odd]
  simp_rw [Finset.sum_mod, hqi, Finset.sum_const, Finset.card_range,
           smul_eq_mul, mul_one]
  omega

-- Helper: If p ≡ 1 (mod 4) and n ≡ 2 (mod 4), then
-- ∑ i in range(n), p^i ≡ 2 (mod 4), hence v₂ of the sum = 1.
-- This is the core argument for Lemma 1 — NO LTE NEEDED.
-- Proof: p^i ≡ 1^i ≡ 1 (mod 4), so ∑ ≡ n ≡ 2 (mod 4).
private lemma geom_sum_mod4_eq2 (p n : ℕ) (hp_mod : p % 4 = 1) (hn_mod : n % 4 = 2) :
    (∑ i in Finset.range n, p ^ i) % 4 = 2 := by
  have hpi : ∀ i, p ^ i % 4 = 1 := fun i => by
    rw [Nat.pow_mod]; simp [hp_mod]
  simp_rw [Finset.sum_mod, hpi, Finset.sum_const, Finset.card_range,
           smul_eq_mul, mul_one]
  omega

-- ============================================================
-- DEFINITIONS
-- ============================================================

-- σ(n) is the sum-of-divisors function, available in Mathlib as
-- ArithmeticFunction.sigma 1.
-- Perfect: σ(n) = 2n
def Perfect (n : ℕ) : Prop := sigma 1 n = 2 * n

-- 2-adic valuation: v₂(n) = multiplicity of 2 in n
-- Available in Mathlib as: (n.factorization) 2
-- or as: multiplicity 2 n
noncomputable def v₂ (n : ℕ) : ℕ := (Nat.factorization n) 2

-- ============================================================
-- EULER'S THEOREM (1747) — the real baseline
-- Every odd perfect number has the form n = p^k * m²
-- where p is prime, p ≡ 1 [MOD 4], k ≡ 1 [MOD 4], gcd(p, m) = 1.
-- ============================================================

-- This is the genuine starting point. Not "proven right now" —
-- proven by Euler in 1747. Mathlib may or may not have this yet;
-- we state it as a sorry if not available.
theorem euler_opn_form (n : ℕ) (h_odd : ¬ 2 ∣ n) (h_perf : Perfect n) :
    ∃ (p k m : ℕ),
      Nat.Prime p ∧
      n = p ^ k * m ^ 2 ∧
      p % 4 = 1 ∧
      k % 4 = 1 ∧
      ¬ p ∣ m := by
  sorry -- Euler 1747. Mathlib reference: not yet in Mathlib as of 2025.

-- ============================================================
-- THE 2-ADIC VALUATION ARGUMENT
-- This is the classical core identified in the framework session.
-- ============================================================

-- Lemma 1: For odd prime p with p ≡ 1 [MOD 4] and k ≡ 1 [MOD 4],
-- v₂(σ(p^k)) = 1.
--
-- Mathematical proof:
--   σ(p^k) = (p^(k+1) - 1) / (p - 1)
--   By 2-adic LTE (even exponent case, 2 | p - 1):
--     v₂(p^(k+1) - 1) = v₂(p-1) + v₂(p+1) + v₂(k+1) - 1
--   Since p ≡ 1 (mod 4): v₂(p+1) = 1  [p+1 ≡ 2 (mod 4)]
--   Since k ≡ 1 (mod 4): v₂(k+1) = 1  [k+1 ≡ 2 (mod 4)]
--   So: v₂(p^(k+1) - 1) = v₂(p-1) + 1 + 1 - 1 = v₂(p-1) + 1
--   Therefore: v₂(σ(p^k)) = v₂(p^(k+1)-1) - v₂(p-1) = 1
-- Key insight: NO LTE NEEDED. The proof uses only mod-4 arithmetic.
-- Since p ≡ 1 (mod 4), each p^i ≡ 1 (mod 4).
-- Sum of k+1 ≡ 2 (mod 4) such terms gives σ(p^k) ≡ 2 (mod 4), so v₂ = 1.
lemma v2_sigma_prime_power (p k : ℕ) (hp : Nat.Prime p) (hp_odd : ¬ 2 ∣ p)
    (hp_mod : p % 4 = 1) (hk_mod : k % 4 = 1) :
    v₂ (sigma 1 (p ^ k)) = 1 := by
  -- Step 1: σ(p^k) = ∑ i in Finset.range (k+1), p^i
  have h_sigma_sum : sigma 1 (p ^ k) = ∑ i in Finset.range (k + 1), p ^ i := by
    -- sigma 1 (p^k) = ∑ d in (p^k).divisors, d^1
    --               = ∑ d in (range(k+1)).image (p^·), d
    --               = ∑ i in range(k+1), p^i   [by sum_image + injectivity of p^·]
    simp only [ArithmeticFunction.sigma_apply, pow_one,
               Nat.divisors_prime_pow hp]
    exact Finset.sum_image (fun i _ j _ h => Nat.pow_right_injective hp.two_le h)
  -- Step 2: The sum has k+1 ≡ 2 (mod 4) terms each ≡ 1 (mod 4), giving sum ≡ 2 (mod 4)
  have h_sum_mod4 : (∑ i in Finset.range (k + 1), p ^ i) % 4 = 2 :=
    geom_sum_mod4_eq2 p (k + 1) hp_mod (by omega)
  -- Step 3: σ(p^k) ≡ 2 (mod 4), so v₂(σ(p^k)) = 1
  rw [h_sigma_sum]
  exact v2_eq_one_of_mod4_eq2 h_sum_mod4

-- Lemma 2: For odd prime q and even exponent 2e,
-- v₂(σ(q^(2e))) = 0.
--
-- Mathematical proof:
--   σ(q^(2e)) = (q^(2e+1) - 1) / (q - 1)
--   By 2-adic LTE (ODD exponent case, 2 | q - 1):
--     v₂(q^n - 1) = v₂(q - 1)   when n is odd
--   Here n = 2e+1 is odd.
--   So: v₂(q^(2e+1) - 1) = v₂(q - 1)
--   Therefore: v₂(σ(q^(2e))) = v₂(q^(2e+1)-1) - v₂(q-1) = 0
-- Note on proof strategy: We do NOT use the 2-adic LTE here.
-- The key insight is simpler: σ(q^(2e)) is a sum of 2e+1 (odd number of)
-- odd terms, so σ(q^(2e)) is odd, hence v₂ = 0.
-- This avoids LTE entirely and is the structurally cleanest proof.
lemma v2_sigma_square_factor (q e : ℕ) (hq : Nat.Prime q) (hq_odd : ¬ 2 ∣ q) :
    v₂ (sigma 1 (q ^ (2 * e))) = 0 := by
  -- Step 1: Express σ(q^(2e)) as a geometric sum over divisors
  have hq_odd_mod : q % 2 = 1 := by
    have : q % 2 ≠ 0 := fun h => hq_odd ⟨q / 2, by omega⟩
    omega
  have h_sigma_sum : sigma 1 (q ^ (2 * e)) =
      ∑ i in Finset.range (2 * e + 1), q ^ i := by
    simp [ArithmeticFunction.sigma_one_apply, Nat.divisors_prime_pow hq,
          Finset.sum_image (fun i _ j _ h => Nat.pow_right_injective hq.two_le h)]
  -- Step 2: The sum of (2e+1) odd terms is odd (no LTE needed)
  have h_sum_mod : (∑ i in Finset.range (2 * e + 1), q ^ i) % 2 = 1 :=
    geom_sum_odd_mod2 q e hq_odd_mod
  -- Step 3: σ(q^(2e)) is odd, so 2 ∤ σ(q^(2e)), so v₂ = 0
  have h_not_dvd : ¬ 2 ∣ sigma 1 (q ^ (2 * e)) := by
    rw [h_sigma_sum, Nat.dvd_iff_mod_eq_zero]
    omega
  simp only [v₂, Nat.factorization_eq_zero_iff]
  right; left; exact h_not_dvd

-- Lemma 3 (THE ACCUMULATION CONSTRAINT):
-- This is the non-trivial core identified in the session.
-- If n = p^k * ∏ qᵢ^(2eᵢ) is an OPN, then σ is multiplicative and
-- v₂(σ(n)) = v₂(σ(p^k)) + ∑ v₂(σ(qᵢ^(2eᵢ)))
--           = 1            + 0
--           = 1
-- But σ(n) = 2n, so v₂(σ(n)) = v₂(2n) = 1 + v₂(n) = 1 + 0 = 1
-- (since n is odd). This is consistent — it does NOT give contradiction.
-- The constraint is that ALL square factors must contribute v₂ = 0,
-- which places strong divisibility restrictions on the qᵢ.

-- Note: The earlier session contained an error — claiming this gives
-- immediate contradiction. It doesn't. Euler's theorem is consistent
-- with v₂(σ(n)) = 1. What the accumulation constraint does is
-- severely restrict the structure of the square part m².

-- What it DOES give (honest statement):
theorem v2_accumulation_constraint (n p k m : ℕ)
    (h_odd : ¬ 2 ∣ n) (h_perf : Perfect n)
    (h_euler : n = p ^ k * m ^ 2)
    (hp : Nat.Prime p) (hp_mod : p % 4 = 1) (hk_mod : k % 4 = 1)
    (hp_odd : ¬ 2 ∣ p)
    (hq_odd : ∀ q ∈ (Nat.factorization m).support, ¬ 2 ∣ q) :
    -- The 2-adic budget is exactly exhausted by the prime power component:
    v₂ (sigma 1 (p ^ k)) = 1 ∧
    ∀ q ∈ (Nat.factorization m).support,
      ∃ e, v₂ (sigma 1 (q ^ (2 * e))) = 0 := by
  constructor
  · -- Part 1: v₂(σ(p^k)) = 1 follows directly from Lemma 1
    exact v2_sigma_prime_power p k hp hp_odd hp_mod hk_mod
  · -- Part 2: For each prime factor q of m, v₂(σ(q^(2e))) = 0
    -- The exponent of q in m² is 2*(exponent of q in m), so even.
    intro q hq_supp
    -- Let e be the exponent of q in m
    use (Nat.factorization m) q
    have hm_pos : m ≠ 0 := by
      intro hm; simp [hm] at h_euler; omega
    have hq_prime : q.Prime := by
      have : q ∈ m.primeFactors := by
        rwa [← Nat.support_factorization]
      exact ((Nat.mem_primeFactors hm_pos).mp this).1
    apply v2_sigma_square_factor q _ hq_prime (hq_odd q hq_supp)

-- ============================================================
-- HONEST STATEMENT OF WHAT REMAINS
-- ============================================================

-- The open problem is NOT that v₂ gives a contradiction.
-- The open problem is showing that the system of constraints
-- (from Euler's form + divisibility conditions on σ(p^k) and σ(qᵢ^(2eᵢ)))
-- has no solution in the integers.
--
-- Current best classical lower bound (as of 2025): OPN > 10^1500 (Ochem-Rao).
-- The accumulation argument is one piece of the constraint system,
-- not a standalone proof.

-- Placeholder for the full impossibility (the actual open problem):
theorem opn_nonexistence : ∀ n : ℕ, ¬ (¬ 2 ∣ n ∧ Perfect n) := by
  sorry -- Open problem. Do not claim proven.

end SynthOmnicon.Classical.OPN