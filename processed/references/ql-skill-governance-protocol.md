# QoreLogic Skill Governance Protocol

## Purpose

This protocol keeps the QoreLogic skill system coherent, portable, and valuable.

It exists to prevent two failure modes:

1. **Consistency drift**: skills disagree on paths, artifacts, handoffs, or execution semantics.
2. **Ecosystem bloat**: new skills are added because they are well-formatted, not because they add meaningful capability.

Every core skill should satisfy both the **Execution Contract** and the **Ecosystem Fit Contract**.

## Execution Contract

### 1. Canonical Paths

Skills must use canonical artifact roots unless a deviation is explicitly justified.

Preferred roots:

- `docs/` for durable project records
- `.agent/staging/` for temporary staged reports
- `src/` for implementation artifacts
- `tests/` for verification artifacts

Rules:

- Do not mix `docs/` and `.failsafe/governance/` for the same artifact class.
- Do not invent a new artifact root if an existing one already fits.
- If a temporary file is produced by one skill and consumed by another, both skills must reference the same path.

### 2. Referenced Assets Must Exist

A skill may only require:

- files bundled with the skill
- files in the standard QoreLogic repository contract
- optional files with explicit fallback behavior

Rules:

- If a helper script is not bundled, document a manual fallback.
- If a template is not bundled, do not claim that the skill generates from it.
- If a repo-specific file may be absent, mark it optional and define the fallback path.

### 3. Empty-State Behavior Must Be Explicit

Every skill must define behavior for missing initial conditions.

Examples:

- no git tags yet
- no upstream branch yet
- no project memory file
- no optional release docs
- no prior ledger entries beyond genesis

Rules:

- Missing-but-valid initial states must not be treated as hard failures.
- First-run behavior must be written as a normal flow, not left implied.

### 4. Cross-Skill Handoffs Must Align

If one skill depends on another skill's output, both must agree on:

- file path
- expected structure
- success/failure semantics
- who owns staging vs committing vs pushing

Rules:

- `audit` emits what `implement`, `status`, and `substantiate` read.
- `implement` stages; it does not silently redefine audit artifacts.
- `substantiate` verifies and stages unless explicit user-approved commit behavior is part of the skill.
- `release` is the only phase that may routinely commit/tag/push, and only with confirmation gates.

### 5. Portable Language by Default

Core skills should prefer reusable wording over project-locked wording.

Avoid unless intentionally project-bound:

- hard-coded repo names
- one-off memory filenames
- one specific manifest path as the only version source
- one specific release helper as the only execution path

Preferred pattern:

- "Use the repository's canonical version source (for example `package.json`, `pyproject.toml`, `Cargo.toml`...)"
- "If the helper exists, use it; otherwise perform the manual fallback"

## Ecosystem Fit Contract

### 6. Every Skill Must Fill a Gap

A skill must justify why it exists as a separate unit.

Each skill should be able to answer:

- What gap in the ecosystem does this fill?
- What job does it do that adjacent skills should not do?
- What breaks or becomes weaker if this skill is removed?

If those answers are weak, the content probably belongs in:

- an existing skill
- a reference file
- a template
- a subsection, not a new skill

### 7. Overlap Is Allowed, Redundancy Is Not

Overlap is healthy when skills touch the same phase from different roles.

Examples of healthy overlap:

- `plan` defines intent
- `audit` judges risk and approval
- `implement` builds
- `substantiate` verifies

Examples of bad redundancy:

- two skills performing the same release workflow with only cosmetic wording differences
- two skills both acting as generic fixers without a meaningful role difference
- a new skill created for a local convention that should have been an option inside an existing skill

### 8. Every Skill Must Have Boundaries

Each skill should define:

- what it is for
- what it is not for
- which adjacent skills it hands off to

Minimum boundary questions:

- What is this skill's primary phase?
- Which skill should run before it?
- Which skill should run after it?
- What tasks should be rejected and routed elsewhere?

### 9. Distinctiveness Test

Before adding or keeping a skill, run this test:

- Does it introduce a new phase or control point?
- Does it introduce a distinct persona with different decision logic?
- Does it package a repeated workflow too large for an existing skill section?
- Does it materially improve outcomes with bundled references/templates/examples?

If the answer to all of those is "no", the skill should usually be merged or removed.

### 10. Retirement / Merge Trigger

A skill should be merged or retired if:

- another skill absorbs its workflow cleanly
- its unique value collapses into formatting only
- its adjacent skills can cover the same work with less confusion
- it remains mostly project-specific while being presented as reusable

## Required Review Checklist

Before accepting a new or revised core skill, verify:

- [ ] Canonical artifact roots are used consistently
- [ ] All referenced files/scripts/templates exist or have fallbacks
- [ ] Empty-state behavior is explicit
- [ ] Cross-skill paths and handoffs align
- [ ] Commit / push / tag semantics are explicit
- [ ] Project-specific names are avoided unless intentional
- [ ] The skill fills a distinct ecosystem gap
- [ ] Adjacent-skill boundaries are clear
- [ ] Redundant behavior has been merged or removed

## Decision Rule

If a proposed change improves formatting but not execution clarity, portability, or ecosystem value, do not add a new skill for it.

If a proposed change improves execution clarity or ecosystem fit, prefer updating an existing skill before creating a new one.
