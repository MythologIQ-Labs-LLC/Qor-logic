# Plan: release-artifact retention and hermetic git fixtures (Phase 209)

**change_class**: hotfix

**doc_tier**: standard

**terms_introduced**: none

**boundaries**:
- limitations: Isolating fixtures from ambient git configuration removes one
  class of environmental variance. It cannot prove the observed CI failure is
  gone, because that failure was never reproduced locally; it removes a
  mechanism that could produce it and makes the next occurrence diagnosable.
- non_goals: No retry logic anywhere. A retry would convert a real failure into
  a slow pass and destroy the signal this phase exists to preserve. No change to
  the merge-velocity grading thresholds or to `assess_merge_velocity`. No change
  to which artifact the release publishes or how it is built.
- exclusions: Fixtures that invoke git against the live `REPO_ROOT` rather than
  a scratch repository are out of scope; they intentionally read real state.

## Open Questions

None.

## Locked Decisions

**LD-1 — The release artifact expires before the approval gate it feeds.**

`git show HEAD:.github/workflows/release.yml | grep -nE "name: release-dist|retention-days|download-artifact" -> 68: name: release-dist | 71: retention-days: 7 | 106: uses: actions/download-artifact@... | 108: name: release-dist`

Observed directly on the v0.135.0 release run: the `release-dist` artifact was
created `2026-08-02T16:37:12Z` with `expires_at 2026-08-09T16:37:11Z`, and the
`pypi` environment approval was granted `2026-08-10T15:38Z`, roughly 23 hours
past expiry. `publish` then failed with the toolkit's generic
"Artifact not found" message, which reads as a build or upload defect when the
build had succeeded and its output had simply been garbage-collected.

The `pypi` environment gate has no bounded wait, so any approval delayed beyond
a week hits this. The sibling workflows already use a month:

`grep -n "retention-days" .github/workflows/*.yml -> ci.yml:49: retention-days: 30 | oss-sast.yml:67: retention-days: 30 | release.yml:71: retention-days: 7`

**LD-2 — The fixture helper still discards git's stderr, which is the gap Phase
194 closed for production code only.**

`git show HEAD:tests/test_merge_velocity_check.py | grep -nE "def _run|check=True" -> 27: def _run(cmd: list[str], cwd: Path, env: dict | None = None) -> str: | 29: cmd, cwd=str(cwd), capture_output=True, text=True, check=True, env=env,`

Phase 194 made `_git_log_merges_in_window` surface git's own reason, and
`test_git_log_failure_surfaces_stderr` locks that. The fixture helper that
BUILDS the scratch history was not covered, so when
`git merge --no-ff feat-b8c90baa -m 'feature 6'` exited 2 on a CI leg, the
report was a bare `CalledProcessError` with no git message. `check=True`
captures stderr onto the exception but `CalledProcessError.__str__` never prints
it, so the diagnostic was discarded at the point it was needed.

**LD-3 — The scratch-repo fixtures inherit ambient git configuration, which is
environment coupling the project's own test doctrine forbids.**

`doctrine-test-discipline.md` requires tests be reliable with "no hidden
time/random/network coupling". A scratch repository created by `git init` still
reads the user's global and the machine's system config. On a GitHub runner,
`actions/checkout` installs `includeIf` entries pointing at credential config
files and removes them during job cleanup; the CI job logs for this repository
show exactly those entries being added and unset. A fixture running git while
ambient config references a file that is being torn down is a plausible
mechanism for an opaque, non-reproducible exit code, and it is unnecessary
coupling regardless of whether it produced this specific failure.

Four test modules build scratch repositories this way:

`grep -rln '"git", "init"' tests/ -> tests/test_merge_velocity_check.py | tests/test_reliability_scripts.py | tests/test_substantiate_changelog_integration.py | tests/test_workspace_fragility_check.py`

Fixing only the module that happened to flake would leave three modules with the
identical latent coupling. All four are treated.

## Phase 1: Raise the release-artifact retention

### Affected Files

- `.github/workflows/release.yml` - `retention-days` on the `release-dist`
  upload becomes 30, matching `ci.yml` and `oss-sast.yml`.

### Changes

One value. The build/publish split is preserved, so the published bytes remain
the ones the CI gate verified; only the window in which a human may approve
grows from a week to a month.

## Phase 2: Hermetic, diagnosable git fixtures

### Unit Tests

- `tests/test_git_fixture_isolation.py::test_scratch_repo_env_disables_ambient_config` -
  calls the shared helper, then runs `git config --get <key>` inside a scratch
  repo under the returned environment with a global config file that DOES define
  that key, and asserts the lookup finds nothing; without the helper's
  environment the same lookup finds the value. Proves ambient config is
  actually excluded rather than merely intended to be.
- `::test_scratch_repo_env_preserves_path_and_identity` - asserts the returned
  environment still carries `PATH` (so `git` resolves) and sets a committer and
  author identity, so a scratch commit succeeds with no ambient identity.
- `::test_run_git_raises_with_stderr_and_context` - runs a git command that
  fails deterministically (`git merge no-such-branch` in a scratch repo) and
  asserts the raised error text contains git's own message, the failing argv,
  and the cwd, rather than a bare exit code.

### Affected Files

- `tests/support/git_fixture.py` - NEW. `scratch_env()` returning an
  environment with `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` pointed at a
  nonexistent path plus a fixed identity, and `run_git(argv, cwd, env=None)`
  raising `RuntimeError` carrying git's stdout, stderr, argv, and cwd.
- `tests/test_merge_velocity_check.py` - `_run` delegates to `run_git`; scratch
  repos are created under `scratch_env()`.
- `tests/test_workspace_fragility_check.py` - same.
- `tests/test_substantiate_changelog_integration.py` - same.
- `tests/test_reliability_scripts.py` - same for its scratch-repo helper.
- `tests/test_git_fixture_isolation.py` - NEW, the three tests above.

### Changes

The date-backdating path keeps working: `scratch_env()` returns a mutable
mapping the caller extends with `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` rather
than rebuilding from `os.environ`. No retry is introduced anywhere; a failing
git command still fails the test, only now it says why.

## Definition of Done

### Deliverable: release-artifact retention

- **D1**: A release approval granted within a month of the build finds its
  artifact present.
- **D2**: `.github/workflows/release.yml` declares `retention-days: 30` on the
  `release-dist` upload.
- **D3**: Seal entry records the observed expiry window, the approval timestamp
  that missed it, and that the failure message named the wrong cause.
- **D4.d**: No automated test. Artifact retention is a GitHub Actions platform
  behavior with no local or CI-observable assertion short of waiting a week;
  asserting the literal YAML value would be a presence-only test that the
  project's own test-functionality doctrine rejects. **Follow-up phase**: none
  required; the value is verified by the next release approval that exercises it.

### Deliverable: hermetic, diagnosable git fixtures

- **D1**: A scratch-repo fixture behaves identically regardless of the machine's
  git configuration, and any git failure inside one reports git's own reason.
- **D2**: `tests/support/git_fixture.py` exports `scratch_env` and `run_git`;
  all four scratch-repo modules use them.
- **D3**: Seal entry records that the CI failure was not reproduced locally
  (12 of 12 passes), names the mechanism removed, and states plainly that this
  removes a cause rather than proving the symptom gone.
- **D4**: `test_scratch_repo_env_disables_ambient_config` asserts a key defined
  in an ambient global config is invisible under the fixture environment and
  visible without it, which fails if the isolation is dropped.

## Feature Inventory Touches

None. This plan touches `.github/workflows/` and `tests/`; it introduces no
user-touchable feature and modifies no FEATURE_INDEX row.

## CI Commands

- `python -m pytest tests/test_git_fixture_isolation.py -q` — the isolation and diagnosability contract.
- `python -m pytest tests/test_merge_velocity_check.py tests/test_workspace_fragility_check.py tests/test_substantiate_changelog_integration.py tests/test_reliability_scripts.py -q` — the four migrated scratch-repo modules.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `qor-logic scripts publication_boundary_lint --repo-root .` — the new files keep the tracked surface clean.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase209-release-retention-and-hermetic-git.md` — this plan asserts each path and command identically at every site.
