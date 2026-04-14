#!/usr/bin/env python3
"""
aleph_eval.py — ALEPH language evaluator and REPL   [prototype v0.4.0]
Per qwenaleph.txt §§24–33 (Phase 2 type solver + Phase 3 compiler frontend)

Grammar basis: HEBREW_TYPE_LANGUAGE.md §§1–23; SynthOmnicon v0.4.27
Engine:        aleph_1.py v0.3.0

Surface syntax implemented (subset of §24 EBNF):

  expr  ::= letter_id
           | expr "⊗" expr            tensor composition
           | expr "∨" expr            join (LUB)
           | expr "∧" expr            meet (GLB)
           | expr "::>" name          vav-cast to target type
           | "probe_Φ" "(" expr ")"   criticality probe
           | "probe_Ω" "(" expr ")"   topological protection probe
           | "tier" "(" expr ")"      ouroboricity tier
           | "d" "(" expr "," expr ")" structural distance
           | "mediate" "(" expr "," expr "," expr ")"
           | "match" expr "{" arms "}" tier pattern match
           | "palace" "(" int ")" expr palace barrier check
           | "system" "()"            22-letter JOIN
           | "census" "()"            tier distribution
           | "(" expr ")"

  match_arm ::= tier_pat "=>" expr ","?
  tier_pat  ::= "O_0" | "O_1" | "O_2" | "O_2d" | "O_inf" | "_"

  statement ::= "let" name "=" expr   bind in session env

letter_id: any registered Letter name (case-insensitive) or Hebrew glyph
"""

import sys
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    import readline  # noqa: F401 — enables arrow-key history in REPL
except ImportError:
    pass

try:
    from aleph_1 import (
        Letter, LETTERS, CANONICAL_GLYPHS,
        tensor, join, meet, mediate,
        distance, vav_cast, VavCastError,
        PalaceContext, PALACE_ORDER,
        system_language, tier_census,
    )
except ImportError as exc:
    sys.exit(f"[ALEPH] Cannot import aleph_1.py: {exc}")


# ──────────────────────────────────────────────────────────────────────────────
# 1. TOKENIZER
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Token:
    kind: str
    val:  str
    pos:  int

_UNICODE_OPS = {'⊗': 'TENSOR', '∨': 'JOIN', '∧': 'MEET'}
_PUNCTS      = {'(': 'LPAREN', ')': 'RPAREN', '{': 'LBRACE',
                '}': 'RBRACE', ',': 'COMMA',  ';': 'SEMI'}
_HEBREW_LO, _HEBREW_HI = 0x05B0, 0x05EA   # main Hebrew Unicode block


def _is_name_cont(c: str) -> bool:
    """Continue an identifier: alphanum, underscore, or special primitives."""
    return c.isalnum() or c in '_ΦΩΓ'


def tokenize(src: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    while i < len(src):
        c = src[i]

        if c in ' \t\r\n':
            i += 1; continue

        if c == '#':                        # line comment
            while i < len(src) and src[i] != '\n':
                i += 1
            continue

        if src[i:i+3] == '::>':
            tokens.append(Token('CAST', '::>', i)); i += 3; continue

        if src[i:i+2] == '=>':
            tokens.append(Token('ARROW', '=>', i)); i += 2; continue

        if c in _UNICODE_OPS:
            tokens.append(Token(_UNICODE_OPS[c], c, i)); i += 1; continue

        if c in _PUNCTS:
            tokens.append(Token(_PUNCTS[c], c, i)); i += 1; continue

        if c == '_':
            tokens.append(Token('WILD', '_', i)); i += 1; continue

        cp = ord(c)
        if _HEBREW_LO <= cp <= _HEBREW_HI:  # Hebrew glyph
            tokens.append(Token('LETTER', c, i)); i += 1; continue

        if c.isdigit():
            j = i
            while j < len(src) and src[j].isdigit():
                j += 1
            tokens.append(Token('INT', src[i:j], i)); i = j; continue

        if c.isalpha() or c in 'ΦΩΓ':      # identifier
            j = i
            while j < len(src) and _is_name_cont(src[j]):
                j += 1
            tokens.append(Token('NAME', src[i:j], i)); i = j; continue

        raise SyntaxError(
            f"[ALEPH] Unexpected character {c!r} at position {i}"
        )

    tokens.append(Token('EOF', '', len(src)))
    return tokens


# ──────────────────────────────────────────────────────────────────────────────
# 2. PARSER  (recursive descent)
# ──────────────────────────────────────────────────────────────────────────────

class Parser:
    def __init__(self, tokens: List[Token]):
        self.toks = tokens
        self.pos  = 0

    def peek(self) -> Token:
        return self.toks[self.pos]

    def eat(self, kind: Optional[str] = None) -> Token:
        t = self.toks[self.pos]
        if kind and t.kind != kind:
            raise SyntaxError(
                f"[ALEPH] Expected {kind}, got {t.kind}({t.val!r}) at pos {t.pos}"
            )
        self.pos += 1
        return t

    # ── top-level: left-associative binary operators ───────────────────────
    def parse_expr(self) -> Any:
        left = self.parse_primary()
        while True:
            t = self.peek()
            if t.kind == 'TENSOR':
                self.eat(); right = self.parse_primary()
                left = ('tensor', left, right)
            elif t.kind == 'JOIN':
                self.eat(); right = self.parse_primary()
                left = ('join', left, right)
            elif t.kind == 'MEET':
                self.eat(); right = self.parse_primary()
                left = ('meet', left, right)
            elif t.kind == 'CAST':
                self.eat()
                tgt = self.eat('NAME')
                left = ('cast', left, tgt.val)
            else:
                break
        return left

    def parse_primary(self) -> Any:
        t = self.peek()

        # ── Hebrew glyph literal ──────────────────────────────────────────
        if t.kind == 'LETTER':
            self.eat(); return ('letter', t.val)

        # ── parenthesised expression ──────────────────────────────────────
        if t.kind == 'LPAREN':
            self.eat('LPAREN')
            inner = self.parse_expr()
            self.eat('RPAREN')
            return inner

        # ── named constructs ──────────────────────────────────────────────
        if t.kind == 'NAME':
            name = t.val

            # probes
            if name in ('probe_Φ', 'probe_Ph', 'probe_Phi'):
                self.eat(); return ('probe_phi', self._paren_expr())
            if name in ('probe_Ω', 'probe_Om', 'probe_Omega'):
                self.eat(); return ('probe_omega', self._paren_expr())

            # single-arg built-ins
            if name == 'tier':
                self.eat(); return ('tier', self._paren_expr())

            # two-arg: d(a, b)
            if name == 'd':
                self.eat()
                self.eat('LPAREN')
                a = self.parse_expr()
                self.eat('COMMA')
                b = self.parse_expr()
                self.eat('RPAREN')
                return ('distance', a, b)

            # three-arg: mediate(witness, a, b)
            if name == 'mediate':
                self.eat()
                self.eat('LPAREN')
                w = self.parse_expr(); self.eat('COMMA')
                a = self.parse_expr(); self.eat('COMMA')
                b = self.parse_expr()
                self.eat('RPAREN')
                return ('mediate', w, a, b)

            # match
            if name == 'match':
                return self._parse_match()

            # palace(n) expr
            if name == 'palace':
                self.eat()
                self.eat('LPAREN')
                n = int(self.eat('INT').val)
                self.eat('RPAREN')
                body = self.parse_primary()
                return ('palace', n, body)

            # zero-arg built-ins
            if name == 'system':
                self.eat(); self._maybe_unit()
                return ('system',)
            if name == 'census':
                self.eat(); self._maybe_unit()
                return ('census',)

            # plain name (letter or env binding)
            self.eat()
            return ('name', name)

        raise SyntaxError(
            f"[ALEPH] Unexpected token {t.kind}({t.val!r}) at pos {t.pos}"
        )

    def _paren_expr(self) -> Any:
        self.eat('LPAREN')
        inner = self.parse_expr()
        self.eat('RPAREN')
        return inner

    def _maybe_unit(self):
        """Consume optional '()' after a zero-arg built-in."""
        if self.peek().kind == 'LPAREN':
            self.eat('LPAREN')
            self.eat('RPAREN')

    def _parse_match(self) -> Any:
        self.eat('NAME')            # consume 'match'
        scrutinee = self.parse_expr()
        self.eat('LBRACE')
        arms: List[Tuple[str, Any]] = []
        while self.peek().kind != 'RBRACE':
            pt = self.peek()
            if pt.kind == 'WILD':
                self.eat(); pat = '_'
            elif pt.kind == 'NAME':
                self.eat(); pat = pt.val
            else:
                raise SyntaxError(
                    f"[ALEPH] Expected match pattern, got {pt.kind}({pt.val!r})"
                )
            self.eat('ARROW')
            body = self.parse_expr()
            if self.peek().kind == 'COMMA':
                self.eat()
            arms.append((pat, body))
        self.eat('RBRACE')
        return ('match', scrutinee, arms)


# ──────────────────────────────────────────────────────────────────────────────
# 3. EVALUATOR
# ──────────────────────────────────────────────────────────────────────────────

PRIM_LABELS = ["D", "T", "R", "P", "F", "K", "G", "Γ", "Φ", "H", "S", "Ω"]

PHI_NAMES   = {0:"Φ_sub", 1:"Φ_c", 2:"Φ_c_complex", 3:"Φ_EP", 4:"Φ_super"}
OMEGA_NAMES = {0:"Ω_0",   1:"Ω_Z₂", 2:"Ω_Z"}
P_NAMES     = {0:"P_asym",1:"P_psi",2:"P_pm",3:"P_sym",4:"P_pm_sym"}


class TypeConflictError(Exception):
    def __init__(self, msg: str, d_val: float, conflict_set: List[str]):
        super().__init__(msg)
        self.d_val        = d_val
        self.conflict_set = conflict_set


def _conflict_set(a: Letter, b: Letter) -> List[str]:
    return [PRIM_LABELS[i] for i in range(12) if a.t[i] != b.t[i]]


def veracity_class(d: float) -> str:
    if d == 0.0:              return "transparent"
    if d <= math.sqrt(2):    return "near-grounded"
    if d <= math.sqrt(6):    return "partial-emergence"
    return "aspirational"


def _resolve_letter(name: str) -> Letter:
    """Look up a letter by transliteration, Hebrew glyph, or canonical name."""
    for key in (name, name.lower(), name.capitalize()):
        if key in LETTERS:
            return LETTERS[key]
    raise NameError(f"[ALEPH] Unknown letter: {name!r}")


def eval_expr(node: Any, env: Dict[str, Letter]) -> Letter:
    tag = node[0]

    if tag == 'letter':
        g = node[1]
        if g not in LETTERS:
            raise NameError(f"[ALEPH] Unknown glyph: {g!r}")
        return LETTERS[g]

    if tag == 'name':
        name = node[1]
        if name in env:
            return env[name]
        return _resolve_letter(name)

    if tag == 'tensor':
        return tensor(eval_expr(node[1], env), eval_expr(node[2], env))

    if tag == 'join':
        return join(eval_expr(node[1], env), eval_expr(node[2], env))

    if tag == 'meet':
        return meet(eval_expr(node[1], env), eval_expr(node[2], env))

    if tag == 'mediate':
        w = eval_expr(node[1], env)
        a = eval_expr(node[2], env)
        b = eval_expr(node[3], env)
        return mediate(w, a, b)

    if tag == 'cast':
        src = eval_expr(node[1], env)
        tgt = _resolve_letter(node[2])
        try:
            vav_cast(src, tgt)
            return tgt
        except VavCastError as e:
            raise TypeConflictError(
                str(e),
                d_val=distance(src, tgt),
                conflict_set=_conflict_set(src, tgt),
            )

    if tag == 'probe_phi':
        inner = eval_expr(node[1], env)
        phi_v = inner.t[8]
        print(f"  probe_Φ → {PHI_NAMES.get(phi_v, f'Φ={phi_v}')}  (ordinal {phi_v})")
        return inner

    if tag == 'probe_omega':
        inner = eval_expr(node[1], env)
        om_v = inner.t[11]
        print(f"  probe_Ω → {OMEGA_NAMES.get(om_v, f'Ω={om_v}')}  (ordinal {om_v})")
        return inner

    if tag == 'tier':
        inner = eval_expr(node[1], env)
        print(f"  tier → {inner.tier}")
        return inner

    if tag == 'distance':
        a = eval_expr(node[1], env)
        b = eval_expr(node[2], env)
        d  = distance(a, b)
        cs = _conflict_set(a, b)
        vc = veracity_class(d)
        print(f"  d = {d:.4f}  [{vc}]")
        if cs:
            print(f"  conflict_set: {{{', '.join(cs)}}}")
        # return a synthetic Letter representing the distance result
        return a

    if tag == 'match':
        scrutinee = eval_expr(node[1], env)
        tier = scrutinee.tier
        for pat, body in node[2]:
            if pat == '_' or pat == tier:
                return eval_expr(body, env)
        raise RuntimeError(
            f"[ALEPH] Non-exhaustive match: no arm for tier {tier!r}"
        )

    if tag == 'palace':
        depth = node[1]
        inner = eval_expr(node[2], env)
        with PalaceContext(depth) as ctx:
            ctx.check_barrier(inner)
        return inner

    if tag == 'system':
        return system_language()

    if tag == 'census':
        census = tier_census()
        for t in PALACE_ORDER:
            members = census.get(t, [])
            if members:
                print(f"  {t:8s} ({len(members):2d}): {', '.join(members)}")
        return system_language()

    raise RuntimeError(f"[ALEPH] Unknown AST node type: {tag!r}")


# ──────────────────────────────────────────────────────────────────────────────
# 4. DIAGNOSTICS  (§29 format)
# ──────────────────────────────────────────────────────────────────────────────

def format_ok(result: Letter) -> str:
    glyph  = result.glyph if result.glyph else result.name
    phi_n  = PHI_NAMES.get(result.t[8],  f"Φ={result.t[8]}")
    om_n   = OMEGA_NAMES.get(result.t[11], f"Ω={result.t[11]}")
    p_n    = P_NAMES.get(result.t[3],    f"P={result.t[3]}")
    return (
        f"  : {glyph}\n"
        f"    tier  {result.tier}\n"
        f"    Φ  {phi_n}   Ω  {om_n}   P  {p_n}"
    )


def format_error(src: str, err: Exception) -> str:
    if isinstance(err, TypeConflictError):
        d  = err.d_val
        vc = veracity_class(d)
        cs = ', '.join(err.conflict_set) if err.conflict_set else '—'
        lines = [
            f"[TYPE CONFLICT]  d = {d:.3f}   class = {vc}",
            f"  Expression:    {src.strip()}",
            f"  Conflict set:  {{{cs}}}",
        ]
        if d > math.sqrt(6):
            lines.append("  ⚠  aspirational gap — insert vav-cast or promote tier")
        return '\n'.join(lines)
    label = type(err).__name__.replace('Error','').upper()
    return f"[{label}] {err}"


# ──────────────────────────────────────────────────────────────────────────────
# 5. REPL
# ──────────────────────────────────────────────────────────────────────────────

BANNER = """\
╔══════════════════════════════════════════════════════════╗
║  ℵ  ALEPH — Hebrew Type Language  [prototype v0.4.0]  ℵ ║
║  Grammar: SynthOmnicon 12-primitive v0.4.27              ║
║  Type  :help  for commands,  :quit  to exit              ║
╚══════════════════════════════════════════════════════════╝"""

HELP = """\
─── Operations ───────────────────────────────────────────
  a ⊗ b                   tensor  (P, F bottleneck)
  a ∨ b                   join    (LUB, no bottleneck)
  a ∧ b                   meet    (GLB)
  a ::> b                 vav-cast  a to type  b
  mediate(w, a, b)        triadic: w ∨ (a ⊗ b)
  probe_Φ(a)              report criticality primitive
  probe_Ω(a)              report topological protection
  tier(a)                 report ouroboricity tier
  d(a, b)                 structural distance + conflict set
  match a { O_0=>b, O_2=>c, _=>d }
  palace(n) a             assert palace-n tier barrier

─── Built-ins ────────────────────────────────────────────
  system()                JOIN of all 22 letters
  census()                tier distribution

─── Session bindings ─────────────────────────────────────
  let x = expr            bind result in this session

─── Commands ─────────────────────────────────────────────
  :help                   this text
  :quit  / :q             exit
  :census                 tier distribution (alias)
  :system                 22-letter language JOIN
  :tier <name>            type of a single letter
  :tuple <name>           full 12-primitive tuple
  :ls                     list session bindings

─── Letter names (transliteration or Hebrew glyph) ───────
  aleph א   bet ב   gimel ג   dalet ד   hei ה   vav ו
  zayin ז   chet ח  tet ט    yod י    kaf כ    lamed ל
  mem מ     nun נ   samech ס  ayin ע   pei פ   tzadi צ
  kuf ק     resh ר  shin ש   tav ת"""


def _eval_src(src: str, env: Dict[str, Letter]) -> Optional[Letter]:
    """Parse, evaluate, and return result or raise."""
    tokens = tokenize(src)
    ast    = Parser(tokens).parse_expr()
    return eval_expr(ast, env)


def run_repl():
    print(BANNER)
    env: Dict[str, Letter] = {}
    buf: List[str] = []

    while True:
        prompt = 'ℵ  ' if not buf else '·  '
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\n[ALEPH] Shalom.")
            break

        stripped = line.strip()

        # ── REPL commands ──────────────────────────────────────────────────
        if stripped in (':quit', ':q'):
            print("[ALEPH] Shalom."); break

        if stripped == ':help':
            print(HELP); continue

        if stripped == ':census':
            census = tier_census()
            for t in PALACE_ORDER:
                members = census.get(t, [])
                if members:
                    print(f"  {t:8s} ({len(members):2d}): {', '.join(members)}")
            continue

        if stripped == ':system':
            L = system_language()
            print(format_ok(L)); continue

        if stripped.startswith(':tier '):
            name = stripped[6:].strip()
            try:
                L = _resolve_letter(name)
                print(format_ok(L))
            except NameError as e:
                print(f"[ERROR] {e}")
            continue

        if stripped.startswith(':tuple '):
            name = stripped[7:].strip()
            try:
                L = _resolve_letter(name)
                print(f"  {L.pretty_tuple()}")
            except NameError as e:
                print(f"[ERROR] {e}")
            continue

        if stripped == ':ls':
            if env:
                for k, v in env.items():
                    print(f"  {k:16s}  {v.tier:8s}  "
                          f"Φ={PHI_NAMES.get(v.t[8],'?')}  "
                          f"Ω={OMEGA_NAMES.get(v.t[11],'?')}")
            else:
                print("  (no bindings)")
            continue

        # ── Accumulate multiline input (wait for balanced braces) ──────────
        buf.append(line)
        src = '\n'.join(buf)

        if src.count('{') > src.count('}'):
            continue        # wait for closing brace

        buf = []
        if not src.strip():
            continue

        # ── let binding: let x = expr ──────────────────────────────────────
        if src.strip().startswith('let '):
            rest = src.strip()[4:]
            if '=' in rest:
                var_name, expr_src = rest.split('=', 1)
                var_name = var_name.strip()
                try:
                    result = _eval_src(expr_src.strip(), env)
                    env[var_name] = result
                    print(f"  {var_name} =")
                    print(format_ok(result))
                except Exception as e:
                    print(format_error(expr_src, e))
            else:
                print("[ERROR] let syntax: let name = expr")
            continue

        # ── expression evaluation ──────────────────────────────────────────
        try:
            result = _eval_src(src, env)
            print(format_ok(result))
        except Exception as e:
            print(format_error(src, e))


# ──────────────────────────────────────────────────────────────────────────────
# 6. SCRIPT MODE  (evaluate expression from argv)
# ──────────────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args or args == ['--repl']:
        run_repl()
        return

    src = ' '.join(args)
    try:
        result = _eval_src(src, {})
        print(format_ok(result))
    except Exception as e:
        print(format_error(src, e))
        sys.exit(1)


if __name__ == '__main__':
    main()
