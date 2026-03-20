# Project Backlog

## Blockers (Must Fix Before Progress)

### Development Blockers
- [x] [D1] Import existing QL skills from FailSafe extension into ingest/internal/ (Complete)
- [x] [D2] Create processing script that normalizes skills to S.H.I.E.L.D. format (Complete — scripts/process-skills.py)
- [x] [D3] Create ql-document skill (Complete — ingest/internal/governance/ql-document.md)

## Backlog (Planned Work)
- [x] [B1] Import all existing ql-* skills from G:/MythologIQ/FailSafe/.claude/commands/ (Complete)
- [x] [B2] Create compilation script for Claude Code format (Complete — scripts/compile-claude.py)
- [x] [B3] Create compilation script for Agent workflow format (Complete — scripts/compile-agent.py)
- [x] [B4] Process collaborative design principles into ql-plan and ql-bootstrap (Complete)
- [x] [B5] Create ql-course-correct skill (Complete — Navigator persona, 190 lines)
- [x] [B6] Identify and fill skill gaps for e2e autonomous building (Complete — all gaps filled)
- [x] [B7] Create skill quality audit checklist (Complete — docs/SKILL_AUDIT_CHECKLIST.md)
- [x] [B8] Create ql-fixer subagent definition (Complete — 4-layer methodology, 122 lines)
- [x] [B9] Reliability scripts (Complete — intent-lock.py, admit-skill.py, gate-skill-matrix.py)
- [x] [B10] Create SKILL_REGISTRY.md — comprehensive index of all content (Complete)
- [x] [B11] Consolidate utility skills — archive, merge, distill (Complete)
- [x] [B12] Wire ql-document → ql-technical-writer subagent dispatch (Complete)

- [ ] [B13] Encode AI code quality doctrine into QoreLogic governance. Add explicit guidance for semantic vs pragmatic functions, stronger model-shaping rules, and anti-slop guardrails inspired by Ben Swerdlow's AI coding write-up at https://aicode.swerdlow.dev/

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
| ql-debug | ql-fixer | PAIRED |
| ql-document | ql-technical-writer | PAIRED |
| ql-audit | (parallel-auditor) | PROPOSED |
| ql-implement | (test-writer) | PROPOSED |
| ql-substantiate | (verification-auditor) | PROPOSED |

## Final Inventory

| Category | Count | Location |
|----------|-------|----------|
| Governance skills | 17 | ingest/internal/governance/ — ALL COMPLIANT |
| Agent personas | 6 | ingest/internal/agents/ |
| Reference docs | 14 | ingest/internal/references/ (7 ql-templates + 7 patterns) |
| Utility skills | 4 | ingest/internal/utilities/ (meta-skills + generic) |
| Third-party agents | 229 | ingest/third-party/agents/ (3 enhanced) |
| Archived | 5 | ingest/experimental/ |
| Scripts/rules | 402 | ingest/scripts/ |

## Remaining Work

**All original backlog items (B1-B12) and all blockers (D1-D3) are COMPLETE.**

- [x] [B13] Encode AI code quality doctrine (Complete — doctrine-code-quality.md, audit checklist + implement patterns updated)

All backlog items complete. Repository fully operational.

---

_Updated by /ql-* commands automatically_
