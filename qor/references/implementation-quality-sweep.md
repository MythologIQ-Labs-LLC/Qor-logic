# Implementation Quality Sweep

Canonical protocol for context-aware implementation-quality inspection in Qor-logic.

This protocol is agent-, host-, repository-, language-, framework-, provider-, forge-, runtime-, and deployment-agnostic. Specific tools, syntax, package ecosystems, and language idioms are discovered from the target environment rather than assumed here.

Normative doctrine: `qor/references/doctrine-implementation-quality.md`.

## Operating principle

A pattern is not a defect merely because it resembles one. For each candidate finding:

1. identify the relevant contract or intended behavior;
2. establish the local convention and boundary context;
3. collect evidence that the candidate is harmful, incomplete, misleading, unsafe, wasteful, or inconsistent;
4. classify severity and ownership;
5. repair only when the active disposition authorizes mutation and the repair stays inside scope;
6. verify the resulting behavior;
7. preserve a valid implementation unchanged when no defect is established.

## Taxonomy

### IQ-COMPLETE: completeness and false-completeness

Look for behavior presented as finished when its contract is not actually implemented.

Candidate signals include placeholders, stubs, inert branches, fabricated interfaces, success-shaped dummy responses, unexercised wiring, missing side effects, tests with no meaningful behavioral assertion, skipped verification without disclosure, and code paths that cannot be reached from the intended entry point.

Confirm against the promised behavior before classifying.

### IQ-CORRECT: correctness and reliability

Look for incorrect state transitions, boundary errors, invalid assumptions, missing edge cases, inconsistent error semantics, ordering defects, unsafe concurrent access, non-deterministic behavior, improper asynchronous coordination, resource-lifetime mistakes, and failure paths that contradict the contract.

When an observed failure exists but the root cause is uncertain, route causal diagnosis to `/qor-debug` rather than guessing through it.

### IQ-TRUST: trust and security boundaries

Look for missing or duplicated trust-boundary validation, injection surfaces, authorization/authentication mistakes, secret exposure, unsafe defaults, integrity bypasses, insecure deserialization or execution, excessive privilege, policy bypass, and security controls that exist only in tests or documentation.

Security obligations may override local style. Do not invent a security requirement that the system does not actually have.

### IQ-CONTEXT: contextual consistency and duplication

Look for a newly introduced mechanism that duplicates an existing repository capability, implements the same policy differently, violates established dependency direction, bypasses canonical helpers, fragments a single source of truth, or introduces style/structure drift that materially raises maintenance or correctness risk.

Do not enforce generic stylistic uniformity where the repository intentionally contains multiple conventions.

### IQ-COMPLEX: proportional complexity

Look for abstraction, indirection, factories, interfaces, service layers, configuration, eventing, persistence, concurrency, wrappers, fallbacks, defensive code, or extension points whose complexity is not justified by demonstrated requirements.

Also check the inverse: do not remove complexity that isolates real volatility, satisfies multiple consumers, protects a boundary, or encodes a necessary invariant.

### IQ-RESOURCE: resource behavior and I/O

Look for repeated scans, nested lookup work on material data sets, avoidable network/database/file calls, unbounded fan-out, missing batching where the target interface supports it, unnecessary serialization, resource leaks, excessive memory retention, retry storms, and blocking work in latency-sensitive paths.

Performance findings require scale or cost evidence. Small-input clarity is not a defect merely because a more asymptotically efficient form exists.

### IQ-CONTRACT: types, dependencies, and external interfaces

Look for type suppression that hides an actual mismatch, unchecked schema divergence, phantom or deprecated APIs, unsupported dependency assumptions, package/runtime features not declared by the environment, silent compatibility fallbacks, contract fields used differently across callers, and external calls built from memory rather than verified interfaces.

A dynamic type escape, lazy import, compatibility branch, or suppression may be valid when context proves the boundary genuinely requires it.

### IQ-MAINTAIN: maintainability and explanatory quality

Look for dead code, stale commented-out implementations, unused dependencies/imports, misleading comments, domain-opaque names, duplicated constants, unexplained policy literals, unnecessary verbosity, and comments that narrate obvious syntax while omitting the reason for non-obvious business behavior.

Match the target repository's comment density, naming style, formatting, and organization before proposing cosmetic change.

### IQ-OBSERVE: observability and truthful failure reporting

Look for swallowed failures, nominal-success responses after partial failure, missing correlation/context where operations require diagnosis, sensitive logging, opaque retry behavior, health signals that do not reflect real readiness, and metrics/logs that claim more work succeeded than actually did.

Observability must be proportional. A pure local helper does not need a distributed tracing subsystem because tracing exists somewhere in the universe.

## Severity

Use consequence, not aesthetics:

- **CRITICAL**: credible production breakage, security/integrity compromise, data corruption, authority bypass, or false proof that can permit an unsafe release.
- **MAJOR**: material reliability, maintainability, performance, contract, test-validity, or operational defect likely to cause real pain or future failures.
- **MINOR**: localized quality debt with low immediate consequence and a justified repair inside scope.
- **OBSERVATION**: evidence worth recording but insufficient to justify mutation now.

Do not inflate severity to make a review look useful.

## Scope profiles

### Focused

Target: snippet, function, file, or narrowly declared concern.

Read enough surrounding context to establish contracts and conventions. Mutations remain within the focused target unless an explicit dependency must change to preserve correctness.

### Changeset

Target: changed code relative to a declared base.

Inspect unchanged neighboring code for context only. Report unrelated legacy defects separately and do not modify them without scope expansion.

### Component

Target: module, package, service, subsystem, or equivalent bounded component.

Include internal contracts, dependency edges, shared state, tests, and operational boundaries relevant to that component.

### Comprehensive

Target: the full declared implementation scope.

Run every applicable taxonomy dimension and look for cross-component duplication, policy divergence, systemic trust-boundary inconsistencies, contract drift, broad observability gaps, repeated quality patterns, and architecture-level implementation debt.

Comprehensive does not mean unlimited. The declared scope and authority boundaries still apply.

## Dispositions

### Review

Detect, confirm, classify, explain, and recommend. Do not mutate implementation artifacts.

Review output must include evidence, consequence, owning dimension, and a smallest-sufficient recommended action. If no defect is confirmed, say so.

### Repair

Detect and confirm first, then make the smallest sufficient in-scope repair. Preserve intended behavior and stronger contracts. Add or strengthen behavioral verification when needed to prove the repair.

After repair, run a residual sweep for defects introduced or exposed by the change.

## Lifecycle profiles

These profiles reuse the taxonomy without reproducing `/qor-harden` as an inline workflow.

### `/qor-plan` prevention profile

Ask whether the plan introduces duplicate capability, unjustified machinery, unsupported interfaces, missing failure behavior, weak behavioral tests, unclear trust boundaries, unsafe state/concurrency assumptions, or operationally invisible failure modes.

### `/qor-audit` adversarial profile

Challenge the plan for false-completeness paths, likely contract drift, dependency/API assumptions, excessive architecture, missing negative cases, invalid test strategy, missing observability, and quality requirements that cannot be substantiated later.

### `/qor-implement` prevention profile

Before adding a mechanism, inspect the local implementation path. After each meaningful behavioral unit, check for accidental duplication, false completeness, hidden failure, unjustified complexity, and weakened contracts. Run a final changeset-quality sweep before handoff.

### `/qor-debug` hypothesis profile

Use taxonomy dimensions to generate candidate mechanisms after symptoms are established. Continue to require evidence-backed root cause before repair. The taxonomy does not replace causal diagnosis.

### `/qor-refactor` remediation profile

Own confirmed IQ-CONTEXT, IQ-COMPLEX, and IQ-MAINTAIN repairs that stay within refactor's structural authority. Route uncertain behavioral failure to debug and architecture/topology decisions to their existing owners.

### `/qor-substantiate` verification profile

Run read-only checks for false completeness, weak tests, hidden failures, contract divergence, scope drift, and quality claims unsupported by evidence. Detect and delegate. Do not mutate implementation to make substantiation pass.

### `/qor-deep-audit` discovery profile

Use all dimensions during reconnaissance and verification. Normalize findings to IQ identifiers so remediation and later verification share one vocabulary.

## Standalone ship question

A `/qor-harden` pass ends by answering, with evidence:

> Is this implementation acceptable to operate, maintain, debug, and extend in its actual environment within the declared scope?

The acceptable answers are `YES`, `NO`, or `INCONCLUSIVE`. `YES` with no code changes is a valid and often desirable result.
