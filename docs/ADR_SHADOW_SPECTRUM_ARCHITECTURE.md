# ADR: Shadow Spectrum as a Typed Feedback Architecture

**Status:** Proposed; formal `/qor-audit` required before adoption
**Date:** 2026-09-22
**Scope:** Shadow Genome architecture, lifecycle feedback, failure memory, drift classification
**Umbrella:** GH #497
**Related:** `docs/ADR_TWO_GAP_ASSURANCE_BOUNDARY.md`

## Context

Qor-logic already contains a substantial Shadow Genome subsystem rather than a single incidental log:

- `docs/SHADOW_GENOME.md` preserves narrative failure patterns and countermeasures;
- structured process events are persisted through `docs/PROCESS_SHADOW_GENOME.md` and the upstream-attribution companion;
- attribution doctrine distinguishes Qor-originated and consumer/LLM-originated failures;
- threshold logic escalates recurring or severe process failures;
- collection and issue-creation tooling turns repeated shadow evidence into remediation work.

The subsystem was originally optimized around failure-pattern memory, process weakness, VETOs, overrides, and recurring governance defects.

The proposed two-gap assurance model introduces additional recurring evidence classes that do not fit cleanly into one undifferentiated concept of "process failure":

- requirement drift or omitted stakeholder intent;
- environment-model mismatch;
- evaluator weakness;
- implementation failure;
- operational divergence after promotion;
- authority/governance mismatch;
- evidence freshness or invalidation;
- supersession drift;
- changed stakeholder intent or changed world conditions.

If all of these are flattened into one Shadow Genome stream, Qor risks losing causal precision. If each becomes a separate independent subsystem, Qor risks architecture sprawl and duplicated machinery.

The question is therefore not whether the Shadow Genome remains relevant. It is whether the Shadow Genome should evolve from a mostly process-failure memory into a typed family of governed feedback signals.

## Decision

Adopt the **Shadow Spectrum** as the conceptual architecture for future Shadow Genome evolution.

The Shadow Spectrum is not a set of mandatory new files or skills. It is a classification model that treats shadow evidence as one governed family with multiple shades/dimensions rather than one undifferentiated failure bucket.

The initial candidate spectrum is:

1. **Intent Shadow** — evidence that written requirements or accepted objectives did not fully capture stakeholder intent, or that intent changed.
2. **Model Shadow** — evidence that evaluation assumptions or environment models failed to represent relevant production/world conditions.
3. **Evaluator Shadow** — evidence that a verifier, test, gate, review, or evaluator failed to detect a defect that was representable in the governed requirement/model envelope.
4. **Implementation Shadow** — recurring implementation-level failure patterns, reward-hacking strategies, hallucinated mechanisms, brittle shortcuts, or false completeness.
5. **Operational Shadow** — post-promotion/runtime divergence, rollback triggers, reliability patterns, dependency/world drift, and production conditions that materially alter assurance.
6. **Governance Shadow** — process failures, gate overrides, authority violations, stale governance, contradictory doctrine, supersession failures, and evidence-chain defects.
7. **Unknown / Cross-spectrum** — evidence that is real but not yet causally attributable to one shade, or legitimately spans several.

Names are conceptual and may change after adversarial review. The architectural requirement is typed, evidence-backed classification, not attachment to this exact vocabulary.

## One genome, many shades

The default architectural posture is **one Shadow Genome family with typed events and views**, not seven independent genomes.

Rationale:

- recurring evidence often crosses boundaries;
- one canonical identity and provenance model reduces duplication;
- correlation across shades is valuable;
- threshold and escalation machinery can remain shared;
- specialized views can emerge without fragmenting historical truth;
- a classification may be revised as evidence improves without moving events between unrelated stores.

A physically split persistence model is deferred until measured scale, access-control, proprietary-boundary, or retention requirements justify it.

## Evidence and classification rules

Shadow classification MUST NOT become speculative labeling.

For each shadow event or pattern, Qor should preserve where practical:

- observed evidence;
- originating lifecycle state;
- revision/artifact/environment binding;
- initial classification;
- confidence or supported/unsupported status where appropriate;
- causal owner if established;
- affected assurance claim;
- disposition;
- supersession/reclassification history;
- link to remediation, plan, issue, ADR, or accepted-risk decision.

`Unknown` is preferable to fabricated certainty.

## Relationship to the two-gap model

The Shadow Spectrum provides the institutional-memory layer for the outer assurance-revision loop.

Examples:

- production reveals an unmodeled third-party rate-limit behavior -> **Model Shadow**;
- users repeatedly reject behavior that satisfied written acceptance criteria -> **Intent Shadow**;
- a test suite should have caught a representable boundary bug but did not -> **Evaluator Shadow**;
- an agent repeatedly implements success-shaped stubs -> **Implementation Shadow**;
- a canary repeatedly fails under one deployment topology -> **Operational Shadow**;
- an ADR remains `Proposed` after implementation or conflicting doctrine stays live -> **Governance Shadow**.

These classifications determine what kind of revision should be considered, but do not themselves authorize the revision.

## Relationship to existing process genomes

Existing structured process-genome files and threshold logic remain valid historical architecture unless a governed migration says otherwise.

This ADR does not authorize renaming or rewriting existing evidence stores.

Instead, follow-on design should determine whether the current structured event schema can safely gain typed shadow dimensions while preserving backward compatibility and existing attribution semantics.

Schema migration is explicitly a governance concern because the Shadow Genome has already recorded migration-blindness as a failure pattern.

## Attribution is orthogonal to shade

Current attribution distinguishes upstream Qor-logic causes from local/consumer/LLM-intrinsic causes.

That axis should remain independent from Shadow Spectrum classification.

For example:

```text
shade: model_shadow
attribution: upstream
```

and

```text
shade: model_shadow
attribution: local
```

are both legitimate.

Do not collapse "what kind of shadow is this?" with "who/what owns the cause?"

## Severity is orthogonal to shade

Severity likewise remains independent.

An Intent Shadow may be minor or catastrophic. A Governance Shadow may be advisory or release-blocking. The shade class identifies the failure domain; severity represents consequence.

## Pattern formation

Individual events should not automatically become durable Shadow Genome patterns.

Pattern promotion should require evidence such as:

- recurrence;
- high consequence;
- systemic reach;
- demonstrated blind spot;
- meaningful countermeasure value;
- explicit operator/governance decision.

This preserves the Genome as institutional learning rather than a dumping ground for every defect.

## Countermeasure semantics

Countermeasures should identify the layer they modify:

- requirement elicitation or acceptance;
- environment/evaluation model;
- evaluator/test/gate;
- implementation doctrine;
- operational control;
- governance process;
- authority/human review.

This allows Qor to learn not only "what failed" but "which layer must change to reduce recurrence."

## Proprietary boundary

The Shadow Genome is a proprietary Qor-logic architectural concept even where portions of its public doctrine and evidence model are visible.

Public documentation should explain enough of the architecture to keep Qor internally coherent and reviewable without requiring disclosure of proprietary implementation detail, proprietary corpora, internal heuristics, or private cross-repository shadow evidence.

Publication-boundary doctrine remains authoritative.

## Consequences

### Positive

- prevents new lifecycle architecture from accidentally sidelining an existing core subsystem;
- provides a coherent home for two-gap and outer-loop learning;
- separates failure domain, attribution, severity, and authority instead of conflating them;
- supports cross-domain correlation without immediately multiplying persistence systems;
- makes stale governance and supersession drift first-class shadow phenomena;
- gives `/qor-remediate` and future review doctrine more precise causal inputs.

### Costs

- existing event schemas and reports may eventually need additive fields;
- countermeasure doctrine will need review;
- threshold logic may need shade-aware behavior rather than a single severity sum;
- reporting and review surfaces will need to avoid overwhelming operators with low-value shadow events;
- proprietary/public documentation boundaries must remain explicit.

## Rejected alternatives

### Ignore Shadow Genome in the new lifecycle model

Rejected. It is already a component architecture for institutional failure learning and should consume the new feedback classes.

### Create one independent genome per failure class now

Rejected. No evidence yet justifies seven persistence and governance subsystems.

### Keep one untyped stream forever

Rejected as the target architecture. It prevents causal precision as Qor begins ingesting requirement, model, evaluator, operational, and governance divergence.

### Treat every failure as a Shadow Genome pattern

Rejected. Events and durable learned patterns are different things.

## Follow-on work

Before implementation:

1. inventory all current Shadow Genome writers/readers/schemas/views;
2. map existing event families to the candidate spectrum without changing history;
3. adversarially review whether the seven candidate shades are minimal and non-overlapping enough;
4. design backward-compatible classification fields or a projection model;
5. determine threshold/escalation behavior per shade and cross-shade pattern;
6. reconcile `/qor-remediate`, review doctrine, and countermeasure doctrine;
7. define stale-governance and supersession-shadow events;
8. verify the public/proprietary boundary;
9. add migration tests before any schema change.

No schema or persistence change is authorized by this proposed ADR until formal `/qor-audit` and a governed plan.