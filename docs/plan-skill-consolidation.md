# Plan: Skill Consolidation — Merge, Distill, Archive, Wire

## Open Questions

None — all resolved by registry analysis and user directives.

## Phase 1: Archive Project-Specific Utilities

### Affected Files

- `ingest/experimental/` — NEW directory for archived skills
- 5 files moved from `ingest/internal/utilities/` to `ingest/experimental/`

### Changes

Move Tauri/host-app-specific utilities that have no generic value:

```
ingest/internal/utilities/build-doctor.md         → ingest/experimental/build-doctor.md
ingest/internal/utilities/tauri-ipc-wiring.md     → ingest/experimental/tauri-ipc-wiring.md
ingest/internal/utilities/tauri2-state-management.md → ingest/experimental/tauri2-state-management.md
ingest/internal/utilities/tauri2-testing-validation.md → ingest/experimental/tauri2-testing-validation.md
ingest/internal/utilities/tauri-launcher.md       → ingest/experimental/tauri-launcher.md
```

These are preserved (not deleted) but excluded from processing pipeline.

## Phase 2: Merge Overlapping Skills into Enhanced Agents

### Affected Files

- `ingest/third-party/agents/code-reviewer.md` — REWRITE with distilled utility content
- `ingest/third-party/agents/accessibility-tester.md` — REWRITE with distilled utility content
- `ingest/third-party/agents/documentation-engineer.md` — REWRITE with distilled utility content
- 3 files removed from `ingest/internal/utilities/` (originals consumed by merge)

### Changes

For each overlap pair, extract generic methodology from the utility (discard host-app references) and merge into the third-party agent definition:

**code-reviewer** (483-line utility → enhanced agent):
- Extract: review process, quality checklists, severity classification, Definition of Done
- Discard: host-app module names, Alden/Vault/Arbiter references, specific coverage targets
- Merge into: `ingest/third-party/agents/code-reviewer.md`

**accessibility-specialist** (566-line utility → enhanced agent):
- Extract: WCAG checklist, keyboard nav testing, screen reader compatibility, cognitive accessibility
- Discard: host-app component names, specific Axe config
- Merge into: `ingest/third-party/agents/accessibility-tester.md`

**documentation-scribe** (773-line utility → enhanced agent):
- Extract: doc standards, API doc patterns, changelog conventions, README structure
- Discard: host-app-specific examples, module references
- Merge into: `ingest/third-party/agents/documentation-engineer.md`

After merge, delete consumed utilities from `ingest/internal/utilities/`.

## Phase 3: Distill Remaining Utilities into Reference Docs

### Affected Files

- `ingest/internal/references/patterns-architecture.md` — NEW from system-architect
- `ingest/internal/references/patterns-devops.md` — NEW from devops-engineer
- `ingest/internal/references/patterns-agent-design.md` — NEW from agent-architect
- `ingest/internal/references/patterns-project-planning.md` — NEW from project-planner
- `ingest/internal/references/patterns-ui-diagnosis.md` — NEW from ui-correction-specialist
- `ingest/internal/references/patterns-voice-integration.md` — NEW from voice-integration-specialist
- `ingest/internal/references/patterns-skill-lifecycle.md` — NEW from skill-integration-system
- 7 files removed from `ingest/internal/utilities/`
- 2 files kept as-is: skill-evaluator, learning-capture (meta-skills, under 250 lines)
- 2 files kept as-is: technical-writing-narrative, web-design-guidelines (generic, small)

### Changes

For each 400-800+ line utility, extract reusable patterns into a lean reference doc (under 250 lines):

- Strip all the host project/the host project project references
- Keep: checklists, methodologies, decision frameworks, architectural patterns
- Discard: project-specific examples, tool configs, team-specific processes
- Format as reference doc (no `<skill>` block — these are pattern libraries, not invocable skills)

After distillation, delete consumed utilities from `ingest/internal/utilities/`.

Final `ingest/internal/utilities/` should contain only: skill-evaluator, learning-capture, technical-writing-narrative, web-design-guidelines (4 files).

## Phase 4: Wire Subagent Pairings

### Affected Files

- `ingest/internal/governance/ql-document.md` — Add ql-technical-writer dispatch
- `docs/SKILL_REGISTRY.md` — Update with final inventory counts
- `docs/BACKLOG.md` — Mark completed items, update inventory

### Changes

Wire `ql-document` to dispatch `ql-technical-writer` agent for parallel doc authoring in RELEASE_METADATA mode. Add dispatch block to skill:

```xml
<dispatch>
  <agent>ql-technical-writer — Parallel authoring of CHANGELOG + README + component docs</agent>
</dispatch>
```

Update SKILL_REGISTRY.md subagent pairing table to show ql-document → ql-technical-writer as PAIRED.

### Validation

Run `python scripts/process-skills.py` — all governance skills must remain COMPLIANT after ql-document edit. Updated ql-document must stay under 250 lines.
