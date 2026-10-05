# Plan: Phase 304 - Maintenance freeze: Qor-logic is declared feature-complete and frozen, and a check keeps it frozen

**change_class**: feature

**doc_tier**: standard

**terms**: `[]` (no new canonical term; "maintenance freeze" is used as plain English in the notices and the check, and the plan gate artifact carries `terms: []`)

**boundaries**:
- limitations: the freeze is declared and checked inside the repository only; repository settings (issues, branch protection, archiving) are owner actions outside this plan (LD-6); `freeze_check` checks the four properties LD-2 names and nothing else
- non_goals: removing or deprecating any skill, script, CLI command or doctrine; changing runtime behavior of any shipped command; any dependency update (dependabot PR #529 is closed unmerged, LD-5); editing sealed plans, gate artifacts, intent-lock records, the ledger or the shadow genome
- exclusions: naming or linking any successor project (owner decision, LD-1)

**Current base**: `7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2` (head of `phase/303-boundary-lint-scope`, Phase 303 sealed at version `0.175.7`, not yet merged; this branch stacks on it so the final release carries Phase 303)

**Target version**: `0.176.0` (feature bump from `0.175.7`)

**Branch**: local `phase/304-maintenance-freeze`, pushed to the harness-designated remote branch `claude/determined-lovelace-7lwx3r`

**iteration**: 2. Iteration 1 was vetoed (V1, `coverage-gap`, META_LEDGER #841): LD-2 made a missing notice file and the list and string forms of `on:` normative, and no planned test produced either input. Iteration 2 adds a test for each normative LD-2 clause (the clause-to-test map under Phase 1), states what a missing `pyproject.toml` and an unparseable workflow do (advisory A4) and that workflows are read with `yaml.safe_load` (A3), corrects the doctrine sentences that describe the GitHub-surface scan as scheduled (A2, LD-8), specifies the FX028 row (A6), states the expected RED as a collection error (A5) and corrects the LD-7 tag wording (A7). Everything else is unchanged from iteration 1.

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

def check(repo_root: Path) -> list[str]: ...   # sorted-by-property violation strings; [] when frozen
def main(argv: list[str] | None = None) -> int: ...
```

`check` returns one string per violation, each prefixed by the path it concerns:

1. **classifier**: `pyproject.toml` (read with `tomllib`) has exactly one `Development Status :: ` classifier and it equals `FROZEN_CLASSIFIER`. A different value, a second value, none, or a missing `pyproject.toml` is one violation.
2. **dependabot**: neither `DEPENDABOT_FILES` path exists. Each present file is one violation.
3. **schedule**: no file matching `.github/workflows/*.yml` or `*.yaml` declares a `schedule` trigger. Each file is read with `yaml.safe_load`; a file that does not parse raises (the check fails loudly rather than passing a workflow it could not read). The trigger key is read from the parsed YAML as `"on"` or as `True` (PyYAML parses a bare `on:` key as the boolean `True`: observed `python -c "import yaml;print(list(yaml.safe_load(open('.github/workflows/ci.yml'))))"` prints `['name', True, 'permissions', 'concurrency', 'jobs']`). A mapping containing `schedule`, a list containing `"schedule"`, or the string `"schedule"` is one violation per workflow file.
4. **notice**: each `NOTICE_FILES` file exists and has a line equal to `FREEZE_HEADING` followed, before the next `## ` line or end of file, by at least one non-blank line. A missing file, a missing heading, or an empty section is one violation per file.

`main` parses `--repo-root` (default `.`), prints each violation on its own line, then `freeze_check: OK` or `freeze_check: <n> violation(s)`, and returns 0 when frozen and 1 otherwise. Each helper stays under 40 lines and the module under 250 (Section 4 Razor).

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

`tests/test_freeze_check.py` builds a frozen tree in `tmp_path` (a `pyproject.toml` with the frozen classifier, a dispatch-only workflow, README.md and AGENTS.md each with a non-empty freeze section) and invokes `freeze_check.check` / `freeze_check.main` on it or on one mutation of it:

- `test_a_frozen_tree_has_no_violations` - `check` returns `[]`.
- `test_a_beta_classifier_is_reported` - classifier `4 - Beta` gives exactly one violation naming `pyproject.toml`.
- `test_two_development_status_classifiers_are_reported` - frozen plus Beta gives one violation.
- `test_a_missing_development_status_is_reported` - no Development Status classifier gives one violation.
- `test_a_missing_pyproject_is_reported` - no `pyproject.toml` gives one violation naming it.
- `test_a_dependabot_config_is_reported` - parametrized over `.yml` and `.yaml`; one violation naming that path.
- `test_a_scheduled_workflow_is_reported` - parametrized over a `.yml` and a `.yaml` workflow whose `on:` mapping holds `schedule`; one violation naming that workflow.
- `test_a_quoted_on_key_with_schedule_is_reported` - `"on":` written quoted (parsed as the string key) is still caught.
- `test_a_list_form_schedule_trigger_is_reported` - `on: [push, schedule]` gives one violation naming that workflow.
- `test_a_string_form_schedule_trigger_is_reported` - `on: schedule` gives one violation naming that workflow.
- `test_a_dispatch_only_list_form_is_not_reported` - `on: [push, workflow_dispatch]` gives no violation (the list rule matches `schedule`, not any list).
- `test_an_unparseable_workflow_raises` - a workflow whose YAML does not parse makes `check` raise `yaml.YAMLError`.
- `test_a_missing_notice_file_is_reported` - parametrized over README.md and AGENTS.md; the file deleted gives one violation naming that file.
- `test_a_missing_freeze_heading_is_reported` - parametrized over README.md and AGENTS.md; heading removed gives one violation naming that file.
- `test_an_empty_freeze_section_is_reported` - heading followed directly by the next `## ` heading gives one violation.
- `test_main_returns_zero_and_prints_ok_when_frozen` and `test_main_returns_one_and_prints_each_violation` - exit code and printed lines.
- `test_the_repository_is_frozen` - `check(REPO_ROOT)` returns `[]` on this repository.

`tests/test_nightly_health_wiring.py::test_workflow_is_dispatch_only_with_least_permissions` - the workflow text has no `schedule:` line and no `cron:`, keeps `workflow_dispatch:` and the existing permission assertions.

Clause-to-test map for LD-2 (every normative clause has a test whose input exercises it):

| LD-2 clause | Test |
|---|---|
| 1: different value | `test_a_beta_classifier_is_reported` |
| 1: second value | `test_two_development_status_classifiers_are_reported` |
| 1: none | `test_a_missing_development_status_is_reported` |
| 1: missing `pyproject.toml` | `test_a_missing_pyproject_is_reported` |
| 2: each present dependabot file | `test_a_dependabot_config_is_reported` (both paths) |
| 3: `*.yml` and `*.yaml` globbed | `test_a_scheduled_workflow_is_reported` (both extensions) |
| 3: unparseable file raises | `test_an_unparseable_workflow_raises` |
| 3: key read as `"on"` | `test_a_quoted_on_key_with_schedule_is_reported` |
| 3: key read as `True` | `test_a_scheduled_workflow_is_reported` |
| 3: mapping form | `test_a_scheduled_workflow_is_reported` |
| 3: list form | `test_a_list_form_schedule_trigger_is_reported`, `test_a_dispatch_only_list_form_is_not_reported` |
| 3: string form | `test_a_string_form_schedule_trigger_is_reported` |
| 4: missing file | `test_a_missing_notice_file_is_reported` (both files) |
| 4: missing heading | `test_a_missing_freeze_heading_is_reported` (both files) |
| 4: empty section | `test_an_empty_freeze_section_is_reported` (both files) |
| `main`: output and exit codes | `test_main_returns_zero_and_prints_ok_when_frozen`, `test_main_returns_one_and_prints_each_violation` |

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
| FX028 | NEW | tests/test_freeze_check.py | freeze_check.check returns no violations for a frozen tree and exactly one named violation for each of a non-Inactive classifier, a dependabot config, a scheduled workflow and a missing or empty freeze section; on this repository it returns none |

## Definition of Done

### Deliverable: freeze_check

- **D1**: The frozen state (Inactive classifier, no dependabot, no scheduled workflow, freeze notice in README and AGENTS) is checkable by one command.
- **D2**: `qor/scripts/freeze_check.py` exposes `check(repo_root: Path) -> list[str]` and `main(argv) -> int` per LD-2.
- **D3**: `FX028` row in `docs/FEATURE_INDEX.md`; ledger implementation and seal entries.
- **D4**: `tests/test_freeze_check.py::test_the_repository_is_frozen` passes, and each mutation test reports exactly its one violation.

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
