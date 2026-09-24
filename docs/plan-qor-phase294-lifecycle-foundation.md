# Plan: Phase 294 - Governed Development Lifecycle Foundation

**Issue:** GH #497, with QA/environment semantics from GH #502
**change_class**: feature
**Status:** current-base doctrine slice prepared; formal `/qor-audit` required before promotion

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

## Provenance note

This is the current-base recomposition of the doctrine work previously reviewed in superseded draft PR #503. The prior promotion vehicle was closed because it was stale and mechanically red. Historical Phase 288 evidence is not reused as current promotion authority. The doctrine content that remains applicable is reintroduced here on current `main` under fresh Phase 294 identity and must earn fresh CI and formal audit evidence.

## Authorized changes

1. Add `qor/references/doctrine-governed-development-lifecycle.md`.
2. Add `qor/references/doctrine-development-environments-and-qa.md`.
3. Register both in `docs/GOVERNANCE_INDEX.md`.
4. Record this phase as the active initiative in the Governance Index.
5. Reconcile README doctrine inventory and generated doctrine count for the two additions.
6. Create a focused draft PR for adversarial audit and review before merge.

## Locked decisions

### LD-1: inner loop vocabulary

The candidate implementation loop is:

`inspect -> choose authorized work -> implement -> exercise -> observe -> verify -> reconcile -> reassess -> CONTINUE | PASS | ESCALATE | ABORT`

Rationale: this preserves the useful original implementation rhythm while separating evidence generation from evidence interpretation and preventing selection/reassessment from implying new authority.

### LD-2: full lifecycle vocabulary

The candidate full lifecycle is:

`UNDERSTAND -> DECIDE -> AUTHORIZE -> EXECUTE -> PROVE -> QA / ACCEPT -> PROMOTE -> OBSERVE -> ADAPT`

This is a **claim progression and semantic ordering of assurance claims**, not a mandatory runtime execution sequence, universal gate order, or one-to-one mapping to skills. Profiles/applicability may lawfully omit, collapse, repeat, or interleave stages where appropriate, but an omitted, deferred, collapsed, or inapplicable stage must never be represented as PASS merely because work advanced.

The current operational skill/gate and QA ordering remains authoritative unless and until a separately audited enforcement change modifies it. This doctrine-only phase therefore does not establish `PROVE -> QA / ACCEPT` as a universal runtime order or introduce any new gate.

### LD-3: QA is distinct from automated verification

Human QA is profile-dependent and required where acceptability depends on experiential, tacit, subjective, visual, interaction, operator, or stakeholder judgment.

Agent-generated observations may prepare QA evidence but must not be represented as human QA.

### LD-4: environment classes are conceptual, not mandatory infrastructure

Qor recognizes `development`, `test`, `preview`, `staging`, and `production` as assurance classes.

Consumers may intentionally collapse classes, but must not silently claim equivalence when it affects assurance.

### LD-5: no premature enforcement

This phase is doctrine-only.

No current skill, schema, QA gate, release path, or policy is changed until the semantics survive formal audit.

### LD-6: publication-boundary scope of this seal

This phase's own tracked content carries no outside-repository identity term: the plan's last non-goal names the downstream composition target generically, and the audit report and gate artifacts are written without the term.

Two sealed plans already on `main` (`docs/plan-qor-phase291-recompose-reconcile-dialect-accessor.md`, `docs/plan-shadow-escalation-origin-signature-current.md`) and their tracked intent-lock plan snapshots carry such a term. They are out of scope here. The Phase 292 plan's bytes are bound by `qor/reliability/intent_lock_committed.py` (CI: `git show 8968bb5f:.github/workflows/ci.yml | grep -n 'intent_lock_committed'` -> `run: python -m qor.reliability.intent_lock_committed --phase-min 231`) through its intent-lock record (`git show 8968bb5f:.qor/intent-lock/2026-09-23T1628-c67a6a.json | grep -n plan_hash` -> `"plan_hash": "bfec0225d22a22784785e6dec0da8ccdc42ea9a438f2ecbbd2f166271f3649c7"`), so removing the term from sealed evidence is a re-attestation design problem for its own phase (audit iter-3 VETO, Shadow Genome entry #35).

At substantiate Step 4.6.14 the seal records `boundary_scope: structural` (the scope CI runs, since the identity overlay is gitignored) as the gating result. It also runs `structural+identity` locally and discloses that result in the SESSION SEAL entry: the two pre-existing sealed-plan findings, attributed to `main`, not introduced by this phase, and with no identity finding in any path this phase touches. The disclosure names the paths and does not quote the term.

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

## CI Commands

```bash
python -m pytest tests/test_plan_schema_ci_commands.py tests/test_skill_doctrine.py tests/test_readme_doctrine_inventory.py -v
python -m pytest tests/ -v
python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .
python -m ruff check qor/ tests/
python -m qor.scripts.publication_boundary_lint --repo-root .
```

These commands verify the plan contract, doctrine inventory, full behavioral suite, generated seal-artifact currency, Python lint, and publication boundary. Formal `/qor-audit` remains a separate required governance verdict and is not replaced by CI.

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
- [x] README doctrine inventory/count reconciled for the two doctrine additions.
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
- migrating work into a downstream composition repository.

## Follow-on slices after PASS

Subject to #497 sequencing and audit findings:

1. reconcile `docs/lifecycle.md`, review/self-audit docs, and delegation semantics;
2. audit and evolve `qa_evidence.py` and QA schemas against the human-QA evidence contract;
3. implement typed lifecycle/acceptance states where they produce material safety or clarity;
4. implement governed attention/applicability from #501;
5. integrate two-gap assurance/evidence invalidation from #498;
6. integrate Shadow Spectrum metadata only after applicability routing exists;
7. add operational/outer-loop handoffs without turning Qor into the runtime platform.
