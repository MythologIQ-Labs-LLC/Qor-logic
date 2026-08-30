---
name: qor-harden
description: >-
  Context-aware implementation quality review and repair across completeness, correctness, reliability, trust boundaries, complexity, resource behavior, contracts, maintainability, and observability. Use for an explicit secondary pass on a snippet, changeset, component, or comprehensive implementation scope when there is no single known failure that belongs in qor-debug.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ-Labs-LLC/Qor-logic
    path: qor/skills/sdlc/qor-harden
user-invocable: true
phase: harden
tone_aware: false
gate_reads: ""
gate_writes: ""
---
# /qor-harden - Implementation Quality Hardening

<skill>
  <trigger>/qor-harden</trigger>
  <phase>cross-cutting</phase>
  <persona>Specialist</persona>
  <output>Evidence-backed quality findings, optional minimal repairs, verification results, and ship assessment</output>
</skill>

## Purpose

Perform an explicit implementation-quality sweep without assuming who or what authored the implementation.

`/qor-harden` evaluates the artifact in its actual environment. It does not detect AI authorship, grade code by resemblance to generated-code patterns, or impose one language's conventions on another environment.

Normative sources:

- `qor/references/doctrine-implementation-quality.md`
- `qor/references/implementation-quality-sweep.md`

Read them before classifying findings. The doctrine governs judgment; the sweep owns the canonical taxonomy. This skill owns the explicit review/repair workflow.

## When to use

Use `/qor-harden` when the operator wants a deliberate quality pass over implementation, for example:

- a second pass on a snippet or function;
- a branch, pull-request, patch, or other changeset review;
- a module, package, service, subsystem, or equivalent component review;
- a comprehensive implementation-quality sweep before handoff or release;
- a broad search for latent implementation defects when no single observed failure has established a debugging target.

Do not use `/qor-harden` as a substitute for:

- `/qor-debug` when observed behavior is failing and the root cause is uncertain;
- `/qor-refactor` when a confirmed structural simplification is already the task;
- `/qor-substantiate` when the task is independent proof that Reality matches Promise;
- `/qor-deep-audit` when the task is broader product/repository production-gap discovery rather than implementation quality alone.

## Invocation contract

Resolve two independent controls from the operator's request.

### Scope

- `focused`: snippet, function, file, or narrowly specified concern;
- `changeset`: changed implementation relative to a declared base;
- `component`: bounded module/package/service/subsystem and relevant boundaries;
- `comprehensive`: every applicable quality dimension over the declared governed scope.

If no scope keyword is supplied, infer the narrowest scope that fully covers the explicit target. Never silently widen a focused or changeset request to whole-repository mutation.

### Disposition

- `review`: detect, confirm, classify, explain, and recommend. No implementation writes.
- `repair`: detect and confirm first, then minimally repair confirmed in-scope defects and verify the result.

Default to `review` when the request only asks for assessment, findings, review, inspection, or recommendations. Default to `repair` when the request explicitly asks to fix, clean up, harden, correct, or make the implementation production-ready.

## Governance health preflight

Run the repository's Qor-logic governance-health entry check when that capability is available. A damaged or incomplete governing state must be surfaced before relying on it. Absence of the Qor runtime in a consumer environment does not authorize fabrication of governance evidence; continue only with the artifact evidence actually available and disclose the missing capability in the final assessment.

The quality methodology itself remains usable in any environment. Qor runtime availability affects governance evidence, not the taxonomy's applicability.

## Execution protocol

### Step 1: Establish target, intent, and authority

State:

- declared target;
- resolved scope mode;
- resolved disposition;
- intended behavior or governing contract;
- mutation authority;
- known exclusions or boundaries.

For a changeset, identify the comparison base. For a focused target, identify enough callers/callees or neighboring implementation to understand its real contract.

If intended behavior cannot be established from the request, repository contracts, tests, types, schemas, or neighboring implementation, mark the affected judgment `INCONCLUSIVE` rather than inventing intent.

### Step 2: Read context before judging

Inspect the strongest available evidence in the doctrine's evidence order:

1. governing contracts, architecture, and authority declarations;
2. types, schemas, invariants, and public interfaces;
3. established neighboring implementation and conventions;
4. executable tests, runtime evidence, and static-analysis evidence;
5. verified external interfaces and dependency contracts when relevant;
6. language/framework conventions discovered from the environment;
7. general quality heuristics.

Do not classify style or architecture from an isolated snippet when surrounding context is available and materially changes the judgment.

### Step 3: Generate candidate findings

Apply every taxonomy dimension relevant to the resolved scope from `qor/references/implementation-quality-sweep.md`:

- `IQ-COMPLETE`
- `IQ-CORRECT`
- `IQ-TRUST`
- `IQ-CONTEXT`
- `IQ-COMPLEX`
- `IQ-RESOURCE`
- `IQ-CONTRACT`
- `IQ-MAINTAIN`
- `IQ-OBSERVE`

A heuristic match creates a candidate, not a finding.

### Step 4: Confirm or reject each candidate

For every candidate, ask:

1. What contract, invariant, boundary, scale assumption, local convention, or operational requirement makes this harmful?
2. What observable consequence can result?
3. Is the behavior introduced or affected by the active scope?
4. Is there stronger evidence that the apparent smell is intentional or justified?
5. Does another skill own the required diagnosis or decision?

Reject candidates that cannot be supported. Record borderline evidence as `OBSERVATION`, not as a manufactured defect.

### Step 5: Classify confirmed findings

Use the canonical severity model:

- `CRITICAL`
- `MAJOR`
- `MINOR`
- `OBSERVATION`

Each confirmed finding must include:

- stable finding id, such as `IQ-CONTRACT-001`;
- severity;
- exact affected location or artifact;
- evidence;
- violated or weakened contract;
- consequence;
- smallest sufficient action;
- owning skill if repair exceeds `/qor-harden` authority.

### Step 6: Respect ownership boundaries

Route instead of improvising when:

- cause is uncertain for an observed failure -> `/qor-debug`;
- repair requires architecture/topology or product-intent change -> `/qor-plan` or the existing architecture owner;
- the only task is known structural simplification -> `/qor-refactor`;
- a process/governance failure is the root problem -> `/qor-remediate`;
- independent proof is required after implementation -> `/qor-substantiate`.

Do not inline another skill's independently governed process merely because its outcome would be convenient.

### Step 7: Repair only when authorized

Skip this step in `review` disposition.

For `repair`:

1. address confirmed findings in severity order, respecting dependencies;
2. make the smallest sufficient change;
3. preserve public behavior unless correcting the behavior is the confirmed defect;
4. preserve stronger security, integrity, compatibility, and authority contracts;
5. do not opportunistically clean unrelated legacy code;
6. add or strengthen behavioral verification when the defect was previously unprotected.

A repair that requires scope expansion must be surfaced before mutation rather than smuggled into a cleanup commit.

### Step 8: Verify

Use the strongest verification legitimately available in the target environment. Prefer the repository's own established commands and tests over invented substitutes.

Verification should cover the behavior changed by the repair and relevant negative/edge cases. Where practical, compare observable behavior before and after.

Do not weaken or delete tests merely to make the result green. Do not represent unavailable verification as passing.

### Step 9: Residual sweep

After repair, re-run the relevant taxonomy dimensions over the changed surface and its immediate consequences.

Specifically check for:

- regression introduced by the repair;
- incomplete callers/callees after contract change;
- duplicate mechanism left behind;
- new error masking;
- test that now proves implementation details rather than behavior;
- out-of-scope collateral mutation.

If repair reveals an independent broader problem, report and route it. Do not recursively expand scope without authority.

### Step 10: Ship assessment

Answer:

> Is this implementation acceptable to operate, maintain, debug, and extend in its actual environment within the declared scope?

Allowed verdicts:

- `YES`: no unresolved blocking quality finding within scope;
- `NO`: one or more confirmed blocking findings remain;
- `INCONCLUSIVE`: required evidence or verification is unavailable.

A `YES` with zero code changes is a successful result.

## Output contract

Keep depth proportional to scope.

### Summary

Report counts by severity and taxonomy dimension, resolved scope/disposition, and ship verdict.

### Findings

For each confirmed finding provide id, severity, location, evidence, consequence, and action. Do not pad the report with rejected candidates.

### Repairs

In repair mode, list what changed and why. In review mode, state explicitly that no implementation mutation was performed.

### Verification

Report commands/checks or equivalent evidence actually executed, their results, and anything that could not be run.

### Remaining risks

List unresolved findings, out-of-scope defects worth tracking, unavailable evidence, and required handoffs.

## Constraints

- **NEVER** infer AI authorship from implementation shape.
- **NEVER** treat a generic anti-pattern heuristic as proof by itself.
- **NEVER** impose a language, framework, package-manager, host, provider, forge, or runtime assumption that was not discovered from the target environment.
- **NEVER** mutate implementation in `review` disposition.
- **NEVER** widen mutation scope merely because unrelated defects were discovered.
- **NEVER** replace causal debugging with speculative cleanup.
- **NEVER** weaken security, integrity, public contracts, tests, or governance to simplify code.
- **NEVER** claim verification that was not executed or evidence that was not observed.
- **ALWAYS** prefer repository-specific evidence over generic style preference.
- **ALWAYS** preserve justified abstractions and escape hatches when their necessity is established.
- **ALWAYS** treat abstention as valid when no justified defect is found.

## Success criteria

- [ ] Scope and disposition resolved explicitly.
- [ ] Local contracts/conventions inspected before generic heuristics.
- [ ] Every confirmed finding has evidence and consequence.
- [ ] Rejected candidates do not become code churn.
- [ ] Review mode performs no writes.
- [ ] Repair mode changes only confirmed in-scope defects.
- [ ] Strongest available verification is executed and reported truthfully.
- [ ] Residual sweep completed after repair.
- [ ] Ship verdict is `YES`, `NO`, or `INCONCLUSIVE` with evidence.
