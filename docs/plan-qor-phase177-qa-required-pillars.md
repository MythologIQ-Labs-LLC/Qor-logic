# Plan: Phase 177 - QA evidence required pillars (GH #269)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: (none)

**boundaries**:
- limitations: The production posture is opt-in per call site; nothing in this phase flips any existing caller to production (the seal/close-guard adoption of the strict posture is a deliberate later decision). Pillar EVIDENCE quality is unchanged -- a `pass` still means whatever the producing backend measured.
- non_goals: No third verdict value (PASS/FAIL enum stays closed for existing strict validators); no ac_close_guard changes (the verdict carries the policy outcome through the existing WARN seam); no CLI (qa_evidence is a library).
- exclusions: Wiring `policy="production"` into /qor-substantiate or release gates is follow-on scope, recorded on GH #269 at disposition.

## Open Questions

(none)

## Origin

Research brief docs/research-brief-qa-required-pillars-2026-07-13.md (ledger entry #426, session `2026-07-13T0617-5f93aa`); GH #269.

## Locked Decisions

- **LD-1: the verdict rule is the single change point.**
  `grep -nE 'verdict = ' qor/scripts/qa_evidence.py -> 70`; `build_payload` signature at line 48 (keyword-only extension is additive; all existing callers keep byte-identical output under the adoption default).
- **LD-2: policy is data on the artifact, not a new verdict value.**
  `qor/gates/schema/qa.schema.json` verdict enum `["PASS","FAIL"]` is strict -- a third value breaks existing validators; optional `policy` (`["adoption","production"]`) and `required_pillars` (items from the closed pillar set `regression|security|stability|coverage`, uniqueItems) fields are additive under `additionalProperties: true`. `qa` is REGISTERED (`grep -nE '"qa"' qor/gates/SCHEMA_REGISTRY.json -> 14`); the freeze lint is presence-based -- no registry change.
- **LD-3: production semantics -- a required pillar must be `pass`.**
  Under `policy="production"` with a non-empty `required_pillars`: any required pillar whose status is `skip` OR `fail` (or absent from the payload) -> verdict FAIL; non-required pillars keep skip-visible semantics. Under adoption (default): current rule exactly (`fail` anywhere -> FAIL). `production` with empty/None required set is rejected (`ValueError`) -- a strict posture that requires nothing is a misconfiguration, not a policy.
- **LD-4: consumers need zero changes.**
  `grep -nE 'not PASS' qor/scripts/ac_close_guard.py -> 97` -- the close guard reads the computed verdict; a production FAIL flows through the existing WARN seam. Doctrine gains a posture paragraph in `qor/references/doctrine-verification-closure-integrity.md` (its "skip does not fail the verdict" sentence gains the production-mode qualifier).

## Phase 1: Policy-aware verdict (TDD first)

### Affected Files

- tests/test_qa_evidence.py - new policy test group appended (existing tests untouched -- they lock the adoption default)
- qor/scripts/qa_evidence.py - `build_payload(..., policy="adoption", required_pillars=None)`; verdict rule per LD-3; payload records `policy` + sorted `required_pillars` when production
- qor/gates/schema/qa.schema.json - optional `policy` + `required_pillars` fields per LD-2

### Changes

`build_payload` gains two keyword-only parameters. Verdict block becomes: compute `failed = any(status == "fail")`; if `policy == "production"`: validate `required_pillars` non-empty subset of the pillar set (else `ValueError`), and `verdict = "FAIL" if failed or any(pillars.get(name, {}).get("status") != "pass" for name in required_pillars) else "PASS"`; else current rule. When production, payload gains `"policy": "production"` and `"required_pillars": sorted(required)`; adoption payloads are byte-identical to today (no new keys). Schema: `policy` enum + `required_pillars` array with `enum` items and `uniqueItems: true`, both optional.

### Unit Tests

- tests/test_qa_evidence.py::test_adoption_default_output_unchanged - build_payload with no new kwargs produces a payload with NO policy/required_pillars keys and the current all-skip PASS verdict (byte-compat regression lock)
- tests/test_qa_evidence.py::test_production_required_skip_fails_verdict - policy=production, required_pillars={security}: an all-skip payload yields FAIL (the GH #269 acceptance)
- tests/test_qa_evidence.py::test_production_required_pass_passes - required pillars supplied with status pass (+ others skip) yields PASS; payload records policy and sorted required_pillars
- tests/test_qa_evidence.py::test_production_required_fail_fails - a required pillar with explicit fail yields FAIL (fail dominates under both policies)
- tests/test_qa_evidence.py::test_production_optional_skip_still_passes - required={regression} pass, security/stability/coverage skip: PASS (non-required skips keep skip-visible semantics)
- tests/test_qa_evidence.py::test_production_without_required_set_raises - policy=production with required_pillars None/empty raises ValueError
- tests/test_qa_evidence.py::test_production_payload_validates_against_schema - a production payload validates against qa.schema.json (proves the schema amendment); an adoption payload still validates

## Phase 2: Doctrine

### Affected Files

- qor/references/doctrine-verification-closure-integrity.md - posture paragraph (adoption vs production; when to require pillars)

### Changes

The QA-evidence section's "skip does not fail the verdict" sentence gains the qualifier "under the default adoption policy" plus a short paragraph: production policy semantics per LD-3, the misconfiguration guard, and the follow-on note that seal/release wiring of the strict posture is deliberate later scope.

## Feature Inventory Touches

(empty -- governance evidence tooling; no FEATURE_INDEX row)

## Definition of Done

### Deliverable: production-grade QA verdict policy

- **D1**: A release or compliance consumer can declare required pillars such that skipped security, stability, or coverage evidence CANNOT yield a production-grade PASS, while every existing caller's output stays byte-identical (GH #269).
- **D2**: `build_payload(policy=..., required_pillars=...)` per LD-3 with the ValueError misconfiguration guard; additive schema fields per LD-2.
- **D3**: Ledger entries for plan/audit/implement/seal; doctrine posture paragraph; GH #269 disposition records the follow-on (wiring production into seal/release gates).
- **D4**: `test_production_required_skip_fails_verdict` observes the acceptance behavior; `test_adoption_default_output_unchanged` observes byte-compat; `test_production_payload_validates_against_schema` observes the schema amendment.

## CI Commands

- `python -m pytest tests/test_qa_evidence.py -q` - focused suite (run twice for determinism)
- `python -m pytest -q` - full suite; locks consumers and schema validators
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
