# Plan: governance signal fidelity (GH #409, #411, #413)

**change_class**: feature

**doc_tier**: standard

**terms**: []

No new domain vocabulary. `satisfied-by-fallback` is a status value on an
existing capability model, not a new concept.

**boundaries**:
- limitations: [the `/qor-enterprise-*` halves of GH #409 and #411 are not in this repository and are tracked separately in the private line; this phase ships only the Qor-logic-side halves those depend on]
- non_goals: [does not touch GH #410's threshold semantics -- that is its own phase because it changes when development is allowed to proceed; does not change the citation requirement for seal PRs, which keeps the full triple]
- exclusions: [no change to `is_available`'s boolean contract -- callers depending on it keep working; the richer status is an additional function]

## Problem

Three unrelated surfaces report a governance signal that is not true, and each
teaches an operator to discount the channel it arrives on.

### GH #409 -- Step 0.5 forces an override it should not need

`qor/skills/sdlc/qor-plan/references/step-extensions.md:10-21` raises
`InterdictionError` on any non-empty `git status --porcelain` and then
unconditionally runs `git checkout -b phase/<NN>-<slug>`.

Under an orchestrator whose Review Boundary requires work to stay staged and
uncommitted, both cannot hold, so every cycle records the same severity-2
`orchestration_override`. The override mechanism works, which is the problem:
it absorbs a standing contradiction as though it were a one-off operator
decision, and `check_shadow_threshold` sums it toward a breach that carries no
new information.

An operator already on a feature branch has the isolation the phase branch
exists to provide. Creating a second branch inside it buys nothing.

### GH #411 -- a covered capability reported as missing

`qor/scripts/qor_platform.py:190-204` `is_available` returns a bare bool, and
`qor/platform/profiles/claude-code-solo.md:22` mandates a severity-2
`capability_shortfall` whenever an `enhances_with` capability is unavailable.
There is no way to say "unavailable, and covered by a supported substitute".

So a host with native subagent dispatch records a shortfall for `agent-teams`
every session, while the fallback does the governance work the capability
exists to do. A capability map that reports "missing" for something the host
demonstrably provides teaches operators to discount its output.

### GH #413 -- the citation lint has one shape for every PR

`qor/scripts/pr_citation_lint.py:26-40` requires all three citations on every
PR: a plan path, a ledger entry, and a 64-hex Merkle seal. A research-phase
record has no plan artifact and no seal, so it can satisfy exactly one.

Observed on PR #412, which carried real ledger entries and could not pass. The
only ways past are all bad: admin-merge past a red required check, cite an
unrelated 64-hex value to satisfy the regex, or stop routing governance records
through PRs at all.

`_PLAN_PATTERN` additionally requires `docs/plan-qor-phase<NN>-`, so a consumer
naming plans after the work rather than a Qor phase number fails the same way
`prompt_injection_canaries` used to (GH #407).

## Fix

1. **`qor/scripts/governance_helpers.py`**: `branch_isolation_satisfied(repo_root)`
   returns True when HEAD is not the repository's default branch. Step 0.5
   accepts that as satisfying isolation instead of requiring branch *creation*,
   and `references/step-extensions.md` records why: the phase branch exists to
   isolate, and an operator already on a feature branch already is.
2. **`qor/scripts/qor_platform.py`**: `availability(capability)` returns
   `"available"`, `"satisfied-by-fallback"`, or `"missing"`. `is_available`
   keeps its boolean contract and is unchanged for existing callers.

   The substitute is declared in a module-level `FALLBACKS` map in
   `qor_platform` (tribunal ground V-1, entry #699). The first draft said "the
   active profile declares" it, but no machine-readable declaration exists --
   profiles are markdown whose only `fallback` mention is descriptive prose, and
   `qor_platform.current()` returns `None` here. A constant map is also the
   right home on the merits: whether a host provides subagent dispatch as a
   substitute for `agent-teams` is a toolkit-level fact, not per-workspace
   configuration. Putting it in platform state would let an operator silence a
   real shortfall by declaring a substitute that does not exist.

   A capability absent from `FALLBACKS` reports `missing`, which is what keeps
   `capability_shortfall` worth its severity.
   `qor/platform/profiles/claude-code-solo.md` records that a
   `satisfied-by-fallback` capability emits no `capability_shortfall`, reserving
   that event for capabilities with no viable substitute -- which is what makes
   it worth its severity.
3. **`qor/scripts/pr_citation_lint.py`**: required citations become a function
   of the PR's phase, derived from the gate artifacts present in the diff rather
   than from a label the author could set to the least demanding value:
   - a `substantiate.json` in the diff -> plan path + ledger entry + seal hash
     (unchanged; a seal PR still cites everything)
   - a `plan.json` but no `substantiate.json` -> plan path + ledger entry
   - a `research.json` only -> brief path + ledger entry
   - no gate artifacts -> today's full triple, so a code PR cannot opt out by
     omitting artifacts
   - **a diff touching non-governance source -> the full triple regardless of
     which artifacts accompany it** (tribunal ground V-2, entry #699)

   That last condition matters because the first draft derived requirements from
   the artifacts present alone, so a PR changing `qor/` or `src/` could land
   under the lenient research rule by including a `research.json`. The plan's own
   reasoning rejects "a self-declared label any author could set to the least
   demanding value"; reading only the artifact set reintroduces that hazard one
   level down, with the artifact set becoming the settable label. Keying on what
   the PR *changes* as well as what it carries confines the lenient rules to PRs
   that are genuinely governance records.
   `_PLAN_PATTERN` widens to `docs/plan-*.md`; the phase-number convention is
   this repository's own and never described what a governance plan is.

## Tests (written first)

- `tests/test_governance_signal_fidelity.py::test_isolation_satisfied_on_a_feature_branch`
  and `::test_isolation_not_satisfied_on_the_default_branch` -- the pair that
  makes fix 1 meaningful rather than always-true.
- `::test_availability_reports_satisfied_by_fallback` -- a capability absent but
  with a declared non-blocking substitute reports the middle value, not
  `missing`. Red before fix 2.
- `::test_availability_reports_missing_without_a_fallback` -- the guard that
  keeps `capability_shortfall` meaningful; a capability with no substitute still
  reports `missing`.
- `::test_is_available_contract_is_unchanged` -- the boolean stays boolean for
  both fallback and missing, pinning the declared non-goal.
- `::test_seal_pr_still_requires_all_three_citations` -- a diff containing
  `substantiate.json` demands the full triple. The guard against fix 3 becoming
  a way to skip citations on the PRs that most need them.
- `::test_research_pr_requires_brief_and_entry_not_a_seal` -- the PR #412 case:
  a research diff passes with a brief path and a ledger entry, and still fails
  without them.
- `::test_pr_with_no_gate_artifacts_requires_the_full_triple` -- a code PR
  cannot opt out by shipping no artifacts.
- `::test_source_changing_pr_requires_the_full_triple_despite_a_research_artifact`
  -- the V-2 guard: a diff touching `qor/` alongside a `research.json` is judged
  under the strict rule. Red before the fix-3 amendment; without it the lenient
  rule is reachable by addition.
- `::test_work_named_plan_path_is_accepted` -- `docs/plan-sprint1-install.md`
  satisfies the plan citation.

Every test invokes the unit and asserts on its return value.

## Validation

- `python -m pytest tests/test_governance_signal_fidelity.py -q` -- run twice for determinism
- `python -m pytest -q` (full suite)
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
- `python -m qor.scripts.publication_boundary_lint`
- This repository's own recent PR bodies must still pass the lint under the new rules

## CI Commands

- `python -m pytest -q`
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
