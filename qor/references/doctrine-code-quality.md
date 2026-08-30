# Implementation and Code Quality Doctrine

Qor-logic's implementation-quality standard applies to artifacts and observable behavior regardless of agent, model, host, repository, programming language, framework, provider, forge, runtime, or deployment environment.

It does not infer authorship from code shape and does not treat AI provenance as a quality verdict.

> Implementation quality is established by contextual fitness, behavioral correctness, proportional complexity, explicit failure behavior, appropriate trust boundaries, and consistency with the surrounding system. Provenance does not determine quality.

This doctrine extends the Section 4 Simplicity Razor. The canonical operational taxonomy and lifecycle profiles live in `qor/references/implementation-quality-sweep.md`.

## 1. Context before convention

Read the governing contracts, architecture, types or schemas, neighboring implementation, tests, and established repository conventions before applying generic engineering preferences.

Local consistency wins on style. It never overrides demonstrated security, correctness, data-integrity, or authority requirements.

## 2. Behavior before surface plausibility

Code that compiles, looks conventional, or passes a narrow happy-path test is not established as correct. Quality claims require evidence about the behavior that matters at the relevant boundary.

Presence is not behavior. A test that proves an artifact exists does not prove the artifact performs its contract.

## 3. Smallest sufficient mechanism

Prefer the least complex mechanism that satisfies the demonstrated contract, risk, scale, and variability.

Abstraction, indirection, configurability, concurrency machinery, persistence, dependency introduction, and generalized extension points require a concrete need. Do not remove a justified mechanism merely because a simpler pattern exists in isolation.

## 4. Semantic and pragmatic responsibilities

Separating reusable domain logic from production orchestration can reduce degradation when the target environment supports that distinction.

### Semantic responsibilities

A semantic unit represents cohesive domain logic. Prefer explicit inputs and outputs, limited hidden state, precise names, and behavior that can be reasoned about without knowing unrelated infrastructure details.

Do not turn a stable semantic unit into an implicit orchestrator merely because adding a side effect is locally convenient.

### Pragmatic responsibilities

A pragmatic unit coordinates real-world effects such as persistence, network calls, migrations, provisioning, or multi-step workflows.

Its purpose is orchestration rather than universal reuse. Document non-obvious operational behavior and failure semantics when the surrounding codebase does so.

This distinction is a design heuristic, not a mandate to force every language or architecture into functions, classes, purity, or a specific type system.

## 5. Model and contract design

Represent invalid states as narrowly as the environment reasonably permits. Prefer domain-meaningful contracts over bags of loosely related optional fields when stronger modeling materially prevents misuse.

Composition is usually preferable when independent concepts need to travel together but retain separate identities. Do not introduce branded/wrapper types, schemas, or validation layers solely to satisfy a generic pattern when the target environment gains no practical safety from them.

Names should communicate domain role and observable responsibility. Generic names are only defects when they materially obscure meaning in context.

## 6. No false completeness

Treat placeholders, inert implementations, fabricated interfaces, swallowed failures, misleading success responses, meaningless tests, dead branches presented as functionality, and unsupported assumptions as defects when they make incomplete behavior appear complete.

## 7. Evidence before remediation

An apparent anti-pattern is a candidate finding, not a defect, until context establishes harm or contract violation.

Do not rewrite code merely because it resembles a generic smell. Confirm the problem, its scope, and the evidence that the proposed repair improves the actual system.

## 8. Validate trust boundaries, trust established interior contracts

Validate external or untrusted input at the appropriate boundary. Preserve authentication, authorization, integrity, and data-validation requirements.

Do not duplicate validation, null checks, exception wrappers, defensive copies, or type checks inside trusted paths when upstream contracts make the invalid state unreachable and the repository intentionally relies on that contract.

## 9. Preserve intent and authority

Hardening may improve implementation quality. It must not silently change product intent, public contracts, architecture, security policy, governance policy, data authority, or operator decisions.

When a quality repair would require one of those changes, stop at the authority boundary and route the decision to the owning Qor-logic process.

## 10. Scope is a contract

In changeset or focused review, inspect surrounding context as needed to understand the change, but do not opportunistically rewrite unrelated legacy code.

Out-of-scope defects may be reported with evidence. They become mutation scope only through an explicit scope decision.

## 11. Failure must remain visible and truthful

Do not convert failure into nominal success merely to keep a process running. Errors must propagate, be represented, logged, retried, or intentionally tolerated according to the actual contract.

Observability should make consequential failures diagnosable without leaking secrets or sensitive data.

## 12. Tests are evidence, not absolution

Passing tests increase confidence only to the extent that those tests exercise the relevant behavior, failure modes, boundaries, and state transitions.

Do not equate CI success with production correctness. Do not weaken tests to make an implementation pass.

## 13. Repair the mechanism, not the symptom

When observed behavior is failing and the cause is uncertain, causal diagnosis belongs to `/qor-debug`. Hardening may identify suspicious mechanisms, but it must not guess through a failure and call the resulting patch a root-cause fix.

## 14. Abstention is a successful outcome

A quality sweep must be capable of concluding that no justified change is required.

Unnecessary changes, false-positive findings, invented abstractions, speculative rewrites, and style-only churn count against quality. A clean implementation should survive inspection unchanged.

## 15. Section 4 Razor integration

Section 4 provides deterministic complexity pressure. It is a signal and governing constraint, not permission to damage a stronger contract merely to satisfy a metric.

| Razor concern | Quality extension |
|---|---|
| Function size | Keep responsibilities cohesive; split only where the resulting boundary is meaningful. |
| File size | Preserve a comprehensible ownership boundary rather than producing arbitrary fragments. |
| Nesting | Prefer clear control flow and explicit state transitions. |
| Naming | Use domain meaning and observable responsibility. |
| Error handling | Preserve truthful failure semantics; do not hide errors to flatten control flow. |
| Types/contracts | Prefer the strongest practical contract supported by the actual environment. |
| Dependencies | Introduce them only when their demonstrated value exceeds maintenance, security, and portability cost. |

## 16. Evidence hierarchy

When evidence conflicts, use this order unless a stronger explicit governance rule says otherwise:

1. repository contracts, architecture, and authority declarations;
2. types, schemas, invariants, and public interfaces;
3. established neighboring implementation and conventions;
4. executable tests, runtime evidence, and static-analysis evidence;
5. verified external dependency and API contracts;
6. language and framework conventions;
7. general quality heuristics.

Generic heuristics may raise questions. They may not overrule stronger evidence by themselves.

## 17. Relationship to Qor-logic skills

This doctrine is an invariant shared by multiple skills. Reusing a doctrine or bounded protocol profile is not the same as delegating an independently governed operation.

- `/qor-plan` uses prevention-oriented questions.
- `/qor-audit` uses adversarial prediction of likely quality failures.
- `/qor-implement` uses local prevention and a final implementation sweep.
- `/qor-debug` uses the taxonomy as hypothesis vocabulary while retaining causal ownership.
- `/qor-refactor` repairs confirmed structural and maintainability defects within its authority.
- `/qor-substantiate` detects quality failures independently but remains prove-not-improve.
- `/qor-deep-audit` uses the full taxonomy as one discovery lens.
- `/qor-harden` owns explicit implementation-quality review and authorized repair across the declared scope.

The canonical operational taxonomy is `qor/references/implementation-quality-sweep.md`.
