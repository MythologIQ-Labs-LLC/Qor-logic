# Plan: Phase 304 - Maintenance freeze: Qor-logic is declared feature-complete and frozen, and a check keeps it frozen

**change_class**: feature

**doc_tier**: standard

**terms**: `[]` (no new canonical term; "maintenance freeze" is used as plain English in the notices and the check, and the plan gate artifact carries `terms: []`)

**boundaries**:
- limitations: the freeze is declared and checked inside the repository only; repository settings (issues, branch protection, archiving) are owner actions outside this plan (LD-6); the `freeze_check` contract is the regression set LD-2 names (K0 to K6); behaviour on other inputs is not specified
- non_goals: removing or deprecating any skill, script, CLI command or doctrine; changing runtime behavior of any shipped command; any dependency update (dependabot PR #529 is closed unmerged, LD-5); editing sealed plans, gate artifacts, intent-lock records, the ledger or the shadow genome
- exclusions: naming or linking any successor project (owner decision, LD-1)

**Current base**: `7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2` (head of `phase/303-boundary-lint-scope`, Phase 303 sealed at version `0.175.7`, not yet merged; this branch stacks on it so the final release carries Phase 303)

**Target version**: `0.176.0` (feature bump from `0.175.7`)

**Branch**: local `phase/304-maintenance-freeze`, pushed to the harness-designated remote branch `claude/determined-lovelace-7lwx3r`

**iteration**: 4. Iterations 1 to 3 were vetoed for `coverage-gap` (META_LEDGER #841, #842, #843); each found surviving mutants in a wider clause list (2, then 3, then 7 after 23 atomic clauses). The cycle-count escalator routed the session to `/qor-remediate`, whose proposal (`.qor/gates/2026-10-05T1757-41eb02/remediate.json`, SHADOW_GENOME #46) is applied here: LD-2 no longer specifies a general-purpose checker clause by clause. Its normative contract is a finite regression contract over this repository's own files (K0 to K6), and parsing details are declared implementation detail. LD-1 and LD-3 to LD-8 are unchanged from iteration 3; the iteration-1 advisories stay closed (safe_load and parse errors in LD-2, the doctrine sentences in LD-8, the FX028 row, the collection-error RED, the LD-7 tag wording).

**Owner decision (2026-10-05)**: freeze Qor-logic so that no further development happens on it; state that it is superseded without naming or linking a successor; publish the final version to PyPI.

## Open Questions

None.

## Problem

Qor-logic is being retired from active development, but nothing in the repository says so, and three mechanisms keep generating work against it:

1. README, CONTRIBUTING and the agent rules describe an actively developed project, and the PyPI classifier is `Development Status :: 4 - Beta`. A user or an agent reading them would start new phases.
2. `.github/dependabot.yml` opens weekly version-update PRs for two ecosystems (PR #529 is one).
3. `nightly-health.yml` runs daily on a cron schedule and opens or updates a GitHub issue on drift.

No check exists that would notice if any of these returned.

## Locked Decisions

### LD-1: the freeze notice and where it lives

`README.md` gains a `## Maintenance freeze` section directly above `## What Qor-logic Does`:

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:README.md | grep -nE '^## What Qor-logic Does'` -> `34:## What Qor-logic Does`

README is the PyPI long description (`readme = "README.md"` in `pyproject.toml`), so the notice reaches the PyPI project page with the release. Text (exact):

> Qor-logic is feature-complete and frozen as of version 0.176.0, its final release. It has been superseded and receives no further development: no new features, fixes, dependency updates, or releases. The published package stays on PyPI and continues to install and work as documented below. New issues and pull requests are not accepted.

`AGENTS.md`, the rules every agent surface defers to, gains a `## Maintenance freeze` section directly above `## Public-repository boundary`:

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:AGENTS.md | grep -nE '^## '` -> `6:## Public-repository boundary`

Text (exact):

> Qor-logic is frozen at version 0.176.0 and superseded. Do not start new phases, plans, features, fixes, dependency updates, or releases in this repository. A change requires the owner to lift the freeze explicitly first; `qor-logic scripts freeze_check` and `tests/test_freeze_check.py` keep the frozen state checked.

`CLAUDE.md` gains a `## Maintenance freeze (mandatory)` section directly above `## Governance flow`, one bullet pointing at `[AGENTS.md](AGENTS.md#maintenance-freeze)`, because CLAUDE.md's governance-flow bullets otherwise instruct an agent to start phases:

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:CLAUDE.md | grep -nE '^## Governance flow'` -> `52:## Governance flow`

`CONTRIBUTING.md` gains a `## Maintenance freeze` section directly above `## Reading order`, saying contributions are no longer accepted and linking `README.md#maintenance-freeze`:

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:CONTRIBUTING.md | grep -nE '^## Reading order'` -> `5:## Reading order`
 `GEMINI.md` and `.github/copilot-instructions.md` already defer to `AGENTS.md` and are unchanged. No notice names or links a successor.

### LD-2: `qor/scripts/freeze_check.py` checks four properties

New module, invoked as `qor-logic scripts freeze_check --repo-root .` through the existing module dispatch, so no CLI change is needed:

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:qor/cli.py | grep -nE 'target = f"qor.\{family\}.\{args.module\}"'` -> `285:    target = f"qor.{family}.{args.module}"`

```python
FROZEN_CLASSIFIER = "Development Status :: 7 - Inactive"
FREEZE_HEADING = "## Maintenance freeze"
NOTICE_FILES = ("README.md", "AGENTS.md")
DEPENDABOT_FILES = (".github/dependabot.yml", ".github/dependabot.yaml")

def check(repo_root: Path) -> list[str]: ...   # [] when frozen
def main(argv: list[str] | None = None) -> int: ...
```

**Intent.** The frozen state is four properties: (1) `pyproject.toml` declares `FROZEN_CLASSIFIER` as its only `Development Status` classifier; (2) no dependabot configuration is committed; (3) no workflow under `.github/workflows` declares a `schedule` trigger; (4) `README.md` and `AGENTS.md` each carry a non-empty `FREEZE_HEADING` section. `check` returns one string per violation, each starting with the repository-relative POSIX path it concerns followed by `: `.

**Normative contract (remediation, `.qor/gates/2026-10-05T1757-41eb02/remediate.json`).** The contract is stated over this repository's own files, not over arbitrary trees. A "copy" is a temporary directory holding copies of this repository's `pyproject.toml`, `README.md`, `AGENTS.md` and `.github/workflows/*.yml`.

- K0 On this repository, and on an unmodified copy, `check` returns `[]`.
- K1 Copy with the `FROZEN_CLASSIFIER` string in `pyproject.toml` replaced by `Development Status :: 4 - Beta` (the pre-freeze value): `check` returns a non-empty list and every element names `pyproject.toml`.
- K2 Copy with `.github/dependabot.yml` written (`version: 2` and an empty `updates` list): non-empty, every element names `.github/dependabot.yml`.
- K3 Copy with the pre-freeze schedule restored in `.github/workflows/nightly-health.yml` (the two lines `  schedule:` and `    - cron: '0 9 * * *'` inserted directly after its `on:` line): non-empty, every element names `.github/workflows/nightly-health.yml`.
- K4 Copy with the `FREEZE_HEADING` section removed from `README.md` (the heading line through the line before the next line starting with `## `): non-empty, every element names `README.md`.
- K5 As K4 for `AGENTS.md`.
- K6 `main(["--repo-root", <copy>])` returns 0 on an unmodified copy and prints exactly `freeze_check: OK`; on the K2 copy it returns 1 and prints the `check` result, one element per line, followed by `freeze_check: 1 violation(s)`.

Everything else, including how YAML trigger keys and forms are read, how the heading and section are matched, behaviour on other trees and the order of violations from different files, is implementation detail and not part of the contract. The implementation reads workflows with `yaml.safe_load` and lets a parse error propagate. Each helper stays under 40 lines and the module under 250 (Section 4 Razor).

### LD-3: the classifier

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:pyproject.toml | grep -nE 'Development Status'` -> `15:    "Development Status :: 4 - Beta",`

Decision: replace that one line with `"Development Status :: 7 - Inactive",`. `version` is bumped by `/qor-substantiate` Step 7.5, not by hand:

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:pyproject.toml | grep -nE '^version = '` -> `7:version = "0.175.7"`

### LD-4: dependabot and the nightly schedule are removed

`git ls-tree --name-only 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2 .github/` lists `.github/dependabot.yml`; it is deleted. The three tests in `tests/test_dependabot_config.py` assert the file exists and covers both ecosystems; that file is deleted with it, and its contract is inverted by property 2 of LD-2. The first of the three:

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:tests/test_dependabot_config.py | grep -nE '^def test_dependabot_config_file_exists'` -> `18:def test_dependabot_config_file_exists():`

The nightly schedule starts at:

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:.github/workflows/nightly-health.yml | grep -nE '^  schedule:'` -> `15:  schedule:`

Decision: delete lines 15-16 (`schedule:` and its `cron` entry) and keep `workflow_dispatch:`, so the check can still be run by hand. The workflow's cost-justification comment is updated to say it is manual-only. The test that locks the schedule:

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:tests/test_nightly_health_wiring.py | grep -nE 'def test_workflow_declares_schedule'` -> `19:def test_workflow_declares_schedule_dispatch_and_permissions():`

It is renamed `test_workflow_is_dispatch_only_with_least_permissions` and asserts the inverse of its two schedule lines (no `schedule:` line, no `cron:`); its other assertions are unchanged. No other workflow declares a schedule (property 3 run on the base reports only `nightly-health.yml`).

### LD-5: no dependency change

Dependabot PR #529 (cyclonedx-bom 7.3.1 to 7.5.0 in `requirements-sbom.txt`) is closed unmerged with a comment citing the freeze. `requirements-sbom.txt` is unchanged:

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:requirements-sbom.txt | grep -nE '^cyclonedx-bom=='` -> `25:cyclonedx-bom==7.3.1 \`

The SBOM tool is build-time only, and admitting a days-old release into the final build would run against the dependency cooling-period doctrine for no runtime gain.

### LD-6: owner actions outside the repository

Not performed by this plan, reported to the owner: disabling issues or archiving the repository on GitHub, and approving the `pypi` environment for the release run.

### LD-7: release-state continuity

`0.175.7` (sealed by Phase 303, never tagged on the remote) gets a `sealed_unpublished` exception in `docs/release-state.json`, the same shape as the existing ones; the most recent:

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:docs/release-state.json | grep -nE '"version": "0.175.6"'` -> `95:      "version": "0.175.6",`

`0.175.7` has no tag on the remote; Phase 303's seal tag exists only in the checkout that sealed it.

This keeps the changelog tag-coverage test green when `0.176.0` is the tagged version.

### LD-8: the publication-boundary doctrine stops calling the surface scan scheduled

`qor/references/doctrine-publication-boundary.md` describes the GitHub-surface scan as scheduled in three places:

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:qor/references/doctrine-publication-boundary.md | grep -nE 'scheduled surface scan both act'` -> `42:tracked-file lint and the scheduled surface scan both act after the fact, so a`

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:qor/references/doctrine-publication-boundary.md | grep -noE 'that gap on a schedule [(].nightly-health[.]yml'` prints `102:that gap on a schedule (`, then a backtick, then `nightly-health.yml` (the line carries backticks, so it is cited by this command rather than quoted as arrow evidence)

`git show 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2:qor/references/doctrine-publication-boundary.md | grep -nE '^The scheduled scan is read-only'` -> `106:The scheduled scan is read-only and reports for a human to anonymize; rewriting`

Decision: line 42 reads "the surface scan"; line 102 reads "that gap when `nightly-health.yml` is run by hand (it ran on a schedule until the Phase 304 maintenance freeze)"; line 106 reads "The surface scan is read-only". Paragraphs are re-wrapped only where the edited line requires it; no other doctrine text changes. The doctrine is not compiled into `qor/dist` (`git ls-tree -r --name-only 7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2 qor/dist | grep -c doctrine-publication-boundary` prints `0`), so no recompile follows.

## Phase 1: Tests first

### Affected Files

- `tests/test_freeze_check.py` - NEW; functionality tests for `freeze_check.check` and `main`
- `tests/test_nightly_health_wiring.py` - first test renamed and inverted (LD-4)
- `tests/test_dependabot_config.py` - deleted (LD-4)

### Unit Tests

`tests/test_freeze_check.py` has a fixture that builds a copy as LD-2 defines it, and one test per contract item:

| ID | Test | Expected |
|---|---|---|
| K0 | `test_the_repository_is_frozen` | `check(<repository root>) == []` |
| K0 | `test_an_unmodified_copy_is_frozen` | `check(<copy>) == []` |
| K1 | `test_restoring_the_beta_classifier_is_reported` | non-empty; every element starts with `pyproject.toml: ` |
| K2 | `test_committing_a_dependabot_config_is_reported` | non-empty; every element starts with `.github/dependabot.yml: ` |
| K3 | `test_restoring_the_nightly_schedule_is_reported` | non-empty; every element starts with `.github/workflows/nightly-health.yml: ` |
| K4, K5 | `test_removing_a_freeze_section_is_reported` (parametrized over `README.md` and `AGENTS.md`) | non-empty; every element starts with `<file>: ` |
| K6 | `test_main_prints_ok_and_returns_zero_on_a_frozen_copy` | 0; stdout lines exactly `["freeze_check: OK"]` |
| K6 | `test_main_prints_each_violation_and_returns_one` | 1 on the K2 copy; stdout lines equal `check(<copy>)` followed by `freeze_check: 1 violation(s)` |

Each regression test also asserts its mutation took effect on the copy before calling `check` (the replaced string, written file, inserted lines or removed heading is present or absent as intended), so a fixture that silently stopped mutating cannot turn a test green.

`tests/test_nightly_health_wiring.py::test_workflow_is_dispatch_only_with_least_permissions` - the workflow text has no `schedule:` line and no `cron:`, keeps `workflow_dispatch:` and the existing permission assertions.

Expected RED before Phase 2: `tests/test_freeze_check.py` fails at collection (`ModuleNotFoundError: qor.scripts.freeze_check`), so pytest reports one collection error for the file rather than per-test failures; the renamed nightly test fails on its no-`schedule:` assertion.

## Phase 2: The check

### Affected Files

- `qor/scripts/freeze_check.py` - NEW, per LD-2
- `docs/FEATURE_INDEX.md` - new row `| FX028 | \`qor-logic scripts freeze_check\` maintenance-freeze conformance check | qor/scripts/freeze_check.py | AGENTS.md (Maintenance freeze) | tests/test_freeze_check.py::test_the_repository_is_frozen | verified |`

### Changes

Implement LD-2. No other module changes.

## Phase 3: Freeze the repository

### Affected Files

- `pyproject.toml` - classifier per LD-3
- `.github/dependabot.yml` - deleted (LD-4)
- `.github/workflows/nightly-health.yml` - schedule removed, comment updated (LD-4)
- `README.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md` - notices per LD-1
- `docs/release-state.json` - `0.175.7` exception per LD-7
- `qor/references/doctrine-publication-boundary.md` - three sentences per LD-8
- `CHANGELOG.md` - `[Unreleased]` entry under `### Changed` describing the freeze (stamped `0.176.0` at seal)

### Changes

Apply LD-1, LD-3, LD-4, LD-7 and LD-8. After this phase `qor-logic scripts freeze_check --repo-root .` prints `freeze_check: OK`.

## Feature Inventory Touches

| entry_id | operation | test_path | test_descriptor |
|---|---|---|---|
| FX028 | NEW | tests/test_freeze_check.py | freeze_check.check returns [] on this repository and on a copy of its files, and a non-empty list naming only the regressed file for each of the restored Beta classifier, a committed dependabot config, the restored nightly schedule and a removed README or AGENTS freeze section |

## Definition of Done

### Deliverable: freeze_check

- **D1**: The frozen state (Inactive classifier, no dependabot, no scheduled workflow, freeze notice in README and AGENTS) is checkable by one command.
- **D2**: `qor/scripts/freeze_check.py` exposes `check(repo_root: Path) -> list[str]` and `main(argv) -> int` per LD-2.
- **D3**: `FX028` row in `docs/FEATURE_INDEX.md`; ledger implementation and seal entries.
- **D4**: every test in the Phase 1 table passes with the expected result in its row (K0 to K6).

### Deliverable: repository frozen

- **D1**: README (and so PyPI), AGENTS, CLAUDE and CONTRIBUTING state the freeze without naming a successor; nothing schedules new work.
- **D2**: LD-1, LD-3, LD-4, LD-7 and LD-8 edits as specified.
- **D3**: CHANGELOG `0.176.0` entry; `docs/release-state.json` carries `0.175.7`.
- **D4**: `tests/test_nightly_health_wiring.py::test_workflow_is_dispatch_only_with_least_permissions` passes; `qor-logic scripts freeze_check --repo-root .` prints `freeze_check: OK`.

## CI Commands

- `python -m pytest tests/test_freeze_check.py tests/test_nightly_health_wiring.py -q` - the new and changed tests
- `python -m qor.scripts.freeze_check --repo-root .` - the repository is frozen
- `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py tests/test_changelog_format.py tests/test_wayfinding_discipline.py tests/test_publication_boundary_policy.py tests/test_attribution_docs_consistency.py -q` - release-state, changelog and agent-doc contracts
- `python qor/scripts/check_variant_drift.py` - dist unchanged by this plan
- `python -m qor.scripts.publication_boundary_lint --repo-root . --expect-scope structural` - boundary
- `python -m pytest tests/ -q` - full suite
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - ledger chain
- `python -m ruff check qor/ tests/` - lint
