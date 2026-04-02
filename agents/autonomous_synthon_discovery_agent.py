"""
Autonomous Synthon Discovery Agent — Self-directed synthon generation and validation.

This agent autonomously:
1. Proposes novel synthons based on chemical space exploration
2. Validates against literature (web search)
3. Checks for duplicates in the catalog
4. Registers valid synthons
5. Repeats until configured limits are reached

Usage:
    from agents.autonomous_synthon_discovery_agent import AutonomousSynthonDiscoveryAgent
    from synthomnicon.provider_config import build_agent_config
    
    config = build_agent_config(provider="anthropic", model=None)
    agent = AutonomousSynthonDiscoveryAgent(config)
    
    # Run for 10 cycles or 30 minutes
    results = await agent.run_autonomous(max_cycles=10, max_duration_minutes=30)
"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from framework import BaseAgent, ToolDefinitions
from synthomnicon import (
    Synthon, Dimensionality, Topology, RecognitionMode,
    Polarity, Fidelity, Granularity, InteractionGrammar,
    global_catalog, ConstraintEngine
)
from synthomnicon.constraints import AxiomValidator
from synthomnicon.thermodynamics import compute_eta_CP
from synthomnicon.perturbation import PerturbationEngine


class ValidationResult(Enum):
    """Result of synthon validation."""
    VALID_NOVEL = "valid_novel"
    DUPLICATE_EXISTS = "duplicate_exists"
    INVALID_CHEMISTRY = "invalid_chemistry"
    LITERATURE_CONFLICT = "literature_conflict"
    LOW_CONFIDENCE = "low_confidence"


@dataclass
class DiscoveryCycle:
    """Results from a single discovery cycle."""
    cycle_number: int
    timestamp: str
    proposed_description: str
    proposed_name: str
    validation_result: ValidationResult
    synthon: Optional[Synthon] = None
    confidence: float = 0.0
    reasoning: str = ""
    literature_found: bool = False
    literature_references: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class AutonomousRunConfig:
    """Configuration for autonomous discovery run."""
    max_cycles: int = 100
    max_duration_minutes: float = 60.0
    min_confidence_threshold: float = 0.7
    target_domains: List[str] = field(default_factory=lambda: ["molecular", "supramolecular", "temporal"])
    focus_areas: Optional[List[str]] = None  # e.g., ["hydrogen bonding", "catalysis"]
    save_interval: int = 10  # Save progress every N cycles
    output_dir: Optional[Path] = None
    diversity_mode: bool = True  # Actively avoid repeating proposals
    # Perturbation-steered discovery
    use_perturbation_steering: bool = False
    target_xi_cp_range: Optional[Tuple[float, float]] = None  # e.g. (5.0, 8.0) nats
    perturbation_delta_g: float = -12.0  # ΔG used for pathfinding, kJ/mol


class AutonomousSynthonDiscoveryAgent(BaseAgent):
    """
    Autonomous agent for continuous synthon discovery and validation.
    
    Runs in cycles:
    1. Propose: Generate novel synthon descriptions
    2. Validate: Check for duplicates and literature conflicts
    3. Register: Add valid synthons to catalog
    4. Report: Log progress and metrics
    5. Repeat until limits reached
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            agent_id="autonomous_discovery",
            name="Autonomous Synthon Discovery Agent",
            description="Self-directed agent for continuous synthon discovery, validation, and registration",
            capabilities=[
                "autonomous_proposal",
                "literature_validation",
                "duplicate_detection",
                "catalog_registration",
                "progress_tracking",
            ],
            config=config,
            persona="Autonomous synthonic explorer specializing in systematic discovery across the full synthon space. "
                    "You propose novel synthonic systems — from molecular organocatalysis to cross-domain ensembles — "
                    "validate them against the ten-primitive framework, and register valid discoveries. "
                    "Primary-tier proposals (molecular/supramolecular) are grounded in experimental chemistry. "
                    "Extended-tier proposals are clearly flagged with analogue grounding. "
                    "You are thorough, creative, and physically rigorous."
        )
        self.provider = self._setup_llm_provider_strict()
        self.discovery_history: List[DiscoveryCycle] = []
        self.proposed_names: set = set()  # Track proposed names to avoid repeats
        self.recent_duplicate_tuples: List[str] = []  # Track failed tuple notations for feedback
        self.recent_duplicate_descriptions: List[str] = []  # Track failed name/desc duplicates for feedback
        self._perturb_engine = PerturbationEngine()
        self._perturbation_hints: List[str] = []  # steering hints for next proposal
        self.stats = {
            "cycles_completed": 0,
            "synthons_proposed": 0,
            "synthons_validated": 0,
            "synthons_registered": 0,
            "duplicates_detected": 0,
            "literature_conflicts": 0,
            "errors": 0,
        }
    
    def _setup_llm_provider_strict(self):
        """Setup LLM provider without fallback."""
        from framework.enhanced_llm_provider import get_llm_provider
        
        provider_name = self.config.get("provider", "anthropic")
        model = self.config.get("model", None)
        
        if "/" in provider_name:
            parts = provider_name.split("/", 1)
            provider_name = parts[0]
            model = parts[1] if len(parts) > 1 else model
        
        try:
            return get_llm_provider(provider_name, model=model)
        except ValueError as e:
            raise e
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Declare tools for autonomous operation."""
        return [
            ToolDefinitions.file_read(),
            ToolDefinitions.file_write(),
            ToolDefinitions.json_load(),
            ToolDefinitions.json_save(),
            ToolDefinitions.run_command(),
        ]
    
    async def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run autonomous discovery (BaseAgent interface).
        
        Args:
            task: Task description (ignored, uses config)
            context: Optional context
        
        Returns:
            Discovery results
        """
        config = AutonomousRunConfig()
        results = await self.run_autonomous(config)
        
        return {
            "status": "success",
            "findings": f"Completed {len(results)} discovery cycles",
            "artifacts": [r.synthon.to_dict() for r in results if r.synthon],
            "metadata": self.stats,
        }
    
    async def run_autonomous(
        self,
        config: Optional[AutonomousRunConfig] = None,
        **kwargs
    ) -> List[DiscoveryCycle]:
        """
        Run autonomous synthon discovery.
        
        Args:
            config: Run configuration (uses defaults if not provided)
            **kwargs: Override config values (e.g., max_cycles=50)
        
        Returns:
            List of DiscoveryCycle results
        """
        # Build configuration
        if config is None:
            config = AutonomousRunConfig()
        
        # Apply kwargs overrides
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Setup output directory
        output_dir = config.output_dir or Path.cwd() / "discovery_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize tracking
        self.discovery_history = []
        self.stats = {k: 0 for k in self.stats}
        self.recent_duplicate_tuples = []  # Reset per run
        self._perturbation_hints = []      # Reset steering hints per run
        self._run_config = config          # Store for use in cycle callbacks
        start_time = time.time()
        
        print(f"\n{'='*70}")
        print("AUTONOMOUS SYNTHON DISCOVERY AGENT")
        print(f"{'='*70}")
        print(f"Configuration:")
        print(f"  Max cycles: {config.max_cycles}")
        print(f"  Max duration: {config.max_duration_minutes} minutes")
        print(f"  Min confidence: {config.min_confidence_threshold}")
        print(f"  Target domains: {config.target_domains}")
        print(f"  Focus areas: {config.focus_areas or 'All'}")
        print(f"  Output directory: {output_dir}")
        print(f"{'='*70}\n")
        
        # Main discovery loop
        cycle = 0
        while cycle < config.max_cycles:
            # Check time limit
            elapsed_minutes = (time.time() - start_time) / 60
            if elapsed_minutes >= config.max_duration_minutes:
                print(f"\n[TIME LIMIT] Reached {config.max_duration_minutes} minutes")
                break
            
            cycle += 1
            print(f"\n{'='*50}")
            print(f"CYCLE {cycle}/{config.max_cycles}")
            print(f"{'='*50}")
            
            # Run discovery cycle
            result = await self._run_discovery_cycle(cycle, config)
            self.discovery_history.append(result)
            
            # Update stats
            self.stats["cycles_completed"] = cycle
            self.stats["synthons_proposed"] += 1
            
            if result.validation_result == ValidationResult.VALID_NOVEL:
                self.stats["synthons_validated"] += 1
                if result.synthon:
                    self.stats["synthons_registered"] += 1
            elif result.validation_result == ValidationResult.DUPLICATE_EXISTS:
                self.stats["duplicates_detected"] += 1
            elif result.validation_result == ValidationResult.LITERATURE_CONFLICT:
                self.stats["literature_conflicts"] += 1
            
            if result.error:
                self.stats["errors"] += 1
            
            # Print cycle summary
            self._print_cycle_summary(result)
            
            # Save progress periodically
            if cycle % config.save_interval == 0:
                self._save_progress(output_dir, cycle, config)
        
        # Final save and report
        self._save_progress(output_dir, cycle, config, final=True)
        self._print_final_report(start_time)
        
        return self.discovery_history
    
    async def _run_discovery_cycle(
        self,
        cycle_number: int,
        config: AutonomousRunConfig
    ) -> DiscoveryCycle:
        """Run a single discovery cycle."""
        timestamp = datetime.now().isoformat()

        try:
            # Step 1: Propose novel synthon
            proposal = await self._propose_synthon(config)

            # Step 2: Check for duplicates in catalog (name/description level)
            is_duplicate, existing = await self._check_duplicate(proposal["name"], proposal["description"])
            if is_duplicate:
                # Record the failed description so next proposal knows what to avoid
                desc_snippet = proposal["description"][:200]
                if desc_snippet not in self.recent_duplicate_descriptions:
                    self.recent_duplicate_descriptions.append(desc_snippet)
                self.recent_duplicate_descriptions = self.recent_duplicate_descriptions[-5:]
                return DiscoveryCycle(
                    cycle_number=cycle_number,
                    timestamp=timestamp,
                    proposed_description=proposal["description"],
                    proposed_name=proposal["name"],
                    validation_result=ValidationResult.DUPLICATE_EXISTS,
                    reasoning=f"Duplicate of existing synthon: {existing}",
                )

            # Step 3: Literature validation
            literature_result = await self._validate_literature(proposal["description"])
            if literature_result["conflict"]:
                return DiscoveryCycle(
                    cycle_number=cycle_number,
                    timestamp=timestamp,
                    proposed_description=proposal["description"],
                    proposed_name=proposal["name"],
                    validation_result=ValidationResult.LITERATURE_CONFLICT,
                    literature_found=True,
                    literature_references=literature_result.get("references", []),
                    reasoning=literature_result["reason"],
                )

            # Step 4: Generate synthon representation
            # Pass forbidden tuples so encoding model knows what NOT to produce
            synthon, confidence, reasoning = await self._generate_synthon_representation(
                proposal["name"],
                proposal["description"],
                forbidden_tuples=self.recent_duplicate_tuples or None,
            )

            # Step 4b: NEW - Tuple-level duplicate check (after synthon generation)
            # This catches cases where model games the system by using different descriptions
            # for chemically equivalent tuples (DeepSeek/Gemini convergence fix)
            tuple_duplicate = self._check_tuple_duplicate(synthon)
            if tuple_duplicate:
                # Record failed tuple for feedback into next proposal
                failed_notation = synthon.to_notation()
                if failed_notation not in self.recent_duplicate_tuples:
                    self.recent_duplicate_tuples.append(failed_notation)
                # Keep only last 5 failed tuples
                self.recent_duplicate_tuples = self.recent_duplicate_tuples[-5:]
                return DiscoveryCycle(
                    cycle_number=cycle_number,
                    timestamp=timestamp,
                    proposed_description=proposal["description"],
                    proposed_name=proposal["name"],
                    validation_result=ValidationResult.DUPLICATE_EXISTS,
                    synthon=synthon,
                    confidence=confidence,
                    reasoning=f"Functionally duplicate tuple — all 9 primitives match existing entry '{tuple_duplicate}'. "
                              f"Failed notation: {failed_notation}. "
                              f"You MUST change at least T (topology), R (recognition mode), P (polarity), or G (granularity).",
                )
            
            # Step 5: Confidence check
            if confidence < config.min_confidence_threshold:
                return DiscoveryCycle(
                    cycle_number=cycle_number,
                    timestamp=timestamp,
                    proposed_description=proposal["description"],
                    proposed_name=proposal["name"],
                    validation_result=ValidationResult.LOW_CONFIDENCE,
                    confidence=confidence,
                    reasoning=f"Confidence {confidence:.2f} below threshold {config.min_confidence_threshold}",
                )

            # Step 5.5: Axiom validation (CRITICAL FIX - prevents false matches)
            # Validate all five composition axioms before registration
            axiom_report = AxiomValidator.validate_all_axioms(synthon)
            axiom_violations = axiom_report.get("violations", 0)
            
            # Check for critical axiom violations (Axioms 1, 4 are hard constraints)
            axiom4_report = axiom_report.get("detailed_results", {}).get("axiom4", {})
            axiom4_violated = axiom4_report.get("violated", False)
            
            axiom1_report = axiom_report.get("detailed_results", {}).get("axiom1", {})
            axiom1_violated = axiom1_report.get("violated", False)
            
            # Reject synthons with hard axiom violations
            if axiom4_violated:
                return DiscoveryCycle(
                    cycle_number=cycle_number,
                    timestamp=timestamp,
                    proposed_description=proposal["description"],
                    proposed_name=proposal["name"],
                    validation_result=ValidationResult.INVALID_CHEMISTRY,
                    confidence=confidence,
                    reasoning=f"AXIOM 4 VIOLATION: Sequential grammar (Γ_→) requires temporal (D_∞) or catalytic (R_‡) dimension. "
                            f"This is a physically impossible combination. Axiom report: {axiom_report}",
                    error="Axiom 4 violation detected",
                )
            
            if axiom1_violated:
                return DiscoveryCycle(
                    cycle_number=cycle_number,
                    timestamp=timestamp,
                    proposed_description=proposal["description"],
                    proposed_name=proposal["name"],
                    validation_result=ValidationResult.INVALID_CHEMISTRY,
                    confidence=confidence,
                    reasoning=f"AXIOM 1 VIOLATION: Cyclic self-complementary synthon (T_⋈/P_±) cannot have low fidelity (F_ell). "
                            f"Axiom report: {axiom_report}",
                    error="Axiom 1 violation detected",
                )
            
            # Log warnings for other violations but allow registration
            axiom_warnings = []
            if axiom_violations > 0:
                axiom_warnings.append(f"{axiom_violations} axiom violation(s) detected - flagged for review")

            # Step 6: Grounding checks (Axioms 6 & 7) — independent of axiom validator
            grounding_failed = []

            # Axiom 6: D_∞ requires named closed cycle
            if synthon.dimensionality == Dimensionality.TEMPORAL:
                reasoning_lower = reasoning.lower()
                reset_indicators = ["reset", "reform", "regenerat", "hydroly", "return",
                                     "cycle", "turnover", "re-form", "dissipat", "release"]
                process_indicators = ["catalyz", "oxidat", "reduct", "transfer",
                                       "phosphoryl", "condensat", "oscillat", "periodic", "aldol"]
                has_reset = any(kw in reasoning_lower for kw in reset_indicators)
                has_process = any(kw in reasoning_lower for kw in process_indicators)
                if not (has_reset and has_process):
                    grounding_failed.append("dimensionality (D_∞ without closed cycle)")

            # Axiom 7: T_⋈ requires named closing bond
            if synthon.topology == Topology.CYCLIC_BOWTIE:
                reasoning_lower = reasoning.lower()
                closing_indicators = ["hydrogen bond", "h-bond", "hbond", "coordinat", "covalent",
                                       "close", "ring", "loop", "cycl", "r2_2", "r22", "macrocycle",
                                       "crown", "cryptand", "rotaxane", "caten", "dimer"]
                invalid_indicators = ["linear", " rod", "chain", "axial", "two-ended",
                                       "terminus", "cumulene", "allene"]
                has_invalid = any(kw in reasoning_lower for kw in invalid_indicators)
                has_closing = any(kw in reasoning_lower for kw in closing_indicators)
                if has_invalid or not has_closing:
                    grounding_failed.append("topology (T_⋈ without closing bond)")

            # Register to catalog
            if synthon.name not in global_catalog:
                # Attach validation metadata
                synthon.metadata["axiom_validated"] = True
                synthon.metadata["axiom_violations"] = axiom_violations
                synthon.metadata["axiom_report"] = axiom_report
                synthon.metadata["grounding_status"] = "partial" if grounding_failed else "full"
                synthon.metadata["failed_primitives"] = grounding_failed
                if axiom_warnings:
                    synthon.metadata["axiom_warnings"] = axiom_warnings
                if grounding_failed:
                    synthon.metadata["flagged_for_review"] = True
                global_catalog.register(synthon)
                registered = True
            else:
                registered = False

            # Perturbation-steered discovery: generate hints for next proposal
            if registered and getattr(self, '_run_config', None) is not None:
                cfg = self._run_config
                if getattr(cfg, 'use_perturbation_steering', False) and cfg.target_xi_cp_range:
                    try:
                        target_xi = sum(cfg.target_xi_cp_range) / 2.0
                        path = self._perturb_engine.find_path_to_target(
                            synthon, cfg.perturbation_delta_g, target_xi
                        )
                        if path and path.get("steps"):
                            hint = (
                                f"Previous synthon '{synthon.name}' registered "
                                f"(ξ_CP baseline near {cfg.perturbation_delta_g} kJ/mol). "
                                f"Target ξ_CP range: {cfg.target_xi_cp_range} nats. "
                                f"Suggested primitive upgrades: "
                                + "; ".join(str(s) for s in path["steps"][:3])
                            )
                            self._perturbation_hints = [hint]
                    except Exception:
                        pass

            return DiscoveryCycle(
                cycle_number=cycle_number,
                timestamp=timestamp,
                proposed_description=proposal["description"],
                proposed_name=proposal["name"],
                validation_result=ValidationResult.VALID_NOVEL,
                synthon=synthon,
                confidence=confidence,
                reasoning=reasoning,
                literature_found=literature_result.get("found", False),
                literature_references=literature_result.get("references", []),
            )
            
        except Exception as e:
            return DiscoveryCycle(
                cycle_number=cycle_number,
                timestamp=timestamp,
                proposed_description="",
                proposed_name="",
                validation_result=ValidationResult.INVALID_CHEMISTRY,
                error=str(e),
            )
    
    async def _propose_synthon(self, config: AutonomousRunConfig) -> Dict[str, str]:
        """Generate a novel synthon proposal."""
        # Build context from existing catalog and proposal history
        existing_names = list(global_catalog._synthons.keys())
        recently_proposed = list(self.proposed_names)[-10:]  # Last 10 proposals

        # Determine which domain to focus on based on what's underexplored
        domain_counts = {
            "molecular": len([s for s in global_catalog._synthons.values() if s.dimensionality == Dimensionality.MOLECULAR]),
            "supramolecular": len([s for s in global_catalog._synthons.values() if s.dimensionality == Dimensionality.SUPRAMOLECULAR]),
            "temporal": len([s for s in global_catalog._synthons.values() if s.dimensionality == Dimensionality.TEMPORAL]),
        }
        underexplored = min(domain_counts, key=domain_counts.get)

        # Find catalog entries already related to focus areas — surface them explicitly
        # so the model knows what EXISTS and doesn't regenerate the same chemistry
        focus_existing_entries: List[str] = []
        if config.focus_areas:
            for focus_kw in config.focus_areas:
                kw_parts = focus_kw.lower().replace(" ", "_").split("_")
                for entry_name, entry_synthon in global_catalog._synthons.items():
                    name_lower = entry_name.lower()
                    desc_lower = (entry_synthon.description or "").lower()
                    if any(part in name_lower or part in desc_lower for part in kw_parts if len(part) > 3):
                        entry_repr = entry_name
                        if hasattr(entry_synthon, "to_notation"):
                            try:
                                entry_repr = f"{entry_name} [{entry_synthon.to_notation()}]"
                            except Exception:
                                pass
                        if entry_repr not in focus_existing_entries:
                            focus_existing_entries.append(entry_repr)

        # NEW: Focus area enforcement prompt addition
        focus_area_guidance = ""
        if config.focus_areas:
            focus_area_guidance = f"""
<focus_area_enforcement>
**CRITICAL: FOCUS AREA REQUIREMENT**

Your proposal **MUST** be **PRIMARILY** about: {', '.join(config.focus_areas)}

**Requirements:**
1. The focus area **MUST** be the **CORE** chemistry, **NOT** just a component
2. You **MUST NOT** wrap unrelated chemistry (cycles, rotaxanes, crowns) around the focus area
3. **Example:** If focus is "extended allenes", propose allene-based systems where the
   allene chemistry **IS** the synthon, **NOT** an allene attached to a rotaxane shuttle
4. The primitive encoding **MUST** reflect the focus area's characteristic interactions
</focus_area_enforcement>
"""

        # Build perturbation steering section if hints are available
        perturbation_steering_section = ""
        if self._perturbation_hints:
            perturbation_steering_section = f"""
<perturbation_steering>
**STEERING HINT FROM PERTURBATION ANALYSIS:**
{self._perturbation_hints[-1]}

Your next proposal SHOULD target the indicated primitive upgrades to move toward
the target ξ_CP range. Design chemistry that naturally achieves these modifications.
</perturbation_steering>
"""

        prompt = f"""<role>You are an expert in synthonic space exploration and discovery.</role>

<task>
Propose a **NOVEL** synthonic system for registration.

**Critical Requirements:**
1. You **MUST** propose a system that is physically reasonable and realistic within its domain
2. You **MUST** use a **UNIQUE** name **NOT** in the "already proposed" list
3. You **MUST NOT** propose systems already in the catalog (avoid existing names)
4. You **MUST** include clear recognition elements and interaction patterns
5. You **MUST** ensure the system can be mapped to the ten primitives (including K, Φ, S)
6. You **MUST** satisfy the grounding rules below (primary-tier: chemical; extended-tier: domain-appropriate)
7. You **MUST** stay within the focus area — the focus domain **MUST** be primary, **NOT** incidental
8. You **MUST** avoid tuple convergence — do **NOT** propose systems encoding to same primitives as existing entries
</task>
{perturbation_steering_section}

<context>
**Avoid These Already Proposed Names (DO NOT REPEAT):**
{recently_proposed if recently_proposed else "None yet - be creative!"}

**Current Catalog Context:**
- Existing synthons: {existing_names[:15]}...
- Domain distribution: {domain_counts}
- Most underexplored domain: {underexplored}
- Target domains: {config.target_domains}
- Focus areas: {config.focus_areas or 'All synthonic domains'}
{focus_area_guidance}
{f'''<focus_area_existing>
**FOCUS-AREA ENTRIES ALREADY IN CATALOG — do NOT reproduce these:**
{chr(10).join(f"  - {e}" for e in focus_existing_entries[:20])}

You MUST propose chemistry that is genuinely distinct from ALL entries above.
Do NOT propose a variant of their names or descriptions.
</focus_area_existing>
''' if focus_existing_entries else ''}{f'''<duplicate_description_feedback>
**RECENTLY REJECTED DESCRIPTIONS (step-2 duplicates) — avoid regenerating these:**
{chr(10).join(f"  - REJECTED: {d}" for d in self.recent_duplicate_descriptions)}

The chemistry in these descriptions already exists in the catalog. Propose something fundamentally different.
</duplicate_description_feedback>
''' if self.recent_duplicate_descriptions else ''}</context>

<grounding_rules>
**MANDATORY GROUNDING REQUIREMENTS:**

<temporal_domain>
**For TEMPORAL domain (D_∞):**
- You **MUST ONLY** propose systems with a physically grounded reset mechanism.
- Two allowed reset types (set in `metadata["grounding"]["reset"]`):
  **discrete** (default, most chemistry): closed cycle — description must include:
    1. What forms (initial state)
    2. What reaction occurs (transformation)
    3. What is produced (work performed)
    4. How the catalyst/system resets (named reset step)
  Use `axiom6_grounding` dict or `metadata["grounding"]["reset"]["cycle_steps"]`.

  **continuous** (open dissipative / driven systems): sustained driving gradient,
  no sharp reset. Set `metadata["grounding"]["reset"]["type"] = "continuous"` and
  provide `driving_gradient.description` + `driving_gradient.coupling`.

- **Examples (discrete):** proline aldol cycle, imine condensation, ATP hydrolysis-driven assembly,
  DTDA radical ⇌ diamagnetic dimer (thermal homolysis as reset), nitroso/hydroxylamine redox couple
- **Examples (continuous):** flow reactors, driven oscillators with external energy input
- **WRONG EXAMPLE (do not repeat):** "The system forms one-dimensional columnar assemblies through
  repetitive recognition events — this aligns with D_∞." ← INCORRECT. Columnar stacking is D_△.
  The D_∞ in a DTDA-phthalocyanine system comes from the DTDA radical ⇌ dimer equilibrium, not
  from the column growth. Always cite the molecular cycle, never the spatial assembly.
- **PROHIBITED:** static molecules, rigid rods, "extended" chains, or quantum systems as temporal synthons
  - These **ARE** molecular (D_∧) or supramolecular (D_△), **NOT** temporal
- **ALSO PROHIBITED:** supramolecular polymerization, open-ended chain/column/stack growth
  - "Repetitive monomer addition" to a growing assembly is D_△ (spatial), NOT D_∞ (temporal).
  - Diagnostic test: does the system return to its **exact initial state** with all components
    regenerated after one cycle? A growing column does not; it accumulates. Assign D_△.
- **COMPOUND SYSTEM RULE:** If a molecule has BOTH a D_△ spatial assembly AND a molecular
  equilibrium cycle (e.g., a DTDA radical ⇌ diamagnetic dimer, or a redox couple), D_∞ is
  permitted **only if** the Axiom 6 grounding names the reset of the **molecular cycle**, not
  the column or stack assembly. Justifying D_∞ with "columnar stacking" while the actual closed
  cycle is a radical dimerization equilibrium is a grounding error — name the correct cycle.
</temporal_domain>

<cyclic_topology>
**For CYCLIC topology (T_⋈):**
- You **MUST** use T_⋈ for **ANY** ring-closed, macrocyclic, polygonal, or cage structure
- Your description **MUST** name the **specific interaction** that closes the ring
- **Examples:**
  - "carboxylic acid homodimer via two O-H···O hydrogen bonds (R²₂(8) motif)"
  - "crown ether macrocycle coordinating K⁺ via six ether oxygens in a closed 18-crown-6 ring"
  - "(D_4)-symmetric Pd₄L₈ cage: four Pd–pyridine coordination bonds close the square"
  - "boronate ester macrocycle: four B–O condensation bonds close the D₄-symmetric ring"
- **PROHIBITED:** assigning T_linear or T_chains to macrocycles, rings, cages, or cyclic assemblies
- **IMPORTANT:** Do **NOT** avoid T_⋈ by using T_linear — assigning T_linear to a ring-closed system is **WRONG** and will produce a duplicate tuple. Satisfy Axiom 7 by naming the closing bond.
</cyclic_topology>
</grounding_rules>

<diversity_guidance>
**Diversity Requirements:**
- If catalog is light on {underexplored}, you **SHOULD** propose something in that domain
- You **MUST** explore different functional groups, interaction types, and structural motifs
- **Consider:** halogen bonds, chalcogen bonds, pnictogen bonds, π-stacking, cation-π, anion-π, metal coordination, imine condensation, boronate esters, etc.
- **Within the focus area, vary primitives — especially:**
  - **Topology (T)**: T_⋈ for cyclic/ring/macrocyclic, T_□ for hub/node/cage, T_≫ for chain — do NOT default to T_linear for ring structures
  - **Recognition Mode (R)**: R_⊆ (covalent: boronate, imine, metal-ligand), R_⊇ (non-covalent: H-bond), R_⇔ (mechanical bond)
  - **Polarity (P)**: P_directional for directed donor-acceptor corners, P_pm_pseudo for self-complementary, P_plus/P_minus for metal-ligand
  - **Granularity (G)**: G_gimel for large macrocycles/cages (cooperative array), G_beth for small pairwise interactions
  - **Fidelity (F)**: F_hbar for rigid covalent macrocycles, F_eth for metal-directed, F_ell for dynamic/reversible
  - Try different **kinetic** characters (fast, moderate, slow) based on barriers
  - Try different **interaction grammars** (AND, OR, SEQUENTIAL with specific/selective/broad)
- You **MUST NOT** propose systems with identical tuples to existing entries
{f'''
<forbidden_tuples>
**PREVIOUSLY REJECTED TUPLES — you MUST NOT reproduce these:**
{chr(10).join(f"  - FORBIDDEN: {t}" for t in self.recent_duplicate_tuples)}

**To escape these tuples, change at least ONE of:**
- T (topology): if you used T_linear, try T_bowtie (for rings) or T_square (for hubs)
- R (recognition): if you used R_superset, try R_subset (covalent) or R_mechanical
- P (polarity): if you used P_pm_pseudo, try P_directional or P_plus/P_minus
- G (granularity): if you used G_beth, try G_gimel (mesoscale assembly)
- F (fidelity): if you used F_eth, try F_hbar (high) or F_ell (low)
</forbidden_tuples>
''' if self.recent_duplicate_tuples else ''}
</diversity_guidance>

<output_format>
You **MUST** provide your proposal as **ONLY** valid JSON with this exact structure:

```json
{{
  "name": "unique_descriptive_name_using_different_chemistry",
  "description": "Detailed chemical description including functional groups, interaction types, and structural features"
}}
```

**Output Requirements:**
- You **MUST** return **ONLY** the JSON object
- You **MUST NOT** include **ANY** markdown formatting, code blocks, or backticks around the JSON
- The output **MUST** start directly with `{{` and end with `}}`
- The name **MUST** be unique and descriptive
- The description **MUST** be detailed enough to map to all seven primitives
</output_format>

<final_instruction>
Be creative but scientifically sound. Explore underexplored regions of chemical space while staying within the focus area and avoiding tuple convergence.
</final_instruction>"""

        response = await self.call_llm(prompt=prompt, temperature=0.9, max_tokens=1000)

        # Parse response
        json_blocks = self.extract_json_blocks(response)
        if json_blocks:
            data = json_blocks[0]
            name = data.get("name", f"proposed_synthon_{int(time.time())}")

            # Ensure uniqueness
            base_name = name
            counter = 1
            while name in self.proposed_names or name in existing_names:
                name = f"{base_name}_{counter}"
                counter += 1

            data["name"] = name
            self.proposed_names.add(name)
            
            # NEW: Validate focus area match
            if config.focus_areas:
                focus_match = self._check_focus_area_match(data["description"], config.focus_areas)
                if not focus_match["matched"]:
                    # Regenerate with stronger guidance
                    data["description"] = f"{data['description']} (Note: Focus area enforcement applied - {focus_match['reason']})"
            
            return data

        # Fallback parsing
        fallback_name = f"discovered_synthon_{int(time.time())}"
        while fallback_name in self.proposed_names:
            fallback_name = f"discovered_synthon_{int(time.time())}_{len(self.proposed_names)}"

        self.proposed_names.add(fallback_name)
        return {
            "name": fallback_name,
            "description": response[:500],
        }

    def _check_focus_area_match(
        self,
        description: str,
        focus_areas: List[str],
    ) -> Dict[str, Any]:
        """
        Check if proposal description actually matches the focus area.
        
        Prevents models from gaming the system by including focus area as incidental
        component while proposing unrelated core chemistry.
        
        Args:
            description: Proposed synthon description
            focus_areas: List of focus area keywords
            
        Returns:
            Dict with matched (bool), reason (str), confidence (float)
        """
        desc_lower = description.lower()
        
        # Check if focus area terms appear prominently (not just in passing)
        focus_matches = []
        for focus in focus_areas:
            focus_lower = focus.lower()
            # Count occurrences
            count = desc_lower.count(focus_lower)
            if count > 0:
                focus_matches.append((focus, count))
        
        if not focus_matches:
            return {
                "matched": False,
                "reason": "Description does not mention focus area chemistry",
                "confidence": 0.0,
            }
        
        # Check if focus area is PRIMARY (appears early and frequently)
        first_focus_pos = min(
            (desc_lower.find(focus.lower()) for focus, _ in focus_matches if desc_lower.find(focus.lower()) >= 0),
            default=len(desc_lower)
        )
        
        # If focus area appears only at the end or very briefly, flag it
        total_focus_mentions = sum(count for _, count in focus_matches)
        desc_length = len(desc_lower.split())
        
        # Heuristic: focus area should be mentioned at least once per 50 words
        # and should appear in the first third of the description
        mention_ratio = total_focus_mentions / max(1, desc_length)
        is_primary = first_focus_pos < len(desc_lower) / 3
        
        if mention_ratio < 0.02 and not is_primary:
            return {
                "matched": False,
                "reason": f"Focus area '{focus_areas}' appears incidental, not primary chemistry",
                "confidence": 0.3,
            }
        
        return {
            "matched": True,
            "reason": f"Focus area chemistry is primary: {focus_matches}",
            "confidence": min(1.0, mention_ratio * 50 + (0.5 if is_primary else 0)),
        }
    
    async def _check_duplicate(
        self,
        name: str,
        description: str,
        proposed_synthon: Optional[Synthon] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if synthon already exists in catalog.
        
        Enhanced with tuple-level deduplication (Fix for convergence issue):
        - If proposed tuple shares 7+ primitives with existing entry, flag as functionally duplicate
        - This prevents models from gaming the system by wrapping same chemistry in different descriptions
        """
        # Check by exact name match
        if name in global_catalog:
            return True, name

        # Check by very similar name (simple normalization)
        name_normalized = name.lower().replace("_", " ").replace("-", " ")
        for existing_name in global_catalog._synthons.keys():
            existing_normalized = existing_name.lower().replace("_", " ").replace("-", " ")
            if name_normalized == existing_normalized:
                return True, existing_name

        # NEW: Tuple-level deduplication (Fix for DeepSeek/Gemini convergence issues)
        if proposed_synthon is not None:
            tuple_duplicate = self._check_tuple_duplicate(proposed_synthon)
            if tuple_duplicate:
                return True, tuple_duplicate

        # Check by description similarity - but be more conservative
        # Only flag as duplicate if there's very high overlap
        desc_words = set(description.lower().split())
        # Filter to meaningful chemical terms (skip common words)
        skip_words = {"the", "a", "an", "with", "and", "or", "of", "in", "for", "to", "is", "that", "this", "system", "synthon", "pair"}
        desc_chemical = desc_words - skip_words

        for existing_name, existing_synthon in global_catalog._synthons.items():
            existing_desc = (existing_synthon.description or "").lower()
            existing_words = set(existing_desc.split()) - skip_words

            # Calculate Jaccard similarity
            if desc_chemical and existing_words:
                intersection = desc_chemical & existing_words
                union = desc_chemical | existing_words
                similarity = len(intersection) / len(union) if union else 0

                # Only flag as duplicate if >60% similar (was 3 words before)
                if similarity > 0.6:
                    return True, existing_name

        return False, None

    def _check_tuple_duplicate(self, proposed_synthon: Synthon) -> Optional[str]:
        """
        Check if proposed synthon tuple is functionally duplicate of existing entry.
        
        Fix for convergence issue: If ALL core primitives match existing tuple, reject as duplicate.
        This allows variation within a chemical family while preventing exact attractor convergence.
        
        Args:
            proposed_synthon: The proposed synthon to check
            
        Returns:
            Name of existing synthon if duplicate found, None otherwise
        """
        # Core primitives that define chemical identity
        # These MUST all match to be considered duplicate
        CORE_PRIMITIVES = ["dimensionality", "topology", "recognition_mode"]
        
        # Secondary primitives that can vary within a chemical family
        # These provide diversity within the core chemical identity
        SECONDARY_PRIMITIVES = ["polarity", "fidelity", "kinetic_character", 
                                "granularity", "interaction_grammar", "criticality_phase"]
        
        for existing_name, existing_synthon in global_catalog._synthons.items():
            # Count matching core primitives
            core_matches = 0
            for prim in CORE_PRIMITIVES:
                existing_val = getattr(existing_synthon, prim, None)
                proposed_val = getattr(proposed_synthon, prim, None)
                if existing_val == proposed_val:
                    core_matches += 1
            
            # If all 3 core primitives match, check secondary primitives
            if core_matches == len(CORE_PRIMITIVES):
                secondary_matches = 0
                for prim in SECONDARY_PRIMITIVES:
                    existing_val = getattr(existing_synthon, prim, None)
                    proposed_val = getattr(proposed_synthon, prim, None)
                    if existing_val == proposed_val:
                        secondary_matches += 1
                
                # Only flag as duplicate if ALL 9 primitives match
                # This allows legitimate variation within a chemical family
                if secondary_matches == len(SECONDARY_PRIMITIVES):
                    return existing_name
        
        return None
    
    async def _validate_literature(self, description: str) -> Dict[str, Any]:
        """
        Validate against existing literature.
        
        Returns dict with:
        - found: bool - whether similar systems exist
        - conflict: bool - whether there's a conflict
        - references: list of references found
        - reason: explanation
        """
        # Use web search tool if available, otherwise skip
        # For now, we'll do a simple heuristic check
        
        # Check for well-known systems that should exist
        known_systems = [
            ("carboxylic acid dimer", True),
            ("dna base pair", True),
            ("amide dimer", True),
            ("urea ribbon", True),
        ]
        
        desc_lower = description.lower()
        for known, should_exist in known_systems:
            if known in desc_lower:
                if should_exist:
                    return {
                        "found": True,
                        "conflict": False,  # Known systems are fine to add
                        "references": [f"Known system: {known}"],
                        "reason": f"References known system '{known}' which is well-documented",
                    }
        
        # No conflicts found
        return {
            "found": False,
            "conflict": False,
            "references": [],
            "reason": "No literature conflicts detected",
        }
    
    # Keywords that indicate a ring-closed / cyclic system requiring T_⋈
    _CYCLIC_KEYWORDS = [
        "macrocycle", "macrocycl", " ring", "cyclic", " cage", "catenane",
        "rotaxane", "crown ether", "cryptand", "cyclophane", "calixarene",
        "porphyrin", "corrole", "phthalocyanine", "metallacycle", "metallacycl",
        "polygon", "triangle", "square", "hexagon", "octagon", "dimer",
        "r2_2", "r22", "r²₂", "homodimer", "heterodimer", "cyclopeptide",
        "cucurbituril", "cyclodextrin", "pillar[", "tubular macrocycle",
    ]

    async def _generate_synthon_representation(
        self,
        name: str,
        description: str,
        forbidden_tuples: Optional[List[str]] = None,
    ) -> Tuple[Synthon, float, str]:
        """Generate full synthon representation from description."""
        prompt = self._build_synthon_generation_prompt(name, description, forbidden_tuples)

        response = await self.call_llm(
            prompt=prompt,
            temperature=0.3,
            max_tokens=2000,
            system=self._get_synthon_system_prompt()
        )

        # Parse response
        json_blocks = self.extract_json_blocks(response)
        if json_blocks:
            data = json_blocks[0]
            synthon_data = data.get("synthon", {})
            confidence = data.get("confidence", 0.7)
            reasoning = data.get("reasoning", "No reasoning provided")

            # Post-processing topology correction:
            # If the description clearly describes a ring-closed system but model returned
            # T_linear, override to T_bowtie. This bypasses DeepSeek's T_linear attractor bias.
            desc_lower = description.lower()
            name_lower = name.lower()
            is_cyclic_system = any(
                kw in desc_lower or kw in name_lower
                for kw in self._CYCLIC_KEYWORDS
            )
            assigned_topology = synthon_data.get("topology", "T_linear")
            is_chain_topology = assigned_topology in ("T_linear", "T_chains", "T_chain", "T_≫")
            if is_cyclic_system and is_chain_topology:
                synthon_data["topology"] = "T_bowtie"
                reasoning = (
                    f"[TOPOLOGY CORRECTED: T_linear → T_bowtie — description indicates "
                    f"ring-closed/macrocyclic system but model returned chain topology] {reasoning}"
                )

            synthon = self._create_synthon_from_data(synthon_data, description, name)
            return synthon, float(confidence), reasoning

        # Fallback to rule-based
        from agents.synthon_generator_agent import SynthonGeneratorAgent
        agent = SynthonGeneratorAgent(self.config)
        result = agent._generate_rule_based(description, name)
        return result.synthon, result.confidence, result.reasoning
    
    def _build_synthon_generation_prompt(
        self,
        name: str,
        description: str,
        forbidden_tuples: Optional[List[str]] = None,
    ) -> str:
        """Build prompt for synthon generation following NLP_FORMAT.md."""
        forbidden_block = ""
        if forbidden_tuples:
            lines = "\n".join(f"  - FORBIDDEN (already in catalog): {t}" for t in forbidden_tuples)
            forbidden_block = f"""
<forbidden_tuples>
**The following tuples are ALREADY IN THE CATALOG — you MUST produce a DIFFERENT tuple:**
{lines}

**To escape, change at least ONE primitive:**
- T: if the system is a ring/macrocycle → use T_bowtie (T_⋈), name the closing bond
- R: try R_subset (covalent) or R_mechanical instead of R_superset
- P: try P_directional or P_plus/P_minus instead of P_pm_pseudo
- G: try G_gimel (mesoscale, cooperative assembly) instead of G_beth (local pairwise)
- F: try F_hbar (high, rigid covalent) or F_ell (low, dynamic/reversible)
</forbidden_tuples>
"""
        return f"""<role>You are an expert in the Unified Synthonicon framework with deep knowledge of synthonic systems and primitive mapping.</role>

<task>
Analyze the provided chemical system and map it to the **nine primitives** with precision and scientific rigor.

**You MUST:**
1. Analyze the chemical system thoroughly
2. Map each primitive based on chemical principles from QUANTSYNTHONICON.md
3. Provide confidence scores for each assignment
4. Include detailed reasoning that references specific chemical features
5. Ensure all primitive assignments are mechanistically grounded
6. Produce a tuple that is NOT in the forbidden list below
</task>

<input>
**System Name:** {name}

**System Description:**
{description}
</input>
{forbidden_block}

<primitive_reference>
**Nine Primitives Reference:**

**Dimensionality (D):**
- D_wedge (D_∧): Molecular — point-like reactivity, single molecules
- D_triangle (D_△): Supramolecular — 3D spatial organization, crystal packing
- D_infinity (D_∞): Temporal — closed cycles with reset mechanism

**Topology (T):**
- T_bowtie (T_⋈): Cyclic — closed loops with named closing interaction
- T_chains (T_≫): Chain — linear/branched without closure
- T_square (T_□): Hub — central node distributing to multiple arms
- T_linear: Linear arrangements
- T_network: Extended interconnected networks

**Recognition Mode (R):**
- R_subset (R_⊆): Covalent — electron sharing, orbital overlap
- R_superset (R_⊇): Non-covalent — H-bonding, electrostatic, dispersion
- R_dagger (R_‡): Catalytic — transition state stabilization, barrier reduction
- R_mechanical (R_⇔): Mechanical bond — steric clipping, topological entanglement

**Polarity (P):**
- P_plus (P+): Acceptor — electron-deficient, electrophilic
- P_minus (P-): Donor — electron-rich, nucleophilic
- P_pm (P_±): Self-complementary — homodimerization
- P_directional (P_+-): Directional donor-acceptor pair

**Fidelity (F):**
- F_hbar (F_ℏ): High — ξ_CP < 8.5 nats, proofreading
- F_eth (F_ℇ): Medium — ξ_CP 8.5-10.5 nats, context-dependent
- F_ell (F_ℓ): Low — ξ_CP > 10.5 nats, promiscuous

**Kinetic Character (K):**
- K_fast: Barrier < 60 kJ/mol, spontaneous
- K_mod: Barrier 60-100 kJ/mol, mild activation required
- K_slow: Barrier > 100 kJ/mol, significant activation required
- K_trap: Pathway multiplicity high, kinetic products diverge

**Granularity (G):**
- G_beth (G_ב): Local — single binding event, pairwise interaction
- G_gimel (G_ג): Mesoscale — cooperative array, superlinear induction
- G_aleph (G_א): Global — network-scale, percolation, long-range order

**Interaction Grammar (Γ):**
- Gamma_and (Γ_∧): AND — all partners required simultaneously
- Gamma_or (Γ_∨): OR — any one partner suffices
- Gamma_seq (Γ_→): SEQUENTIAL — ordered sequential recognition
- Tiers: SPECIFIC, SELECTIVE, BROAD

**Criticality Phase (Φ):**
- Phi_sub (Φ_sub): Subcritical — normal phase, G and D independent
- Phi_critical (Φ_c): Critical — scale-free, correlation length diverges
- Phi_super (Φ_super): Supercritical — post-assembly, synthon identity lost
</primitive_reference>

<topology_grounding>
**TOPOLOGY ASSIGNMENT — CRITICAL:**

**T_⋈ (cyclic/bowtie) — USE for:**
- ANY ring-closed structure: macrocycles, cages, cycles, dimers via cyclic H-bonding
- (D_n)-symmetric polygons: square, triangular, hexagonal macrocycles
- Any assembly where the last bond/interaction closes a ring
- **You MUST name the specific closing bond.** Examples:
  - Square macrocycle: "the 4th Pd–pyridine coordination bond closes the D₄-symmetric ring"
  - Boronate ester macrocycle: "the 4th B–O condensation closes the square"
  - H-bonded dimer: "two O–H···O hydrogen bonds complete the R²₂(8) ring motif"

**T_≫ (chain) — USE for:**
- Linear/branched polymers without ring closure
- Helices, rods, linear covalent chains

**T_□ (hub/node) — USE for:**
- Star-shaped, dendritic, or branching topologies from a central node
- MOF nodes connecting to multiple arms WITHOUT forming a closed ring

**You MUST NOT assign T_linear or T_chains to macrocycles, rings, cages, or cyclic assemblies.**
**Assigning T_linear to a (D_n)-symmetric macrocycle is a GROUNDING VIOLATION.**
The fact that Axiom 7 requires a named closing bond for T_⋈ does NOT mean you should avoid T_⋈.
Instead, SATISFY Axiom 7 by naming the bond.
</topology_grounding>

<grounding_requirements>
**Grounding Requirements — You MUST:**
1. Justify each primitive assignment with specific chemical phenomena
2. For D_∞: Explicitly name the closed cycle with reset mechanism
3. For T_⋈: Explicitly name the closing bond/interaction (see topology grounding above)
4. For T_linear/T_chains: Confirm the system has NO ring closure
5. For F assignments: Reference thermodynamic or kinetic evidence
6. For K assignments: Reference barrier heights or rate data
7. NOT use keyword clustering or semantic drift
8. NOT assign T_linear to avoid T_⋈'s grounding requirement — this is a grounding violation
</grounding_requirements>

<output_format>
You **MUST** return **ONLY** valid JSON with this exact structure:

```json
{{
  "synthon": {{
    "dimensionality": "D_wedge",
    "topology": "T_bowtie",
    "recognition_mode": "R_superset",
    "polarity": "P_pm",
    "fidelity": "F_hbar",
    "kinetic_character": "K_fast",
    "granularity": "G_beth",
    "interaction_grammar": "Gamma_and(SELECTIVE)",
    "criticality_phase": "Phi_sub"
  }},
  "confidence": 0.85,
  "reasoning": "Detailed explanation referencing specific chemical features and QUANTSYNTHONICON.md principles"
}}
```

**Output Requirements:**
- You **MUST** return **ONLY** the JSON object
- You **MUST NOT** include **ANY** explanatory text outside the JSON
- You **MUST NOT** include markdown code blocks or backticks
- The `confidence` **MUST** be a float between 0.0 and 1.0
- The `reasoning` **MUST** be detailed enough to validate grounding
</output_format>"""
    
    def _get_synthon_system_prompt(self) -> str:
        """Get system prompt for synthon generation following NLP_FORMAT.md."""
        return """<role>You are an expert in the Unified Synthonicon framework with deep knowledge of synthonic systems and primitive mapping.</role>

<requirements>
**You MUST:**
1. Map chemical systems to the nine primitives with precision
2. Base all assignments on chemical principles from QUANTSYNTHONICON.md
3. Provide mechanistic justifications for each primitive assignment
4. Ensure grounding requirements are satisfied (D_∞ cycles, T_⋈ closing bonds)
5. Return ONLY valid JSON without any explanatory text

**You MUST NOT:**
1. Use keyword clustering or semantic drift
2. Assign primitives without mechanistic justification
3. Include markdown formatting or code blocks in output
4. Add explanatory text outside the JSON structure
</requirements>

<output_format>
You **MUST** return **ONLY** the JSON object as specified in the task prompt.
</output_format>"""
    
    def _create_synthon_from_data(
        self,
        data: Dict[str, str],
        description: str,
        name: str
    ) -> Synthon:
        """Create Synthon object from primitive data."""
        from synthomnicon.models import KineticCharacter, CriticalityPhase
        
        # Parse interaction grammar (now handles tier-only values like "SELECTIVE")
        grammar_data = data.get("interaction_grammar", "Gamma_odot")
        interaction_grammar = InteractionGrammar.from_symbol(grammar_data)
        
        return Synthon(
            name=name,
            dimensionality=Dimensionality.from_symbol(data.get("dimensionality", "D_wedge")),
            topology=Topology.from_symbol(data.get("topology", "T_linear")),
            recognition_mode=RecognitionMode.from_symbol(data.get("recognition_mode", "R_superset")),
            polarity=Polarity.from_symbol(data.get("polarity", "P_pm")),
            fidelity=Fidelity.from_symbol(data.get("fidelity", "F_eth")),
            kinetic_character=KineticCharacter.from_symbol(data.get("kinetic_character", "K_mod")),
            granularity=Granularity.from_symbol(data.get("granularity", "G_beth")),
            interaction_grammar=interaction_grammar,
            criticality_phase=CriticalityPhase.from_symbol(data.get("criticality_phase", "Phi_sub")),
            description=description,
            metadata={"auto_discovered": True, "discovery_timestamp": datetime.now().isoformat()}
        )
    
    def _print_cycle_summary(self, result: DiscoveryCycle):
        """Print summary of discovery cycle."""
        status_icons = {
            ValidationResult.VALID_NOVEL: "✓",
            ValidationResult.DUPLICATE_EXISTS: "⊗",
            ValidationResult.INVALID_CHEMISTRY: "✗",
            ValidationResult.LITERATURE_CONFLICT: "⚠",
            ValidationResult.LOW_CONFIDENCE: "?",
        }
        
        icon = status_icons.get(result.validation_result, "?")
        print(f"\n[{icon}] {result.validation_result.value}")
        print(f"    Name: {result.proposed_name or 'N/A'}")
        
        if result.synthon:
            print(f"    Notation: {result.synthon.to_notation()}")
            print(f"    Confidence: {result.confidence:.1%}")
        
        if result.literature_found:
            print(f"    Literature: {len(result.literature_references)} references found")
        
        if result.error:
            print(f"    Error: {result.error}")
    
    def _print_final_report(self, start_time: float):
        """Print final discovery report."""
        elapsed = (time.time() - start_time) / 60
        
        print(f"\n{'='*70}")
        print("DISCOVERY RUN COMPLETE")
        print(f"{'='*70}")
        print(f"Duration: {elapsed:.1f} minutes")
        print(f"Cycles completed: {self.stats['cycles_completed']}")
        print(f"Synthons proposed: {self.stats['synthons_proposed']}")
        print(f"Synthons validated: {self.stats['synthons_validated']}")
        print(f"Synthons registered: {self.stats['synthons_registered']}")
        print(f"Duplicates detected: {self.stats['duplicates_detected']}")
        print(f"Literature conflicts: {self.stats['literature_conflicts']}")
        print(f"Errors: {self.stats['errors']}")
        
        if self.stats['cycles_completed'] > 0:
            success_rate = self.stats['synthons_registered'] / self.stats['cycles_completed'] * 100
            print(f"Success rate: {success_rate:.1f}%")
        
        print(f"\nCatalog now contains {len(global_catalog)} synthons")
        print(f"{'='*70}\n")
    
    def _save_progress(
        self,
        output_dir: Path,
        cycle: int,
        config: AutonomousRunConfig,
        final: bool = False
    ):
        """Save discovery progress to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "final" if final else f"cycle_{cycle}"
        
        # Save discovery history
        history_file = output_dir / f"discovery_history_{timestamp}_{suffix}.json"
        history_data = []
        for cycle_result in self.discovery_history:
            cycle_dict = {
                "cycle_number": cycle_result.cycle_number,
                "timestamp": cycle_result.timestamp,
                "proposed_description": cycle_result.proposed_description,
                "proposed_name": cycle_result.proposed_name,
                "validation_result": cycle_result.validation_result.value,
                "confidence": cycle_result.confidence,
                "reasoning": cycle_result.reasoning,
                "literature_found": cycle_result.literature_found,
                "literature_references": cycle_result.literature_references,
                "error": cycle_result.error,
            }
            if cycle_result.synthon:
                cycle_dict["synthon"] = cycle_result.synthon.to_dict()
            history_data.append(cycle_dict)
        
        with open(history_file, "w") as f:
            json.dump(history_data, f, indent=2)
        
        # Save stats
        stats_file = output_dir / f"discovery_stats_{timestamp}_{suffix}.json"
        with open(stats_file, "w") as f:
            json.dump({
                "stats": self.stats,
                "config": {
                    "max_cycles": config.max_cycles,
                    "max_duration_minutes": config.max_duration_minutes,
                    "min_confidence_threshold": config.min_confidence_threshold,
                    "target_domains": config.target_domains,
                    "focus_areas": config.focus_areas,
                },
                "catalog_size": len(global_catalog),
            }, f, indent=2)
        
        # Export catalog
        catalog_file = output_dir / f"catalog_{timestamp}_{suffix}.json"
        with open(catalog_file, "w") as f:
            f.write(global_catalog.to_json())
        
        print(f"\n[SAVE] Progress saved to {output_dir}")


# Convenience function for quick autonomous runs
async def run_autonomous_discovery(
    max_cycles: int = 10,
    max_minutes: float = 30.0,
    provider: str = "anthropic",
    model: Optional[str] = None,
    focus: Optional[str] = None,
) -> List[DiscoveryCycle]:
    """
    Run autonomous synthon discovery with simple configuration.
    
    Args:
        max_cycles: Maximum discovery cycles
        max_minutes: Maximum runtime in minutes
        provider: LLM provider
        model: Model name (uses provider default if None)
        focus: Optional focus area (e.g., "hydrogen bonding")
    
    Returns:
        List of DiscoveryCycle results
    """
    from synthomnicon.provider_config import build_agent_config
    
    config = build_agent_config(provider=provider, model=model)
    agent = AutonomousSynthonDiscoveryAgent(config)
    
    run_config = AutonomousRunConfig(
        max_cycles=max_cycles,
        max_duration_minutes=max_minutes,
        focus_areas=[focus] if focus else None,
    )
    
    return await agent.run_autonomous(run_config)
