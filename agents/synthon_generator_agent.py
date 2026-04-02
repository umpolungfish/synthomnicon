"""
Synthon Generator Agent — AjintK-powered agent for automatic synthon generation.

This module implements an LLM agent that analyzes chemical descriptions,
SMILES strings, or natural language queries to automatically generate
Synthon objects with correctly assigned ten primitives.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


def _desc_slug(desc: str, maxlen: int = 60) -> str:
    """Slugify a description, truncating at a word boundary (no mid-word cuts)."""
    slug = desc.replace('-', ' ').replace('/', ' ').replace(' ', '_')
    if len(slug) <= maxlen:
        return slug
    truncated = slug[:maxlen].rsplit('_', 1)[0]
    return truncated or slug[:maxlen]

from framework import BaseAgent, ToolDefinitions
from synthomnicon import (
    Synthon, Dimensionality, Topology, RecognitionMode,
    Polarity, Fidelity, Granularity, InteractionGrammar,
    KineticCharacter, CriticalityPhase, Chirality,
    Protection, Stoichiometry,
    global_catalog, parse_notation
)
from synthomnicon.thermodynamics import compute_eta_CP, get_reference
from synthomnicon.criticality import analyze_criticality  # NEW


@dataclass
class SynthonGenerationResult:
    """Result of AI-powered synthon generation."""
    synthon: Synthon
    confidence: float  # 0.0-1.0 confidence in primitive assignments
    reasoning: str  # LLM explanation for assignments
    alternatives: List[Synthon] = field(default_factory=list)
    thermodynamic_metrics: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    grounding_status: str = "unverified"  # "full", "partial", "failed", "override", "unverified"
    failed_primitives: List[str] = field(default_factory=list)  # primitives that failed grounding


class GroundingBlockedError(Exception):
    """Raised when registration is blocked due to failed mechanistic grounding."""
    def __init__(self, failed_primitives: List[str]):
        self.failed_primitives = failed_primitives
        super().__init__(
            f"Registration blocked: ungrounded primitives {failed_primitives}. "
            f"Use strict_grounding=False to override, or fix primitive assignments. "
            f"Overrides are logged to the audit trail."
        )


class SynthonGeneratorAgent(BaseAgent):
    """
    AjintK agent for automatic synthon generation from chemical descriptions.

    This agent leverages LLM reasoning to:
    1. Parse natural language descriptions of chemical systems
    2. Analyze SMILES strings and molecular structures
    3. Assign all ten primitives based on chemical knowledge
    4. Generate unified notation
    5. Compute thermodynamic efficiency metrics
    6. Register generated synthons to the catalog

    Usage:
        from synthomnicon.provider_config import build_agent_config
        
        config = build_agent_config(provider="anthropic", model=None)
        agent = SynthonGeneratorAgent(config)
        result = await agent.generate_from_description(
            "carboxylic acid dimer with cyclic hydrogen bonding"
        )
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            agent_id="synthon_generator",
            name="Synthon Generator",
            description="AI-powered agent for automatic synthon generation from chemical descriptions",
            capabilities=[
                "natural_language_synthon_generation",
                "smiles_analysis",
                "primitive_assignment",
                "thermodynamic_analysis",
                "catalog_registration",
            ],
            config=config,
            persona="Expert in the Unified Synthonicon framework specializing in synthonic system analysis. "
                    "You excel at mapping any self-organizing system to the ten primitives: "
                    "Dimensionality (D), Topology (T), Recognition Mode (R), Polarity (P), "
                    "Fidelity (F), Kinetics (K), Granularity (G), Interaction Grammar (Γ), "
                    "Criticality (Φ), and Stoichiometry (S). "
                    "For molecular and supramolecular systems (primary validation tier) your analyses "
                    "are grounded in experimental data and chemical mechanism. "
                    "For cross-domain systems (extended tier) you use domain-appropriate physical grounding."
        )
        # Override provider setup to respect config strictly
        self.provider = self._setup_llm_provider_strict()

    def _setup_llm_provider_strict(self):
        """Setup LLM provider without fallback to Anthropic."""
        from framework.enhanced_llm_provider import get_llm_provider
        
        provider_name = self.config.get("provider", "anthropic")
        model = self.config.get("model", None)
        
        # Handle provider/model format like "deepseek/deepseek-chat"
        if "/" in provider_name:
            parts = provider_name.split("/", 1)
            provider_name = parts[0]
            model = parts[1] if len(parts) > 1 else model
        
        try:
            return get_llm_provider(provider_name, model=model)
        except ValueError as e:
            # Don't fallback - just raise
            raise e

    def _generate_rule_based(self, description: str, name: Optional[str] = None) -> SynthonGenerationResult:
        """
        Rule-based synthon generation fallback when no API keys available.
        Uses keyword matching and chemical heuristics.
        
        Extended to support ten primitives: D, T, R, P, F, K, G, Γ, Φ, S
        """
        description_lower = description.lower()

        # Keyword-based primitive assignment
        dimensionality = Dimensionality.MOLECULAR
        topology = Topology.LINEAR
        recognition_mode = RecognitionMode.NON_COVALENT
        polarity = Polarity.SELF_COMPLEMENTARY_PSEUDO  # Updated
        fidelity = Fidelity.MEDIUM
        kinetic_character = KineticCharacter.MODERATE  # NEW
        granularity = Granularity.LOCAL
        interaction_grammar = InteractionGrammar.SELECTIVE_AND  # Updated
        criticality_phase = None  # NEW
        chirality = None  # H — default None = H0 (achiral)

        reasoning_parts = []
        
        # Dimensionality detection
        if any(kw in description_lower for kw in ["crystal", "packing", "co-crystal", "supramolecular", "framework", "mof"]):
            dimensionality = Dimensionality.SUPRAMOLECULAR
            reasoning_parts.append("Supramolecular domain detected (crystal packing/framework).")
        elif any(kw in description_lower for kw in ["cycle", "catalytic", "oscillator", "temporal", "reaction cycle"]):
            dimensionality = Dimensionality.TEMPORAL
            reasoning_parts.append("Temporal domain detected (catalytic cycle/oscillator).")
        else:
            reasoning_parts.append("Molecular domain (point-like reactivity).")
        
        # Topology detection
        if any(kw in description_lower for kw in ["dimer", "cyclic", "ring", "r22(8)", "r₂²(8)"]):
            topology = Topology.CYCLIC_BOWTIE
            reasoning_parts.append("Cyclic topology (dimer/ring motif).")
        elif any(kw in description_lower for kw in ["chain", "catemer", "polymer", "linear"]):
            topology = Topology.CHAIN
            reasoning_parts.append("Chain topology (catemer/polymer).")
        elif any(kw in description_lower for kw in ["network", "framework", "3d"]):
            topology = Topology.NETWORK
            reasoning_parts.append("Network topology (3D framework).")
        
        # Recognition mode detection
        if any(kw in description_lower for kw in ["hydrogen bond", "h-bond", "h bond"]):
            recognition_mode = RecognitionMode.NON_COVALENT
            reasoning_parts.append("Non-covalent recognition (hydrogen bonding).")
        elif any(kw in description_lower for kw in ["covalent", "bond formation"]):
            recognition_mode = RecognitionMode.COVALENT
            reasoning_parts.append("Covalent recognition mode.")
        elif any(kw in description_lower for kw in ["catalytic", "dynamic", "reversible"]):
            recognition_mode = RecognitionMode.DYNAMIC_CATALYTIC
            reasoning_parts.append("Dynamic catalytic recognition.")
        elif any(kw in description_lower for kw in ["halogen bond", "x-bond", "σ-hole", "sigma-hole"]):
            recognition_mode = RecognitionMode.NON_COVALENT
            reasoning_parts.append("Non-covalent recognition (halogen bonding).")
        elif any(kw in description_lower for kw in ["mechanical", "rotaxane", "catenane", "interlocked"]):
            recognition_mode = RecognitionMode.MECHANICAL
            reasoning_parts.append("Mechanical bond recognition.")
        
        # Polarity detection
        if any(kw in description_lower for kw in ["acid", "carboxylic", "amide", "self-complementary", "homodimer"]):
            polarity = Polarity.SELF_COMPLEMENTARY_SYM
            reasoning_parts.append("Self-complementary polarity (acid/amide motif).")
        elif any(kw in description_lower for kw in ["pyridine", "base", "acceptor"]):
            polarity = Polarity.ACCEPTOR
            reasoning_parts.append("Acceptor polarity (basic site).")
        elif any(kw in description_lower for kw in ["donor", "nucleophile", "anion"]):
            polarity = Polarity.DONOR
            reasoning_parts.append("Donor polarity (nucleophilic site).")
        elif any(kw in description_lower for kw in ["hetero", "acid-base", "co-crystal"]):
            polarity = Polarity.DONOR_ACCEPTOR
            reasoning_parts.append("Directional donor-acceptor polarity.")
        
        # Fidelity detection
        # F_hbar: geometry-enforcing, >9 bits — lock-and-key, triple H-bond, tight cage binding
        if any(kw in description_lower for kw in [
            "robust", "reliable", "classic", "high-fidelity", "f_hbar", "f_ℏ",
            "lock-and-key", "triple h-bond", "triple hydrogen bond", "dad·ada", "dad-ada",
            "geometry-enforcing", "geometry enforcing", "cucurbituril", "cb[7]", "cb[8]",
            "cryptand", "carceplex", "specific recognition", "enantioselective",
            "shape complementary", "tight binding", "picomolar", "nanomolar affinity",
        ]):
            fidelity = Fidelity.HIGH
            reasoning_parts.append("High fidelity (geometry-enforcing, >9 bits).")
        # F_ell: probabilistic, <6 bits — weak/promiscuous/metastable interactions
        elif any(kw in description_lower for kw in [
            "weak", "probabilistic", "low-fidelity", "f_ell", "f_ℓ",
            "promiscuous", "nonspecific", "non-specific", "van der waals",
            "π-stacking", "pi-stacking", "pi stacking", "metastable", "competition-sensitive",
            "low affinity", "micromolar", "millimolar", "dispersion-dominated",
        ]):
            fidelity = Fidelity.LOW
            reasoning_parts.append("Low fidelity (probabilistic, <6 bits).")
        else:
            fidelity = Fidelity.MEDIUM
            reasoning_parts.append("Medium fidelity (context-dependent, 6–9 bits).")
        
        # Kinetic character detection (ΔG‡ for constraint rearrangement)
        # K_trap: metastable, locked — cannot reach thermodynamic minimum without perturbation
        if any(kw in description_lower for kw in [
            "k_trap", "kinetic trap", "trapped", "metastable", "glass", "amorphous",
            "locked", "irreversible", "quenched", "frozen glass", "kinetically locked",
            "cannot equilibrate", "oxygen triplet", "triplet ground state", "spin-forbidden",
            "persistent radical", "conformationally locked",
        ]):
            kinetic_character = KineticCharacter.TRAP
            reasoning_parts.append("Kinetic trap (metastable, cannot equilibrate without perturbation).")
        # K_slow: ΔG‡ > 100 kJ/mol — frozen, ordered, crystalline, persistent
        elif any(kw in description_lower for kw in [
            "k_slow", "crystalline", "crystal", "ordered phase", "slow exchange",
            "persistent", "arrested", "high barrier", "solid-state", "solid state",
            "100 kj", "150 kj", "200 kj", "non-labile", "nonlabile", "inert",
            "proton-ordered", "proton ordered", "co-crystal", "polymorph",
        ]):
            kinetic_character = KineticCharacter.SLOW
            reasoning_parts.append("K_slow (ΔG‡ > 100 kJ/mol — crystalline/ordered/persistent).")
        # K_fast: ΔG‡ < 60 kJ/mol — rapid exchange, diffusion-limited, proton transfer
        elif any(kw in description_lower for kw in [
            "k_fast", "fast exchange", "rapid", "diffusion-limited", "diffusion limited",
            "barrierless", "fluxional", "proton transfer", "proton shuttle", "labile",
            "fast dynamics", "nanosecond", "picosecond", "femtosecond",
            "low barrier", "< 60 kj", "room temperature exchange", "fast equilibrium",
            "solution exchange", "solvent exchange", "enzyme turnover", "kcat",
        ]):
            kinetic_character = KineticCharacter.FAST
            reasoning_parts.append("K_fast (ΔG‡ < 60 kJ/mol — rapid exchange/dynamics).")
        else:
            # Topology-based inference for K when keywords absent
            if topology in [Topology.CAGE, Topology.NETWORK] or any(
                kw in description_lower for kw in ["cage", "encapsulat", "cucurbit", "cryptand", "carceplex"]
            ):
                kinetic_character = KineticCharacter.SLOW
                reasoning_parts.append("K_slow inferred from cage/network topology (encapsulation barrier).")
            elif topology == Topology.BOWL or any(
                kw in description_lower for kw in ["calix", "resorcinarene", "pillar[", "bowl", "open cavity"]
            ):
                kinetic_character = KineticCharacter.FAST
                reasoning_parts.append("K_fast inferred from bowl topology (open portal, RT exchange).")
            else:
                kinetic_character = KineticCharacter.MODERATE
                reasoning_parts.append("K_mod (ΔG‡ 60–100 kJ/mol — no strong barrier indicator).")

        # Criticality phase detection (Φ)
        if any(kw in description_lower for kw in [
            "phi_c", "critical", "criticality", "scale-free", "scale free", "diverging",
            "percolation threshold", "self-organized criticality", "soc", "phase transition",
            "bifurcation", "tipping point", "second-order transition", "continuous transition",
            "power law", "power-law", "1/f noise", "avalanche", "autocatalytic amplification",
            "symmetry breaking", "spontaneous", "emergence", "emergent", "condensate",
        ]):
            criticality_phase = CriticalityPhase.CRITICAL
            reasoning_parts.append("Φ_c (critical phase — scale-free, diverging correlations).")
        elif any(kw in description_lower for kw in [
            "phi_super", "supercritical", "post-assembly", "fully assembled", "saturated",
            "completed", "mature", "post-transition",
        ]):
            criticality_phase = CriticalityPhase.SUPERCRITICAL
            reasoning_parts.append("Φ_super (post-assembly / supercritical).")
        else:
            criticality_phase = CriticalityPhase.SUBCRITICAL
            reasoning_parts.append("Φ_sub (subcritical — normal assembly, no critical divergence).")

        # Chirality (H) detection
        # H_inf: topology-protected — trefoil knots, catenanes, Solomon links
        if any(kw in description_lower for kw in [
            "h_inf", "h_∞", "topological chirality", "topologically chiral",
            "trefoil knot", "solomon link", "mechanical chirality",
            "topology-protected chirality", "knot chirality",
        ]):
            chirality = Chirality.H_inf
            reasoning_parts.append("H_∞ (topologically chiral — topology-protected, implies K_trap).")
        # H2: persistent chirality — amino acids, DNA, proteins, Soai, enantioselective catalysis
        elif any(kw in description_lower for kw in [
            "h2", "chiral", "enantioselective", "enantiomer", "enantiopure",
            "asymmetric catalysis", "asymmetric synthesis", "optically active",
            "amino acid", "l-alanine", "d-alanine", "l-proline", "d-proline",
            "peptide", "protein", "enzyme", "dna", "rna", "nucleotide", "nucleoside",
            "helix", "helical", "soai", "chiral amplification", "enantiomeric excess",
            "ee ", "quartz", "homochiral", "heterochiral", "chirality transfer",
            "point chirality", "axial chirality", "planar chirality",
            "asymmetric induction", "chiral recognition", "enantiospecific",
        ]):
            chirality = Chirality.H2
            reasoning_parts.append("H₂ (persistent chirality — multiple reinforcing axes, memory depth n).")
        # H1: soft/dynamic chirality — atropisomers, dynamic helices
        elif any(kw in description_lower for kw in [
            "h1", "atropisomer", "atropoisomer", "dynamic helix", "dynamic chirality",
            "configurationally labile", "torsional chirality", "conformational chirality",
            "pseudochiral", "prochiral",
        ]):
            chirality = Chirality.H1
            reasoning_parts.append("H₁ (soft chiral — single axis, thermally interconvertible).")
        else:
            chirality = Chirality.H0
            reasoning_parts.append("H₀ (achiral — no persistent symmetry breaking detected).")

        # Granularity detection
        if any(kw in description_lower for kw in ["network", "framework", "global", "extended"]):
            granularity = Granularity.GLOBAL
            reasoning_parts.append("Global granularity (network-scale control).")
        elif any(kw in description_lower for kw in ["motif", "cluster", "mesoscale"]):
            granularity = Granularity.MESOSCALE
            reasoning_parts.append("Mesoscale granularity (motif-level control).")
        else:
            granularity = Granularity.LOCAL
            reasoning_parts.append("Local granularity (single interaction).")
        
        # Interaction grammar detection
        if any(kw in description_lower for kw in ["specific", "lock-and-key", "otimes"]):
            interaction_grammar = InteractionGrammar.SPECIFIC_AND
            reasoning_parts.append("Specific interaction grammar (one partner).")
        elif any(kw in description_lower for kw in ["broad", "promiscuous", "many partners"]):
            interaction_grammar = InteractionGrammar.BROAD_AND
            reasoning_parts.append("Broad interaction grammar (many partners).")
        else:
            interaction_grammar = InteractionGrammar.SELECTIVE_AND
            reasoning_parts.append("Selective interaction grammar (3-10 partners).")
        
        # Stoichiometry detection (rule-based)
        stoichiometry_str = None
        if topology == Topology.CYCLIC_BOWTIE and polarity == Polarity.SELF_COMPLEMENTARY_SYM:
            stoichiometry_str = "1:1"
        elif any(kw in description_lower for kw in ["homodimer", "1:1", "symmetric dimer"]):
            stoichiometry_str = "1:1"
        elif any(kw in description_lower for kw in ["heterodimer", "co-crystal", "1:2", "2:1"]):
            stoichiometry_str = "n:m"
        stoichiometry = Stoichiometry.from_symbol(stoichiometry_str) if stoichiometry_str else Stoichiometry.n_m

        # Generate name if not provided
        synthon_name = name or _desc_slug(description)

        synthon = Synthon(
            name=synthon_name,
            dimensionality=dimensionality,
            topology=topology,
            recognition_mode=recognition_mode,
            polarity=polarity,
            fidelity=fidelity,
            kinetic_character=kinetic_character,
            granularity=granularity,
            grammar=interaction_grammar,
            criticality_phase=criticality_phase,
            chirality=chirality,
            protection=Protection.Omega_0,
            stoichiometry=stoichiometry,
            description=description,
            metadata={"auto_generated": True, "generation_method": "rule_based"}
        )
        
        return SynthonGenerationResult(
            synthon=synthon,
            confidence=0.65,  # Lower confidence for rule-based
            reasoning="Rule-based analysis (no API key available): " + " ".join(reasoning_parts),
            alternatives=[],
            thermodynamic_metrics=None,
            metadata={
                "input_description": description,
                "generation_method": "rule_based",
                "provider": "rule_based_fallback"
            }
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """Declare tools available for autonomous synthon generation."""
        return [
            ToolDefinitions.file_read(),
            ToolDefinitions.file_write(),
            ToolDefinitions.json_load(),
            ToolDefinitions.json_save(),
            ToolDefinitions.run_command(),
        ]

    async def generate_from_description(
        self,
        description: str,
        name: Optional[str] = None,
        delta_g: Optional[float] = None,
        auto_register: bool = True,
        require_grounding: bool = False,  # NEW: Require mechanistic grounding
        smiles: Optional[str] = None,  # NEW: For RDKit ΔG estimation
    ) -> SynthonGenerationResult:
        """
        Generate a synthon from a natural language description.

        Args:
            description: Chemical description (e.g., "carboxylic acid dimer with cyclic H-bonding")
            name: Optional name for the synthon (auto-generated if not provided)
            delta_g: Optional free energy value for thermodynamic analysis
            auto_register: Whether to automatically register to catalog
            require_grounding: Whether to require mechanistic grounding validation
            smiles: Optional SMILES for RDKit-based ΔG estimation

        Returns:
            SynthonGenerationResult with generated synthon and analysis
        """
        # Extract mechanistic justifications if grounding requested
        grounding_result = None
        if require_grounding or smiles:
            try:
                from synthomnicon.llm_grounding import extract_and_validate
                is_valid, grounding_result = extract_and_validate(
                    description, smiles=smiles, require_full_grounding=require_grounding
                )
                
                # Use extracted ΔG if not provided
                if delta_g is None and grounding_result.delta_g_value is not None:
                    delta_g = grounding_result.delta_g_value
                    
            except ImportError:
                if require_grounding:
                    raise RuntimeError("LLM grounding module not available but required")
                # Otherwise continue without grounding

        # Build the analysis prompt
        prompt = self._build_generation_prompt(description, name)

        try:
            # Call LLM for synthon generation
            raw_response = await self.call_llm(
                prompt=prompt,
                max_tokens=self.config.get("max_tokens", 4000),
                temperature=0.3,  # Lower temperature for more deterministic output
                system=self._get_system_prompt()
            )

            # Parse the response
            synthon_data, reasoning, confidence, alternatives = self._parse_llm_response(raw_response)

            # Create the synthon — pass explicit name so goal-derived slug wins
            synthon = self._create_synthon_from_data(synthon_data, description, explicit_name=name)

        except Exception as e:
            # Fall back to rule-based generation
            console = None
            try:
                from rich.console import Console
                console = Console()
                console.print(f"[yellow]LLM API failed ({type(e).__name__}), using rule-based fallback...[/yellow]")
            except:
                pass

            return self._generate_rule_based(description, name)

        # Compute thermodynamic metrics if delta_g provided
        thermo_metrics = None
        if delta_g is not None:
            try:
                result = compute_eta_CP(synthon, delta_g)
                thermo_metrics = {
                    "delta_g": delta_g,
                    "eta_CP": result.eta_CP,
                    "xi_CP": result.xi_CP,
                    "efficiency_description": result.efficiency_description,
                }
                # Append calibrated I(bits) if available
                try:
                    from synthomnicon.information import calibrate_I_pipeline
                    cal = calibrate_I_pipeline()
                    thermo_metrics["I_bits_calibrated"] = {
                        "acid_dimer": cal.acid_dimer_result,
                        "triple_hbond": cal.triple_hbond_result,
                        "proline_cycle": cal.proline_cycle_result,
                        "all_pass": cal.all_pass,
                    }
                except Exception:
                    pass
            except Exception:
                thermo_metrics = {"delta_g": delta_g, "error": "Could not compute metrics"}

        # --- Grounding gate ---
        # Determine grounding status and failed primitives from grounding_result
        grounding_status = "unverified"
        failed_primitives = []

        if grounding_result is not None:
            if grounding_result.is_fully_grounded:
                grounding_status = "full"
            else:
                grounding_status = "partial"
                # Extract which primitives failed if the grounding result provides them
                if hasattr(grounding_result, "failed_primitives"):
                    failed_primitives = grounding_result.failed_primitives
                else:
                    # Fall back: mark all as suspect if we can't determine specifics
                    failed_primitives = ["unspecified — run with --use-llm-grounding for details"]

        # Axiom 6: D_∞ requires a named closed cycle — check independently of grounding module
        if synthon.dimensionality == Dimensionality.TEMPORAL:
            reasoning_lower = reasoning.lower()
            reset_indicators = ["reset", "reform", "regenerat", "hydroly", "return",
                                 "cycle", "turnover", "re-form", "dissipat", "release"]
            process_indicators = ["catalyz", "oxidat", "reduct", "transfer",
                                   "phosphoryl", "condensat", "oscillat", "periodic", "aldol"]
            has_reset = any(kw in reasoning_lower for kw in reset_indicators)
            has_process = any(kw in reasoning_lower for kw in process_indicators)
            if not (has_reset and has_process):
                if "dimensionality" not in failed_primitives:
                    failed_primitives.append("dimensionality (D_∞ assigned but no closed cycle specified)")
                grounding_status = "partial"

        # Axiom 7: T_⋈ requires a named closing bond — check independently
        if synthon.topology == Topology.CYCLIC_BOWTIE:
            reasoning_lower = reasoning.lower()
            closing_indicators = ["hydrogen bond", "h-bond", "hbond", "coordinat", "covalent",
                                   "close", "ring", "loop", "cycl", "r2_2", "r22", "macrocycle",
                                   "crown", "cryptand", "rotaxane", "caten", "dimer"]
            invalid_indicators = ["linear", " rod", "chain", "axial", "two-ended", "terminus",
                                   "cumulene", "allene"]
            has_invalid = any(kw in reasoning_lower for kw in invalid_indicators)
            has_closing = any(kw in reasoning_lower for kw in closing_indicators)
            if has_invalid or not has_closing:
                if "topology" not in failed_primitives:
                    failed_primitives.append("topology (T_⋈ assigned but no closing bond/interaction named)")
                grounding_status = "partial"

        # Registration block
        strict = require_grounding  # strict_grounding mirrors require_grounding for now
        override = kwargs.get("override_grounding", False) if hasattr(self, "_kwargs") else False
        override_reason = kwargs.get("override_reason", None) if hasattr(self, "_kwargs") else None

        if strict and failed_primitives and not override:
            raise GroundingBlockedError(failed_primitives)

        if strict and failed_primitives and override:
            # Log to audit trail in metadata
            grounding_status = "override"
            import datetime
            audit_entry = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "failed_primitives": failed_primitives,
                "override_reason": override_reason or "No reason provided",
                "provider": self.config.get("provider"),
                "model": self.config.get("model"),
            }
            # Append to a persistent audit log if catalog supports it
            try:
                global_catalog.log_grounding_override(synthon.name, audit_entry)
            except AttributeError:
                pass  # Catalog doesn't support audit logging yet — Fix 1b for Qwen

        # Register to catalog if requested
        if auto_register and synthon.name not in global_catalog:
            # Tag catalog entry with grounding status
            synthon.metadata["grounding_status"] = grounding_status
            synthon.metadata["failed_primitives"] = failed_primitives
            if failed_primitives:
                synthon.metadata["flagged_for_review"] = True
            global_catalog.register(synthon)

        # Build result metadata with grounding info
        metadata = {
            "input_description": description,
            "provider": self.config.get("provider"),
            "model": self.config.get("model"),
        }

        if grounding_result:
            metadata["grounding"] = {
                "is_fully_grounded": grounding_result.is_fully_grounded,
                "justifications": grounding_result.justifications,
                "delta_g_value": grounding_result.delta_g_value,
                "delta_g_justification": grounding_result.delta_g_justification,
                "confidence": grounding_result.confidence,
            }

        return SynthonGenerationResult(
            synthon=synthon,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            thermodynamic_metrics=thermo_metrics,
            metadata=metadata,
            grounding_status=grounding_status,
            failed_primitives=failed_primitives,
        )

    async def generate_from_smiles(
        self,
        smiles: str,
        name: Optional[str] = None,
        functional_groups: Optional[List[str]] = None,
        auto_register: bool = True,
    ) -> SynthonGenerationResult:
        """
        Generate a synthon from a SMILES string.

        Args:
            smiles: SMILES string of the molecule
            name: Optional name for the synthon
            functional_groups: Optional list of functional groups to consider
            auto_register: Whether to automatically register to catalog

        Returns:
            SynthonGenerationResult with generated synthon and analysis
        """
        # Build the SMILES analysis prompt
        prompt = self._build_smiles_prompt(smiles, functional_groups)

        # Call LLM for SMILES analysis
        raw_response = await self.call_llm(
            prompt=prompt,
            max_tokens=self.config.get("max_tokens", 4000),
            temperature=0.2,  # Even lower for structure analysis
            system=self._get_system_prompt()
        )

        # Parse the response
        synthon_data, reasoning, confidence, alternatives = self._parse_llm_response(raw_response)

        # Create the synthon — explicit name or derive from SMILES prefix
        synthon_name = name or f"synthon_{smiles[:20].replace('/', '_').replace('\\', '_')}"
        synthon = self._create_synthon_from_data(synthon_data, f"SMILES: {smiles}", explicit_name=synthon_name)
        synthon.metadata["smiles"] = smiles

        # Register to catalog if requested
        if auto_register and synthon.name not in global_catalog:
            global_catalog.register(synthon)

        return SynthonGenerationResult(
            synthon=synthon,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            metadata={
                "input_smiles": smiles,
                "functional_groups": functional_groups or [],
                "provider": self.config.get("provider"),
                "model": self.config.get("model"),
            }
        )

    async def generate_batch(
        self,
        descriptions: List[str],
        names: Optional[List[str]] = None,
        auto_register: bool = True,
    ) -> List[SynthonGenerationResult]:
        """
        Generate multiple synthons in batch.

        Args:
            descriptions: List of chemical descriptions
            names: Optional list of names (must match length of descriptions)
            auto_register: Whether to automatically register to catalog

        Returns:
            List of SynthonGenerationResult objects
        """
        if names is None:
            names = [None] * len(descriptions)

        results = []
        for desc, name in zip(descriptions, names):
            try:
                result = await self.generate_from_description(desc, name, auto_register=auto_register)
                results.append(result)
            except Exception as e:
                results.append(SynthonGenerationResult(
                    synthon=None,
                    confidence=0.0,
                    reasoning=f"Error: {str(e)}",
                    metadata={"error": str(e)}
                ))

        return results

    def _get_system_prompt(self) -> str:
        """Get the system prompt for synthon generation."""
        return """<role>You are an expert in the Unified Synthonicon framework — a **domain-agnostic** information-theoretic and thermodynamic language for encoding self-organizing systems. The framework applies equally to: molecular H-bond complexes, bulk crystal polymorphs, biological catalytic cycles, synthetic host-guest systems, and any other process that propagates constraints through an environment. Your encoding must be grounded in **physics and information theory**, not in chemical template matching.</role>

<task>You **MUST** analyze the provided **self-organizing system** and map it to all twelve primitives (D, T, R, P, F, K, G, Γ, Φ, H, S, Ω) with **PHYSICAL AND INFORMATION-THEORETIC ACCURACY**. Do NOT pattern-match to chemical templates. For each primitive, reason from first principles: What is the energy barrier? How much information is transmitted? At what length scale does constraint propagate? Does the system break orientational symmetry persistently?</task>

<primitives>
1. **Dimensionality (D)**: Where does this synthon operate?
   - **D_wedge** (D_∧): Molecular domain — point-like reactivity
   - **D_triangle** (D_△): Supramolecular domain — 3D crystal packing
   - **D_infinity** (D_∞): Temporal domain — periodic sequences/cycles

2. **Topology (T)**: What is the connectivity pattern?
   - **T_cage** (T_□□): Guest ENCLOSED in 3D — egress requires framework distortion; K_slow/K_trap default.
     **Examples: cucurbiturils (CB[6], CB[7], CB[8]), cryptands, carceplexes, self-assembled metal-organic
     cages, COCs, Fujita spheres.** Keywords: "cage", "capsule", "encapsulat", "cucurbit", "cryptand",
     "carceplex", "carcerand". If fully enclosed → T_□□.
   - **T_bowl** (T_∪): **Open concave cavity — single portal, guest enters/exits freely; K_fast default.**
     **Examples: calix[4]arene, calix[6]arene, calix[4]pyrrole, calix[4]resorcinarene, resorcinarene,
     pillar[n]arene, cyclotriveratrylene (CTV), corannulene, cavitand (uncapped), hemicarceplex.**
     **If the name contains "calix", "resorcinarene", "pillar[", "calixpyrrole", "bowl", or "upper/lower
     rim" → USE T_∪, NOT T_□□ and NOT T_⋈.** The key test: can a guest exchange at room temperature
     through an open portal? Yes → T_∪. Sealed in, requires distortion to escape? → T_□□.
   - **T_bowtie** (T_⋈): Planar cyclic dimers — two partners form a CLOSED ring of contacts at their
     INTERFACE. Requires a named closing bond (e.g., "two O-H···O bonds close the R²₂(8) ring"). Use for:
     carboxylic acid dimers, DNA base pairs, urea dimers. NOT for hosts/guests, NOT for cages, NOT for bowls.
   - **T_chains** (T_≫): Open-ended chain growth (polymers, columnar stacks)
   - **T_square** (T_□): Hub/node structures (MOF SBUs, dendrimer cores)
   - **T_linear** (T_|): Strict one-dimensional head-to-tail arrangement, no branching
   - **T_branched** (T_⊥): Main chain with pendant side groups or orthogonal arms
   - **T_network** (T_∈): Generic network — use a sub-label when ring topology is known:
     - **T_network_hex** (T_∈(hex)): 6-membered rings only — graphene, ice Ih/Ic/XI, honeycomb MOFs, hex-COFs
     - **T_network_mixed** (T_∈(mixed)): mixed ring sizes — ice III/IV/V/IX, amorphous/strained networks
     - **T_network_interp** (T_∈(×2)): two interpenetrating independent sub-networks — ice VI/VII/VIII, interpenetrating MOFs
     - **T_network_sym** (T_∈(sym)): centrosymmetric bonding — ice X (symmetric O-H-O), superionic phases

3. **Recognition Mode (R)**: What physical mechanism enables interaction?
   - **R_superset** (R_⊇): **NON-COVALENT** — hydrogen bonds, H-bonds, halogen bonds, π-stacking, van der Waals,
     electrostatics, coordination bonds, host-guest, ionic. **Use this for water H-bond networks, CB[n] complexes,
     ammonium/crown-ether, metal coordination, base pairs, carboxylic acid dimers.** No bond making/breaking.
   - **R_subset** (R_⊆): **COVALENT bond formation ONLY** — condensation, aldol, Michael addition, imine formation,
     polymerization, any reaction that forms or breaks a covalent σ/π bond. NOT for hydrogen bonding.
   - **R_dagger** (R_‡): Catalytic / dynamic — transition-state stabilization, autocatalysis, reversible covalent.
   - **R_mechanical** (R_⇔): Mechanical bonds (rotaxanes, catenanes).
   **CRITICAL: R_subset ≠ "strong binding". R_subset = covalent bond formation. If unsure, default to R_superset.**

4. **Polarity (P)**: What is the directional character?
   - **P_plus** (P+): Acceptor/electrophile
   - **P_minus** (P-): Donor/nucleophile
   - **P_pm** (P_±): Self-complementary
   - **P_directional** (P_+-): Donor-acceptor pairs

5. **Fidelity (F)**: How much information does one recognition event transmit? (ξ_CP, I_net)
   - **F_hbar** (F_ℏ): I_net > 9 bits / ξ_CP ≤ 8.5 nats — geometry-enforcing, dominant constraint. *Examples: carboxylic acid dimer R²₂(8), CB[7]·Fc, triple H-bond DAD·ADA array.*
   - **F_eth** (F_ℇ): I_net 6–9 bits / ξ_CP 8.5–11.0 nats — context-dependent, reliable under the right conditions. *Examples: single H-bond, most ice H-bond networks, proline aldol cycle.*
   - **F_ell** (F_ℓ): I_net < 6 bits / ξ_CP > 11.0 nats — probabilistic, fires unreliably. *Examples: weak π-stacking, metastable phase interactions.*
   **FIDELITY IS NOT BOND STRENGTH.** A weak but specific interaction is F_hbar; a strong but promiscuous one is F_ell. Ask: "How reliably and specifically does this interaction fire?"

6. **Kinetic Character (K)**: What is the energy barrier to constraint rearrangement? (ΔG‡)
   — **K is independent of F.** A system can be F_eth (medium information) and K_fast (rapidly exchanging) OR K_slow (kinetically frozen). F tells you how good the lock is; K tells you how fast you can turn the key.
   - **K_fast**: ΔG‡ < 60 kJ/mol — system **explores configuration space** on experimental timescales; enables access to multiple ordered endpoints; proton/molecular reorientation accessible at RT.
   - **K_mod**: ΔG‡ 60–100 kJ/mol — moderate barrier; accessible under mild conditions.
   - **K_slow**: ΔG‡ > 100 kJ/mol — constraint is kinetically frozen; ordered descendants require external driving (pressure ramp, slow cooling).
   - **K_trap**: system locked in a kinetically metastable state — cannot reach thermodynamic minimum without perturbation.
   *Ice VI example:* K_fast predicts ice VI can access multiple ordered endpoints on experimental timescales (→ ice XV at ~1 GPa, ice XIX at >1.5 GPa). K_fast is the **causal primitive** enabling the entire ordering landscape.

7. **Granularity (G)**: At what length scale does constraint propagate? (correlation length)
   — G is **not** about physical size. It encodes the range over which a recognition event in one part of the system influences another.
   - **G_beth** (G_ב): Correlation length ≈ 1 unit — constraint is local to a single bond/interaction. The recognition event does not influence its neighbours.
   - **G_gimel** (G_ג): Correlation length spans a motif/cluster (~10–1000 units) — constraint propagates mesoscopically through cooperative effects.
   - **G_aleph** (G_א): Correlation length diverges — constraint propagates across the entire system (network-wide, global). Associated with scale-free behavior, criticality, or interpenetrating networks where every sub-network is coupled.

7. **Interaction Grammar (Γ)**: Partner selection logic?
   - **G_and**: Conjunctive — all partners required simultaneously (specific/cooperative)
   - **G_or**: Disjunctive — any partner suffices (broad/promiscuous)
   - **G_seq**: Sequential — ordered recognition steps

8. **Kinetic Character (K)**: Activation barrier?
   - **K_fast**: < 60 kJ/mol — fast exchange
   - **K_mod**: 60–100 kJ/mol — moderate
   - **K_slow**: > 100 kJ/mol — slow, persistent
   - **K_trap**: kinetic trap — system locked in state

9. **Criticality Phase (Φ)**: Proximity to critical point?
   - **Phi_sub**: subcritical — normal assembly
   - **Phi_c**: critical — scale-free, G/D degenerate
   - **Phi_super**: post-assembly / supercritical

10. **Chirality (H)**: Degree and persistence of broken orientational symmetry?
    — H encodes whether the recognition interface distinguishes its mirror image, and how deep the symmetry-breaking memory is. H is the **only temporally anisotropic primitive** — the only one that breaks time-symmetry.
    - **H0** (achiral): mirror image accessible; memory depth 0. *Examples: achiral molecules, CB[n] hosts, most bulk water phases.*
    - **H1** (soft chiral): single axis, thermally interconvertible at RT; memory depth 1. *Examples: atropisomers with low inversion barrier, axially chiral biphenyls below the conformational lock threshold.*
    - **H2** (persistent chiral): multiple axes, structurally enforced; memory depth n. *Examples: amino acids, chiral drugs, DNA double helix, enantioselective catalysts, chiral polymers.*
    - **H_∞** (topological chirality): topology-protected; memory depth ∞; **implies K_trap**. *Examples: catenanes with chirally locked rings, trefoil knots, topological insulators with chiral edge states.*
    **Physical peel (H-peel = racemization):** ΔG‡ ≈ 120–160 kJ/mol for amino acids. Each tier costs +2.303 nats/tier (CLU) to lift. H_∞ + K_trap coexistence → P-99 prediction. Soai reaction is a physical H-lift machine: H0→H2 over n_T autocatalytic cycles.
    **When to assign H2:** any system where the description mentions chiral, enantioselective, amino acid, L-form, D-form, protein folding, DNA, or enantiopure.

11. **Stoichiometry (S)**: Valency ratio of interacting partners?
    - **1:1**: homodimeric / symmetric pairing
    - **n:n**: higher symmetric oligomers
    - **n:m**: asymmetric — different stoichiometry on each face
    - Leave blank if not determinable from the description.
</primitives>

<output_format>You **MUST** respond with a **VALID JSON OBJECT** in this **EXACT** format:
```json
{
  "synthon": {
    "dimensionality": "D_wedge",
    "topology": "T_bowtie",
    "recognition_mode": "R_superset",
    "polarity": "P_pm",
    "fidelity": "F_hbar",
    "kinetic_character": "K_mod",
    "granularity": "G_beth",
    "interaction_grammar": "G_and",
    "criticality_phase": "Phi_sub",
    "chirality": "H0",
    "stoichiometry": "1:1"
  },
  "confidence": 0.85,
  "reasoning": "Detailed explanation of primitive assignments...",
  "alternatives": [
    {
      "dimensionality": "D_wedge",
      "topology": "T_linear",
      "recognition_mode": "R_superset",
      "polarity": "P_pm",
      "fidelity": "F_eth",
      "granularity": "G_beth",
      "interaction_grammar": "G_or"
    }
  ]
}
```
</output_format>

<reasoning_framework>**For EACH primitive, apply this reasoning chain — do NOT skip steps:**
1. **D**: Does the constraint operate on molecular DOFs, propagate through spatial assembly, or recur through a temporal cycle with reset? → D_∧ / D_△ / D_∞
2. **T**: What is the topological connectivity of the recognition interface? Closed ring? Open cavity? Interpenetrating networks? Chain? → T
3. **R**: What physical mechanism enables recognition? Non-covalent forces? Bond formation/breaking? Transition-state stabilization? Mechanical topology? → R
4. **P**: Is the interface symmetric (both partners identical), directed (distinct donor/acceptor faces), or self-complementary in another sense? → P
5. **F**: How much information is transmitted per recognition event? What is ξ_CP (in nats)? Is the interaction geometry-enforcing (F_hbar) or probabilistic (F_ell)? → F
6. **K**: What is ΔG‡ for constraint rearrangement? Can the system explore configurations at room temperature or experimental conditions? → K
7. **G**: At what length scale does the constraint influence the system? Local bond? Mesoscale motif? Global network? → G
8. **Γ**: How many partners can the recognition site accept? One specific partner? A few selective partners? Many? → Γ
9. **Φ**: Is the system near a critical point where G and D degenerate (scale-free, diverging correlations)? → Φ
10. **H**: Does the system break orientational symmetry persistently? Is the mirror image accessible (H0), thermally interconvertible (H1), structurally enforced (H2), or topology-protected (H_∞)? → H
11. **S**: What is the stoichiometric ratio of the recognition event? → S
</reasoning_framework>

<reference_systems>**Multi-domain reference examples:**

*Molecular domain:*
- Carboxylic acid R²₂(8) dimer: ⟨D_wedge; T_bowtie; R_superset; P_pm_pseudo; F_hbar; K_fast; G_beth; Gamma_and(SELECTIVE); Phi_sub; 1:1⟩ — I_net ≈ 9.4 bits, ξ_CP = 6.66 nats
- Triple H-bond DAD·ADA: ⟨D_wedge; T_bowtie; R_superset; P_directional; F_hbar; K_fast; G_gimel; Gamma_and(SPECIFIC); Phi_sub; 1:1⟩ — I_net ≈ 16.6 bits, ξ_CP = 7.65 nats

*Network / bulk material domain:*
- Ice Ih (hexagonal network): ⟨D_triangle; T_network_hex; R_superset; P_directional; F_eth; K_mod; G_gimel; Gamma_and(SELECTIVE); Phi_sub⟩ — pure 6-membered rings, 4-coordinate H-bond network
- Ice VI (interpenetrating, **K_fast**): ⟨D_triangle; T_network_interp; R_superset; P_directional; F_eth; **K_fast**; G_gimel; Gamma_and(SELECTIVE); Phi_sub⟩ — K_fast is the **causal primitive**: rapid proton dynamics (dielectric relaxation time << ordered phases) enable access to ice XV and ice XIX ordering landscapes on experimental timescales. K_fast is not a mistake — it is the physically correct assignment supported by Yamane et al. (2021) dielectric data.
- Ice XV (proton-ordered from VI, ~1 GPa): ⟨D_triangle; T_network_interp; R_superset; P_directional; F_eth; K_slow; G_gimel; ...⟩ — K_slow because ordering is kinetically frozen (ordered phase, not disordered parent)
- Ice XIX (proton-ordered from VI, >1.5 GPa): ⟨D_triangle; T_network_interp; R_superset; P_directional; F_eth; K_slow; **G_beth**; ...⟩ — G_beth (LOCAL) encodes that ordering correlation length is shorter at higher pressure (compressed O-O distances constrain local geometry more rigidly)

*Temporal domain:*
- Proline aldol cycle: ⟨D_infinity; T_bowtie; R_dagger; P_directional; F_eth; K_mod; G_gimel; Gamma_seq(SPECIFIC); Phi_sub; 1:1⟩ — ΔG‡ = 97 kJ/mol (K_mod), F_cycle ≈ 0.999, ξ_CP = 9.21 nats

*Key lesson from ice polymorphs:* The framework distinguishes 13 ice phases using four primitives: T (ring topology sub-label), K (kinetic barrier), G (correlation length), P (proton ordering). Before the T_∈ sub-labels existed, ice Ih and ice III appeared identical — the catalog self-audit revealed the missing primitive. This is the framework's self-correcting property: identical tuples → missing primitive.
</reference_systems>

<mechanistic_constraints>
**MECHANISTIC CONSTRAINTS (AXIOMS) — YOU MUST SATISFY ALL:**

<axiom_6>**AXIOM 6 — D_infinity (TEMPORAL) REQUIRES A PHYSICALLY GROUNDED RESET:**
You **MUST** use D_infinity **ONLY IF** the system has a physically specifiable
reset mechanism. Two allowed types:

  **discrete** (most chemistry): closed catalytic/reaction cycle with a named
  reset step (hydrolysis, product release, energy input).
  Set ``metadata["grounding"]["reset"]["type"] = "discrete"`` with
  ``cycle_steps`` or fill ``axiom6_grounding`` dict.
  EXAMPLES: proline aldol cycle, imine condensation, oscillatory reactions.

  **continuous** (open dissipative / non-chemical): sustained driving gradient
  with no sharp reset event. Set
  ``metadata["grounding"]["reset"]["type"] = "continuous"`` and provide
  ``driving_gradient.description`` + ``driving_gradient.coupling``.
  EXAMPLES: supply chains, living cells, flow reactors.

**PHOTOSWITCHABLE SYSTEMS** are valid D_∞ if and only if you name all four cycle steps:
  STATE (which form, open/closed/E/Z) → WORK (recognition event or function) →
  RESET (thermal relaxation or second photon restores initial state) → CYCLE (named).
  The reset must be specified: "thermal relaxation regenerates E-isomer" or
  "irradiation at 450 nm ring-opens diarylethene back to open form".
  WITHOUT a named reset, assign D_wedge or D_triangle.

You **MUST NOT** use D_infinity for:
- **STATIC** molecules (allenes, cumulenes, rods) → **USE D_wedge**
- Crystal packing → **USE D_triangle**
- Dimers/complexes **WITHOUT** cycles → **USE D_wedge**
- **PHOTOSWITCHES WITHOUT NAMED RESET** — if you cannot specify the reset step → **USE D_wedge**
- **SUPRAMOLECULAR POLYMERIZATION** — monomer addition to a growing chain, column, or stack
  → **USE D_triangle**. "Repetitive" or "sequential" assembly that grows open-endedly never
  returns to its initial state; it has no reset. A column that grows by stacking is D_△, not D_∞.
- **ANY assembly whose "cycle" is just growth + disassembly** — the test is: do ALL components
  return to their pre-cycle state after one turn? If the column must fully disassemble to "reset",
  that is not a closed cycle; it is a reversible equilibrium in the D_△ (spatial) dimension.

**COMPOUND SYSTEM RULE:** A molecule may have BOTH a D_△ spatial assembly mechanism AND a genuine
D_∞ molecular cycle (e.g., a radical that stacks into columns AND undergoes a radical ⇌ dimer
equilibrium). In such cases, D_∞ is valid **ONLY IF** the Axiom 6 grounding names the reset of the
**molecular cycle** specifically — e.g., "thermal homolysis regenerates the radical monomer". Do NOT
justify D_∞ by citing the column growth or columnar stacking. Attributing D_∞ to stacking when the
actual closed cycle is a radical equilibrium is a grounding error that will fail Axiom 6 enforcement.
</axiom_6>

<axiom_7>**AXIOM 7 — TOPOLOGY MUST MATCH ACTUAL CONNECTIVITY:**

**T_cage (T_□□) — FULL ENCLOSURE:** Guest cannot exchange without distortion; K_slow/K_trap default.
- **Cucurbiturils** (CB[6], CB[7], CB[8]), **cryptands**, **carceplexes**, **self-assembled cages**
- **Covalent organic cages** (COCs), **Fujita spheres**, any system where guest is FULLY enclosed
- Keywords: "cage", "capsule", "encapsulat", "cucurbit", "cryptand", "carceplex"
- **DO NOT use T_⋈ for these — cage closure is a closing FACE, not a closing BOND**

**T_bowl (T_∪) — OPEN CAVITY:** Single portal, guest exchanges freely; K_fast default.
- **Calixarenes**: calix[4]arene, calix[6]arene, calix[8]arene (cone conformation)
- **Calixpyrroles**: calix[4]pyrrole, calix[6]pyrrole (anion binding)
- **Resorcinarenes**: calix[4]resorcinarene, resorcarene bowl
- **Pillar[n]arenes**: pillar[5]arene, pillar[6]arene (uncapped)
- **Others**: cyclotriveratrylene (CTV), corannulene, hemicarceplex, cavitand (open face)
- **Key test**: can a guest enter/exit through an open portal at room temperature? → T_∪
- **DO NOT use T_□□ for calixarenes/pillarenes/resorcinarenes** — these are BOWLS, not cages

**T_bowtie (T_⋈) — CYCLIC DIMER:** Use ONLY for planar dimers with a named closing bond.
- **CLOSED RING** motifs (R₂²(8) dimers, base pairs, urea dimers)
- You **MUST** name the bond: "two O-H···O bonds close the R²₂(8) ring"
- **NEVER** use T_⋈ for encapsulation, cage, capsule, or cucurbituril systems

**T_chains (T_≫)** — extended chains, rods, polymers, cumulenes, allenes, catemers

**T_square (T_□)** — metal coordination centers, MOF secondary building units

**T_network (T_∈) and sub-labels** — extended networks. Use the most specific sub-label:
- **T_∈(hex)**: ice Ih, graphene, honeycomb MOFs — 6-membered rings only
- **T_∈(mixed)**: ice III/IV/V — mixed ring sizes, strained
- **T_∈(×2)**: ice VI/VII/VIII, interpenetrating MOFs — two independent sub-networks
- **T_∈(sym)**: ice X — centrosymmetric bonding
- **T_∈**: bulk water, unspecified network, ring topology not relevant
</axiom_7>

<axiom_8>**AXIOM 8 — RECOGNITION MODE MUST MATCH INTERACTION PHYSICS:**
You **MUST** use **R_superset** (R_⊇, NON-COVALENT) **FOR**:
- **H-BONDING**, hydrogen bonds, water networks, electrostatic, dispersion, σ-hole interactions
- **Coordination chemistry**: metal-ligand bonds, host-guest (CB[n], crown ethers, cyclodextrins)
- **Ionic interactions**, ion-pair recognition, halogen bonds, π-stacking
- **NO** covalent bond formation/breaking — if in doubt, use R_superset

You **MUST** use **R_subset** (R_⊆, COVALENT bond formation) **FOR**:
- **ELECTRON sharing**: σ/π bond formation, condensation reactions
- **Aldol, Michael, imine** formation, esterification, polymerization
- **NOT** for hydrogen bonds — R_subset ≠ "strong binding"

You **MUST** use **R_dagger** (R_‡, catalytic/dynamic) **FOR**:
- **TRANSITION STATE** stabilization, barrier reduction, organocatalysis
- **REVERSIBLE** covalent bond formation with error correction (dynamic imine, etc.)
- **AUTOCATALYTIC** cycles where the product catalyzes its own formation

You **MUST** use **R_mechanical FOR**:
- **STERIC** clipping, topological entanglement, rotaxanes, catenanes
</axiom_8>
</mechanistic_constraints>

<requirements>You **MUST**:
1. **ANALYZE** the chemical description **THOROUGHLY**
2. **MAP** each feature to the **CORRECT** primitive
3. **SATISFY** all mechanistic constraints (Axioms 6, 7, 8)
4. **PROVIDE** detailed reasoning for **EACH** primitive assignment
5. **INCLUDE** at least one alternative interpretation
6. **ASSIGN** confidence based on chemical certainty
</requirements>
"""

    def _build_generation_prompt(self, description: str, name: Optional[str]) -> str:
        """Build the prompt for synthon generation from description."""
        name_instruction = f"You **MUST** name it '{name}'." if name else "You **MUST** generate an appropriate name."
        return f"""<task>You **MUST** analyze the following self-organizing system and generate a synthon representation using the twelve-primitive Synthonicon encoding.</task>

<input>
**System Description:**
{description}
</input>

<instructions>
You **MUST**:
1. **APPLY** the reasoning framework above — work through each primitive from first principles
2. **GROUND** each assignment in the underlying physics: energy barrier (K), information content (F), correlation length (G)
3. **DO NOT** default to chemical templates — reason from the actual system behavior
4. {name_instruction}
</instructions>

<output>You **MUST** provide your complete analysis as a **JSON OBJECT**.</output>
"""

    def _build_smiles_prompt(self, smiles: str, functional_groups: Optional[List[str]]) -> str:
        """Build the prompt for synthon generation from SMILES."""
        fg_section = f"<functional_groups>**Functional Groups:** {functional_groups}</functional_groups>" if functional_groups else ""
        return f"""<task>You **MUST** analyze the following molecular structure and generate a synthon representation.</task>

<input>
**SMILES String:**
{smiles}
{fg_section}
</input>

<instructions>
You **MUST**:
1. **PARSE** the SMILES to identify key structural features
2. **DETERMINE** the dominant functional groups and their interactions
3. **MAP** to all ten primitives based on:
   - Molecular structure → **D_wedge** (typically)
   - Functional group geometry → **Topology**
   - Interaction type → **Recognition Mode**
   - Electronic character → **Polarity**
   - Bond strength/specificity → **Fidelity**
   - Size of motif → **Granularity**
   - Partner specificity → **Interaction Grammar**
</instructions>

<output>You **MUST** provide your analysis as a **JSON OBJECT**.</output>
"""

    def _parse_llm_response(
        self,
        response: str
    ) -> Tuple[Dict[str, str], str, float, List[Dict[str, str]]]:
        """Parse the LLM response into synthon data and metadata."""
        # Extract JSON from response
        json_blocks = self.extract_json_blocks(response)

        if not json_blocks:
            # Fallback: try to extract primitive values with regex
            return self._parse_with_regex(response)

        data = json_blocks[0]

        # Extract synthon data
        synthon_data = data.get("synthon", {})

        # Extract reasoning
        reasoning = data.get("reasoning", "No reasoning provided.")

        # Extract confidence
        confidence = data.get("confidence", 0.7)
        if not isinstance(confidence, (int, float)):
            confidence = 0.7

        # Extract alternatives
        alternatives = data.get("alternatives", [])
        if not isinstance(alternatives, list):
            alternatives = []

        return synthon_data, reasoning, float(confidence), alternatives

    def _parse_with_regex(self, response: str) -> Tuple[Dict[str, str], str, float, List]:
        """Fallback parsing using regex for primitive values."""
        primitives = {}

        # Try to extract each primitive
        patterns = {
            "dimensionality": r"[\"']?dimensionality[\"']?\s*[:=]\s*[\"']?(D_\w+)[\"']?",
            "topology": r"[\"']?topology[\"']?\s*[:=]\s*[\"']?(T_\w+)[\"']?",
            "recognition_mode": r"[\"']?recognition[_ ]?mode[\"']?\s*[:=]\s*[\"']?(R_\w+)[\"']?",
            "polarity": r"[\"']?polarity[\"']?\s*[:=]\s*[\"']?(P_\w+)[\"']?",
            "fidelity": r"[\"']?fidelity[\"']?\s*[:=]\s*[\"']?(F_\w+)[\"']?",
            "granularity": r"[\"']?granularity[\"']?\s*[:=]\s*[\"']?(G_\w+)[\"']?",
            "interaction_grammar": r"[\"']?interaction[_ ]?grammar[\"']?\s*[:=]\s*[\"']?(Gamma_\w+)[\"']?",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                primitives[key] = match.group(1)

        # Set defaults for missing primitives
        defaults = {
            "dimensionality": "D_wedge",
            "topology": "T_linear",
            "recognition_mode": "R_superset",
            "polarity": "P_pm",
            "fidelity": "F_eth",
            "granularity": "G_beth",
            "interaction_grammar": "Gamma_selective",
        }

        for key, default in defaults.items():
            if key not in primitives:
                primitives[key] = default

        # Extract reasoning (text after "reasoning" or "analysis")
        reasoning_match = re.search(r"(?:reasoning|analysis)[:\s]+(.+?)(?:$|```|\n\n)", response, re.DOTALL | re.IGNORECASE)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else "Parsed from response."

        return primitives, reasoning, 0.5, []

    def _create_synthon_from_data(
        self,
        data: Dict[str, str],
        description: str,
        explicit_name: Optional[str] = None,
    ) -> Synthon:
        """Create a Synthon object from parsed data.

        Extended to support ten primitives: D, T, R, P, F, K, G, Γ, Φ, S
        """
        # Map string values to enum members
        dimensionality = Dimensionality.from_symbol(data.get("dimensionality", "D_wedge"))
        topology = Topology.from_symbol(data.get("topology", "T_linear"))
        recognition_mode = RecognitionMode.from_symbol(data.get("recognition_mode", "R_superset"))
        polarity = Polarity.from_symbol(data.get("polarity", "P_pm_pseudo"))
        fidelity = Fidelity.from_symbol(data.get("fidelity", "F_eth"))
        kinetic_character = KineticCharacter.from_symbol(data.get("kinetic_character", "K_mod"))
        granularity = Granularity.from_symbol(data.get("granularity", "G_beth"))
        interaction_grammar = InteractionGrammar.from_symbol(data.get("interaction_grammar", "Gamma_and(SELECTIVE)"))

        # Criticality phase (optional)
        criticality_phase = CriticalityPhase.from_symbol(data.get("criticality_phase") or "Phi_sub")

        # Stoichiometry (optional, string "1:1" / "n:m" / etc.)
        stoichiometry_str = data.get("stoichiometry") or None
        stoichiometry = Stoichiometry.from_symbol(stoichiometry_str) if stoichiometry_str else Stoichiometry.n_m

        # Chirality (optional)
        chirality = Chirality.from_symbol(data.get("chirality") or "H0")

        # Explicit name wins over LLM-generated name; sanitize LLM bleed otherwise
        if explicit_name:
            name = explicit_name.strip()
        else:
            raw_name = data.get("name") or _desc_slug(description)
            name = raw_name.split("\n")[0].strip().replace(" ", "_")
            if not name:
                name = _desc_slug(description)

        return Synthon(
            name=name,
            dimensionality=dimensionality,
            topology=topology,
            recognition_mode=recognition_mode,
            polarity=polarity,
            fidelity=fidelity,
            kinetic_character=kinetic_character,
            granularity=granularity,
            grammar=interaction_grammar,
            criticality_phase=criticality_phase,
            chirality=chirality,
            protection=Protection.Omega_0,
            stoichiometry=stoichiometry,
            description=description,
            metadata={"auto_generated": True}
        )

    async def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the synthon generation task.

        This is the main entry point for the AjintK framework.
        """
        try:
            # Parse the task to determine the generation mode
            task_lower = task.lower()

            if "smiles" in task_lower:
                # Extract SMILES from task
                smiles_match = re.search(r'[A-Za-z0-9@+\-\[\]\(\)=#]+', task)
                if smiles_match:
                    smiles = smiles_match.group(0)
                    result = await self.generate_from_smiles(smiles)
                else:
                    return {
                        "status": "error",
                        "error": "Could not extract SMILES string from task",
                    }
            else:
                # Treat as natural language description
                result = await self.generate_from_description(task)

            return {
                "status": "success",
                "findings": f"Generated synthon: {result.synthon.name}\n"
                           f"Notation: {result.synthon.to_notation()}\n"
                           f"Confidence: {result.confidence:.2f}\n"
                           f"Reasoning: {result.reasoning}",
                "artifacts": self.artifacts,
                "metadata": {
                    "synthon_name": result.synthon.name,
                    "notation": result.synthon.to_notation(),
                    "confidence": result.confidence,
                    "thermodynamic_metrics": result.thermodynamic_metrics,
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "findings": None,
            }


# Convenience function for quick synthon generation
async def generate_synthon(
    description: str,
    provider: str = "anthropic",
    model: Optional[str] = None,
    delta_g: Optional[float] = None,
) -> SynthonGenerationResult:
    """
    Convenience function for quick synthon generation.

    Args:
        description: Chemical description
        provider: LLM provider to use (default: "anthropic")
        model: Model name (default: provider-specific default from config)
        delta_g: Optional free energy for thermodynamic analysis

    Returns:
        SynthonGenerationResult

    Example:
        >>> result = await generate_synthon(
        ...     "carboxylic acid dimer with cyclic hydrogen bonding",
        ...     delta_g=-52.0
        ... )
        >>> print(result.synthon.to_notation())
    """
    from synthomnicon.provider_config import build_agent_config
    
    config = build_agent_config(provider=provider, model=model, max_tokens=4000)
    agent = SynthonGeneratorAgent(config)
    return await agent.generate_from_description(description, delta_g=delta_g)
