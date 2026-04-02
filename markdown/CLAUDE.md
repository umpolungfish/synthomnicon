# SynthOmnicon — Claude Code configuration

## LaTeX formatting (mandatory, all output)
All mathematical symbols in ALL output (code comments, markdown files, conversational responses)
must use proper `$...$` LaTeX notation — never raw Unicode math characters.
- `Φ_c` → `$\Phi_c$`, `Ω_Z` → `$\Omega_Z$`, `Γ_seq` → `$\Gamma_\text{seq}$`
- `P_pm_sym` → `$P_{\pm}^{\text{sym}}$` (not `P_\text{pm\_sym}`)
- `O_∞`, `O_1`, `O_2` → `$O_\infty$`, `$O_1$`, `$O_2$`
- `→` in math → `$\to$`, `ℏ` → `$\hbar$`, `ℓ` → `$\ell$`
- Display equations use `$$...$$` blocks
- Synthon tuples use `$\langle D;\ T;\ \ldots \rangle$`

## Git
Do not run any git commands. The user manages all commits.

## SynthOmnicon grammar — 12-primitive tuple
`$\langle D;\ T;\ R;\ P;\ F;\ K;\ G;\ \Gamma;\ \Phi;\ H;\ S;\ \Omega \rangle$`

| Primitive | Name | Values (low → high) |
|-----------|------|---------------------|
| D | Dimensionality | D_wedge, D_triangle, D_infty, D_holo |
| T | Topology | T_network, T_in, T_bowtie, T_box, T_holo |
| R | Relational mode | R_super, R_cat, R_dagger, R_lr |
| P | Parity/symmetry | P_asym, P_psi, P_pm, P_sym, P_pm_sym |
| F | Fidelity | F_ell, F_eth, F_hbar |
| K | Kinetic character | K_fast, K_mod, K_slow, K_trap |
| G | Scope/granularity | G_beth, G_gimel, G_aleph |
| Γ | Interaction grammar | G_and, G_or, G_seq, G_broad |
| Φ | Criticality | Phi_sub, Phi_c, Phi_c_complex, Phi_EP, Phi_super |
| H | Chirality/temporal depth | H0, H1, H2, H_inf |
| S | Stoichiometry | one_one, n_n, n_m |
| Ω | Topological protection | Omega_0, Omega_Z2, Omega_Z |

**$P_{\pm}^{\text{sym}}$** is the highest P ordinal (5). Assign only when $Z_2$ symmetry at $\Phi_c$ is provably exact — the Frobenius special condition ($\mu \circ \delta = \text{id}$).

## Key structural facts
- **$\Phi_c$ is absorbing under meet**: $\text{meet}(\Phi_c, x) = \Phi_c$ for all $x$. It is the necessary condition for self-modeling.
- **Ouroboricity tiers** (R1–R5, priority order):
  - R1: $\Phi_c$ + $P_{\pm}^{\text{sym}}$ → $O_\infty$ (special Frobenius)
  - R2: $\Phi \in \{\Phi_\text{sub}, \Phi_\text{super}, \Phi_\text{EP}\}$ → $O_0$
  - R3: $\Phi_c$ + $\Omega_0$ → $O_1$
  - R4: $\Phi_c$ + $\Omega \neq \Omega_0$ + $D \in \{D_\wedge, D_\text{holo}, D_\triangle\}$ → $O_2$
  - R5: $\Phi_c$ + $\Omega \neq \Omega_0$ + $D_\infty$ → $O_2^\dagger$
  - $O_\infty$ is absorbed under tensor by $\Phi_\text{EP}$ systems ($\Phi_\text{EP}$ ordinal 2.67 > $\Phi_c$ = 2.00)
- **Ouroboricity scalar** $\mathcal{O}(\mathbf{x}) = [\Phi=\Phi_c] \cdot (1 + [\Omega \neq \Omega_0] + [H \geq H_1] + [G = G_\aleph])$ — does NOT include P; cannot detect $O_\infty$
- **Two senses of $O_\infty$**: (a) §XXIV ontological inexhaustibility ($H_\infty$, YHWH); (b) Frobenius $O_\infty$ ($P_{\pm}^{\text{sym}}$, finite algebraic). Incompatible classes.

## Consciousness score — corrected formula
Current formula has wrong structure. Derived weights from critical manifold (variance method):

$$C(\mathbf{x}) = [\Phi = \Phi_c] \cdot [K \neq K_\text{trap}] \cdot (0.158\,\tilde{K} + 0.273\,\tilde{G} + 0.292\,\tilde{T} + 0.276\,\tilde{\Omega})$$

where $\tilde{X}$ = normalized ordinal. Two independent gates (neither subsumes the other):
- Gate 1 $[\Phi = \Phi_c]$: state-space condition — topology admits self-modeling loop
- Gate 2 $[K \neq K_\text{trap}]$: flow condition — dynamics can actualize the loop; $T$/$G$/$\Omega$ are structural and cannot substitute

BH (stellar): $C = 0$ (Gate 2 fails). White dwarf: $C = 0$ (Gate 1 fails). Magnetar: $C = 0.677$ (highest in stellar catalog).
**Derivation merged into SYNTHONICON_DIAPHORICS.md §VIII (v2, 2026-03-30).** Other documents citing $C = 0.875$ use v1 scores and are pending update.

## Key files
- `syncon_catalog.json` — 312+ encoded systems (source of truth for JSON pipeline)
- `syncon_inquiry.py` — agent loop with full tool suite (encode, distance, meet/join/tensor, ouroborics, etc.)
- `synthomnicon/cli.py` — CLI (`syncon` command); `syncon ouroborics [name]` for Frobenius tier
- `space_search/primitives.py` — canonical ordinals and distance functions (v0.4.26, 12-primitive)
- `SYNTHONICON_ONTICS.md` — ontological theorems (v0.4.73+)
- `SYNTHONICON_DIAPHORICS.md` — empirical predictions P-1→P-174+ (v0.4.74+)
- `PRIMITIVE_THEOREMS.md` — formal theorems §1–§23 including Frobenius §23
- `PRIMITIVE_PREDICTIONS.md` — prediction registry

## Monadic growth principle
Improve by lifting, not replacing. Keep origin metadata visible as labeled references.
Mirrors the framework's own recursive self-encoding principle.
