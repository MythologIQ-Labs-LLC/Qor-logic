# Plan: Phase 288 - Governed Development Lifecycle Foundation

**Issue:** GH #497, with QA/environment semantics from GH #502
**change_class:** feature
**Status:** implementation slice prepared; formal `/qor-audit` required before promotion

## Problem contract

Qor's operational gate chain is mature, but the canonical lifecycle vocabulary still compresses several distinct concepts and does not clearly distinguish the full governed-development lifecycle from the inner implementation loop.

The ambiguity creates several risks:

- `test` may be mistaken for complete verification;
- `render` is treated as UI-specific rather than one observation mode;
- `select` can imply unauthorized scope/architecture choice;
- `reassess` can silently expand authority;
- `/qor-validate` can be misunderstood as generic product/runtime acceptance;
- automated verification can be mistaken for human QA;
- development/test/preview/staging/production environment differences are not canonically modeled;
- `implemented`, `verified`, `accepted`, `released`, and `deployed` can be described as if they were equivalent completion states.

## Objective

Establish a doctrine-only semantic foundation that later implementation slices can safely enforce.

This phase does not rename skills, change gate schemas, change release authority, add an acceptance skill, or alter runtime behavior.

## Authorized changes

1. Add `qor/references/doctrine-governed-development-lifecycle.md`.
2. Add `qor/references/doctrine-development-environments-and-qa.md`.
3. Register both in `docs/GOVERNANCE_INDEX.md`.
4. Record this phase as the active initiative in the Governance Index.
5. Create a focused PR for adversarial audit and review before merge.

## Locked decisions

### LD-1: inner loop vocabulary

The candidate implementation loop is:

`inspect -> choose authorized work -> implement -> exercise -> observe -> verify -> reconcile -> reassess -> CONTINUE | PASS | ESCALATE | ABORT`

Rationale: this preserves the useful original implementation rhythm while separating evidence generation from evidence interpretation and preventing selection/reassessment from implying new authority.

### LD-2: full lifecycle vocabulary

The candidate full lifecycle is:

`UNDERSTAND -> DECIDE -> AUTHORIZE -> EXECUTE -> PROVE -> QA / ACCEPT -> PROMOTE -> OBSERVE -> ADAPT`

These are semantic stages, not one-to-one skill names.

### LD-3: QA is distinct from automated verification

Human QA is profile-dependent and required where acceptability depends on experiential, tacit, subjective, visual, interaction, operator, or stakeholder judgment.

Agent-generated observations may prepare QA evidence but must not be represented as human QA.

### LD-4: environment classes are conceptual, not mandatory infrastructure

Qor recognizes `development`, `test`, `preview`, `staging`, and `production` as assurance classes.

Consumers may intentionally collapse classes, but must not silently claim equivalence when it affects assurance.

### LD-5: no premature enforcement

This phase is doctrine-only.

No current skill, schema, QA gate, release path, or policy is changed until the semantics survive formal audit.

## Evidence strategy

This phase should be reviewed for:

- contradiction with `docs/lifecycle.md` operational chain semantics;
- contradiction with `qor/gates/delegation-table.md`;
- unintended authority creation;
- mandatory staging/QA ceremony for inapplicable changes;
- accidental redefinition of `/qor-validate`;
- duplicate ownership with existing QA evidence machinery;
- documentation freshness and Governance Index consistency;
- terminology that would make current historical evidence false retroactively.

## Acceptance criteria

- [x] Full lifecycle and inner loop are explicitly separated.
- [x] `select` is narrowed to choosing authorized work.
- [x] `test/render` generalize to `exercise -> observe -> verify` without removing visual inspection requirements.
- [x] `reassess` is typed and does not create authority.
- [x] universal outcomes include CONTINUE/PASS/ESCALATE/ABORT.
- [x] verification/substantiation/integrity attestation/acceptance are distinguished.
- [x] merge/release/publish/deploy/activate are declared non-equivalent.
- [x] environment classes and fidelity limits are defined.
- [x] human QA is distinct from agent/automated verification.
- [x] QA debt is represented as a lifecycle concern without prematurely adding machine state.
- [x] no new runtime enforcement is introduced in this slice.
- [ ] formal `/qor-audit` PASS.
- [ ] documentation conflict sweep after audit findings.
- [ ] promotion through normal substantiation/release path.

## Explicit non-goals

- adding `/qor-accept`;
- renaming `/qor-validate`;
- introducing a deployment platform;
- requiring dedicated staging infrastructure for every consumer;
- adding Shadow Spectrum schema fields;
- implementing governed attention/applicability resolution;
- changing current gate chain ordering;
- migrating work into Qortara Logic.

## Follow-on slices after PASS

Subject to #497 sequencing and audit findings:

1. reconcile `docs/lifecycle.md`, review/self-audit docs, and delegation semantics;
2. audit and evolve `qa_evidence.py` and QA schemas against the human-QA evidence contract;
3. implement typed lifecycle/acceptance states where they produce material safety or clarity;
4. implement governed attention/applicability from #501;
5. integrate two-gap assurance/evidence invalidation from #498;
6. integrate Shadow Spectrum metadata only after applicability routing exists;
7. add operational/outer-loop handoffs without turning Qor into the runtime platform.
