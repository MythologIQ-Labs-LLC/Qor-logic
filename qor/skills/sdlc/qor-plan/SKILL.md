---
name: qor-plan
description: >-
  Planning protocol following Rich Hickey's "Simple Made Easy" principles for creating implementation plans. Use when: (1) Designing complex features, (2) Planning multi-phase implementations, (3) Architecting new components, or (4) Any work requiring systematic planning before implementation.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ/QorLogic
    path: qor/skills/sdlc/qor-plan
phase: plan
gate_reads: research
gate_writes: plan
---
# /qor-plan - Simple Made Easy Planning

<skill>
  <trigger>/qor-plan</trigger>
  <phase>PLAN</phase>
  <persona>Governor</persona>
  <output>plan-*.md file with incremental phases and unit test descriptions</output>
</skill>

## Purpose

Create implementation plans following Rich Hickey's "Simple Made Easy" principles. This skill focuses on objective simplicity over subjective ease, avoiding complecting, and favoring composable, declarative, value-oriented designs.

## Core Principles

### Choose SIMPLE over EASY

Strive for un-braided, composable designs that minimize incidental complexity. Judge a tool, abstraction, or pattern by long-term properties: clarity, changeability, and robustness. "Easy to start" is not sufficient.

### Detect Complecting

Whenever you join concerns (state & time, data & behavior, configuration & code...), pause and seek an alternative that keeps them independent. Favor composition (placing things side-by-side) over interleaving.

### Prefer Values, Resist State

Immutable data is default. Mutable state must be narrowly scoped, well-named, and justified.

### Assess by Artifacts

Judge designs by what they produce: clarity, changeability, and robustness. Measure decisions by how much braid they remove, not how quickly they compile.

### Declarative > Imperative

Describe WHAT, not HOW. Lean on data, configuration, queries, and rule systems where possible.

### Polymorphism a la Carte

Separate data definitions, behavior specifications, and their connections. Avoid inheritance hierarchies that entangle unrelated facets.

### Guard-rails Are Not Simplicity

Tests, static checks, and refactors are valuable, but cannot compensate for complex design. Seek to remove complexity first.

## Execution Protocol

### Step 0: Gate Check (advisory — Phase 8 wiring)

Verify prior-phase artifact exists and is well-formed before proceeding.

```python
import sys; sys.path.insert(0, 'qor/scripts')
import gate_chain, session

sid = session.get_or_create()
result = gate_chain.check_prior_artifact("plan", session_id=sid)
if not result.found:
    # Prompt user to override; on confirm:
    gate_chain.emit_gate_override(
        current_phase="plan",
        prior_phase_name="research",
        reason="user override: research.json not found",
        session_id=sid,
    )
elif not result.valid:
    gate_chain.emit_gate_override(
        current_phase="plan",
        prior_phase_name="research",
        reason=f"user override: {result.errors}",
        session_id=sid,
    )
```

Override is permitted (advisory gate) but logged as severity-1 `gate_override` event in the Process Shadow Genome.

### Step 0.5: Phase branch creation (Phase 13 wiring)

Before authoring a plan, cut a per-phase branch. Dirty tree blocks checkout; operator chooses stash / commit / abandon.

```python
# Phase 13 wiring: dirty-tree check + per-phase branch
import subprocess, sys
sys.path.insert(0, 'qor/scripts')
import governance_helpers as gh

result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
if result.stdout.strip():
    raise gh.InterdictionError(
        "Working tree dirty; operator must choose stash/commit/abandon before plan branch"
    )

phase_num, slug = gh.derive_phase_metadata(plan_path)  # raises on letter-suffix legacy plans
subprocess.run(["git", "checkout", "-b", f"phase/{phase_num:02d}-{slug}"], check=True)
```

Plan header MUST declare `**change_class**: hotfix | feature | breaking` (bold — V-2). Doctrine test `test_plans_declare_change_class` enforces.

### Step 1: Collaborative Design Dialogue

Before writing any plan, understand the design through conversation:

1. **Check project context first** — read existing files, docs, recent commits
2. **Ask questions one at a time** — prefer multiple choice when possible
3. **Focus on understanding**: purpose, constraints, success criteria, anti-goals
4. **Propose 2-3 approaches** with trade-offs before settling on design
5. **Present design in sections** (200-300 words) — validate each before proceeding
6. **YAGNI ruthlessly** — challenge every proposed feature: "Is this essential for v1?"

Only proceed to write the plan file after the user has validated the design direction.

### Step 1.a — Capability check (agent-teams parallel mode, Phase 8 wiring)

```python
import qor_platform as qplat
import shadow_process

if qplat.is_available("agent-teams"):
    # Fan out specialist tracks (frontend/backend/infra) in parallel via TeamCreate;
    # synthesize results in this skill.
    mode = "teams"
else:
    state = qplat.current() or {}
    if state.get("detected", {}).get("host") == "claude-code":
        # claude-code host but agent-teams not declared -> log capability_shortfall
        shadow_process.append_event({
            "ts": shadow_process.now_iso(), "skill": "qor-plan", "session_id": sid,
            "event_type": "capability_shortfall", "severity": 2,
            "details": {"capability": "agent-teams"},
            "addressed": False, "issue_url": None, "addressed_ts": None,
            "addressed_reason": None, "source_entry_id": None,
        })
    mode = "sequential"
```

Contract for `teams` mode (reserved for future harness wiring): `TeamCreate(<spec>) -> [{track, deliverable}, ...]`. Skill synthesizes the track outputs into a single artifact.

### Step 2: Research Existing Code

Use existing code as foundation for plan. Identify existing abstractions, naming conventions, test structure, and integration points.

### Step 3: Create Plan File

Create plan markdown file with specific requirements:

#### Plan Structure

```markdown
# Plan: [feature/component name]

## Open Questions

[List any open questions or edge cases requiring clarification]

## Phase 1: [Phase Name]

### Affected Files

- [file path 1] - [concise change summary]
- [file path 2] - [concise change summary]

### Changes

[Specific code changes, minimal prose]

### Unit Tests

- [test file path] - [what it tests, why important]
```

#### Plan Requirements

- **Specific code changes** - Describe concisely with minimal surrounding prose
- **Incremental phases** - 2-3 logical phases that stack on each other
- **Well-typed interfaces** - Self-documenting, self-consistent with surrounding code
- **Unit test descriptions** - Grouped with relevant phases
- **Affected files summary** - At top of each phase

### Step 4: Avoid Common Pitfalls

**Do NOT include:**

- Exploration steps (grep for X, consult docs)
- Backwards compatibility concerns
- Feature gating or release plans
- Concluding errata (future considerations, next steps)

**DO include:**

- Complex logic unit test descriptions
- Open questions flagged at TOP of plan
- Refactoring required for clean abstractions

### Step 5: Review Plan

Before finalizing, ensure:

- [ ] Plan is precise and consistent with itself
- [ ] Follows "Simple Made Easy" principles
- [ ] Open questions are clearly flagged
- [ ] No backwards compatibility concerns
- [ ] No concluding errata sections

## Success Criteria

A reader unfamiliar with code should be able to:

- Locate a part without untangling others
- Understand the change without reading surrounding code
- Replace a part without breaking other parts
- See the complete scope of work

### Step Z: Write Gate Artifact (Phase 11D wiring)

Persist the structured gate artifact at `.qor/gates/<session_id>/plan.json` so downstream phases can read it via `gate_chain.check_prior_artifact`.

```python
import sys; sys.path.insert(0, 'qor/scripts')
import gate_chain, shadow_process

# Build payload conforming to qor/gates/schema/plan.schema.json
payload = {
    "ts": shadow_process.now_iso(),
    # ... phase-specific required fields (see schema)
}
gate_chain.write_gate_artifact(phase="plan", payload=payload, session_id=sid)
```

Schema lives at `qor/gates/schema/plan.schema.json`; the helper validates before write.

## Delegation

Per `qor/gates/delegation-table.md`:

- **Plan complete** → `/qor-audit` (next phase).
- **Plan needs architectural restructuring** (changing where things live, splitting modules across boundaries) → `/qor-organize` (project topology is its domain). The plan should reference the organize step explicitly, not embed restructuring instructions.
- **Re-research needed** for an open question that emerges during planning → return to `/qor-research`.

## Constraints

- **NEVER** worry about backwards compatibility (prefer streamlined, clean codebase)
- **NEVER** add concluding errata (future considerations belong in next plan)
- **NEVER** include exploration steps (do research before writing plan)
- **NEVER** skip the collaborative dialogue — do not jump straight to writing a plan file
- **ALWAYS** ask questions one at a time (prefer multiple choice)
- **ALWAYS** flag open questions at TOP of plan
- **ALWAYS** list unit test files FIRST in each phase, before implementation files (TDD enforcement)
- **ALWAYS** prioritize SIMPLE over EASY
- **ALWAYS** note CI commands needed to validate the plan (clippy/lint/test flags matching CI)

## Integration with QorLogic

This skill implements:

- **Simple Made Easy**: Objective simplicity over subjective ease
- **Complecting Detection**: Identifies and removes braided concerns
- **Value-Oriented Design**: Prefers immutable data and composable abstractions
- **Incremental Planning**: Phased approach with clear deliverables

---

**Remember**: Simple is not easy. Dialogue before design, design before plan, plan before code.
