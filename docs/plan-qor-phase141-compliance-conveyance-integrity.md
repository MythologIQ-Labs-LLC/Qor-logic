# Plan: Phase 141 -- compliance-conveyance integrity (control matrix + conformance + ratchet)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: Compliance Control Matrix
  home: qor/references/doctrine-compliance-conveyance.md
- term: Control Posture
  home: qor/references/doctrine-compliance-conveyance.md
- term: Conveyance Conformance
  home: qor/references/doctrine-compliance-conveyance.md
- term: Compliance Ratchet
  home: qor/references/doctrine-compliance-conveyance.md

**boundaries**:
- limitations:
  - V1 seeds the matrix with the deterministic, already-shipping gate controls; it is a working
    mechanism + initial registry, not an exhaustive enumeration of every framework clause. New
    controls append; the ratchet ensures none silently leaves.
  - Posture detection covers three declared mechanisms (`skill-marker`, `test`, `ci-job`); a control
    enforced by a mechanism outside those three cannot be expressed in V1 and must be added to the
    dispatcher first.
- non_goals:
  - No git-hook installer and no Claude Code hook pack (operator deferred all hook work).
  - No change to any existing gate's behavior or posture; this phase only *describes and verifies*
    the controls that already exist.
  - No new CI workflow job: conformance + ratchet run as pytest tests inside the existing `ci.yml`
    pytest matrix.
- exclusions:
  - `docs/FEATURE_INDEX.md` (pre-existing MISSING, separate remediation).

## Open Questions

None. Design is grounded in
`docs/research-brief-compliance-conveyance-integrity-and-hook-gates-2026-06-09.md` and the verified
substantiate/audit gate ladder. Seed-posture accuracy is self-validating: a wrongly-seeded posture
makes the Phase 2 conformance test fail, forcing correction (the mechanism proves itself).

## Phase 1: Control matrix data + schema + loader

### Affected Files

- `tests/test_compliance_matrix_loader.py` (NEW) - loader + schema-validation behavior.
- `qor/compliance/control_matrix.json` (NEW) - the declarative registry (controls + waivers).
- `qor/gates/schema/control_matrix.schema.json` (NEW) - JSON schema (posture enum, required fields).
- `qor/compliance/__init__.py` (NEW) - package marker.
- `qor/scripts/compliance_matrix.py` (NEW) - pure loader/validator.

### Changes

`control_matrix.json` shape:
```json
{
  "schema_version": "1",
  "controls": [
    {
      "id": "secret-scan",
      "framework": "OWASP-LLM06 / NIST-AI-600-1 SS.2.10",
      "control": "pre-seal secret scan over staged content",
      "enforcing_module": "qor.scripts.secret_scanner",
      "invocation": "secret_scanner --staged",
      "posture": "ABORT",
      "detection": "skill-marker",
      "wired_into": {"skill": "qor/skills/governance/qor-substantiate/SKILL.md", "step": "4.6.5"},
      "variants": ["claude", "codex", "kilo-code", "gemini"]
    }
  ],
  "waivers": []
}
```
`detection` is one of `skill-marker` | `test` | `ci-job`. For `test`/`ci-job`, `wired_into` carries
`{"test": "<test path::name>"}` or `{"job": "<workflow::job>"}` instead of `skill`/`step`.

`compliance_matrix.py`:
- `@dataclass(frozen=True) Control` (the fields above; `wired_into` a dict).
- `load_matrix(root: Path) -> tuple[Control, ...]` -- read + JSON-parse + schema-validate (raise
  `ValueError` on schema violation, naming the offending control id).
- `enforced_set(controls) -> frozenset[tuple[str, str]]` -- `{(id, posture)}` for the ratchet.
- `POSTURES = ("ABORT", "WARN")` closed enum; `DETECTIONS = ("skill-marker", "test", "ci-job")`.

Seed the registry with the verified deterministic controls (each posture pinned by grep-evidence at
implement time): `prompt-injection` (audit, ABORT), `secret-scan` (4.6.5, ABORT), `data-api-acl`
(4.6.10, ABORT), `doc-integrity` (4.7, ABORT), `badge-currency` (6.5, ABORT), `governance-index`
(4.7.5, ABORT), `gate-chain-completeness` (7.8, ABORT), `prose-test-lint` (audit `--enforce`, ABORT),
`ai-provenance` (detection `test` -> `tests/test_gate_chain_phase52_provenance_still_enforced.py::test_provenance_error_blocks_write_and_blocks_hook`),
`ssdf-tags` (7.4, WARN/emit), `dependency-review` (detection `ci-job` -> `pr-dependency-review.yml`).

### Unit Tests

- `tests/test_compliance_matrix_loader.py`:
  - `test_load_matrix_parses_seed_registry` - `load_matrix(REPO)` returns >=1 `Control` and every
    control's `posture` is in `POSTURES` and `detection` in `DETECTIONS` (asserts on parsed objects).
  - `test_load_matrix_rejects_bad_posture` - a synthetic matrix with `posture: "MAYBE"` raises
    `ValueError` naming the control id (invoke loader on a tmp file, assert the raise + message).
  - `test_enforced_set_shape` - `enforced_set` of a 2-control synthetic returns exactly the
    `{(id, posture)}` pairs (assert set equality).
  - `test_schema_rejects_missing_required_field` - a control missing `enforcing_module` fails
    schema validation with a ValueError (assert raise).

## Phase 2: Conveyance conformance test

### Affected Files

- `tests/test_compliance_conformance.py` (NEW) - the generic verifier (runs in CI pytest).
- `qor/scripts/compliance_conformance.py` (NEW) - pure detection dispatcher (CLI + importable).

### Changes

`compliance_conformance.py`:
- `verify_control(control, root) -> list[str]` -- returns a list of failure reasons (empty == pass),
  dispatching on `control.detection`:
  - `skill-marker`: read the declared `skill` file, extract the declared `step` section; FAIL if the
    `invocation` substring is absent, or if the posture marker disagrees (ABORT control whose step
    carries `|| true`, or WARN control lacking `|| true`). Then for each name in `variants`, read the
    compiled `qor/dist/variants/<v>/.../SKILL.md` for the same skill and FAIL if the `invocation` is
    absent there (conveyance check -- the gate must reach the installed payload).
  - `test`: FAIL if the named test path::name does not exist in `tests/` (parse the file for the
    `def <name>`), so a control claiming test-enforcement cannot point at a vanished test.
  - `ci-job`: FAIL if the named workflow file lacks the job/step reference.
- `verify_all(root) -> dict[str, list[str]]` -- `{control_id: reasons}` for every failing control.
- `main()` -- exits 1 and prints the failing cells when `verify_all` is non-empty (local/manual use).

`test_compliance_conformance.py`:
- `test_every_seeded_control_is_satisfied` - `verify_all(REPO)` is empty; on failure the assertion
  message lists each `control_id -> reasons` (this is the live conformance gate -- a downgraded or
  un-conveyed control reds CI).
- `test_skill_marker_detects_posture_downgrade` - synthetic skill text where an ABORT control's step
  carries `|| true`; `verify_control` returns a non-empty reason naming the downgrade.
- `test_skill_marker_detects_missing_in_variant` - control present in source skill but absent from a
  declared variant's compiled skill -> `verify_control` flags the conveyance gap.
- `test_test_detection_flags_vanished_test` - a `detection: test` control pointing at a non-existent
  test name returns a failure reason.

## Phase 3: Compliance ratchet

### Affected Files

- `tests/test_compliance_ratchet.py` (NEW) - drop/downgrade/waiver/first-intro behavior.
- `qor/scripts/compliance_ratchet.py` (NEW) - pure diff vs the prior release tag.

### Changes

`compliance_ratchet.py`:
- `prior_matrix(root, ref) -> tuple[Control, ...] | None` -- `git show <ref>:qor/compliance/control_matrix.json`;
  return None when the path does not exist at `ref` (first introduction -- nothing to ratchet).
- `regressions(current, prior, waivers) -> list[str]` -- a regression is a control id in
  `prior` whose `(id)` is absent from `current` (dropped) OR whose posture went `ABORT -> WARN`
  (downgraded), UNLESS a `waivers[]` entry names that id with a non-empty `justification` and `issue`.
  Returns human-readable regression strings.
- `check(root, ref) -> list[str]` -- load current + prior, return `regressions(...)`; empty when
  `prior_matrix` is None.
- `main()` -- `--base <tag>` (default: highest `v*` SemVer tag below the current pyproject version);
  exit 1 listing regressions.

`test_compliance_ratchet.py`:
- `test_dropped_control_is_a_regression` - prior has control X, current omits it, no waiver ->
  `regressions` names X (synthetic Control tuples, assert on returned list).
- `test_posture_downgrade_is_a_regression` - X goes ABORT->WARN, no waiver -> flagged.
- `test_waiver_suppresses_regression` - same downgrade with a matching waiver (id+justification+issue)
  -> `regressions` empty.
- `test_first_introduction_has_no_regressions` - `prior_matrix` None -> `check` returns empty.
- `test_added_control_is_not_a_regression` - current has an extra control absent from prior -> empty
  (the ratchet only forbids shrink/downgrade, never growth).

## Definition of Done

### Deliverable: D-matrix -- declarative control registry

- **D1**: every conveyed compliance control is a row in a machine-readable matrix with a declared
  framework, enforcing module, posture, and conveyance target.
- **D2**: `qor/compliance/control_matrix.json` (+ `control_matrix.schema.json`) and
  `qor.scripts.compliance_matrix.load_matrix/enforced_set` (`Control` dataclass, `POSTURES`/`DETECTIONS`).
- **D3**: new doctrine `qor/references/doctrine-compliance-conveyance.md` (the four terms' home);
  glossary entries wired; ledger SESSION SEAL records the registry.
- **D4**: `test_load_matrix_parses_seed_registry` + `test_load_matrix_rejects_bad_posture` assert
  parse + reject behavior.

### Deliverable: D-conformance -- live conveyance verifier

- **D1**: CI fails when any matrix control is missing, posture-downgraded, or absent from a conveyed
  variant.
- **D2**: `qor.scripts.compliance_conformance.verify_control/verify_all`; pytest
  `test_every_seeded_control_is_satisfied` runs in the `ci.yml` matrix.
- **D3**: ledger entry records the conformance gate; doctrine documents the three detection modes.
- **D4**: `test_skill_marker_detects_posture_downgrade` + `test_skill_marker_detects_missing_in_variant`
  assert the downgrade and conveyance-gap detections on synthetic input.

### Deliverable: D-ratchet -- non-regression across releases

- **D1**: a release that drops or downgrades a control fails CI unless an explicit justified waiver
  exists; growth is always allowed.
- **D2**: `qor.scripts.compliance_ratchet.prior_matrix/regressions/check`.
- **D3**: ledger entry records the ratchet; doctrine documents the waiver shape (id+justification+issue).
- **D4**: `test_posture_downgrade_is_a_regression` + `test_waiver_suppresses_regression` +
  `test_first_introduction_has_no_regressions` assert the three core behaviors.

## CI Commands

- `python -m pytest tests/test_compliance_matrix_loader.py tests/test_compliance_conformance.py tests/test_compliance_ratchet.py -q` -- the three new suites.
- `python -m pytest -q` -- full suite green (the conformance + ratchet tests gate every PR).
- `qor-logic scripts compliance_conformance` -- manual conveyance check (exit 1 lists failing cells).
- `qor-logic scripts compliance_ratchet --base v0.104.0` -- manual ratchet vs the prior release.
