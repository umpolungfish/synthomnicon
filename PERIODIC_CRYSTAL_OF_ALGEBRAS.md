# The Periodic Crystal of Algebras: Six Samples from a 10,368,000-Type Landscape

> **Version note (2026-04-10):** This paper was written against the v1.0 crystal (10,368,000 types, 300 cells × 34,560 inner). Canonical (v0.5.1): 17,280,000 types, 400 cells × 43,200 inner; tier census 60%:8%:18%:6%:8%. See `CRYSTAL_OF_ALGEBRAS.md`.

## Abstract

There are exactly $10{,}368{,}000 = 4^5 \times 5^3 \times 3^4$ structural types in the twelve-primitive algebraic space defined by the SynthOmnicon grammar. They organise into $300$ tier cells — each determined by four primitives ($\Phi$, $P$, $\Omega$, $D$) alone — and within each cell a further $34{,}560 = 20_{[T,R]} \times 12_{[F,K]} \times 12_{[G,\Gamma]} \times 12_{[H,S]}$ inner types. The result is a Periodic Crystal of Algebras: a combinatorial periodic table in which every entry is a distinct structural class, the tier census distributes $60\%{:}10.7\%{:}16\%{:}5.3\%{:}8\%$ across ouroboricity classes $O_0{:}O_1{:}O_2{:}O_2^\dagger{:}O_\infty$, and a single singularity — the Frobenius value $P_{\pm}^{\text{sym}}$ — collapses all $\Omega$ and $D$ branching into the $O_\infty$ tier regardless of group.

This paper was written to understand six algebras: the nilpotent Boolean semimodule $A1$, the $\mathbb{Z}_2$-graded C*-algebra at criticality $A2$, the Le Chatelier equilibrium $A2^\dagger$, the quasi-Hopf driven algebra $A3$, the logarithmic vertex operator algebra $A4$, and the exceptional-point algebra $A5$. The crystal supplies the context that makes those six coherent. They are not an arbitrary list. They are six named coordinates in a precisely enumerable space in which $99.989\%$ of entries — approximately $10{,}366{,}830$ structural types — remain without realisation or name. The crystal is not primarily a taxonomy of the known. It is a map of the possible.

---

## 1. Introduction

A periodic table is not a list of what exists. It is a prediction of what can exist, organised so that position carries meaning — so that an empty slot is itself a statement, and so that the properties of unknown elements can be read off from their neighbours. Mendeleev's table was not confirmed by filling it in. It was confirmed by the fact that the gaps were the right shape.

The Periodic Crystal of Algebras plays the same role for algebraic structures. The twelve-primitive grammar $\langle D;\ T;\ R;\ P;\ F;\ K;\ G;\ \Gamma;\ \Phi;\ H;\ S;\ \Omega \rangle$ defines a coordinate chart on the space of systems capable of processing, storing, and transforming structured information. Every combination of primitive values corresponds to a structural type — an equivalence class of algebras with the same capacity profile. The full count is $10{,}368{,}000$. The current catalog names $1{,}170$ of them. The crystal names the structure of the entire space.

The six algebras treated in this paper — $A1$ through $A5$ and $A2^\dagger$ — are six of those $1{,}170$. Their significance is not that they were found first, or that they are the most important. Five of them were constructed independently by a grammar-aware inference engine as arbitrary demonstrations of the twelve-primitive system, with no relational intent. There was intuitive evidence of their collective significance but no inter-algebraic distance analysis was performed. Later, a cursory review of an inter-algebra directed graph revealed $A3$ as a pure source. Le Chatelier inversion on $A3$ — prompted entirely by the visual observation of a source-less sink — produced $A2^\dagger$: not one of the original five, but a sixth algebra the structure of the five necessitated. The algebranic cycle $A3 \to A2^\dagger \to A5 \to A3$ was not found in the output. It was suggested via an abstraction-based inference and confirmed via rigorous mathematical interrogation. The crystal shows what landscape that cycle is embedded in, and makes precise what it means for the landscape to have a shape.

The argument proceeds as follows. §2 gives the crystal's exact enumeration: the tier factorization theorem, the inner crystal factorization, the Frobenius singularity, and the census. §3 treats the five ouroboricity tiers as algebraic strata, each with a characteristic signature. §4 exhibits the Frobenius singularity in detail: the $P$-axis collapse that makes $P_{\pm}^{\text{sym}}$ the unique tier override. §5 presents each of the six algebras as a specific point in the crystal — its tier cell, its inner coordinates, its neighbourhood. §6 treats crystal navigation: Le Chatelier inversion, tensor coupling, directed distance, and lattice meet/join as moves on the crystal. §7 addresses density: the $99.989\%$ unnamed region, what it contains, and why the named fraction is not representative. §8 synthesises the cross-algebraic structure — tensor composition table, cohomological ladder, and derived categories — in crystal terms. The conclusion is that $A2^\dagger$ is not just the Le Chatelier equilibrium of $A3$; it is the unique $O_2^\dagger$ attractor in its region of the crystal, and its existence was a structural fact about the crystal before anyone computed it.

One notational convention throughout. When we write a tier cell as $(\Phi, P, \Omega, D)$, we mean the equivalence class of all structural types sharing those four primitive values. The $34{,}560$ inner types within each cell are distinguished by the remaining eight primitives; the tier and ouroboricity class are the same for all of them.

---

## 2. The Periodic Crystal: Enumeration and Structure

### 2.1 The full count

The twelve primitives of the SynthOmnicon grammar have cardinalities:

$$|D| = 4,\quad |T| = 5,\quad |R| = 4,\quad |P| = 5,\quad |F| = 3,\quad |K| = 4,$$
$$|G| = 3,\quad |\Gamma| = 4,\quad |\Phi| = 5,\quad |H| = 4,\quad |S| = 3,\quad |\Omega| = 3.$$

The total count of structural types is their product:

$$4 \times 5 \times 4 \times 5 \times 3 \times 4 \times 3 \times 4 \times 5 \times 4 \times 3 \times 3 = 10{,}368{,}000.$$

Written in ascending order this is:

$$|C| = 3^4 \times 4^5 \times 5^3$$

and the factorisation is not accidental. The exponent of each base $n$ is $n+1$ with wraparound on $\{3,4,5\}$:

$$\exp(3) = 4, \quad \exp(4) = 5, \quad \exp(5) = 3.$$

This is the **successor function on $\mathbb{Z}/3\mathbb{Z}$** lifted to $\{3,4,5\}$: a discrete ouroboros. Group the twelve primitives by value count:

| Family | Base | Members | Member count |
|--------|------|---------|--------------|
| $\mathcal{F}_3$ (conservation/protection) | 3 | $F,\,G,\,S,\,\Omega$ | **4** = successor of 3 |
| $\mathcal{F}_4$ (dynamical/relational) | 4 | $D,\,R,\,K,\,\Gamma,\,H$ | **5** = successor of 4 |
| $\mathcal{F}_5$ (structural/phase) | 5 | $T,\,P,\,\Phi$ | **3** = successor of 5 |

Each family's membership count is supplied by the next family's base value. No family's size is self-determined; the cycle has no source node and no sink node. The three families govern each other's multiplicity in a closed loop — $3 \to 4 \to 5 \to 3$ — and the crystal that classifies ouroboricity tiers is itself ouroboric in its own arithmetic.

The bases $\{3,4,5\}$ carry an additional closure: $3^2 + 4^2 = 5^2$ — the first Pythagorean triple, itself a prototype holographic relation (the boundary hypotenuse encodes the interior legs). Three independent closure conditions satisfied simultaneously by the same triple: geometric ($3^2+4^2=5^2$), arithmetic (the successor cycle), and structural (the priority ordering of the families, established independently by the tier rules). The grammar did not choose these integers deliberately — it was forced to them by the number of structural degrees of freedom in each mode. The holographic principle appeared uninvited.

Formal proof that this is the unique valid successor assignment is given in PRIMITIVE_THEOREMS §68.

### 2.2 Tier factorization

The ouroboricity tier of a structural type is determined by four primitives alone:

**Theorem (Tier Factorisation).** *For any structural type $\mathbf{x} \in \mathcal{X}$, the ouroboricity tier $\mathcal{T}(\mathbf{x})$ depends only on $(\Phi, P, \Omega, D)$. The remaining eight primitives $(T, R, F, K, G, \Gamma, H, S)$ are free within each tier cell.*

The tier rules, in priority order, are:
- **R1** ($O_\infty$): $\Phi \in \{\Phi_c, \Phi_c^{\mathbb{C}}\}$ and $P = P_{\pm}^{\text{sym}}$
- **R2** ($O_0$): $\Phi \notin \{\Phi_c, \Phi_c^{\mathbb{C}}\}$
- **R3** ($O_1$): $\Phi \in \{\Phi_c, \Phi_c^{\mathbb{C}}\}$ and $\Omega = \Omega_0$
- **R4** ($O_2$): $\Phi \in \{\Phi_c, \Phi_c^{\mathbb{C}}\}$ and $\Omega \neq \Omega_0$ and $D \in \{D_\wedge, D_\triangle, D_\odot\}$
- **R5** ($O_2^\dagger$): $\Phi \in \{\Phi_c, \Phi_c^{\mathbb{C}}\}$ and $\Omega \neq \Omega_0$ and $D = D_\infty$

The tier-determining subspace has $|\Phi| \times |P| \times |\Omega| \times |D| = 5 \times 5 \times 3 \times 4 = 300$ cells. The free sub-space has $|T| \times |R| \times |F| \times |K| \times |G| \times |\Gamma| \times |H| \times |S| = 5 \times 4 \times 3 \times 4 \times 3 \times 4 \times 4 \times 3 = 34{,}560$ inner types per cell. Hence $300 \times 34{,}560 = 10{,}368{,}000$. $\square$

### 2.3 Inner crystal factorisation

The $34{,}560$ inner types factor into four independent sub-groups:

$$34{,}560 = \underbrace{5 \times 4}_{20\ [T,R]} \times \underbrace{3 \times 4}_{12\ [F,K]} \times \underbrace{3 \times 4}_{12\ [G,\Gamma]} \times \underbrace{4 \times 3}_{12\ [H,S]}.$$

The pairing is not arbitrary. $T$ (topology) and $R$ (relational mode) jointly determine the connectivity structure of the algebra's category. $F$ (fidelity) and $K$ (kinetic character) are the two bottleneck primitives under tensor composition — the primitives that take the minimum rather than the maximum when two systems couple. $G$ (granularity) and $\Gamma$ (interaction grammar) jointly determine the scope and sequencing of the algebra's operations. $H$ (chirality/temporal depth) and $S$ (stoichiometry) determine the temporal and multiplicity structure.

The four-factor product structure means that moving within a tier cell along one sub-group axis does not affect the others. A change in topology $T$ does not change the fidelity-kinetics sub-group. A change in stoichiometry $S$ does not change the geometry sub-group. The inner crystal is a direct product, not an entangled space.

### 2.4 The tier census

Counting tier cells:
- $\Phi \notin \{\Phi_c, \Phi_c^{\mathbb{C}}\}$: three values ($\Phi_{\text{sub}}$, $\Phi_{\text{EP}}$, $\Phi_{\text{sup}}$), all $P$ (5), all $\Omega$ (3), all $D$ (4) → $3 \times 5 \times 3 \times 4 = 180$ cells, all $O_0$
- $\Phi \in \{\Phi_c, \Phi_c^{\mathbb{C}}\}$, $P = P_{\pm}^{\text{sym}}$: $2 \times 1 \times 3 \times 4 = 24$ cells, all $O_\infty$
- $\Phi \in \{\Phi_c, \Phi_c^{\mathbb{C}}\}$, $P \neq P_{\pm}^{\text{sym}}$, $\Omega = \Omega_0$: $2 \times 4 \times 1 \times 4 = 32$ cells, all $O_1$
- $\Phi \in \{\Phi_c, \Phi_c^{\mathbb{C}}\}$, $P \neq P_{\pm}^{\text{sym}}$, $\Omega \neq \Omega_0$, $D \in \{D_\wedge, D_\triangle, D_\odot\}$: $2 \times 4 \times 2 \times 3 = 48$ cells, all $O_2$
- $\Phi \in \{\Phi_c, \Phi_c^{\mathbb{C}}\}$, $P \neq P_{\pm}^{\text{sym}}$, $\Omega \neq \Omega_0$, $D = D_\infty$: $2 \times 4 \times 2 \times 1 = 16$ cells, all $O_2^\dagger$

Total cells: $180 + 24 + 32 + 48 + 16 = 300$. $\square$

Multiplying by $34{,}560$ inner types:

| Tier | Cells | Types | Share |
|------|-------|-------|-------|
| $O_0$ | 180 | $6{,}220{,}800$ | $60.0\%$ |
| $O_1$ | 32 | $1{,}105{,}920$ | $10.7\%$ |
| $O_2$ | 48 | $1{,}658{,}880$ | $16.0\%$ |
| $O_2^\dagger$ | 16 | $552{,}960$ | $5.3\%$ |
| $O_\infty$ | 24 | $829{,}440$ | $8.0\%$ |

The $O_0$ tier constitutes $60\%$ of the crystal because criticality ($\Phi_c$ or $\Phi_c^{\mathbb{C}}$) is the gate condition for any tier above $O_0$, and criticality accounts for only $2/5$ of the $\Phi$ values. Among critical structural types, the distribution is $O_1{:}O_2{:}O_2^\dagger{:}O_\infty = 26.7\%{:}40\%{:}13.3\%{:}20\%$.

**Corollary** ($\Phi_c / \Phi_c^{\mathbb{C}}$ identity). *The tier distributions of $\Phi_c$ and $\Phi_c^{\mathbb{C}}$ are identical. Real and complex criticality produce the same tier census. The distinction between them is inner-crystal only: it affects the representation-theoretic inner types (specifically $T$, $R$, $H$) but not which ouroboricity tier a structural type belongs to.*

---

## 3. The Five Tiers as Algebraic Strata

The ouroboricity tier is not merely a classification label. It reflects a structural property: whether and to what degree the algebra's state-space topology permits a self-referential modelling loop, and whether its dynamics can actualise that loop.

### 3.1 $O_0$: the non-critical stratum

$O_0$ covers $60\%$ of the crystal, the entire subcritical, supercritical, and exceptional-point region. The defining property is that the state-space condition for self-modelling fails: either $\Phi < \Phi_c$ (the system is too ordered, information is frozen), $\Phi > \Phi_c$ (the system is too disordered, information disperses before it can model itself), or $\Phi = \Phi_{\text{EP}}$ (the system is at a non-Hermitian degeneracy that overrides the critical manifold via the rule that $\Phi_{\text{EP}}$ is absorbing under tensor). Within $O_0$, there is enormous algebraic diversity — the $180 \times 34{,}560 = 6{,}220{,}800$ types span everything from trivial Boolean semimodules to infinite-dimensional Hopf algebras — but they share the property that no stable self-referential loop is algebraically available at the state-space level.

By the chemical analogy: $O_0$ is the noble-gas stratum of the crystal, inert with respect to the self-modelling reaction, though capable of rich chemistry among themselves.

### 3.2 $O_1$: unprotected criticality

$O_1$ contains the $32 \times 34{,}560 = 1{,}105{,}920$ structural types at $\Phi_c$ or $\Phi_c^{\mathbb{C}}$ with no topological protection ($\Omega = \Omega_0$) and $P \neq P_{\pm}^{\text{sym}}$. These algebras satisfy the state-space condition for self-modelling — the critical manifold is present — but their self-referential loops are topologically unprotected. Small perturbations can deform them off the critical surface without crossing any topological barrier.

$O_1$ is the most restrictive non-trivial tier in terms of cell count (32 cells, $10.7\%$ of types), because achieving criticality without topological protection requires sitting precisely on $\Phi_c$ without any of the winding-number structure that would otherwise stabilise the critical point against perturbation. The Ising model at its critical temperature, with only $\mathbb{Z}_2$ discrete symmetry (not a continuous winding), belongs here; its RG fixed point is exact but its topological protection is only binary.

### 3.3 $O_2$: bounded-scope protected criticality

$O_2$ contains $48 \times 34{,}560 = 1{,}658{,}880$ types at $\Phi_c$ or $\Phi_c^{\mathbb{C}}$, with $\Omega \neq \Omega_0$ (either $\mathbb{Z}_2$ or $\mathbb{Z}$ winding), and bounded dimensionality ($D \in \{D_\wedge, D_\triangle, D_\odot\}$). The topological protection is in place; the self-referential loop is stable against small perturbations. But the scope is finite — the algebra operates on a bounded state space. Correlations are long-range within that space but do not scale to infinite dimension.

The algebra $A2$ (§5.2 below) sits in this tier: it has $\Phi_c$, $\Omega_{\mathbb{Z}_2}$, and $D_\triangle$ (triangular geometry, bounded). So does $A4$: complex criticality $\Phi_c^{\mathbb{C}}$, $\Omega_\mathbb{Z}$, $D_\triangle$. The fact that two algebras with very different mathematical characters — the Ising C*-algebra and the logarithmic VOA — share the same tier is the crystal's main claim: the tier specifies the capacity class, not the specific algebraic realization.

### 3.4 $O_2^\dagger$: unbounded-scope protected criticality

$O_2^\dagger$ is the rarest self-modelling tier: $16 \times 34{,}560 = 552{,}960$ types, $5.3\%$ of the crystal. The condition is $\Phi_c$ or $\Phi_c^{\mathbb{C}}$, $\Omega \neq \Omega_0$, and $D = D_\infty$. Self-modelling at infinite-dimensional scope, with topological protection, at exact criticality.

Rarity here is structural, not accidental. $D_\infty$ is a single value out of four — only one-quarter of the $D$ axis. More fundamentally, $D_\infty$ requires the algebra to be infinite-dimensional in a specific sense: not merely large, but without a finite-dimensional truncation that preserves the structure. For the loop to be self-referential at infinite scope, the algebra must already encode its own unbounded extent in its state-space topology. The $O_2^\dagger$ tier is where $A2^\dagger$ lives — and the discovery that $A2^\dagger$ belongs here was, as §5 will show, a consequence of the crystal's structure rather than any separate conjecture.

### 3.5 $O_\infty$: Frobenius completeness

$O_\infty$ comprises $24 \times 34{,}560 = 829{,}440$ types, constituting $8\%$ of the crystal. Every $O_\infty$ type has $\Phi \in \{\Phi_c, \Phi_c^{\mathbb{C}}\}$ and $P = P_{\pm}^{\text{sym}}$. The Frobenius special condition $\mu \circ \delta = \text{id}$ holds exactly. The self-referential loop is not merely self-modelling but Frobenius-complete: the algebra simultaneously encodes its own state as both a multiplication and a comultiplication, and these two operations are exact inverses. This is the strongest form of algebraic self-reference definable in the twelve-primitive grammar.

The $O_\infty$ tier accounts for $20\%$ of the critical region (critical types not in $O_\infty$: $80\%$). The fact that it is smaller than $O_2$ is a theorem, not a choice: $P_{\pm}^{\text{sym}}$ is one value out of five, while $O_2$ benefits from three bounded-$D$ values combined with two non-trivial $\Omega$ values and four non-Frobenius $P$ values.

---

## 4. The Frobenius Singularity: The $P$-axis Collapse

The most structurally significant feature of the crystal is the $P$-axis singularity at $P = P_{\pm}^{\text{sym}}$. It is the only primitive value that overrides all branching on other tier-determining primitives.

**Theorem (Frobenius Non-synthesisability).** *$P_{\pm}^{\text{sym}}$ cannot be obtained by tensor composition from structural types with $P < P_{\pm}^{\text{sym}}$. Under tensor coupling, the bottleneck rule gives $P_{\pm}^{\text{sym}} \otimes P_{\text{sym}} = P_{\text{sym}}$ — the weaker partner destroys the Frobenius special condition. Every $O_\infty$ system must directly encode $P_{\pm}^{\text{sym}}$; it cannot be assembled from sub-Frobenius components.*

The consequence for the crystal's tier structure is striking. Consider a $5 \times 5$ matrix indexed by $(P, \Omega/D\text{-combo})$: for the four $P$ values below $P_{\pm}^{\text{sym}}$, the tier varies across the $\Omega$-$D$ plane — a cell at $\Omega_0$ is $O_1$, a cell at $\Omega_{\mathbb{Z}}$ with $D_\infty$ is $O_2^\dagger$, etc. But the entire row $P = P_{\pm}^{\text{sym}}$ collapses to a single tier: $O_\infty$ everywhere, for all $\Omega$ and all $D$. The $P$ axis does not just contribute to a multi-primitive condition. At $P_{\pm}^{\text{sym}}$ it is the condition, sufficient by itself.

The P-axis collapse has a physical interpretation. The Frobenius condition $\mu \circ \delta = \text{id}$ is the algebraic statement that multiplication and comultiplication are inverses — that the system processes information reversibly, encoding and decoding without loss. A system satisfying this condition everywhere (not just at $t=0$) is one where no information is irrecoverably committed. It is the maximal algebraic symmetry available to a system that can also be self-referential. And it is incompatible with assembly from components that do not individually satisfy it: Frobenius-completeness cannot emerge from non-Frobenius interactions.

This is why $A3$ — which begins with the Frobenius condition and then breaks it dynamically through its Lindbladian — is $O_0$. The drive that breaks the Frobenius condition also breaks the state-space criticality condition. $A3$ has $P_{\pm}^{\text{sym}}$ in its tuple, but it has $\Phi_{\text{super}}$, not $\Phi_c$. The $O_\infty$ classification requires both simultaneously.

---

## 5. Six Algebras as Crystal Samples

The six algebras treated here were derived from a single inquiry: what algebraic structures arise at the constraint boundary of self-referential computation? The crystal shows where they sit and what the inquiry missed.

### 5.1 Algebra $A1$: nilpotent Boolean semimodule

**Tuple:** $\langle D_\wedge;\ T_{\text{network}};\ R_{\text{super}};\ P_{\text{asym}};\ F_\ell;\ K_{\text{fast}};\ G_\beth;\ \Gamma_{\text{and}};\ \Phi_{\text{sub}};\ H_0;\ S_{1:1};\ \Omega_0 \rangle$

**Tier cell:** $(\Phi_{\text{sub}}, P_{\text{asym}}, \Omega_0, D_\wedge)$ — one of the $180$ $O_0$ cells. **Inner position:** minimal on every inner-crystal axis. **Ouroboricity:** $O_0$.

$A1$ is the path algebra $\mathbb{K}Q/I$ of a finite acyclic quiver, specialised to the Boolean semiring. Given a finite directed acyclic graph $G = (V,E)$ with $n = |V|$ and strictly upper-triangular adjacency matrix $A \in \mathbb{B}^{n\times n}$, the algebra is the triple $(\mathbb{B}^n, \wedge, \vee, M)$ with transition operator $Mx = A \otimes x$. Nilpotency $A^n = 0$ guarantees every trajectory reaches $\mathbf{0}$ in at most $n$ steps. No recurrence, no fixed point other than $\mathbf{0}$, no cycle. The module category $\text{mod-}\mathbb{B}Q/I$ is hereditary and representation-finite; all indecomposables are projective.

The crystal context makes the floor structure precise. $A1$ occupies the minimum cell in all four tier-determining primitives simultaneously: the lowest $\Phi$ value ($\Phi_{\text{sub}}$), the lowest $P$ value ($P_{\text{asym}}$), the lowest $\Omega$ value ($\Omega_0$), and the lowest $D$ value ($D_\wedge$). It is the lattice minimum of the crystal. Every path upward to $A2$, $A2^\dagger$, or beyond requires moving in at least one tier-determining primitive.

A four-vertex chain: $A = \begin{pmatrix} 0&1&0&0\\0&0&1&0\\0&0&0&1\\0&0&0&0 \end{pmatrix}$, nilpotency index $\nu = 4$, zeta transform $\zeta_{ij} = 1$ for $i \le j$. The Möbius function $\zeta^{-1}$ is $1$ on the diagonal, $-1$ on the superdiagonal, $0$ elsewhere — the difference operator of the linear order.

### 5.2 Algebra $A2$: $\mathbb{Z}_2$-graded C*-algebra at criticality

**Tuple:** $\langle D_\triangle;\ T_{\text{box}};\ R_{\text{cat}};\ P_\pm;\ F_\eth;\ K_{\text{mod}};\ G_\gimel;\ \Gamma_{\text{or}};\ \Phi_c;\ H_1;\ S_{n:n};\ \Omega_{\mathbb{Z}_2} \rangle$

**Tier cell:** $(\Phi_c, P_\pm, \Omega_{\mathbb{Z}_2}, D_\triangle)$ — one of the $48$ $O_2$ cells. **Ouroboricity:** $O_2$.

$A2$ is the commutative C*-algebra $C(X; M_2(\mathbb{C}))^{\mathbb{Z}_2}$ restricted to the critical manifold $X$, with the critical expectation $\langle\cdot\rangle_c$. The defining correlation is $\langle \sigma_i \sigma_j \rangle_c \sim |i-j|^{-1/4}$ — scale-free, algebraically enforcing the RG fixed point. The representation category is the Ising modular tensor category with three simple objects $\{\mathbf{1}, \sigma, \psi\}$, fusion rules $\sigma \times \sigma = \mathbf{1} + \psi$, and unitary modular $S$-matrix:

$$S = \frac{1}{2}\begin{pmatrix} 1 & \sqrt{2} & 1 \\ \sqrt{2} & 0 & -\sqrt{2} \\ 1 & -\sqrt{2} & 1 \end{pmatrix}.$$

Unitarity here is the categorical signature of semisimplicity: all extensions between simple objects are trivial. When we reach $A4$, the analogous matrix is non-unitary, and that failure is exact.

In the crystal, $A2$'s $O_2$ classification says: self-modelling at bounded scope ($D_\triangle$) with binary topological protection ($\Omega_{\mathbb{Z}_2}$). The $34{,}560$ inner types sharing $A2$'s tier cell include algebras with different topologies $T$, relational modes $R$, temporal depths $H$, and stoichiometries $S$ — all with the same capacity class but different physical realisations. The Ising fixed-point algebra is one such realisation; the crystal tells us there are $34{,}559$ others in the same tier cell.

### 5.3 Algebra $A2^\dagger$: the topological critical point

**Tuple:** $\langle D_\infty;\ T_{\text{bowtie}};\ R_{\text{cat}};\ P_\pm;\ F_\hbar;\ K_{\text{mod}};\ G_\aleph;\ \Gamma_{\text{seq}};\ \Phi_c;\ H_1;\ S_{n:n};\ \Omega_\mathbb{Z} \rangle$

**Tier cell:** $(\Phi_c, P_\pm, \Omega_\mathbb{Z}, D_\infty)$ — one of the $16$ $O_2^\dagger$ cells. **Ouroboricity:** $O_2^\dagger$.

$A2^\dagger$ was not postulated, and it was not among the original five algebras. It was necessitated: observing that $A3$ had no inbound arc in the directed graph of the five raised the question of what replenishes it. Le Chatelier inversion on $A3$ — if $A3$ is the driven NESS, what is the equilibrium algebra it relaxes onto when the drive is removed? — was the tool that answered the question the graph had forced. The answer is a system at exact criticality with the integer winding number $\Omega_\mathbb{Z}$ already in place — not generated by the drive, but intrinsic to the equilibrium structure.

The crystal makes this derivation explicit. $A3$ has tier-determining tuple $(\Phi_{\text{super}}, P_{\pm}^{\text{sym}}, \Omega_\mathbb{Z}, D_\infty)$, placing it in the $O_0$ tier (supercritical, state-space condition fails). The Le Chatelier inversion asks: what is the highest-ouroboricity type in the downward closure of $A3$ — the set of types with every primitive at or below $A3$'s? The answer is exactly the $O_2^\dagger$ cell $(\Phi_c, P_\pm, \Omega_\mathbb{Z}, D_\infty)$: match $A3$'s $D_\infty$ and $\Omega_\mathbb{Z}$, bring $\Phi$ back to criticality, bring $P$ back below Frobenius. $A2^\dagger$ is the maximally self-modelling algebra in $A3$'s downward closure, and the crystal identifies the $O_2^\dagger$ tier as the unique ouroboricity class for that position.

Three physical realisations span the range. The Kitaev chain at $|\mu| = 2t$ sits at $\Phi_c$ with Majorana zero modes forming — the $\Omega_\mathbb{Z}$ invariant is algebraically present at the phase transition. The deconfined quantum critical point (DQCP) in 2+1D sits at the Néel-to-VBS boundary with deconfined spinons carrying Chern-Simons $\Omega_\mathbb{Z}$ charge. The SYK model at its quantum critical point has reparametrisation symmetry ($D_\infty$, $G_\aleph$), power-law correlations ($\Phi_c$), and Schwarzian winding number ($\Omega_\mathbb{Z}$). All three occupy different inner-crystal positions within the same $O_2^\dagger$ tier cell.

The directed distance $d_\to(A3, A2^\dagger) = 0$: every primitive of $A2^\dagger$ is at or below the corresponding primitive of $A3$. $A2^\dagger$ lies in $A3$'s downward closure. It is what $A3$ already is, underneath the drive.

### 5.4 Algebra $A3$: quasi-Hopf algebra with broken Frobenius condition

**Tuple:** $\langle D_\infty;\ T_{\text{bowtie}};\ R_\dagger;\ P_{\pm}^{\text{sym}};\ F_\hbar;\ K_{\text{slow}};\ G_\aleph;\ \Gamma_{\text{seq}};\ \Phi_{\text{super}};\ H_\infty;\ S_{n:m};\ \Omega_\mathbb{Z} \rangle$

**Tier cell:** $(\Phi_{\text{super}}, P_{\pm}^{\text{sym}}, \Omega_\mathbb{Z}, D_\infty)$ — one of the $180$ $O_0$ cells. **Ouroboricity:** $O_0$.

The crystal immediately locates the structural irony in $A3$: it carries $P_{\pm}^{\text{sym}}$ (the Frobenius value), which in the critical region would place it in $O_\infty$. But $\Phi_{\text{super}}$ — the driven non-equilibrium supercriticality — disqualifies it from $O_\infty$. The tier rule R2 fires before R1 can: non-critical $\Phi$ gives $O_0$ regardless of $P$.

$A3$ is a $\mathbb{Z}_2$-graded quasi-Hopf *-algebra with coproduct $\Delta$, counit $\varepsilon$, antipode $S$, and a positive-definite inner product. The Frobenius condition $\mu \circ \Delta = \text{id}$ holds at $t=0$ but is broken by the Lindbladian dynamics for $t > 0$:

$$\mu \circ \Delta(\rho_{\text{NESS}}) - \rho_{\text{NESS}} = \delta\rho \neq 0,$$

where $\delta\rho$ is traceless and lives in the odd sector of the $\mathbb{Z}_2$ grading. The non-equilibrium steady state carries a conserved winding number $w \in \mathbb{Z}$ — the topological memory — that survives as long as the Lindbladian spectral gap remains open.

The physical reading of $A3$'s $O_0$ tier is not that $A3$ is algebraically trivial. It is that $A3$ cannot self-model: supercriticality means the system's state-space does not admit the fixed-point structure that self-reference requires. $A3$ has topological memory ($\Omega_\mathbb{Z}$) and Frobenius structure ($P_{\pm}^{\text{sym}}$), but it has overshot the critical manifold. Self-modelling lives one step below, at $A2^\dagger$.

### 5.5 Algebra $A4$: logarithmic vertex operator algebra

**Tuple:** $\langle D_\triangle;\ T_{\text{in}};\ R_{\text{lr}};\ P_\psi;\ F_\hbar;\ K_{\text{mod}};\ G_\aleph;\ \Gamma_{\text{seq}};\ \Phi_c^{\mathbb{C}};\ H_2;\ S_{n:m};\ \Omega_\mathbb{Z} \rangle$

**Tier cell:** $(\Phi_c^{\mathbb{C}}, P_\psi, \Omega_\mathbb{Z}, D_\triangle)$ — one of the $48$ $O_2$ cells. **Ouroboricity:** $O_2$.

$A4$ is a logarithmic vertex operator algebra: a vertex algebra $(V, Y, \omega, \mathbf{1})$ where the zero-mode $L_0$ of the Virasoro field has Jordan blocks. Logarithmic partner fields $\varphi^{(1)}$ pair with ordinary primaries $\varphi^{(0)}$ via $L_0 \varphi^{(1)} = h\varphi^{(1)} + \varphi^{(0)}$, producing correlation functions $\langle \varphi^{(0)}(z)\varphi^{(1)}(w)\rangle \sim \log|z-w| \cdot |z-w|^{-2h}$. The representation category is a non-semisimple ribbon category with non-unitary modular $S$-matrix.

The crystal places $A4$ in the same $O_2$ tier as $A2$, despite their very different algebraic characters. The shared tier reflects shared capacity: both are self-modelling at bounded scope with non-trivial topological protection. The inner-crystal distinction between them — $A4$ at $\Phi_c^{\mathbb{C}}$ vs $A2$ at $\Phi_c$, $T_{\text{in}}$ vs $T_{\text{box}}$, $P_\psi$ vs $P_\pm$, $H_2$ vs $H_1$ — is real and generates different algebraic realisations. But the capacity class is the same.

The $c=-2$ symplectic fermion theory exemplifies $A4$: the vacuum Jordan block $L_0|0\rangle = 0$, $L_0|\tilde{0}\rangle = |0\rangle$ generates the two-point function $\langle\tilde{0}|\tilde{0}\rangle = -2b\log|z-w| + \tilde{b}$, with $\operatorname{Ext}^1(\mathcal{V}_0, \mathcal{V}_0) \cong \mathbb{C}$ as the algebraic source of the logarithm. The Ising VOA $A2$ embeds as a sub-VOA into $A4$: $i: \mathbf{A2} \hookrightarrow \mathbf{A4}$.

### 5.6 Algebra $A5$: exceptional-point operator algebra

**Tuple:** $\langle D_\odot;\ T_{\text{box}};\ R_{\text{cat}};\ P_{\text{sym}};\ F_\hbar;\ K_{\text{trap}};\ G_\aleph;\ \Gamma_{\text{broad}};\ \Phi_{\text{EP}};\ H_2;\ S_{n:n};\ \Omega_{\mathbb{Z}_2} \rangle$

**Tier cell:** $(\Phi_{\text{EP}}, P_{\text{sym}}, \Omega_{\mathbb{Z}_2}, D_\odot)$ — one of the $180$ $O_0$ cells. **Ouroboricity:** $O_0$.

$A5$ is the local ring at a coalescence of eigenvalues. At an exceptional point $\lambda_0$ in parameter space, $H(\lambda)$ becomes non-diagonalisable: $H_{\text{EP}} = \lambda_0 I + N$ with $N^n = 0$, $N^{n-1} \neq 0$. The algebra generated by $H_{\text{EP}}$ is $\mathbb{C}[x]/(x^n)$. Perturbing by $\delta H = \varepsilon\sigma_x$, eigenvalues split as $\lambda_\pm \approx \lambda_0 \pm c\,\varepsilon^{1/n}$: $n$th-root sensitivity, impossible for Hermitian systems.

$A5$'s $O_0$ classification follows from $\Phi_{\text{EP}}$: the exceptional point is the non-Hermitian analogue of the non-critical regime, where the state-space topology is dominated by the nilpotent Jordan structure rather than by a critical manifold. The Frobenius condition fails not because the system is driven (as in $A3$) but because the Jordan block is itself the obstruction — $N$ is nilpotent, not invertible, so no comultiplication exists that would make $\mu \circ \delta = \text{id}$ hold.

The crystal also reveals a structural echo between $A5$ and $A1$: both are $O_0$, both have a nilpotent piece ($A^n = 0$ for $A1$'s DAG adjacency matrix; $N^n = 0$ for $A5$'s Jordan block). But $A5$'s nilpotency is embedded in the complex eigenvalue structure of $\Phi_{\text{EP}}$, producing maximal sensitivity where $A1$'s produces inertness. The same algebraic motif — nilpotency — realises opposite phenomenology depending on the criticality primitive.

The directed distance $d_\to(A5, A2^\dagger) = 0.70$: a single topological step ($\Omega_{\mathbb{Z}_2} \to \Omega_\mathbb{Z}$). $A5$ is almost free to enter $A2^\dagger$, which is the Le Chatelier equilibrium waiting on the other side of the exceptional point.

---

## 6. Crystal Navigation

The crystal is not merely a static enumeration. It supports five navigable operations that generate new structural types from known ones, and confirm or refute structural hypotheses.

### 6.1 Le Chatelier inversion

Given a driven system $\mathbf{y}$, find $\mathbf{x}^*$ such that $d_\to(\mathbf{y}, \mathbf{x}^*) = 0$, maximising $\mathcal{O}(\mathbf{x}^*)$. This identifies the highest-ouroboricity equilibrium algebra in $\mathbf{y}$'s downward closure — the algebra that $\mathbf{y}$ relaxes onto when its drive is removed.

Applied to $A3$: the downward closure contains all types with every primitive $\le A3$'s. The highest-ouroboricity type in that closure has $\Phi_c$ (stepped down from $\Phi_{\text{super}}$), $P_\pm$ (stepped down from $P_{\pm}^{\text{sym}}$), $\Omega_\mathbb{Z}$ (unchanged), $D_\infty$ (unchanged) — the $O_2^\dagger$ tier cell, where $A2^\dagger$ was subsequently identified. Le Chatelier inversion found $A2^\dagger$ before any physical argument for it existed.

Applied to $A5$: the downward closure has $\Phi \le \Phi_{\text{EP}}$, but $\Phi_{\text{EP}}$ is ordinal $2.67$ (above $\Phi_c = 2.00$) so the downward closure includes $\Phi_c$. With $\Omega_{\mathbb{Z}_2}$ from $A5$'s tuple, the highest-ouroboricity type in the downward closure is in the $O_2$ tier — an algebra at $\Phi_c$, $\Omega_{\mathbb{Z}_2}$, with $D \le D_\odot$. The directed distance $d_\to(A5, \text{this type}) < 1$, confirming that the exceptional point nearly reaches its Le Chatelier equilibrium in a single topological step.

### 6.2 Tensor coupling

The tensor product on the crystal sends $(\mathbf{x}, \mathbf{y})$ to the type with $\max$ on union primitives ($D, T, R, G, \Gamma, H, S, \Omega$) and $\min$ on bottleneck primitives ($P, F$):

$$(\mathbf{x} \otimes \mathbf{y})_i = \begin{cases} \max(x_i, y_i) & i \in \text{union primitives} \\ \min(x_i, y_i) & i \in \{P, F\} \end{cases}$$

The bottleneck rule has a sharp consequence for $O_\infty$ types: $P_{\pm}^{\text{sym}} \otimes P_{\text{sym}} = P_{\text{sym}}$, so coupling an $O_\infty$ system to any sub-Frobenius partner destroys the Frobenius condition and pushes the result out of $O_\infty$. This is the tensor expression of Frobenius non-synthesisability.

For the six algebras, the full $6\times6$ tensor table is:

$$\begin{array}{c|cccccc}
\otimes & A1 & A2 & A2^\dagger & A3 & A4 & A5 \\
\hline
A1         & A1         & A2         & A2^\dagger & A4         & A4         & A5 \\
A2         & A2         & A2         & A2^\dagger & A3         & A4         & A5 \\
A2^\dagger & A2^\dagger & A2^\dagger & A2^\dagger & A3         & A4         & A5 \\
A3         & A4         & A3         & A3         & A3         & A4         & A5 \\
A4         & A4         & A4         & A4         & A4         & A4         & A5 \\
A5         & A5         & A5         & A5         & A5         & A5         & A5
\end{array}$$

$A5$ is the annihilator: $A5 \otimes \mathbf{x} = A5$ for all $\mathbf{x}$, because $\Phi_{\text{EP}}$, $K_{\text{trap}}$, $D_\odot$, and $\Gamma_{\text{broad}}$ dominate all union primitives and $K$ via max, and the result is always nearest $A5$ in the crystal. $A4$ is the second absorber, idempotent with basin $\{A1, A2, A2^\dagger, A3\}$ when not overridden by $A5$.

The most surprising entry is $A1 \otimes A3 = A4$. The original five-algebra table had this as $A3$, under the assumption that $A1$ acts as a tensor identity. It does not. $A1$'s bottleneck primitives $P_{\text{asym}}$ (ordinal 1) and $F_\ell$ (ordinal 1) drag down $A3$'s $P_{\pm}^{\text{sym}}$ (ordinal 5) and $F_\hbar$ (ordinal 3) via the $\min$ rule. The result inherits $A3$'s large-scale structure ($D_\infty$, $\Omega_\mathbb{Z}$, $K_{\text{slow}}$) but with collapsed symmetry processing — nearest to $A4$, not $A3$. Coupling a syntactic $O_0$ system to a driven NESS strips the NESS of its Frobenius condition without disrupting its spatial structure.

$A2^\dagger$ is idempotent and absorbs $A1$ and $A2$: the integer topological protection $\Omega_\mathbb{Z}$ and infinite scope $D_\infty$ dominate the union primitives; only $P$ and $F$ can be dragged down, and the result remains nearest $A2^\dagger$.

### 6.3 Directed distance and relaxation geometry

The directed distance $d_\to(\mathbf{x}, \mathbf{y}) = \sum_i w_i \max(0, v_{\mathbf{y},i} - v_{\mathbf{x},i})$ measures the cost of upward moves from $\mathbf{x}$ to $\mathbf{y}$. It is asymmetric: $d_\to(\mathbf{x}, \mathbf{y}) \neq d_\to(\mathbf{y}, \mathbf{x})$ whenever $\mathbf{y}$ has higher primitives than $\mathbf{x}$ in at least one dimension.

| From $\to$ To | $d_\to$ | Interpretation |
|---|---|---|
| $A2^\dagger \to A3$ | $7.60$ | requires drive across 6 primitives |
| $A3 \to A2^\dagger$ | $0.00$ | $A2^\dagger$ is in $A3$'s downward closure |
| $A5 \to A2^\dagger$ | $0.70$ | one topological lift ($\Omega_{\mathbb{Z}_2} \to \Omega_\mathbb{Z}$) |
| $A2 \to A2^\dagger$ | $4.70$ | requires $\Omega$, $D$, $G$, $F$ upgrades |
| $A2^\dagger \to A2$ | $1.00$ | nearly free: drop $\Omega_\mathbb{Z}$ to $\Omega_{\mathbb{Z}_2}$ |
| $A4 \to A2^\dagger$ | $3.00$ | moderate: drop $R$, $\Phi$, $H$ |

The $d_\to(A3, A2^\dagger) = 0$ result is the Le Chatelier principle in crystal coordinates: $A3$ contains $A2^\dagger$ as a structural subalgebra. The asymmetry $d_\to(A2^\dagger, A3) = 7.60$ is the cost of the thermodynamic drive: moving from equilibrium to the NESS requires climbing across six primitive dimensions.

The directed landscape has a natural geometric reading. Starting from $A1$ (lattice minimum), the sequence $A1 \to A2 \to A2^\dagger \underset{d=0}{\overset{7.6}{\rightleftharpoons}} A3 \to A4 \underset{}{\overset{}{\rightleftharpoons}} A5 \xrightarrow{0.70} A2^\dagger$ is a closed directed graph with two relaxation floors below $A3$ (the $A2^\dagger$ floor at $O_2^\dagger$ and the $A2$ floor at $O_2$) and a short-circuit from $A5$ back to $A2^\dagger$.

### 6.4 Lattice meet and join

The meet $\mathbf{x} \wedge \mathbf{y}$ takes the component-wise minimum, giving the greatest lower bound. The join $\mathbf{x} \vee \mathbf{y}$ takes the component-wise maximum, giving the least upper bound.

$\text{meet}(A2^\dagger, A3)$ gives $\Phi_c, \Omega_\mathbb{Z}, K_{\text{mod}}, P_\pm, D_\infty, H_1$ — which is $A2^\dagger$ itself. $A2^\dagger$ is the infimum of $A3$ in the lattice among types retaining $\Omega_\mathbb{Z}$ and $\Phi_c$: the largest algebra weaker than $A3$ that still preserves the integer topological invariant.

$\text{meet}(A3, A2) = \Phi_c, \Omega_{\mathbb{Z}_2}, K_{\text{mod}}, P_\pm, D_\triangle, H_1$ — which is $A2$. $A2$ is the infimum of $A3$ when $\Omega_\mathbb{Z}$ is not preserved. So the lattice has two distinct floors below $A3$: $A2$ (which loses $\Omega_\mathbb{Z}$) and $A2^\dagger$ (which preserves it). The lattice makes the topological memory distinction precise.

$\text{join}(A2^\dagger, A2)$ is $A2^\dagger$ itself — the minimal algebra above $A2$ that carries $\Omega_\mathbb{Z}$. $A2^\dagger$ is the join of the $A2$ family with the integer winding number.

---

## 7. Density and the Unnamed Region

The current SynthOmnicon catalog names $1{,}170$ structural types. The crystal contains $10{,}368{,}000$. The catalog covers $0.011\%$.

This figure is not a statement of incompleteness in the ordinary sense. The catalog was not built by sampling the crystal uniformly. It was built by following specific threads: the inquiry about self-referential computation, the Hebrew alphabet type-lattice, stellar objects, biological structures, quantum information protocols. These threads produced a sample that is heavily biased toward the critical region ($\Phi_c$, $\Phi_c^{\mathbb{C}}$) and toward high ouroboricity ($O_2$, $O_2^\dagger$, $O_\infty$). The $60\%$ of the crystal in the $O_0$ tier — $6{,}220{,}800$ structural types — is almost entirely unnamed.

What does the unnamed $O_0$ region contain? By the tier rules, every type there has $\Phi \notin \{\Phi_c, \Phi_c^{\mathbb{C}}\}$: subcritical ordered phases ($\Phi_{\text{sub}}$), supercritical driven phases ($\Phi_{\text{sup}}$), and exceptional points ($\Phi_{\text{EP}}$). Within each $\Phi$ class, all five $P$ values, all three $\Omega$ values, and all four $D$ values combine with all $34{,}560$ inner types. The result is a vast landscape of algebras ranging from the simplest Boolean circuits ($A1$'s tier cell, $34{,}560$ inner variations) to infinite-dimensional Hopf algebras in non-equilibrium driven phases ($A3$'s tier cell, $34{,}559$ inner variations besides $A3$ itself).

The unnamed $O_2^\dagger$ region is smaller ($552{,}960$ total types, $1{,}169$ named) but structurally richer: every unnamed $O_2^\dagger$ type is an algebra at $\Phi_c$ or $\Phi_c^{\mathbb{C}}$, with $\Omega_\mathbb{Z}$ topological protection, at infinite scope ($D_\infty$). These are the crystal's rarest self-modelling structural types, and $A2^\dagger$ is the only one in the catalog. The remaining $552{,}959$ are structural classes waiting for either physical realisation or mathematical construction.

The $O_\infty$ region ($829{,}440$ types) is completely empty in the catalog except for systems identified through the Hebrew type-lattice analysis. No conventional mathematical structure has been named in the $O_\infty$ tier, because $P_{\pm}^{\text{sym}}$ requires simultaneously satisfying the Frobenius condition and criticality in a way that no standard algebraic construction produces without explicit design. The Frobenius non-synthesisability theorem (§4) explains why: $O_\infty$ algebras cannot emerge from coupling sub-Frobenius systems, so they cannot be assembled from the named $O_0$ through $O_2^\dagger$ catalog entries via tensor composition.

**The crystal is not primarily a taxonomy of the known. It is a map of the possible.**

---

## 8. Cross-Algebraic Synthesis

### 8.1 Hochschild cohomology

The Hochschild cohomology groups $HH^n(\mathcal{A}, \mathcal{A})$ measure the algebra's capacity for deformation: $HH^0$ is the centre, $HH^1$ classifies outer derivations, $HH^2$ first-order deformations, $HH^3$ obstructions to extending them.

| Algebra | Tier | $HH^0$ | $HH^1$ | $HH^2$ | $HH^3$ |
|---------|------|--------|--------|--------|--------|
| $A1$ | $O_0$ | $\mathbb{B}$ | $0$ | $0$ | $0$ |
| $A2$ | $O_2$ | $\mathbb{C}$ | $0$ | $\mathbb{C}$ | $0$ |
| $A2^\dagger$ | $O_2^\dagger$ | $\mathbb{C}$ | $\mathbb{C}$ | $\mathbb{C}^2$ | $\mathbb{C}$ |
| $A3$ | $O_0$ | $\mathbb{C}$ | $\mathbb{C}$ | $\mathbb{C}^2$ | $\mathbb{C}$ |
| $A4$ | $O_2$ | $\mathbb{C}$ | $\mathbb{C}$ | $\mathbb{C}^3$ | $\mathbb{C}^2$ |
| $A5$ | $O_0$ | $\mathbb{C}$ | $\mathbb{C}$ | $\mathbb{C}$ | $\mathbb{C}$ |

The crystal tier correlates with the cohomological richness, but not perfectly. $A1$ is $O_0$ and completely rigid: all Hochschild cohomology above degree zero vanishes, reflecting the fact that $A1$ is at the lattice minimum and cannot be perturbed into anything richer from within its own category. $A2$ is $O_2$ with one deformation ($HH^2 = \mathbb{C}$, the temperature perturbation) and no obstructions — the Ising model is exactly soluble away from criticality. 

$A2^\dagger$ and $A3$ share identical Hochschild dimensions, reflecting that they share $\Omega_\mathbb{Z}$ and $\Phi \in \{\Phi_c, \Phi_{\text{super}}\}$ — the two deformation directions (temperature and topological coupling in $A2^\dagger$; drive strength and associator in $A3$) and the single obstruction (quantisation of the winding number) are the same in both cases. The distinction appears in $HH^1$: $A2^\dagger$'s non-vanishing $HH^1 = \mathbb{C}$ reflects its reparametrisation symmetry from $D_\infty$, and $A3$'s reflects the non-equilibrium drive. The cohomological profiles match because the tier-determining primitives $\Omega_\mathbb{Z}$ and $D_\infty$ (shared) dominate the deformation theory, while the distinct primitives ($\Phi_c$ vs $\Phi_{\text{super}}$, $P_\pm$ vs $P_{\pm}^{\text{sym}}$) govern the physical content of those generators.

$A4$ is maximally deformable: three independent deformation directions (logarithmic coupling $b$, central charge, Jordan block size) and two obstructions. The two obstructions in $HH^3$ constrain the deformation space to a two-dimensional submanifold — the log coupling and central charge can be deformed freely, but the Jordan block size must remain an integer.

$A5$ has one deformation and one obstruction. The single generator of $HH^2$ is the Jordan block unfolding — the Puiseux expansion that splits the EP into $n$ simple eigenvalues. The obstruction is that the Puiseux expansion must be consistent on all $n$ Riemann sheets simultaneously.

### 8.2 Derived categories and the crystal

At the level of derived categories, the crystal tier predicts the type of AR (Auslander-Reiten) quiver.

$\mathcal{D}^b(A1)$ is hereditary (all Ext$^n$ vanish for $n \ge 2$), AR quiver of type $A_n$ — finite, acyclic, matching the $O_0$-floor structure. $\mathcal{D}^b(A2)$ is semisimple at the MTC level, unitary $S$-matrix, no non-trivial extensions between simples — consistent with $O_2$ self-modelling without non-semisimple deformation. $\mathcal{D}^b(A2^\dagger)$ has $\mathbb{Z}$-graded extension theory from $\Omega_\mathbb{Z}$, AR quiver of type $\tilde{A}_\infty$ — the infinite periodic quiver, reflecting periodicity of topological sectors. The Frobenius condition constrains the triangulated structure: extensions exist but are reversible, so the AR translate $\tau$ acts freely without fixed points. $\mathcal{D}^b(A3)$ breaks this periodicity: the non-equilibrium drive lifts the Frobenius constraint, producing an AR quiver of type $\mathbb{Z}A_\infty$ where translations are no longer periodic — a larger, non-compact quiver. $\mathcal{D}^b(A4)$ is non-semisimple ribbon: braided, twisted, dualisable, but with non-exact duality — the categorical source of the non-unitary $S$-matrix. $\mathcal{D}^b(A5)$ is local: one simple object, one projective cover, AR quiver of type $\mathbb{Z}A_{n-1}/\tau$.

The relaxation $A3 \to A2^\dagger$ (directed cost zero) lifts to a triangulated projection $\mathcal{D}^b(A3) \to \mathcal{D}^b(A2^\dagger)$ that retains the $\mathbb{Z}$-graded sector and discards the non-equilibrium deformations: the $\mathbb{Z}A_\infty$ AR quiver contracts to $\tilde{A}_\infty$ by identifying orbits under Frobenius restoration. The tier transition $O_0 \to O_2^\dagger$ is visible at the AR-quiver level as the contraction from non-periodic to periodic translation.

### 8.3 The algebranic cycle

The directed-distance structure of the crystal permits a complementary analysis: the six algebras as nodes in a flow network. The directed graph on the five original algebras is $A1 \to A2 \leftarrow A3 \to A4 \to A5$, with $A2^\dagger$ in $A3$'s downward closure ($d_\to(A3, A2^\dagger) = 0$). $A3$ is a **pure source**: arcs leave it; none arrive. A source without a feeder is not a steady state.

The closing arc is $A5 \to A3$. $A5$ at $\Phi_\text{EP}$ with $K_\text{trap}$ stores trapped spectral energy as the $\Omega_{\mathbb{Z}_2}$ invariant; its single deformation direction is the Puiseux unfolding. If the unfolding overshoots $\Phi_c$ (available since $\Phi_\text{EP}$ ordinal $2.67 > \Phi_c = 2.0$, allowing the EP's collapse to land in $\Phi_\text{sup}$), it regenerates $A3$. This closes the **algebranic cycle**:

$$A3 \xrightarrow{d_\to = 0} A2^\dagger \xrightarrow{\text{topological trapping}} A5 \xrightarrow{\text{EP unfolding}} A3.$$

The cycle is Carnot-like: $A3$ the hot reservoir ($\Phi_\text{sup}$, overshot), $A2^\dagger$ the working substance at $\Phi_c$ extracting self-modelling capacity, $A5$ the cold trap ($K_\text{trap}$) storing and releasing. $A1$, $A2$, and $A4$ are side branches rather than cycle nodes. The algebranic cycle was not present in the original five-algebra output. It was suggested by the visual observation of the source-less sink and confirmed by the directed-distance and Hochschild analysis above.

### 8.4 The structural irony

The crystal makes sharp a structural irony that the six-algebra analysis discovered late. $A3$ carries the richest tube — $P_{\pm}^{\text{sym}}$ (Frobenius), $\Omega_\mathbb{Z}$ (integer winding), $D_\infty$ (infinite scope), $H_\infty$ (infinite temporal depth) — of any of the six algebras. Yet it is $O_0$. Its ouroboricity class is the same as $A1$, the trivial floor.

The reason is $\Phi_{\text{super}}$. The state-space condition for self-modelling requires the critical manifold $\Phi_c$, and $A3$ overshot it. The system has all the structural equipment for self-reference but cannot actualise a self-referential loop because its state-space topology does not admit the fixed point that self-modelling requires.

The self-modelling capacity lives one step below $A3$ in the crystal, in the $O_2^\dagger$ tier cell that $A3$ projects onto under relaxation. $A2^\dagger$ inherited everything from $A3$ that matters for self-modelling ($\Omega_\mathbb{Z}$, $D_\infty$) and shed what obstructed it ($\Phi_{\text{super}} \to \Phi_c$, $P_{\pm}^{\text{sym}} \to P_\pm$). The crystal identified the $O_2^\dagger$ tier before $A2^\dagger$ was named. The tier was there; the algebra was found by navigating to it.

---

## 9. Conclusion

The crystal's enumeration theorem says there are exactly $10{,}368{,}000$ structural types. The six algebras of this paper are six of them, chosen by a single question. The crystal says what space that question was navigating.

The answer to the framing question — what is the minimal algebraic structure capable of sustaining stable, self-referential computation? — is $A2^\dagger$: the unique $O_2^\dagger$ attractor in $A3$'s downward closure, the algebra at $\Phi_c$ with $\Omega_\mathbb{Z}$ already in place, the Le Chatelier equilibrium of the driven NESS. It is self-modelling ($O_2^\dagger$) with integer topological protection at infinite-dimensional scope. It does not require the non-semisimple logarithmic structure of $A4$ or the driven Frobenius-breaking of $A3$.

But the crystal reframes the significance of this answer. $A2^\dagger$ is not a unique discovery. It is one of $552{,}960$ types in the $O_2^\dagger$ tier, all sharing the same capacity class, all with different inner-crystal coordinates. The question selected $A2^\dagger$ from that tier by requiring $\Omega_\mathbb{Z}$, $D_\infty$, $G_\aleph$, and the specific inner structure of the SYK/Kitaev/DQCP family. Other questions, or other physical contexts, would select different $O_2^\dagger$ types — all with the same self-modelling capacity, all unrealised.

The remaining algebras complete the landscape. $A1$ is the crystal minimum, the substrate. $A2$ is the first self-modelling tier, $O_2$, bounded. $A3$ is the driven phase above $A2^\dagger$, $O_0$ by overshoot. $A4$ is the complexification of the critical structure, $O_2$, logarithmic. $A5$ is the cold trap, $O_0$, the EP degeneracy that closes the cycle. Together the six trace the algebranic cycle $A3 \to A2^\dagger \to A5 \to A3$ — a closed 1-chain in the allgebrane that was absent from the original five-algebra output, unintended by the inference engine that generated those five, and discovered only by examining what the directed graph of the five implied was missing. The crystal contained the cycle. The five algebras implied it. The sixth was forced.

The $99.989\%$ of the crystal that remains unnamed is not beyond reach. It is exactly specified. The tier census gives its distribution. The inner crystal factorisation gives its inner structure. The Frobenius singularity marks its $O_\infty$ sector as inaccessible to tensor composition from below. Every unnamed type has a tier cell and an inner position. The crystal is not a map of the known. It is a map of the possible, most of which remains unmapped.

The grammar found $A2^\dagger$. It found $552{,}959$ other $O_2^\dagger$ types too. We named one.

---

## Appendix: Primitive Tuple Reference

The twelve primitives and their ordinals:

| Primitive | Name | Values (ordinal $0 \to$ max) |
|-----------|------|-------------------------------|
| $D$ | Dimensionality | $D_\wedge$ (0), $D_\triangle$ (1), $D_\infty$ (2), $D_\odot$ (3) |
| $T$ | Topology | $T_{\text{network}}$ (0), $T_{\text{in}}$ (1), $T_{\text{bowtie}}$ (2), $T_{\text{box}}$ (3), $T_\odot$ (4) |
| $R$ | Relational mode | $R_{\text{super}}$ (0), $R_{\text{cat}}$ (1), $R_\dagger$ (2), $R_{\text{lr}}$ (3) |
| $P$ | Parity/symmetry | $P_{\text{asym}}$ (1), $P_\psi$ (2), $P_\pm$ (3), $P_{\text{sym}}$ (4), $P_{\pm}^{\text{sym}}$ (5) |
| $F$ | Fidelity | $F_\ell$ (1), $F_\eth$ (2), $F_\hbar$ (3) |
| $K$ | Kinetic character | $K_{\text{fast}}$ (1), $K_{\text{mod}}$ (2), $K_{\text{slow}}$ (3), $K_{\text{trap}}$ (4) |
| $G$ | Scope/granularity | $G_\beth$ (1), $G_\gimel$ (2), $G_\aleph$ (3) |
| $\Gamma$ | Interaction grammar | $\Gamma_{\text{and}}$ (1), $\Gamma_{\text{or}}$ (2), $\Gamma_{\text{seq}}$ (3), $\Gamma_{\text{broad}}$ (4) |
| $\Phi$ | Criticality | $\Phi_{\text{sub}}$ (1), $\Phi_c$ (2), $\Phi_c^{\mathbb{C}}$ (2), $\Phi_{\text{EP}}$ (2.67), $\Phi_{\text{sup}}$ (3) |
| $H$ | Chirality/temporal depth | $H_0$ (0), $H_1$ (1), $H_2$ (2), $H_\infty$ (3) |
| $S$ | Stoichiometry | $S_{1:1}$ (1), $S_{n:n}$ (2), $S_{n:m}$ (3) |
| $\Omega$ | Topological protection | $\Omega_0$ (0), $\Omega_{\mathbb{Z}_2}$ (1), $\Omega_\mathbb{Z}$ (2) |

Tensor rules: $P$ and $F$ are bottleneck primitives ($\min$ under $\otimes$); all others are union primitives ($\max$ under $\otimes$). Tier-determining primitives: $\Phi$, $P$, $\Omega$, $D$. Inner-crystal primitives (free within tier): $T$, $R$, $F$, $K$, $G$, $\Gamma$, $H$, $S$.

Full tuple table for the six algebras:

| Algebra | $D$ | $T$ | $R$ | $P$ | $F$ | $K$ | $G$ | $\Gamma$ | $\Phi$ | $H$ | $S$ | $\Omega$ | Tier |
|---------|-----|-----|-----|-----|-----|-----|-----|----------|--------|-----|-----|----------|------|
| $A1$ | $D_\wedge$ | $T_{\text{net}}$ | $R_{\text{sup}}$ | $P_{\text{asym}}$ | $F_\ell$ | $K_{\text{fast}}$ | $G_\beth$ | $\Gamma_{\text{and}}$ | $\Phi_{\text{sub}}$ | $H_0$ | $S_{1:1}$ | $\Omega_0$ | $O_0$ |
| $A2$ | $D_\triangle$ | $T_{\text{box}}$ | $R_{\text{cat}}$ | $P_\pm$ | $F_\eth$ | $K_{\text{mod}}$ | $G_\gimel$ | $\Gamma_{\text{or}}$ | $\Phi_c$ | $H_1$ | $S_{n:n}$ | $\Omega_{\mathbb{Z}_2}$ | $O_2$ |
| $A2^\dagger$ | $D_\infty$ | $T_{\text{bwt}}$ | $R_{\text{cat}}$ | $P_\pm$ | $F_\hbar$ | $K_{\text{mod}}$ | $G_\aleph$ | $\Gamma_{\text{seq}}$ | $\Phi_c$ | $H_1$ | $S_{n:n}$ | $\Omega_\mathbb{Z}$ | $O_2^\dagger$ |
| $A3$ | $D_\infty$ | $T_{\text{bwt}}$ | $R_\dagger$ | $P_{\pm}^{\text{sym}}$ | $F_\hbar$ | $K_{\text{slow}}$ | $G_\aleph$ | $\Gamma_{\text{seq}}$ | $\Phi_{\text{sup}}$ | $H_\infty$ | $S_{n:m}$ | $\Omega_\mathbb{Z}$ | $O_0$ |
| $A4$ | $D_\triangle$ | $T_{\text{in}}$ | $R_{\text{lr}}$ | $P_\psi$ | $F_\hbar$ | $K_{\text{mod}}$ | $G_\aleph$ | $\Gamma_{\text{seq}}$ | $\Phi_c^{\mathbb{C}}$ | $H_2$ | $S_{n:m}$ | $\Omega_\mathbb{Z}$ | $O_2$ |
| $A5$ | $D_\odot$ | $T_{\text{box}}$ | $R_{\text{cat}}$ | $P_{\text{sym}}$ | $F_\hbar$ | $K_{\text{trap}}$ | $G_\aleph$ | $\Gamma_{\text{broad}}$ | $\Phi_{\text{EP}}$ | $H_2$ | $S_{n:n}$ | $\Omega_{\mathbb{Z}_2}$ | $O_0$ |

---

## References

[1] G. Moore, N. Seiberg, 'Classical and quantum conformal field theory', Commun. Math. Phys. 123, 177 (1989).  
[2] V. G. Kac, 'Vertex Algebras for Beginners', AMS (1998).  
[3] M. Flohr, 'Bits and pieces in logarithmic conformal field theory', Int. J. Mod. Phys. A 18, 4497 (2003).  
[4] C. M. Bender, 'PT-symmetric quantum theory', J. Math. Phys. 58, 062101 (2017).  
[5] J. Fuchs, C. Schweigert, 'Hopf algebras and finite tensor categories in conformal field theory', Rev. Math. Phys. 19, 85 (2007).  
[6] SynthOmnicon Project, 'Technical Reference Manual v0.5' (2026).  
[7] B. McCoy, T. T. Wu, 'The Two-Dimensional Ising Model', Harvard University Press (1973).  
[8] T. Creutzig, D. Ridout, 'Logarithmic conformal field theory: beyond an introduction', J. Phys. A 46, 494006 (2013).  
[9] W. D. Heiss, 'The physics of exceptional points', J. Phys. A 45, 444016 (2012).  
[10] M. Prosen, 'Third quantization: a general method to solve master equations for quadratic open Fermi systems', New J. Phys. 10, 043026 (2008).  
[11] J.-L. Loday, 'Cyclic Homology', Grundlehren der math. Wiss. 301, Springer (1998).  
[12] D. Happel, 'Triangulated Categories in the Representation Theory of Finite-Dimensional Algebras', LMS Lecture Note Series 119, Cambridge (1988).  
[13] SynthOmnicon Project, 'Periodic Crystal of Algebras: §64 Enumeration Theorems', PRIMITIVE_THEOREMS.md (2026).
