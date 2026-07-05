# Research Brief: Risk-Tiered Gate Depth (GH #248)

**Date**: 2026-07-04
**Analyst**: The Qor-logic Analyst
**Target**: GH #248 -- short chain for low-risk changes, full ceremony for high-risk (perspective-reset rec 1)
**Scope**: chain machinery, existing risk axes, an external mutation-classification doctrine (M0-M5 classes) reference, design shapes, Governor decisions

---

## Executive Summary

Every change today traverses the six-phase chain (`gate_chain.py:28`) with ~8 effective gate evaluations at the measured ~33% VETO rate (entry #378). The machinery already contains the seams tiering needs: `check_prior_artifact` supports substitutable priors (the Phase 59 ideation precedent, gate_chain.py:102-117), gate skipping has an audited precedent (Phase 75 `gate_skipped_prerequisite_absent` + Phase 59 severity-1 `gate_override` events), and `gate_chain_completeness` validates a hardcoded artifact tuple (`REQUIRED_PHASES`, gate_chain_completeness.py:20) that can defer to a per-plan declaration. Three design shapes were evaluated; the Governor selected **Shape 3 (declared artifact set)** with **guarded audit-skip for L1**: the plan artifact itself declares `required_gate_artifacts`, and only L1-risk, non-release changes touching no security-critical path (qor/capabilities/risk.py routing) may declare the short chain `[plan, implement, substantiate]`, with the skipped audit recorded as a severity-1 shadow event and every substantiate fail-closed gate unchanged.

## Findings

1. **Chain + priors**: `CHAIN = [research, plan, audit, implement, substantiate, validate]` (gate_chain.py:28); `check_prior_artifact` resolves the prior by index (50-99) with the ideation alternative-prior carve-out (102-117) proving substitutable priors are an established pattern.
2. **Completeness**: `REQUIRED_PHASES = (plan, audit, implement, substantiate)` hardcoded (gate_chain_completeness.py:20); `check()` (52-88) validates each artifact per sealed phase >= 52. A short chain fails it today; the seam is reading a declared set from the session's plan.json with the current tuple as default.
3. **Existing axes**: `change_class` (hotfix/feature/breaking) lives in plan prose + artifact payloads and drives semver + release-class gates; `risk_grade` (L1/L2/L3) is enum-ed in audit.schema.json:15 and routed by `qor/capabilities/risk.py:55-79` from file paths (L3: substantiate/ledger_hash/hash_guard; L2: META_LEDGER/implement/dependency manifests; L1 default). Tiering composes these rather than adding a third taxonomy: the DECLARATION is the artifact set; the GUARD is risk routing + change_class.
4. **External mutation-classification doctrine reference** (M0-M5 classes; doctrine file sections 269-335): M0-M5 target classes with default treatments; alignment M0/M1->L1, M2/M3->L2, M4/M5->L3. Adopted as rationale, not as a new field.
5. **Skip precedents**: Phase 75 operator-signaled SKIP + shadow event; Phase 59 advisory-gate override with severity-1 logging. An audit-skip must follow the same discipline: never silent, always evidenced.
6. **Anchors that must move**: chain.md's "implement reads audit.json (must be PASS)" row; delegation-table audit->implement row; gate_chain_completeness tests (tests/test_gate_chain_completeness.py).

## Governor Decisions (recorded 2026-07-04)

- **Shape 3**: `required_gate_artifacts` declared in plan.json; completeness validates the declaration; absent field defaults to the full tuple (all history grandfathered by construction).
- **Audit-skip posture**: short chain `[plan, implement, substantiate]` permitted ONLY when risk routing over the plan's affected files yields L1 AND change_class is hotfix-or-docs-scope (non-release); declaring it emits a severity-1 shadow event; substantiate gates unchanged; anything touching risk.py L2/L3 paths or declaring feature/breaking must carry the full chain (schema-enforceable via if-then on change_class; the risk-routing check is the implement-time guard).

## Recommendations

1. Phase 168 ships: plan.schema.json `required_gate_artifacts` (+ if-then: feature/breaking may not omit audit), a `tier_guard` helper (route_risk over affected_files -> allowed set) invoked at plan-write and at `check_prior_artifact` time for implement (accepting plan.json-PASS-equivalent when audit is legitimately absent), gate_chain_completeness reading the declaration, shadow-event emission on short-chain declaration, chain.md/delegation-table/doc updates via /qor-document, and behavioral tests for every cell (short chain valid; short chain rejected on L2/L3 path; missing field defaults to full; completeness honors declaration; event emitted).
2. Self-application note: Phase 168 itself is a full-chain feature change (touches gate machinery = L3 path) -- the first change the new guard must classify as full-chain.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
