# Plan: Phase 148 -- Audit Sprint B (conveyance correctness) + Sprint C tail

**change_class**: feature

**doc_tier**: minimal

## Open Questions

None. Implements GH #211 (Sprint B conveyance correctness) from the production-gap audit, plus the last
Sprint C item (GAP-TEST-10) folded in. Two operator decisions are already settled: ci/seal get **real
runners** (wire the 3 CLI-runnable controls; disclose the 2 that genuinely cannot be CLI runners), and the
wiring uses a disclosed-skip-if-absent mechanism so a consumer lacking a governance artifact is not
hard-failed. Verified runnability: `prompt_injection_canaries.main --files` (ci); `governance_index.main
--cross-check-ledger` (seal, already Phase-75 graceful on absent index); `gate_chain_completeness.main
--repo-root .` (seal). Not CLI-runnable (disclosed): `ai_provenance` (a manifest builder, no pass/fail
entry) and `dependency-review` (a GitHub Action, no CLI module). Deferred: GAP-SEC-01 (constrain the
conformance importlib target to an allowlist) -- a separate hardening, noted not done.

## Phase 1: schema + matrix (wire 3, disclose 2)

### Affected Files

- `qor/gates/schema/control_matrix.schema.json` - runner gains optional `requires` (array of paths); control gains optional `runner_unavailable_reason` (string).
- `qor/compliance/control_matrix.json` - wire prompt-injection / governance-index / gate-chain-completeness; add `runner_unavailable_reason` to ai-provenance + dependency-review.
- `qor/scripts/compliance_matrix.py` - `Control` gains `runner_unavailable_reason: str | None`; parsed from the row.
- `tests/test_compliance_matrix.py` - assert the 3 runners + 2 disclosed reasons parse.

### Changes

Schema `runner` object: add `"requires": {"type": "array", "items": {"type": "string"}}` (optional;
keeps `additionalProperties: false`). Control item: add `"runner_unavailable_reason": {"type": "string"}`
(optional). Matrix runners:
- prompt-injection: `{"module": "qor.scripts.prompt_injection_canaries", "entry": "main", "args": ["--files", "docs/META_LEDGER.md"], "requires": ["docs/META_LEDGER.md"]}`
- governance-index: `{"module": "qor.scripts.governance_index", "entry": "main", "args": ["--cross-check-ledger", "--repo-root", "."], "requires": ["docs/GOVERNANCE_INDEX.md"]}`
- gate-chain-completeness: `{"module": "qor.reliability.gate_chain_completeness", "entry": "main", "args": ["--repo-root", "."], "requires": ["docs/META_LEDGER.md"]}`
- ai-provenance: `runner: null`, `runner_unavailable_reason: "build_manifest() embeds provenance at gate-write time; not a standalone pass/fail gate (enforced via tests/test_gate_chain_phase52_provenance_still_enforced.py)"`
- dependency-review: `runner: null`, `runner_unavailable_reason: "enforced as a GitHub Action (.github/workflows/pr-dependency-review.yml); not a CLI-invokable control"`

### Unit Tests

- `tests/test_compliance_matrix.py`:
  - `test_ci_seal_runnable_controls_have_runners` - prompt-injection / governance-index / gate-chain-completeness each return a runner dict with a `requires` list.
  - `test_disclosed_controls_carry_reason` - ai-provenance + dependency-review have `runner is None` AND a non-empty `runner_unavailable_reason`.

## Phase 2: enforce() status + disclosed-skip (no vacuous PASS)

### Affected Files

- `qor/compliance/enforce.py` - `ControlResult` gains `status`; `run_control` honors `requires`; `enforce`/`Verdict` gain `status` and surface disclosed controls; `main` prints status + reasons.
- `tests/test_compliance_enforce.py` - extend.

### Changes

`ControlResult` gains `status: str` ("pass" | "fail" | "skip" | "disclosed"); `passed` becomes
`status != "fail"`. `run_control`: if `runner.get("requires")` names a path absent under `root`, return
`ControlResult(status="skip", exit_code=0)` without importing/invoking; else run and set status from the
exit code. `enforce`: results = the runnable controls (run -> pass/fail/skip) PLUS one synthetic
`ControlResult(status="disclosed", exit_code=0)` per engagement-matched control whose `runner is None` and
that carries a `runner_unavailable_reason`. `Verdict` gains `status`: `"failed"` if any ABORT result is
`fail`; else `"enforced"` if >=1 result is `pass`/`fail`; else `"no_op"` (everything skipped/disclosed --
nothing actually ran). `passed = status != "failed"`. `main`: print each result `STATUS id (posture)`,
print each disclosed reason, print `engagement X: <status>`; return 1 only when `status == "failed"`.

### Unit Tests

- `tests/test_compliance_enforce.py`:
  - `test_requires_absent_yields_skip` - a control whose `requires` path is missing under root -> result status `skip`, not imported; verdict not `failed`.
  - `test_requires_present_runs` - same control with the path present -> status `pass`/`fail` from the runner.
  - `test_disclosed_control_surfaced_not_silent` - an engagement with a disclosed (null+reason) control yields a result with status `disclosed` carrying the reason; verdict status is not a bare `enforced` when nothing ran.
  - `test_seal_engagement_not_vacuous_pass` - `enforce("seal", root)` over the real packaged matrix no longer returns an empty-results PASS: results include the wired seal controls (pass/skip) and the disclosed ones; status is explicit.

## Phase 3: conformance + packaging + py.typed + cwd tail

### Affected Files

- `qor/scripts/compliance_conformance.py` - verify ANY control carrying a runner has an importable+callable entry (not only RUNNABLE_POINTS controls).
- `qor/py.typed` (NEW, empty marker) + `pyproject.toml` package-data glob.
- `tests/test_packaging.py` - add `compliance/` and `py.typed` to `required_fragments`.
- `tests/test_doctrine_dependency_admission.py`, `tests/test_codeowners_doctrine.py` - GAP-TEST-10 cwd-coupling fix (resolve from `__file__`). [already applied]

### Changes

`_verify_runner`: in addition to the existing RUNNABLE_POINTS requirement, when `control.runner` is
present (any engagement), assert its module imports and entry is callable -- so the 3 newly-wired ci/seal
runners are guarded against drift. Create empty `qor/py.typed`; add `"py.typed"` to the `qor`
package-data globs in `pyproject.toml`. `test_pyproject_declares_package_data.required_fragments` gains
`"compliance/"` and `"py.typed"`.

### Unit Tests

- `tests/test_compliance_conformance.py`:
  - `test_wired_ci_seal_runners_are_importable` - conformance over the real matrix reports no failure for the 3 wired runners (their modules import + entries callable).
- `tests/test_packaging.py`:
  - extend `test_pyproject_declares_package_data` to assert `compliance/` and `py.typed` are in the globs (regression floor: silent removal of the SDK matrix data or the type marker fails a test).
- `tests/test_py_typed_marker.py` (NEW):
  - `test_py_typed_ships` - `qor/py.typed` exists and is empty (PEP 561 marker), so the typed SDK surface is consumable by downstream type checkers.

## Definition of Done

### Deliverable: D-sprint-b-conveyance

- **D1**: `compliance enforce --engagement ci|seal` enforces real controls and never returns a vacuous PASS; the typed SDK ships a `py.typed` marker; the SDK matrix data is guarded against silent removal.
- **D2**: 3 controls carry importable runners with `requires` disclosed-skip; 2 carry `runner_unavailable_reason`; `enforce()` surfaces status (`enforced`/`failed`/`no_op`) + skips + disclosed; `qor/py.typed` ships via package-data.
- **D3**: ledger SEAL records Sprint B closure (GAP-ARCH-02/CLI-07/CLI-01/CLI-03) + the GAP-TEST-10 tail; GAP-SEC-01 deferred with rationale.
- **D4**: `test_requires_absent_yields_skip` (skip, not import) + `test_seal_engagement_not_vacuous_pass` (explicit status over real matrix) + `test_disclosed_control_surfaced_not_silent` + `test_wired_ci_seal_runners_are_importable` + `test_py_typed_ships` + the packaging-guard extension.

## CI Commands

- `python -m pytest tests/test_compliance_enforce.py tests/test_compliance_matrix.py tests/test_compliance_conformance.py tests/test_packaging.py tests/test_py_typed_marker.py -q` -- new + extended (run twice for determinism).
- `python -m pytest -q` -- full suite green.
