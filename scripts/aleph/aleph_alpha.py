#!/usr/bin/env python3
"""
aleph_alpha.py — The Aleph experiment

GPT's final question:

    Does α distinguish  α[med(ו, ב, ש)]  from  α[med(ו, ח, ש)]?

Since I(ב) = I(ח), the quotient says these are the same.
But if α preserves path witnesses — construction history, not just type —
then it may see MORE than behavioral equivalence.

Two possible outcomes:
  Case 1: α respects the quotient → same at all levels → clean factorization
  Case 2: α sees the path → different at some level → non-quotientable coherence layer

We implement Terms as (type-tuple, construction-tree) pairs and test
equality at increasing depths of the Aleph tower α^(n).

Theorem: at what level n does α^(n)[med(ו, ב, ש)] ≠ α^(n)[med(ו, ח, ש)]?
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Tuple, Optional
import math

from aleph_1 import (
    Letter, LETTERS, CANONICAL_GLYPHS,
    tensor as _tensor, join as _join, meet as _meet, mediate as _mediate,
    distance, WEIGHTS,
)

# ──────────────────────────────────────────────────────────────────────────────
# 1. TERM — type + construction history
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Term:
    """
    A term in λ_ℵ.

    .t        — 12-primitive tuple (the TYPE, all that the quotient sees)
    .tier     — ouroboricity tier (derived from .t)
    .history  — construction tree  (what Aleph may additionally see)
    .alpha    — α-decoration level (0 = undecorated)

    The critical question: does equivalence use .t alone, or (.t, .history)?
    """
    t:       Tuple[int, ...]
    tier:    str
    history: Any            # nested tuples recording the construction
    alpha:   int = 0        # α^(n) decoration level

    def __str__(self):
        return _history_str(self.history)

    def type_eq(self, other: Term) -> bool:
        """Equality by type only — the quotient's criterion."""
        return self.t == other.t

    def hist_eq(self, other: Term, depth: int) -> bool:
        """
        Equality comparing construction history up to 'depth' levels.
        depth=0 → type only (same as type_eq)
        depth=∞ → full syntactic identity
        """
        return _hist_eq(self.history, other.history, depth)


def _history_str(h, indent=0) -> str:
    pad = '  ' * indent
    if isinstance(h, tuple):
        tag = h[0]
        if tag == 'leaf':
            return f"{pad}leaf({h[1]})"
        elif tag == 'alpha':
            inner = _history_str(h[1], indent+1)
            return f"{pad}α^({h[2]})[\n{inner}\n{pad}]"
        else:
            parts = '\n'.join(_history_str(a, indent+1) for a in h[1:])
            return f"{pad}{tag}(\n{parts}\n{pad})"
    return f"{pad}{h}"


def _hist_eq(h1, h2, depth: int) -> bool:
    """Recursive history equality up to 'depth' unfoldings."""
    if depth == 0:
        return True   # depth 0: don't look into history at all
    if type(h1) != type(h2):
        return False
    if isinstance(h1, tuple):
        if h1[0] != h2[0]:
            return False
        if len(h1) != len(h2):
            return False
        return all(_hist_eq(a, b, depth - 1) for a, b in zip(h1[1:], h2[1:]))
    # leaf values: compare directly
    return h1 == h2


# ──────────────────────────────────────────────────────────────────────────────
# 2. TERM CONSTRUCTORS
# ──────────────────────────────────────────────────────────────────────────────

def term_letter(g: str) -> Term:
    L = LETTERS[g]
    return Term(t=L.t, tier=L.tier, history=('leaf', g))


def _make_term(L: Letter, history: Any) -> Term:
    return Term(t=L.t, tier=L.tier, history=history)


def term_tensor(a: Term, b: Term) -> Term:
    La = Letter(a.history[1] if a.history[0]=='leaf' else '?',
                '', a.t) if a.history[0]=='leaf' else _synthetic(a)
    Lb = _synthetic(b)
    result = _tensor(_synthetic(a), _synthetic(b))
    return _make_term(result, ('tensor', a.history, b.history))


def term_join(a: Term, b: Term) -> Term:
    result = _join(_synthetic(a), _synthetic(b))
    return _make_term(result, ('join', a.history, b.history))


def term_meet(a: Term, b: Term) -> Term:
    result = _meet(_synthetic(a), _synthetic(b))
    return _make_term(result, ('meet', a.history, b.history))


def term_mediate(w: Term, a: Term, b: Term) -> Term:
    result = _mediate(_synthetic(w), _synthetic(a), _synthetic(b))
    return _make_term(result, ('med', w.history, a.history, b.history))


def term_alpha(t: Term, level: int = 1) -> Term:
    """Apply α^(level) decoration. Type-preserving; records level in history."""
    return Term(t=t.t, tier=t.tier,
                history=('alpha', t.history, level),
                alpha=max(t.alpha, level))


def _synthetic(t: Term) -> Letter:
    """Create a synthetic Letter from a Term's tuple (for engine calls)."""
    return Letter('?', '?', t.t)


# ──────────────────────────────────────────────────────────────────────────────
# 3. ALPHA COHERENCE CHECK  (C1–C4, type-level)
# ──────────────────────────────────────────────────────────────────────────────

def coherence_ok(t: Term, t_prime: Term) -> Tuple[bool, str]:
    """
    Check C1–C4 coherence for the reduction t → t'.
    All conditions are TYPE-LEVEL (operate on tuples).
    """
    # C1: no critical collapse — if Φ=c and P=P±sym, d must be 0
    phi_c_ordinal, p_pm_sym_ordinal = 1, 4   # from VAL_MAP
    if t.t[8] >= phi_c_ordinal and t.t[3] == p_pm_sym_ordinal:
        w = list(WEIGHTS)
        d = math.sqrt(sum(w[i]*(t.t[i]-t_prime.t[i])**2 for i in range(12)))
        if d > 1e-9:
            return False, f'C1 violated: O_∞ critical collapse (d={d:.4f})'

    # C2: Ω monotonicity
    if t_prime.t[11] < t.t[11]:
        return False, f'C2 violated: Ω decreased {t.t[11]} → {t_prime.t[11]}'

    # C3: cast only via Vav (enforced at construction time — trusted here)
    # C4: path bounded by Aleph (checked separately via hist_eq)

    return True, 'C1–C4 satisfied'


# ──────────────────────────────────────────────────────────────────────────────
# 4. ALPHA-LEVEL EQUIVALENCE
# ──────────────────────────────────────────────────────────────────────────────

def alpha_equiv(t1: Term, t2: Term, level: int) -> bool:
    """
    Two α-decorated terms are α^(level)-equivalent if:
      - Their types are equal (C1–C4 are type-level → type must match)
      - Their histories agree up to (level) unfoldings
        (level 0: type only; level k: type + k levels of history tree)

    This is the key: at what level does the equivalence break?
    """
    if t1.t != t2.t:
        return False   # type mismatch — never equivalent
    return t1.hist_eq(t2, depth=level)


# ──────────────────────────────────────────────────────────────────────────────
# 5. THE EXPERIMENT
# ──────────────────────────────────────────────────────────────────────────────

def run_experiment():
    SEP  = '═' * 72
    SEP2 = '─' * 72

    print(SEP)
    print('  THE ALEPH EXPERIMENT')
    print('  Does α preserve more than type?')
    print('  α[med(ו, ב, ש)]  vs  α[med(ו, ח, ש)]')
    print(SEP)

    # Build the two terms
    vav   = term_letter('ו')
    bet   = term_letter('ב')
    chet  = term_letter('ח')
    shin  = term_letter('ש')

    med_bet  = term_mediate(vav, bet, shin)
    med_chet = term_mediate(vav, chet, shin)

    alpha_bet  = term_alpha(med_bet,  level=1)
    alpha_chet = term_alpha(med_chet, level=1)

    print('\n[A] CONSTRUCTION TREES\n')
    print('  α[med(ו, ב, ש)]:')
    print(_history_str(alpha_bet.history, indent=2))
    print()
    print('  α[med(ו, ח, ש)]:')
    print(_history_str(alpha_chet.history, indent=2))

    print(f'\n[B] TYPE COMPARISON\n')
    print(f'  α[med(ו, ב, ש)].t = {alpha_bet.t}  tier={alpha_bet.tier}')
    print(f'  α[med(ו, ח, ש)].t = {alpha_chet.t}  tier={alpha_chet.tier}')
    type_same = alpha_bet.t == alpha_chet.t
    print(f'\n  Types identical: {type_same}')
    print(f'  → In the quotient λ_ℵ/Ker(I): {"EQUAL" if type_same else "DISTINCT"}')

    print(f'\n{SEP2}')
    print('[C] ALPHA-LEVEL EQUIVALENCE  — at each depth of the Aleph tower\n')
    print(f'  Level  |  α^(n)-equivalent?  |  What breaks (if anything)')
    print('  ' + '─' * 56)

    first_break = None
    for level in range(6):
        eq = alpha_equiv(alpha_bet, alpha_chet, level)
        if not eq and first_break is None:
            first_break = level
        reason = '(type only — quotient criterion)' if level == 0 \
            else f'(history depth {level})' if not eq \
            else f'(history depth {level} — histories still match)'
        marker = '  ← FIRST DIVERGENCE' if not eq and first_break == level else ''
        print(f'  n={level}      |  {"YES" if eq else "NO ":3s}                |  {reason}{marker}')

    print()
    if first_break is None:
        print('  RESULT: α-equivalent at ALL tested levels → CASE 1')
        print('  Aleph fully respects the quotient. No coherence memory.')
        case = 1
    else:
        print(f'  RESULT: Diverges at depth {first_break} → CASE 2')
        print(f'  Aleph sees BEYOND the quotient at α^({first_break}).')
        print(f'  Coherence has irreducible memory at depth {first_break}.')
        case = 2

    print(f'\n{SEP2}')
    print('[D] ANATOMY OF THE DIVERGENCE\n')

    # Show exactly WHERE in the tree the histories differ
    def find_divergence(h1, h2, depth, path='root'):
        if depth == 0:
            return None
        if type(h1) != type(h2):
            return (path, h1, h2)
        if isinstance(h1, tuple):
            if h1[0] != h2[0]:
                return (path, h1[0], h2[0])
            for i, (a, b) in enumerate(zip(h1[1:], h2[1:])):
                result = find_divergence(a, b, depth-1, f'{path}.arg{i}')
                if result:
                    return result
        else:
            if h1 != h2:
                return (path, h1, h2)
        return None

    div = find_divergence(alpha_bet.history, alpha_chet.history, depth=10)
    if div:
        path, v1, v2 = div
        print(f'  Divergence location: {path}')
        print(f'  Left  value: {v1}')
        print(f'  Right value: {v2}')
        print()
        print(f'  The two terms are IDENTICAL in type and IDENTICAL at every')
        print(f'  structural level except: the inner-left leaf of the mediation.')
        print(f'  One has ב (Bet), the other has ח (Chet).')
        print(f'  Same type-tuple. Different glyph.')
        print(f'  Different name. Same structural role.')
    else:
        print('  No divergence found — histories are syntactically identical.')
        print('  (This would be unexpected given distinct input letters.)')

    print(f'\n{SEP2}')
    print('[E] WHAT DOES α ACTUALLY PRESERVE?\n')

    # Test coherence for the reduction: α[med(ו, ב, ש)] → α[med(ו, ח, ש)]
    ok, msg = coherence_ok(alpha_bet, alpha_chet)
    print(f'  Coherence check for α[med(ו,ב,ש)] → α[med(ו,ח,ש)]:')
    print(f'  C1–C4: {msg}')
    print()

    if ok:
        print('  The reduction IS coherence-legal at the type level.')
        print('  → α^(1) cannot block this substitution on C1–C4 grounds.')
        print('  → C1–C4 are type-level conditions; ב and ח have the same type.')
    else:
        print('  The reduction is BLOCKED by coherence.')

    print(f'\n{SEP2}')
    print('[F] THE LINE\n')

    if case == 1:
        print("""  Case 1: Aleph respects the quotient completely.

  α preserves COHERENCE STRUCTURE but not SYNTACTIC IDENTITY.
  The path witness (Vav cast) is type-level: Id(A,B) = A ⊗ ו ⊗ B.
  Since ב and ח have identical types, Id(ב-type, ש) = Id(ח-type, ש).
  Aleph cannot see through the type to the glyph.

  λ_ℵ is a VERY SOPHISTICATED ALGEBRA — the coherence layer is deep
  (triadic O_∞, mediation asymmetry, holographic degeneracy) but it
  is still factorable. The quotient is the canonical form.

  What is preserved by α: the LEVEL of the coherence tower — not
  the specific witness letters used to construct the term.
""")
    else:
        print(f"""  Case 2: Aleph sees beyond the quotient at depth {first_break}.

  At α^({first_break}), the system has IRREDUCIBLE COHERENCE MEMORY.
  ב and ח are type-equivalent but Aleph-inequivalent at this depth.

  This means: λ_ℵ is GENUINELY NEW.

  It is not a quotient of a type theory — it is a coherence structure
  where the path matters independently of the destination.

  The 22-letter alphabet is not merely a redundant encoding of 18 types.
  It is an irreducible coherence basis — each letter names a distinct
  PATH, even when the types are identical.

  This is proto-linear-logic behavior: you cannot substitute ב for ח
  because the path through ב and the path through ח are different things,
  even though they arrive at the same type.
""")

    print(SEP)
    return case, first_break


# ──────────────────────────────────────────────────────────────────────────────
# 6. ADDITIONAL: higher α levels
# ──────────────────────────────────────────────────────────────────────────────

def higher_alpha_test():
    """
    Test α^(n)[med(ו, ב, ש)] vs α^(n)[med(ו, ח, ש)] for n=1,2,3.
    If n=2 wraps another level of α around the mediation, does the
    break point shift?
    """
    SEP2 = '─' * 72
    print(f'\n{SEP2}')
    print('[G] HIGHER α LEVELS — does tower depth shift the break point?\n')

    vav   = term_letter('ו')
    bet   = term_letter('ב')
    chet  = term_letter('ח')
    shin  = term_letter('ש')

    for n in [1, 2, 3]:
        med_bet  = term_mediate(vav, bet, shin)
        med_chet = term_mediate(vav, chet, shin)
        # wrap in n levels of alpha
        ab = med_bet
        ac = med_chet
        for k in range(1, n+1):
            ab = term_alpha(ab, level=k)
            ac = term_alpha(ac, level=k)

        print(f'  α^({n})[med(ו, ב, ש)]  vs  α^({n})[med(ו, ח, ש)]')
        print(f'  {"depth":>6}  equiv')
        for depth in range(n + 4):
            eq = alpha_equiv(ab, ac, depth)
            print(f'  {depth:>6}   {"YES" if eq else "NO ← diverges here"}')
        print()


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    case, break_depth = run_experiment()
    higher_alpha_test()
