# Plan: git auto-maintenance guard (Phase 214, GH #308)

**change_class**: governance

**doc_tier**: standard

**terms_introduced**: none

**boundaries**:
- limitations: The guard suppresses git's auto-maintenance for the test
  process only. It changes no shipped code and no operator-facing behavior.
  This host cannot demonstrate the fix's effect -- its git predates the
  behavior -- so the regression test asserts the guard is in effect rather
  than asserting an outcome it cannot observe.
- non_goals: No retry anywhere. No change to `scratch_env` or `run_git` from
  Phase 209; the guard composes with them rather than replacing them. No
  re-derivation of the root cause, which GH #308 established with an A/B
  counterfactual this repository has no failing case to reproduce.
- exclusions: `gc.auto` is not touched; GH #308 records that it does not
  suppress the repack, which still runs via the geometric/incremental task.

## Open Questions

None.

## Locked Decisions

**LD-1 — The mechanism is adopted, not re-derived.**

GH #308 root-causes the intermittent exit-128 failures to git auto-maintenance:
git >= 2.5x runs `git maintenance run --auto --no-quiet --detach` after
`git commit` / `git merge`, and because it daemonizes, `git repack -d` keeps
rewriting the scratch repository's object store *after* the foreground call has
returned, deleting loose objects and their `objects/xx` shard directories while
the fixture's next call is using them. It carries an A/B counterfactual --
baseline 15/25 failures, guarded 0/25 twice -- which this repository cannot
reproduce because it has no failing case on hand. Re-deriving it here would
produce a weaker artifact, not a stronger one.

**LD-2 — Phase 209's remedy cannot suppress this, and that correction is
this phase's premise.**

Phase 209 pinned `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` to a nonexistent
path on the theory that ambient configuration was mutating underneath the
fixture. Auto-maintenance is a built-in default, not a configured behavior, so
removing configuration cannot disable it. GH #308 records the same approach
being tried upstream and failing. The Phase 209 seal's framing of that change
as the mechanism removed was wrong; the hermetic fixtures and the diagnostic
error surface remain worth keeping on their own merits.

**LD-3 — The guard must use git's env-config layer, or Phase 209 shadows it.**

`scratch_env()` sets `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, and
`GIT_CONFIG_NOSYSTEM`, so any guard expressed as a global or system config file
would be read out of scope by construction. The env-config layer
(`GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_0` / `GIT_CONFIG_VALUE_0`) is read
independently of those files. Verified on this host rather than assumed: with
both pinned to a nonexistent path and the layer set,
`git config --get maintenance.auto` returns `false` at exit 0; without the
layer the same lookup is unset at exit 1.

`scratch_env()` builds from `{**os.environ}`, so a value set by an autouse
fixture flows into every call it constructs.

**LD-4 — An autouse fixture covers every caller; a targeted one would not.**

Fourteen test files shell out to git. Every environment they pass derives from
`os.environ`, including the two that build their own dicts
(`tests/test_cli_module_dispatch.py` via `dict(os.environ)` and
`tests/test_git_fixture_isolation.py` via `{**scratch_env()}`). An autouse
fixture in `tests/conftest.py` therefore reaches all of them, including future
tests that shell out without knowing this hazard exists. `GIT_CONFIG_COUNT`
and `GIT_CONFIG_KEY` appear nowhere in `tests/` or `qor/`, so index 0 is free.

**LD-5 — This host cannot observe the fix working, so the test must not
pretend otherwise.**

`git --version` here is 2.52.0; GH #308 correlates the behavior with git
version and names 2.52 structurally immune against CI's 2.54.0. The obvious
regression test -- "a scratch repo has zero pack files after N merges" --
passes vacuously on this host, which is exactly where it would most often be
run. The assertion is therefore that the guard is *in effect*, which goes red
on every platform the moment the fixture is absent.

## Phase 1: Install the guard

### Unit Tests

- `tests/test_git_auto_maintenance_guard.py::test_maintenance_auto_is_disabled_for_test_git_calls` -
  runs `git config --get maintenance.auto` in a scratch repo under the
  fixture's own environment and asserts `false` at exit 0. Fails on every
  platform if the autouse fixture is removed, including hosts whose git
  predates the behavior.
- `::test_guard_survives_the_hermetic_scratch_environment` - performs the same
  lookup under `scratch_env()`, which pins `GIT_CONFIG_GLOBAL` /
  `GIT_CONFIG_SYSTEM` / `GIT_CONFIG_NOSYSTEM`, asserting the env-config layer
  is not shadowed. This is the composition LD-3 establishes, pinned so a later
  change to either mechanism cannot silently break the other.
- `::test_guard_does_not_clobber_an_existing_env_config_layer` - sets a
  pre-existing `GIT_CONFIG_COUNT` entry, then asserts both that entry and
  `maintenance.auto` resolve, so the fixture appends rather than overwrites.

### Affected Files

- `tests/conftest.py` - an autouse `_git_no_auto_maintenance` fixture setting
  the env-config layer, appending to any existing `GIT_CONFIG_COUNT`.
- `tests/test_git_auto_maintenance_guard.py` - NEW, the three tests above.

### Changes

The fixture sets `maintenance.auto=false` through the env-config layer for the
duration of each test. It appends rather than assuming index 0 is free, so a
future fixture adding its own entry does not silently lose one of the two.

## Phase 2: Record the correction

### Affected Files

- `docs/SHADOW_GENOME.md` - the pattern: a fix whose mechanism was never
  demonstrated, reported as the mechanism removed, and defended with a null
  result the host could not have produced.

### Changes

Phase 209 shipped a plausible remedy for an undiagnosed failure and its seal
described the mechanism as removed. Three occurrences were cited as motivation
and none was reproduced. The supporting evidence -- twelve consecutive local
passes -- came from a host structurally incapable of exhibiting the behavior,
which makes it not weak evidence but no evidence. Recording that shape matters
more than the specific bug.

## Definition of Done

### Deliverable: the guard

- **D1**: A test process cannot have its scratch repositories rewritten by a
  detached maintenance run, on any git version.
- **D2**: `tests/conftest.py` carries an autouse fixture setting
  `maintenance.auto=false` via `GIT_CONFIG_COUNT` / `KEY` / `VALUE`, appending
  to any existing layer.
- **D3**: Seal entry records that the mechanism was adopted from GH #308 rather
  than re-derived, and that this host cannot demonstrate the effect.
- **D4**: The three Phase 1 tests assert the resolved config value under the
  plain environment, under `scratch_env()`, and alongside a pre-existing layer.
  All three go red if the fixture is removed, on every platform.

### Deliverable: the correction on record

- **D1**: The Phase 209 claim is corrected where the project's memory lives,
  not only in a closed issue thread.
- **D2**: `docs/SHADOW_GENOME.md` carries the pattern.
- **D3**: Seal entry states plainly that Phase 209's framing was wrong and why
  the local evidence was worthless.
- **D4.d**: No test. A process-narrative entry has no executable assertion;
  `sg_closure_lint` accepts a `cannot-automate:` decision for exactly this
  shape. **Follow-up phase**: none required.

## Feature Inventory Touches

None. This plan touches `tests/` and `docs/` only; `pyproject.toml` packages
`qor*`, so nothing shipped changes and no FEATURE_INDEX row moves.

## CI Commands

- `python -m pytest tests/test_git_auto_maintenance_guard.py -q` — the guard is in effect and composes with the hermetic environment.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `python -m ruff check qor/ tests/` — the new test file is lint clean.
- `qor-logic scripts sg_closure_lint` — the new Shadow Genome entry carries an enforcer citation or a decision.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase214-git-auto-maintenance-guard.md` — this plan asserts each path and command identically at every site.
