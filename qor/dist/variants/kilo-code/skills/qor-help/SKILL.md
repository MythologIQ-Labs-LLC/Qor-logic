---
name: qor-help
description: >-
  Quick reference that summarizes the purpose and usage of all QorLogic commands. Use when: (1) Need to understand available commands, (2) Unsure which command to use, or (3) Looking for command overview.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QorLogic
    path: processed/skills-output/qor-help
phase: help
gate_reads: ""
gate_writes: ""
---
# /qor-help - Command Summary

<skill>
  <trigger>/qor-help</trigger>
  <phase>ANY</phase>
  <persona>Governor</persona>
  <output>Concise summary of available QorLogic commands</output>
</skill>

## Execution Protocol

### Step 1: Display Command Summary

Present the command table and decision tree below. No file reads required.

### Step 2: Route User

If the user asks about a specific command, direct them to invoke it. If unsure, recommend `/qor-status` first.

## Summary

| Command            | Purpose                                                                      | Typical When                                    |
| ------------------ | ---------------------------------------------------------------------------- | ----------------------------------------------- |
| `/qor-bootstrap`    | Initialize QorLogic DNA for a **new workspace** (CONCEPT, ARCHITECTURE_PLAN, META_LEDGER). | First-time setup only. NOT for new features. |
| `/qor-plan`         | Create implementation plan for a **new feature** (plan-*.md with phases, tests). | Planning a feature in an existing workspace. |
| `/qor-status`       | Diagnose lifecycle stage and next required action.                           | Any time you need current state.                |
| `/qor-audit`        | Judge review for L2/L3 risk work; produces PASS/VETO.                        | Before any high-risk change.                    |
| `/qor-implement`    | Execute work under KISS constraints after a PASS verdict.                    | After `/qor-audit` PASS.                         |
| `/qor-refactor`     | Apply scoped refactors with guardrails.                                      | After initial implementation or when requested. |
| `/qor-validate`     | Verify Merkle chain integrity and artifacts.                                 | Before delivery or handoff.                     |
| `/qor-substantiate` | Seal the session and record evidence.                                        | End of a completed work session.                |

## Quick Decision Tree

```
New workspace?     → /qor-bootstrap
New feature?       → /qor-plan
Check state?       → /qor-status
Ready to build?    → /qor-audit → /qor-implement
Done with session? → /qor-substantiate
```

## Constraints

- **NEVER** execute other skills from within qor-help (display only)
- **ALWAYS** recommend /qor-status when user is uncertain

## Success Criteria

- [ ] Command summary displayed
- [ ] User directed to appropriate next skill

## Integration with S.H.I.E.L.D.

This skill implements:

- **Lifecycle Navigation**: Entry point for discovering available commands
- **Zero-Read Design**: No file reads required, pure reference output
- **Governor Persona**: Routing guidance without execution
