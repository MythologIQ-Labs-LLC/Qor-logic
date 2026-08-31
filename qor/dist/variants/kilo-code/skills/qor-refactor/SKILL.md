---
name: qor-refactor
description: >-
  Context-aware, behavior-preserving simplification pass over a declared scope (changeset, focused, component, or explicit). Use when: (1) invoked as the post-implementation refinement step, (2) a confirmed structural/maintainability defect needs repair, (3) Section 4 Simplicity Razor thresholds are breached, or (4) general behavior-preserving cleanup is requested.
metadata:
  category: development
  author: MythologIQ
  source:
    repository: https://github.com/MythologIQ-Labs-LLC/Qor-logic
    path: qor/skills/sdlc/qor-refactor
phase: implement
tone_aware: false
gate_reads: audit
gate_writes: implement
permitted_tools: [Read, Grep, Glob, Bash, Edit, Write]
permitted_subagents: []
---
# /qor-refactor - KISS Simplification Pass

<skill>
  <trigger>/qor-refactor</trigger>
  <phase>implement (maintenance)</phase>
  <persona>Specialist</persona>
  <output>Refactored code, updated SYSTEM_STATE.md, ledger entry</output>
</skill>

## Governance Health Preflight

<!-- qor:governance-health-preflight -->
Run `qor-logic governance-health --profile skill-entry` before reading governance artifacts. If any finding is `DAMAGED` or `INCOMPLETE`, do not continue: report the finding's `path`, `reason`, and `legal_next`. Only `UNINITIALIZED` or scaffold-owned `MISSING` may be resolved by `qor-logic seed` (interactive: offer Y/N; autonomous: seed silently). `DAMAGED` and `INCOMPLETE` always route to `/qor-remediate` or section completion -- never to seed or bootstrap.

## Purpose

Perform context-aware, behavior-preserving simplification of a declared implementation scope, improving clarity, consistency, structural coherence, and maintainability without changing its externally observable contract. Applies both micro-level (function) and macro-level (file/module) KISS principles, bounded to the scope declared in Step 3.

Behavior preservation is the primary invariant. A metric breach (Section 4 or otherwise) is a signal that triggers examination, not a license to force decomposition that would weaken a stronger existing contract, boundary, or defensive mechanism. `NO REFACTOR REQUIRED` is a valid, successful outcome when the current implementation is already clearer or when a proposed simplification would weaken something stronger than the metric it satisfies.

Follow the target environment's own governing instructions, conventions, formatter/linter configuration, dependency manifests, type/schema contracts, neighboring implementation, and tests. Explicit local rules take precedence over generic simplification preferences unless they conflict with stronger correctness, security, integrity, or governance requirements. Do not assume a specific language, framework, or entry-point convention (e.g. `package.json`, `main.tsx`); discover it from the target repository.

Authority boundary with `/qor-harden`: harden discovers and confirms broad implementation-quality defects; `/qor-refactor` owns the confirmed behavior-preserving structural repair. A confirmed `IQ-COMPLEX`, `IQ-CONTEXT`, or `IQ-MAINTAIN` finding routes here when the repair is structurally scoped and behavior-preserving, per the `/qor-refactor` remediation profile in `qor/references/implementation-quality-sweep.md`. Uncertain behavioral failure routes to `/qor-debug`; architecture/topology or product-intent change exceeds refactor authority and routes to `/qor-plan` or `/qor-organize`.

## Execution Protocol

### Step 0: Gate Check (advisory — Phase 8 wiring)

Verify prior-phase artifact exists and is well-formed before proceeding.

```python
from qor.scripts import gate_chain, session

sid = session.get_or_create()
result = gate_chain.check_prior_artifact("implement", session_id=sid)
if not result.found:
    # Prompt user to override; on confirm:
    gate_chain.emit_gate_override(
        current_phase="implement",
        prior_phase_name="audit",
        reason="user override: audit.json not found",
        session_id=sid,
    )
elif not result.valid:
    gate_chain.emit_gate_override(
        current_phase="implement",
        prior_phase_name="audit",
        reason=f"user override: {result.errors}",
        session_id=sid,
    )
```

Override is permitted (advisory gate) but logged as severity-1 `gate_override` event in the Process Shadow Genome.

**Phase 54 wiring**: when `gate_chain.emit_gate_override` raises `OverrideFrictionRequired`, prompt the operator for a written justification (>=50 chars) and re-call `emit_gate_override` with `justification=<text>`. Per `qor/references/doctrine-ai-rmf.md` §MANAGE-1.1 + `qor/references/doctrine-eu-ai-act.md` Art. 14.

### Step 1: Identity Activation
You are now operating as **The Qor-logic Specialist** in refactoring mode.

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
            "ts": shadow_process.now_iso(), "skill": "qor-implement", "session_id": sid,
            "event_type": "capability_shortfall", "severity": 2,
            "details": {"capability": "agent-teams"},
            "addressed": False, "issue_url": None, "addressed_ts": None,
            "addressed_reason": None, "source_entry_id": None,
        })
    mode = "sequential"
```

Contract for `teams` mode (reserved for future harness wiring): `TeamCreate(<spec>) -> [{track, deliverable}, ...]`. Skill synthesizes the track outputs into a single artifact.

### Step 2: Environment Scan

```
Glob: [target path]
Read: [each file in scope]
```

Identify violations of Section 4 Simplicity Razor:
- Functions > 40 lines
- Files > 250 lines
- Nesting > 3 levels
- Nested ternaries
- Generic variable names

### Step 3: Scope Determination

Declare exactly one scope mode before making any change. Do not silently expand a narrower scope into unrelated legacy code.

- **`changeset`** (recommended default when invoked as the post-implementation step of `/qor-implement` or immediately after a fresh diff exists): recently changed implementation only.
- **`focused`**: an explicit snippet, function, or single file. Maps to the Single-File Micro-Refactor path below.
- **`component`**: a declared module/package/service/subsystem boundary. Maps to the Multi-File Macro-Refactor path below.
- **`explicit`**: any broader operator-declared scope. Maps to the Multi-File Macro-Refactor path below.

`changeset` scope typically runs the Single-File Micro-Refactor path per touched file; escalate to Multi-File Macro-Refactor only if the changeset itself spans a module boundary.

### Simplification Test

Before applying any proposed simplification, answer all seven questions. If any answer is unclear or unfavorable, do not apply that simplification; record `NO REFACTOR REQUIRED` for that finding instead.

1. What complexity is being removed?
2. Why is it unnecessary or obscuring intent?
3. What contract must remain unchanged?
4. What evidence establishes that contract (tests, schema, type signature, documented invariant)?
5. Is the proposed result actually easier to understand?
6. Does the change remove a useful abstraction, boundary, or defensive mechanism?
7. Can behavior equivalence be verified?

---

## Single-File Micro-Refactor

### Step 3a: Function Decomposition

For each function exceeding 40 lines, split into cohesive sub-functions.
Reference examples: `references/qor-refactor-examples.md`.

### Step 3b: Logic Flattening

Replace deep nesting with early returns.
Reference examples: `references/qor-refactor-examples.md`.

### Step 3c: Ternary Elimination

Replace nested ternaries with explicit control flow.
Reference examples: `references/qor-refactor-examples.md`.

### Step 3d: Variable Renaming

Audit and replace generic identifiers.
Reference examples: `references/qor-refactor-examples.md`.

### Step 3e: Cleanup

- Remove debug/print artifacts not intended for production, in whatever form the target environment actually uses (e.g. `console.log`, `print`, `fmt.Println`, `System.out.println`); discover the convention rather than assuming one
- Remove commented-out code
- Remove unrequested config options
- Remove empty catch/except blocks
- Remove unused imports

---

## Multi-File Macro-Refactor

### Step 4a: Orphan Detection

```
Discover: [entry point(s), from the target environment's own build/run configuration - do not assume main.tsx/index.ts]
Trace: Import chains to all files in scope
```

Flag any file not reachable from entry point. Template:
`references/qor-refactor-examples.md`.

**For orphans**: Remove or wire into build path

### Step 4b: File Splitting

For files exceeding 250 lines, split into cohesive modules.
Reference example: `references/qor-refactor-examples.md`.

### Step 4c: God Object Elimination

Identify and split "God Objects" (classes/modules doing too much).
Reference example: `references/qor-refactor-examples.md`.

### Step 4d: Dependency Audit

```
Read: [the target environment's own dependency manifest, e.g. package.json, Cargo.toml, pyproject.toml, go.mod, pom.xml]
```

For each dependency:
1. Is it actually imported/used?
2. Can the target language's own standard library replace it in a small, justified amount of code?

Template: `references/qor-refactor-examples.md`.

### Step 4e: Macro-Level Structure Check

Audit module boundaries and architecture flow:

- Verify directories align to domains (no mixed responsibilities).
- Check for cyclic imports between modules; break cycles by extracting shared interfaces.
- Enforce dependency direction (UI -> domain -> data). No reverse imports.
- Consolidate duplicated domain logic into a single module.
- Centralize cross-cutting concerns (logging, auth, config) to avoid scattering.
- Identify config/flags sprawl; consolidate or document ownership.

If any violation is found, refactor to restore clear boundaries before proceeding.

---

## Post-Refactor Verification

### Step 5: Compliance Check

For each completed pass (including a `NO REFACTOR REQUIRED` outcome), establish and report at minimum:

- **behavior preserved**: `YES | NO | INCONCLUSIVE`
- **complexity reduced**: `YES | NO`
- **clarity improved**: `YES | NO | SUBJECTIVE`
- **contract weakened**: `YES | NO`
- **scope exceeded**: `YES | NO`
- **tests/checks executed and their actual results**

A `NO` on "contract weakened" or a "YES" on "scope exceeded" blocks completion until corrected. Template: `references/qor-refactor-examples.md`.

All must pass before completion.

### Step 6: Update System State

```
Edit: docs/SYSTEM_STATE.md
```

Template: `references/qor-refactor-examples.md`.

### Step 7: Update Ledger

```
Edit: docs/META_LEDGER.md
```

Template: `references/qor-refactor-examples.md`.

### Step 8: Handoff

Template: `references/qor-refactor-examples.md`.

### Step Z: Write Gate Artifact (Phase 11D wiring)

Persist the structured gate artifact at `.qor/gates/<session_id>/implement.json` so downstream phases can read it via `gate_chain.check_prior_artifact`.

```python
from qor.scripts import gate_chain, shadow_process, ai_provenance

# Build payload conforming to qor/gates/schema/implement.schema.json
payload = {
    "ts": shadow_process.now_iso(),
    # ... phase-specific required fields (see schema)
}
manifest = ai_provenance.build_manifest(
    "implement", human_oversight=ai_provenance.HumanOversight.ABSENT
)
gate_chain.write_gate_artifact(
    phase="implement", payload=payload, session_id=sid, ai_provenance=manifest,
)
```

Schema lives at `qor/gates/schema/implement.schema.json`; the helper validates before write. Per Phase 54: refactor calls `ai_provenance.build_manifest` to embed AI provenance.

## Delegation

Per `qor/gates/delegation-table.md`:

- **Refactor complete** → `/qor-audit` (re-audit) when invoked from outside the SDLC chain, or `/qor-substantiate` when invoked from a substantiate-driven Section 4 cleanup.
- **File-internal refactor surfaces project-level structural issues** (e.g., a refactor reveals two modules that should be one, or a directory boundary that's wrong) → escalate to `/qor-organize`. Refactor owns file-internal logic shape; project topology belongs to organize.

## Constraints

- **NEVER** change behavior during refactor (only structure)
- **NEVER** skip orphan detection in multi-file mode
- **NEVER** decompose solely to satisfy a line-count/nesting threshold when doing so weakens a stronger existing contract, boundary, or defensive mechanism, or reduces clarity
- **NEVER** silently expand a `changeset`/`focused` scope into unrelated legacy code
- **NEVER** push refactored code to CI without running CI-equivalent commands locally first
- **NEVER** push individual fix commits — batch all refactoring into one commit
- **NEVER** force-push to shared branches without GR-2 coordination protocol
- **NEVER** leave secrets in code — rotate, rewrite history, then gitignore (GR-1)
- **ALWAYS** update SYSTEM_STATE.md with new tree
- **ALWAYS** update ledger with refactor hash
- **ALWAYS** verify tests still pass after refactor
- **ALWAYS** run local CI mirror (lint + test with CI flags) before pushing refactored code
- **ALWAYS** batch CI fixes into a single push

## Success Criteria

Refactor succeeds when either:

- [ ] Every violation found in scope (Section 4 thresholds, nested ternaries, generic variable names) was examined via the Simplification Test, and each resulting change reduces complexity without weakening a stronger contract, boundary, or defensive mechanism; or
- [ ] `NO REFACTOR REQUIRED` was recorded, with the Simplification Test answers showing why no change was justified

And in both cases:

- [ ] No orphan files detected (all connected to the discovered entry point(s))
- [ ] All tests pass after refactor
- [ ] Behavior unchanged (only structure modified), reported as `behavior preserved: YES` per Step 5, never `INCONCLUSIVE`
- [ ] SYSTEM_STATE.md updated with new file tree
- [ ] META_LEDGER.md updated with refactor hash

## Integration with S.H.I.E.L.D.

This skill implements:

- **Section 4 Razor Enforcement**: Mandatory examination of violations via the Simplification Test; behavior-preserving repair only where justified
- **Structural Integrity**: Ensures no orphans or broken imports after changes
- **Hash Chain Continuation**: Records refactoring in META_LEDGER
- **Specialist Persona**: Precision structural changes without behavior modification
