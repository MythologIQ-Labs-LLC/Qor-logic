# Plan: Phase 88 — gh-PR-state pre-check for /qor-research (GH #80)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #80

**boundaries**:
- limitations: the pre-check is advisory WARN-only — when a MERGED PR
  referencing the target issue is found, the skill surfaces it to the
  operator before continuing, but does not abort the cycle. The operator
  decides whether the existing PR truly closed the same target. The check
  searches the current repo only; cross-repo PRs that close consumer-workspace
  issues are out of scope (no `--repo` discovery). When `gh` is not on PATH
  or the target is not an existing GH issue, the step is skipped with a
  one-line note (parallels the Phase 75 declarative-tolerance pattern).
- non_goals: `/qor-auto-dev-1` SKILL.md is NOT updated by this seal because
  that skill does not live in this repo's canonical SSoT. The repo owns
  `qor/skills/sdlc/qor-research/SKILL.md` only; `/qor-auto-dev-1` lives at
  the user-side install path (`~/.claude/skills/qor-auto-dev-1/SKILL.md`)
  and is governed externally. GH #80 names both skills; this phase ships the
  in-repo half. The same Step 2.5 prose can be applied externally — the
  handoff documents the recommended companion change.
- exclusions: no changes to `/qor-plan`, `/qor-implement`, `/qor-audit`,
  `/qor-substantiate`. Step 2.5 is scope-conditional (only runs when the
  research target is an existing GH issue number); non-issue research
  targets (API surfaces, codebases, dependencies) behave identically to
  today.

## Open Questions

None.

## Feature Inventory Touches

Empty. This plan touches a governance skill (`qor/skills/sdlc/qor-research/SKILL.md`)
and adds a wiring test under `tests/`; it introduces no `src/` user-facing
feature. `feature_inventory_touches`: `[]`.

## Design notes

GH #80 documents a concrete waste-cycle: a full `/qor-auto-dev-1` pass (plan
iter-1 written, audit PASS, implementation staged) was discovered redundant
because a PR had MERGED the same fix from a different branch hours earlier.
No code-side re-survey would have caught it because the fix existed only on
the merged branch, not on the working branch the skill was inspecting.

The minimal correction is two `gh pr list` searches before fresh research
begins on an existing-issue target: one for the literal `#<N>` token, one
for the issue number in the PR body. If either returns a MERGED PR, the
skill surfaces it (number, state, mergedAt, title) and asks the operator
to confirm whether to proceed.

Per `[[feedback-progressive-disclosure]]` (the GH #92 corpus-bloat lesson),
the change is kept lean: a single Step 2.5 sub-section in
`qor/skills/sdlc/qor-research/SKILL.md`, no new doctrine file, no chained
reference. The behavior is small enough that inline prose is honest; new
sub-pass / step prose escalation would be over-engineered for a five-line
check.

The lint test follows the `tests/test_audit_skill_iteration_lint_wiring.py`
pattern (Phase 84): an anchored positive test that asserts the Step 2.5
section cites both `gh pr list` invocations and the MERGED-PR surfacing
directive, paired with a strip-and-fail negative that proves the assertion
collapses when the section is removed. Per
`qor/references/doctrine-test-functionality.md`: presence-only checks are
forbidden; the test verifies behavior (the operative directive carries the
right shell commands and operative verbs), not artifact existence.

## Phase 1: Step 2.5 issue-state pre-check + lint enforcement

### Affected Files

- `qor/skills/sdlc/qor-research/SKILL.md` — insert Step 2.5 between Step 2
  (State Verification) and Step 3 (Target Discovery). Scope-conditional:
  fires only when the target is an existing GH issue number.
- `tests/test_qor_research_issue_state_check.py` — NEW. Anchored positive
  + strip-and-fail negative wiring tests for the Step 2.5 prose.
- `docs/plan-qor-phase88-pr-state-precheck.md` — NEW. This plan file.

### Unit Tests

- `tests/test_qor_research_issue_state_check.py`
  - `test_step_2_5_anchored_in_qor_research_skill` — read the SKILL.md,
    isolate the `### Step 2.5` section by header; assert it cites the
    literal `gh pr list --state all --search "#` substring (covers the
    `#<N>` form), the literal `in:body` substring (covers the body-search
    form), and the operative surfacing directive containing the substring
    `MERGED` and the substring `surface`. Three independent substring
    assertions so a partial decay (e.g., one command removed) still fails.
  - `test_step_2_5_section_removed_breaks_anchored_assertions` —
    strip-and-fail negative: locate the `### Step 2.5` block in the
    SKILL.md text, remove it in-memory, re-isolate; assert the previous
    three substrings are no longer present in the isolated section. This
    proves the positive test would catch silent deletion of the block.
  - `test_step_2_5_scope_conditional_language_present` — assert the
    section explicitly carries the substring `existing GH issue` (or
    equivalent scope-narrowing language). This guards against the prose
    decaying into an unconditional check that fires for non-issue
    research targets and burns `gh` API calls every cycle.

### Changes

`qor/skills/sdlc/qor-research/SKILL.md` — insert the following block between
the existing Step 2 (State Verification) section and Step 3 (Target
Discovery):

```markdown
### Step 2.5: Issue-state pre-check (when target is an existing GH issue)

If the research target is an existing GitHub issue (e.g., `#80`), check
whether a PR has already addressed it before doing fresh research:

```bash
gh pr list --state all --search "#<ISSUE_NUMBER>" --limit 5 \
  --json number,state,title,mergedAt
gh pr list --state all --search "in:body <ISSUE_NUMBER>" --limit 5 \
  --json number,state,title
```

If any PR is MERGED and closes the target issue, surface the PR number,
state, mergedAt, and title to the operator before continuing. The operator
decides whether the existing PR truly closed the same target (the body of
an old issue can still read as a fresh defect; `/qor-research` should
not redo work that has already shipped).

When `gh` is not on PATH or the target is not an existing GH issue
(e.g., the target is an API surface or a dependency rather than an issue
number), skip this step with a one-line note and continue.

Closes GH #80; pairs with the existing target-verification chain.
```

The insertion preserves the existing Step 0 (chain position) and Step 0.2
(install drift check) and Step 1 (Identity Activation) and Step 2 (State
Verification) verbatim. No other section is touched.

## CI Commands

- `python -m pytest tests/test_qor_research_issue_state_check.py -q` — Step 2.5 anchor + strip-and-fail + scope-conditional language wiring tests.
- `python -m pytest tests/ -q` — full regression suite.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase88-pr-state-precheck.md` — plan-internal text-consistency.
