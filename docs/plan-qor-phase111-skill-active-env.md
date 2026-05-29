# Plan: Phase 111 - skill_active env-var leakage fix (#138)

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Fixes the leakage at the qor-logic layer (Layer 1 context manager + Layer 2 authoritative reporter + Layer 3 doc). It cannot change a closed-source harness status-line that reads `$QOR_SKILL_ACTIVE` directly; Layer 2 gives such a status-line a correct source to consume.
- non_goals: No change to the provenance-binding contract itself (QOR_SKILL_ACTIVE must still match the phase); only how the env var is set/cleared.
- exclusions: No edit to every skill SKILL.md execution block in this phase (Layer 3 is a single doctrine note; the broad shell-prefix-deprecation sweep is deferred).

## Open Questions

None. Issue #138 specifies the three-layer fix with a context-manager reference implementation and a backward-compatibility contract.

## Context

The inline shell-prefix `QOR_SKILL_ACTIVE=plan python ...` is a POSIX pattern; on Windows/Git Bash it can leak to the parent shell and persist, so a status-line reading `$QOR_SKILL_ACTIVE` shows a stale phase. The fix replaces caller-set shell env with a Python context manager that scripts self-manage, and adds an authoritative gate-artifact-mtime reporter as a non-leaking phase source.

## Feature Inventory Touches

Empty. Governance tooling + doctrine only; no `src/` user-touchable product feature surface.
`feature_inventory_touches`: `[]`.

## Phase 1: skill_active context manager + write_gate_artifact skill param

### Affected Files

- `tests/test_skill_active_env.py` - NEW. Behavioral tests: env unset after the call when previously unset; restored to prior value when preset; gate write succeeds without a shell prefix.
- `qor/scripts/gate_chain.py` - AMENDED. Add `skill_active(skill_name)` context manager; add optional `skill: str | None = None` to `write_gate_artifact` that wraps the provenance check + write in `skill_active(skill)` so callers need no shell prefix. Backward compatible: when `skill` is None, behavior is unchanged (reads ambient env).

### Changes

```python
@contextlib.contextmanager
def skill_active(skill_name: str):
    prev = os.environ.get("QOR_SKILL_ACTIVE")
    os.environ["QOR_SKILL_ACTIVE"] = skill_name
    try:
        yield
    finally:
        if prev is None:
            os.environ.pop("QOR_SKILL_ACTIVE", None)
        else:
            os.environ["QOR_SKILL_ACTIVE"] = prev
```

`write_gate_artifact(..., skill=None)`: when `skill` is provided, run the provenance check + write inside `with skill_active(skill):`. The existing ambient-env path is preserved for `skill=None`.

### Unit Tests

- `tests/test_skill_active_env.py::test_env_unset_after_call_when_previously_unset` - with `QOR_SKILL_ACTIVE` unset and `QOR_GATE_PROVENANCE_OPTIONAL` cleared, `write_gate_artifact(phase, payload, skill=phase)` writes the artifact AND leaves `QOR_SKILL_ACTIVE` unset afterward (invokes the unit, asserts the post-call env + that the file exists).
- `tests/test_skill_active_env.py::test_env_restored_to_prior_value` - with `QOR_SKILL_ACTIVE='outer'` preset, `skill_active('inner')` yields `'inner'` inside and restores `'outer'` after.
- `tests/test_skill_active_env.py::test_skill_param_avoids_shell_prefix_provenance_error` - `write_gate_artifact(phase, payload, skill=phase)` succeeds with no ambient env (no ProvenanceError), proving the caller no longer needs the shell prefix.

## Phase 2: authoritative active-phase reporter (Layer 2)

### Affected Files

- `tests/test_active_phase_reporter.py` - NEW. Behavioral tests for newest-gate-mtime phase resolution.
- `qor/scripts/active_phase.py` - NEW. `latest_gate_phase(session_id, repo_root) -> str | None` returns the `phase` field of the newest-mtime `.qor/gates/<sid>/*.json`; CLI `python -m qor.scripts.active_phase --repo-root . [--session <sid>]` prints the authoritative phase.

### Changes

Read `.qor/gates/<session_id>/*.json` (excluding `audit_history.jsonl`), pick the newest mtime, return its `phase`. None when the dir is empty/absent. CLI prints the phase or `none`.

### Unit Tests

- `tests/test_active_phase_reporter.py::test_returns_phase_of_newest_gate_artifact` - writes `plan.json` then a later-mtime `audit.json`; asserts the reporter returns `audit` (invokes the unit, asserts on the returned phase — not file presence).
- `tests/test_active_phase_reporter.py::test_returns_none_for_empty_session` - empty/absent gate dir returns None.

## Phase 3: env-management pattern doctrine note (Layer 3)

### Affected Files

- `qor/references/doctrine-prompt-resilience.md` - AMENDED. Add a short "Skill-active env management" note: scripts self-manage `QOR_SKILL_ACTIVE` via `gate_chain.skill_active` (or the `skill=` param) rather than relying on a leak-prone inline shell prefix; status surfaces read the authoritative `active_phase` reporter, not the ambient env var.

### Unit Tests

- `tests/test_skill_active_env.py::test_doctrine_documents_env_management` - invokes a parser over the doctrine; asserts it names `skill_active` and the authoritative-reporter guidance. (Co-located in the Phase 1 test module.)

## Definition of Done

### Deliverable D-111.1: non-leaking skill-active env management
- **D1**: Scripts set/clear `QOR_SKILL_ACTIVE` via a context manager that restores prior state; no reliance on a leak-prone shell prefix.
- **D2**: `gate_chain.skill_active` + `write_gate_artifact(..., skill=)`; backward compatible when `skill=None`.
- **D3**: Doctrine documents the pattern.
- **D4**: `tests/test_skill_active_env.py` passes (unset-after, restore, no-prefix-needed, doctrine-documents).

### Deliverable D-111.2: authoritative active-phase reporter
- **D1**: A non-leaking source reports the true active phase from newest gate-artifact mtime.
- **D2**: `qor/scripts/active_phase.py` with `latest_gate_phase` + CLI.
- **D3**: Layer-2 source documented in the doctrine note.
- **D4**: `tests/test_active_phase_reporter.py` passes.

## CI Commands

- `python -m pytest tests/test_skill_active_env.py -q` - context manager + doctrine note.
- `python -m pytest tests/test_active_phase_reporter.py -q` - phase reporter.
- `python -m pytest tests/test_gate_chain_provenance.py tests/test_gate_chain_phase52_provenance_still_enforced.py -q` - provenance-binding regression.
- `python -m pytest tests/ -q` - full regression.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase111-skill-active-env.md` - plan-internal consistency.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase111-skill-active-env.md` - Definition of Done declaration check.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - ledger chain integrity.

## CI Coverage Exemptions

- `test_packaging_install` - packaging integration smoke; orthogonal.
- `gate_chain_completeness` - sealed-phase chain audit; runs every PR.
- `dependency_admission_lint` - dependency cooling-period check; no dependency changes here.
- `check_variant_drift` - no source-skill prompt changes in this phase; variants unaffected.
