# Plan: Phase 86 — Post-merge seal-tag push (GH #98)

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: GH #98

**boundaries**:
- limitations: this fixes only the seal-tag PUSH timing in `/qor-substantiate`.
  Tag CREATION stays at Step 9.5.5 on the seal commit (the Phase 33 timing
  fix is correct and unchanged). The `release.yml` workflow and the `main`
  ruleset are not modified.
- non_goals: not changing `governance_helpers.create_seal_tag`; not changing
  the Step 9.6 push/merge menu's four options themselves; not removing
  `build-and-publish` from the ruleset (issue #98 option 2, declined in
  favour of option 1).
- exclusions: phase 86's own seal still tags-before-merge — the fix takes
  effect for phase 87 onward, so phase 86's own PR still needs `--admin`.

## Open Questions

None.

## Design notes

The bug is one line. `/qor-substantiate` Step 9.6 line "Push `--tags`
alongside the branch push" pushes the annotated `v{X.Y.Z}` tag together with
the phase branch — before the seal commit is on `origin/main`. `release.yml`
triggers `on: push: tags` and its `build-and-publish` job guards with
`git merge-base --is-ancestor "$GITHUB_SHA" origin/main`; the tag commit is
not yet on main, so the job fails, attaches as a red check on the PR head,
and the `main` ruleset blocks the merge — the merge that would make the tag
valid. The fix keeps tag CREATION pre-merge (the tag must point at the real
seal commit) and moves only the tag PUSH to after the seal commit reaches
`origin/main`. A new Step 9.7 gates the tag push on the same
`merge-base --is-ancestor` reachability check that `release.yml` uses, so
the push and the publish guard agree by construction.

## Phase 1: Defer the seal-tag push to post-merge

### Affected Files

- `tests/test_substantiate_tag_push_timing.py` - NEW. Anchored wiring tests
  (with strip-and-fail negatives) for the Step 9.6 / Step 9.7 prose.
- `qor/skills/governance/qor-substantiate/SKILL.md` - rewrite the Step 9.6
  tag-push directive to push the branch only; add Step 9.7 (post-merge
  seal-tag push); add one Constraints line.
- `qor/references/doctrine-governance-enforcement.md` - extend the
  `seal_tag_timing` note with the push-timing clause.

### Unit Tests

- `tests/test_substantiate_tag_push_timing.py` (uses a fence-aware,
  level-aware markdown-section extractor like the one in
  `tests/test_inverse_coverage_skill_wiring.py`, so `### Step 9.6` stops at
  the next equal-or-shallower header)
  - `test_step_9_6_pushes_branch_only_not_tags` — extract the Step 9.6
    section from `qor-substantiate/SKILL.md`; assert the section is non-empty
    AND does not contain the token `--tags` (regression guard: the
    push-the-tag-with-the-branch directive is gone).
  - `test_step_9_6_defers_tag_push_to_post_merge` — extract the Step 9.6
    section; assert it directs the tag push to be deferred (it references
    the post-merge tag-push step and states the branch is pushed without
    the tag).
  - `test_step_9_6_defer_assertion_fails_when_directive_stripped` —
    strip-and-fail negative: remove the deferral directive line from an
    in-memory copy; assert the Step 9.6 defer assertion no longer holds.
  - `test_step_9_7_pushes_tag_gated_on_origin_main_reachability` — extract
    the Step 9.7 section; assert it (a) pushes the seal tag and (b) gates
    the push on the seal commit being reachable from `origin/main` via a
    `git merge-base --is-ancestor` check.
  - `test_step_9_7_assertion_fails_when_section_removed` — strip-and-fail
    negative: remove the Step 9.7 section; assert the Step 9.7 assertion no
    longer holds.

### Changes

`qor/skills/governance/qor-substantiate/SKILL.md`:

- **Step 9.6**: replace the trailing line "Annotated tag was already
  created in Step 9.5.5; do not re-offer. Push `--tags` alongside the
  branch push." with: the annotated tag was created in Step 9.5.5 but is
  NOT pushed here — `release.yml` refuses to publish a tag whose commit is
  not yet on `origin/main`, and that failing check blocks the seal PR.
  Push the branch only; Step 9.7 pushes the tag once the seal commit is on
  `origin/main`. The four options' own commands already push branch-only
  (`git push origin <branch>`, `gh pr create`); only this trailing
  instruction changes.
- **Step 9.7 (NEW): Post-merge seal-tag push (Phase 86 wiring; GH #98)** —
  inserted between Step 9.6 and `## Failure Scenarios`. Prose: the tag
  stays local until the seal commit reaches `origin/main`; push it then,
  gated on reachability:

  ```bash
  git fetch origin main
  if git merge-base --is-ancestor "$SEAL_COMMIT" origin/main; then
    git push origin "$SEAL_TAG"
  else
    echo "Seal commit not on origin/main yet; tag $SEAL_TAG held local. Push after merge: git push origin $SEAL_TAG"
  fi
  ```

  Per Step 9.6 option: option 3 (merge to main locally) runs this right
  after `git push origin main`; option 2 (push + PR) runs it after the PR
  is merged; options 1 and 4 leave the tag local until the operator merges,
  and the operator pushes it then. The reachability gate mirrors
  `release.yml`'s own `merge-base --is-ancestor` guard so the tag push and
  the publish guard agree by construction.
- **Constraints**: add one line — never push the seal tag before the seal
  commit is reachable from `origin/main`; tag creation is Step 9.5.5
  (pre-merge), tag push is Step 9.7 (post-merge).

`qor/references/doctrine-governance-enforcement.md`: extend the
`seal_tag_timing` note — the tag is CREATED at Step 9.5.5 (pre-merge, on
the seal commit) but PUSHED at Step 9.7 (post-merge), because `release.yml`
triggers on tag push and its `build-and-publish` guard refuses a tag whose
commit is not reachable from `origin/main`. Pushing the tag with the branch
makes `build-and-publish` fail on the seal PR and blocks the merge.

### Dependent tests (verified unaffected)

Two existing tests anchor to the `qor-substantiate/SKILL.md` step layout
this plan mutates. Both are verified unaffected and are run in the
regression gate:

- `tests/test_seal_flow_ordering.py` — slices the Step 9.5.5 section
  bounded by `body.find("### Step 9.6")`. This plan does NOT move the
  `### Step 9.5.5` or `### Step 9.6` headers; the new `### Step 9.7` inserts
  AFTER Step 9.6 (between Step 9.6 and `## Failure Scenarios`). The
  Step 9.5.5↔9.6 boundary the test slices on is unchanged — unaffected.
- `tests/test_substantiate_tag_timing_wired.py` — its `_STEP_HEADER_RE`
  matches `### Step 9.N` headers into an ordered list and slices each
  section to the next header. Its `_step_section("9.5.5")` ends at the next
  step header, which remains `### Step 9.6`. The new `### Step 9.7` joins
  the ordered list but does not change the 9.5.5 or 9.6 slice boundaries —
  unaffected.

Both run under `python -m pytest tests/ -q` and the dedicated CI command
below confirms them green after the SKILL.md edit.

## CI Commands

- `python -m pytest tests/test_substantiate_tag_push_timing.py -q` — Phase 1 wiring tests (anchored + strip-and-fail).
- `python -m pytest tests/test_seal_flow_ordering.py tests/test_substantiate_tag_timing_wired.py -q` — the two dependent step-layout tests, confirmed green after the SKILL.md edit.
- `python -m pytest tests/ -q` — full regression suite.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase86-post-merge-tag-push.md` — plan-internal text-consistency.
