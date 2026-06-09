# Research Brief

**Date**: 2026-06-09
**Analyst**: The Qor-logic Analyst
**Target**: Phase 142 -- downstream enforcement SDK (engagement precursor values + mini-SDK over the compliance control matrix)
**Scope**: `qor/cli.py`, `qor/cli_handlers/compliance.py`, the deterministic gate `main()` signatures, `qor/compliance/`, `pyproject.toml` packaging, `qor/scripts/compliance_conformance.py`

---

## Executive Summary

The mechanism the operator wants -- Qor-logic ships a cohesive enforcement contract + mini-SDK,
downstream owns the trigger -- is buildable on the Phase 141 matrix with small, well-grounded
additions. The matrix becomes the engagement manifest (add an `engagement` precursor field + an
optional `runner` block), and a thin `qor-logic compliance enforce --engagement <point>` facade runs
the runnable controls and returns a structured verdict. Two drifts must be fixed for it to work
downstream: (1) the matrix JSON is NOT currently in `package-data`, so pip consumers never receive
it; (2) the import package is `qor`, not `qor_logic`. Five of the nine seeded controls are cleanly
standalone-runnable (the deterministic pre-commit-grade gates); the other four are seal/CI-context
and get an `engagement` tag but no V1 runner.

## Findings

### CLI dispatch -- where `enforce` fits

- The CLI entry is `qor.cli:main` (`pyproject.toml:32`). `_build_parser` (`qor/cli.py:275`) registers
  families via `_register_compliance_policy` (`qor/cli.py:235-243`), which delegates to
  `qor/cli_handlers/compliance.py`.
- `cli_handlers/compliance.py` already owns a `compliance` subcommand group with `register(sub)`
  (`:86`) and `dispatch(args)` (`:103`), today exposing `report` / `ai-provenance` / `sprint-progress`
  subparsers (`:90-96`). **A new `enforce` subparser slots in here** -- `qor-logic compliance enforce
  --engagement <point>` -- reusing the existing register/dispatch pattern. No new top-level command or
  cli wiring change beyond this handler.

### Gate runner contract -- uniform `main(argv) -> int`

Every deterministic gate exposes the same callable shape (an importable `main(argv: list[str] | None)
-> int`, exit 0 pass / 1 fail), so a `runner` block of `{module, entry, args}` runs via
`importlib.import_module(module).main(args)` capturing the return code:

| Control | Entry | Args (illustrative) | Source |
|---|---|---|---|
| secret-scan | `qor.scripts.secret_scanner:main` | `--staged` (or `--files ...`) | `secret_scanner.py:223,197-200`; exit `secret_scanner.py:251` |
| data-api-acl | `qor.scripts.data_api_acl_lint:main` | `--repo-root .` | `data_api_acl_lint.py:190-193`; exit `:201,210` |
| prompt-injection | `qor.scripts.prompt_injection_canaries:main` | `--files <paths>` | `prompt_injection_canaries.py:151,156`; exit `:193` |
| prose-test-lint | `qor.scripts.prose_test_lint:main` | `--tests-dir tests --enforce` | `prose_test_lint.py:151-154`; exit `:168,169` |
| badge-currency | `qor.scripts.badge_currency:main` | `--repo-root . --ledger docs/META_LEDGER.md` | `badge_currency.py:135-138`; exit `:145,147` |

### Runnability classification (engagement V1)

- **Standalone-runnable (pre-commit / pre-push grade)**: `secret-scan`, `data-api-acl`,
  `prompt-injection`, `prose-test-lint`, `badge-currency`. Each runs from a working tree / git
  context with no seal/session state. These are the V1 SDK runners.
- **Seal/CI-context (engagement tag, no V1 runner)**: `governance-index` (advances Last-Reviewed,
  seal-time), `gate-chain-completeness` (needs sealed gate artifacts), `ai-provenance` (enforced
  inside `gate_chain.write_gate_artifact`, detection=test -- not a standalone CLI),
  `dependency-review` (a CI job, detection=ci-job). These get `engagement: ["ci"]` (or `["seal"]`)
  and `runner: null`; the SDK skips them for pre-commit/pre-push points.

### Packaging -- the matrix does NOT ship (DRIFT, load-bearing)

- `pyproject.toml:41` sets `include-package-data = true`; `:43-44` `packages.find include = ["qor*"]`
  (so the `qor.compliance` package ships); `:47-59` `[tool.setuptools.package-data]` lists
  `gates/schema/*.json` and `dist/variants/**/*.json` -- **but NOT `compliance/*.json`**.
- Grep-evidence: `grep -nE "compliance|control_matrix" pyproject.toml` returns nothing under
  package-data. Net: `pip install qor-logic` delivers the loader code and the schema (under
  `gates/schema/*.json`) but **not `qor/compliance/control_matrix.json`** -- the SDK would have no
  manifest downstream. **Fix: add `"compliance/*.json"` to `[tool.setuptools.package-data]."qor"`.**

### Import-package naming (DRIFT)

- The PyPI distribution is `qor-logic` (`pyproject.toml:6`) but the **import package is `qor`** (all
  source uses `from qor.scripts import ...`). The prior-conversation name `qor_logic.sdk` is wrong;
  the SDK facade is `qor.sdk` (a thin re-export) or, cohesively, `qor.compliance.enforce`.

### Conformance extension

`qor/scripts/compliance_conformance.py:verify_control` (Phase 141) already dispatches on `detection`.
A V1 addition: for any control carrying `engagement` + a non-null `runner`, verify the runner module
is importable and the `entry` attribute is callable (a control claiming to be runnable cannot point at
a missing entry). This reuses the existing failure-reason list shape; the live conformance test then
guards runner integrity the same way it guards posture.

## Blueprint Alignment

| Blueprint Claim (prior conversation) | Actual Finding | Status |
|---|---|---|
| Extend matrix with `engagement` + `runner` | Matrix schema is local + additive; `additionalProperties:false` must be relaxed for the new fields | MATCH (schema edit needed) |
| `qor-logic enforce` CLI | Best as `qor-logic compliance enforce` via existing `cli_handlers/compliance.py` register/dispatch | MATCH (placement refined) |
| `qor_logic.sdk` Python facade | Import package is `qor`; use `qor.sdk` / `qor.compliance.enforce` | DRIFT (naming) |
| Gates callable as runners | All five expose `main(argv)->int`; uniform | MATCH |
| Matrix conveyed to consumers | `compliance/*.json` absent from package-data | DRIFT (must add) |

## Recommendations

1. **Add `compliance/*.json` to `pyproject.toml` package-data (P0)** -- without it the SDK has no
   manifest in a pip install; nothing else works downstream. One-line packaging fix + a test that
   asserts the matrix path is covered by the package-data globs.
2. **Extend the matrix schema + seed rows**: add `engagement` (closed-enum array over
   `pre-commit | pre-push | pre-tool-write | ci | seal`) and optional `runner` (`module`, `entry`,
   `args[]`); relax `additionalProperties` for the two fields. Tag the five runnable controls with
   pre-commit/pre-push + a runner; tag the rest `ci`/`seal` with `runner: null`.
3. **Build the SDK core `qor.compliance.enforce`**: `enforce(engagement, root) -> Verdict(passed,
   results[])` where each result is `(control_id, posture, exit_code, passed)`; wire
   `qor-logic compliance enforce --engagement <point>` in `cli_handlers/compliance.py`; add a thin
   `qor.sdk` re-export for a stable top-level import.
4. **Extend `compliance_conformance`** so every engagement-tagged control with a runner is verified
   importable+callable; the live conformance test guards it.
5. **Downstream-integration doc**: a consumer wires their own hook (git `pre-commit`, Claude
   `PreToolUse`, CI step) to call `qor-logic compliance enforce --engagement pre-commit` and act on the
   exit code. Hook wiring stays out of scope -- the doc shows the contract, not an installer.

**Phasing**: rec 1 (packaging) + rec 2 (schema/seed) are the precursor values; rec 3 (SDK + CLI) is
the facade; rec 4 (conformance) keeps it honest; rec 5 (doc) hands ownership downstream. One feature
phase. The conformance/ratchet self-validation from Phase 141 extends to the new fields for free.

## Updated Knowledge

Candidate doctrine note (extend `doctrine-compliance-conveyance.md`): the matrix is not only a
verification manifest but the **engagement manifest** a downstream SDK consumes; `engagement` is the
precursor value naming which active enforcement layer a control plugs into, and `runner` is the
standalone-callable contract. Ownership boundary: Qor-logic owns the manifest + uniform runner
behavior + verdict shape; the consumer owns the trigger. Two packaging invariants must hold or the
conveyance silently fails: the matrix JSON ships in package-data, and the import package is `qor`.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
