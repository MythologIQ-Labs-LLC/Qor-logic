# Plan: Seal-artifact generation after the entry it counts

**iteration**: 4

**change_class**: hotfix

**doc_tier**: standard

**Note on the class.** `hotfix` is a release class, so this phase bumps the patch version and tags. It is also exempt from the release-class condition guarding the seal-artifact ABORT, so the gate this plan relocates will not ABORT on this phase's own seal. The third deliverable's D4 does not rely on it.

**boundaries**:
- limitations: Fixes one defect with one cause -- a generate/check pair positioned before its input exists -- and corrects the documentation surfaces that state the old position. The other four presence-over-truth controls named in the post-223 research brief are out of scope.
- non_goals: No change to what a badge counts, to the `tests` badge tolerance, or to which change classes ABORT on stale artifacts.
- exclusions: GH #333, GH #332, GH #320, GH #286, and the `plan_grep_lint` citation-form gap recorded under Open Questions Q2.

## What the earlier iterations got wrong

The tribunal VETOed iteration 1 (ledger entry #582). The substantive finding:

1. The corrected step was placed "between Step 7 and Step 7.4" on the reading that step numbers are execution order. They are not, in that region: Steps 7.4 and 7.5 produce content that goes *into* the seal entry before Step 7 computes its hash. The corrected step would have run in the same pre-append window as the original. Iteration 2 moved the anchor to Step 7.7.5, which this iteration keeps.

Four more were completeness: two existing tests die on the tightened comparison, a spine invariant and its pinning test went unlisted, three documentation surfaces state the placement being changed, and the plan named a presence-only lint as its own truth-verification. All are addressed here.

A sixth finding claimed a second root cause -- that README.md never reaches the seal commit, making the ordering fix inert. **Iteration 2 was written around it and it was refuted.** `git show --stat` lists README.md in all seven recent seal commits, and `git show a55f1fc:README.md` carries `Ledger-577%20entries` against a post-append truth of 578. README reaches the commit carrying its pre-append value; operators stage more than the documented block. The ordering is the only cause. Iteration 3 removed the two-cause framing, the deliverable, and the test that iteration 2 built on it. Iteration 4 drops the documented-staged-set edit entirely: correcting it would mean listing five omissions, not one, and it is not a cause of this defect, so it is filed separately rather than half-fixed here. Recorded in `docs/SHADOW_GENOME.md` as `SG-VerifiedPremiseUncheckedConclusion-A`.

## Open Questions

**Q1 (non-blocking, record only).** Why did most sealed phases since Phase 164 pass the CI `seal-artifacts currency` step, given the drift is structural on every seal? Two occurrences are on record (`851c9f4` after Phase 215, `08f594a` after Phase 223). Recorded in the seal entry if it surfaces during implementation.

**Q2 (out of scope, file separately).** `plan_grep_lint` does not truth-check the grep-evidence form that `/qor-plan` Step 2 mandates. `qor/scripts/plan_grep_lint.py:109` resolves only bare source-file citations, and `:230` enumerates `git show <ref>:<path>` as presence-only. Every Locked Decision below is therefore machine-unverified and was verified by hand.

## Locked Decisions

Every statement below was re-run with `git show` against `v0.146.0` during iteration 2 authoring and re-walked in full at iterations 3 and 4, per the Phase 72 iter-N>1 contract. The lint cannot check this form (Q2), so the verification is manual and is recorded as such.

**LD-1: The currency gate reads pre-seal state.**

> `git show v0.146.0:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'seal_artifacts --check --repo-root'` -> `365:  qor-logic scripts seal_artifacts --check --repo-root . \`

**LD-2: The generator also runs pre-seal.**

> `git show v0.146.0:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'seal_artifacts --write --phase'` -> `305:qor-logic scripts seal_artifacts --write --phase <N> --snapshot <YYYY-MM-DD>`

**LD-3: Step numbering is not execution order between Step 7 and Step 7.7.** Steps 7.4 and 7.5 generate content the seal entry carries, so they precede the append despite their numbers.

> `git show v0.146.0:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'Computes NIST SSDF practice tags'` -> `413:Computes NIST SSDF practice tags for the SESSION SEAL entry body BEFORE Step 7 computes content_hash. Scope + grandfather boundary: \`references/seal-gate-ladder.md\`.`
> `git show v0.146.0:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'Operator pastes'` -> `423:Operator pastes \`$SSDF_LINE\` into the SESSION SEAL entry body before Step 7 computes content_hash. Per \`qor/references/doctrine-nist-ssdf-alignment.md\` §"Phase 52 wiring (forward-only emission)".`

**LD-4: Step 7.7 is the first step that asserts the entry exists.** It is therefore the earliest correct anchor for regeneration.

> `git show v0.146.0:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'Runs \*after\* Step 7 has appended'` -> `469:Runs *after* Step 7 has appended the SESSION SEAL entry. Verifies the entry exists for this phase and the latest chain hash is internally consistent -- closes SG-AdjacentState-A. **Phase 76 (GH #51)** adds a \`previous_hash uniqueness\` pass: a duplicate signals a concurrent federation race -> reconcile per \`SG-ConcurrentLedgerRace-A\` (pre-Phase-76 entries grandfathered). Helper detail + rationale: \`references/seal-gate-ladder.md\`.`

**LD-5: The documented staged set omits README.md, while the actual seal commits contain it.** These are the only two `git add` lines in the skill, so the written ceremony understates practice. This is a documentation gap, not a cause: `git show --stat a55f1fc` lists `README.md`, and `git show a55f1fc:README.md` -> `Ledger-577%20entries` against a post-append truth of 578, so the badge reaches the commit carrying its pre-append value. Both commands were run by the orchestrating agent, not by the independent reviewer, which had no shell; the reviewer corroborated the numeric half from the working tree (`### Entry #` count 580, README declaring 578, entries #581 and #582 appended this cycle) and could not test the `--stat` half.

> `git show v0.146.0:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE '^  git add'` -> `548:  git add CHANGELOG.md docs/CONCEPT.md docs/ARCHITECTURE_PLAN.md docs/META_LEDGER.md` and `549:  git add docs/SYSTEM_STATE.md docs/BACKLOG.md src/ ".qor/gates/$SESSION_ID/"`

**LD-6: The placement is a spine invariant, pinned as an exact token.**

> `git show v0.146.0:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'Step 6\.5 README badge currency check'` -> `46:2. Step 6.5 README badge currency check -> \`|| ABORT\` on drift.`
> `git show v0.146.0:tests/test_skill_corpus_consolidation.py | grep -nE 'Step 6\.5 README badge currency check'` -> `95:    "Step 6.5 README badge currency check -> \`|| ABORT\`",`

**LD-7: The placement is also stated as doctrine and in the ladder reference.**

> `git show v0.146.0:qor/references/doctrine-governance-enforcement.md | grep -nE 'Step 6/6\.5 wiring regression lock'` -> `177:Locked at the test layer by \`tests/test_seal_artifacts.py\` (behavioral tests of the generators against synthetic fixtures) and \`tests/test_substantiate_seal_artifacts_wiring.py\` (Step 6/6.5 wiring regression lock). The pre-164 live-equality class (5 badge tests + 2 SYSTEM_STATE header tests + 6 prose-wiring tests) is retired: it asserted generated-artifact state against moving truth and broke on nearly every seal (phases 121/122/123/140).`
> `git show v0.146.0:qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md | grep -nE '^## Step 6 seal-artifact generation'` -> `140:## Step 6 seal-artifact generation (Phase 164 wiring; generate, don't assert)`

**LD-8: The header dimension already absorbs the early write with a one-step window.**

> `git show v0.146.0:qor/scripts/seal_artifacts.py | grep -nE 'latest <= got <= latest \+ 1'` -> `175:        if not latest <= got <= latest + 1:`

**LD-9: The ledger badge is checked exactly; the tests badge carries a tolerance.** The pattern matches two lines; both are shown.

> `git show v0.146.0:qor/scripts/badge_currency.py | grep -nE 'README declares \{declared_value\}, truth \{actual\}'` -> `207:                    f"tests: README declares {declared_value}, truth {actual} "` and `212:                f"{key}: README declares {declared_value}, truth {actual}"`
> `git show v0.146.0:qor/scripts/badge_currency.py | grep -nE 'tests_tolerance: int = 5'` -> `186:    tests_tolerance: int = 5,`

**LD-10: The existing test fixture seals at Phase 7 while its callers write phase 8.** The tolerance is what makes those assertions pass today.

> `git show v0.146.0:tests/test_seal_artifacts.py | grep -nE 'SESSION SEAL -- Phase 7 something'` -> `50:### Entry #3: SESSION SEAL -- Phase 7 something (v0.1.0)`

**LD-11: The step ordering is already pinned, to the defective order.**

> `git show v0.146.0:tests/test_substantiate_seal_artifacts_wiring.py | grep -nE 'def test_substantiate_steps_6_and_6_5_invoke_seal_artifacts'` -> `19:def test_substantiate_steps_6_and_6_5_invoke_seal_artifacts():`

**LD-12: Regenerating after the append does not disturb the seal.** The content hash is taken over the plan file.

> `git show v0.146.0:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'Seal hashes via'` -> `405:Seal hashes via \`ledger_hash.content_hash(plan)\` + \`chain_hash\` (bound at Step 7.7; GAP-GOV-01).`

## Phase 1: Prove the defect and the fix from the mechanism

### Affected Files

- `tests/test_seal_artifacts_ordering.py` - NEW. Drives `collect_counts` / `update_files` / `check_files` over a fixture repo across a simulated seal append.

### Changes

Build a fixture repo carrying a README with a `Ledger-<n> entries sealed` badge, a `docs/META_LEDGER.md` with a known number of `### Entry #N: SESSION SEAL -- Phase M` entries, and a `docs/SYSTEM_STATE.md` with `**Phase**:` / `**Snapshot**:` markers. Append one further SESSION SEAL entry to model Step 7, then exercise the two orderings directly. No subprocess, no network, no clock or randomness: entry text and snapshot date are fixture constants.

### Unit Tests

- `tests/test_seal_artifacts_ordering.py::test_check_before_append_passes_over_a_badge_that_is_about_to_be_stale` - with badges written from pre-append truth, asserts `check_files` returns an empty list *before* the append and a ledger mismatch naming the declared value and the truth *after* it. One test holds both halves of the blindness: the gate's pass and the fact it was wrong. This is the assertion the existing suite does not make.
- `tests/test_seal_artifacts_ordering.py::test_write_after_append_leaves_no_mismatch` - in the same fixture, appends the seal entry first, then `update_files`, then asserts `check_files` returns an empty list. The sufficiency direction: it is the only mechanical evidence that the reordering achieves anything, and no existing test makes it (`test_main_write_then_check_exit_codes` stops at the failing check after its append and never re-writes; `test_check_files_clean_after_write` never appends).

### Note on coverage overlap

`tests/test_seal_artifacts.py::test_main_write_then_check_exit_codes` already writes, checks clean, appends a seal entry, and asserts the following check fails naming `ledger`. Iteration 1 proposed three tests here; two restated it and are dropped. What remains is the pair the suite genuinely lacks -- that the check *passes* in the pre-append window, and that it passes again once the write follows the append. Neither direction is covered today, and the second is the one that demonstrates the fix works rather than that the defect exists.

## Phase 2: Move the pair after Step 7.7

### Affected Files

- `tests/test_substantiate_seal_artifacts_wiring.py` - rewritten; the two assertions binding the invocations to Steps 6 and 6.5 are replaced.
- `tests/test_skill_corpus_consolidation.py` - `SUBST_INVARIANTS` token updated to the new step number.
- `qor/skills/governance/qor-substantiate/SKILL.md` - remove the `--write` invocation from Step 6 and the seal-artifact currency block from Step 6.5; add Step 7.7.5 carrying both; update the spine invariant at line 46.

### Changes

Step 6 keeps its system-state mapping and loses the `seal_artifacts --write` invocation. Step 6.5 keeps `check_documentation_currency` and loses the Phase 49/164 seal-artifact currency block. Both move into a new Step 7.7.5, placed after Step 7.7 and before Step Z, preserving the release-class condition and the ABORT semantics unchanged. Step 7.7 is the anchor because it is the first step that verifies the appended entry exists (LD-4); Steps 7.4 and 7.5 are numbered later but run earlier (LD-3).

Nothing between Step 7.7 and the Step 9.5 staging changes a counted input. Step Z writes a gate artifact, Step 7.8 reads, and Step 7.9 folds spec deltas into `qor/specs/<capability>/spec.md`, which is not a counted root; this plan declares no `spec_deltas`, so the fold is a no-op here.

The spine invariant at SKILL.md:46 becomes `Step 7.7.5 README badge currency check -> `|| ABORT` on drift.`, and the matching token in `SUBST_INVARIANTS` is updated to `Step 7.7.5 README badge currency check -> `|| ABORT``.

### Unit Tests

- `tests/test_substantiate_seal_artifacts_wiring.py::test_regeneration_follows_the_step_that_verifies_the_entry_exists` - asserts the character offset of the `seal_artifacts --write` invocation falls between the `### Step 7.7:` heading and the `git add` block. Bound to 7.7 rather than 7 because Step 7's numeric successors run before the append; an offset test against `### Step 7:` would have passed for iteration 1's defective placement. Both bounds are asserted: a lower bound alone is satisfied by any later position, including one after staging, where the regenerated README would miss the commit.
- `tests/test_substantiate_seal_artifacts_wiring.py::test_step_7_7_5_retains_abort_and_the_hotfix_exemption` - asserts the Step 7.7.5 region matches `seal_artifacts --check`, `ABORT`, and `hotfix exempt`. Carries forward the three properties the superseded Step 6.5 assertions protected.
- `tests/test_substantiate_seal_artifacts_wiring.py::test_step_6_no_longer_regenerates_seal_artifacts` - asserts the Step 6 region contains no `seal_artifacts --write`. Fails on a partial edit that adds Step 7.7.5 while leaving the original invocation, which would write twice and mask the ordering.

## Phase 3: Retire the tolerance the early write required

### Affected Files

- `tests/test_seal_artifacts.py` - fixture ledger's SESSION SEAL raised from Phase 7 to Phase 8 (LD-10); add coverage for the tightened comparison.
- `qor/scripts/seal_artifacts.py` - `_check_header` compares the recorded phase to the latest sealed phase for equality; module docstring updated to name the new step.

### Changes

Replace `if not latest <= got <= latest + 1:` with an equality comparison against `latest`. With the generator running after the append, the header records the phase whose entry exists, so the one-step window admits only states the reordered procedure cannot produce.

The fixture at `tests/test_seal_artifacts.py:50` is raised to Phase 8 so its two existing callers keep writing `phase=8` and keep asserting a clean check. The alternative -- changing the writes to `phase=7` -- would also pass, since `render_system_state_header` rewrites the Snapshot date as well as the phase and the fixture's `2026-06-10` differs from the written `2026-07-04`, so SYSTEM_STATE lands in `changed` either way. The fixture is raised instead because it keeps every existing assertion exercising the same values it exercises today, which is the smaller perturbation to coverage.

Raising the fixture makes the first `check_files` call in `test_check_files_reports_stale_badge_and_header` also return a header mismatch (7 against a latest of 8) that it did not return before. That test asserts only on `"skills"` at that point, so it passes, but its comment naming Phase 7 as "the latest sealed phase" goes stale and is corrected in the same edit.

**Razor and budget.** `qor/scripts/seal_artifacts.py` is 275 lines against the 250-line file cap -- pre-existing, and this edit replaces one condition with another, so it is line-neutral and introduces no overage. `_check_header` stays at 23 lines, nesting depth 3, no ternaries. The Phase 2 SKILL.md edit relocates a block verbatim and adds one heading, so it is near-neutral against the `skill_size_budget` EXCEEDED threshold asserted at `tests/test_skill_corpus_consolidation.py:52-54`.

### Unit Tests

- `tests/test_seal_artifacts.py::test_header_one_phase_ahead_of_latest_seal_is_a_mismatch` - a SYSTEM_STATE recording Phase N+1 against a latest seal of Phase N returns a mismatch naming both numbers. This state passed before this phase and is the slack being retired.
- `tests/test_seal_artifacts.py::test_header_equal_to_latest_seal_is_current` - Phase N against a latest seal of Phase N returns no header mismatch. Confirms the tightening did not invert the comparison.
- `tests/test_seal_artifacts.py::test_header_behind_latest_seal_is_a_mismatch` - Phase N-1 against a latest seal of Phase N returns a mismatch. Confirms the lower bound survived the edit.

## Phase 4: Correct the surfaces that state the old placement

### Affected Files

- `qor/references/doctrine-governance-enforcement.md` - lines 175 and 177 restate the placement and rename the wiring lock.
- `qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md` - heading at 140, the sentence at 149, and the operator-judgment section at 165-172.
- `.github/workflows/ci.yml` - the comment at 100-102 naming Step 6.5 as where the Tests badge is verified.
- `qor/scripts/badge_currency.py` - module docstring cross-reference.
- `tests/test_seal_artifacts.py`, `tests/test_readme_badge_currency.py`, `tests/test_system_state_freshness.py`, `tests/test_badge_layout_config.py` - docstrings naming Step 6.5 as the gate site.

### Changes

Each surface names Step 7.7.5 in place of Step 6 / Step 6.5. No semantic change beyond the placement.

**The documented staged set is deliberately not touched.** `SKILL.md:548-549` omits `README.md`, and also `docs/SHADOW_GENOME.md`, the plan file, `.agent/staging/AUDIT_REPORT.md`, and the `qor/specs/` paths Step 7.9 writes. Adding README alone would leave the block inaccurate in four other ways while appearing to have been corrected, and the block is not a cause of the defect this phase fixes (LD-5). It is filed as a separate documentation issue rather than half-fixed here.

### Unit Tests

None. These are prose surfaces with no invokable unit; the behavior they describe is asserted in Phases 2 and 3. Declared here rather than omitted so the Affected Files contract is complete, per `SG-AffectedFilesContract-A`.

## Feature Inventory Touches

Empty. This plan touches governance skills, governance scripts, documentation, and tests. There is no `src/` tree in this repository and no user-touchable feature surface is introduced or modified.

## Definition of Done

### Deliverable: regeneration follows the step that verifies the entry exists

- **D1**: The gate that grades badge currency reads the ledger state the seal produced, not the state that preceded it.
- **D2**: `qor/skills/governance/qor-substantiate/SKILL.md` carries Step 7.7.5 after Step 7.7 and before Step Z, holding `seal_artifacts --write` followed by `seal_artifacts --check` under the existing release-class condition; Step 6 and Step 6.5 carry neither; the spine invariant at line 46 names the new step.
- **D3**: The Phase 224 seal entry records the relocation, the retired header window, and Q1 if it surfaced. There is no staging fix in this phase; the documented staged set is filed separately.
- **D4**: `test_check_before_append_passes_over_a_badge_that_is_about_to_be_stale` shows the gate passed over a badge that was about to be wrong; `test_write_after_append_leaves_no_mismatch` shows the reordered sequence leaves nothing for it to miss. `test_regeneration_follows_the_step_that_verifies_the_entry_exists` binds the procedure to that sequence, and is a document-position assertion rather than a behavioral one -- the mechanical evidence is the first two.

### Deliverable: the header tolerance is retired

- **D1**: The header comparison admits only states the reordered procedure can produce.
- **D2**: `qor/scripts/seal_artifacts.py::_check_header` compares the recorded phase to `latest` for equality.
- **D3**: The seal entry states that the retired window was slack left by the early write.
- **D4**: `test_header_one_phase_ahead_of_latest_seal_is_a_mismatch` passes, and it fails against the pre-phase implementation.

### Deliverable: this phase's own seal is clean without a follow-up commit

- **D1**: No manual badge-refresh commit follows the Phase 224 seal.
- **D2**: n/a -- observed, not coded.
- **D3**: The Phase 224 seal commit is the last commit on the branch before the merge, with no `fix: regenerate ...` successor. (An earlier form of this criterion also required `git show --stat` to list `README.md`; that is already true of every recent seal per LD-5, so it grades nothing and is removed.)
- **D4**: `python -m qor.scripts.seal_artifacts --check --repo-root .` exits 0 against the post-seal tree, and the CI `seal-artifacts currency` step is green on the pull request without an intervening badge commit. CI triggers on `push: branches: [main]` and `pull_request`, so this is observed once the PR exists, against the merge ref.

## CI Commands

- `python -m pytest tests/test_seal_artifacts_ordering.py tests/test_seal_artifacts.py tests/test_substantiate_seal_artifacts_wiring.py tests/test_skill_corpus_consolidation.py -q` — the four test files this plan adds to or rewrites
- `python -m pytest -q` — full suite, run twice consecutively to confirm determinism
- `python -m ruff check qor tests` — lint parity with CI
- `python -m qor.scripts.seal_artifacts --check --repo-root .` — badge and header currency against the working tree
- `python -m qor.scripts.dist_compile` — recompiles the `qor/dist/variants/*` copies of the edited SKILL.md; `check_variant_drift.py` exits 1 on byte drift in CI
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase224-seal-artifact-ordering.md` — asserts this plan states each command and path identically at every site
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase224-seal-artifact-ordering.md` — reports zero citations truth-checked for this plan; the grep-evidence form is presence-only at `qor/scripts/plan_grep_lint.py:230`, so this command confirms pairing and not correctness. The twelve Locked Decisions were verified by hand with `git show` during iteration 2 authoring.
