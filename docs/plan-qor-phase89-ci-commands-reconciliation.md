# Plan: Phase 89 — Plan ci_commands reconciliation against .github/workflows (GH #91)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #91

**boundaries**:
- limitations: V1 ships a Python-fingerprint heuristic — extracts `python ...`
  and `pytest ...` commands from `run:` blocks in `.github/workflows/*.yml`.
  Non-Python checks (custom shell, `cargo`, `npm`, `go`, native binaries)
  are not candidates; the issue's COREFORGE origination case is a Python
  script (`scripts/architecture/check_test_metadata.py`), so V1 covers the
  motivating failure class. WARN-only (parallels existing Step 0.6
  pre-audit lints `plan_test_lint`, `plan_grep_lint`,
  `plan_text_consistency_lint`, `delivery_branch_lint`). Tag-only
  workflows (`on: push: tags:` exclusively) are skipped by default — they
  do not run on branch PRs and so cannot be plan-verified per-phase.
  Environment-setup commands (`pip install`, `git fetch`,
  `git merge-base`, `echo`, `printf`, doc-only conditional bash) are
  filtered out by construction.
- non_goals: full bash AST parsing; cross-workflow dependency graphing;
  re-assertion at `/qor-substantiate` Step 6 (the issue calls this
  "optional"; deferred to a follow-on phase, analogous to the V1/V2 split
  the cluster has used for #88/#92); exemption via comment annotation in
  workflow files (operators justify via the plan-side
  `## CI Coverage Exemptions` block instead); auto-suggestion of
  exemption rationale (operator authors the justification).
- exclusions: no changes to `release.yml`, `ci.yml`, or `pr-lint.yml`;
  the lint is consumed by `/qor-audit` Step 0.6 only — not by
  `/qor-plan`, not by `/qor-implement`, not by `/qor-substantiate`. WARN
  output is advisory; no VETO is bound to the lint output in V1.

## Open Questions

None.

## Feature Inventory Touches

Empty. This plan touches a new lint script under `qor/scripts/`, a
governance skill (`qor/skills/governance/qor-audit/SKILL.md`), a doctrine
reference (`qor/references/doctrine-shadow-genome-countermeasures.md`),
and wiring tests under `tests/`; it introduces no `src/` user-facing
feature. `feature_inventory_touches`: `[]`.

## Design notes

GH #91 documents a credibility-class failure: COREFORGE 2026-05-22 ran a
10-phase governed remediation stack (Phases 358-369) under
`/qor-auto-dev-1`; every phase plan's `ci_commands` listed the obvious
checks (`cargo check` / `cargo test`, `npx tsc`, `npx eslint`,
`npx jest`, `check_razor_budget.py`); every phase sealed `all CI green`;
when the 10-phase stack was opened as an integration PR, the
`Architecture Guard` GitHub Actions job (running
`scripts/architecture/check_test_metadata.py`) failed because three
test files introduced across Phases 358 and 366 lacked the required
`SPEC:` / `FEATURE:` / `TEST_ID:` markers. The `Architecture Guard` job
was never listed in any phase's `ci_commands` — the gap was invisible
to the governed cycle, then surfaced only after ten seals.

The minimal V1 fix is a pre-audit plan-lint, in the same spirit and
shape as `plan_text_consistency_lint` / `plan_grep_lint` /
`delivery_branch_lint`. Per `[[feedback-progressive-disclosure]]` (the
GH #92 corpus-bloat lesson), the change is kept lean: a single new lint
script under `qor/scripts/`, one wiring paragraph in
`/qor-audit` Step 0.6, one extension to
`qor/references/doctrine-shadow-genome-countermeasures.md`. No new
top-level doctrine file. No skill-prose escalation beyond Step 0.6.

The lint reads `.github/workflows/*.yml` (PyYAML is already in the
test-dep tree; no new runtime dep), enumerates each job's `run:` steps,
extracts `python ...` / `pytest ...` candidates (the Python fingerprint
that covers the issue's motivating COREFORGE case and the bulk of
Qor-logic's own CI surface), filters environment-setup boilerplate
(`pip install`, `git fetch`, `git merge-base`, `echo`, `printf`,
doc-only `[[ ]]` shell, `BASE_BRANCH=`, `CHANGED=`), and compares each
candidate against the plan's `## CI Commands` bullet list (substring
match: the discovered command must appear as a substring of some plan
bullet, modulo whitespace collapse). Unmatched candidates emit a WARN
naming the workflow, job, and command.

The plan may declare a `## CI Coverage Exemptions` block (optional) as
a bullet list — each bullet of the form
`` - `<substring-pattern>` — <justification> `` exempts any discovered
command matching the substring pattern, with the operator's
justification recorded inline. The exemption block is the only V1
justification mechanism (per non_goals).

This phase's own plan covers the lint by enumerating Qor-logic's
current CI surface explicitly in its `## CI Commands` section (rather
than using exemptions): the first time the lint runs against this very
plan, it should report zero WARNs. That self-application property is
the deterministic acceptance test for the lint shipping correctly —
captured in `test_lint_self_applies_to_phase_89_plan` below.

Tests follow the established Phase 84 / Phase 87 wiring convention:
behavior tests in `tests/test_ci_coverage_lint.py` cover each
classification branch with fixture workflows and fixture plans;
wiring tests in `tests/test_ci_coverage_lint_wiring.py` are anchored to
the `### Step 0.6` section header in `qor-audit` SKILL.md and paired
with a strip-and-fail negative per
`qor/references/doctrine-test-functionality.md`.

## Phase 1: ci_coverage_lint module + Step 0.6 wiring + doctrine bullet + tests

### Affected Files

- `qor/scripts/ci_coverage_lint.py` — NEW. The lint module.
- `qor/skills/governance/qor-audit/SKILL.md` — Step 0.6: add the
  `ci_coverage_lint` invocation to the WARN-only pre-audit lint block,
  after the existing four lints. Phase 89 wiring paragraph.
- `qor/references/doctrine-shadow-genome-countermeasures.md` — append an
  `SG-CICoverageDrift-A` paragraph (originating COREFORGE incident
  citation + Phase 89 countermeasure).
- `tests/test_ci_coverage_lint.py` — NEW. Behavior tests.
- `tests/test_ci_coverage_lint_wiring.py` — NEW. Anchored + strip-and-fail
  wiring test for the Step 0.6 paragraph.
- `docs/plan-qor-phase89-ci-commands-reconciliation.md` — NEW. This plan
  file.

### Unit Tests

- `tests/test_ci_coverage_lint.py`

  Each test uses tmp-path workflow + plan fixtures (no dependency on the
  repo's own `.github/workflows/*.yml`, except for the dedicated
  self-application test).

  - `test_python_pytest_command_in_workflow_matched_by_plan_yields_no_warning`
    — fixture workflow has a `run:` step invoking pytest in CI-form
    (verbose flag); fixture plan's `## CI Commands` lists pytest in
    quiet-flag form; the discovered command appears as a substring of
    the plan bullet (modulo trailing flag); no warnings.
  - `test_python_script_command_missing_from_plan_yields_warning`
    — fixture workflow `run: python qor/scripts/check_variant_drift.py`;
    fixture plan `## CI Commands` is empty; one WARN naming the workflow,
    job, and command.
  - `test_pip_install_is_not_a_candidate` — fixture workflow's only
    `run:` is `pip install -e ".[dev]"`; fixture plan has no CI Commands
    section; no warnings (env-setup filtered).
  - `test_git_fetch_and_merge_base_are_not_candidates` — fixture
    `release.yml`-style step `run: |\n  git fetch origin main --depth=100\n  git merge-base --is-ancestor "$X" origin/main`;
    no warnings.
  - `test_doc_only_conditional_bash_is_not_a_candidate` — fixture
    `pr-lint.yml`-style multiline `run:` block with `BASE_BRANCH=`,
    `[[ -z "$CHANGED" ]]`, `echo "result=false" >> $GITHUB_OUTPUT`; no
    warnings.
  - `test_tag_only_workflow_is_skipped` — fixture workflow with
    `on: { push: { tags: ['v*.*.*'] } }` containing
    `python -m build`; no warnings.
  - `test_multiline_run_block_extracts_each_python_command` — fixture
    workflow `run: |\n  python -m qor.reliability.X\n  python -m qor.reliability.Y`;
    fixture plan covers only one; one WARN for the uncovered command.
  - `test_exemption_block_suppresses_matching_warning` — fixture
    workflow has uncovered `python qor/scripts/check_variant_drift.py`;
    fixture plan has a `## CI Coverage Exemptions` bullet
    `` - `check_variant_drift` — pre-existing infra CI, not phase-relevant ``;
    no warnings.
  - `test_exemption_pattern_must_appear_as_substring_of_command`
    — boundary: an exemption bullet whose pattern is the string
    `nonexistent_module_name` does NOT suppress a warning for
    `check_variant_drift` (the exemption substring is unrelated to the
    candidate command).
  - `test_plan_missing_ci_commands_section_warns_for_every_candidate`
    — fixture plan has no `## CI Commands` section; every Python
    candidate in the fixture workflow emits a WARN.
  - `test_pytest_marker_form_is_candidate` — fixture workflow
    `run: python -m pytest tests/test_packaging_install.py -v -m integration`
    is a candidate (pytest marker syntax is part of the discoverable
    command); plan must cover it or exempt it.
  - `test_main_cli_returns_zero_even_with_warnings`
    — `subprocess.run([sys.executable, "-m", "qor.scripts.ci_coverage_lint", "--plan", <fixture-with-gaps>, "--workflows-dir", <fixture-dir>])`
    exit code is 0 (WARN-only contract); stdout contains the warning
    text.
  - `test_lint_self_applies_to_phase_89_plan`
    — self-application: run `check_plan` against
    `docs/plan-qor-phase89-ci-commands-reconciliation.md` with
    `workflows_dir=.github/workflows`; assert the returned warning list
    is empty (Phase 89's own plan must cover its own CI). This is the
    deterministic shipping-correctness test.

- `tests/test_ci_coverage_lint_wiring.py`

  - `test_step_0_6_invokes_ci_coverage_lint` — read
    `qor/skills/governance/qor-audit/SKILL.md`; isolate `### Step 0.6`
    section; assert it contains the substring
    `python -m qor.scripts.ci_coverage_lint`; assert it contains the
    substring `|| true` (the existing Step 0.6 WARN-only convention).
  - `test_step_0_6_assertion_fails_when_section_removed`
    — strip-and-fail negative: locate the Step 0.6 section in the
    SKILL.md text, remove it in-memory, re-isolate; assert the
    `ci_coverage_lint` substring is no longer present.

### Changes

`qor/scripts/ci_coverage_lint.py` — new module structured like the
existing `qor/scripts/*_lint.py` scripts:

```python
@dataclass(frozen=True)
class LintWarning:
    workflow: str
    job: str
    step_name: str | None
    command: str
    reason: str

def discover_ci_commands(workflows_dir: Path) -> list[tuple[str, str, str | None, str]]:
    """Walk *.yml in workflows_dir; return one tuple per plan-verifiable
    `run:` command. Skips tag-only workflows; filters env-setup."""

def check_plan(plan_path: Path, workflows_dir: Path) -> list[LintWarning]:
    """Compare discovered CI commands against the plan's `## CI Commands`
    section; honor `## CI Coverage Exemptions` substring patterns; emit
    WARN per unmatched, non-exempt command."""

def main(argv: list[str] | None = None) -> int:
    """CLI: prints warnings to stdout; exit 0 always (WARN-only,
    parallels delivery_branch_lint exit semantics)."""
```

Module-level normalization helpers:
- `_ENV_SETUP_PREFIXES`: tuple of `("pip install", "git fetch",
  "git merge-base", "echo ", "printf ", "cd ", ":", "mkdir ", "rm ",
  "mv ", "cp ", "cat ", "ls ")`.
- `_DOC_ONLY_PATTERNS`: tuple of regex prefixes matching common
  workflow-conditional bash (`r"^\s*(BASE_BRANCH|CHANGED)\s*="`,
  `r"^\s*\[\["`, `r"^\s*if\b"`, `r"^\s*fi\b"`, `r"^\s*then\b"`,
  `r"^\s*else\b"`, `r"^\s*>>"`, `r"^\s*exit \d"`).
- `_PYTHON_CANDIDATE_RE`: regex matching a line that starts with
  optional whitespace then `python ` or `pytest ` (the V1 fingerprint).

Discovery normalization:
- Each `run:` block is split into logical lines (split on `\n`).
- For each line, strip leading whitespace and any trailing `|| true`,
  `|| ABORT`, `|| { ... }` clauses (the existing Step 0.6 WARN
  convention).
- Drop empty lines and lines starting with `#` (comments).
- Drop lines matching `_ENV_SETUP_PREFIXES` or `_DOC_ONLY_PATTERNS`.
- Keep lines matching `_PYTHON_CANDIDATE_RE`; these are the
  candidates.

Tag-only workflow detection:
- Parse the workflow's `on:` key. If it is a dict whose only trigger
  keys are `push.tags` or `release` (no `pull_request`, no
  `push.branches`, no `workflow_dispatch`), skip the workflow.

Match rule:
- For each candidate `(workflow, job, step_name, command)`, normalize
  the command (collapse whitespace runs to a single space).
- Read the plan's `## CI Commands` section as a list of bullets;
  normalize each bullet's text the same way; keep only the portion
  between the first leading `` ` `` and the matching closing `` ` ``
  if the bullet is backticked (otherwise the whole bullet text).
- Read the plan's `## CI Coverage Exemptions` section the same way
  for exemption patterns.
- For each candidate command:
  - If any plan bullet contains the candidate command as a substring,
    it is covered.
  - Else if any exemption pattern is a substring of the candidate
    command, it is exempt (operator-justified).
  - Else emit a WARN.

`qor/skills/governance/qor-audit/SKILL.md` — Step 0.6 gets one new
line in the WARN-only pre-audit lint block, placed after the
existing four lints, and a `Phase 89 wiring (GH #91)` paragraph that
cites the workflow-vs-plan reconciliation purpose and the
COREFORGE-class originating incident:

```bash
python -m qor.scripts.ci_coverage_lint --plan "$PLAN_PATH" --workflows-dir .github/workflows || true
```

Argv-form invocation; SG-Phase47-A countermeasure honored by
construction (no `python -c "...${VAR}..."` interpolation).

`qor/references/doctrine-shadow-genome-countermeasures.md` — append
`SG-CICoverageDrift-A`: pattern (phase plans hand-author `ci_commands`
without parsing actual workflow files; CI jobs the operator forgot to
list never run via the governed cycle; latent CI failures surface only
at integration PR time after multiple seals); originating incident
(COREFORGE 2026-05-22 10-phase stack; `Architecture Guard`
`check_test_metadata.py` failed after 10 seals); countermeasure
(Phase 89 `qor.scripts.ci_coverage_lint` at `/qor-audit` Step 0.6;
WARN-only; plan-side `## CI Coverage Exemptions` block for operator
justification).

## CI Coverage Exemptions

None for this phase. Phase 89's own plan declares the full Qor-logic
CI surface in `## CI Commands` below to satisfy
`test_lint_self_applies_to_phase_89_plan`.

## CI Commands

- `python -m pytest tests/test_ci_coverage_lint.py -q` — behavior tests for the new lint module.
- `python -m pytest tests/test_ci_coverage_lint_wiring.py -q` — Step 0.6 wiring (anchored + strip-and-fail).
- `python -m pytest tests/ -v` — full regression suite (matches the ci.yml `test` job's `-v` form).
- `python qor/scripts/check_variant_drift.py` — ci.yml `test` job step.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ci.yml `test` job step.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — ci.yml `install-smoke` job step.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — ci.yml `gate-chain-completeness` job step.
- `python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto` — ci.yml `test` job step (Phase 156, GAP-GOV-03: re-verify the committed seal binding).
- `python qor/scripts/pr_citation_lint.py` — pr-lint.yml `lint` job step (non-doc-only PRs).
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase89-ci-commands-reconciliation.md` — plan-internal text-consistency.
- `python -m qor.scripts.dependency_admission_lint --base <ref>` — Phase 105 pr-dependency-review.yml WARN-only step (forward-maintenance: command introduced after Phase 89 seal; the self-applied test discipline requires Phase 89's CI Commands list to enumerate every operator-runnable Python invocation across all workflows).
- `python -m qor.scripts.session_id_lint` — Phase 106 /qor-substantiate Step 4.6 WARN-only step (forward-maintenance; same pattern as the Phase 105 entry above).
- `python -m qor.scripts.gate_provenance verify-committed --phase-min 158` — Phase 158 ci.yml `provenance-attest` job: keyless GAP-GOV-05 merge gate over committed provenance sidecars (forward-maintenance; command introduced after Phase 89 seal).
- `python -m qor.scripts.gate_provenance attest-latest` — Phase 158 ci.yml `provenance-attest` job: emit the CI-secret-keyed attestation over the latest sealed entry (disclosed-skip when the secret is absent; forward-maintenance).
