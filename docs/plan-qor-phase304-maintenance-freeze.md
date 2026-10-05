# Plan: Phase 304 - Maintenance freeze: Qor-logic is declared feature-complete and frozen, and a check keeps it frozen

**change_class**: feature

**doc_tier**: standard

**terms**: `[]` (no new canonical term; "maintenance freeze" is used as plain English in the notices and the check, and the plan gate artifact carries `terms: []`)

**boundaries**:
- limitations: the freeze is declared and checked inside the repository only; repository settings (issues, branch protection, archiving) are owner actions outside this plan (LD-6); `freeze_check` checks the clauses LD-2 names (C1.1 to C5.2) and nothing else
- non_goals: removing or deprecating any skill, script, CLI command or doctrine; changing runtime behavior of any shipped command; any dependency update (dependabot PR #529 is closed unmerged, LD-5); editing sealed plans, gate artifacts, intent-lock records, the ledger or the shadow genome
- exclusions: naming or linking any successor project (owner decision, LD-1)

**Current base**: `7228bacd1a0f3dfb0d410bf0e69f8a8e100624e2` (head of `phase/303-boundary-lint-scope`, Phase 303 sealed at version `0.175.7`, not yet merged; this branch stacks on it so the final release carries Phase 303)

**Target version**: `0.176.0` (feature bump from `0.175.7`)

**Branch**: local `phase/304-maintenance-freeze`, pushed to the harness-designated remote branch `claude/determined-lovelace-7lwx3r`

**iteration**: 3. Iteration 1 was vetoed (V1, `coverage-gap`, META_LEDGER #841): a missing notice file and the list and string forms of `on:` were normative with no test. Iteration 2 (vetoed, `coverage-gap`, META_LEDGER #842) added those tests and a clause-to-test map, but the map grouped several property-4 conditions in one row, so heading equality, blank-only sections and the end-of-file boundary had no discriminating input. Iteration 3 restates LD-2 as atomic clauses with IDs (C1.1 to C5.2) and gives each ID a test in the Phase 1 table whose input flips under a mutation of that clause alone; it also adds the property order (C5.1) and `main`'s default root (C5.2) tests (iteration-2 advisories A1, A3), and closes the iteration-1 advisories as before: safe_load and unparseable files (C3.3), a missing `pyproject.toml` (C1.1), the doctrine sentences (LD-8), the FX028 row, the collection-error RED and the LD-7 tag wording. LD-1 and LD-3 to LD-8 are unchanged from iteration 2.

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

`check` returns one string per violation, each starting with the repository-relative POSIX path it concerns followed by `: `. Each clause below is atomic and carries an ID; the Phase 1 map gives every ID a test whose input flips under a mutation of that clause alone.

**Property 1, classifier** (`pyproject.toml`, read with `tomllib`). A classifier is a status classifier when it starts with `Development Status :: `.
- C1.1 `pyproject.toml` absent: one violation.
- C1.2 the status classifiers are exactly `[FROZEN_CLASSIFIER]`: no violation (other classifiers are ignored).
- C1.3 exactly one status classifier with another value: one violation.
- C1.4 more than one status classifier, even if one is frozen: one violation.
- C1.5 no status classifier (including no `[project]` table): one violation.

**Property 2, dependabot.**
- C2.1 each `DEPENDABOT_FILES` path that exists is one violation, so both present give two; neither present gives none.

**Property 3, schedule** (each file directly in `.github/workflows/` whose name ends in `.yml` or `.yaml`).
- C3.1 no `.github/workflows` directory: no violation.
- C3.2 files with any other extension are not read.
- C3.3 each file is read with `yaml.safe_load`; a file that does not parse makes `check` raise `yaml.YAMLError` (fail loudly rather than pass a file it could not read).
- C3.4 an empty file, or one whose top level is not a mapping, declares no trigger.
- C3.5 the triggers are the values of both the `"on"` key and the `True` key (PyYAML reads a bare `on:` key as the boolean `True`: `python -c "import yaml;print(list(yaml.safe_load(open('.github/workflows/ci.yml'))))"` prints `['name', True, 'permissions', 'concurrency', 'jobs']`); a schedule under either key is a violation.
- C3.6 a mapping value schedules iff it has the key `schedule`.
- C3.7 a list value schedules iff it contains `"schedule"`.
- C3.8 a string value schedules iff it equals `"schedule"`.
- C3.9 a scheduling file is exactly one violation; files are reported in sorted order of their path, across both extensions.

**Property 4, notice** (for each name in `NOTICE_FILES`, in that order).
- C4.1 the file is absent: one violation.
- C4.2 no line of the file is exactly equal to `FREEZE_HEADING` (no stripping; a longer heading, a deeper heading or trailing whitespace does not match): one violation.
- C4.3 the section is the lines after the first line equal to `FREEZE_HEADING`, up to the next line that starts with `## ` or the end of the file.
- C4.4 a `### ` line does not end the section and is section content.
- C4.5 the section is empty when it has no line with a non-whitespace character: one violation.

**Order and `main`.**
- C5.1 violations are listed property 1, 2, 3, 4 in that order.
- C5.2 `main` parses `--repo-root` (default `.`), prints each violation on its own line in `check` order, then `freeze_check: OK` or `freeze_check: <n> violation(s)`, and returns 0 when frozen and 1 otherwise.

Each helper stays under 40 lines and the module under 250 (Section 4 Razor).

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

`tests/test_freeze_check.py` builds a frozen tree in `tmp_path` (a `pyproject.toml` whose classifiers are `FROZEN_CLASSIFIER` and `Programming Language :: Python :: 3`, a workflow `manual.yml` whose `on:` mapping holds only `workflow_dispatch`, and README.md and AGENTS.md each holding `# Title`, a blank line, `FREEZE_HEADING`, a blank line, `Frozen.`, a blank line and `## Next` with text) and invokes `freeze_check.check` or `freeze_check.main` on it or on one mutation of it. "One violation naming X" means `check` returns a list of length 1 whose element starts with `X: `.

| ID | Test | Input (mutation of the frozen tree) | Expected |
|---|---|---|---|
| C1.2 | `test_a_frozen_tree_has_no_violations` | none | `[]` |
| C1.1 | `test_a_missing_pyproject_is_reported` | `pyproject.toml` deleted | one violation naming `pyproject.toml` |
| C1.3 | `test_a_beta_classifier_is_reported` | status `4 - Beta` only | one violation naming `pyproject.toml` |
| C1.4 | `test_two_development_status_classifiers_are_reported` | frozen and `4 - Beta` | one violation naming `pyproject.toml` |
| C1.5 | `test_a_missing_development_status_is_reported` | parametrized: only `Programming Language :: Python :: 3`; and a `pyproject.toml` with no `[project]` table | one violation naming `pyproject.toml` |
| C2.1 | `test_a_dependabot_config_is_reported` | parametrized over each `DEPENDABOT_FILES` path | one violation naming that path |
| C2.1 | `test_both_dependabot_configs_are_reported_separately` | both paths | two violations, `.yml` then `.yaml` |
| C3.1 | `test_a_tree_without_workflows_has_no_schedule_violation` | `.github/workflows` removed | `[]` |
| C3.2 | `test_a_non_yaml_file_in_workflows_is_not_read` | `.github/workflows/notes.txt` holding a scheduled workflow text | `[]` |
| C3.3 | `test_an_unparseable_workflow_raises` | `broken.yml` holding `on: [push` | `check` raises `yaml.YAMLError` |
| C3.4 | `test_an_empty_or_non_mapping_workflow_declares_no_trigger` | parametrized: empty `empty.yml`; `list.yml` holding `- schedule` | `[]` |
| C3.5, C3.6 | `test_a_scheduled_workflow_is_reported` | parametrized over `nightly.yml` and `nightly.yaml` with a bare `on:` mapping holding `schedule` and `workflow_dispatch` | one violation naming that file |
| C3.5 | `test_a_quoted_on_key_with_schedule_is_reported` | `"on":` written quoted, mapping holding `schedule` | one violation naming that file |
| C3.5 | `test_a_schedule_under_either_on_key_is_reported` | one file with a quoted `"on":` mapping holding only `workflow_dispatch` and a bare `on:` mapping holding `schedule` | one violation naming that file |
| C3.6 | (frozen tree) | mapping without `schedule` | `[]` |
| C3.7 | `test_a_list_form_schedule_trigger_is_reported` | `on: [push, schedule]` | one violation naming that file |
| C3.7 | `test_a_list_form_without_schedule_is_not_reported` | `on: [push, workflow_dispatch]` | `[]` |
| C3.8 | `test_a_string_form_schedule_trigger_is_reported` | `on: schedule` | one violation naming that file |
| C3.8 | `test_a_string_form_without_schedule_is_not_reported` | `on: push` | `[]` |
| C3.9 | `test_scheduling_workflows_are_reported_in_path_order` | `b.yml` and `a.yaml`, both scheduled | two violations, `a.yaml` then `b.yml` |
| C4.1 | `test_a_missing_notice_file_is_reported` | parametrized over `NOTICE_FILES`: the file deleted | one violation naming that file |
| C4.2 | `test_a_missing_freeze_heading_is_reported` | parametrized over `NOTICE_FILES`: heading line removed | one violation naming that file |
| C4.2 | `test_a_heading_that_is_not_exactly_the_freeze_heading_is_reported` | parametrized over `## Maintenance freeze (lifted)`, `### Maintenance freeze` and `## Maintenance freeze` with a trailing space, each followed by `Work resumes.`, in README.md | one violation naming `README.md` |
| C4.3, C4.5 | `test_an_empty_freeze_section_is_reported` | parametrized over `NOTICE_FILES`: heading directly followed by `## Next` and text | one violation naming that file |
| C4.5 | `test_a_blank_only_freeze_section_is_reported` | heading, two empty lines and a line of spaces, then `## Next` and text, in README.md | one violation naming `README.md` |
| C4.3, C4.5 | `test_an_empty_freeze_section_at_end_of_file_is_reported` | AGENTS.md ending in the heading followed by one blank line | one violation naming `AGENTS.md` |
| C4.3 | `test_a_freeze_section_at_end_of_file_with_text_is_not_reported` | AGENTS.md ending in the heading and `Frozen.` | `[]` |
| C4.4 | `test_a_subheading_counts_as_freeze_section_content` | heading followed only by `### Detail`, then `## Next` | `[]` |
| C4.3 | `test_only_the_first_freeze_heading_counts` | README.md: an empty freeze section, then `## Other`, then a second freeze heading with text | one violation naming `README.md` |
| C5.1 | `test_violations_are_listed_in_property_order` | Beta classifier, `.github/dependabot.yml`, scheduled `nightly.yml`, README.md deleted | four violations naming `pyproject.toml`, `.github/dependabot.yml`, `.github/workflows/nightly.yml`, `README.md` in that order |
| C5.2 | `test_main_returns_zero_and_prints_ok_when_frozen` | none, `--repo-root <tree>` | exit 0; stdout exactly `freeze_check: OK` |
| C5.2 | `test_main_returns_one_and_prints_each_violation` | dependabot `.yml` and scheduled `nightly.yml` | exit 1; stdout the two violations in order, then `freeze_check: 2 violation(s)` |
| C5.2 | `test_main_defaults_to_the_current_directory` | `monkeypatch.chdir(<tree>)`, then `main([])`; then dependabot added and `main([])` again | exit 0, then exit 1 |
| (repo) | `test_the_repository_is_frozen` | this repository | `[]` |

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
| FX028 | NEW | tests/test_freeze_check.py | freeze_check.check returns no violations for a frozen tree and exactly one named violation for each of a non-Inactive classifier, a dependabot config, a scheduled workflow and a missing or empty freeze section; on this repository it returns none |

## Definition of Done

### Deliverable: freeze_check

- **D1**: The frozen state (Inactive classifier, no dependabot, no scheduled workflow, freeze notice in README and AGENTS) is checkable by one command.
- **D2**: `qor/scripts/freeze_check.py` exposes `check(repo_root: Path) -> list[str]` and `main(argv) -> int` per LD-2.
- **D3**: `FX028` row in `docs/FEATURE_INDEX.md`; ledger implementation and seal entries.
- **D4**: every test in the Phase 1 table passes with the expected result in its row, and `tests/test_freeze_check.py::test_the_repository_is_frozen` passes on this repository.

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
