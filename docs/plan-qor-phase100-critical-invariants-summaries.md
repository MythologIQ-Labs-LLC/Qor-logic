# Plan: Phase 100 — Critical Invariants summaries (F4)

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: F4 (internal prompt-surface review)

**boundaries**:
- limitations: V1 adds a top-level `## Critical Invariants` summary
  block to two binding-gate skills (qor-audit, qor-substantiate)
  between the `## Purpose` and `## Environment` sections. Each block
  is ~10 lines listing the inviolable contracts (ABORT/VETO conditions)
  with pointers to the detail step numbers. Adds structural tests
  asserting each binding-gate skill in `governance/` carries an
  invariants block.
- non_goals: rewriting the underlying ABORT/VETO logic; adding new
  invariants; extending to non-governance skills (sdlc/memory/meta
  skills mostly do not carry binding gates); reformatting the existing
  Constraints sections at the foot of each SKILL.md.
- exclusions: no changes to step-level prose; no changes to existing
  Step 0.6 audit lints, Step 4.6.* substantiate gates, Step 3 pass
  semantics; no changes to Phase 99 Runtime Contract Walk wiring
  (the V2 walk is WARN-only, NOT a binding VETO — the invariants
  block correctly omits it from the inviolable list while noting it
  as a pending V2-of-V2 surface).

## Open Questions

None.

## Feature Inventory Touches

Empty. Skill-prose addition + structural test.
`feature_inventory_touches`: `[]`.

## Design notes

F4 of the internal prompt-surface review documented that two binding-
gate skills (qor-audit, qor-substantiate) lack a consolidated top-
level summary of what cannot be violated. The ABORT/VETO conditions
are scattered across steps and end-of-file Constraint sections; an
operator skimming the file or an LLM with truncated context sees
Steps 0 → 1 → 2 → ... without ever seeing a consolidated list.

**Cross-coupling constraint operative** (per meta-memo): Phase 100
must follow Phase 99 V2 so the invariants block can correctly
represent the V2 walk as a NEW Step 3 sub-pass — but explicitly NOT
as a binding VETO at first rollout (the V2 ramp is WARN-only).
Phase 100 captures the correct framing from authoring time, avoiding
the amendment cycle.

**qor-audit Critical Invariants** (~10 lines + cross-ref paragraph):

The binding contracts the Judge cannot violate:
1. Step 0.3 plan-iteration lint failure → ABORT.
2. Step 3 Prompt Injection Pass failure → ABORT.
3. Step 3 L3 VETO conditions (security, financial, compliance, etc.).
4. Step 3 OWASP Top-10 violation → VETO.
5. Step 3 Ghost-UI / Razor / self-application violation → VETO.
6. Step 3 Test Functionality Pass violation → VETO (Phase 79).
7. Step 3 Filter-Stage Pass violation → VETO.
8. Step 3 Infrastructure Alignment Pass violation → VETO with
   `infrastructure-mismatch` category.
9. Step 3 Feature Test Declaration Pass violation → VETO with
   `feature-test-undeclared` category.

Note: the Phase 99 Runtime Contract Walk at Step 3 is NEW but ships
WARN-only in V2; it is NOT yet on the binding-VETO list and will
join only after V2-of-V2 (post-evidence) flips the ramp.

**qor-substantiate Critical Invariants** (~10 lines + cross-ref paragraph):

The binding contracts the Judge cannot violate:
1. Step 4.6.* reliability gates (intent-lock, secret-scanner,
   procedural-fidelity, ci-coverage, dod-check, merge-velocity,
   skill-corpus-budget) → non-zero exit aborts substantiate.
2. Step 6.5 README badge currency check → `|| ABORT`.
3. Step 7.8 gate-chain completeness check → `|| ABORT`.
4. Constraints section at end of file (post-batch-1 inventory).

**Structural countermeasure test**:

`tests/test_governance_skills_carry_critical_invariants_block.py`
asserts every SKILL.md under `qor/skills/governance/` that carries
ABORT/VETO conditions in its step prose ALSO carries a top-level
`## Critical Invariants` block. The sweep is forward-only: future
governance skills must adopt the same discipline. Catches the
inverse F4 defect (a future binding-gate skill ships without a
summary block).

## Phase 1: invariants blocks + structural sweep

### Affected Files

- `qor/skills/governance/qor-audit/SKILL.md` — add
  `## Critical Invariants` between `## Purpose` and
  `## Environment (Phase 90 wiring; GH #79)`. ~10-line summary +
  cross-reference paragraph + note on V2 WARN ramp.
- `qor/skills/governance/qor-substantiate/SKILL.md` — same structural
  insertion at the same position. ~10-line summary + cross-reference
  paragraph.
- `tests/test_governance_skills_carry_critical_invariants_block.py`
  — NEW. Three assertions: qor-audit has block; qor-substantiate
  has block; forward-only sweep covering future governance skills
  (any governance/*/SKILL.md containing `VETO` or `ABORT` in step
  prose must carry `## Critical Invariants`).
- `docs/plan-qor-phase100-critical-invariants-summaries.md` — NEW.
  This plan.

### Unit Tests

- `tests/test_governance_skills_carry_critical_invariants_block.py`
  - `test_qor_audit_carries_critical_invariants_block` — anchored
    positive: qor-audit SKILL.md contains `## Critical Invariants`
    section + the V2 ramp framing note.
  - `test_qor_substantiate_carries_critical_invariants_block` —
    anchored positive: qor-substantiate SKILL.md contains
    `## Critical Invariants` section.
  - `test_critical_invariants_block_positioned_before_environment`
    — positional guard: the block appears BEFORE the Environment
    section in both files (top-level anchor placement).
  - `test_governance_skills_with_veto_carry_invariants_block` —
    forward-only sweep: any governance/*/SKILL.md whose step prose
    contains `VETO` or `ABORT` keywords carries
    `## Critical Invariants`. Catches future drift.

### Changes

Each skill's `## Critical Invariants` block (positioned between
`## Purpose` and `## Environment`):

```markdown
## Critical Invariants

The binding contracts /qor-X cannot violate. ABORT halts the skill;
VETO returns the work to /qor-plan or /qor-remediate.

- [1] <inviolable 1> -> ABORT/VETO
- [2] <inviolable 2> -> ABORT/VETO
...

V2 ramp note (qor-audit only): the Phase 99 Runtime Contract Walk
ships WARN-only at Step 3 Infrastructure Alignment; it is NOT yet a
binding VETO. A V2-of-V2 phase will gather Phase 96 V1 operator-
evidence on false-positive rate, then flip the walk's WARN to hard
VETO with `runtime-contract-mismatch` category.

See <step-level prose / Constraints section> for the detail.
```

## Definition of Done

### Deliverable: qor-audit Critical Invariants block

- **D1**: qor-audit/SKILL.md carries a top-level `## Critical Invariants` section between Purpose and Environment.
- **D2**: The block enumerates the 9 inviolable Step 0.3 / Step 3 ABORT/VETO conditions, includes the V2 WARN-ramp framing note, and cross-references the step-level prose.
- **D3**: Plan + ledger + SYSTEM_STATE Phase 100 entry seal.
- **D4**: `tests/test_governance_skills_carry_critical_invariants_block.py` carries `test_qor_audit_carries_critical_invariants_block` + the positional guard; both pass.

### Deliverable: qor-substantiate Critical Invariants block

- **D1**: qor-substantiate/SKILL.md carries a top-level `## Critical Invariants` section between Purpose and Environment.
- **D2**: The block enumerates the Step 4.6.* / Step 6.5 / Step 7.8 binding contracts and cross-references the Constraints section at file foot.
- **D3**: Plan + ledger entry cover the addition.
- **D4**: `test_qor_substantiate_carries_critical_invariants_block` + positional guard pass.

### Deliverable: forward-only structural sweep

- **D1**: A sweep test exists that prevents future governance skills from shipping with ABORT/VETO step prose but no top-level invariants block.
- **D2**: `test_governance_skills_with_veto_carry_invariants_block` walks `qor/skills/governance/*/SKILL.md`, checks for `VETO`/`ABORT` keywords in step prose, and asserts a `## Critical Invariants` block exists when keywords are present.
- **D3**: Plan + ledger seal.
- **D4**: All four tests pass twice deterministically; the sweep is the structural countermeasure preventing F4-class drift in future governance skill additions.

## CI Coverage Exemptions

None.

## CI Commands

- `python -m pytest tests/test_governance_skills_carry_critical_invariants_block.py -q` — Phase 100 structural tests.
- `python -m pytest tests/ -v` — full regression.
- `python qor/scripts/check_variant_drift.py` — ci.yml.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ci.yml.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — install-smoke.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — gate-chain.
- `python qor/scripts/pr_citation_lint.py` — pr-lint.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase100-critical-invariants-summaries.md` — plan-internal.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase100-critical-invariants-summaries.md --workflows-dir .github/workflows` — Phase 89 ci-coverage.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase100-critical-invariants-summaries.md` — Phase 92 DoD check.
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` — Phase 95 skill-corpus-budget lint (WARN-only).
