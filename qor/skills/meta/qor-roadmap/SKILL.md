---
name: qor-roadmap
description: >-
  Experimental long-horizon decision-topology navigator. Use only when an objective cannot responsibly become one implementation plan yet because prerequisite facts, authority decisions, or cross-context dependencies must be preserved first.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ-Labs-LLC/Qor-logic
    path: qor/skills/meta/qor-roadmap
user-invocable: true
phase: meta
tone_aware: false
gate_reads: ""
gate_writes: ""
permitted_tools: [Read, Grep, Glob, Bash]
---
# /qor-roadmap — Experimental Long-Horizon Decision Topology

<skill>
  <trigger>/qor-roadmap</trigger>
  <phase>meta</phase>
  <output>durable Roadmap state + actionable frontier + legal resolver/handoff guidance</output>
</skill>

## Governance Health Preflight

<!-- qor:governance-health-preflight -->
Run `qor-logic governance-health --profile skill-entry` before reading governance artifacts. If any finding is `DAMAGED` or `INCOMPLETE`, do not continue: report the finding's `path`, `reason`, and `legal_next`. Only `UNINITIALIZED` or scaffold-owned `MISSING` may be resolved by `qor-logic seed`. `DAMAGED` and `INCOMPLETE` route to `/qor-remediate` or section completion, never to seed/bootstrap.

## Purpose

Preserve the prerequisite topology of genuinely long-horizon work across agent contexts without turning uncertainty into fictional implementation tasks.

Roadmap owns topology and routing. Existing Qor skills own the work that resolves topology nodes.

## Environment (Phase 90 wiring; GH #79)

Before invoking the Roadmap runtime, verify that the active Python environment can import Qor's reliability package:

```bash
python -c "import qor.reliability"
```

If that check fails, activate the environment where `pip show qor-logic` resolves, or use `pipx install qor-logic` for a global install. On hosts where Python or `qor-logic` is unavailable, the Phase 75 declarative-tolerance contract applies: prerequisite-dependent gates record SKIP and emit `gate_skipped_prerequisite_absent` rather than pretending the check ran.

## Admission Guard

Use Roadmap only when at least one is true:

- the objective is expected to span multiple fresh agent contexts before planning is trustworthy;
- future work cannot yet be specified because prerequisite facts or authority decisions block it;
- several independent resolution branches must survive context changes;
- one long-horizon objective is expected to yield multiple governed implementation plans over time.

Do NOT invoke Roadmap merely because a feature is complex. `/qor-plan` already handles complex and multi-phase implementation planning.

Do NOT invoke Roadmap merely because a concept is fuzzy. `/qor-ideate` owns problem framing, assumptions, options, and scope.

P1 is explicitly operator-invoked. Do not auto-route into Roadmap.

## Canonical State

Use only the existing module-dispatch surface:

```bash
qor-logic scripts roadmap_cli --repo-root . <command> ...
```

Canonical state is `.qor/roadmaps/<roadmap-id>/events.jsonl`. Do not create a second mutable Roadmap summary or `state.json` cache.

Initialize:

```bash
qor-logic scripts roadmap_cli --repo-root . init \
  --roadmap <id> --objective "<long-horizon outcome>" \
  --success "<condition>" --exclude "<non-goal>"
```

## Node Model

Only three P1 node kinds exist:

- `fact` — resolvable evidence; use resolver `/qor-research` when investigation is required.
- `decision` — consequential authority choice; MUST declare `--authority-required`.
- `prerequisite` — non-production condition/setup state.

Roadmap does not create implementation-task nodes.

Add nodes and dependencies with `add-node` and `add-dependency`. Dependency cycles are illegal and the state engine rejects them.

Use `add-space` only for uncertainty that cannot yet be responsibly decomposed. Retire it with rationale when it becomes irrelevant or has graduated into explicit nodes.

## Frontier Protocol

Run:

```bash
qor-logic scripts roadmap_cli --repo-root . frontier \
  --roadmap <id> [--authority <authority> ...]
```

The frontier output is the complete set of nodes that can legally proceed now. It includes blockers, resolver, authority requirement, and graph-derived dependent counts.

Do not convert those counts into a model-authored priority score. Do not silently pick one node when several are ready. Present the ready set and resolve work according to operator direction or an already-declared priority.

## Resolution and Delegation

Per `qor/gates/delegation-table.md`:

1. Missing problem framing → `/qor-ideate`.
2. Fact requires investigation → `/qor-research`.
3. Ready named planning scope → `/qor-plan`.

For delegated work, return to Roadmap and record the result by pointer. Do not reproduce the delegated skill's workflow inline.

Resolve a fact only with at least one evidence pointer:

```bash
qor-logic scripts roadmap_cli --repo-root . resolve \
  --roadmap <id> --node <fact-id> \
  --evidence <artifact-or-source-pointer> --rationale "<why this resolves the fact>"
```

Resolve a decision only when the acting authority exactly matches the node's declared requirement:

```bash
qor-logic scripts roadmap_cli --repo-root . resolve \
  --roadmap <id> --node <decision-id> \
  --authority <declared-authority> --rationale "<decision rationale>"
```

Decision supersession and downstream invalidation are deliberately deferred until post-P1 evaluation. P1 records resolved decisions but exposes no supersession API.

## Planning Scope and Handoff

Create a named planning scope only after the operator can identify the exact subset intended for one `/qor-plan`:

```bash
qor-logic scripts roadmap_cli --repo-root . add-scope \
  --roadmap <id> --id <scope-id> --title "<scope>" \
  --node <required-node> [--node <required-node> ...]
```

Handoff requires every scope node resolved, every named unresolved-space entry retired, and a repository-local legal predecessor artifact from `ideation` or `research`:

```bash
qor-logic scripts roadmap_cli --repo-root . handoff \
  --roadmap <id> --scope <scope-id> \
  --predecessor-phase research \
  --predecessor-artifact .qor/gates/<sid>/research.json
```

If the predecessor is missing, route to `/qor-ideate` or `/qor-research`; do not manufacture a routine gate override.

A successful handoff ends Roadmap work. Invoke `/qor-plan`. The handoff deliberately contains no implementation task list.

## Constraints

- **NEVER** modify production implementation from Roadmap.
- **NEVER** perform another Qor skill's process inline.
- **NEVER** create Roadmap-specific leases/heartbeats in P1.
- **NEVER** create a persisted state cache in P1.
- **NEVER** auto-select a frontier node using model-estimated priority.
- **NEVER** auto-invoke Roadmap in P1.
- **ALWAYS** keep canonical state under `.qor/roadmaps/<id>/events.jsonl`.
- **ALWAYS** preserve explicit authority on decision resolution.
- **ALWAYS** stop at `/qor-plan` handoff.

## Success Criteria

- [ ] Objective and prerequisite topology survive a fresh context without conversation history.
- [ ] Frontier shows all legally ready nodes and real blockers.
- [ ] Facts carry evidence pointers; decisions carry authority.
- [ ] Planning handoff fails closed until the named scope is genuinely ready.
- [ ] Legal next action from a ready scope is `/qor-plan`, never production implementation.
