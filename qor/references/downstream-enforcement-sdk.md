# Downstream Enforcement SDK

A consumer that installs `qor-logic` gets a cohesive enforcement contract and a mini-SDK; the
consumer owns the trigger. Qor-logic does not install or manage any hook -- it conveys the controls
and the runner; you wire your own enforcement layer to call them.

## What ships

- The **engagement manifest** (`qor/compliance/control_matrix.json`, shipped in package-data): every
  control with its `engagement` points and, where standalone-runnable, its `runner`.
- The **SDK**: `qor.compliance.enforce` (re-exported at `qor.sdk`) and the CLI
  `qor-logic compliance enforce --engagement <point>`.

## Engagement points

`pre-commit`, `pre-push`, `pre-tool-write`, `ci`, `seal`. The SDK runs only controls wired to the
requested point that carry a runner (the runnable points are `pre-commit` / `pre-push` /
`pre-tool-write`); `ci` / `seal` controls run in the audit/seal flow.

## Using it from your own trigger

The contract is a single command that returns a structured result and an exit code (0 pass / 1 fail):

```
qor-logic compliance enforce --engagement pre-commit --repo-root .
```

Python:

```python
from qor.sdk import enforce
verdict = enforce("pre-commit", root=".")
if not verdict.passed:
    for r in verdict.results:
        print(r.id, r.posture, r.exit_code, r.passed)
    raise SystemExit(1)
```

Wire that command into whatever enforcement layer you own -- a git `pre-commit` / `pre-push` hook, an
editor/agent pre-action hook, or a CI step. Qor-logic deliberately ships no hook installer: the
trigger, and the decision of when and whether to enforce, are yours.

## Verdict semantics

A control's posture decides severity: an `ABORT` control whose runner fails makes the verdict fail; a
`WARN` control's failure is recorded but advisory. The exit code follows the verdict.

Each `ControlResult` carries an explicit `status` (Phase 148): `pass`, `fail`, `skip`, or `disclosed`.
The `Verdict.status` is `enforced` (at least one control ran), `failed` (an `ABORT` control failed), or
`no_op` (nothing actually ran). `verdict.passed` is `status != "failed"`; the SDK never returns a silent
PASS for an engagement that enforced nothing -- a `no_op` is reported explicitly.

- **Disclosed-skip** -- a runner may declare `requires` paths (relative to the consumer root). If any is
  absent, the control reports `skip` *without* importing or invoking its runner, so a consumer who lacks
  a given governance artifact is not hard-failed.
- **Disclosed (non-CLI) controls** -- a control that is enforced elsewhere and has no CLI runner carries
  `runner: null` + a `runner_unavailable_reason`; `enforce()` surfaces it with `status: disclosed` and
  the reason, rather than silently dropping it. (V1 examples: `ai-provenance` is a gate-write-time
  manifest builder; `dependency-review` is a GitHub Action.)
- **ci / seal engagements** now carry real runners (`prompt-injection` for ci; `governance-index` +
  `gate-chain-completeness` for seal) plus disclosed controls -- they are no longer vacuous passes.
