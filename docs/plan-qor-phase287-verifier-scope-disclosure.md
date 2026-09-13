# Plan: a verifier reports what it examined, and examining nothing is not a pass

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Three verifiers gain scope disclosure and a zero floor: the plan
  citation truth-checker, the stale-commitment gate, and the install-sync gate.
  It does not widen what any of them checks beyond the install-sync gate's
  `references/` extension, which is the one case where the narrow scope and the
  silence are the same defect. Other verifiers in the repository are untouched.
- non_goals: No execution-evidence contract (GH #463 is a separate design
  boundary). No change to the error-handling property of GH #455. No change to
  what `ledger_commitment` considers stale, only to whether an empty examination
  reads as clean.
- exclusions: No retroactive re-verification of already-sealed phases.

## Open Questions

None.

## Locked Decisions

### LD-1: the property already exists here and is not being invented

Phase 219 established that a green result must carry its own scope:

> `grep -n 'scope: str' qor/scripts/publication_boundary_lint.py` -> `147:    scope: str`

`BoundaryResult` carries the detector scope that produced its findings, the CLI
prints it, `tests/test_boundary_scope_disclosure.py` pins it as a property, and
the doctrine states the rule. Its own docstring gives the general form: an
unqualified "0 findings" from CI and from a local run mean different things and
currently look identical.

One verifier has it. This phase gives it to three more. Nothing here is a new
convention, which is why it needs no new doctrine section -- only a sentence
saying the rule is general.

### LD-2: disclosure alone is insufficient; the floor is the second half

`plan_grep_lint` already prints its examined count. It prints **zero** against
every plan written to the house convention, and exits 0:

> `git show HEAD:qor/scripts/plan_evidence.py | grep -n '_LD_HEADING_RE = '` -> `32:_LD_HEADING_RE = re.compile(r"^#+\s.*(locked decision|citation inventory)", re.IGNORECASE)`

So a verifier that reports its scope faithfully and still exits clean over
nothing has disclosed and not protected.

**Disclosure is universal; the floor is not.** A floor belongs where an empty
scope means the examiner failed to look, and not where it means there was nothing
to look at. `ledger_commitment`'s set is declared by the party it audits, so an
empty set is that party having named nothing and the gate must not pass on it.
`plan_grep_lint`'s zero, once the regex is repaired, means the plan cites no
infrastructure -- legitimate for a decision of pure design reasoning. A floor
there over-flags, and is unreachable for the defect it targets: any citation at
all, even a bare `file:line`, already yields a non-zero count. Implementation
confirmed both, and `tests/test_plan_grep_lint_citation_evidence.py` caught the
over-flag. The protection against that defect returning is the regression test
asserting a known plan examines more than none.

### LD-3: #487 is a scope bug with a one-line cause

`_LD_HEADING_RE` matches `## Locked Decisions`. Plans write their decisions as
`### LD-<n>: <title>` beneath it, and `_ANY_HEADING_RE` ends a block at the next
heading of **any** level -- which is the first `### LD-1`. So every Locked
Decision body falls outside the scanned region and the truth-checker examines
nothing.

The fix is to recognise `### LD-<n>` as a block heading in its own right. That is
narrower than changing the block-termination rule, which would also alter how the
`citation inventory` blocks are read, and this phase does not need that.

### LD-4: #461 is not a bug and must not be fixed as one

`ledger_commitment.stale_commitments(repo_root, touched)` works. Its scope is
supplied by the party it audits -- `files_touched` from the implement artifact --
and measured, **105 of 204** implement artifacts name no plan or brief at all, so
about half of sealed phases ran this gate over source and tests only.

Widening the checked set is a separate argument with its own trade-offs. What
this phase fixes is that `stale_commitments([])` returns `[]` and reads exactly
like a thorough pass. The gate discloses how many artifacts it examined, and an
empty set fails.

### LD-5: #476 is the one case where narrow scope and silence are the same defect

`tests/test_install_sync_with_source.py` globs `SKILL.md` only. Measured: **32
`SKILL.md` against 26 `references/*.md`**, so the gate covers 55 percent of the
installed markdown surface and reports no shortfall.

Here disclosure alone would be perverse -- announcing that the gate ignores the
half of the surface most likely to be edited, while continuing to ignore it. So
this one also gains the coverage: `references/*.md` are compared between source
and dist on the same terms as `SKILL.md`, and the count is reported.

### LD-6: #486 rides along because the ladder is already open

The escape calls `append_event` with neither `attribution=` nor `log_path=`:

> `git show HEAD:qor/scripts/merge_velocity_check.py | grep -n 'shadow_process.append_event'` -> `251:        shadow_process.append_event({`

and that call raises:

> `grep -n 'append_event requires' qor/scripts/shadow_process.py` -> `122:            raise ValueError("append_event requires attribution=... or log_path=...")`

so `--override`, the documented escape from a fail-closed seal gate, raises
before it can log. It is unrelated to scope and is carried because a seal gate
with no working escape is worse than the throughput it guards, and the fix is one
argument plus a test that drives the flag to completion rather than asserting it
parses.

## Phase 1: pin the behaviour

### Affected Files

- `tests/test_verifier_scope.py` - NEW.

### Changes

Tests drive each verifier against fixtures and assert on the reported scope and
the exit behaviour, not on formatting.

### Unit Tests

- `test_locked_decision_bodies_are_inside_the_scanned_region` - a plan written as
  `## Locked Decisions` followed by `### LD-1:` with one grep-evidence statement
  yields one parsed statement. Red before: `_ld_blocks` returns a single empty
  block and the count is 0.
- `test_the_truth_checker_reports_a_nonzero_count_on_a_house_convention_plan` -
  `count_truth_checked` over a real repository plan returns > 0. Red before: it
  returns 0 for every such plan, which is the defect stated as a number.
- `test_stale_commitments_reports_how_many_artifacts_it_examined` - the result
  carries the examined count. Red before: the function returns a bare list and
  the caller cannot tell one from none.
- `test_an_empty_touched_set_fails_rather_than_returning_clean` - the CLI exits
  non-zero when `files_touched` names no ledger-citable artifact. Red before:
  `stale_commitments([])` returns `[]` and the gate passes.
- `test_a_populated_touched_set_still_passes_when_nothing_is_stale` - the floor
  must not turn every clean run red. The negative control; fails if the floor is
  implemented as "always fail on an empty findings list" rather than on an empty
  examination.
- `test_reference_files_are_compared_between_source_and_dist` - a `references/`
  file that differs between source and dist is reported. Red before: only
  `SKILL.md` is globbed, so the difference is invisible.
- `test_the_sync_gate_reports_how_many_files_it_compared` - the comparison count
  covers both classes. Red before: nothing reports coverage, so 55 percent and
  100 percent look identical.
- `test_merge_velocity_override_appends_its_event_and_passes` - with
  `--override`, the run exits 0 and one `gate_override` event is appended to an
  injected log. Red before: `append_event` raises `ValueError` and the override
  cannot complete.

## Phase 2: the fixes

### Affected Files

- `qor/scripts/plan_evidence.py` - `_LD_HEADING_RE` recognises `### LD-<n>`.
- `qor/scripts/ledger_commitment.py` - the result carries the examined count.
- `qor/reliability/` or `qor/scripts/` CLI for the stale-commitment gate - exits
  non-zero on an empty examination.
- `tests/test_install_sync_with_source.py` - compares `references/*.md` and
  reports the compared count.
- `qor/scripts/merge_velocity_check.py` - `append_event(..., attribution="LOCAL")`.

### Changes

The shared shape is a count travelling with a result and a floor on that count.
Each verifier keeps its own result type; nothing is unified into a new base
class, because three call sites do not justify an abstraction and Phase 219's
precedent is a plain field rather than a framework.

### Unit Tests

The Phase 1 tests go green. No new tests.

## Phase 3: state that the rule is general

### Affected Files

- `qor/references/doctrine-verification-closure-integrity.md` - one paragraph.

### Changes

> A verifier reports the size of what it examined, and an examination of nothing
> is not a pass. An unqualified clean result from a narrow scope and from a
> thorough one are indistinguishable to the reader, so the scope travels with the
> result -- and because a faithful report of zero is still a clean exit, the count
> carries a floor. Phase 219 established this for the publication-boundary lint;
> it holds for any gate whose scope can be empty, partial, or supplied by the
> party it audits.

### Unit Tests

- `test_the_doctrine_states_the_scope_rule` - the doctrine states both halves,
  disclosure and floor, and the three verifiers' own messages name their counts.
  Red before the change, and red if doctrine and implementation drift.

## Feature Inventory Touches

Empty. This plan touches `qor/scripts/`, `tests/` and `qor/references/`.

## Definition of Done

### Deliverable: the citation truth-checker examines the citations

- **D1**: `plan_grep_lint` reports a non-zero examined count against a plan
  written to the house convention. It does **not** fail on a zero: that state
  means the plan cites nothing, which is legitimate, and LD-2 records why a floor
  there over-flags and is unreachable.
- **D2**: `_LD_HEADING_RE` recognises `### LD-<n>`.
- **D3**: LD-3 records the one-line cause and why the block-termination rule is
  left alone.
- **D4**: `test_the_truth_checker_reports_a_nonzero_count_on_a_house_convention_plan`.
  Observed before: 0 on every recent plan; after: 8, 3 and 3 on phases 286, 285
  and 283.

### Deliverable: an author-declared scope is disclosed and floored

- **D1**: The stale-commitment gate reports how many artifacts it examined and
  fails when that is none.
- **D2**: `stale_commitments` returns the examined count beside its findings; the
  CLI exits non-zero on zero.
- **D3**: LD-4 records that the gate is not broken and that widening its scope is
  a separate argument.
- **D4**: `test_an_empty_touched_set_fails_rather_than_returning_clean` and
  `test_a_populated_touched_set_still_passes_when_nothing_is_stale` -- the second
  is the control against a floor implemented on the wrong quantity.

### Deliverable: the sync gate covers the surface it claims

- **D1**: A `references/` file differing between source and dist is reported, and
  the compared count is stated.
- **D2**: `tests/test_install_sync_with_source.py` globs both classes.
- **D3**: LD-5 records the measured 32 against 26 and why this case needs the
  coverage rather than disclosure alone.
- **D4**: `test_reference_files_are_compared_between_source_and_dist` and
  `test_the_sync_gate_reports_how_many_files_it_compared`.

### Deliverable: the seal gate's escape runs

- **D1**: `merge_velocity_check --override` completes, logs, and exits 0.
- **D2**: `append_event` is called with `attribution="LOCAL"`.
- **D3**: LD-6 records why an unrelated one-line fix rides along.
- **D4**: `test_merge_velocity_override_appends_its_event_and_passes`. Observed
  before: `ValueError`.

## CI Commands

- `python -m pytest tests/test_verifier_scope.py -q` — the scope contract for all three verifiers and the override fix.
- `python -m pytest tests/test_install_sync_with_source.py tests/test_plan_grep_lint.py tests/test_ledger_commitment.py -q` — the suites that own the changed modules.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase287-verifier-scope-disclosure.md --repo-root .` — this plan's own citations are truth-checked, which is the fix demonstrating itself.
- `python -m qor.scripts.publication_boundary_lint` — no boundary finding.
- `python -m pytest -q` — full suite.
