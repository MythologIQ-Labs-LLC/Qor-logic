# AUDIT REPORT -- Phase 157: hash_guard.hash_file CRLF-invariant seal-text option

**Verdict**: PASS
**Risk Grade**: L1 (opt-in hardening on a seal-relevant hasher; default path byte-exact and unchanged)
**Mode**: solo (audit_risk_score option_b_required=false)
**Target**: docs/plan-qor-phase157-hash-guard-crlf-invariance.md
**Session**: 2026-06-10T0000-hashcrlf157

## Automated gate ladder

| Gate | Result |
|---|---|
| plan_iteration_status_lint | rc=0 |
| prompt_injection_canaries | rc=0 |
| plan_test_lint / plan_grep_lint | rc=0 |
| plan_text_consistency_lint | rc=0 |
| ci_coverage_lint | rc=0 (WARN-only; flagged commands are pre-existing CI steps unrelated to this plan) |
| plan_feature_tdd_lint | rc=0 |
| audit_risk_score | option_b_required=false |

## Adversarial passes

- **Integrity (the point)** -- PASS. Phase 156 LF-normalized `ledger_hash.content_hash`; `hash_guard.hash_file` is the OTHER seal-relevant file hasher (cited in `/qor-substantiate` Step 6.8 Preparation, verified by `test_substantiate_hash_integrity_step.py::test_hash_gate_preparation_names_canonical_helpers`) and still hashes raw bytes (hash_guard.py:35 `read_bytes()` -> `sha256(raw)`). A digest it produces over a text seal artifact would drift on git autocrlf exactly as content_hash did pre-156. The plan adds an OPT-IN `normalize_newlines` flag rather than an unconditional change, correctly preserving byte-exactness for the documented general-purpose / binary use (`test_hash_file_returns_64_lower_hex_digest` hashes a `.bin` fixture).
- **Scope honesty (devil's advocate)** -- PASS. The plan does not overclaim: there are no current seal-text callers of `hash_file` (the live seal records `content_hash`, already fixed). This is preventive hardening + Step-6.8 guidance, and the plan states that plainly rather than dressing it as a live-binding fix. Not a half-measure: it closes the "helper cannot produce a CRLF-invariant digest" capability gap and documents when to use it; `intent_lock._hash_file` is correctly excluded (intra-checkout, no git round-trip).
- **No-regression** -- PASS. `normalize_newlines` defaults `False`, so every existing call is byte-identical and the missing-path `FileNotFoundError` still raises from `read_bytes()`. `byte_count` is computed over the bytes actually hashed under either mode, keeping the dataclass internally consistent.
- **Test Functionality** -- PASS. The three new tests invoke `hash_file` and assert digest EQUALITY across CRLF/LF under the flag, digest INEQUALITY at the default, and `byte_count` == hashed length -- all behavioral, none presence-only.
- **Razor / Dependency / Security** -- PASS. One keyword-only param + one `replace`/branch line; stdlib only; no auth/secret/deserialization surface (OWASP A08 N/A).
- **Skill-budget discipline** -- PASS. The plan deliberately routes new guidance to `qor/references/seal-gate-ladder.md` and leaves `qor-substantiate/SKILL.md` untouched (9 bytes under the 40 KB EXCEEDED budget), honoring the progressive-disclosure doctrine; the Step 6.8 self-test's cited `hash_guard.hash_file` token is unchanged.
- **Ghost UI / Live-Progress / Filter-Stage / Orphan** -- N/A.

## Scope note

Closes the GAP-GOV-03 follow-on fragility class for the second seal-relevant hasher. After this, Sprint A has only GAP-GOV-05 (non-forgeable provenance) remaining.

## Next action

PASS -> `/qor-implement` -> `/qor-substantiate`.
