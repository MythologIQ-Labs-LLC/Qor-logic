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

- [ ] [B14] **Seed workspace scaffolding on install**: after `qorlogic install`, optionally seed the minimum repo file structure the installed skills/prompts require to operate (e.g., `docs/META_LEDGER.md`, `docs/SHADOW_GENOME.md`, `.agent/staging/`, `.qor/gates/`). Gate behind a flag such as `--seed` so existing workspaces are not overwritten.
- [ ] [B15] **Prompt resilience**: harden skill prompts against missing-file / first-run conditions. Skills currently assume governance artifacts exist; when they do not (fresh install, partial workspace), the skill should either self-heal the missing scaffold or emit a clear prerequisite error naming the missing path(s). Audit all `/qor-*` skills for hard assumptions on file existence.

Raised by user during Phase 24 implementation (2026-04-17). Drives Phase 25 plan.

---

_Updated by /qor-* commands automatically_
