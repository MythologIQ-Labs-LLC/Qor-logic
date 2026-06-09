# Plan: Phase 142 -- downstream enforcement SDK (engagement manifest + mini-SDK)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: Engagement Point
  home: qor/references/doctrine-compliance-conveyance.md
- term: Enforcement Runner
  home: qor/references/doctrine-compliance-conveyance.md

**boundaries**:
- limitations:
  - V1 ships generic runners only for the four context-free gates (secret-scan, data-api-acl,
    prose-test-lint, badge-currency). `prompt-injection` needs explicit `--files`, so it is tagged
    `ci` with `runner: null` (not a generic standalone runner); the seal/CI controls likewise.
  - The SDK runs a control by importing its `runner.module` and calling `runner.entry(args)`; a
    control with no runner is not runnable and is skipped for runnable engagement points.
- non_goals:
  - No hook installer and no hook pack. Trigger wiring (git hooks, Claude PreToolUse, CI steps)
    stays entirely downstream-owned; this phase ships the contract + SDK the consumer calls.
  - No change to any gate's own behavior; the SDK is a uniform facade over existing `main(argv)`.
- exclusions:
  - `docs/FEATURE_INDEX.md` (pre-existing MISSING, separate remediation).

## Open Questions

None. Grounded in `docs/research-brief-downstream-enforcement-sdk-2026-06-09.md` and verified source.

## Phase 1: Engagement + runner matrix fields

### Affected Files

- `tests/test_compliance_matrix_loader.py` (EXTEND) - engagement/runner parse + schema rejection.
- `qor/gates/schema/control_matrix.schema.json` - add `engagement` (required, enum array) + `runner` (optional object/null).
- `qor/compliance/control_matrix.json` - add `engagement` + `runner` to all nine controls.
- `qor/scripts/compliance_matrix.py` - `Control` gains `engagement: tuple[str,...]`, `runner: dict | None`; add `ENGAGEMENTS`, `RUNNABLE_POINTS`.

### Changes

Schema: each control item gains `engagement` (required; `{"type":"array","items":{"enum":["pre-commit","pre-push","pre-tool-write","ci","seal"]}}`) and `runner` (optional; either `null` or `{"module":str,"entry":str,"args":[str]}` with `additionalProperties:false`). Grep-evidence (LD-142a):
> `grep -n additionalProperties qor/gates/schema/control_matrix.schema.json` -> control items are `additionalProperties:false`, so the two new properties must be declared explicitly.

`compliance_matrix.py`: `ENGAGEMENTS = ("pre-commit","pre-push","pre-tool-write","ci","seal")`;
`RUNNABLE_POINTS = ("pre-commit","pre-push","pre-tool-write")`; `Control` gains `engagement` (tuple)
and `runner` (dict|None); `load_matrix` populates them.

Seed mapping (engagement / runner):
- `secret-scan`: `[pre-commit, pre-push]` / `{qor.scripts.secret_scanner, main, [--staged]}`
- `data-api-acl`: `[pre-commit, pre-push]` / `{qor.scripts.data_api_acl_lint, main, [--repo-root, .]}`
- `prose-test-lint`: `[pre-commit]` / `{qor.scripts.prose_test_lint, main, [--tests-dir, tests, --enforce]}`
- `badge-currency`: `[pre-push]` / `{qor.scripts.badge_currency, main, [--repo-root, ., --ledger, docs/META_LEDGER.md]}`
- `prompt-injection`: `[ci]` / `null` (needs explicit --files context)
- `governance-index`, `gate-chain-completeness`, `ai-provenance`: `[seal]` / `null`
- `dependency-review`: `[ci]` / `null`

### Unit Tests

- `tests/test_compliance_matrix_loader.py` (extend):
  - `test_engagement_and_runner_parsed` - `load_matrix(REPO)`; every control's `engagement` is a
    non-empty tuple of `ENGAGEMENTS` members; controls with a runnable engagement point carry a
    `runner` dict with `module`/`entry`/`args`.
  - `test_schema_rejects_unknown_engagement` - a synthetic control with `engagement:["nope"]` raises
    `ValueError` (invoke loader on tmp matrix, assert raise).

## Phase 2: SDK core + `qor-logic compliance enforce`

### Affected Files

- `tests/test_compliance_enforce.py` (NEW) - run_control/enforce behavior on synthetic + real controls.
- `qor/compliance/enforce.py` (NEW) - SDK core.
- `qor/sdk.py` (NEW) - thin re-export facade.
- `qor/cli_handlers/compliance.py` - add `enforce` subparser + dispatch route.

### Changes

`enforce.py`:
- `@dataclass(frozen=True) ControlResult` (`id`, `posture`, `exit_code`, `passed`).
- `@dataclass(frozen=True) Verdict` (`engagement`, `passed`, `results: tuple[ControlResult,...]`).
- `run_control(control, root) -> ControlResult` -- `importlib.import_module(control.runner["module"])`,
  `getattr(mod, control.runner["entry"])`, call with `control.runner["args"]`, capture int exit code;
  `passed = exit_code == 0`. (Runs from `root` as cwd via a `contextlib.chdir`-style guard.)
- `enforce(engagement, root) -> Verdict` -- select controls where `engagement in control.engagement`
  AND `control.runner` is not None; run each; `passed = every ABORT-posture result passed` (WARN
  failures are recorded but do not fail the verdict, honoring posture).
- `main(argv) -> int` -- `--engagement`, `--repo-root`; print per-control results; return 0/1.

Grep-evidence (LD-142b, runner entry contract):
> `grep -n "def main" qor/scripts/secret_scanner.py qor/scripts/data_api_acl_lint.py qor/scripts/prose_test_lint.py qor/scripts/badge_currency.py`
> -> each defines `def main(argv: list[str] | None = None) -> int` (uniform callable).

`qor/cli_handlers/compliance.py`: add `compliance_sub.add_parser("enforce", ...)` with
`--engagement` (required, choices from `ENGAGEMENTS`) + `--repo-root` (default `.`); in `dispatch`,
route `cmd == "enforce"` to a `do_enforce(args)` that calls `enforce.enforce(...)`, prints the
verdict, returns `0 if verdict.passed else 1`. Grep-evidence (LD-142c):
> `grep -n "def register\|def dispatch\|compliance_command" qor/cli_handlers/compliance.py`
> -> `register` at :85 adds subparsers under `compliance_sub`; `dispatch` at :102 routes on
> `compliance_command`.

`qor/sdk.py`: `from qor.compliance.enforce import enforce, Verdict, ControlResult` (+ `__all__`).

### Unit Tests

- `tests/test_compliance_enforce.py`:
  - `test_run_control_reports_exit_code` - a synthetic control whose runner points at a tmp module
    with `def main(argv): return 0` yields `ControlResult(passed=True, exit_code=0)`; a module whose
    `main` returns 1 yields `passed=False` (write tmp module, import via runner, assert result).
  - `test_enforce_selects_by_engagement_and_runner` - given controls tagged `[pre-commit]`+runner and
    `[seal]`+null, `enforce("pre-commit", root)` runs only the first (assert `result.id` set).
  - `test_enforce_verdict_fails_when_abort_runner_fails` - an ABORT control whose runner returns 1
    makes `Verdict.passed False`; a WARN control returning 1 leaves `passed True` (posture honored).
  - `test_sdk_reexports_enforce` - `from qor.sdk import enforce` is the same callable as
    `qor.compliance.enforce.enforce` (assert identity).
  - `test_cli_enforce_runs_pre_commit` - `compliance_handlers.dispatch` with a namespace
    `compliance_command="enforce", engagement="pre-commit", repo_root=REPO` returns an int exit code
    (0 on the clean repo) -- exercises the real wired path end to end.

## Phase 3: Packaging + conformance + docs

### Affected Files

- `tests/test_package_data_ships_matrix.py` (NEW) - matrix is covered by package-data globs.
- `tests/test_compliance_conformance.py` (EXTEND) - runner integrity check.
- `pyproject.toml` - add `compliance/*.json` to `[tool.setuptools.package-data]."qor"`.
- `qor/scripts/compliance_conformance.py` - verify each control with a runnable engagement point has
  an importable runner whose entry is callable.
- `qor/references/doctrine-compliance-conveyance.md` (EXTEND) - engagement manifest + runner + ownership.
- `qor/references/downstream-enforcement-sdk.md` (NEW) - consumer integration doc.
- `qor/references/glossary.md` - two new terms.

### Changes

`pyproject.toml`: add `"compliance/*.json"` to the `"qor"` package-data list. Grep-evidence (LD-142d):
> `grep -nE "package-data|gates/schema|compliance" pyproject.toml` -> package-data lists
> `gates/schema/*.json` + `dist/variants/**/*.json` but NOT `compliance/*.json`; the matrix would not
> ship to a pip consumer without this line.

`compliance_conformance.py`: add `_verify_runner(control, root) -> list[str]` -- for any control whose
`engagement` intersects `RUNNABLE_POINTS`, FAIL when `runner` is None, the module is not importable,
or `entry` is not callable; fold its reasons into `verify_control`'s result so the live conformance
test guards runner integrity alongside posture/conveyance.

Docs: extend the doctrine with the engagement-manifest + runner + ownership-boundary sections; the new
`downstream-enforcement-sdk.md` shows a consumer wiring their own hook to `qor-logic compliance enforce
--engagement pre-commit` (contract, not an installer). Two glossary terms (Engagement Point,
Enforcement Runner) homed in the doctrine.

### Unit Tests

- `tests/test_package_data_ships_matrix.py`:
  - `test_matrix_covered_by_package_data` - parse `pyproject.toml`; assert at least one
    `package-data["qor"]` glob matches `compliance/control_matrix.json` (fnmatch), so the manifest
    ships. Fails today, passes after the packaging line.
- `tests/test_compliance_conformance.py` (extend):
  - `test_conformance_flags_missing_runner_for_runnable_point` - a synthetic control tagged
    `[pre-commit]` with `runner=None` returns a reason naming the missing runner.
  - `test_conformance_flags_uncallable_runner` - a runner pointing at a real module but a missing
    `entry` attribute returns a reason.
  - `test_every_seeded_runnable_control_has_callable_runner` - over the real matrix, every control
    with a runnable engagement point imports and exposes a callable entry (live guard).

## Definition of Done

### Deliverable: D-engagement -- engagement + runner precursor values

- **D1**: every conveyed control declares which enforcement layers it engages and, when standalone-
  runnable, how to run it.
- **D2**: schema `engagement`(req enum array)+`runner`(opt); `Control.engagement`/`Control.runner`;
  `ENGAGEMENTS`/`RUNNABLE_POINTS` in `compliance_matrix.py`; all nine rows seeded.
- **D3**: ledger SESSION SEAL records the fields; doctrine + 2 glossary terms.
- **D4**: `test_engagement_and_runner_parsed` + `test_schema_rejects_unknown_engagement`.

### Deliverable: D-sdk -- the enforce facade

- **D1**: a downstream consumer runs `qor-logic compliance enforce --engagement <point>` (or `qor.sdk.enforce`)
  and gets a structured pass/fail over that point's runnable controls.
- **D2**: `qor.compliance.enforce.{run_control,enforce,Verdict,ControlResult}`; `qor.sdk` re-export;
  `enforce` subparser + dispatch in `cli_handlers/compliance.py`.
- **D3**: ledger entry + the downstream-integration doc record the contract.
- **D4**: `test_enforce_selects_by_engagement_and_runner` + `test_enforce_verdict_fails_when_abort_runner_fails`
  + `test_cli_enforce_runs_pre_commit`.

### Deliverable: D-conveyance -- the matrix actually ships + runners verified

- **D1**: the matrix reaches pip consumers and every runnable control has a working runner.
- **D2**: `pyproject` package-data covers `compliance/*.json`; `compliance_conformance._verify_runner`.
- **D3**: ledger entry records the packaging fix.
- **D4**: `test_matrix_covered_by_package_data` + `test_every_seeded_runnable_control_has_callable_runner`.

## CI Commands

- `python -m pytest tests/test_compliance_matrix_loader.py tests/test_compliance_enforce.py tests/test_compliance_conformance.py tests/test_package_data_ships_matrix.py -q` -- the new/extended suites.
- `python -m pytest -q` -- full suite green.
- `qor-logic compliance enforce --engagement pre-commit` -- the SDK facade runs the pre-commit controls.
- `qor-logic scripts compliance_conformance` -- conformance incl. runner integrity.
