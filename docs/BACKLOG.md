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

- [ ] [B17] **Audit-report language clarity (skill-selection affordance)**: the `AUDIT_REPORT.md` template currently uses a generic "Mandated Remediation" header for every VETO. This creates a skill-selection ambiguity: operators read "Mandated Remediation" and reach for `/qor-remediate`, but that skill is for process-level failures (repeated gate overrides, SG threshold breach, systemic regression), not plan-text fixes. Phase 26 should:
  1. Replace the generic header with a per-ground skill directive. Each VETO ground in an AUDIT_REPORT names exactly which skill (if any) is the correct next action:
     - Code-shape ground -> "Invoke `/qor-refactor`"
     - Project-topology ground -> "Invoke `/qor-organize`"
     - Plan-text ground -> "Governor: amend plan text (no skill required); re-run `/qor-audit`"
     - Process-level / systemic -> "Invoke `/qor-remediate`"
  2. Update `qor/skills/governance/qor-audit/references/qor-audit-templates.md` accordingly so every future audit report inherits the clearer directive.
  3. Audit existing AUDIT_REPORT.md history for the generic phrase and note in `doctrine-governance-enforcement.md` that legacy reports use the ambiguous wording.

- [ ] [B18] **Repeated-VETO auto-trigger for `/qor-remediate`**: Phases 24 and 25 each required multiple audit passes (Phase 24: three, Phase 25: ongoing). Repeated VETOs on plans authored by the same Governor within a session may fit the "regression pattern across multiple implement/substantiate cycles" criterion from `qor-remediate`'s purpose statement. Phase 26 should:
  1. Define a concrete threshold (e.g., >= 3 plan-text VETOs on the same plan file, OR >= 2 consecutive phases requiring > 1 audit pass).
  2. Emit a Shadow Genome event when the threshold crosses, with `event_type: repeated_veto_pattern`.
  3. Auto-suggest `/qor-remediate` in the next AUDIT_REPORT when the threshold is crossed (surfacing as a "Pattern detected" note, not a VETO).

Raised by user during Phase 25 audit-pass-2 remediation (2026-04-17).

---

_Updated by /qor-* commands automatically_
