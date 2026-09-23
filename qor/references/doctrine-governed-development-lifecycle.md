# Doctrine: Governed Development Lifecycle

**Status:** proposed implementation slice for GH #497; subject to formal `/qor-audit` before merge

## Purpose

Define the lifecycle semantics that sit above the current skill/gate chain without prematurely renaming skills or inventing new authority.

The current Qor phase chain remains operationally authoritative:

`research -> plan -> audit -> implement -> substantiate -> validate -> remediate`

`/qor-repo-release` is a downstream repo-level promotion skill, not a phase in that canonical chain. This doctrine clarifies what the chain means inside a more complete governed-development lifecycle and establishes the inner implementation loop that prompted GH #497.

## Core invariant

> No state transition may claim more certainty, authority, completion, or fitness than its evidence establishes.

This applies to agents, humans, skills, gate artifacts, issue state, release state, and documentation.

## Lifecycle model

Qor distinguishes the full governed-development lifecycle from the inner implementation loop.

### Full governed-development lifecycle

```text
UNDERSTAND
  -> DECIDE
  -> AUTHORIZE
  -> EXECUTE
  -> PROVE
  -> QA / ACCEPT
  -> PROMOTE
  -> OBSERVE
  -> ADAPT
```

This line is a **claim progression and semantic ordering of assurance claims**, not a mandatory runtime execution sequence, universal gate order, or one-skill-per-stage pipeline. It describes how claims generally become stronger and more externally consequential as evidence and authority accumulate.

Profiles and applicability rules may lawfully omit, collapse, repeat, or interleave stages when the governed operation does not require each one independently. An omitted, collapsed, deferred, or inapplicable stage must never be represented as PASS merely because the workflow advanced.

The existing operational skill/gate ordering remains authoritative until a separately audited enforcement change explicitly modifies it. In particular, this doctrine does not by itself require `PROVE -> QA / ACCEPT` as runtime ordering, reorder existing QA evidence, or create a new admission gate.

### Stage meanings

#### UNDERSTAND

Establish why work exists and what is known.

May consume operator requests, repository inspection, incidents, telemetry, support evidence, dependency changes, external research, governance drift, or other discovery sources.

Typical Qor owners include `/qor-ideate`, `/qor-research`, `/qor-roadmap`, `/qor-repo-audit`, and `/qor-debug` depending on the entry condition.

#### DECIDE

Choose and document the intended intervention, boundaries, risks, evidence strategy, acceptance conditions, and non-goals.

`/qor-plan` is the primary owner.

#### AUTHORIZE

Determine whether the proposed change may proceed under current authority and evidence.

`/qor-audit` is the primary plan-authorization gate. Authorization does not grant authority beyond the audited scope.

#### EXECUTE

Perform the authorized implementation through the inner implementation loop defined below.

`/qor-implement` is the primary owner. `/qor-debug`, `/qor-refactor`, `/qor-harden`, and `/qor-organize` may participate through explicit delegation.

#### PROVE

Establish that the implementation and evidence match the governed promise and that the evidence chain is internally trustworthy.

`/qor-substantiate` owns implementation substantiation. `/qor-validate` currently performs a narrower integrity/provenance validation and must not be interpreted as generic runtime or stakeholder acceptance.

#### QA / ACCEPT

Determine whether the result is acceptable for its intended use, including human or experiential judgment where required.

QA and acceptance are profile-dependent. They are not silently satisfied by automated test success.

See `doctrine-development-environments-and-qa.md`.

#### PROMOTE

Advance the proven and accepted result into the next authorized state.

Promotion may include merge, release, publication, deployment, or activation. These are distinct operations and must not be treated as synonyms.

`/qor-repo-release` owns repository release ceremony where applicable. External systems may own deployment or activation.

#### OBSERVE

Collect evidence from the environment in which the change is actually used.

Observation may include technical telemetry, user behavior, support feedback, operational evidence, compliance evidence, or other real-world signals. Qor need not become the observability provider in order to govern how evidence is interpreted and routed.

#### ADAPT

Reconcile new evidence with the assumptions, requirements, environment model, evaluator, implementation, and governance process that produced the current result.

Valid outcomes may include closure, further implementation, rollback/recovery, renewed research/planning, debugging, remediation, or explicit accepted risk.

## Inner implementation loop

The implementation loop is:

```text
inspect
  -> choose authorized work
  -> implement
  -> exercise
  -> observe
  -> verify
  -> reconcile
  -> reassess
  -> CONTINUE | PASS | ESCALATE | ABORT
```

### inspect

Read the actual current repository, runtime, artifact, configuration, or other relevant state before mutation. Assumptions are not inspection evidence.

### choose authorized work

Select the next work item already covered by the active change contract.

This does not authorize:

- new scope;
- a materially different architecture;
- a new product decision;
- a higher-risk intervention;
- authority the current actor does not possess.

If the necessary next action exceeds the authorized contract, the correct outcome is `ESCALATE`, not silent expansion.

### implement

Perform the bounded mutation.

### exercise

Invoke the changed behavior through an appropriate surface.

Examples include:

- unit or integration tests;
- browser interaction;
- API calls;
- CLI execution;
- database transactions;
- schema validation;
- simulation;
- benchmark;
- installer execution;
- generated artifact execution;
- agent traces.

### observe

Inspect the resulting behavior, state, output, or evidence.

For UI work this normally includes actual rendering and visual inspection where relevant. Passing DOM assertions alone does not establish rendered quality.

### verify

Interpret observations against the active change contract and relevant acceptance criteria.

Exercise produces evidence. Verification interprets evidence.

### reconcile

Compare the claim being made with all material observable state.

Reconciliation may include:

- intent/problem reconciliation;
- plan/change-contract reconciliation;
- implementation reconciliation;
- evidence reconciliation;
- documentation/configuration reconciliation;
- governance/provenance reconciliation;
- environment/runtime reconciliation.

> Every governed state transition must reconcile claimed state with observable state before authority advances.

### reassess

Determine what the new evidence changes.

Reassessment is typed:

- **residual reassessment**: more in-scope work remains;
- **scope reassessment**: required work lies outside the authorized scope;
- **risk reassessment**: evidence changes the risk posture;
- **objective reassessment**: the original objective or problem framing may no longer be sufficient.

Reassessment does not imply authority to act on everything it discovers.

## Universal loop outcomes

### CONTINUE

Current authority and scope remain sufficient and more in-scope implementation work remains.

### PASS

The current implementation-loop objective is satisfied under the evaluated conditions.

A loop PASS is not automatically substantiation, acceptance, release, deployment, or production fitness.

### ESCALATE

Evidence is valid, but the necessary next action exceeds current scope, capability, or authority.

Delegation resolves the lawful next owner.

### ABORT

Continuation would be unsafe, invalid, internally contradictory, or incapable of producing trustworthy evidence.

ABORT is not a failure to be hidden. It is a truthful lifecycle outcome.

## Problem contract and change contract

Qor distinguishes why work exists from how the intervention is authorized.

### Problem contract

May include:

- observed state;
- desired state;
- affected actors;
- evidence;
- impact/consequence;
- constraints;
- non-goals;
- uncertainty and assumptions;
- consequence of inaction.

### Change contract

May include:

- chosen approach;
- scope;
- architecture/implementation boundaries;
- authority boundaries;
- risk;
- exercise/verification strategy;
- QA and acceptance criteria;
- promotion implications;
- recovery implications.

> A plan is not authorized merely because it is internally coherent. It must remain traceable to an established problem or objective.

Profiles may scale the amount of explicit documentation required. Trivial work should not be forced into disproportionate ceremony.

## Verification, substantiation, attestation, acceptance

These concepts are distinct.

### Verification

Did the observed behavior satisfy the applicable contract under the evaluated conditions?

### Substantiation

Does the implementation and its evidence match the governed promise, scope, documentation, and release metadata?

### Integrity attestation

Is the governance/evidence chain internally intact and trustworthy?

Current `/qor-validate` behavior is closest to this class and must not be represented as broad product/runtime acceptance.

### Acceptance

Is the result acceptable to advance for its intended use?

Acceptance may require human judgment, stakeholder authority, accessibility review, operational readiness, performance thresholds, security review, or other profile-specific evidence.

## Promotion vocabulary

Qor must not collapse the following states:

`merge != release != publish != deploy != activate`

A repository may use only some of them, but any state it claims must have explicit evidence and authority.

## Operation, recovery, and adaptation

Runtime or production divergence is not always an implementation defect.

Potential divergence classes include:

- requirement/intent gap;
- environment/model gap;
- evaluator weakness;
- implementation defect;
- world/dependency change;
- stakeholder intent change;
- governance/process defect;
- inconclusive/unknown.

Recovery and remediation are distinct:

- **recovery/containment** restores a safe or known state now;
- **remediation** addresses the root process or governance defect that allowed recurrence.

## Historical truth vs current fitness

A PASS can remain historically truthful while no longer being sufficient evidence of current fitness.

Evidence should be interpreted within its envelope, including as applicable:

- revision/build/artifact;
- requirements/change contract;
- evaluator/check set;
- environment model and conditions;
- evidence sources;
- timestamp/freshness;
- explicit exclusions/limitations.

Later evidence may invalidate current applicability without rewriting the historical record.

## Cross-cutting infrastructure

The lifecycle is supported by, but is not itself replaced by:

- authority and delegation;
- evidence/provenance;
- governance freshness and supersession;
- governed attention/applicability;
- Shadow Genome learning;
- policy evaluation;
- traceability;
- recovery and escalation.

These mechanisms should remain proportionate and should not become mandatory ceremony merely because they exist.

## Compatibility rule

This doctrine does not by itself rename `/qor-validate`, add a new acceptance skill, alter the gate schema, or change release authority.

Those mutations require separately audited implementation slices under GH #497 and its child issues.
