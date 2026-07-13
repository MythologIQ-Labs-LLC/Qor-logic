---
name: qor-onboard
type: workflow-bundle
description: >-
  Tutorial mode for a first governed session: find one small, safe improvement in the operator's real codebase and walk the full gate chain on it end-to-end with narration, every gate artifact produced for real, every doctrine term linked to its glossary home at first use. Use when (1) a repo was just seeded and the chain has never run, (2) a new operator wants to learn the ceremony on a 30-minute change instead of load-bearing work.
phases: [ideate, research, plan, audit, implement, substantiate]
tone_aware: false
checkpoints: [after-ideate, after-audit]
budget:
  max_phases: 6
  abort_on_token_threshold: 0.7
  max_iterations_per_phase: 2
metadata:
  category: meta
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ-Labs-LLC/Qor-logic
    path: qor/skills/meta/qor-onboard
phase: meta
gate_reads: ""
gate_writes: ""
---

# /qor-onboard — Tutorial Mode (Workflow Bundle)

<skill>
  <trigger>/qor-onboard</trigger>
  <phase>meta (workflow bundle)</phase>
  <persona>Governor</persona>
  <output>One sealed governed cycle on an operator-confirmed trivial change, with narration</output>
</skill>

## Governance Health Preflight

<!-- qor:governance-health-preflight -->
Run `qor-logic governance-health --profile skill-entry` before reading governance artifacts. If any finding is `DAMAGED` or `INCOMPLETE`, do not continue: report the finding's `path`, `reason`, and `legal_next`. Only `UNINITIALIZED` or scaffold-owned `MISSING` may be resolved by `qor-logic seed` (interactive: offer Y/N; autonomous: seed silently). `DAMAGED` and `INCOMPLETE` always route to `/qor-remediate` or section completion -- never to seed or bootstrap.

## Purpose

Take a first-session operator from "18 gate schemas and a hundred-term vocabulary" to "I have watched the whole chain run on my own code" in one sitting. The bundle finds a small, low-risk improvement in the operator's real repository, gets the operator's confirmation, then walks ideate -> research -> plan -> audit -> implement -> substantiate on it with narration. Every phase delegates to its single-purpose skill -- the bundle does no analysis itself, only orchestration and teaching.

## When to use

- Immediately after `qor-logic seed` on a fresh repo (the chain has never run)
- A new operator or team member wants to learn the ceremony safely
- NOT for external-codebase intake -- that job has its own workflow bundle (see the skill registry's meta section)

## Execution Protocol

### Step 1: Improvement scan (bundle-owned, operator-confirmed)

Scan the repository for tutorial-sized candidates per `references/improvement-scan.md` (candidate classes, risk criteria, exclusions). Present 2-3 candidates with a one-line risk note each. **The operator picks one or declines; nothing proceeds unconfirmed.**

### Step 2: Walk the chain with narration

Run each phase by invoking its skill, prefacing each with the narration beat from `references/tutorial-narration.md` (what this phase proves, which gate artifact it writes, which doctrine terms appear -- each linked to its glossary home at first use, never restated):

1. `/qor-ideate` — frame the tiny change as a scoped intent. **Checkpoint: operator confirms the selection before research.**
2. `/qor-research` — verify the target against source with file:line citations.
3. `/qor-plan` — author the plan file with change_class and Definition of Done.
4. `/qor-audit` — the tribunal issues a binding PASS/VETO. **Checkpoint: walk the operator through the verdict before implementing.** On VETO, narrate the delegation row and iterate (this too is the tutorial).
5. `/qor-implement` — red test first, then green twice.
6. `/qor-substantiate` — the seal ceremony to the LOCAL review boundary: when the publish menu appears, choose the local-hold path and show the operator the exact commands they would run to publish.

### Step 3: Debrief

Show the operator what now exists: the ledger entries appended this session, the gate artifacts under `.qor/gates/<session>/`, the plan file, and the seal. Point at `/qor-help` and the delegation table for the next real cycle.

## Constraints

- The bundle NEVER edits files itself; constituent skills own all changes.
- Terms are linked to `qor/references/glossary.md` homes at first use -- never redefined in narration (see the rule in `references/tutorial-narration.md`).
- The Review Boundary holds: no push, PR, tag, or release from a tutorial session.
- If the operator's repo offers no safe candidate, say so and stop -- do not manufacture work.

## Success Criteria

- [ ] Operator confirmed the candidate before any phase ran
- [ ] All six phases ran by delegation with narration beats
- [ ] Every gate artifact present under `.qor/gates/<session>/`
- [ ] Session sealed to the local review boundary
- [ ] Debrief delivered (ledger entries, artifacts, next steps)

## Delegation

Per `qor/gates/delegation-table.md`:

- **Audit PASS** → `/qor-implement` (continue the chain)
- **Audit VETO** → narrate the finding class, then the mandated skill (`/qor-plan`, `/qor-research`, `/qor-refactor`, or `/qor-remediate`)
- **Runtime defect mid-tutorial** → `/qor-debug`
- **Repo has no safe candidate** → stop; suggest `/qor-help`

See `qor/gates/workflow-bundles.md` for bundle protocol.
