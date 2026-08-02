# Plan: attribution co-author policy and seal-subject coverage (Phase 207)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: none (no new governance concept; `AttributionPolicy` is a
code symbol local to `qor/scripts/attribution_policy.py`)

**boundaries**:
- limitations: The policy is read from `.qorlogic/config.json` at the repository
  root, the same file `qor-logic init` writes and `external_reviewer` reads. No
  environment variable, no global-scope merge, no per-commit override. The
  policy governs only whether the model co-author line is REQUIRED and EMITTED;
  it never suppresses the `Authored via [Qor-logic SDLC]` line.
- non_goals: No rewriting of published history to add or remove trailers on
  existing commits. No change to `pr_footer` or `changelog_attribution_line`. No
  change to the emoji carve-out. No new CLI subcommand.
- exclusions: The operator's own instruction files are out of scope; this plan
  changes what Qor-logic REQUIRES, not what any operator declares elsewhere.

## Open Questions

None.

## Locked Decisions

**LD-1 — The framework line is the attribution this doctrine exists for; the
model co-author line is a separate, GitHub-specific concern.**

`git show HEAD:qor/scripts/attribution.py | grep -nE 'def commit_trailer\(|Co-Authored-By: \{model\}|def message_has_full_trailer' -> 21: def commit_trailer( | 38: f"Co-Authored-By: {model} <{model_email}>" | 100: def message_has_full_trailer(message: str) -> bool:`

`doctrine-attribution.md` states the co-author line's purpose in one sentence:
"the `Co-Authored-By:` line stays so GitHub's contributor-stats machinery still
records the model." That is a reporting convenience, not a governance
requirement. The Merkle chain, the gate artifacts, and the `Authored via
[Qor-logic SDLC]` line are what establish provenance. An operator who forbids AI
co-author trailers loses nothing governance-bearing by omitting it, so the
requirement becomes declarable rather than absolute.

**LD-2 — `attribution.py` is declared pure and must stay pure.**

The doctrine's Helper API contract declares: "**Pure**: no I/O, no env reads, no
time/random/network coupling." The policy read is I/O, so it lives in a separate
module and reaches `attribution.py` only as an already-resolved keyword. This
also keeps the pure helper testable without a filesystem.

**LD-3 — The live-history seal guard silently skips any seal commit whose
subject does not contain a phase number, and the documented seal-commit template
produces exactly that subject.**

`git show HEAD:tests/test_attribution_tiered_usage.py | grep -nE 'def _phase_num_from_subject|return int\(m' -> 117: def _phase_num_from_subject(subject: str) -> int | None: | 119: return int(m.group(1)) if m else None`

`grep -n 'seal: \[plan-slug\]' qor/skills/governance/qor-substantiate/SKILL.md -> 616:   seal: [plan-slug] - Session substantiated`

`_seal_phase_in_scope(None)` returns False, so an unparseable subject is skipped
rather than flagged. Measured against the last twelve seal commits, two are
unparseable and both follow the SKILL.md template verbatim. An operator who
follows the documented template is therefore exempted from the guard by
accident. This is the mechanism by which the Phase 206 seal commit, which
deliberately omitted the co-author line, passed the full suite unnoticed.

## Phase 1: Declarable co-author requirement

### Unit Tests

- `tests/test_attribution_coauthor_policy.py::test_commit_trailer_omits_coauthor_when_policy_disables_it` -
  calls `commit_trailer(model, model_coauthor=False)` and asserts the returned
  string contains the `Authored via [Qor-logic SDLC]` line and no
  `Co-Authored-By:` line, while the default call still returns both.
- `::test_message_has_full_trailer_accepts_framework_line_only_when_not_required` -
  feeds a message carrying only the framework line and asserts
  `message_has_full_trailer(msg, require_coauthor=False)` is True while
  `message_has_full_trailer(msg)` is False, so the default stays strict.
- `::test_message_has_full_trailer_still_rejects_missing_framework_line` -
  feeds a message carrying only `Co-Authored-By:` and asserts False under BOTH
  settings; relaxing the co-author requirement must never relax the framework
  requirement.
- `::test_policy_defaults_to_requiring_coauthor_when_config_absent` -
  resolves the policy against a temporary directory with no
  `.qorlogic/config.json` and asserts `model_coauthor` is True, so every
  existing adopter is unchanged.
- `::test_policy_reads_declared_false_from_config` - writes
  `{"attribution": {"model_coauthor": false}}` and asserts the resolved policy
  is False.
- `::test_policy_tolerates_malformed_config` - writes invalid JSON and asserts
  the resolver returns the strict default rather than raising, so a corrupt
  config fails closed toward requiring attribution.
- `::test_seal_trailer_check_honors_declared_policy` - builds a temporary git
  repository with a framework-line-only seal commit plus a config declaring
  `model_coauthor: false`, runs the `seal_trailer_check` CLI against it, and
  asserts exit 0; with no config, the same commit exits 1.

### Affected Files

- `qor/scripts/attribution_policy.py` - NEW. `AttributionPolicy` (frozen,
  one field `model_coauthor: bool = True`) and `resolve_policy(repo_root)`
  reading `.qorlogic/config.json` -> `attribution.model_coauthor`, tolerant
  parse returning the strict default on absent file, absent key, or malformed
  JSON.
- `qor/scripts/attribution.py` - `commit_trailer` gains a keyword-only
  `model_coauthor: bool = True`; `message_has_full_trailer` gains a
  keyword-only `require_coauthor: bool = True`. Stays pure.
- `qor/scripts/seal_trailer_check.py` - resolves the policy from `--repo-root`
  and passes `require_coauthor` through; the failure message names the policy
  when it is in force.

### Changes

Both new parameters default to today's behavior, so no call site changes
meaning. The failure message gains a sentence naming
`.qorlogic/config.json -> attribution.model_coauthor` so an operator hitting the
gate learns the declarable escape rather than being told only to comply.

## Phase 2: Close the seal-subject coverage hole

### Unit Tests

- `tests/test_attribution_coauthor_policy.py::test_seal_subject_without_phase_number_is_flagged_not_skipped` -
  asserts the seal-scope predicate treats an unparseable subject as in scope
  when the commit is newer than the enforcement floor, rather than returning
  False and skipping.
- `tests/test_attribution_tiered_usage.py::test_seal_phase_in_scope_excludes_below_floor` -
  amended so `None` no longer asserts an exemption; the phase-number floor
  still excludes 48.

### Affected Files

- `tests/test_attribution_tiered_usage.py` - `_seal_phase_in_scope` no longer
  exempts an unparseable subject. Seal commits whose subject carries no phase
  number are checked against the same full-trailer rule, honoring the resolved
  policy so the Phase 206 seal is judged under the operator's declared setting
  rather than skipped.
- `qor/skills/governance/qor-substantiate/SKILL.md` - the Step 9.5 seal-commit
  template becomes `seal: phase <N> - <plan-slug>`, matching what the doctrine
  and the guard already expect.
- `qor/references/doctrine-attribution.md` - documents the declarable policy,
  its default, its config key, and the corrected seal-subject form.
- `.qorlogic/config.json` - NEW, TRACKED. Declares
  `{"attribution": {"model_coauthor": false}}` for this repository. Forced by
  audit entry #506: Phase 2 brings the Phase 206 seal commit into the
  live-history walk for the first time, and that commit deliberately omits the
  co-author line, so it passes only if this declaration exists. `git check-ignore
  -v .qorlogic/config.json` reports the path is not ignored, so the file reaches
  CI. Without it, implementing this plan produces a red suite.

### Changes

The guard's skip-on-unparseable behavior is the reason a non-compliant seal
reached `main` unnoticed, so the subject form and the guard are brought into
agreement from both directions: the template emits a parseable subject, and an
unparseable one is no longer an accidental exemption.

## Definition of Done

### Deliverable: declarable co-author requirement

- **D1**: An operator whose policy forbids AI co-author trailers can seal
  without a gate failure, and every operator who declares nothing keeps today's
  behavior exactly.
- **D2**: `qor/scripts/attribution_policy.py` exports `AttributionPolicy` and
  `resolve_policy`; `commit_trailer(..., model_coauthor=...)` and
  `message_has_full_trailer(..., require_coauthor=...)` exist with strict
  defaults; `seal_trailer_check` resolves and honors the policy.
- **D3**: Seal entry records the doctrine change and states that the framework
  line remained mandatory throughout.
- **D4**: The seven Phase 1 tests assert returned strings, resolved policy
  values, and CLI exit codes. The CLI test is the binding one: the same commit
  exits 1 with no config and 0 with the policy declared.

### Deliverable: seal-subject coverage

- **D1**: A seal commit can no longer be exempted from the trailer guard by the
  shape of its subject line.
- **D2**: `_seal_phase_in_scope` no longer returns False for an unparseable
  subject; the substantiate seal-commit template carries the phase number.
- **D3**: Seal entry records the coverage hole, names the two live seal commits
  that hit it, and states that this is how the Phase 206 omission passed.
- **D4**: `test_seal_subject_without_phase_number_is_flagged_not_skipped`
  asserts the predicate's return value directly; the live-history walk then
  covers the previously-skipped commits, which the full suite exercises.

### Deliverable: this repository's declaration

- **D1**: This repository declares that it does not require the model co-author
  line, so its own seals satisfy the widened guard.
- **D2**: `.qorlogic/config.json` exists at the repository root, is tracked, and
  declares `attribution.model_coauthor: false`.
- **D3**: Seal entry records that the declaration is what makes the Phase 206
  seal legal under the widened guard, rather than the guard being loosened for
  it.
- **D4**: The full suite passes with the previously-skipped Phase 206 seal now
  in scope. Removing the file turns the suite red, which is the observable that
  proves the declaration is load-bearing rather than decorative.

## Feature Inventory Touches

None. This plan touches `qor/scripts/`, `qor/skills/`, `qor/references/`, and
`tests/`; it introduces no user-touchable feature and modifies no FEATURE_INDEX
row.

## CI Commands

- `python -m pytest tests/test_attribution_coauthor_policy.py tests/test_attribution_tiered_usage.py tests/test_attribution_docs_consistency.py tests/test_seal_trailer_guard.py -q` — the directly affected suites.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `python -m ruff check qor/scripts/attribution_policy.py qor/scripts/attribution.py qor/scripts/seal_trailer_check.py` — lint on the touched modules.
- `qor-logic scripts skill_size_budget_lint --skills-root qor/skills` — the substantiate SKILL.md edit stays within budget.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase207-attribution-coauthor-policy.md` — this plan asserts each path and command identically at every site.
