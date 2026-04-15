# AUDIT REPORT — plan-qor-phase12-v2.md

**Tribunal Date**: 2026-04-15
**Target**: `docs/plan-qor-phase12-v2.md`
**Risk Grade**: L1 (precision defects + 1 ironic complect)
**Auditor**: The QorLogic Judge

---

## VERDICT: **VETO**

---

### Executive Summary

Plan v2 addresses all 11 V-* items from v1 audit, but introduces 5 new defects — most consequential: a test-count arithmetic error and a complect-named test that reproduces the exact V-4 defect v2 was meant to fix. Plan substantively sound; remediation is mechanical.

### Audit Results

#### Security/Ghost UI/Razor/Macro/Orphan Passes
**Result**: PASS.

#### Dependency Pass
**Result**: PASS — pyyaml decision committed to "regex only" (V-2 closure verified).

### Violations Found

| ID | Category | Location | Description |
|---|---|---|---|
| V-A | Math error | plan §Success Criteria line "Full suite 184/184 passing (163 prior + 7 workflow + 1 V-10 + 4 V-7 + 9 unchanged ledger tests already running)" | Verified `pytest tests/` returns **178**, not 163. The existing `tests/test_ledger_hash.py` (15 tests, uncommitted) IS being discovered. Correct math: 178 prior + 7 (Track A workflow) + 1 (V-10 parser robustness) + 4 (V-7 gate_chain) = **190**. Plan asserts 184 with mystery "9 unchanged ledger tests" — the ledger file has 15 tests, not 9. Plan arithmetic broken; final count wrong by 6. |
| V-B | Ironic complect | plan §Track B.1 V-10 line "add `test_verify_handles_malformed_entry_header` — fake ledger with non-monotonic entry numbers + entries missing required hash markers + entries with malformed numeric IDs" | Single test name combines THREE distinct conditions. This is exactly the V-4 defect (combined-assertion test name) that v2 was meant to fix. Reproduces in the same plan. Split into `test_verify_handles_non_monotonic_entry_numbers`, `test_verify_handles_missing_hash_markers`, `test_verify_handles_malformed_numeric_ids`. |
| V-C | Doctrine wording broader than rule | plan §Track A.1 rule 4 first sentence "Aggressive caching mandatory: workflows installing Python deps MUST use ..." vs the narrowed scope on the next line "rule applies only to workflows that explicitly use `setup-python` action" | Two adjacent sentences disagree on scope. Reader sees the first sentence's "MUST" + "Python deps" as universal; only the second sentence narrows. A doctrine doc cannot have its rule and its scope-restriction in tension. Rewrite as one sentence: "Workflows that explicitly use `actions/setup-python@` MUST also declare the `cache:` parameter (or use `actions/cache` for explicit pip cache). Workflows using uv/poetry/pdm/Docker images choose their own caching mechanism." |
| V-D | Test coverage gap | plan §Track B.2 lists 4 tests; none covers the `session_id` argument explicit case | `write_gate_artifact(session_id=...)` is the dual path to `session_id=None`. Tests cover the None path (`test_write_gate_artifact_uses_session_get_or_create`); explicit-session-id path is uncovered. Add `test_write_gate_artifact_respects_explicit_session_id`. |
| V-E | Missing verification step | plan §Track B.1 V-3 says "rename + update docstring" with no instruction to verify no callers reference the old name | After rename, must `grep -r "test_write_manifest_atomic_write" tests/` to confirm zero callers. Add as success criterion. |
| V-F | Ratification incomplete | plan header line "post-dialogue with user Q1=(a), Q2=(a), Q3=(i) decisions ratified" | Only cites the FIRST dialogue round. The SECOND round (Q-A=(a), Q-B=(a), Q-C=(b)) is incorporated in body but not in the explicit ratification line. Per V-1 doctrine, plan header must declare ALL ratified decisions. Update to "Q1=(a), Q2=(a), Q3=(i), Q-A=(a), Q-B=(a), Q-C=(b)". |
| V-G | Cosmetic | plan §Affected Files line "Track B (1 modified, 1 modified)" | Typo: should be "(2 modified)". |

### Required Remediation

1. **V-A**: Recalc and update plan §Success Criteria. Current pre-Phase-12 state is `pytest tests/` = 178. After Phase 12: 178 + 7 + 1 + 4 = **190**. Plan must say 190.
2. **V-B**: Split combined-condition V-10 test into 3 tests, each named for one condition.
3. **V-C**: Rewrite doctrine rule 4 as one sentence whose scope matches its assertion.
4. **V-D**: Add `test_write_gate_artifact_respects_explicit_session_id` to Track B.2 (5 tests, not 4).
5. **V-E**: Add to plan §Success Criteria: "[ ] `grep -r test_write_manifest_atomic_write tests/` returns zero matches after V-3 rename".
6. **V-F**: Update header ratification line to include all six decisions (Q1, Q2, Q3, Q-A, Q-B, Q-C).
7. **V-G**: Fix typo "1 modified, 1 modified" → "2 modified".

### Verdict Hash

(computed at ledger entry — see Entry #23)

---
_This verdict is binding._
