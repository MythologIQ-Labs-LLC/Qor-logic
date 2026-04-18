# Qor Workflow Bundles

A **workflow bundle** is a meta-skill that orchestrates a sequence of single-purpose skills under one trigger. Bundles are useful for repeated multi-phase workflows (production gap audits, release cycles, migrations) but introduce a UX risk: they take on too much without checkpointing back to the user.

This convention defines the metadata and guardrails every bundle MUST follow.

## When to write a bundle

- The workflow chains 4+ skills in a fixed sequence
- Users invoke the same chain repeatedly (cost: typing + remembering order)
- The chain is well-defined enough that decision points between skills are mechanical

When in doubt, **don't bundle** — typing `/qor-research → /qor-plan → /qor-audit → /qor-implement` keeps each phase explicit and interruptible.

## Bundle metadata

YAML frontmatter every bundle SKILL.md must carry:

```yaml
---
name: qor-<bundle-name>
type: workflow-bundle           # marks this as a bundle, not a single skill
phases: [research, plan, audit, implement, substantiate, validate, remediate]    # canonical full chain per qor/gates/chain.md; individual bundles may declare a truncated subset
checkpoints:                    # named breakpoints; bundle halts at each
  - after-research
  - after-audit
  - after-implement
budget:
  max_phases: 6                 # hard ceiling on phases per invocation
  abort_on_token_threshold: 0.7 # of remaining context window
  max_iterations_per_phase: 3   # for verification rounds (deep-audit-style)
decomposes_into:                # for very large bundles, list sub-bundles
  - qor-<bundle>-recon
  - qor-<bundle>-remediate
---
```

## Checkpoint protocol

At every checkpoint the bundle MUST:

1. Summarize what was completed in the most recent phase (1-3 sentences)
2. Surface the proposed next phase
3. Prompt the user: **continue / branch / stop**
4. On `continue`: proceed to next phase
5. On `branch`: invoke the alternative skill the user names; bundle pauses
6. On `stop`: write a resume marker (`.qor/bundle-pending-<name>.json`) capturing current phase + artifacts; exit cleanly

The resume marker schema:

```json
{
  "bundle": "qor-deep-audit",
  "session_id": "<UTC-ISO-MIN>-<6hex>",
  "completed_phases": ["recon", "synthesis"],
  "next_phase": "verification-round-1",
  "artifacts": {"research_brief": "docs/.../RESEARCH_BRIEF.md"},
  "ts": "ISO-8601"
}
```

Resume via `python qor/scripts/<bundle>.py --resume` (when bundle has a script) or by re-invoking the bundle, which detects the marker.

## Budget protocol

Bundles MUST consult the token-efficiency doctrine (`qor/references/doctrine-token-efficiency.md`) and abort gracefully when:

- `max_phases` is exceeded → write resume marker, summarize, exit
- Conversation context approaches `abort_on_token_threshold` of the harness limit → suggest `/cost` check; suggest fresh-session resume; write resume marker
- A single phase exceeds `max_iterations_per_phase` (e.g., research verification stuck in a loop) → halt that phase, write findings to date, escalate to `/qor-debug` or `/qor-remediate` per phase

The bundle's prose must explicitly cite these limits in its Constraints section.

## Decomposition pattern

Bundles >5 phases SHOULD decompose into sub-bundles separated by a hard checkpoint. Example: `qor-deep-audit` → `qor-deep-audit-recon` (recon + verification, ends at RESEARCH_BRIEF) + `qor-deep-audit-remediate` (plan + implement + validate).

The parent bundle becomes a thin orchestrator documenting the split; sub-bundles are independently invokable. Operators choose recon-only when scoping; recon+remediate when ready to act.

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| No checkpoints | Bundle runs to completion; user can't redirect mid-flow | Add `checkpoints` to metadata; insert prompts in protocol |
| No budget | Bundle runs until context exhausted; user loses ability to inspect | Declare `budget`; abort with resume marker |
| Bundles invoking bundles | Recursive invocation depth → context blowup | Forbid; require sub-bundle composition via decomposes_into |
| Implicit chain | Bundle doesn't list `phases` in metadata; reader can't tell what runs | Required in YAML |
| Inline reinvention | Bundle does the work itself instead of invoking constituent skills | Bundle MUST `/qor-<skill>` each phase by name (per delegation-table.md) |

## Token-efficiency requirements

Per `qor/references/doctrine-token-efficiency.md`, bundles MUST:

- Reference artifacts by path, not paste content (`see RESEARCH_BRIEF.md §3` not 200 inline lines)
- Delegate high-token research to subagents (offloads from main context)
- Avoid re-reading files between phases unless changed
- At each checkpoint, summarize in <100 words

## Example bundles

- `qor-deep-audit` (parent, decomposed): full-cycle production gap audit
- `qor-deep-audit-recon`: recon + synthesis + verification (ends at RESEARCH_BRIEF)
- `qor-deep-audit-remediate`: plan + implement + validate (consumes RESEARCH_BRIEF)

Future candidates (not authored): `qor-release-cycle` (validate → release → tag), `qor-onboard-codebase` (research → organize → audit → plan).
