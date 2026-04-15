# Plan: Phase 10 — E2E Validation Suite + Gap Audit

**Status**: Active (scope-limited)
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Scope**: Cross-module integration tests + gap discovery during testing + workflow-bundle opportunity scan.

## Open Questions

None. Scope is fixed: tests + findings doc.

## Why this phase

Existing 108 tests are unit-scoped — each module verified in isolation. We have no test that exercises the actual integration: session → gate_chain → shadow_process → qor_platform working together. E2E proves the assembly, not just the parts.

## Track A — E2E test suite

`tests/test_e2e.py`. Each test exercises 3+ modules in a realistic sequence.

### Tests

1. **`test_full_chain_advisory_flow`** — Simulate research → plan → audit. Each phase writes a valid artifact; next phase reads + validates. Verifies session continuity, schema validation, and gate_chain delegation across phases.

2. **`test_override_path_full_cycle`** — Skip the plan phase (no artifact). Audit calls `check_prior_artifact("audit")` → not found → simulate user override → `emit_gate_override` → event lands in shadow log → `check_shadow_threshold` sees the event → severity 1 < threshold 10 (no marker yet). Verifies the entire override pipeline.

3. **`test_capability_shortfall_pipeline`** — Apply `claude-code-solo` profile → `should_run_adversarial_mode()` returns False → `emit_capability_shortfall("codex-plugin")` → event lands → threshold checker counts it (sev 2). Verifies platform → audit-runtime → shadow integration.

4. **`test_threshold_breach_writes_marker_and_remediate_pending`** — Append events totaling sev ≥ 10 → `check_shadow_threshold` writes `.qor/remediate-pending` → marker payload contains aggregated event ids. Verifies the auto-trigger surface for `/qor-remediate`.

5. **`test_aged_high_severity_self_escalation_idempotent_e2e`** — Append sev-3 event 91 days old → first sweep emits aged_high_severity_unremediated (sev 5) → second sweep produces no duplicate. Verifies the idempotence rule end-to-end.

6. **`test_session_continuity_across_modules`** — `session.get_or_create()` → use returned id in `gate_chain.emit_gate_override(session_id=sid)` → use same id when reading `.qor/gates/<sid>/`. Verifies session ID propagates correctly through every module that needs it.

7. **`test_compile_drift_full_cycle`** — Take a fixture skill source, compile, mutate the source, recompile, verify drift detector exits 0 (recompile matched). Verifies compile + check_variant_drift cycle works against real-world content.

8. **`test_collector_subprocess_chain`** — Mocked subprocess: collector invokes per-repo check_shadow_threshold → reads updated log → builds issue body → mocked gh issue create → flip-only per repo. Verifies the cross-repo orchestration end-to-end.

9. **`test_platform_marker_affects_audit_runtime`** — Apply different platform profiles in sequence; `should_run_adversarial_mode()` reflects each correctly; capability_shortfall events carry correct details. Verifies platform marker reads are dynamic, not cached.

## Track B — Gap discovery during testing

While writing tests, log discovered gaps to `docs/phase10-findings.md`:

- Modules that need additional public functions (e.g., a helper to emit shadow events without manual dict construction)
- Cross-module surfaces that lack convenience wrappers
- Documentation/code mismatches noticed during integration
- Missing CLI commands (e.g., is there a way for an operator to manually flip an event addressed=true? `create_shadow_issue.py --flip-only` exists but only with URL)

## Track C — Workflow-bundle opportunity scan

Identify common multi-skill flows that could become bundles:

- **Release cycle** — `qor-validate` → `qor-repo-release` (small bundle, 2 phases)
- **Onboard external codebase** — `qor-research` → `qor-organize` → `qor-audit` → `qor-plan` (medium bundle)
- **Process review cycle** — `qor-shadow-process` (sweep) → `qor-remediate` (act on findings) → `qor-audit` (verify the remediation)
- **Repo scaffold + bootstrap** — `qor-repo-scaffold` → `qor-bootstrap` (small)

For each candidate, document in `docs/phase10-findings.md`:
- Trigger pattern (when do we invoke this chain repeatedly?)
- Phase list
- Recommended checkpoints
- Decomposition need (sub-bundles?)
- Estimated effort to author

## Affected Files

- `tests/test_e2e.py` (new)
- `docs/phase10-findings.md` (new — discovered gaps + bundle proposals)
- `docs/plan-qor-phase10-e2e-validation.md` (this file)

No SKILL.md edits expected unless e2e exposes a critical gap that demands inline fix.

## Constraints

- **No new runtime code** unless a gap demands it (note the gap; defer fix to a future phase)
- **Use existing fixtures** — `tests/fixtures/skill_samples/` (deferred), or build minimal inline fixtures via `tmp_path`
- **Mock subprocess + gh** consistent with existing test patterns
- **Honor token-efficiency doctrine** — tests reference modules by name, not paste source

## Success Criteria

- [ ] 9 e2e tests authored and passing
- [ ] Full suite: 117/117 (108 prior + 9 e2e)
- [ ] `docs/phase10-findings.md` lists discovered gaps + bundle opportunities
- [ ] At least 1 concrete bundle proposal with phase list + checkpoint plan
- [ ] Drift clean; ledger chain intact
- [ ] Committed + pushed

## CI Commands

```bash
python -m pytest tests/test_e2e.py -v
python -m pytest tests/ -v
python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
```
