# Project Backlog

## Blockers (Must Fix Before Progress)

### Development Blockers
- [x] [D1] Import existing QL skills from FailSafe extension into ingest/internal/ (Complete)
- [x] [D2] Create processing script that normalizes skills to S.H.I.E.L.D. format (Complete — scripts/process-skills.py)
- [x] [D3] Create qor-document skill (Complete — ingest/internal/governance/qor-document.md)

## Backlog (Planned Work)
- [x] [B1] Import all existing qor-* skills from G:/MythologIQ/FailSafe/.claude/commands/ (Complete)
- [x] [B2] Create compilation script for Claude Code format (Complete — scripts/compile-claude.py)
- [x] [B3] Create compilation script for Agent workflow format (Complete — scripts/compile-agent.py)
- [x] [B4] Process collaborative design principles into qor-plan and qor-bootstrap (Complete)
- [x] [B5] Create qor-course-correct skill (Complete — Navigator persona, 190 lines)
- [x] [B6] Identify and fill skill gaps for e2e autonomous building (Complete — all gaps filled)
- [x] [B7] Create skill quality audit checklist (Complete — docs/SKILL_AUDIT_CHECKLIST.md)
- [x] [B8] Create qor-fixer subagent definition (Complete — 4-layer methodology, 122 lines)
- [x] [B9] Reliability scripts (Complete — intent-lock.py, admit-skill.py, gate-skill-matrix.py)
- [x] [B10] Create SKILL_REGISTRY.md — comprehensive index of all content (Complete)
- [x] [B11] Consolidate utility skills — archive, merge, distill (Complete)
- [x] [B12] Wire qor-document → qor-technical-writer subagent dispatch (Complete)

- [x] [B13] Encode AI code quality doctrine into Qor-logic governance (Complete — doctrine-code-quality.md, audit checklist + implement patterns updated)

## Lifecycle Coverage

```
ALIGN → ENCODE → PLAN → GATE → IMPLEMENT → SUBSTANTIATE → DELIVER
  ✓        ✓       ✓      ✓       ✓            ✓           ✓
```
Cross-cutting: RESEARCH ✓, DEBUG ✓, STATUS ✓, VALIDATE ✓, ORGANIZE ✓, RECOVER ✓

**All persona gaps filled. All lifecycle phases covered.**

## Subagent Pairings

| Governance Skill | Subagent | Status |
|-----------------|----------|--------|
| qor-debug | qor-fixer | PAIRED |
| qor-document | qor-technical-writer | PAIRED |
| qor-audit | (parallel-auditor) | PROPOSED |
| qor-implement | (test-writer) | PROPOSED |
| qor-substantiate | (verification-auditor) | PROPOSED |

## Inventory

Inventory maintained live in the repo tree; see `qor/skills/`, `qor/references/`, `qor/agents/`, `qor/scripts/`, `qor/experimental/`. Use `find qor -name SKILL.md` or equivalent to enumerate at the current HEAD.

## Remaining Work

**All original backlog items (B1-B18) and all blockers (D1-D3) are COMPLETE.**

All backlog items complete. Repository fully operational.

## Queued for Next Branch (Phase 25 candidate)

- [x] [B14] (v0.16.0 - Complete) **Seed workspace scaffolding**: delivered as `qorlogic seed` top-level subcommand in Phase 25 Phase 1. Idempotent, pure scaffold, templates in `qor/templates/`. See `qor/seed.py`.
- [x] [B15] (v0.16.0 - Complete) **Prompt resilience**: delivered in Phase 25 Phases 2+3. Doctrine at `qor/references/doctrine-prompt-resilience.md`, canonical templates at `qor/references/skill-recovery-pattern.md`, lint at `tests/test_prompt_resilience_lint.py`, coverage at `tests/test_skill_prerequisite_coverage.py`. Autonomy classification (autonomous / interactive) landed on 11 skills. YAML discipline widened to `tests/**/*.py`.

Raised by user during Phase 24 substantiation (2026-04-17). Drives Phase 25 plan.

- [x] [B16] **Tiered communication complexity** -- folded into Phase 25 Phase 4 during audit-VETO amendment (2026-04-17 user direction: "proceed with all suggestions and add that direction to this plan"). See `docs/plan-qor-phase25-prompt-resilience-and-seed.md` Phase 4.

- [x] [B17] (v0.17.0 - Complete) **Audit-report language clarity**: delivered in Phase 26 Phase 2. Doctrine at `qor/references/doctrine-audit-report-language.md`, template updated, qor-audit SKILL.md passes each carry `**Required next action:**` directives.

- [x] [B18] (v0.17.0 - Complete) **Repeated-VETO auto-suggest**: delivered in Phase 26 Phase 1. Detector `qor/scripts/veto_pattern.py`, threshold = ">= 2 consecutive sealed phases where audit required >1 pass", emits severity-3 `repeated_veto_pattern` Shadow Genome event, surfaces advisory in AUDIT_REPORT.

Raised by user during Phase 25 audit-pass-2 remediation (2026-04-17).

## Queued for post-Phase-35 (SG-PlanAuditLoop-A countermeasures)

Source: `docs/SHADOW_GENOME.md` Entry #26. Raised by operator postmortem 2026-04-19. Rescope proposal accepted by operator 2026-04-20 (META_LEDGER Entry #122); original Phase 36 plan (`docs/plan-qor-phase36-planaudit-loop-countermeasures.archived.md`) retained as investigation record.

### Phase 36 — B19 only (two-stage addressed flip)

- [x] **[B19] (v0.26.0 — Complete)** Two-stage addressed flip in `/qor-remediate`. Schema: `addressed_pending` optional field with `allOf` invariant enforcing `addressed == true AND addressed_reason == "remediated"` implies `addressed_pending == true`. Refactor: `mark_addressed_pending` (stage 1) + `mark_addressed(review_pass_artifact_path, remediate_gate_path)` (stage 2) with `_flip_event_fields` helper; `ReviewAttestationError` raised on verification failure. Skill prose: `/qor-remediate` Step 4 calls pending variant; new Step 6 documents review-pass flip invoked by `/qor-audit`. `/qor-audit` Step 4.1 captures `reviews-remediate:<path>` operator arg, Step 4.2 invokes `mark_addressed` on PASS with signal. Audit schema gains optional `reviews_remediate_gate` field. Doctrine §10.1 (two-stage flip) + §10.2 (SG narrative closure protocol). 15 new tests across `test_shadow_event_schema.py` (5) + `test_remediate.py` (10); 3 existing `test_mark_addressed_*` updated to pending-stage API. **Plan**: `docs/plan-qor-phase36-remediate-two-stage-flip.md`. Green on 654 tests across 2 consecutive runs.

### Phase 37 — stall-detection infrastructure (B20 + B21)

- [x] **[B20] (v0.27.0 — Complete)** Audit history append-only log. `qor/scripts/audit_history.py` + `gate_chain.write_gate_artifact` hook writes `.qor/gates/<sid>/audit_history.jsonl` alongside singleton `audit.json`. Solves V10 from original Phase 36 plan.
- [x] **[B20b] (v0.27.0 — Complete)** `findings_categories` closed 12-value enum + `allOf` required-on-VETO in `audit.schema.json`. `qor/scripts/findings_signature.py` computes 16-hex-char prefix over sorted unique categories; LEGACY sentinel for absent field. `UnmappedCategoryError` raised at emission. `/qor-audit` SKILL.md carries the audit-pass → category mapping discipline.
- [x] **[B21] (v0.27.0 — Complete)** `qor/scripts/stall_walk.py` (shared walker), `cycle_count_escalator.py` (K=3 orchestrator), `orchestration_override.py` (decline handler with session-scoped suppression marker). gate-loop classifier unions `gate_override | orchestration_override`. `/qor-plan` Step 2c + `/qor-audit` Step 0.5 cycle-count hooks. `/qor-audit` gains 7th Infrastructure Alignment Pass (catches V10-class findings at audit time; `infrastructure-mismatch` finding category). Delegation-table rows + doctrine §10.3-10.5 + `SG-InfrastructureMismatch` in shadow-genome-countermeasures catalog.

### Phase 38 — `ci_commands` schema slot (B22)

- [x] **[B22] (v0.28.0 — Complete)** `ci_commands` required field added to `qor/gates/schema/plan.schema.json` (minItems 1, item minLength 1). `/qor-plan` SKILL.md §Plan Structure template carries `## CI Commands` section. Grandfathering at test layer (phase < 38 skipped). 9 test fixtures updated to include `ci_commands` in plan payloads. `tests/test_plan_schema_ci_commands.py` NEW (6 tests). 711 tests green x2.

### Phase 39 — context-discipline doctrine + persona reshape

- [x] **Phase 39 Phase 1 (v0.29.0 — Complete)** `qor/references/doctrine-context-discipline.md` authored with 5 sections (three mechanisms, persona-as-scaffold, stance directive discipline, subagent invocation rule, verification protocol). `doctrine-governance-enforcement.md` §11 cross-references.
- [x] **Phase 39 Phase 2 (v0.29.0 — Complete, scope narrowed)** A/B corpus fixtures retained: 20 defects across 10 categories + MANIFEST + 4 hand-authored variant files under `tests/fixtures/ab_corpus/`. Anthropic-SDK harness withdrawn (required API key + $32/cycle external cost). Agent Team orchestration moves to Phase 39b.

### Phase 39b — Agent Team A/B + persona sweep

- [x] **Phase 39b Phase 1 (v0.30.0 — Complete)** `/qor-ab-run` skill at `qor/skills/meta/qor-ab-run/SKILL.md` orchestrates A/B via parallel Task-tool subagent dispatch. `qor/scripts/ab_aggregator.py` provides pure-Python reduction (parse, group, mean/stddev, winner declaration, markdown rendering). Subagent prompt template at `qor/skills/meta/qor-ab-run/references/ab-subagent-prompt.md`. Delegation-table row added. `qor-help` catalog updated. 22 tests across `test_qor_ab_run_skill.py` and `test_ab_aggregator.py`.
- [x] **Phase 39b Phase 2 (v0.30.0 — Complete)** S3 decorative sweep: 5 tags removed (`qor-status`, `qor-help`, `qor-repo-scaffold`, `qor-bootstrap`, `qor-document`). R4: `qor-debug` line 108 constraint cross-references `doctrine-context-discipline.md` §4. R5: `qor-document` splits Identity Activation stance from subagent pairing (cites doctrine §1.2/§1.3). `LOAD_BEARING_PENDING_EVIDENCE` registry in `tests/test_persona_sweep.py` documents 19 skills retained as load-bearing by doctrine judgment. 5 sweep tests enforce.

### Phase 58 — Procedural-fidelity check at /qor-substantiate (B23 — DONE)

- [x] **[B23] (v0.44.0 — Complete)** Procedural-fidelity check shipped at /qor-substantiate Step 4.6.6 via `qor/scripts/procedural_fidelity.py`. Phase 58 v1 ships the `doc-surface-uncovered` detector (skill/script/doctrine/schema changes without at least one system-tier doc update); `missing-step`/`ordering-drift`/`argv-shape-divergence` reserved as stubs for future phases. WARN posture; severity-2 events append to Process Shadow Genome. Plus SYSTEM_STATE.md backfill (12 phases) + forward-only drift-prevention test. Doctrine: `qor/references/doctrine-procedural-fidelity.md`. SG: `SG-DocSurfaceUncovered-A`. Original B23 description below for historical reference.

  Original request: Add a required output to `/qor-substantiate` that performs a literal 1-to-1 procedural check: for every component touched by the seal commit AND every step of every called function in the implement gate's `files_touched`, verify the step was followed exactly as the plan / doctrine / skill prose specifies. Any deviations (skipped step, reordered step, swallowed precondition, divergent argument shape, etc.) are written as severity-3 events to the Process Shadow Genome (`docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`) and surfaced in the seal report.
  - **Why**: Phase 57 self-audit revealed silent doc-update gaps (SYSTEM_STATE, operations.md, architecture.md were not updated until the operator pointed it out, even though substantiate Step 6 mandates SYSTEM_STATE update). A procedural-fidelity check at seal time would catch these structurally rather than relying on operator review.
  - **Scope hints**: AST-based traversal of called functions; step-by-step diff against skill prose; whitelist of "may-skip" steps. Likely lives in `qor/scripts/procedural_fidelity.py` invoked at substantiate Step 4.6.6 (between Step 4.6.5 secret-scan and Step 4.7 doc integrity).
  - **Deviation classification**: each deviation gets a `severity`, a `step_id`, a `reason` (operator-provided or "auto-detected"), and an `addressed` boolean. Deviations not addressed by the next seal cycle escalate.
  - **Source incident**: Phase 57 substantiate (2026-05-01) — operator manually identified the doc-update gap (`SYSTEM_STATE.md` not updated, `operations.md` not updated, `architecture.md` not updated for Phase 57 surface). Substantiate completed and sealed; gaps caught only on user review of the PR.
  - **Plan target**: future `docs/plan-qor-phase59-procedural-fidelity-check.md` (or whatever next-available phase number is when this gets prioritized). Should be a `change_class: feature` plan; `doc_tier: standard`; introduces 2-3 glossary terms (`procedural-fidelity check`, `procedural deviation`, possibly `procedural deviation severity`).

### Phase 60+ wishlist (post-Phase-59 future-phase work)

These items are tracked but not scheduled. Each is a deliberate future-phase reservation; none is imminent. Cite the relevant doctrine when scoping a real plan against any of them.

- [ ] **[B24] (proposed; future phase)** Procedural-fidelity v2 detectors: implement the three reserved stub classes in `qor/scripts/procedural_fidelity.py` (`missing-step`, `ordering-drift`, `argv-shape-divergence`). Phase 58 v1 shipped only `doc-surface-uncovered` active; the other three are stubs returning `[]`. Operator-observation-driven; lands when accumulated WARN events characterize specific failure-mode patterns worth structurally surfacing. Doctrine: `qor/references/doctrine-procedural-fidelity.md` §"Future extensions".

- [ ] **[B25] (proposed; future phase)** WARN → BLOCK escalation for `/qor-substantiate` Step 4.6.6 procedural-fidelity check. After accumulated WARN events characterize false-positive rate, tighten Step 4.6.6 from advisory WARN to fail-closed `|| ABORT` semantics matching Step 4.6.5 secret-scan. Phase 58 declared this as a future-phase decision per `qor/references/doctrine-procedural-fidelity.md`.

- [ ] **[B26] (proposed; future phase)** `qor-remediate` consumes ideation artifacts when repeated failures suggest the original concept was malformed. Codified in Phase 59 plan §exclusions and Issue #20 Open Question 6. Routing: when `/qor-remediate` detects K consecutive same-signature VETOs across phases, walk the session's `ideation.json` to identify which assumption may have been wrong rather than diving into code-level diagnosis. Requires extending `qor-remediate` skill body and adding ideation-aware detector to `qor/scripts/cycle_count_escalator.py` or a sibling.

- [ ] **[B27] (proposed; future phase)** Substantiate readiness check: tighten `/qor-substantiate` to verify `ideation.readiness.status == ready` for non-hotfix plans whose session has an `ideation.json` artifact. Phase 59 declared this as advisory-gate posture (no substantiate-time check); future phase makes it a substantiate-time gate. Hotfix exemption preserved.

- [ ] **[B28] (proposed; future phase)** Embedded-vs-inherited remediation routes. Currently `failure_remediation[]` lives in the ideation artifact only; downstream phases read it via prior-artifact lookup. Future phase decides whether plan/audit/implement artifacts should also embed the routes (with override semantics) or always inherit. Per Phase 58 plan §exclusions and Issue #20 Open Question 5.

- [ ] **[B29] (proposed; future phase)** Cross-link ideation predecessor in `qor-research` and `qor-plan` skill bodies. The `gate_chain.check_prior_artifact` helper accepts ideation as a valid prior since Phase 59, but the two skill bodies don't explicitly mention this in their Step 0 prose. Doc-only refresh; runtime behavior unchanged. Operators currently discover the new predecessor through `qor/gates/chain.md` and `qor/gates/delegation-table.md`.

---

_Updated by /qor-* commands automatically_
