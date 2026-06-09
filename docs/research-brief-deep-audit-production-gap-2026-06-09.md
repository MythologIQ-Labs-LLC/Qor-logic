# Research Brief: Full Production-Gap Red-Team Audit (Recon)

**Date**: 2026-06-09
**Analyst**: The Qor-logic Analyst (6-agent parallel recon + verification round)
**Target**: Whole Qor-logic package at HEAD = main (post Phase 146 seal, v0.107.2)
**Scope**: governance-integrity, security, code-quality/Razor, test-integrity, architecture (Reality=Promise), CLI/SDK/packaging
**Method**: `/qor-deep-audit` Phase 1 (parallel subagent recon) + Phase 3 Round-1 verification of CRITICAL/HIGH governance claims with file:line. Recon-only -- no remediation in this artifact.

---

## Executive Summary

61 raw findings across 6 vectors; deduped to the consolidated matrix below. **No remotely-exploitable security vulnerability** surfaced (no `shell=True`, no `eval`/`exec`/`pickle`/unsafe-`yaml.load`, no hardcoded secrets, no install-time network; the SDK `importlib` runner sources its module list from schema-validated package data). The highest-value finding is a **Promise vs Reality gap in the integrity model**, corroborated by three independent agents: the META_LEDGER chain proves *ordering and linkage* of operator-supplied `content_hash` values but **never recomputes those hashes against the sealed artifacts**, so it is tamper-*evidence over its own chain*, not tamper-*proof over the sealed plans/code*. The one routine that would bind content to artifacts is dead placeholder code. This does not make seals worthless (ordering integrity + the deterministic gate ladder are real), but it is a genuine gap for a framework that *sells* integrity/compliance conveyance downstream.

**Risk grade**: L2 (governance/provenance integrity; no L3 security/financial/rights surface reached). **None of the confirmed findings are remotely exploitable**; the realistic adversary is the repo author bypassing their own discipline, plus undetected post-hoc artifact edits and accidental drift.

### Top 5

1. **GAP-GOV-01/02 (HIGH, CONFIRMED)** -- `content_hash` is an operator-authored field never re-derived from the sealed bytes at verify time (`ledger_hash.verify_post_anchor:480`, `seal_entry_check.py:107`); the only artifact-binding hasher (`calculate-session-seal.py:38-45`) is dead code with a literal `previous_hash = "PREVIOUS_LEDGER_HASH"` placeholder.
2. **GAP-GOV-04 (HIGH, CONFIRMED)** -- `QOR_GATE_PROVENANCE_OPTIONAL=1` (`gate_chain.py:237`) disables the gate-artifact provenance binding entirely, in any process; advertised in the error text.
3. **GAP-ARCH-02 / GAP-CLI-07 (MEDIUM-HIGH, CORROBORATED x2)** -- `compliance enforce --engagement ci|seal` passes vacuously: every ci/seal-tagged control has `runner:null`, so the SDK finds zero runnable controls and returns PASS with no enforcement. The downstream-conveyance promise is unmet for two of five engagements.
4. **GAP-GOV-14 (MEDIUM, CONFIRMED)** -- gate-chain completeness reads the session id from the seal entry's own prose and only checks `is_file()`; author controls both the claimed id and the files.
5. **GAP-CLI-01/03 (HIGH/MEDIUM)** -- no `py.typed` ships (typed public SDK, no marker), and `compliance/*.json` has no packaging-test guard (silent removal breaks installed `compliance enforce` with no failing test).

## Consolidated Gap Matrix

Severity re-graded by the Analyst against the real threat model; "Verdict" = verification status (CONFIRMED / CORROBORATED / PLAUSIBLE / BY-DESIGN).

| ID | Category | Sev | Verdict | file:line | Blocks-GA | Effort |
|---|---|---|---|---|---|---|
| GAP-GOV-01 | content-hash not bound to bytes | HIGH | CONFIRMED | ledger_hash.py:480, seal_entry_check.py:107 | no | M |
| GAP-GOV-02 | dead artifact-hasher (placeholder prev) | HIGH | CONFIRMED | calculate-session-seal.py:38-45 | no | S |
| GAP-GOV-04 | env bypass of provenance | HIGH | CONFIRMED | gate_chain.py:237 | no | S |
| GAP-GOV-14 | existence-only completeness, self-reported sid | MEDIUM | CONFIRMED | gate_chain_completeness.py:44,75 | no | S |
| GAP-GOV-03 | TOCTOU gate-pass vs committed bytes | MEDIUM | PLAUSIBLE | qor-substantiate/SKILL.md:508-626 | no | M |
| GAP-GOV-09/CQ-03 | verify() skips unverifiable-markup entries (returns 0) | MEDIUM | CONFIRMED | ledger_hash.py:354-359 | no | S |
| GAP-GOV-05 | skill-phase provenance is self-asserted string | MEDIUM | CONFIRMED | gate_chain.py:232-249 | no | M |
| GAP-GOV-06/07/08 | post-anchor/reconciliation/grandfather tolerances | LOW | BY-DESIGN (GH #88; harden-candidate) | ledger_hash.py:344,401,227 | no | M |
| GAP-GOV-10 | Phase 75 SKIP is prose-attested | LOW | BY-DESIGN (SG-HalfSealedClaim-A) | qor-substantiate/SKILL.md:54-64 | no | M |
| GAP-GOV-11 | WARN-only gates never block | LOW | BY-DESIGN (V1 posture) | seal-gate-ladder.md; model_pinning_lint.py:132 | no | S |
| GAP-SEC-04/05/07 | session_id path-traversal: validator applied inconsistently | MEDIUM | CONFIRMED | orchestration_override.py:21, cycle_count_escalator.py:36 | no | S |
| GAP-SEC-01 | conformance importlib over consumer-supplied matrix | MEDIUM | CONFIRMED | compliance_conformance.py:135 | no | S |
| GAP-ARCH-02 | ci/seal enforce passes vacuously (runner:null) | MEDIUM | CORROBORATED x2 | enforce.py:62-75; cli_handlers/compliance.py:101 | no | M |
| GAP-CLI-07 | enforce() returns PASS on zero runnable controls | MEDIUM | CORROBORATED x2 | enforce.py:88 | no | S |
| GAP-CLI-01 | no py.typed for typed SDK | HIGH | CONFIRMED (wheel) | qor/ (absent) | no | XS |
| GAP-CLI-03 | compliance/*.json unguarded by packaging test | MEDIUM | CONFIRMED | tests/test_packaging.py:32 | no | XS |
| GAP-CLI-02 | FX017 cites wrong test file | MEDIUM | CONFIRMED | docs/FEATURE_INDEX.md:28 | no | XS |
| GAP-ARCH-04 | FX013 line-anchor points into fn body | LOW | CONFIRMED | docs/FEATURE_INDEX.md:24 | no | XS |
| GAP-ARCH-01 | orphaned lint (no caller) | MEDIUM | CONFIRMED | pipeline_inversion_lint.py:1 | no | S |
| GAP-ARCH-03/05 | verify-ledger/governance-health doc-vs-arg drift | LOW | CONFIRMED | README.md:311,312 | no | XS |
| GAP-ARCH-06 | drift check excludes manifest.json content | LOW | CONFIRMED (documented) | check_variant_drift.py:21-35 | no | S |
| GAP-TEST-01/02 | presence-only doctrine tests (no unit invoked) | MEDIUM | CONFIRMED | test_doctrine_prompt_compilation_present.py:20, test_doctrine_dependency_admission.py:19 | no | S |
| GAP-TEST-05/06/07/08 | conditional skips no-op in degraded CI | MEDIUM | CONFIRMED | test_attribution_tiered_usage.py:150, test_compliance_ratchet.py:61, test_changelog_tag_coverage.py:39, test_sast_scan.py:67 | no | M |
| GAP-TEST-10 | cwd-coupled relative paths (error off-root) | LOW | CONFIRMED | test_codeowners_doctrine.py:6 | no | XS |
| GAP-CQ-02 | ledger_hash.verify() ~118 lines, tolerance branches | MEDIUM | CONFIRMED | ledger_hash.py:300-417 | no | M |
| GAP-CQ-04 | entry-heading regex duplicated in 8+ modules | MEDIUM | CONFIRMED | ledger_hash.py:132 (+7) | no | M |
| GAP-CQ-05/06/07 | Razor: run_lint/analyze/probe over ~40 lines | LOW | CONFIRMED | dependency_admission_lint.py:116, data_api_acl_lint.py:138 | no | S |

Positive confirmations (NOT gaps): reliability gates + compliance SDK are genuinely behaviorally tested (not import-only); all 17 CLI commands have handlers + passing behavioral tests (FX 17/17 *substance* holds despite the FX017 citation bug); all 4 control_matrix runner targets export `main` and are importable; badge counts match filesystem; YAML is uniformly `safe_load` (lint-enforced); subprocess is uniformly list-form argv.

## Blueprint Alignment

| Promise | Reality | Status |
|---|---|---|
| "Merkle seal" / hash-chained tamper-evident ledger | Chain binds ordering + recorded hashes, NOT hashes-to-artifacts; dead binder script | DRIFT (the headline) |
| compliance enforce runs the controls wired to an engagement | ci/seal engagements have only runner:null -> vacuous PASS | DRIFT |
| FEATURE_INDEX cites the test that proves each feature | FX017 mis-cites; FX013 line-anchor into fn body | DRIFT (citations; coverage substance holds) |
| Typed downstream SDK (qor.sdk) | No py.typed marker ships | DRIFT |
| Conveyance is non-regressable to consumers | compliance/*.json has no packaging-test guard | DRIFT (silent-removal risk) |
| Deterministic gate ladder enforces at seal | Real for ABORT gates; several gates are WARN-only / prose-attested SKIP / env-bypassable | PARTIAL |

## Recommendations (Sprint Plan -- for operator approval at checkpoint; NOT yet executed)

Ordered GA-relevance -> severity -> effort. Each is TDD (failing test first).

- **Sprint A -- integrity binding (the headline cluster)**: (1) add a seal-time gate that recomputes the latest entry's `content_hash` from its declared source artifact(s) and FAILs on mismatch (closes GOV-01); decide the canonical artifact set (plan? plan+audit+touched-src?) -- this is a design choice. (2) Delete or fully wire `calculate-session-seal.py` (GOV-02). (3) Gate `QOR_GATE_PROVENANCE_OPTIONAL` behind an actual pytest-context detector, not a bare env (GOV-04). (4) Make gate-chain completeness validate artifact provenance/schema, not just `is_file()` (GOV-14).
- **Sprint B -- conveyance correctness**: (5) make `enforce()` return a non-PASS / explicit "no-op" verdict when an engagement has zero runnable controls, or give ci/seal real runners (ARCH-02/CLI-07). (6) add a packaging-test guard for `compliance/*.json` (CLI-03). (7) ship `py.typed` (CLI-01).
- **Sprint C -- harden documented tolerances + hygiene**: apply the existing session-id validator at every path-build site (SEC-04/05/07); convert the presence-only doctrine tests to behavioral or strip-and-fail (TEST-01/02); make the conditional CI skips fail-or-required (TEST-05/06/07/08); fix FX017/FX013 citations (CLI-02/ARCH-04); remove/­wire the orphaned lint (ARCH-01); centralize the entry-heading regex (CQ-04); decompose `ledger_hash.verify()` with tolerance-branch tests (CQ-02).

The BY-DESIGN tolerances (GOV-06/07/08/10/11) are deliberately deferred V1 posture; they belong in a doctrine-level "V2 enforcement" decision, not a defect sprint.

## Updated Knowledge

Candidate Shadow Genome entry: **SG-UnboundContentHash-A** -- a hash-chained ledger that never re-derives `content_hash` from the artifacts it claims to seal provides ordering integrity but not artifact tamper-detection; the binding must be an enforced seal-time recomputation, not an authoring convention.

---

_Recon complete. Findings are advisory -- the remediation sprint plan above is NOT executed; it awaits the operator's after-recon checkpoint decision (continue / scope-down / stop)._
