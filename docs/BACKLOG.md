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

- [x] [B13] Encode AI code quality doctrine into QorLogic governance (Complete — doctrine-code-quality.md, audit checklist + implement patterns updated)

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

**All original backlog items (B1-B12) and all blockers (D1-D3) are COMPLETE.**

- [x] [B13] Encode AI code quality doctrine (Complete — doctrine-code-quality.md, audit checklist + implement patterns updated)

All backlog items complete. Repository fully operational.

## Queued for Next Branch (Phase 25 candidate)

- [x] [B14] (v0.16.0 - Complete) **Seed workspace scaffolding**: delivered as `qorlogic seed` top-level subcommand in Phase 25 Phase 1. Idempotent, pure scaffold, templates in `qor/templates/`. See `qor/seed.py`.
- [x] [B15] (v0.16.0 - Complete) **Prompt resilience**: delivered in Phase 25 Phases 2+3. Doctrine at `qor/references/doctrine-prompt-resilience.md`, canonical templates at `qor/references/skill-recovery-pattern.md`, lint at `tests/test_prompt_resilience_lint.py`, coverage at `tests/test_skill_prerequisite_coverage.py`. Autonomy classification (autonomous / interactive) landed on 11 skills. YAML discipline widened to `tests/**/*.py`.

Raised by user during Phase 24 substantiation (2026-04-17). Drives Phase 25 plan.

- [x] [B16] **Tiered communication complexity** -- folded into Phase 25 Phase 4 during audit-VETO amendment (2026-04-17 user direction: "proceed with all suggestions and add that direction to this plan"). See `docs/plan-qor-phase25-prompt-resilience-and-seed.md` Phase 4.

- [x] [B17] (v0.17.0 - Complete) **Audit-report language clarity**: delivered in Phase 26 Phase 2. Doctrine at `qor/references/doctrine-audit-report-language.md`, template updated, qor-audit SKILL.md passes each carry `**Required next action:**` directives.

- [x] [B18] (v0.17.0 - Complete) **Repeated-VETO auto-suggest**: delivered in Phase 26 Phase 1. Detector `qor/scripts/veto_pattern.py`, threshold = ">= 2 consecutive sealed phases where audit required >1 pass", emits severity-3 `repeated_veto_pattern` Shadow Genome event, surfaces advisory in AUDIT_REPORT.

Raised by user during Phase 25 audit-pass-2 remediation (2026-04-17).

---

_Updated by /qor-* commands automatically_
