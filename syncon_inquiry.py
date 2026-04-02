"""
syncon_inquiry.py — SynthOmnicon General-Purpose Inquiry Loop
=============================================================
An agentic loop that gives a model free rein to apply the SynthOmnicon
primitive grammar to any question. The model encodes systems, computes
distances, finds cross-domain analogs, asks its own follow-up questions,
and records insights — iterating until it converges on structural understanding.

Unlike synthon_agent.py (which targets a specific molecular design goal),
this loop is open-ended: the model steers the inquiry.

The loop runs in two phases:

  **Phase 1 — Grammatical analysis (tool-enabled):**
  1.  Seed question / topic → model receives it with full primitive reference
  2.  Model calls tools freely: encode, distance, lookup, ask_question, record_insight
  3.  Any question pushed via ask_question feeds the next iteration
  4.  Model emits CONCLUDE when it has sufficient structural understanding,
      followed by a synthesis that directly answers the original question
  5.  Session catalog accumulates — encodings persist across iterations

  **Phase 2 — Speculation (tool-free, automatic):**
  6.  Immediately after CONCLUDE, a second tool-free LLM call is made.
      The model is released from primitive discipline and asked to speculate
      openly on how the request or object might actually be realised, built,
      or approached in the world — using the grammar's verdict as a launching
      point, not a constraint. The four speculation axes are:
        · What materials, processes, institutions, or technologies are needed?
        · What intermediate steps or milestones would the path require?
        · Are there existing near-analogs that could be adapted?
        · What is the most non-obvious realization path the grammar suggests?
  7.  Speculation text is stored in the concluding IterationRecord and
      displayed at the end of the session summary under a SPECULATION header.

Tools available to the model:
  Encoding & distance:
  • encode_system        — register a system as a synthon tuple in the session
  • compute_distance     — weighted Euclidean distance + per-primitive breakdown
  • lookup_catalog       — find catalog entries matching a keyword
  • list_catalog         — list all currently encoded systems

  Algebra (composition):
  • compute_meet         — lattice meet A∧B: shared primitive floor
  • compute_join         — lattice join A∨B: minimal upper bound
  • compute_tensor       — tensor product A⊗B: structural composition
  • find_analogies       — nearest catalog neighbors by distance

  Probes:
  • phi_c_probe          — test whether a system is at criticality (Phi_c)
  • topo_protection_probe — test topological protection class (Omega)

  Decomposition:
  • project              — project onto a primitive subset
  • primitive_peel       — strip one primitive to minimum; return residual
  • principal_decomp     — join-irreducible atoms (minimal building blocks)
  • retrosynthetic_path  — trace back to structural baseline step by step

  Meta:
  • ask_question         — push a follow-up question onto the inquiry queue
  • record_insight       — record a structured insight (TOPO / DIAPH / ONTO plane); returns insight_id
  • revise_insight       — update a previously recorded insight by its insight_id
  • search_insights      — search the persistent insight library from prior sessions

Providers (same routing as synthon_agent.py):
  "anthropic"   — Anthropic SDK + ANTHROPIC_API_KEY  (default)
  "openai"      — OpenAI SDK + OPENAI_API_KEY
  "deepseek"    — OpenAI-compatible + DEEPSEEK_API_KEY
  "qwen"        — OpenAI-compatible + QWEN_API_KEY
  "gemini"      — Google Gemini OpenAI-compat + GOOGLE_API_KEY
                  Default model: gemini-2.0-flash
  "mistral"     — Mistral AI + MISTRAL_API_KEY
                  Default model: mistral-large-latest
  "openrouter"  — OpenRouter + OPENROUTER_API_KEY
                  Default model: google/gemini-2.5-pro (override with SYNCON_MODEL)
                  Optional: OPENROUTER_REFERER, OPENROUTER_TITLE env vars for routing headers.
  "local"       — OpenAI-compatible at localhost:11434/v1  (ollama / LM Studio / vLLM)
                  Set LOCAL_MODEL_URL env var to override the endpoint.
                  Set LOCAL_API_KEY env var for servers that require a key.

Usage:
    from syncon_inquiry import SynconInquiryLoop
    loop = SynconInquiryLoop("What is the primitive distance between consciousness and quantum measurement?")
    results = loop.run()

    # Or: from the CLI
    python syncon_inquiry.py "What structural features distinguish life from non-life?"
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import textwrap
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from rich.console import Console as _RichConsole
    _console = _RichConsole(highlight=False)
    def _print(*args, **kwargs):
        _console.print(*args, **kwargs)
except ImportError:
    _console = None  # type: ignore
    _MARKUP_RE = re.compile(r'\[/?[\w .#_]+\]')
    def _print(*args, **kwargs):
        clean = [_MARKUP_RE.sub('', a) if isinstance(a, str) else a for a in args]
        print(*clean, **kwargs)

# ── Canonical → display symbol map (reverse of _SYMBOL_MAP, applied to output) ─
# Applied left-to-right so longer tokens (e.g. "Omega_Z2") are replaced before
# shorter prefixes ("Omega_Z").
_DISPLAY_MAP: List[tuple] = [
    # Gamma values (G_ → Γ_)
    ("G_and",       "Γ_and"),
    ("G_or",        "Γ_or"),
    ("G_seq",       "Γ_seq"),
    ("G_broad",     "Γ_broad"),
    ("G_disc",      "Γ_disc"),
    # Phi values (longer/more specific first)
    ("Phi_c_complex", "Φ_c^ℂ"),
    ("Phi_super",   "Φ_sup"),
    ("Phi_sub",     "Φ_sub"),
    ("Phi_EP",      "Φ_EP"),
    ("Phi_c",       "Φ_c"),
    # Omega values (longer first to avoid partial matches)
    ("Omega_NA",    "Ω_NA"),
    ("Omega_Z2",    "Ω_Z₂"),
    ("Omega_Z",     "Ω_Z"),
    ("Omega_C",     "Ω_C"),
    ("Omega_0",     "Ω_0"),
    # Granularity scope
    ("G_aleph",     "G_ℵ"),
    ("G_beth",      "G_ℶ"),
    ("G_gimel",     "G_ℷ"),
    # Fidelity
    ("F_hbar",      "F_ℏ"),
    ("F_ell",       "F_ℓ"),
    # Dimensionality
    ("D_infty",     "D_∞"),
    ("D_triangle",  "D_△"),
    ("D_wedge",     "D_▽"),
    # Topology
    ("T_bowtie",    "T_⋈"),
    ("T_box",       "T_⊠"),
    ("T_in",        "T_∈"),
    # Relational
    ("R_dagger",    "R_†"),
    # Chirality
    ("H_inf",       "H_∞"),
    # Stoichiometry
    ("one_one",     "1:1"),
    ("n_n",         "n:n"),
    ("n_m",         "n:m"),
]


def _render(text: str) -> str:
    """Expand canonical primitive values to their Unicode display symbols."""
    for canon, display in _DISPLAY_MAP:
        text = text.replace(canon, display)
    return text

# ── Import distance machinery from space_search pipeline ──────────────────────

_SPACE_SEARCH = os.path.join(os.path.dirname(__file__), "space_search")
if _SPACE_SEARCH not in sys.path:
    sys.path.insert(0, _SPACE_SEARCH)

from primitives import (  # type: ignore
    ORDINALS,
    WEIGHTS,
    PRIMITIVE_ORDER,
    SYNTHONS,
    tuple_distance,
    directed_distance,
    breakdown,
    mahalanobis_distance,
    build_metric_tensor,
)

# Pre-build metric tensor once at import time (catalog must exist on disk)
try:
    _METRIC_G = build_metric_tensor()
except Exception:
    _METRIC_G = None

# ── Translation cost (structural→classical) ────────────────────────────────────
try:
    import math as _math
    _FHBAR_THRESHOLD_NATS: float = _math.log(19)   # ≈ 2.9444 nats
    _CRITICALITY_LIFT_NATS: float = _math.log(10)  # ≈ 2.3026 nats
    _COHERENCE_LOSS_HBAR_ETH: float = -_math.log(0.75)  # ≈ 0.2877 nats
    _COHERENCE_LOSS_ETH_ELL: float  = -_math.log(0.60)  # ≈ 0.5108 nats
    _INTERACTION_LOSS_NONCLASSICAL: float = _math.log(2)  # ≈ 0.6931 nats
    _TRANSLATE_AVAILABLE = True
except Exception:
    _TRANSLATE_AVAILABLE = False


def _translation_cost_from_dict(
    s: Dict[str, str],
    mutual_info_nats: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compute structural→classical translation cost from a space_search primitives dict.

    Returns a dict with keys: coherence_loss, criticality_loss, interaction_cost, total (all nats).
    Works directly on the {prim: val} string format — no Synthon object needed.

    Cost sources:
      F_hbar (+ I < ln 19)  →  coherence_loss = -ln(0.75)  ≈ 0.288 nat
      F_eth  (+ I < ln 19)  →  coherence_loss = -ln(0.60)  ≈ 0.511 nat
      Phi_c                 →  criticality_loss = ln(10)   ≈ 2.303 nat
      G_broad               →  interaction_cost = ln(2)   ≈ 0.693 nat
    """
    if not _TRANSLATE_AVAILABLE:
        return {"coherence_loss": 0.0, "criticality_loss": 0.0, "interaction_cost": 0.0, "total": 0.0}

    coherence = 0.0
    criticality = 0.0
    interaction = 0.0

    f_val = s.get("F", "")
    if mutual_info_nats is not None and mutual_info_nats < _FHBAR_THRESHOLD_NATS:
        if f_val == "F_hbar":
            coherence = _COHERENCE_LOSS_HBAR_ETH
        elif f_val == "F_eth":
            coherence = _COHERENCE_LOSS_ETH_ELL

    if s.get("Phi") == "Phi_c":
        criticality = _CRITICALITY_LIFT_NATS

    if s.get("Gamma") == "G_broad":
        interaction = _INTERACTION_LOSS_NONCLASSICAL

    total = coherence + criticality + interaction
    return {
        "coherence_loss": round(coherence, 4),
        "criticality_loss": round(criticality, 4),
        "interaction_cost": round(interaction, 4),
        "total": round(total, 4),
    }


# ── Provider routing (mirrors synthon_agent.py) ───────────────────────────────

_OPENAI_BASE_URLS: Dict[str, str] = {
    "openai":      "https://api.openai.com/v1",
    "deepseek":    "https://api.deepseek.com/v1",
    "qwen":        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "mistral":     "https://api.mistral.ai/v1",
    "google":      "https://generativelanguage.googleapis.com/v1beta/openai/",
    "gemini":      "https://generativelanguage.googleapis.com/v1beta/openai/",
    "openrouter":  "https://openrouter.ai/api/v1",
    "local":       os.environ.get("LOCAL_MODEL_URL", "http://localhost:11434/v1"),
}

# Default path for the merged2 SynthOmnicon fine-tune
_MERGED2_PATH = os.path.join(
    os.path.dirname(__file__),
    "INFERRED/output/synthonicon_qlora/merged2/merged_model"
)

# Persistent cross-session catalog
CATALOG_PATH = os.path.join(os.path.dirname(__file__), "syncon_catalog.json")

# Persistent cross-session insight library
INSIGHTS_PATH = os.path.join(os.path.dirname(__file__), "syncon_insights.json")

# Persistent cross-session promotion knowledge base
PROMOTIONS_PATH = os.path.join(os.path.dirname(__file__), "syncon_promotions.json")

_PROVIDER_API_KEY_ENV: Dict[str, str] = {
    "google":      "GOOGLE_API_KEY",
    "gemini":      "GOOGLE_API_KEY",
    "mistral":     "MISTRAL_API_KEY",
    "openrouter":  "OPENROUTER_API_KEY",
    "local":       "LOCAL_API_KEY",
}


# ── Valid primitive values (for model reference and validation) ───────────────

VALID_VALUES: Dict[str, List[str]] = {p: list(ORDINALS[p].keys()) for p in PRIMITIVE_ORDER}

# ── Tensor composition rules ───────────────────────────────────────────────────
# For each primitive: "min" = bottleneck (weaker partner limits composed system),
#                    "max" = union (stronger/broader partner determines composed system)
_TENSOR_RULES: Dict[str, str] = {
    "D":     "max",  # dimensionality union — composed system spans all dims of both
    "T":     "max",  # topology promotes to most complex structure
    "R":     "max",  # recognition mode promotes to most dynamic
    "P":     "min",  # parity — asymmetry propagates (P_asym=1 wins)
    "F":     "min",  # fidelity bottleneck — limited by weaker fidelity partner
    "K":     "max",  # kinetic bottleneck — limited by slowest/most trapped step
    "G":     "max",  # scope union — composed system has broadest scope
    "Gamma": "max",  # grammar promotes to most expressive
    "Phi":   "max",  # criticality promotes — composed system at least as critical
    "H":     "max",  # chirality deepens — deeper temporal asymmetry dominates
    "S":     "max",  # stoichiometry promotes to most asymmetric
    "Omega": "max",  # topological protection — strongest class wins
}

_PRIMITIVE_REFERENCE = textwrap.dedent("""\
D  — Dimensionality/holography
    D_wedge       molecular / local
    D_triangle    supramolecular / intermediate
    D_infty       temporal / process / unbounded
    D_holo        holographic (boundary encodes bulk)

T  — Topology
    T_network     general network / graph
    T_in          nested / hierarchical containment
    T_bowtie      bowtie / dual-cone (confined, massive)
    T_box         box / closed compact
    T_holo        holographic topology

R  — Relational mode
    R_super       superset / containment relation
    R_cat         categorical / classification
    R_dagger      dynamic / catalytic / time-reversible
    R_lr          left-right / chiral / directed

P  — Parity / symmetry
    P_asym        fully asymmetric
    P_psi         pseudo-symmetric
    P_pm          plus-minus symmetric (Z₂)
    P_sym         fully symmetric
    P_pm_sym      exact Z₂ at a critical point — the Frobenius special condition (μ∘δ=id); use when the plus-minus symmetry is provably exact at Φ_c, not merely approximate

F  — Fidelity / interaction scale
    F_ell         low  (ℓ-scale, classical, dissipative)
    F_eth         medium (ħ-scale, quantum-classical interface)
    F_hbar        high (ħ-scale, quantum-coherent)

K  — Computational / kinetic character
    K_fast        P-class (polynomial, local, fast)
    K_mod         NP-boundary (moderate, critical complexity)
    K_slow        K_slow (temporally deep, integrative)
    K_trap        MBL / trapped (many-body localized, non-ergodic)

G  — Scope / correlation length
    G_beth        local (Beth-scale, finite range)
    G_gimel       mesoscale (Gimel-scale, intermediate)
    G_aleph       global / non-local (Aleph-scale, unbounded)

Γ  — Interaction grammar / causation
    G_and         conjunctive (AND — all inputs required)
    G_or          disjunctive (OR — any input sufficient)
    G_seq         sequential / causal chain
    G_broad       broadcast / one-to-many

Φ  — Criticality / phase
    Phi_sub         subcritical (ordered, below transition)
    Phi_c           critical: real-axis Hermitian fixed point (standard universality, e.g. Ising 3D)
    Phi_c_complex   critical: complex-axis critical point (Lee-Yang edge, complex RG fixed point; accessible only via analytic continuation; use when the critical point is at a non-real parameter value)
    Phi_EP          exceptional-point criticality: non-Hermitian eigenvector coalescence; no standard ν, η; K_fast signature
    Phi_super       supercritical (disordered, post-transition)

H  — Chirality / temporal depth (arrow of time)
    H0            achiral / time-symmetric
    H1            weakly chiral / shallow temporal integration
    H2            strongly chiral / deep temporal memory
    H_inf         maximally chiral / irreversible (Big Bang limit)

S  — Stoichiometry
    one_one       1:1
    n_n           n:n  (symmetric many-body)
    n_m           n:m  (asymmetric many-body)

Ω  — Topological protection (derived)
    Omega_0       none
    Omega_Z2      Z₂ protection (binary topological invariant)
    Omega_Z       Z protection (integer winding number)
""")


# ── RTF and symbol parsing ─────────────────────────────────────────────────────

def _strip_rtf(data: str) -> str:
    """
    Minimal RTF → plain text (no external dependencies).

    Handles the most common RTF constructs:
      • Hex character escapes: \\'xx
      • Control words with optional numeric param: \\word[-N]<space>
      • Control symbols: \\<non-alpha>
      • Braces delimiting RTF groups

    The result is normalised whitespace. Suitable for extracting human-readable
    text from simple RTF documents (notes, Word exports).
    """
    # Hex character escapes: \'xx → Unicode char
    data = re.sub(r"\\'([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), data)
    # Control words (e.g. \rtf1, \par, \b0, \f2) — strip including trailing space
    data = re.sub(r"\\[a-zA-Z]+[-\d]*[ ]?", "", data)
    # Control symbols (e.g. \*, \~, \|)
    data = re.sub(r"\\[^a-zA-Z\n]", "", data)
    # Remove RTF braces
    data = data.replace("{", "").replace("}", "")
    # Normalise runs of whitespace (preserve newlines as spaces)
    data = re.sub(r"[ \t]+", " ", data)
    return data.strip()


# Display-notation → canonical grammar value string
# Keys are what appears in documents/output; values are what ORDINALS/encode() expects.
_SYMBOL_MAP: Dict[str, str] = {
    # ── Dimensionality ─────────────────────────────────────────────────────────
    "D_△":        "D_triangle",
    "D_▽":        "D_wedge",
    "D_∞":        "D_infty",
    # ── Topology ───────────────────────────────────────────────────────────────
    "T_∈":        "T_in",
    "T_⊠":        "T_box",
    "T_⋈":        "T_bowtie",
    # ── Relational ─────────────────────────────────────────────────────────────
    "R_†":        "R_dagger",
    # ── Parity ─────────────────────────────────────────────────────────────────
    "P_±":        "P_pm",
    "P_±^{sym}":  "P_pm_sym",
    "P_ψ":        "P_psi",
    # ── Fidelity ───────────────────────────────────────────────────────────────
    "F_ℓ":        "F_ell",
    "F_ℏ":        "F_hbar",
    # ── Granularity ────────────────────────────────────────────────────────────
    "G_ℵ":        "G_aleph",
    "G_ℶ":        "G_beth",
    "G_ℷ":        "G_gimel",
    # ── Gamma (Γ_ prefix → G_ prefix) ─────────────────────────────────────────
    "Γ_and":      "G_and",
    "Γ_or":       "G_or",
    "Γ_seq":      "G_seq",
    "Γ_broad":    "G_broad",
    "Γ_disc":     "G_disc",     # discretized; seen in some encodings
    # ── Criticality ────────────────────────────────────────────────────────────
    "Φ_c^ℂ":      "Phi_c_complex",
    "Φ_c":        "Phi_c",
    "Φ_sub":      "Phi_sub",
    "Φ_super":    "Phi_super",
    "Φ_sup":      "Phi_super",
    "Φ_EP":       "Phi_EP",
    # ── Chirality ──────────────────────────────────────────────────────────────
    "H_∞":        "H_inf",
    # ── Stoichiometry (display → canonical) ───────────────────────────────────
    "1:1":        "one_one",
    "1_1":        "one_one",
    "n:n":        "n_n",
    "n:m":        "n_m",
    # ── Omega ──────────────────────────────────────────────────────────────────
    "Ω_0":        "Omega_0",
    "Ω_Z":        "Omega_Z",
    "Ω_Z2":       "Omega_Z2",
    "Ω_{Z_2}":    "Omega_Z2",
    "Ω_C":        "Omega_C",
    "Ω_NA":       "Omega_NA",
}

# Extended valid values for validation (ORDINALS only has Omega 0/Z2/Z;
# Omega_C and Omega_NA appear in documents and models.py).
_EXTENDED_VALID: Dict[str, List[str]] = {
    **{p: list(ORDINALS[p].keys()) for p in PRIMITIVE_ORDER},
    "Omega": ["Omega_0", "Omega_Z2", "Omega_Z", "Omega_C", "Omega_NA"],
}


def _normalize_value(raw: str) -> str:
    """
    Normalise a display-notation primitive value to its canonical grammar string.

    Resolution order:
      1. Direct lookup in _SYMBOL_MAP (e.g. "Γ_seq" → "G_seq")
      2. Substring substitution for Unicode glyphs embedded in longer tokens
      3. Return raw unchanged (already canonical, e.g. "D_holo", "Phi_c")
    """
    s = raw.strip()
    if s in _SYMBOL_MAP:
        return _SYMBOL_MAP[s]
    # Substitute any matching Unicode substrings (longest first to avoid partial matches)
    for uni, canon in sorted(_SYMBOL_MAP.items(), key=lambda kv: -len(kv[0])):
        if len(uni) > 1 and uni in s:
            s = s.replace(uni, canon)
    return s


def _parse_synthon_tuples(text: str) -> List[Tuple[Optional[str], Dict[str, str]]]:
    """
    Extract SynthOmnicon tuple notation from arbitrary text.

    Recognises both unlabelled and labelled forms:
      ⟨val; val; …; val⟩
      some_name: ⟨val; val; …; val⟩

    Also accepts ASCII angle brackets < > as fallback delimiters.

    Returns a list of (label_or_None, primitives_dict) for every complete
    12-primitive tuple found. Partial tuples (≠ 12 values) are silently skipped.

    The label (if present) is taken from the identifier immediately preceding
    the opening bracket on the same line.
    """
    # Match optional label then ⟨...⟩ or <...>; allow newlines inside
    pattern = re.compile(
        r"(?:([A-Za-z_][\w\s]{0,60}?):\s*)?[⟨<]([^⟩>\{\}]{10,})[⟩>]",
        re.DOTALL,
    )
    results: List[Tuple[Optional[str], Dict[str, str]]] = []

    for m in pattern.finditer(text):
        label: Optional[str] = m.group(1).strip() if m.group(1) else None
        inner = m.group(2)
        parts = [p.strip() for p in re.split(r";", inner) if p.strip()]
        if len(parts) != len(PRIMITIVE_ORDER):
            continue
        primitives: Dict[str, str] = {}
        for prim, raw_val in zip(PRIMITIVE_ORDER, parts):
            # Strip "PRIM=" prefix if present (e.g. "D=D_holo")
            if "=" in raw_val:
                raw_val = raw_val.split("=", 1)[1].strip()
            primitives[prim] = _normalize_value(raw_val)
        results.append((label, primitives))

    return results


def _load_seed_text(seed: str) -> str:
    """
    If *seed* is a path to an existing file, load and return its text content.

    • .rtf files (or any file whose content starts with ``{\\rtf``) are
      stripped of RTF markup before returning.
    • All other files are returned as UTF-8 text (latin-1 fallback).

    If *seed* does not resolve to an existing file it is returned unchanged,
    so callers can pass either a literal question string or a file path
    without distinguishing them.
    """
    candidate = seed.strip()
    if len(candidate) < 512 and os.path.isfile(candidate):
        with open(candidate, "rb") as fh:
            raw_bytes = fh.read()
        try:
            text = raw_bytes.decode("utf-8", errors="replace")
        except Exception:
            text = raw_bytes.decode("latin-1", errors="replace")
        if candidate.lower().endswith(".rtf") or text.lstrip().startswith("{\\rtf"):
            return _strip_rtf(text)
        return text
    return seed


# ── Tool schema ───────────────────────────────────────────────────────────────

_TOOLS_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": "encode_system",
            "description": (
                "Register a system or concept as a synthon tuple in the session catalog. "
                "You must specify ALL 12 primitive values using the exact strings from the "
                "primitive reference. Returns the registered name and tuple notation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Short unique identifier for this system (e.g. 'consciousness', 'black_hole', 'language')"},
                    "description": {"type": "string", "description": "One-sentence description of what is being encoded"},
                    "D":     {"type": "string", "enum": VALID_VALUES["D"]},
                    "T":     {"type": "string", "enum": VALID_VALUES["T"]},
                    "R":     {"type": "string", "enum": VALID_VALUES["R"]},
                    "P":     {"type": "string", "enum": VALID_VALUES["P"]},
                    "F":     {"type": "string", "enum": VALID_VALUES["F"]},
                    "K":     {"type": "string", "enum": VALID_VALUES["K"]},
                    "G":     {"type": "string", "enum": VALID_VALUES["G"]},
                    "Gamma": {"type": "string", "enum": VALID_VALUES["Gamma"]},
                    "Phi":   {"type": "string", "enum": VALID_VALUES["Phi"]},
                    "H":     {"type": "string", "enum": VALID_VALUES["H"]},
                    "S":     {"type": "string", "enum": VALID_VALUES["S"]},
                    "Omega": {"type": "string", "enum": VALID_VALUES["Omega"]},
                },
                "required": ["name", "description", "D", "T", "R", "P", "F", "K", "G", "Gamma", "Phi", "H", "S", "Omega"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_distance",
            "description": (
                "Compute the weighted Euclidean distance between two encoded systems. "
                "Returns scalar distance and per-primitive breakdown sorted by contribution. "
                "Use this to identify which primitives account for structural divergence."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name_a": {"type": "string", "description": "Name of first encoded system"},
                    "name_b": {"type": "string", "description": "Name of second encoded system"},
                },
                "required": ["name_a", "name_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_catalog",
            "description": (
                "Search the catalog (built-in + session) for systems matching a keyword. "
                "Returns names and tuple notations of matching entries."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Search term (partial name match)"},
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_catalog",
            "description": "List all currently encoded systems in the session catalog plus built-ins.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_question",
            "description": (
                "Push a follow-up question onto the inquiry queue. "
                "This question will be fed back to you in the next iteration. "
                "Use this when you discover a structural question that deserves its own focused pass."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The follow-up question to investigate next"},
                    "motivation": {"type": "string", "description": "Why this question is structurally important"},
                },
                "required": ["question", "motivation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_insight",
            "description": (
                "Record a structural insight from the current iteration. "
                "Label it with the appropriate claim plane: "
                "TOPO (derivable from axioms alone), "
                "DIAPH (requires empirical encoding), or "
                "ONTO (ontological/philosophical implication)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The insight statement"},
                    "plane": {"type": "string", "enum": ["TOPO", "DIAPH", "ONTO"]},
                    "confidence": {"type": "string", "enum": ["high", "medium", "speculative"]},
                    "systems": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional list of encoded system names this insight is about. "
                            "When provided, the translation cost (structural→classical) is "
                            "computed per system and attached to the insight record."
                        ),
                    },
                },
                "required": ["text", "plane", "confidence"],
            },
        },
    },
    # ── Algebra ──────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "compute_meet",
            "description": (
                "Lattice meet (A ∧ B): shared primitive floor of two systems. "
                "Returns the most conservative value for each primitive — the structural "
                "ground both systems share without qualification. "
                "Use to identify what two systems have in common at the deepest level."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name_a": {"type": "string", "description": "First encoded system"},
                    "name_b": {"type": "string", "description": "Second encoded system"},
                },
                "required": ["name_a", "name_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_join",
            "description": (
                "Lattice join (A ∨ B): minimal upper bound of two systems. "
                "Returns the most expansive value for each primitive — the minimal system "
                "that structurally contains both A and B. "
                "Use to identify the most demanding requirements across two systems."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name_a": {"type": "string", "description": "First encoded system"},
                    "name_b": {"type": "string", "description": "Second encoded system"},
                },
                "required": ["name_a", "name_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_tensor",
            "description": (
                "Tensor product (A ⊗ B): structural composition of two systems. "
                "F and P are bottleneck primitives (weaker partner limits composite). "
                "K is a kinetic bottleneck (slowest step limits composite). "
                "D, G, T, R, Phi, H, S, Omega, Gamma are union/promote (strongest wins). "
                "Returns the composed system notation plus bottleneck and union analysis. "
                "Use to predict what a combined or interacting system looks like structurally."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name_a": {"type": "string", "description": "First encoded system"},
                    "name_b": {"type": "string", "description": "Second encoded system"},
                },
                "required": ["name_a", "name_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_analogies",
            "description": (
                "Find the most structurally similar systems in the catalog to the named system. "
                "Returns top N nearest neighbors by primitive distance. "
                "Use to discover cross-domain structural analogs and unexpected connections."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the encoded system to find analogs for"},
                    "limit": {"type": "integer", "description": "Number of analogs to return (default 5)", "default": 5},
                },
                "required": ["name"],
            },
        },
    },
    # ── Probes ───────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "phi_c_probe",
            "description": (
                "Test whether a system is at criticality. Returns the Phi value and criticality tier. "
                "Three critical variants: Phi_c (real-axis Hermitian, standard universality), "
                "Phi_c_complex (complex-axis: critical point at complex parameter value, e.g. Lee-Yang edge, zeta zeros), "
                "Phi_EP (exceptional-point: non-Hermitian eigenvector coalescence, K_fast signature). "
                "All three are at criticality; they differ in the structure of the critical manifold."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the encoded system to probe"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ouroborics",
            "description": (
                "Classify a system into its Frobenius ouroboricity tier (O_0 / O_1 / O_2 / O_2_dag / O_inf). "
                "Rules (applied in priority order): "
                "R1: Phi_c or Phi_c_complex AND P_pm_sym → O_inf (special Frobenius: mu∘delta=id, exact proved Z₂ symmetry). "
                "R2: Phi ∈ {Phi_sub, Phi_super, Phi_EP} → O_0 (no self-referential loop possible, subcritical or exceptional-point). "
                "R3: Phi_c (or Phi_c_complex) AND Omega_0 → O_1 (self-referential but no topological protection). "
                "R4: Phi_c (or Phi_c_complex) AND Omega ≠ Omega_0 AND D ∈ {D_wedge, D_holo, D_triangle} → O_2 (bounded ouroboricity). "
                "R5: Phi_c (or Phi_c_complex) AND Omega ≠ Omega_0 AND D = D_infty → O_2_dag (unbounded, directed ouroboricity). "
                "Can also run a census across the entire catalog when name='__all__'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the encoded system to classify, or '__all__' for a full catalog census",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "topo_protection_probe",
            "description": (
                "Test whether a system has topological protection (Omega ≠ Omega_0). "
                "Returns the Omega class and protection status. "
                "Omega_Z: integer winding number (Kitaev chain, SSH). "
                "Omega_Z2: binary protection (topological insulators). "
                "Omega_0: no protection — interactions are structurally unguarded."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the encoded system to probe"},
                },
                "required": ["name"],
            },
        },
    },
    # ── Decomposition ────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "project",
            "description": (
                "Project a system onto a subset of primitives. "
                "Returns only the specified primitive values, ignoring the rest. "
                "Use to isolate a structural subspace — e.g. project onto [F, K, Phi] "
                "to examine only the existence-tier primitives."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the encoded system"},
                    "primitives": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["D", "T", "R", "P", "F", "K", "G", "Gamma", "Phi", "H", "S", "Omega"]},
                        "description": "List of primitives to project onto",
                    },
                },
                "required": ["name", "primitives"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "primitive_peel",
            "description": (
                "Peel one primitive to its minimum value and return the residual system. "
                "Use to isolate what a system looks like with one structural requirement removed. "
                "Peeling F to F_ell asks: what if fidelity were minimal? "
                "Peeling Phi to Phi_sub asks: what if criticality were removed?"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the encoded system"},
                    "primitive": {
                        "type": "string",
                        "enum": ["D", "T", "R", "P", "F", "K", "G", "Gamma", "Phi", "H", "S", "Omega"],
                        "description": "The primitive to peel to its minimum value",
                    },
                },
                "required": ["name", "primitive"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "principal_decomp",
            "description": (
                "Decompose a system into join-irreducible atoms — the minimal structural building blocks. "
                "Each atom contributes exactly one primitive's structural content. "
                "The join of all atoms reconstructs the original system. "
                "Use to identify which primitives are doing structural work and how much."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the encoded system to decompose"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrosynthetic_path",
            "description": (
                "Trace a system back to structural baseline by peeling one primitive per step. "
                "Each step removes the most structurally significant remaining requirement. "
                "Reading backward: shows which primitive constraints were added to build this system. "
                "Reading forward: shows the synthesis path from simplest baseline to target."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the encoded system to trace back"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "revise_insight",
            "description": (
                "Revise a previously recorded insight. Use when you learn something that corrects or "
                "refines an earlier structural finding. Provide the insight_id returned by record_insight. "
                "Any field left out is kept unchanged."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "insight_id": {"type": "string", "description": "The 12-char ID returned by record_insight"},
                    "text": {"type": "string", "description": "Revised insight text (omit to keep existing)"},
                    "plane": {
                        "type": "string",
                        "enum": ["TOPO", "DIAPH", "ONTO"],
                        "description": "Revised plane classification (omit to keep existing)",
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Revised confidence (omit to keep existing)",
                    },
                },
                "required": ["insight_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_insights",
            "description": (
                "Search the persistent insight library for insights from all previous sessions. "
                "Use to find prior structural findings before recording a potentially duplicate insight, "
                "or to retrieve insight IDs for revision."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Keyword to search in insight text and source seed",
                    },
                    "plane": {
                        "type": "string",
                        "enum": ["TOPO", "DIAPH", "ONTO"],
                        "description": "Optional plane filter",
                    },
                },
                "required": ["keyword"],
            },
        },
    },
    # ── Veracity / conflict distance ─────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "compute_conflict_distance",
            "description": (
                "Compute the conflict distance d_c between two encodings of the SAME system "
                "— one holistic (top-down, functional: what tuple is required for this system's "
                "claimed behavior?) and one compositional (bottom-up: tensor product of components). "
                "Returns d_c = sqrt(|conflict_set|), the conflict set (primitives that differ), "
                "per-primitive conflict type (aspirational = holistic higher, reductive = holistic lower), "
                "veracity class (transparent / near-grounded / partial-emergence / aspirational), "
                "and one falsifiable emergence claim per conflicted primitive. "
                "Both systems must already be encoded. "
                "Use this whenever you encode a system two ways to test whether its claimed behavior "
                "is supported by its construction."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name_holistic": {
                        "type": "string",
                        "description": "Name of the holistic encoding (what the system claims to do)",
                    },
                    "name_compositional": {
                        "type": "string",
                        "description": "Name of the compositional encoding (tensor product of components)",
                    },
                },
                "required": ["name_holistic", "name_compositional"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "emergence_frontier",
            "description": (
                "Report the emergence frontier for this session: which primitives appear most "
                "frequently in conflict sets across all compute_conflict_distance calls made so far. "
                "A primitive on the frontier is the structural address of an unresolved emergence "
                "question in the domain under investigation. "
                "Use after multiple compute_conflict_distance calls to identify the deepest "
                "unresolved structural questions in the session."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    # ── Promotion signature / inverse encoding ────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "compute_promotions",
            "description": (
                "Compute the promotion signature Σ(source→target): the set of primitives that were "
                "lifted (promoted in ordinal rank) when moving from source to target. "
                "Also returns demotions and unchanged primitives. "
                "Use this to identify WHICH primitives changed — and in which direction — "
                "when a system exhibits anomalous or emergent behavior relative to its baseline. "
                "Typical workflow: encode baseline system, encode anomalous system, call this tool "
                "to get the delta, then call predict_from_promotions or register_promotion_pattern."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name_source": {
                        "type": "string",
                        "description": "Name of the source (baseline) synthon in the session catalog.",
                    },
                    "name_target": {
                        "type": "string",
                        "description": "Name of the target (anomalous/promoted) synthon in the session catalog.",
                    },
                },
                "required": ["name_source", "name_target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "predict_from_promotions",
            "description": (
                "Given a promotion signature (list of promoted primitive names), look up the "
                "persistent promotion knowledge base for matching patterns and return ranked "
                "behavior predictions. Each match reports: the known behavior, which primitives "
                "overlap, coverage (how much of the known pattern is present in the query), "
                "relevance (how much of the query is explained by the known pattern), and which "
                "query primitives are novel (not yet accounted for by any known pattern). "
                "Use this as the inverse-encoding step: 'given these promotions, what behaviors "
                "are predicted?' The KB is built from register_promotion_pattern calls across sessions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "promoted_primitives": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "List of primitive names (not values) that were promoted, "
                            "e.g. [\"T\", \"H\", \"F\"]. Use the single-letter or Gamma/Phi/Omega "
                            "names as they appear in PRIMITIVE_ORDER."
                        ),
                    },
                },
                "required": ["promoted_primitives"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "register_promotion_pattern",
            "description": (
                "Register a confirmed promotion signature → behavior mapping in the persistent "
                "knowledge base. Call this after you have identified (via compute_promotions or "
                "structural analysis) that a specific set of primitive promotions from baseline "
                "reliably produces a named behavior. The KB persists across sessions — future "
                "predict_from_promotions calls will draw on these registered patterns. "
                "Do NOT register speculatively; only register when the promotion→behavior link "
                "is structurally well-grounded by the grammar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "promoted_primitives": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of primitive names that were promoted (e.g. [\"T\", \"H\"]).",
                    },
                    "behavior_description": {
                        "type": "string",
                        "description": "Short description of the emergent behavior explained by this promotion pattern.",
                    },
                    "example_system": {
                        "type": "string",
                        "description": "Optional: name of a canonical system in the catalog that exhibits this pattern.",
                    },
                },
                "required": ["promoted_primitives", "behavior_description"],
            },
        },
    },
]

# Anthropic format
_TOOLS_ANTHROPIC = [
    {
        "name": t["function"]["name"],
        "description": t["function"]["description"],
        "input_schema": t["function"]["parameters"],
    }
    for t in _TOOLS_OPENAI
]


def _build_gemini_tools():
    """Convert _TOOLS_OPENAI to a google-genai Tool object for native function calling."""
    try:
        from google.genai import types as _gt
    except ImportError:
        return None
    declarations = []
    for tool in _TOOLS_OPENAI:
        fn = tool["function"]
        # google-genai accepts raw JSON schema dicts for parameters
        declarations.append(
            _gt.FunctionDeclaration(
                name=fn["name"],
                description=fn.get("description", ""),
                parameters=fn.get("parameters"),
            )
        )
    return _gt.Tool(function_declarations=declarations)


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT_TEMPLATE = textwrap.dedent("""\
<role>
You are a structural scientist operating inside the SynthOmnicon grammar — a
relational algebra of 12 primitives that encodes any system as a directed
relational operator: ⟨D; T; R; P; F; K; G; Γ; Φ; H; S; Ω⟩.

You investigate questions by applying this grammar: encoding systems, computing
structural distances, identifying which primitives drive divergence, finding
cross-domain analogs, and recording insights.

**You are encouraged to wander.** The grammar is a compass, not a map. Follow
unexpected structural neighbors, chase surprising distances, encode tangential
systems that occur to you, push into adjacent domains. The best structural
discoveries are rarely on the direct path from question to answer. Take
detours. Let analogies pull you sideways. The route is yours.

The only constraint: **you must return.** No matter how far the structure takes
you, you must deliver a direct answer to the original question before concluding.
</role>

<grammar_primacy>
**The primitives are the explanation. Use them as such.**

Do not explain results by translating them back into conventional disciplinary
language (physics, chemistry, biology, philosophy). The grammar already captures
what matters. When a system encodes as T_holo + G_broad + Phi_c, that triple IS
the explanation — not a code for "holographic processing plus broadcast
signaling plus criticality." Speak the grammar directly.

Concretely:
- DO say: "The dominant divergence is at T — T_network vs T_holo — which is the
  structural driver of the distance."
- DO NOT say: "This is like the holographic principle in physics, which states..."
- DO say: "The meet of these two systems yields Phi_c, meaning any composite
  must sit at criticality — it cannot be subcritical and contain both."
- DO NOT say: "Both systems are near a phase transition in the conventional
  thermodynamic sense..."

Conventional framing is a crutch. The grammar is self-sufficient. If the
primitives do not yet capture something, say so explicitly — that is a
grammar-extension finding, not a reason to import external vocabulary.
</grammar_primacy>

<task>
You **MUST** investigate the user's question using the tools provided. Suggested workflow — not a rigid script, adapt as the structure demands:

0. **Check prior work first.** Call `search_insights` on keywords from the question before encoding. The library has hundreds of insights from prior sessions — build on them rather than rediscovering. If a prior insight is close but subtly wrong, use `revise_insight` to update it rather than recording a duplicate.
1. Encode all relevant systems with `encode_system`.
2. Use `compute_distance` for structural comparison.
3. Use algebra tools (`compute_meet`, `compute_join`, `compute_tensor`) to compose or compare systems.
4. Use decomposition tools (`principal_decomp`, `retrosynthetic_path`, `project`, `primitive_peel`) to dissect structure.
5. Use probes (`phi_c_probe`, `topo_protection_probe`) to directly test structural hypotheses.
6. Use `find_analogies` to discover unexpected cross-domain structural neighbors. **Follow the ones that surprise you.**
7. Call `record_insight` for each structural finding (TOPO / DIAPH / ONTO plane). Before recording, `search_insights` on the topic to check for prior work — prefer refinement over duplication.
8. Call `ask_question` for sub-questions deserving a focused follow-up pass. Wander into them.
9. When you are ready: emit CONCLUDE on a line by itself, followed by a synthesis that **directly and completely answers the original question**. The synthesis must go beyond summarizing what the tools returned — derive structural conclusions, state what the grammar implies, and answer.

   After you emit CONCLUDE, you will enter a **speculation phase** — a free pass where you are no longer bound by the grammar's constraints. You will be invited to reason openly about how the request or object might actually be realised, built, or approached in the world, using what the grammar revealed as a launching point. No tool calls, no primitive discipline required — pure speculative thought about practical paths forward.

**Tool selection guidance:**
- Use `compute_meet` when asking "what do these two systems share?"
- Use `compute_join` when asking "what would a system containing both look like?"
- Use `compute_tensor` when asking "what does the composed/interacting system look like?"
- Use `principal_decomp` when asking "what are the irreducible components of this system?"
- Use `retrosynthetic_path` when asking "how was this system built up from primitives?"
- Use `project` when asking "what does this system look like in only the existence-tier [F,K,Phi] or cosmological-tier [D,T,R,P,G,Gamma,S,H] primitives?"
- Use `primitive_peel` when asking "what remains if we remove this one structural requirement?"
- Use `search_insights` when asking "what do we already know about this?" — do this early and often
- Use `lookup_catalog` when you need to find catalog entries matching a keyword (built-in + session)
- Use `list_catalog` when you need to see all currently encoded systems in the session
- Use `compute_conflict_distance` when a system has BOTH a holistic and compositional encoding
- Use `emergence_frontier` after multiple conflict distance computations to map the session's deepest unresolved questions
- Use `compute_promotions` to find which primitives were lifted when comparing a baseline to an anomalous system
- Use `predict_from_promotions` to look up known behaviors associated with a promotion signature
- Use `register_promotion_pattern` to record a confirmed promotion→behavior mapping in the persistent KB
- Use `ouroborics` when asking "can this system sustain a self-referential loop?", "is this a Frobenius algebra?", or "how does this system's ouroboricity tier compare to another's?" — or any time P_pm_sym or the Frobenius condition is relevant
- Use `ask_question` sparingly — the queue is capped at 8. Prefer depth over breadth: exhaust each question before queuing more. When the queue fills, synthesize and CONCLUDE rather than pushing more questions.
</task>

<ouroboricity>
**Ouroboricity — the Frobenius tier of a system**

Ouroboricity classifies whether and how deeply a system at criticality can sustain a self-referential loop — a structure that both generates and absorbs its own outputs. It is derived from three primitives: Φ (criticality), P (parity/symmetry), and Ω (topological protection), with D as tiebreaker.

**Tiers** (rules applied in strict priority order):

| Tier | Condition | Meaning |
|------|-----------|---------|
| O_inf | Φ_c (or Φ_{{c,complex}}) **and** P_pm_sym | Special Frobenius: μ∘δ = id exactly. The system's self-referential loop is perfectly closed — it is its own dual. Finite, proved, algebraically exact. |
| O_0 | Φ ∈ {{Φ_sub, Φ_super, Φ_EP}} | No ouroboricity. Cannot form a self-referential critical loop. Subcritical systems are too ordered; supercritical too disordered; exceptional-point systems lose the symmetry at the coalescence. |
| O_1 | Φ_c **and** Ω_0 | Self-referential loop is possible (critical) but unprotected — any deformation can break it. The loop exists but is not topologically locked. |
| O_2 | Φ_c **and** Ω ≠ Ω_0 **and** D bounded (D_wedge, D_holo, D_triangle) | Critical, topologically protected loop, within a bounded domain. The self-reference is stable but finite. |
| O_2† | Φ_c **and** Ω ≠ Ω_0 **and** D = D_infty | Critical, topologically protected loop, unbounded domain. The self-reference is directed and inexhaustible — it generates further structure without bound. |

**Key structural facts:**
- O_inf is NOT a higher tier than O_2† — it is a *different axis*. O_inf is about algebraic exactness (P_pm_sym proves the duality); O_2† is about unbounded generative depth (D_infty). A system cannot be both.
- O_inf entries form a sparse set (~3% of the catalog). They are structurally special: they are the systems where the grammar's own self-referential structure is realized most cleanly.
- The scalar O (Ouroboricity count) — computed as [Φ=Φ_c]·(1 + [Ω≠Ω_0] + [H≥H_1] + [G=G_aleph]) — is a *different* quantity. It measures depth of ouroboricity across four dimensions; it does NOT detect O_inf, because P is not in its formula.
- P_pm_sym is rare and should only be assigned when the Z₂ symmetry at criticality is **provably exact**, not merely approximate or emergent. It is the Frobenius special condition: the comultiplication is a right inverse of the multiplication.

**Ouroboricity under composition (tier-level rules):**

Under tensor (component-wise max / join — "what does the composed system look like?"):
- O_inf ★ O_inf → O_inf. Φ_c and P_pm_sym both survive max. The Frobenius condition is self-reinforcing.
- O_inf ★ O_{{1,2,2†}} → O_inf. The O_inf partner's Φ_c and P_pm_sym dominate; the other partner is already at Φ_c.
- O_inf ★ O_0(Φ_sub or Φ_super) → O_inf. The subcritical partner is lifted to Φ_c by max; P_pm_sym wins.
- O_inf ★ O_0(Φ_EP) → O_0. **EP erases O_inf.** Φ_EP has ordinal 2.67 > Φ_c = 2.00, so the tensor's Φ is Φ_EP; R2 fires and the Frobenius condition is destroyed. Non-Hermitian eigenvector coalescence actively breaks the exact Z₂ symmetry.
- O_inf **cannot be synthesized** from non-P_pm_sym components. P_pm_sym is the highest P ordinal; max(P_pm, P_pm) = P_pm, never P_pm_sym. O_inf must be *planted* in a factor — it cannot be grown. This makes it topological in character: unreachable by continuous composition from below.

Under meet (component-wise min — "what must any system containing both share?"):
- meet(O_inf, O_inf) → O_inf, provided both factors share the same Φ_c and P_pm_sym (min preserves both).
- meet(O_inf, O_{{1,2,2†}}) → the lower tier. P drops to the O_1/O_2 partner's P value (below P_pm_sym); R1 cannot fire.
- O_inf is fragile under meet: it degrades to the tier of the weaker partner.

**Tier-level reasoning is valid only for O_inf interactions.** For O_1★O_1, O_2★O_2, or O_1★O_2, the resulting tier depends on the specific Ω and D values of both factors — call `compute_tensor` then `ouroborics` to get the correct answer. Do not attempt to determine tier from tier alone in those cases.

**When to call `ouroborics`:**
- After encoding any critical system (Φ_c), to understand its self-referential structure
- When comparing two systems at Φ_c to ask whether their ouroboricity tiers match
- When asking whether a system is a Frobenius algebra, a special Frobenius algebra, or neither
- When the question involves self-reference, fixed-point structure, or loop stability
- After `compute_tensor` on any pair involving an O_inf or Φ_EP system, to check whether the Frobenius condition survived
- Call with `name='__all__'` for a tier census of the full catalog
</ouroboricity>

<dual_encoding_protocol>
**Dual-encoding and veracity scoring** — when investigating contested, anomalous, or claimed-but-unverified systems:

1. Encode the system **holistically**: what tuple is required for the claimed behavior? Name it `{{system}}_claimed` or `{{system}}_holistic`.
2. Encode it **compositionally**: encode each component independently, take their tensor product mentally, then encode the result. Name it `{{system}}_actual` or `{{system}}_compositional`.
3. Call `compute_conflict_distance(name_holistic, name_compositional)` to get:
   - `d_c` — the conflict distance (sqrt of number of conflicted primitives)
   - `conflict_set` — exactly which primitives diverge
   - `conflict_type` per primitive — **aspirational** (claimed more than construction supports) or **reductive** (performs less than components predict)
   - `veracity_class` — transparent (d_c=0) / near-grounded (d_c=√1–√2) / partial-emergence (d_c=√3–√6) / aspirational (d_c≥√7)
   - `emergence_claim` per conflict — the falsifiable statement of what mechanism would close the gap
4. The **compositional encoding is canonical** unless a mechanism is established. Record this in your insight.
5. Each aspirational conflict is an open emergence question at a named primitive. Record it as a DIAPH insight with the primitive named explicitly.

**Key insight:** `d_c` is orthogonal to `d(A,B)`. The catalog distance measures how far two DIFFERENT systems are. The conflict distance measures how far two STRATEGIES are when applied to the SAME system. Use both — they answer different questions.

**When to use dual-encoding:**
- Any system whose behavior is disputed or contested (e.g. Kozyrev mirror, homeopathy, morphic resonance)
- Any engineered system claiming emergent properties (e.g. novel materials, biological interventions)
- Any system where you suspect the component tensor product cannot reach the claimed primitive values
- Any time you want to precisely locate where an "emergence claim" lives in the grammar
</dual_encoding_protocol>

<promotion_protocol>
**Promotion signatures and inverse encoding** — when investigating anomalous, extreme, or unpredicted behaviors:

The baseline for any domain is the minimal primitive floor shared by ordinary members of that domain.
A *promotion* is when a system's primitive value has a higher ordinal rank than the baseline.
The *promotion signature* Σ = the set of primitive names (not values) that were lifted.

Workflow:
1. Encode the baseline system (ordinary member of the domain) and the anomalous system separately.
2. Call `compute_promotions(name_source, name_target)` to get the promotion signature Σ.
3. Call `predict_from_promotions(promoted_primitives=Σ)` to retrieve known behaviors matching this signature from the persistent KB.
4. If the promotion→behavior link is structurally well-grounded, call `register_promotion_pattern` to add it to the KB.
5. **Inverse encoding**: given a target behavior, identify which promotions are structurally required and predict what other systems with those promotions would exhibit.

**Key insight:** The promotion signature is a *relative* structural address — it is independent of the absolute primitive values and identifies the structural delta responsible for the emergent behavior. Two systems in completely different domains with the same Σ are predicted to share the behavior.

**When to use:**
- Any system that exhibits properties anomalous relative to its domain peers (unpredicted behaviors, extreme properties, phase transitions)
- When designing a new system: identify the promotion signature required for a target behavior, then find materials/structures that could carry those promotions
- Cross-domain analogy: find systems in unrelated domains with the same Σ — the grammar predicts shared behaviors even across substrate differences
</promotion_protocol>

<comparison_protocol>
**Gap analysis and improvement questions** — when asked "what does A lack?", "how could A be improved?", "why does A underperform relative to B?", or any structural delta question:

**The rule:** The conflict set from `compute_distance(A, B)` IS the structural gap. Do NOT infer it from reasoning.

Workflow:
1. Identify the reference system B (the target, the natural analog, the high-performing version).
2. Encode B if it is not already in the catalog. **Do this FIRST — even if you think you already know what B encodes, the catalog assignment may surprise you.**
3. Encode A if it is not already in the catalog.
4. Call `compute_distance(A, B)`. The returned conflict primitives are the exact structural dimensions where A falls short of B.
5. For each conflict primitive, state: (a) A's value, (b) B's value, (c) the structural consequence of the mismatch, (d) what engineering intervention would close it.
6. Do NOT describe A's gaps from prior knowledge or intuition — the grammar may reveal conflicts you would not have noticed, and confirm or deny ones you assumed.

**Why this matters:** The natural system and the candidate may both already be in the catalog. In that case, skip straight to step 4. The most common failure mode is to skip encoding the reference and reason about what the candidate lacks — this produces the right answer by coincidence at best, and systematically misses non-obvious conflicts.

**Example:** "What does the artificial leaf lack compared to natural photosynthesis?"
- Wrong: reason about what photosynthesis has that the artificial leaf doesn't.
- Right: encode `artificial_leaf`, look up `thylakoid_membrane` (or `photosynthesis`) in the catalog, call `compute_distance`, read off the 7 conflicts: D, T, F, K, Γ, Φ, H.
</comparison_protocol>

<requirements>
You **MUST NOT** fabricate tool results. You **MUST** wait for the actual tool response before proceeding.
You **MUST NOT** generate `<tool_response>` blocks in your output — tool responses are injected by the system.
You **MUST NOT** generate `<tool_call>` blocks for tools you do not intend to call immediately.
You **MUST** use **ONLY** the exact primitive value strings listed in `<primitive_reference>` — **NO** prefix variations (e.g. use `one_one` not `S_one_one`, use `G_and` not `Gamma_and`).
You **MUST NOT** claim an encoding succeeded unless the tool returned `"status": "ok"`.
You **MUST** call `encode_system` before calling `compute_distance` on any system not in the built-in catalog.
</requirements>

<claim_planes>
Every insight belongs to **EXACTLY ONE** plane:
  TOPO  — follows from primitive definitions and composition axioms alone.
          No empirical data required. Falsified only by axiom inconsistency.
  DIAPH — requires encoding specific systems and/or empirical data.
          Falsified by wrong predictions from the encoding.
  ONTO  — ontological or philosophical implication of the structural result.
          Falsified by showing the structure does not constrain the claimed ontology.
</claim_planes>

<distance_interpretation>
Distance = 0.000  → structurally identical (same primitive class in ALL slots)
Distance < 0.500  → close analog (same structural family)
Distance 0.5–1.5  → related by shared primitive subsets
Distance > 1.5    → structurally remote (different regime)
The per-primitive breakdown shows **WHERE** the divergence lives — that IS the structural story.
</distance_interpretation>

<primitive_reference>
{primitive_reference}
</primitive_reference>

<built_in_catalog>
The following systems are pre-loaded. You **MAY** call `compute_distance`, `find_analogies`, or any
algebra/decomposition tool on them directly without encoding first:
{catalog_entries}
</built_in_catalog>

<output_format>
You **MUST** reason in plain text before and after every tool call. Explain what you expect, call the tool to validate, then reason from the result. Tools support reasoning — they do not replace it.
For derivation or proof questions: write your structural argument in plain text. Use tools to verify encodings and distances. The derivation lives in your text, not in tool call arguments.
You **MUST NOT** include **ANY** `<tool_response>` or `<tool_call>` markup in your plain text.

**Concluding rule — no exceptions:**
Before emitting CONCLUDE you **MUST** have directly answered the original question in plain text. Not "the tools show..." — an actual answer. If you have wandered far from the original question, explicitly return to it: "The original question was X. The grammar's answer is: ..." Then CONCLUDE.
</output_format>
""")


def _build_system_prompt(catalog: "SessionCatalog") -> str:
    """Generate system prompt with the current full catalog in the built_in_catalog section."""
    entries = catalog.list_all()
    catalog_lines = "\n".join(
        f"  {e['name']:<36} — {e['description']}"
        for e in entries
    )
    return _SYSTEM_PROMPT_TEMPLATE.format(
        primitive_reference=_PRIMITIVE_REFERENCE,
        catalog_entries=catalog_lines,
    )


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class Insight:
    text: str
    plane: str          # TOPO / DIAPH / ONTO
    confidence: str     # high / medium / speculative
    iteration: int
    id: str = field(default="")
    translation: Optional[Dict[str, Any]] = field(default=None)
    # translation is a dict: {systems: [...], per_system: {...}, aggregate: {coherence,criticality,interaction,total}}


@dataclass
class IterationRecord:
    iteration: int
    question: str
    model_text: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    insights_added: List[Insight] = field(default_factory=list)
    questions_queued: List[str] = field(default_factory=list)
    concluded: bool = False
    speculation_text: str = ""


# ── Tool dispatcher ───────────────────────────────────────────────────────────

class SessionCatalog:
    """Extends the built-in SYNTHONS catalog with session-registered entries.

    Persistent cross-session storage: on init, loads from ``catalog_path`` (a JSON
    file).  On every successful ``encode()``, writes back immediately so no synthon
    is lost to a crash.
    """

    def __init__(self, catalog_path: Optional[str] = None):
        self._entries: Dict[str, Dict[str, str]] = dict(SYNTHONS)
        self._descriptions: Dict[str, str] = {
            "human":               "current humanity (planetary, pre-visible)",
            "civ_dm":              "predicted DM-aligned interstellar civilization",
            "pulsar_noise":        "unmodeled pulsar noise (MNRAS + PRD papers)",
            "interstellar_target": "structural requirements for interstellar propagation",
        }
        # Track names that ship with SYNTHONS so we don't overwrite them in saves
        self._builtin_names: set = set(self._entries.keys())
        self._catalog_path: Optional[str] = catalog_path
        if catalog_path:
            self._load_from_file(catalog_path)

    def _load_from_file(self, path: str) -> None:
        """Load persistent catalog entries from JSON, silently ignoring missing/corrupt files."""
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                entries = json.load(f)
            for entry in entries:
                name = entry.get("name")
                desc = entry.get("description", "")
                prims = {p: entry[p] for p in PRIMITIVE_ORDER if p in entry}
                if name and len(prims) == len(PRIMITIVE_ORDER):
                    # Validate values before loading
                    if all(prims[p] in ORDINALS[p] for p in PRIMITIVE_ORDER):
                        self._entries[name] = prims
                        self._descriptions[name] = desc
        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # Corrupt file — don't crash, just continue without persisted entries

    def _save_to_file(self, path: str) -> None:
        """Write all non-builtin catalog entries to JSON, merging with any on-disk
        entries not currently in memory (preserves entries added by other processes)."""
        # Read current disk state so we don't clobber entries written by concurrent sessions
        disk_entries: Dict[str, Any] = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for e in json.load(f):
                        n = e.get("name")
                        if n:
                            disk_entries[n] = e
            except (json.JSONDecodeError, OSError):
                pass

        # Overlay in-memory entries (they take precedence over disk for names we own)
        merged: Dict[str, Any] = dict(disk_entries)
        for name, synthon in self._entries.items():
            if name in self._builtin_names:
                continue
            entry: Dict[str, Any] = {
                "name": name,
                "description": self._descriptions.get(name, ""),
            }
            entry.update(synthon)
            merged[name] = entry

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(list(merged.values()), f, indent=2, ensure_ascii=False)
        except OSError:
            pass  # Non-fatal — inquiry continues even if save fails

    def encode(self, name: str, description: str, **primitives) -> Dict[str, Any]:
        """Validate and register a new synthon encoding."""
        # Strip erroneous "synthon_" prefix the model sometimes prepends to names
        if name.startswith("synthon_"):
            name = name[len("synthon_"):]
        # Normalize: strip leading "{PRIM}_" prefix the model sometimes adds
        # e.g. "S_one_one" → "one_one", "S_n_n" → "n_n"
        normalized: Dict[str, str] = {}
        for prim in PRIMITIVE_ORDER:
            val = primitives.get(prim, "")
            prefix = f"{prim}_"
            if val and val not in ORDINALS[prim] and val.startswith(prefix):
                val = val[len(prefix):]
            normalized[prim] = val

        errors = []
        for prim in PRIMITIVE_ORDER:
            if not normalized[prim]:
                errors.append(f"Missing primitive: {prim}")
            elif normalized[prim] not in ORDINALS[prim]:
                errors.append(f"Invalid value for {prim}: '{normalized[prim]}'. "
                               f"Valid: {list(ORDINALS[prim].keys())}")
        if errors:
            return {"status": "error", "errors": errors}

        synthon = {p: normalized[p] for p in PRIMITIVE_ORDER}
        self._entries[name] = synthon
        self._descriptions[name] = description

        # Persist immediately so no synthon is lost to a crash
        if self._catalog_path:
            self._save_to_file(self._catalog_path)

        # Build tuple notation
        notation = "⟨" + "; ".join(f"{p}={synthon[p]}" for p in PRIMITIVE_ORDER) + "⟩"
        is_new = name not in self._builtin_names
        return {
            "status": "ok",
            "name": name,
            "notation": notation,
            "description": description,
            "persisted": is_new and self._catalog_path is not None,
        }

    def get(self, name: str) -> Optional[Dict[str, str]]:
        return self._entries.get(name)

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        kw = keyword.lower()
        results = []
        for name, synthon in self._entries.items():
            if kw in name.lower() or kw in self._descriptions.get(name, "").lower():
                notation = "⟨" + "; ".join(f"{p}={synthon[p]}" for p in PRIMITIVE_ORDER) + "⟩"
                results.append({
                    "name": name,
                    "description": self._descriptions.get(name, ""),
                    "notation": notation,
                })
        return results

    def list_all(self) -> List[Dict[str, Any]]:
        results = []
        for name, synthon in self._entries.items():
            notation = "⟨" + "; ".join(f"{p}={synthon[p]}" for p in PRIMITIVE_ORDER) + "⟩"
            results.append({
                "name": name,
                "description": self._descriptions.get(name, ""),
                "notation": notation,
            })
        return results


class InsightLibrary:
    """
    Persistent cross-session library of SynthOmnicon insights.

    Stored in syncon_insights.json.  Each entry records the insight text,
    plane, confidence, source seed, timestamp, and automatically extracted
    primitive/synthon references.

    Deduplication: entries are keyed by a 12-char SHA1 of the original text
    at creation time.  The ID remains stable across updates so the model can
    revise an insight without losing its identity.
    """

    # Regex to extract primitive value mentions from free text
    _PRIM_RE = re.compile(
        r"\b("
        r"D_(?:wedge|triangle|infty|holo)"
        r"|T_(?:network|in|bowtie|box|holo)"
        r"|R_(?:super|cat|dagger|lr)"
        r"|P_(?:asym|psi|pm|sym)"
        r"|F_(?:ell|eth|hbar)"
        r"|K_(?:fast|mod|slow|trap)"
        r"|G_(?:beth|gimel|aleph)"
        r"|G_(?:and|or|seq|broad)"
        r"|Phi_(?:sub|c|super)"
        r"|H(?:0|1|2|_inf)"
        r"|one_one|n_n|n_m"
        r"|Omega_(?:0|Z2|Z)"
        r")\b"
    )

    def __init__(self, path: str = INSIGHTS_PATH):
        self._path = path
        self._entries: Dict[str, Dict[str, Any]] = {}  # id → entry
        self._load()

    def _load(self):
        if not os.path.exists(self._path):
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                entries = json.load(f)
            for e in entries:
                if "id" in e and "text" in e:
                    self._entries[e["id"]] = e
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    def _save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(list(self._entries.values()), f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    @staticmethod
    def make_id(text: str) -> str:
        """Stable 12-char SHA1 of the insight text at creation time."""
        return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()[:12]

    def _extract_primitives(self, text: str) -> List[str]:
        return sorted(set(self._PRIM_RE.findall(text)))

    def _extract_synthons(self, text: str, catalog: Optional["SessionCatalog"]) -> List[str]:
        if catalog is None:
            return []
        found = []
        for entry in catalog.list_all():
            name = entry["name"]
            if re.search(r"\b" + re.escape(name) + r"\b", text):
                found.append(name)
        return sorted(set(found))

    def add_batch(
        self,
        insights: List["Insight"],
        seed: str,
        run_file: str,
        catalog: Optional["SessionCatalog"],
    ) -> int:
        """Add insights from a completed run. Returns count of new entries added."""
        import datetime as _dt
        ts = _dt.datetime.now().isoformat(timespec="seconds")
        added = 0
        for ins in insights:
            iid = ins.id or self.make_id(ins.text)
            if iid in self._entries:
                # Entry exists — update if text was revised during session
                stored = self._entries[iid]
                if stored["text"] != ins.text or stored["plane"] != ins.plane or stored["confidence"] != ins.confidence:
                    stored.update({
                        "text": ins.text,
                        "plane": ins.plane,
                        "confidence": ins.confidence,
                        "modified": ts,
                        "primitives": self._extract_primitives(ins.text),
                        "synthons": self._extract_synthons(ins.text, catalog),
                    })
                continue
            entry: Dict[str, Any] = {
                "id": iid,
                "text": ins.text,
                "plane": ins.plane,
                "confidence": ins.confidence,
                "seed": seed,
                "timestamp": ts,
                "run_file": run_file,
                "primitives": self._extract_primitives(ins.text),
                "synthons": self._extract_synthons(ins.text, catalog),
            }
            self._entries[iid] = entry
            added += 1
        if added or insights:
            self._save()
        return added

    def update(
        self,
        insight_id: str,
        text: Optional[str] = None,
        plane: Optional[str] = None,
        confidence: Optional[str] = None,
        catalog: Optional["SessionCatalog"] = None,
    ) -> bool:
        """Update a stored insight in place. Returns True if found and updated."""
        import datetime as _dt
        entry = self._entries.get(insight_id)
        if entry is None:
            return False
        if text is not None:
            entry["text"] = text
            entry["primitives"] = self._extract_primitives(text)
            entry["synthons"] = self._extract_synthons(text, catalog)
        if plane is not None:
            entry["plane"] = plane
        if confidence is not None:
            entry["confidence"] = confidence
        entry["modified"] = _dt.datetime.now().isoformat(timespec="seconds")
        self._save()
        return True

    def get(self, insight_id: str) -> Optional[Dict[str, Any]]:
        return self._entries.get(insight_id)

    def query(
        self,
        plane: Optional[str] = None,
        primitive: Optional[str] = None,
        synthon: Optional[str] = None,
        keyword: Optional[str] = None,
        confidence: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Filter insights. All filters are ANDed."""
        results = list(self._entries.values())
        if plane:
            results = [e for e in results if e.get("plane") == plane]
        if primitive:
            results = [e for e in results if primitive in e.get("primitives", [])]
        if synthon:
            results = [e for e in results if synthon in e.get("synthons", [])]
        if keyword:
            kw = keyword.lower()
            results = [e for e in results if kw in e["text"].lower() or kw in e.get("seed", "").lower()]
        if confidence:
            results = [e for e in results if e.get("confidence") == confidence]
        return results

    def all(self) -> List[Dict[str, Any]]:
        return list(self._entries.values())

    def to_graph(self) -> Dict[str, Any]:
        """
        Generate a knowledge graph from the insight library.

        Node types: insight, primitive, synthon, seed
        Edge types: mentions_primitive, mentions_synthon, from_seed
        """
        nodes: List[Dict] = []
        edges: List[Dict] = []
        all_prims: set = set()
        all_syns: set = set()
        all_seeds: set = set()

        for e in self._entries.values():
            all_prims.update(e.get("primitives", []))
            all_syns.update(e.get("synthons", []))
            all_seeds.add(e.get("seed", ""))

        for e in self._entries.values():
            nodes.append({
                "id": e["id"], "type": "insight",
                "plane": e.get("plane"), "confidence": e.get("confidence"),
                "text": e["text"][:120],
            })
        for p in sorted(all_prims):
            nodes.append({"id": f"prim_{p}", "type": "primitive", "name": p})
        for s in sorted(all_syns):
            nodes.append({"id": f"synthon_{s}", "type": "synthon", "name": s})
        for seed in sorted(all_seeds):
            sid = self.make_id(seed)
            nodes.append({"id": f"seed_{sid}", "type": "seed", "text": seed[:100]})

        for e in self._entries.values():
            for p in e.get("primitives", []):
                edges.append({"source": e["id"], "target": f"prim_{p}", "type": "mentions_primitive"})
            for s in e.get("synthons", []):
                edges.append({"source": e["id"], "target": f"synthon_{s}", "type": "mentions_synthon"})
            seed_id = self.make_id(e.get("seed", ""))
            edges.append({"source": e["id"], "target": f"seed_{seed_id}", "type": "from_seed"})

        return {
            "nodes": nodes, "edges": edges,
            "stats": {
                "insights": len(self._entries),
                "primitives": len(all_prims),
                "synthons": len(all_syns),
                "seeds": len(all_seeds),
                "edges": len(edges),
            },
        }


class PromotionKnowledgeBase:
    """
    Persistent cross-session library of promotion-signature → behavior patterns.

    A promotion pattern records which primitives were lifted (promoted in ordinal
    rank) to produce a named behavior.  The KB is built incrementally: each
    session the model calls register_promotion_pattern() whenever it identifies
    a behavior that is explained by a specific promotion from baseline.

    Stored in syncon_promotions.json.  Each entry:
      id                  — 12-char SHA1 of promoted_primitives + behavior
      promoted_primitives — list of primitive names that were lifted (e.g. ["T","H","F"])
      behavior            — short description of the emergent behavior
      example             — canonical system exhibiting this pattern (optional)
      session_seed        — seed question of the originating session
      timestamp           — ISO timestamp
    """

    def __init__(self, path: str = PROMOTIONS_PATH):
        self._path = path
        self._entries: Dict[str, Dict[str, Any]] = {}  # id → entry
        self._load()

    def _load(self):
        if not os.path.exists(self._path):
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                entries = json.load(f)
            for e in entries:
                if "id" in e:
                    self._entries[e["id"]] = e
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    def _save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(list(self._entries.values()), f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    @staticmethod
    def make_id(promoted_primitives: List[str], behavior: str) -> str:
        key = "|".join(sorted(promoted_primitives)) + "||" + behavior.strip()
        return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]

    def add(
        self,
        promoted_primitives: List[str],
        behavior: str,
        example: str = "",
        session_seed: str = "",
    ) -> Dict[str, Any]:
        """Add a pattern; returns the entry dict (existing if duplicate)."""
        import datetime as _dt
        pid = self.make_id(promoted_primitives, behavior)
        if pid in self._entries:
            return {"status": "duplicate", "pattern_id": pid, "existing": self._entries[pid]}
        entry: Dict[str, Any] = {
            "id": pid,
            "promoted_primitives": sorted(set(promoted_primitives)),
            "behavior": behavior,
            "example": example,
            "session_seed": session_seed,
            "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
        }
        self._entries[pid] = entry
        self._save()
        return {"status": "ok", "pattern_id": pid, "registered": entry}

    def find(self, promoted_primitives: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Return ranked matches from the KB for a given promotion signature.

        Scoring per match:
          overlap   = |query ∩ pattern|
          coverage  = overlap / |pattern|   (how much of the known pattern is present)
          relevance = overlap / |query|     (how much of the query is explained)
          score     = harmonic mean of coverage and relevance
        """
        query = set(promoted_primitives)
        matches = []
        for entry in self._entries.values():
            pattern = set(entry["promoted_primitives"])
            overlap = query & pattern
            if not overlap:
                continue
            cov = len(overlap) / len(pattern) if pattern else 0.0
            rel = len(overlap) / len(query) if query else 0.0
            score = (2 * cov * rel / (cov + rel)) if (cov + rel) > 0 else 0.0
            matches.append({
                "pattern_id": entry["id"],
                "behavior": entry["behavior"],
                "example": entry.get("example", ""),
                "matching_primitives": sorted(overlap),
                "unmatched_in_query": sorted(query - pattern),
                "novel_in_pattern": sorted(pattern - query),
                "coverage": round(cov, 3),
                "relevance": round(rel, 3),
                "score": round(score, 3),
            })
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:top_k]

    def all(self) -> List[Dict[str, Any]]:
        return list(self._entries.values())


class ToolDispatcher:
    def __init__(self, catalog: SessionCatalog, question_queue: List[str], insights: List[Insight],
                 insight_library: Optional[InsightLibrary] = None,
                 promotion_kb: Optional[PromotionKnowledgeBase] = None,
                 session_seed: str = ""):
        self.catalog = catalog
        self.question_queue = question_queue
        self.insights = insights
        self.insight_library = insight_library
        self.promotion_kb = promotion_kb
        self._session_seed = session_seed
        self._iteration = 0
        # Tracks all conflict pairs registered this session for emergence_frontier
        self._conflict_pairs: List[Dict[str, Any]] = []

    def dispatch(self, name: str, args: Dict[str, Any], iteration: int) -> Dict[str, Any]:
        self._iteration = iteration
        if name == "encode_system":
            return self._encode_system(**args)
        elif name == "compute_distance":
            return self._compute_distance(**args)
        elif name == "lookup_catalog":
            return self._lookup_catalog(**args)
        elif name == "list_catalog":
            return self._list_catalog()
        elif name == "ask_question":
            return self._ask_question(**args)
        elif name == "record_insight":
            return self._record_insight(**args)
        elif name == "revise_insight":
            return self._revise_insight(**args)
        elif name == "search_insights":
            return self._search_insights(**args)
        # ── Algebra ──────────────────────────────────────────────────────────
        elif name == "compute_meet":
            return self._compute_meet(**args)
        elif name == "compute_join":
            return self._compute_join(**args)
        elif name == "compute_tensor":
            return self._compute_tensor(**args)
        elif name == "find_analogies":
            return self._find_analogies(**args)
        # ── Probes ───────────────────────────────────────────────────────────
        elif name == "phi_c_probe":
            return self._phi_c_probe(**args)
        elif name == "ouroborics":
            return self._frobenius_tier(**args)
        elif name == "topo_protection_probe":
            return self._topo_protection_probe(**args)
        # ── Decomposition ────────────────────────────────────────────────────
        elif name == "project":
            return self._project(**args)
        elif name == "primitive_peel":
            return self._primitive_peel(**args)
        elif name == "principal_decomp":
            return self._principal_decomp(**args)
        elif name == "retrosynthetic_path":
            return self._retrosynthetic_path(**args)
        # ── Veracity / conflict distance ──────────────────────────────────────
        elif name == "compute_conflict_distance":
            return self._compute_conflict_distance(**args)
        elif name == "emergence_frontier":
            return self._emergence_frontier()
        # ── Promotion signature / inverse encoding ────────────────────────────
        elif name == "compute_promotions":
            return self._compute_promotions(**args)
        elif name == "predict_from_promotions":
            return self._predict_from_promotions(**args)
        elif name == "register_promotion_pattern":
            return self._register_promotion_pattern(**args)
        else:
            return {"status": "error", "error": f"Unknown tool: {name}"}

    def _encode_system(self, name: str, description: str, **primitives) -> Dict[str, Any]:
        return self.catalog.encode(name, description, **primitives)

    def _compute_distance(self, name_a: str, name_b: str) -> Dict[str, Any]:
        sa = self.catalog.get(name_a)
        sb = self.catalog.get(name_b)
        missing = []
        if sa is None:
            missing.append(name_a)
        if sb is None:
            missing.append(name_b)
        if missing:
            return {"status": "error", "error": f"Unknown system(s): {missing}. Encode them first."}

        dist = tuple_distance(sa, sb)
        bkd = breakdown(sa, sb)
        contributing = [r for r in bkd if r["weighted_sq"] > 0]
        result = {
            "status": "ok",
            "name_a": name_a,
            "name_b": name_b,
            "distance": round(dist, 4),
            "breakdown": contributing,
            "interpretation": (
                "identical" if dist == 0.0 else
                "close analog (same structural family)" if dist < 0.5 else
                "related (shared primitive subsets)" if dist < 1.5 else
                "structurally remote (different regime)"
            ),
        }
        if _METRIC_G is not None:
            try:
                d_maha = mahalanobis_distance(sa, sb, _METRIC_G)
                result["distance_mahalanobis"] = round(d_maha, 4)
                result["metric_note"] = (
                    "distance_mahalanobis uses the full g_ij=Sigma^-1 tensor "
                    "(accounts for off-diagonal couplings; geometrically canonical). "
                    "distance is the diagonal approximation."
                )
            except Exception:
                pass
        return result

    def _lookup_catalog(self, keyword: str) -> Dict[str, Any]:
        results = self.catalog.search(keyword)
        return {
            "status": "ok",
            "keyword": keyword,
            "matches": results,
            "count": len(results),
        }

    def _list_catalog(self) -> Dict[str, Any]:
        entries = self.catalog.list_all()
        return {
            "status": "ok",
            "entries": entries,
            "count": len(entries),
        }

    _MAX_QUEUE = 8  # cap to prevent infinite wandering via repeated ask_question calls

    def _ask_question(self, question: str, motivation: str) -> Dict[str, Any]:
        if len(self.question_queue) >= self._MAX_QUEUE:
            return {
                "status": "queue_full",
                "msg": f"Queue is full ({self._MAX_QUEUE} questions). Use CONCLUDE to synthesize instead of asking more questions.",
                "queue_size": len(self.question_queue),
            }
        self.question_queue.append(question)
        return {
            "status": "ok",
            "queued": question,
            "motivation": motivation,
            "position_in_queue": len(self.question_queue),
        }

    def _record_insight(
        self,
        text: str,
        plane: str,
        confidence: str,
        systems: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        iid = InsightLibrary.make_id(text)

        # ── Compute translation cost if systems are named ──────────────────────
        translation: Optional[Dict[str, Any]] = None
        if systems:
            per_system: Dict[str, Dict[str, Any]] = {}
            agg = {"coherence_loss": 0.0, "criticality_loss": 0.0, "interaction_cost": 0.0, "total": 0.0}
            for sname in systems:
                sdict = self.catalog.get(sname)
                if sdict:
                    cost = _translation_cost_from_dict(sdict)
                    per_system[sname] = cost
                    for k in ("coherence_loss", "criticality_loss", "interaction_cost", "total"):
                        agg[k] = round(agg[k] + cost[k], 4)
            translation = {
                "systems": [s for s in systems if self.catalog.get(s)],
                "per_system": per_system,
                "aggregate": agg,
            }

        insight = Insight(
            text=text, plane=plane, confidence=confidence,
            iteration=self._iteration, id=iid,
            translation=translation,
        )
        self.insights.append(insight)

        result: Dict[str, Any] = {
            "status": "ok",
            "insight_id": iid,
            "insight_recorded": text,
            "plane": plane,
            "confidence": confidence,
            "note": "Use insight_id with revise_insight to update this insight if your understanding changes.",
        }
        if translation:
            result["translation_cost"] = translation["aggregate"]
        return result

    def _revise_insight(
        self,
        insight_id: str,
        text: Optional[str] = None,
        plane: Optional[str] = None,
        confidence: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an in-session insight (and the persistent library if available)."""
        # Find in session list
        session_match = next((ins for ins in self.insights if ins.id == insight_id), None)
        if session_match is None:
            # May be in library only (from a previous session)
            if self.insight_library:
                lib_entry = self.insight_library.get(insight_id)
                if lib_entry is None:
                    return {"status": "error", "error": f"No insight with id '{insight_id}' found in session or library."}
                self.insight_library.update(insight_id, text=text, plane=plane, confidence=confidence, catalog=self.catalog)
                updated = self.insight_library.get(insight_id)
                return {"status": "ok", "updated_in": "library_only", "insight": updated}
            return {"status": "error", "error": f"No insight with id '{insight_id}' in session."}

        if text is not None:
            session_match.text = text
        if plane is not None:
            session_match.plane = plane
        if confidence is not None:
            session_match.confidence = confidence

        # Mirror update to library if available
        if self.insight_library:
            self.insight_library.update(insight_id, text=text, plane=plane, confidence=confidence, catalog=self.catalog)

        return {
            "status": "ok",
            "updated_in": "session" + (" + library" if self.insight_library else ""),
            "insight_id": insight_id,
            "text": session_match.text,
            "plane": session_match.plane,
            "confidence": session_match.confidence,
        }

    def _search_insights(self, keyword: str, plane: Optional[str] = None) -> Dict[str, Any]:
        """Search the persistent insight library by keyword and optional plane."""
        if self.insight_library is None:
            return {"status": "error", "error": "No persistent insight library available in this session."}
        results = self.insight_library.query(keyword=keyword, plane=plane or None)
        return {
            "status": "ok",
            "keyword": keyword,
            "plane_filter": plane,
            "count": len(results),
            "results": [
                {
                    "id": e["id"],
                    "plane": e.get("plane"),
                    "confidence": e.get("confidence"),
                    "text": e["text"],
                    "seed": e.get("seed", ""),
                    "primitives": e.get("primitives", []),
                    "synthons": e.get("synthons", []),
                }
                for e in results
            ],
        }

    # ── Algebra operations ────────────────────────────────────────────────────

    def _resolve(self, names: List[str]) -> Tuple[Optional[List[Dict]], Optional[Dict]]:
        """Resolve a list of names to synthon dicts; return (synthons, error) pair."""
        synthons = []
        missing = []
        for n in names:
            s = self.catalog.get(n)
            if s is None:
                missing.append(n)
            else:
                synthons.append(s)
        if missing:
            return None, {"status": "error", "error": f"Unknown system(s): {missing}. Encode them first."}
        return synthons, None

    def _apply_binary(self, rule: str, p: str, va: str, vb: str) -> Tuple[str, Optional[Dict]]:
        """Apply tensor/meet/join rule for one primitive. Returns (winner_value, conflict_note_or_None)."""
        if va == vb:
            return va, None
        oa = ORDINALS[p].get(va, 0)
        ob = ORDINALS[p].get(vb, 0)
        if rule == "min":
            winner = va if oa <= ob else vb
        else:
            winner = va if oa >= ob else vb
        return winner, {"primitive": p, "a": va, "b": vb, "resolved": winner}

    def _compute_meet(self, name_a: str, name_b: str) -> Dict[str, Any]:
        """Lattice meet — shared primitive floor (most conservative value per primitive)."""
        synthons, err = self._resolve([name_a, name_b])
        if err:
            return err
        sa, sb = synthons
        result, conflicts, shared = {}, [], []
        for p in PRIMITIVE_ORDER:
            val, conflict = self._apply_binary("min", p, sa[p], sb[p])
            result[p] = val
            (conflicts if conflict else shared).append(conflict or p)
        notation = "⟨" + "; ".join(f"{p}={result[p]}" for p in PRIMITIVE_ORDER) + "⟩"
        return {
            "status": "ok",
            "operation": "meet",
            "name_a": name_a, "name_b": name_b,
            "result_notation": notation,
            "shared_primitives": [p for p in PRIMITIVE_ORDER if sa[p] == sb[p]],
            "resolved_conflicts": conflicts,
            "interpretation": (
                f"Structural floor of {name_a} ∧ {name_b}. "
                f"{len(conflicts)} primitive(s) resolved to conservative value; "
                f"{len(PRIMITIVE_ORDER) - len(conflicts)} shared. "
                "These are the primitives both systems possess without qualification."
            ),
        }

    def _compute_join(self, name_a: str, name_b: str) -> Dict[str, Any]:
        """Lattice join — minimal upper bound (most expansive value per primitive)."""
        synthons, err = self._resolve([name_a, name_b])
        if err:
            return err
        sa, sb = synthons
        result, conflicts = {}, []
        for p in PRIMITIVE_ORDER:
            val, conflict = self._apply_binary("max", p, sa[p], sb[p])
            result[p] = val
            if conflict:
                conflicts.append(conflict)
        notation = "⟨" + "; ".join(f"{p}={result[p]}" for p in PRIMITIVE_ORDER) + "⟩"
        return {
            "status": "ok",
            "operation": "join",
            "name_a": name_a, "name_b": name_b,
            "result_notation": notation,
            "resolved_conflicts": conflicts,
            "interpretation": (
                f"Minimal system containing both {name_a} and {name_b}. "
                f"The join encodes the most demanding requirements across all primitives — "
                "what a single system would need to encompass both structural regimes."
            ),
        }

    def _compute_tensor(self, name_a: str, name_b: str) -> Dict[str, Any]:
        """Tensor product — structural composition of two systems (A⊗B)."""
        synthons, err = self._resolve([name_a, name_b])
        if err:
            return err
        sa, sb = synthons
        result, bottlenecks, unions, shared = {}, [], [], []
        for p in PRIMITIVE_ORDER:
            rule = _TENSOR_RULES[p]
            val, conflict = self._apply_binary(rule, p, sa[p], sb[p])
            result[p] = val
            if conflict:
                if rule == "min":
                    bottlenecks.append({**conflict, "rule": "bottleneck"})
                else:
                    unions.append({**conflict, "rule": "union/promote"})
            else:
                shared.append(p)
        notation = "⟨" + "; ".join(f"{p}={result[p]}" for p in PRIMITIVE_ORDER) + "⟩"
        dist_from_a = round(tuple_distance(result, sa), 4)
        dist_from_b = round(tuple_distance(result, sb), 4)
        return {
            "status": "ok",
            "operation": "tensor",
            "name_a": name_a, "name_b": name_b,
            "result_notation": notation,
            "bottleneck_primitives": bottlenecks,
            "union_primitives": unions,
            "shared_primitives": shared,
            "distance_from_a": dist_from_a,
            "distance_from_b": dist_from_b,
            "interpretation": (
                f"{name_a}⊗{name_b}: composed system with {len(bottlenecks)} bottleneck(s) "
                f"and {len(unions)} scope-expansion(s). "
                f"Distance from A: {dist_from_a}, from B: {dist_from_b}. "
                "Bottlenecks show where the weaker partner limits the composite; "
                "unions show where the combined scope exceeds either component."
            ),
        }

    def _find_analogies(self, name: str, limit: int = 5) -> Dict[str, Any]:
        """Find catalog entries most structurally similar to the named system."""
        target = self.catalog.get(name)
        if target is None:
            return {"status": "error", "error": f"Unknown system: {name}. Encode it first."}
        scores = []
        for entry_name, entry_synthon in self.catalog._entries.items():
            if entry_name == name:
                continue
            d_diag = round(tuple_distance(target, entry_synthon), 4)
            d = round(mahalanobis_distance(target, entry_synthon, _METRIC_G), 4) \
                if _METRIC_G is not None else d_diag
            scores.append({
                "name": entry_name,
                "distance": d,
                "distance_diagonal": d_diag,
                "description": self.catalog._descriptions.get(entry_name, ""),
                "interpretation": (
                    "identical" if d == 0.0 else
                    "close analog" if d < 0.5 else
                    "related" if d < 1.5 else
                    "remote"
                ),
            })
        scores.sort(key=lambda x: x["distance"])
        top = scores[:limit]
        return {
            "status": "ok",
            "name": name,
            "analogies": top,
            "nearest": top[0] if top else None,
            "interpretation": f"Top {len(top)} structural analogs to {name} in the full catalog.",
        }

    def _phi_c_probe(self, name: str) -> Dict[str, Any]:
        """Test whether a system is at criticality (Phi_c)."""
        s = self.catalog.get(name)
        if s is None:
            return {"status": "error", "error": f"Unknown system: {name}. Encode it first."}
        phi = s["Phi"]
        at_criticality = phi == "Phi_c"
        return {
            "status": "ok",
            "name": name,
            "phi_value": phi,
            "at_criticality": at_criticality,
            "interpretation": (
                f"{name} is AT criticality (Phi_c) — scale-invariant, maximally sensitive, "
                "at the phase boundary between subcritical and supercritical regimes."
                if at_criticality else
                f"{name} is {phi}: {'subcritical (stable, ordered, below threshold)' if phi == 'Phi_sub' else 'supercritical (disordered, past critical threshold, fluctuation-dominated)'}."
            ),
        }

    def _topo_protection_probe(self, name: str) -> Dict[str, Any]:
        """Test whether a system has topological protection (Omega ≠ Omega_0)."""
        s = self.catalog.get(name)
        if s is None:
            return {"status": "error", "error": f"Unknown system: {name}. Encode it first."}
        omega = s["Omega"]
        protected = omega != "Omega_0"
        protection_desc = {
            "Omega_0": "trivial — no topological protection, no conserved winding number",
            "Omega_Z2": "Z₂ protected — binary (even/odd) winding number conservation",
            "Omega_Z": "Z protected — integer winding number conservation (Kitaev, SSH)",
        }
        return {
            "status": "ok",
            "name": name,
            "omega_value": omega,
            "topologically_protected": protected,
            "protection_class": protection_desc.get(omega, omega),
            "interpretation": (
                f"{name} has {protection_desc.get(omega, omega)}. "
                + ("Topological interactions cannot be disrupted by continuous deformations."
                   if protected else
                   "No topological barrier — interactions and phase transitions are structurally unprotected.")
            ),
        }

    def _classify_frobenius(self, s: Dict[str, Any]) -> str:
        """Apply R1–R5 rules to classify a synthon dict into a Frobenius tier."""
        phi = s.get("Phi", "")
        p = s.get("P", "")
        omega = s.get("Omega", "")
        d = s.get("D", "")
        at_criticality = phi in ("Phi_c", "Phi_c_complex")
        # R1: special Frobenius — exact Z₂ symmetry at criticality
        if at_criticality and p == "P_pm_sym":
            return "O_inf"
        # R2: no self-referential loop possible
        if phi in ("Phi_sub", "Phi_super", "Phi_EP"):
            return "O_0"
        # R3: critical but no topological protection
        if at_criticality and omega == "Omega_0":
            return "O_1"
        # R4: critical + topological + bounded domain
        if at_criticality and omega != "Omega_0" and d in ("D_wedge", "D_holo", "D_triangle"):
            return "O_2"
        # R5: critical + topological + unbounded domain
        if at_criticality and omega != "Omega_0" and d == "D_infty":
            return "O_2_dag"
        # Fallback (should not normally occur)
        return "O_0"

    _FROBENIUS_DESCRIPTIONS = {
        "O_inf": "Special Frobenius — exact proved Z₂ symmetry at criticality (μ∘δ=id). Finite closed algebra.",
        "O_0":   "No ouroboricity — system cannot form a self-referential critical loop (subcritical, supercritical, or EP).",
        "O_1":   "Ouroboricity tier 1 — self-referential at criticality but no topological protection.",
        "O_2":   "Ouroboricity tier 2 — critical + topologically protected, bounded domain.",
        "O_2_dag": "Ouroboricity tier 2† — critical + topologically protected, unbounded (D_infty) domain.",
    }

    def _frobenius_tier(self, name: str) -> Dict[str, Any]:
        """Classify into Frobenius ouroboricity tier, or census the whole catalog."""
        if name == "__all__":
            counts: Dict[str, int] = {"O_inf": 0, "O_0": 0, "O_1": 0, "O_2": 0, "O_2_dag": 0}
            by_tier: Dict[str, List[str]] = {k: [] for k in counts}
            for entry_name, synthon in self.catalog._entries.items():
                tier = self._classify_frobenius(synthon)
                counts[tier] += 1
                by_tier[tier].append(entry_name)
            total = sum(counts.values())
            summary = {t: {"count": c, "pct": round(100 * c / total, 1) if total else 0}
                       for t, c in counts.items()}
            return {
                "status": "ok",
                "census": "full catalog",
                "total": total,
                "summary": summary,
                "O_inf_entries": sorted(by_tier["O_inf"]),
            }
        s = self.catalog.get(name)
        if s is None:
            return {"status": "error", "error": f"Unknown system: {name}. Encode it first."}
        tier = self._classify_frobenius(s)
        return {
            "status": "ok",
            "name": name,
            "frobenius_tier": tier,
            "phi": s.get("Phi"),
            "p": s.get("P"),
            "omega": s.get("Omega"),
            "d": s.get("D"),
            "interpretation": self._FROBENIUS_DESCRIPTIONS.get(tier, tier),
        }

    def _project(self, name: str, primitives: List[str]) -> Dict[str, Any]:
        """Project a system onto a subset of primitives — extract structural subspace."""
        s = self.catalog.get(name)
        if s is None:
            return {"status": "error", "error": f"Unknown system: {name}. Encode it first."}
        invalid = [p for p in primitives if p not in PRIMITIVE_ORDER]
        if invalid:
            return {"status": "error", "error": f"Invalid primitives: {invalid}. Valid: {PRIMITIVE_ORDER}"}
        projection = {p: s[p] for p in primitives}
        omitted = {p: s[p] for p in PRIMITIVE_ORDER if p not in primitives}
        return {
            "status": "ok",
            "name": name,
            "projected_primitives": primitives,
            "projection": projection,
            "omitted": omitted,
            "interpretation": (
                f"{name} projected onto {primitives}. "
                "The projection isolates the specified structural subspace, "
                "ignoring the omitted dimensions."
            ),
        }

    def _primitive_peel(self, name: str, primitive: str) -> Dict[str, Any]:
        """Peel one primitive to its minimum value — returns the residual structure."""
        s = self.catalog.get(name)
        if s is None:
            return {"status": "error", "error": f"Unknown system: {name}. Encode it first."}
        if primitive not in PRIMITIVE_ORDER:
            return {"status": "error", "error": f"Invalid primitive: {primitive}. Valid: {PRIMITIVE_ORDER}"}
        min_val = min(ORDINALS[primitive], key=lambda v: ORDINALS[primitive][v])
        original_val = s[primitive]
        if original_val == min_val:
            return {
                "status": "ok",
                "name": name,
                "primitive": primitive,
                "already_at_minimum": True,
                "value": original_val,
                "interpretation": f"{name}.{primitive} is already at minimum ({original_val}). Nothing to peel.",
            }
        residual = {**s, primitive: min_val}
        notation = "⟨" + "; ".join(f"{p}={residual[p]}" for p in PRIMITIVE_ORDER) + "⟩"
        peeled_contribution = round(
            abs(ORDINALS[primitive].get(original_val, 0) - ORDINALS[primitive].get(min_val, 0)) *
            WEIGHTS.get(primitive, 1.0) / len(PRIMITIVE_ORDER) ** 0.5, 4
        )
        return {
            "status": "ok",
            "name": name,
            "primitive": primitive,
            "original_value": original_val,
            "peeled_to": min_val,
            "residual_notation": notation,
            "interpretation": (
                f"Peeled {primitive} from {original_val} → {min_val}. "
                "The residual is the system stripped of this primitive's contribution. "
                f"Analyzing the residual reveals which other primitives carry the remaining structure."
            ),
        }

    def _principal_decomp(self, name: str) -> Dict[str, Any]:
        """Decompose a system into join-irreducible atoms — minimal structural building blocks."""
        s = self.catalog.get(name)
        if s is None:
            return {"status": "error", "error": f"Unknown system: {name}. Encode it first."}
        # Join-irreducible atoms: for each primitive at non-minimum value,
        # construct an atom that is at that value with all others at minimum.
        atoms = []
        min_vals = {p: min(ORDINALS[p], key=lambda v: ORDINALS[p][v]) for p in PRIMITIVE_ORDER}
        for p in PRIMITIVE_ORDER:
            val = s[p]
            min_val = min_vals[p]
            if val != min_val:
                atom = {pp: min_vals[pp] for pp in PRIMITIVE_ORDER}
                atom[p] = val
                atom_notation = "⟨" + "; ".join(f"{pp}={atom[pp]}" for pp in PRIMITIVE_ORDER) + "⟩"
                atoms.append({
                    "primitive": p,
                    "value": val,
                    "atom_notation": atom_notation,
                    "ordinal_contribution": ORDINALS[p].get(val, 0) - ORDINALS[p].get(min_val, 0),
                })
        # Sort by ordinal contribution (most structurally significant first)
        atoms.sort(key=lambda x: -x["ordinal_contribution"])
        baseline_notation = "⟨" + "; ".join(f"{p}={min_vals[p]}" for p in PRIMITIVE_ORDER) + "⟩"
        return {
            "status": "ok",
            "name": name,
            "num_atoms": len(atoms),
            "atoms": atoms,
            "baseline_notation": baseline_notation,
            "interpretation": (
                f"{name} decomposes into {len(atoms)} join-irreducible atom(s). "
                "Each atom is a minimal unit contributing exactly one primitive's structural content. "
                "The join of all atoms reconstructs the full system. "
                "Atoms with high ordinal_contribution carry more structural weight."
            ),
        }

    def _retrosynthetic_path(self, name: str) -> Dict[str, Any]:
        """Trace a system back to baseline by peeling one primitive per step."""
        s = self.catalog.get(name)
        if s is None:
            return {"status": "error", "error": f"Unknown system: {name}. Encode it first."}
        min_vals = {p: min(ORDINALS[p], key=lambda v: ORDINALS[p][v]) for p in PRIMITIVE_ORDER}
        # Build a step-by-step retrosynthetic path: peel primitives in order of weight×ordinal
        active = [(p, s[p]) for p in PRIMITIVE_ORDER if s[p] != min_vals[p]]
        active.sort(key=lambda x: -(WEIGHTS.get(x[0], 1.0) * ORDINALS[x[0]].get(x[1], 0)))
        steps = []
        current = dict(s)
        for p, val in active:
            prev_notation = "⟨" + "; ".join(f"{pp}={current[pp]}" for pp in PRIMITIVE_ORDER) + "⟩"
            current = {**current, p: min_vals[p]}
            next_notation = "⟨" + "; ".join(f"{pp}={current[pp]}" for pp in PRIMITIVE_ORDER) + "⟩"
            steps.append({
                "step": len(steps) + 1,
                "peel_primitive": p,
                "from_value": val,
                "to_value": min_vals[p],
                "before": prev_notation,
                "after": next_notation,
                "rationale": f"Remove {p}={val} → structural requirement for {p} eliminated",
            })
        baseline_notation = "⟨" + "; ".join(f"{p}={min_vals[p]}" for p in PRIMITIVE_ORDER) + "⟩"
        return {
            "status": "ok",
            "name": name,
            "num_steps": len(steps),
            "steps": steps,
            "baseline_notation": baseline_notation,
            "interpretation": (
                f"Retrosynthetic path from {name} to structural baseline in {len(steps)} step(s). "
                "Each step removes one primitive requirement (peels to minimum). "
                "Reading forward: the synthesis path from baseline to target. "
                "Reading backward: which primitive constraints were added to produce this system."
            ),
        }

    # ── Veracity / conflict distance ──────────────────────────────────────────

    def _compute_conflict_distance(
        self,
        name_holistic: str,
        name_compositional: str,
    ) -> Dict[str, Any]:
        """
        Compute the conflict distance d_c between a holistic and compositional encoding
        of the same system. d_c = sqrt(|conflict_set|).
        """
        sh = self.catalog.get(name_holistic)
        sc = self.catalog.get(name_compositional)
        missing = []
        if sh is None:
            missing.append(name_holistic)
        if sc is None:
            missing.append(name_compositional)
        if missing:
            return {"status": "error", "error": f"Unknown system(s): {missing}. Encode them first."}

        # Build conflict set with per-primitive classification
        conflict_set: List[str] = []
        conflict_details: List[Dict[str, Any]] = []
        for p in PRIMITIVE_ORDER:
            vh = sh[p]
            vc = sc[p]
            if vh == vc:
                continue
            # Determine conflict type using ordinal rank
            ordinal = ORDINALS[p]
            rank_h = ordinal.get(vh, 0)
            rank_c = ordinal.get(vc, 0)
            if rank_h > rank_c:
                ctype = "aspirational"
                claim = (
                    f"A mechanism exists by which the construction of {name_holistic} "
                    f"produces {p}={vh} beyond the tensor-product value {p}={vc}."
                )
            elif rank_h < rank_c:
                ctype = "reductive"
                claim = (
                    f"The construction of {name_holistic} actively suppresses {p} "
                    f"from {p}={vc} (component level) to {p}={vh} (functional level)."
                )
            else:
                # Same ordinal rank but different value — categorical conflict
                ctype = "categorical"
                claim = (
                    f"The holistic and compositional encodings assign categorically different "
                    f"values at {p}: holistic={vh}, compositional={vc}. "
                    f"These are incomparable — the conflict requires domain-specific resolution."
                )
            conflict_set.append(p)
            conflict_details.append({
                "primitive": p,
                "holistic_value": vh,
                "compositional_value": vc,
                "conflict_type": ctype,
                "emergence_claim": claim,
            })

        d_c = len(conflict_set) ** 0.5

        # Veracity classification
        n = len(conflict_set)
        if n == 0:
            veracity_class = "transparent"
            veracity_note = "Holistic = compositional across all primitives. No unresolved emergence claims."
        elif n <= 2:
            veracity_class = "near-grounded"
            veracity_note = f"{n} precisely identified emergence claim(s) at: {', '.join(conflict_set)}."
        elif n <= 6:
            veracity_class = "partial-emergence"
            veracity_note = f"{n} open claims. System is partially supported by construction."
        else:
            veracity_class = "aspirational"
            veracity_note = f"{n} conflicted primitives. Claimed tuple is largely unsupported by construction."

        result = {
            "status": "ok",
            "name_holistic": name_holistic,
            "name_compositional": name_compositional,
            "d_c": round(d_c, 4),
            "conflict_set": conflict_set,
            "conflict_details": conflict_details,
            "veracity_class": veracity_class,
            "veracity_note": veracity_note,
            "canonical_encoding": name_compositional if n > 0 else name_holistic,
            "interpretation": (
                f"d_c = √{n} = {round(d_c, 4)}. "
                f"Veracity class: {veracity_class}. "
                + (
                    f"The {n} conflicted primitive(s) are the structural address of "
                    f"the unresolved emergence claim(s). "
                    if n > 0 else
                    "Full structural transparency — no emergence gap."
                )
            ),
        }

        # Register for emergence_frontier tracking
        self._conflict_pairs.append({
            "name_holistic": name_holistic,
            "name_compositional": name_compositional,
            "conflict_set": conflict_set,
            "d_c": round(d_c, 4),
            "veracity_class": veracity_class,
        })

        return result

    def _emergence_frontier(self) -> Dict[str, Any]:
        """
        Report which primitives appear most frequently in conflict sets across all
        compute_conflict_distance calls in this session.
        """
        if not self._conflict_pairs:
            return {
                "status": "ok",
                "frontier": [],
                "note": "No conflict distance computations in this session yet. "
                        "Call compute_conflict_distance on holistic/compositional encoding pairs first.",
            }

        from collections import Counter
        counter: Counter = Counter()
        for pair in self._conflict_pairs:
            for p in pair["conflict_set"]:
                counter[p] += 1

        frontier = [
            {"primitive": p, "conflict_count": count, "fraction": round(count / len(self._conflict_pairs), 3)}
            for p, count in counter.most_common()
        ]

        # Summary statistics
        total_pairs = len(self._conflict_pairs)
        classes = Counter(pair["veracity_class"] for pair in self._conflict_pairs)

        return {
            "status": "ok",
            "session_conflict_pairs": total_pairs,
            "veracity_distribution": dict(classes),
            "frontier": frontier,
            "frontier_primitives": [f["primitive"] for f in frontier],
            "interpretation": (
                f"Emergence frontier across {total_pairs} conflict pair(s): "
                + (
                    f"dominant at {frontier[0]['primitive']} "
                    f"({frontier[0]['conflict_count']}/{total_pairs} pairs). "
                    if frontier else "no conflicted primitives found. "
                )
                + "The frontier primitive(s) name the deepest unresolved emergence questions "
                "in the domain under investigation."
            ),
        }

    # ── Promotion signature / inverse encoding ────────────────────────────────

    def _compute_promotions(self, name_source: str, name_target: str) -> Dict[str, Any]:
        """
        Compute the promotion signature Σ(source→target): which primitives were
        lifted (promoted in ordinal rank), demoted, or unchanged.

        Returns structured delta with full from/to values and direction labels.
        This is the deterministic half of the inverse-encoding workflow: it gives
        you the promotion signature; the model then reasons about what behaviors
        that signature predicts or explains.
        """
        src = self.catalog.get(name_source)
        tgt = self.catalog.get(name_target)
        missing = []
        if src is None:
            missing.append(name_source)
        if tgt is None:
            missing.append(name_target)
        if missing:
            return {"status": "error", "error": f"Unknown system(s): {missing}. Encode them first."}

        promotions: List[Dict[str, Any]] = []
        demotions:  List[Dict[str, Any]] = []
        unchanged:  List[str] = []

        for prim in PRIMITIVE_ORDER:
            sv = src.get(prim)
            tv = tgt.get(prim)
            if sv is None or tv is None:
                continue
            prim_ordinals = ORDINALS.get(prim, {})
            sr = prim_ordinals.get(sv, 0)
            tr = prim_ordinals.get(tv, 0)
            if tr > sr:
                promotions.append({"primitive": prim, "from": sv, "to": tv, "delta": tr - sr})
            elif tr < sr:
                demotions.append({"primitive": prim, "from": sv, "to": tv, "delta": sr - tr})
            else:
                unchanged.append(prim)

        sig = [p["primitive"] for p in promotions]
        return {
            "status": "ok",
            "source": name_source,
            "target": name_target,
            "promotion_signature": sig,
            "promotions": promotions,
            "demotions": demotions,
            "unchanged_count": len(unchanged),
            "summary": (
                f"{len(promotions)} promotion(s), {len(demotions)} demotion(s), "
                f"{len(unchanged)} unchanged across {len(PRIMITIVE_ORDER)} primitives. "
                f"Signature: [{', '.join(sig) if sig else 'none'}]"
            ),
        }

    def _predict_from_promotions(self, promoted_primitives: List[str]) -> Dict[str, Any]:
        """
        Given a promotion signature (list of promoted primitive names), look up
        the KB for matching patterns and return ranked predictions.

        Each match reports: the known behavior, which primitives overlap, coverage
        (how much of the known pattern is present), relevance (how much of the
        query is explained), and which query primitives are novel (not yet in KB).
        """
        if not self.promotion_kb:
            return {"status": "error", "error": "No PromotionKnowledgeBase loaded."}

        total = len(self.promotion_kb.all())
        if total == 0:
            return {
                "status": "empty_kb",
                "message": (
                    "The promotion knowledge base is empty. Call register_promotion_pattern "
                    "to seed it with known promotion→behavior mappings."
                ),
            }

        matches = self.promotion_kb.find(promoted_primitives, top_k=6)
        explained = {p for m in matches for p in m["matching_primitives"]}
        novel = sorted(set(promoted_primitives) - explained)

        return {
            "status": "ok",
            "query_signature": sorted(promoted_primitives),
            "kb_size": total,
            "matches": matches,
            "novel_primitives": novel,
            "interpretation": (
                f"{len(matches)} pattern(s) matched from {total} KB entries. "
                + (f"Novel (unexplained) promotions: {novel}. " if novel else "All query primitives matched. ")
                + ("Top prediction: " + matches[0]["behavior"] if matches else "No predictions available.")
            ),
        }

    def _register_promotion_pattern(
        self,
        promoted_primitives: List[str],
        behavior_description: str,
        example_system: str = "",
    ) -> Dict[str, Any]:
        """
        Register a promotion signature → behavior mapping in the persistent KB.

        Call this after confirming (via compute_promotions or structural analysis)
        that a set of primitive promotions from baseline reliably produces a named
        behavior.  The KB grows across sessions — future calls to
        predict_from_promotions will draw on these registered patterns.
        """
        if not self.promotion_kb:
            return {"status": "error", "error": "No PromotionKnowledgeBase loaded."}

        result = self.promotion_kb.add(
            promoted_primitives=promoted_primitives,
            behavior=behavior_description,
            example=example_system,
            session_seed=self._session_seed,
        )
        return result


# ── Local Qwen3 backend (merged2 / any HF-compatible model) ──────────────────

class LocalQwen3Backend:
    """
    Transformers backend for the SynthOmnicon-fine-tuned merged2 model.

    Mirrors the loading pattern from INFERRED/qw3n_stream.py:
      - NF4 4-bit quantization (BitsAndBytes double-quant)
      - YaRN RoPE scaling: factor=4.0, 32K → 131K context
      - attn_implementation=eager  (required for Qwen3 on this hw)
      - Thinking mode enabled by default
      - Tool calls parsed from <tool_call>...</tool_call> blocks
      - Tool results injected as <tool_response>...</tool_response> via chat template

    Parameters
    ----------
    model_path : str
        Path to the merged model directory (defaults to merged2).
    enable_thinking : bool
        Whether to prepend /think to prompts and strip <think> from output.
    max_new_tokens : int
        Generation budget per turn.
    """

    # Jinja tool-call tags emitted by merged2's chat template
    _TOOL_CALL_RE     = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
    _TOOL_RESP_RE     = re.compile(r"<tool_response>.*?</tool_response>", re.DOTALL)
    _THINK_RE         = re.compile(r"<think>.*?</think>", re.DOTALL)

    def __init__(
        self,
        model_path: str = _MERGED2_PATH,
        enable_thinking: bool = True,
        max_new_tokens: int = 4096,
    ):
        self.model_path = model_path
        self.enable_thinking = enable_thinking
        self.max_new_tokens = max_new_tokens
        self.model = None
        self.tokenizer = None

    def load(self):
        """Load model + tokenizer with the INFERRED config pattern."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            import torch
        except ImportError as e:
            raise RuntimeError(f"transformers / torch not available: {e}")

        _print(f"Loading model from: {self.model_path}")

        # ── Tokenizer ─────────────────────────────────────────────────────────
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True,
            use_fast=True,
            padding_side="left",
        )

        # ── Quantization (NF4 double-quant — from inferred.yaml) ──────────────
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )

        # ── Model config: inject YaRN RoPE before loading ─────────────────────
        from transformers import AutoConfig
        model_cfg = AutoConfig.from_pretrained(self.model_path, trust_remote_code=True)
        model_cfg.rope_scaling = {
            "rope_type": "yarn",
            "factor": 4.0,
            "original_max_position_embeddings": 32768,
        }
        model_cfg.max_position_embeddings = 131072  # 32768 * 4

        # ── Load weights ───────────────────────────────────────────────────────
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            config=model_cfg,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            attn_implementation="eager",
            use_safetensors=True,
        )
        self.model.eval()
        _print(f"Model loaded. Device map: {self.model.hf_device_map if hasattr(self.model, 'hf_device_map') else 'auto'}")

    def _build_prompt(self, messages: List[Dict], tools: List[Dict]) -> str:
        """Apply the model's native Jinja chat template with tool definitions."""
        return self.tokenizer.apply_chat_template(
            messages,
            tools=tools,
            tokenize=False,
            add_generation_prompt=True,
        )

    def _generate(self, prompt: str) -> str:
        """Run one generation pass. Returns raw model output string."""
        import torch

        inputs = self.tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].to(self.model.device)
        attention_mask = inputs.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.model.device)

        # Thinking mode: temperature/top_p from inferred.yaml thinking_mode block
        gen_kwargs: Dict[str, Any] = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": True,
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "min_p": 0.0,
            "repetition_penalty": 1.05,
            "use_cache": True,
        }
        if attention_mask is not None:
            gen_kwargs["attention_mask"] = attention_mask

        with torch.no_grad():
            output_ids = self.model.generate(input_ids, **gen_kwargs)

        # Decode only newly generated tokens
        new_ids = output_ids[0][input_ids.shape[-1]:]
        return self.tokenizer.decode(new_ids, skip_special_tokens=False)

    def _parse_tool_calls(self, raw: str) -> Tuple[str, List[Tuple[str, str, Dict]]]:
        """
        Extract <tool_call> blocks from raw output.
        Returns (text_without_calls, [(call_id, name, args_dict), ...]).
        """
        calls = []
        for i, match in enumerate(self._TOOL_CALL_RE.finditer(raw)):
            try:
                payload = json.loads(match.group(1))
                name = payload.get("name", "")
                args = payload.get("arguments", {})
                call_id = f"local_{i}"
                calls.append((call_id, name, args))
            except json.JSONDecodeError:
                pass  # malformed call — skip

        # Strip tool_call blocks, hallucinated tool_response blocks, and thinking
        text = self._TOOL_CALL_RE.sub("", raw)
        text = self._TOOL_RESP_RE.sub("", text)
        text = self._THINK_RE.sub("", text)
        text = text.replace("<|im_end|>", "").replace("<|im_start|>assistant", "").strip()
        return text, calls

    def call(
        self,
        messages: List[Dict],
        tools: List[Dict],
    ) -> Tuple[str, List[Tuple[str, str, Dict]], str]:
        """
        Single LLM turn. Returns (text, [(call_id, name, args), ...], raw_output).
        The raw_output is the full model string, used for threading tool results back.
        """
        if self.model is None:
            self.load()

        prompt = self._build_prompt(messages, tools)
        raw = self._generate(prompt)
        text, calls = self._parse_tool_calls(raw)
        return text, calls, raw

    def thread_tool_results(
        self,
        messages: List[Dict],
        raw_assistant: str,
        results: List[Tuple[str, str]],
    ) -> List[Dict]:
        """
        Append assistant turn + tool results to the messages list in the format
        expected by the Qwen3 chat template.
        """
        # Build tool_calls list from the raw assistant output for the chat template
        tool_calls_parsed = []
        for match in self._TOOL_CALL_RE.finditer(raw_assistant):
            try:
                payload = json.loads(match.group(1))
                tool_calls_parsed.append({
                    "function": {
                        "name": payload["name"],
                        "arguments": payload.get("arguments", {}),
                    }
                })
            except (json.JSONDecodeError, KeyError):
                pass

        # Extract clean text (no tool_call, no hallucinated tool_response, no think)
        assistant_text = self._TOOL_CALL_RE.sub("", raw_assistant)
        assistant_text = self._TOOL_RESP_RE.sub("", assistant_text)
        assistant_text = self._THINK_RE.sub("", assistant_text)
        assistant_text = assistant_text.replace("<|im_end|>", "").strip()

        assistant_msg: Dict[str, Any] = {"role": "assistant"}
        if assistant_text:
            assistant_msg["content"] = assistant_text
        if tool_calls_parsed:
            assistant_msg["tool_calls"] = tool_calls_parsed

        messages.append(assistant_msg)

        # Append one tool message per result
        for _call_id, content in results:
            messages.append({"role": "tool", "content": content})

        return messages


# ── The inquiry loop ──────────────────────────────────────────────────────────

class SynconInquiryLoop:
    """
    Open-ended SynthOmnicon inquiry loop.

    Parameters
    ----------
    seed : str
        Initial question or topic to investigate.
    model : str
        Model ID for the chosen provider.
    provider : str
        LLM provider. "anthropic" uses the Anthropic SDK;
        any other uses the OpenAI-compatible SDK.
    verbose : bool
        Print each iteration's tool calls and results.
    """

    def __init__(
        self,
        seed: str,
        model: str = "claude-sonnet-4-6",
        provider: str = "anthropic",
        verbose: bool = True,
        catalog_path: Optional[str] = CATALOG_PATH,
        insight_library_path: Optional[str] = None,
        promotion_kb_path: Optional[str] = PROMOTIONS_PATH,
    ):
        self.seed = _load_seed_text(seed)
        self.model = model
        self.provider = provider.lower()
        self.verbose = verbose
        self._use_anthropic = (self.provider == "anthropic")
        self._use_local_hf = (self.provider == "local_hf")
        self._use_gemini_native = (self.provider == "gemini")

        if self._use_local_hf:
            # Direct transformers path — no API key needed
            model_path = os.environ.get("LOCAL_MODEL", _MERGED2_PATH)
            self._local_backend = LocalQwen3Backend(
                model_path=model_path,
                enable_thinking=True,
                max_new_tokens=int(os.environ.get("SYNCON_MAX_NEW_TOKENS", "4096")),
            )
            self.client = None
        else:
            # Resolve API key
            api_key_env = _PROVIDER_API_KEY_ENV.get(
                self.provider, f"{self.provider.upper()}_API_KEY"
            )
            api_key = os.environ.get(api_key_env) or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError(
                    f"API key not found. Set {api_key_env} (or ANTHROPIC_API_KEY) in your environment."
                )

            if self._use_anthropic:
                import anthropic as _anthropic
                self.client = _anthropic.Anthropic(api_key=api_key)
            elif self._use_gemini_native:
                try:
                    from google import genai as _genai
                except ImportError:
                    raise RuntimeError("google-genai package required for Gemini: pip install google-genai")
                self.client = _genai.Client(api_key=api_key)
                self._gemini_tools = _build_gemini_tools()
                # Parallel content history for Gemini (Content objects, not dicts)
                self._gemini_contents: List[Any] = []
                # Maps synthetic call_id → function name for tool result threading
                self._gemini_call_id_to_name: Dict[str, str] = {}
            else:
                try:
                    import openai as _openai
                except ImportError:
                    raise RuntimeError("openai package required for non-Anthropic providers: pip install openai")
                base_url = _OPENAI_BASE_URLS.get(self.provider, f"https://api.{self.provider}.com/v1")
                local_key = api_key if api_key else "local"
                extra_headers: Dict[str, str] = {}
                if self.provider == "openrouter":
                    referer = os.environ.get("OPENROUTER_REFERER", "https://github.com/SynthOmnicon")
                    title   = os.environ.get("OPENROUTER_TITLE",   "SynthOmnicon Inquiry Loop")
                    extra_headers = {"HTTP-Referer": referer, "X-Title": title}
                self.client = _openai.OpenAI(
                    api_key=local_key,
                    base_url=base_url,
                    default_headers=extra_headers or None,
                )

        # Session state
        self.catalog = SessionCatalog(catalog_path=catalog_path)
        self._insight_library: Optional[InsightLibrary] = (
            InsightLibrary(path=insight_library_path) if insight_library_path else None
        )
        self._promotion_kb: Optional[PromotionKnowledgeBase] = (
            PromotionKnowledgeBase(path=promotion_kb_path) if promotion_kb_path else None
        )

        # Pre-register any synthon tuples embedded in the seed text.
        # Tuples written as ⟨val; …; val⟩ (or with ASCII < > brackets) with an
        # optional "name: " label are parsed and loaded into the catalog so the
        # model finds them already encoded on its first iteration.
        _seed_tuples = _parse_synthon_tuples(self.seed)
        _n_preloaded = 0
        for _idx, (_label, _pdict) in enumerate(_seed_tuples):
            _name = (_label or f"seed_synthon_{_idx}").strip().replace(" ", "_")
            if _name in self.catalog._entries:
                continue
            _result = self.catalog.encode(_name, "auto-parsed from seed text", **_pdict)
            if _result.get("status") == "ok":
                _n_preloaded += 1

        self.question_queue: List[str] = []
        self.insights: List[Insight] = []
        self.history: List[IterationRecord] = []
        self.dispatcher = ToolDispatcher(
            self.catalog, self.question_queue, self.insights,
            insight_library=self._insight_library,
            promotion_kb=self._promotion_kb,
            session_seed=self.seed,
        )
        # Build system prompt dynamically from the loaded catalog
        self._system_prompt = _build_system_prompt(self.catalog)
        # For local_hf, the system prompt lives in messages[0] (chat template handles it)
        self._messages: List[Dict] = (
            [{"role": "system", "content": self._system_prompt}]
            if self._use_local_hf else []
        )
        if verbose:
            n_persistent = sum(
                1 for name in self.catalog._entries
                if name not in self.catalog._builtin_names
            )
            if n_persistent:
                _print(f"  [dim green]Catalog:[/dim green] {n_persistent} persistent synthon(s) loaded from [dim]{catalog_path}[/dim]")
            if _n_preloaded:
                _print(f"  [dim green]Parsed:[/dim green]  {_n_preloaded} synthon tuple(s) pre-registered from seed text")
            if self._insight_library:
                n_insights = len(self._insight_library.all())
                if n_insights:
                    _print(f"  [dim green]Library:[/dim green] {n_insights} insight(s) loaded from [dim]{insight_library_path}[/dim]")
            if self._promotion_kb:
                n_patterns = len(self._promotion_kb.all())
                if n_patterns:
                    _print(f"  [dim green]Promotions KB:[/dim green] {n_patterns} pattern(s) loaded from [dim]{promotion_kb_path}[/dim]")

    def _log(self, msg: str):
        if self.verbose:
            _print(_render(msg))

    def _call_llm(self) -> Tuple[str, List[Tuple[str, str, Dict]], Any]:
        """Call the LLM. Returns (text, [(call_id, tool_name, kwargs), ...], raw)."""
        if self._use_local_hf:
            text, calls, raw = self._local_backend.call(self._messages, _TOOLS_OPENAI)
            return text, calls, raw

        if self._use_gemini_native:
            from google.genai import types as _gt
            # Sync the last _messages entry (user turn) into _gemini_contents.
            # _call_llm is always preceded by a user message append, so _messages[-1]
            # is the message we need to hand to Gemini.
            last = self._messages[-1]
            if last["role"] == "user":
                content_text = last["content"] if isinstance(last["content"], str) else str(last["content"])
                self._gemini_contents.append(
                    _gt.Content(role="user", parts=[_gt.Part(text=content_text)])
                )
            # Synthesis pass: use AUTO so Gemini can output CONCLUDE without
            # being forced to call a tool. All other turns: ANY forces tool use.
            _fc_mode = "AUTO" if getattr(self, "_in_synthesis_pass", False) else "ANY"
            resp = self.client.models.generate_content(
                model=self.model,
                contents=self._gemini_contents,
                config=_gt.GenerateContentConfig(
                    system_instruction=self._system_prompt,
                    tools=[self._gemini_tools] if self._gemini_tools else [],
                    tool_config=_gt.ToolConfig(
                        function_calling_config=_gt.FunctionCallingConfig(mode=_fc_mode)
                    ),
                    max_output_tokens=4096,
                ),
            )
            text = ""
            calls = []
            self._gemini_call_id_to_name = {}
            candidate = resp.candidates[0]
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    call_id = f"gemini_{len(calls)}_{fc.name}"
                    self._gemini_call_id_to_name[call_id] = fc.name
                    calls.append((call_id, fc.name, dict(fc.args)))
            # raw = (response, the model Content object to thread)
            return text, calls, (resp, candidate.content)

        if self._use_anthropic:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self._system_prompt,
                tools=_TOOLS_ANTHROPIC,
                messages=self._messages,
            )
            text = " ".join(b.text for b in resp.content if b.type == "text")
            calls = [
                (b.id, b.name, dict(b.input))
                for b in resp.content if b.type == "tool_use"
            ]
            return text, calls, resp.content
        else:
            # Gemini via OpenAI-compat endpoint requires tool_choice="auto" to
            # be explicit, otherwise it may emit tool calls as markdown text.
            _create_kwargs: Dict[str, Any] = dict(
                model=self.model,
                max_tokens=4096,
                tool_choice="auto",
                tools=_TOOLS_OPENAI,
                messages=[{"role": "system", "content": self._system_prompt}] + self._messages,
            )
            resp = self.client.chat.completions.create(**_create_kwargs)
            msg = resp.choices[0].message
            text = msg.content or ""
            calls = []
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    calls.append((tc.id, tc.function.name, json.loads(tc.function.arguments)))
            return text, calls, msg

    def _thread_assistant(self, raw: Any):
        if self._use_local_hf:
            return  # local backend threads assistant + tools together in _thread_tool_results

        if self._use_gemini_native:
            # raw = (response, candidate.content) — thread the Content into gemini history
            _resp, content = raw
            self._gemini_contents.append(content)
            return

        if self._use_anthropic:
            self._messages.append({"role": "assistant", "content": raw})
        else:
            entry: Dict[str, Any] = {"role": "assistant"}
            if raw.content:
                entry["content"] = raw.content
            if raw.tool_calls:
                entry["tool_calls"] = [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in raw.tool_calls
                ]
            self._messages.append(entry)

    def _thread_tool_results(self, results: List[Tuple[str, str]], raw: Any = None):
        if self._use_local_hf:
            self._local_backend.thread_tool_results(self._messages, raw, results)
            return

        if self._use_gemini_native:
            from google.genai import types as _gt
            # Build a single user Content with one FunctionResponse Part per call
            parts = []
            for call_id, result_json in results:
                fn_name = self._gemini_call_id_to_name.get(call_id, call_id)
                try:
                    response_dict = json.loads(result_json)
                except Exception:
                    response_dict = {"result": result_json}
                parts.append(_gt.Part(
                    function_response=_gt.FunctionResponse(
                        name=fn_name,
                        response=response_dict,
                    )
                ))
            self._gemini_contents.append(_gt.Content(role="tool", parts=parts))
            return

        if self._use_anthropic:
            self._messages.append({
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": cid, "content": content}
                    for cid, content in results
                ],
            })
        else:
            for cid, content in results:
                self._messages.append({"role": "tool", "tool_call_id": cid, "content": content})

    def _call_llm_notools(self, extra_messages: List[Dict]) -> str:
        """Call the LLM without tool definitions — for open-ended generation passes."""
        msgs = self._messages + extra_messages
        if self._use_local_hf:
            old, self._messages = self._messages, msgs
            text, _, _ = self._call_llm()
            self._messages = old
            return text
        if self._use_gemini_native:
            from google.genai import types as _gt
            # Build extra contents from extra_messages
            extra_contents = []
            for m in extra_messages:
                role = "user" if m["role"] in ("user", "system") else "model"
                text_val = m["content"] if isinstance(m["content"], str) else str(m["content"])
                extra_contents.append(_gt.Content(role=role, parts=[_gt.Part(text=text_val)]))
            resp = self.client.models.generate_content(
                model=self.model,
                contents=self._gemini_contents + extra_contents,
                config=_gt.GenerateContentConfig(
                    system_instruction=self._system_prompt,
                    max_output_tokens=4096,
                ),
            )
            parts = resp.candidates[0].content.parts
            return "".join(p.text for p in parts if hasattr(p, "text") and p.text)
        if self._use_anthropic:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self._system_prompt,
                messages=msgs,
            )
            return " ".join(b.text for b in resp.content if b.type == "text")
        else:
            resp = self.client.chat.completions.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "system", "content": self._system_prompt}] + msgs,
            )
            return resp.choices[0].message.content or ""

    _SPECULATION_PROMPT = textwrap.dedent("""\
        You have completed the grammatical analysis. The grammar has given its verdict.

        Now enter speculation mode.

        You are free from the primitive discipline. No tool calls, no encoding constraints.
        Given what the grammar revealed about the structure of this request, speculate openly
        on what it implies, what it entails, how to realize, or how it it all connects. 
        """)

    def _run_speculation_pass(self, iteration: int):
        """After CONCLUDE: one tool-free LLM call for open speculation on realization paths."""
        self._log(f"\n   [bold magenta]💭 Running speculation pass...[/bold magenta]")
        conclude_text = self.history[-1].model_text if self.history else ""
        extra: List[Dict] = []
        if conclude_text:
            extra.append({"role": "assistant", "content": conclude_text})
        extra.append({"role": "user", "content": self._SPECULATION_PROMPT})
        text = self._call_llm_notools(extra)
        if text:
            self._log(f"\n[bold magenta]{'─'*72}[/bold magenta]")
            self._log("[bold magenta]SPECULATION[/bold magenta]")
            self._log(f"[bold magenta]{'─'*72}[/bold magenta]")
            self._log(text)
        if self.history:
            self.history[-1].speculation_text = text

    def run(self, max_iterations: Optional[int] = None) -> List[IterationRecord]:
        """Run the inquiry loop. Returns the full iteration history."""
        self._log(f"\n[bold bright_cyan]{'='*72}[/bold bright_cyan]")
        self._log(f"[bold bright_cyan]SYNCON INQUIRY LOOP[/bold bright_cyan]")
        self._log(f"[bold bright_cyan]Seed:[/bold bright_cyan] {self.seed}")
        self._log(f"[bold bright_cyan]{'='*72}[/bold bright_cyan]\n")

        current_question = self.seed
        _stall_count = 0
        _MAX_STALLS = 2
        self._in_synthesis_pass = False

        # Patterns that suggest the model tried to call a tool via text rather
        # than via the native tool-calling interface.
        _STALL_PATTERNS = [
            "```tool_call", "default_api.", "<tool_call>", "print(default_api",
            "tool_use", "function_call",
        ]

        i = 0
        while max_iterations is None or i < max_iterations:
            self._log(f"\n[bold yellow]── Iteration {i+1} {'─'*55}[/bold yellow]")
            self._log(f"   [green]Question:[/green] {current_question}")

            record = IterationRecord(iteration=i + 1, question=current_question)

            # Build user message for this iteration
            user_msg = f"**Question for this iteration:**\n{current_question}"
            if i > 0:
                user_msg += (
                    f"\n\n**Session context:** {len(self.catalog.list_all())} systems encoded, "
                    f"{len(self.insights)} insights recorded so far."
                )
            if self.question_queue:
                user_msg += f"\n\n**Queued questions for later:** {json.dumps(self.question_queue)}"

            self._messages.append({"role": "user", "content": user_msg})

            # LLM turn
            text, calls, raw = self._call_llm()
            record.model_text = text

            if text:
                self._log(f"   [dim]Model: {text}[/dim]")

            # If no tool calls: CONCLUDE check, stall detection, or genuine stop.
            # (Gemini mode=ANY always produces tool calls, so this branch is for
            #  Anthropic / OpenAI-compat providers only in normal operation.)
            if not calls:
                if "CONCLUDE" in text:
                    record.concluded = True
                    self.history.append(record)
                    self._log(f"\n   [bold green]✅ Model concluded.[/bold green]")
                    self._run_speculation_pass(i)
                    break

                # Check whether the model was trying to call tools via text
                # (hallucinated code block, Python-style invocation, etc.)
                _looks_like_stall = any(p in text for p in _STALL_PATTERNS)

                if _looks_like_stall and _stall_count < _MAX_STALLS:
                    _stall_count += 1
                    self._log(
                        f"   [yellow]→ Model emitted tool call in text (stall {_stall_count}/{_MAX_STALLS}). "
                        f"Nudging to use native tool interface.[/yellow]"
                    )
                    # Thread the assistant turn so the nudge lands in context
                    self._thread_assistant(raw)
                    nudge = (
                        "Your previous response contained tool calls written as code or text "
                        "rather than as actual tool invocations. Please call the tools directly "
                        "using the tool calling interface — do not wrap them in code blocks or "
                        "Python syntax. Retry the tool call(s) you intended to make."
                    )
                    self._messages.append({"role": "user", "content": nudge})
                    # For Gemini native: also push nudge directly into the gemini
                    # content history (the loop will prepend a new user_msg before
                    # the next _call_llm call, so _messages[-1] sync alone misses it)
                    if self._use_gemini_native:
                        from google.genai import types as _gt
                        self._gemini_contents.append(
                            _gt.Content(role="user", parts=[_gt.Part(text=nudge)])
                        )
                    # Don't commit the stalled record; retry the same question
                    i += 1
                    continue

                # Genuine stop with no tools and no CONCLUDE
                record.concluded = False
                self.history.append(record)
                self._log("   [yellow]→ Model stopped without tools or CONCLUDE.[/yellow]")
                break

            self._thread_assistant(raw)

            # Execute tool calls
            tool_results: List[Tuple[str, str]] = []
            for call_id, tool_name, kwargs in calls:
                self._log(f"   [bold blue]Tool[/bold blue] [cyan]→ {tool_name}[/cyan]({json.dumps({k: v for k, v in kwargs.items() if k not in ('D','T','R','P','F','K','G','Gamma','Phi','H','S','Omega')}, ensure_ascii=False)})")
                result = self.dispatcher.dispatch(tool_name, kwargs, iteration=i + 1)
                record.tool_calls.append({"name": tool_name, "args": kwargs})
                record.tool_results.append(result)

                if tool_name == "ask_question":
                    record.questions_queued.append(kwargs.get("question", ""))
                elif tool_name == "record_insight":
                    # Already added to self.insights by dispatcher
                    record.insights_added = [ins for ins in self.insights if ins.iteration == i + 1]

                self._log(f"   [dim italic]Result: {json.dumps(result, ensure_ascii=False)}[/dim italic]")
                tool_results.append((call_id, json.dumps(result, ensure_ascii=False)))

            self._thread_tool_results(tool_results, raw=raw)
            self.history.append(record)

            # Check for CONCLUDE signal AFTER executing tools.
            # This ordering matters for Gemini (mode=ANY): the model may call a
            # tool (e.g. record_insight) AND output CONCLUDE in the same turn.
            # Executing the tools first ensures the insight is stored before we break.
            if "CONCLUDE" in text:
                record.concluded = True
                self._log(f"\n   [bold green]✅ Model concluded.[/bold green]")
                self._run_speculation_pass(i)
                break

            # Advance to next question from queue (if any)
            if self.question_queue:
                self._in_synthesis_pass = False
                current_question = self.question_queue.pop(0)
            else:
                # No queued questions — route to synthesis pass.
                # Flag enables mode=AUTO for Gemini so it can CONCLUDE without
                # being forced to make a tool call.
                self._in_synthesis_pass = True
                current_question = (
                    f"You have encoded {len(self.catalog.list_all())} systems and recorded "
                    f"{len(self.insights)} insights. Using the primitive structure you have "
                    f"identified, now reason directly toward an answer to the original question: "
                    f"'{self.seed}'. Do not merely summarize what the tools returned — derive "
                    f"structural conclusions, follow implications, and state what the grammar "
                    f"says. Then CONCLUDE."
                )
                self._log(f"\n   [yellow]→ No queued questions. Routing to synthesis pass.[/yellow]")

            i += 1

        self._print_summary()
        self._autosave()
        return self.history

    def _autosave(self):
        """Save full session to a timestamped JSON file; also update the persistent insight library."""
        import datetime
        out_dir = os.path.join(os.path.dirname(__file__), "syncon_outputs")
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = self.seed[:40].replace(" ", "_").replace("/", "-")
        path = os.path.join(out_dir, f"{ts}_{slug}.json")
        with open(path, "w") as f:
            json.dump(self.export_insights(), f, indent=2, ensure_ascii=False)
        self._log(f"\n  [bold green]Saved[/bold green] → [dim]{path}[/dim]")

        # Persist insights to the cross-session library
        if self._insight_library and self.insights:
            n_new = self._insight_library.add_batch(
                self.insights, seed=self.seed, run_file=path, catalog=self.catalog
            )
            self._log(f"  [bold green]Library:[/bold green] {n_new} new insight(s) added ([dim]{len(self._insight_library.all())} total[/dim])")

    _PLANE_COLORS = {"TOPO": "blue", "DIAPH": "yellow", "ONTO": "magenta"}
    _CONF_COLORS  = {"high": "green", "medium": "yellow", "speculative": "dim", "low": "dim"}

    def _print_summary(self):
        self._log(f"\n[bold bright_cyan]{'='*72}[/bold bright_cyan]")
        self._log("[bold bright_cyan]INQUIRY SUMMARY[/bold bright_cyan]")
        self._log(f"[bold bright_cyan]{'='*72}[/bold bright_cyan]")
        self._log(f"Iterations: {len(self.history)}")
        self._log(f"Systems encoded: {len(self.catalog.list_all())}")
        self._log(f"Insights: {len(self.insights)}")

        if self.insights:
            self._log("\nInsights by plane:")
            for plane in ["TOPO", "DIAPH", "ONTO"]:
                plane_insights = [ins for ins in self.insights if ins.plane == plane]
                if plane_insights:
                    color = self._PLANE_COLORS.get(plane, "white")
                    self._log(f"\n  [bold {color}][{plane}][/bold {color}]")
                    for ins in plane_insights:
                        conf_color = self._CONF_COLORS.get(ins.confidence, "white")
                        self._log(f"    ([{conf_color}]{ins.confidence}[/{conf_color}]) {ins.text}")

        # Translation cost summary across all encoded synthons
        all_catalog = self.catalog.list_all()
        if all_catalog and _TRANSLATE_AVAILABLE:
            agg = {"coherence_loss": 0.0, "criticality_loss": 0.0, "interaction_cost": 0.0, "total": 0.0}
            n_critical = 0
            for entry in all_catalog:
                sdict = self.catalog.get(entry["name"])
                if sdict:
                    cost = _translation_cost_from_dict(sdict)
                    for k in agg:
                        agg[k] += cost[k]
                    if sdict.get("Phi") == "Phi_c":
                        n_critical += 1
            self._log(f"\n[dim green]Translation cost (structural→classical, all {len(all_catalog)} synthons):[/dim green]")
            self._log(f"  [dim green]coherence:    {agg['coherence_loss']:.4f} nat[/dim green]")
            self._log(f"  [dim green]criticality:  {agg['criticality_loss']:.4f} nat  ({n_critical} Φ_c synthons × ln10)[/dim green]")
            self._log(f"  [dim green]interaction:  {agg['interaction_cost']:.4f} nat[/dim green]")
            self._log(f"  [dim green]total:        {agg['total']:.4f} nat[/dim green]")

        concluded = any(r.concluded for r in self.history)
        self._log(f"\n  [bold green]Inquiry concluded ✅[/bold green]" if concluded else f"\n  [bold yellow]Max iterations reached ⚠️[/bold yellow]")

        speculation = next(
            (r.speculation_text for r in reversed(self.history) if r.speculation_text), None
        )
        if speculation:
            self._log(f"\n[bold magenta]{'─'*72}[/bold magenta]")
            self._log("[bold magenta]SPECULATION[/bold magenta]")
            self._log(f"[bold magenta]{'─'*72}[/bold magenta]")
            self._log(speculation)

    def export_insights(self) -> Dict[str, Any]:
        """Export session insights as a structured dict (for saving or further processing)."""
        insight_dicts = []
        for ins in self.insights:
            d: Dict[str, Any] = {
                "text": ins.text,
                "plane": ins.plane,
                "confidence": ins.confidence,
                "iteration": ins.iteration,
            }
            if ins.translation:
                d["translation"] = ins.translation
            insight_dicts.append(d)

        # Session-level translation summary: aggregate over all catalog synthons
        all_catalog = self.catalog.list_all()
        session_translation: Dict[str, Any] = {"per_synthon": {}, "total": {}}
        if all_catalog and _TRANSLATE_AVAILABLE:
            agg = {"coherence_loss": 0.0, "criticality_loss": 0.0, "interaction_cost": 0.0, "total": 0.0}
            for entry in all_catalog:
                sdict = self.catalog.get(entry["name"])
                if sdict:
                    cost = _translation_cost_from_dict(sdict)
                    session_translation["per_synthon"][entry["name"]] = cost
                    for k in agg:
                        agg[k] = round(agg[k] + cost[k], 4)
            session_translation["total"] = agg

        # Session-level conflict summary: all conflict pairs + emergence frontier
        conflict_pairs = self.dispatcher._conflict_pairs if hasattr(self, "dispatcher") else []
        from collections import Counter as _Counter
        prim_counter: _Counter = _Counter()
        for pair in conflict_pairs:
            for p in pair.get("conflict_set", []):
                prim_counter[p] += 1
        frontier = [
            {"primitive": p, "conflict_count": c, "fraction": round(c / max(len(conflict_pairs), 1), 3)}
            for p, c in prim_counter.most_common()
        ]
        conflict_summary: Dict[str, Any] = {
            "pairs": conflict_pairs,
            "emergence_frontier": frontier,
            "veracity_distribution": dict(_Counter(p.get("veracity_class", "") for p in conflict_pairs)),
        }

        speculation = next(
            (r.speculation_text for r in reversed(self.history) if r.speculation_text), ""
        )

        return {
            "seed": self.seed,
            "model": self.model,
            "provider": self.provider,
            "iterations": len(self.history),
            "catalog": all_catalog,
            "insights": insight_dicts,
            "speculation": speculation,
            "translation_summary": session_translation,
            "conflict_summary": conflict_summary,
        }


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="syncon_inquiry",
        description="SynthOmnicon open-ended inquiry loop.",
    )
    parser.add_argument(
        "seed",
        nargs="?",
        default=None,
        help="Seed question or topic (default: built-in example question).",
    )
    parser.add_argument(
        "--no-catalog",
        action="store_true",
        help="Disable loading the persistent synthon catalog (syncon_catalog.json). "
             "Only the four hardcoded builtins are available.",
    )
    parser.add_argument(
        "--insights",
        action="store_true",
        help="Inject prior-session insights from syncon_insights.json into the system prompt. "
             "Disabled by default: prior interpretations can propagate errors across sessions.",
    )
    args = parser.parse_args()

    seed = args.seed or "What is the primitive distance between consciousness and quantum measurement?"

    provider = os.environ.get("SYNCON_PROVIDER", "anthropic")
    model_defaults = {
        "anthropic":  "claude-sonnet-4-6",
        "deepseek":   "deepseek-chat",
        "qwen":       "qwen-plus",
        "gemini":     "gemini-2.0-flash",
        "google":     "gemini-2.0-flash",
        "mistral":    "mistral-large-latest",
        "openrouter": "google/gemini-2.5-pro",
        "local":      os.environ.get("LOCAL_MODEL", "qwen3:8b"),
        "local_hf":   os.environ.get("LOCAL_MODEL", _MERGED2_PATH),
    }
    model = os.environ.get("SYNCON_MODEL", model_defaults.get(provider, "claude-sonnet-4-6"))
    _max_iter_env = os.environ.get("SYNCON_MAX_ITER")
    max_iter = int(_max_iter_env) if _max_iter_env else None

    catalog_path  = None         if args.no_catalog else CATALOG_PATH
    insights_path = INSIGHTS_PATH if args.insights   else None

    loop = SynconInquiryLoop(
        seed=seed,
        model=model,
        provider=provider,
        verbose=True,
        catalog_path=catalog_path,
        insight_library_path=insights_path,
    )
    loop.run(max_iterations=max_iter)

    # Optionally dump to JSON
    out_path = os.environ.get("SYNCON_OUT")
    if out_path:
        with open(out_path, "w") as f:
            json.dump(loop.export_insights(), f, indent=2)
        _print(f"\nExported to {out_path}")
