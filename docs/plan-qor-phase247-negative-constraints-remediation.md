# Plan: Close the Phase 240 independent-audit findings shipped to main (remediation)

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: META_LEDGER entry #642 post-merge re-VETO by the Phase 240 independent reviewer

**boundaries**:
- limitations: remediates the five confirmed findings only; no new capability.
- non_goals: does not reopen the Phase 240 architecture (execution-context contract unchanged); does not renumber or rewrite sealed ledger entries.
- exclusions: V-3 (qor-plan Step 0.3 prose) was already fixed pre-merge in the Phase 240 amendment commit; V-7's process failure is recorded in the ledger amendment, not re-litigated in code.

## Open Questions

None.

## Locked Decisions

**LD-1 (V-1): The fabrication-protection binding predicate is unconditional.** `qor/references/doctrine-negative-constraints.md` no longer keys NR-001/NR-002 applicability on the retired `min_model_capability` field: the rules bind unconditionally for the declared fabrication-risk skill set (`qor-audit`, `qor-plan`, `qor-substantiate`) independent of model identity, host, tier, or provider, per the Phase 240 execution-context delta's own requirement. The stale "pin `min_model_capability`" prose is corrected. Verified: `grep -c "min_model_capability" qor/references/doctrine-negative-constraints.md` -> only the historical-retirement mention remains.

**LD-2 (V-2): The compiled preamble claims only what is true.** `qor/scripts/dist_compile.py`'s injected block is retitled "Negative Constraints (Binding on Every Execution)" and states the fabrication-risk rationale without asserting a declaration that no longer exists or a tier condition; all six host variants recompiled. Verified: `grep -c "min_model_capability" qor/dist/variants/codex/skills/qor-audit/SKILL.md` -> 0.

**LD-3 (V-4/V-5): Fixture tests drive the shared detectors.** The retired-field detector flags EITHER field alone; the synthetic negative/positive fixtures call the same `_skills_with_pinning_keys` / `_plan_skill_invokes_lint` helpers the live-corpus test uses, so they can actually fail.

**LD-4 (V-6): The real seam is tested unstubbed.** `execution_context.inspect_skill` is driven end to end against the live qor-audit contract with a controlled `ExecutionContext` (no monkeypatching), plus the unstubbed no-contract failure path.

## Phase 1: Remediation (test-first where a guard was missing)

### Affected Files

- `tests/test_qor_plan_skill_invokes_model_pinning_lint.py` - rewritten per LD-3.
- `tests/test_qor_audit_execution_context.py` - two real-seam tests added per LD-4.
- `qor/references/doctrine-negative-constraints.md` - LD-1.
- `qor/scripts/dist_compile.py` - LD-2.
- `qor/dist/manifest.json`, `qor/dist/variants/**` - recompiled.

## Definition of Done

### Deliverable: closed findings

- **D1**: Every confirmed finding from the Phase 240 independent reviewer's post-merge re-VETO is closed or explicitly dispositioned, and the ledger records both the reviewer race and entry #642's over-claimed assertions.
- **D2**: The four source surfaces above.
- **D3**: Tribunal iteration 1 records the reviewer's re-VETO; iteration 2 PASS only after the SAME reviewer re-verifies the branch; seal + amendment entries chained.
- **D4**: Focused suites 9/9 (4+5); full suite green twice.

## CI Commands

- `python -m pytest tests/test_qor_plan_skill_invokes_model_pinning_lint.py tests/test_qor_audit_execution_context.py -q`
- `python -m qor.scripts.publication_boundary_lint`
- `python -m pytest tests/ -q`

**ci_commands**:
- `python -m pytest tests/test_qor_plan_skill_invokes_model_pinning_lint.py tests/test_qor_audit_execution_context.py -q`
- `python -m qor.scripts.publication_boundary_lint`
- `python -m pytest tests/ -q`

## Governance note

The Phase 240 promotion merged on a replacement reviewer's narrower PASS while the original reviewer's full VETO and post-seal re-confirmation were still in flight - a messaging race, recorded here as a process failure rather than concealed. This phase closes the confirmed findings on main and corrects the record: the sealed entry #642 report over-claimed that the Phase 240 tests exercised runtime behavior (V-5/V-6 show two fixture tests could not fail and three stubbed the seam) and that the live corpus obeyed the new governance (V-1's doctrine predicate was unsatisfiable). The verdict-generating harness was bounded and did run its declared checks; the defect is that its report asserted facts those checks structurally could not observe.
