# Plan: Phase 9 — Handoffs + Workflow Bundles + Token Efficiency

**Status**: Active (scope-limited, 3-track combined)
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Scope**: Three coordinated deliverables sharing the doctrine "skills name skills explicitly; long workflows checkpoint and budget".

## Open Questions

None. Decisions settled:
- Three tracks ship together (shared doctrine)
- qor-audit Razor VETO → `/qor-refactor`; Orphan/Macro VETO → `/qor-organize`
- qor-deep-audit splits into recon + remediate sub-bundles, each with per-phase checkpoints
- Token-efficiency doctrine lives at `qor/references/doctrine-token-efficiency.md`; consumer-facing summary at repo-root `CLAUDE.md`

## Track A — Cross-ref wiring + Delegation Table

### A.1 Add explicit handoffs to 6 SKILL.md files

| Skill | Add reference at | New target |
|---|---|---|
| `qor-audit` | Section 4 Razor Pass conclusion | `/qor-refactor` (Razor VETO mandates this) |
| `qor-audit` | Orphan Detection + Macro-Level conclusion | `/qor-organize` |
| `qor-audit` | Final Report (PASS) | `/qor-implement` (next phase) |
| `qor-research` | Final Report | `/qor-plan` (next phase); `/qor-organize` for structural concerns |
| `qor-plan` | Final Report | `/qor-audit` (next phase); `/qor-organize` for restructuring needs |
| `qor-implement` | Razor enforcement section | `/qor-refactor` for mid-implement bloat |
| `qor-implement` | Final Report | `/qor-substantiate` (next); `/qor-debug` on regression |
| `qor-refactor` | When file-internal refactor surfaces project-level issues | `/qor-organize` |
| `qor-validate` | On repeat failure | `/qor-remediate` |

### A.2 Author `qor/gates/delegation-table.md`

Single-source delegation matrix. When skill X detects condition Y, the legal next skill is Z. No skill should reinvent another skill's process.

```
| Detector       | Condition                          | Delegate to        |
|----------------|------------------------------------|--------------------|
| qor-audit      | Section 4 Razor violation          | /qor-refactor      |
| qor-audit      | Orphan / macro structural breach   | /qor-organize      |
| qor-audit      | Plan PASS                          | /qor-implement     |
| qor-implement  | Mid-implement Razor bloat          | /qor-refactor      |
| qor-implement  | Regression / hallucination         | /qor-debug         |
| qor-substantiate | Section 4 violation post-build   | /qor-refactor      |
| any phase      | Process failure (>=10 sev)         | /qor-remediate     |
| qor-refactor   | Project-level structural issue     | /qor-organize      |
```

## Track B — Workflow-Bundle Convention

### B.1 Author `qor/gates/workflow-bundles.md`

Convention doc defining bundle metadata (in YAML frontmatter):

```yaml
---
name: qor-deep-audit
type: workflow-bundle
phases: [...]
checkpoints: [after-recon, after-synthesis, after-verification, after-plan, after-implement]
budget:
  max_phases: 6
  max_gaps_per_sprint: 5
  abort_on_token_threshold: 0.7  # of context window
decomposes_into: [qor-deep-audit-recon, qor-deep-audit-remediate]
---
```

Specifies:
- **Checkpoint protocol**: bundle halts at named checkpoints, summarizes, prompts user
- **Budget protocol**: declared limits; bundle aborts if exceeded with a resume-marker
- **Decomposition pointer**: large bundles list their sub-bundles for explicit handoff

### B.2 Migrate qor-deep-audit into the canonical tree

Source: the operator's globally installed qor-deep-audit/SKILL.md (verified: 180 lines, 6 phases, no checkpoints).

- Move into `qor/skills/meta/qor-deep-audit/SKILL.md` (canonical SSoT location)
- Add bundle frontmatter per B.1
- Insert "**CHECKPOINT — confirm continuation**" between each phase
- Reference `qor/gates/workflow-bundles.md` for the convention
- Update qor-deep-audit's chained refs (`/qor-plan`, `/qor-audit`, etc.) — already correct

### B.3 Decompose into sub-bundles

Author two sub-skills:

- `qor/skills/meta/qor-deep-audit-recon/SKILL.md` — Phases 1-3 (recon + synthesis + verification rounds), ends at `RESEARCH_BRIEF.md`
- `qor/skills/meta/qor-deep-audit-remediate/SKILL.md` — Phases 4-6 (plan + implement + validate), takes `RESEARCH_BRIEF.md` as input

Parent `qor-deep-audit` becomes a thin orchestrator that documents the two-phase split, with a hard checkpoint between recon and remediate.

## Track C — Token Efficiency Doctrine

### C.1 Author `qor/references/doctrine-token-efficiency.md`

Codifies (informed by `drona23/claude-token-efficient`):

- No sycophantic openers / closers
- Short sentences (8-10 words for prose; code stays normal)
- Read once, don't re-read unchanged files
- Edit > rewrite (smaller diffs, smaller token footprint)
- Skip files >100KB unless required
- Reference-by-link (`see docs/X.md §Y`) over inline paste
- Subagent delegation for high-token research (offloads from main context)
- Per-skill context budget (declare in frontmatter when relevant)
- `/cost` monitoring on long sessions
- Suggest fresh session on topic shift
- No em-dashes, smart quotes, or non-ASCII parser-unfriendly chars in code/data

### C.2 Drop `CLAUDE.md` at repo root

Consumer-facing summary that loads automatically per Claude Code convention. Brief (target <60 lines) so its own input cost stays low.

References `qor/references/doctrine-token-efficiency.md` for the full doctrine.

### C.3 Cross-link from workflow-bundles.md

Workflow bundles MUST cite the token-efficiency doctrine; budget protocol explicitly references the per-skill context budget pattern.

## Affected Files

### Track A (6 SKILL.md edits + 1 new doc)
- `qor/skills/governance/qor-audit/SKILL.md`
- `qor/skills/sdlc/qor-research/SKILL.md`
- `qor/skills/sdlc/qor-plan/SKILL.md`
- `qor/skills/sdlc/qor-implement/SKILL.md`
- `qor/skills/sdlc/qor-refactor/SKILL.md`
- `qor/skills/governance/qor-validate/SKILL.md`
- `qor/gates/delegation-table.md` (new)

### Track B (2 new docs + 3 SKILL.md, 1 migrated + 2 new)
- `qor/gates/workflow-bundles.md` (new)
- `qor/skills/meta/qor-deep-audit/SKILL.md` (migrated from `~/.claude/skills/qor-deep-audit/`)
- `qor/skills/meta/qor-deep-audit-recon/SKILL.md` (new)
- `qor/skills/meta/qor-deep-audit-remediate/SKILL.md` (new)

### Track C (1 new doc + 1 new repo-root file)
- `qor/references/doctrine-token-efficiency.md` (new)
- `CLAUDE.md` (new, repo root)

### Dist
- `qor/dist/**` regenerated by compile.py

## Constraints

- **No new Python** — markdown + doctrine only
- **No new tests** — Tracks A/B/C are documentation/policy; existing 108 tests cover underlying primitives
- **Audit existing skill bodies** — additions are insertions at handoff points; existing methodology preserved
- **CLAUDE.md must stay short** — per drona23 doctrine, instruction files cost input tokens every turn; target <60 lines

## Success Criteria

- [ ] All 6 SKILL.md files cite at least one explicit `/qor-*` handoff
- [ ] `qor/gates/delegation-table.md` lists every legal handoff condition
- [ ] `qor/gates/workflow-bundles.md` defines bundle metadata + checkpoint + budget protocols
- [ ] `qor-deep-audit` lives at canonical `qor/skills/meta/qor-deep-audit/` with checkpoint protocol applied
- [ ] `qor-deep-audit-recon` + `qor-deep-audit-remediate` sub-bundles authored
- [ ] `qor/references/doctrine-token-efficiency.md` codifies all 11 rules
- [ ] Repo-root `CLAUDE.md` exists, <60 lines, references the doctrine
- [ ] Dist regenerated; drift exits 0
- [ ] Tests 108/108 (no new tests; no regression)
- [ ] Ledger chain verify OK
- [ ] Committed + pushed with `BUILD_REGEN=1`

## CI Commands

```bash
python -m pytest tests/
python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
wc -l CLAUDE.md  # should be <60
```
