# Implementation Quality Doctrine

## Purpose

This doctrine defines Qor-logic's implementation-quality standard independent of agent, model, host, repository, programming language, framework, provider, forge, runtime, or deployment environment.

It applies to artifacts and observable behavior. It does not infer authorship from code shape and does not treat AI provenance as a quality verdict.

> Implementation quality is established by contextual fitness, behavioral correctness, proportional complexity, explicit failure behavior, appropriate trust boundaries, and consistency with the surrounding system. Provenance does not determine quality.

## Governing rules

### IQ-1: Context before convention

Read the governing contracts, architecture, types or schemas, neighboring implementation, tests, and established repository conventions before applying generic engineering preferences.

Local consistency wins on style. It never overrides demonstrated security, correctness, data-integrity, or authority requirements.

### IQ-2: Behavior before surface plausibility

Code that compiles, looks conventional, or passes a narrow happy-path test is not established as correct. Quality claims require evidence about the behavior that matters at the relevant boundary.

Presence is not behavior. A test that proves an artifact exists does not prove the artifact performs its contract.

### IQ-3: Smallest sufficient mechanism

Prefer the least complex mechanism that satisfies the demonstrated contract, risk, scale, and variability.

Abstraction, indirection, configurability, concurrency machinery, persistence, dependency introduction, and generalized extension points require a concrete need. Do not remove a justified mechanism merely because a simpler pattern exists in isolation.

### IQ-4: No false completeness

Treat placeholders, inert implementations, fabricated interfaces, swallowed failures, misleading success responses, meaningless tests, dead branches presented as functionality, and unsupported assumptions as defects when they make incomplete behavior appear complete.

### IQ-5: Evidence before remediation

An apparent anti-pattern is a candidate finding, not a defect, until context establishes harm or contract violation.

Do not rewrite code merely because it resembles a generic smell. Confirm the problem, its scope, and the evidence that the proposed repair improves the actual system.

### IQ-6: Validate trust boundaries, trust established interior contracts

Validate external or untrusted input at the appropriate boundary. Preserve authentication, authorization, integrity, and data-validation requirements.

Do not duplicate validation, null checks, exception wrappers, defensive copies, or type checks inside trusted paths when upstream contracts make the invalid state unreachable and the repository intentionally relies on that contract.

### IQ-7: Preserve intent and authority

Hardening may improve implementation quality. It must not silently change product intent, public contracts, architecture, security policy, governance policy, data authority, or operator decisions.

When a quality repair would require one of those changes, stop the repair at the authority boundary and route the decision to the owning Qor-logic process.

### IQ-8: Scope is a contract

In changeset or focused review, inspect surrounding context as needed to understand the change, but do not opportunistically rewrite unrelated legacy code.

Out-of-scope defects may be reported with evidence. They become mutation scope only through an explicit scope decision.

### IQ-9: Failure must remain visible and truthful

Do not convert failure into nominal success merely to keep a process running. Errors must propagate, be represented, logged, retried, or intentionally tolerated according to the actual contract.

Observability should make consequential failures diagnosable without leaking secrets or sensitive data.

### IQ-10: Tests are evidence, not absolution

Passing tests increase confidence only to the extent that those tests exercise the relevant behavior, failure modes, boundaries, and state transitions.

Do not equate CI success with production correctness. Do not weaken tests to make an implementation pass.

### IQ-11: Repair the mechanism, not the symptom

When observed behavior is failing and the cause is uncertain, causal diagnosis belongs to `/qor-debug`. Hardening may identify suspicious mechanisms, but it must not guess through a failure and call the resulting patch a root-cause fix.

### IQ-12: Abstention is a successful outcome

A quality sweep must be capable of concluding that no justified change is required.

Unnecessary changes, false-positive findings, invented abstractions, speculative rewrites, and style-only churn count against quality. A clean implementation should survive inspection unchanged.

## Evidence hierarchy

When evidence conflicts, use this order unless a stronger explicit governance rule says otherwise:

1. repository contracts, architecture, and authority declarations;
2. types, schemas, invariants, and public interfaces;
3. established neighboring implementation and conventions;
4. executable tests, runtime evidence, and static-analysis evidence;
5. verified external dependency and API contracts;
6. language and framework conventions;
7. general quality heuristics.

Generic heuristics may raise questions. They may not overrule stronger evidence by themselves.

## Relationship to Qor-logic skills

This doctrine is an invariant shared by multiple skills. Reusing a doctrine or a bounded profile is not the same as delegating an independently governed operation.

- `/qor-plan` uses prevention-oriented questions.
- `/qor-audit` uses adversarial prediction of likely quality failures.
- `/qor-implement` uses local prevention and a final implementation sweep.
- `/qor-debug` uses the taxonomy as hypothesis vocabulary while retaining causal ownership.
- `/qor-refactor` repairs confirmed structural and maintainability defects within its authority.
- `/qor-substantiate` detects quality failures independently but remains prove-not-improve.
- `/qor-deep-audit` uses the full taxonomy as one discovery lens.
- `/qor-harden` owns explicit implementation-quality review and authorized repair across the declared scope.

The canonical operational taxonomy is `qor/references/implementation-quality-sweep.md`.
