# Plan: Phase 169 - Evidence reconstruction over ceremony artifacts (GH #251)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: (none)

**boundaries**:
- limitations: The bundle RECONSTRUCTS -- it writes nothing per phase and never fabricates a missing signal (absent signals are named in `completeness.missing`). Git-derived signals (seal commit/tag) are best-effort local lookups; the bundle never touches the network. The freeze lint is WARN-only in V1 (audit Step 0.6 `|| true`); the WARN->FAIL flip is deferred.
- non_goals: No markdown/csv formatters (JSON only, status_json final-line contract); no changes to any existing gate artifact or schema semantics; no retroactive registry enforcement (the baseline IS the current schema directory).
- exclusions: doctrine rule via /qor-document at seal; no glossary terms.

## Open Questions

(none)

## Origin

Research brief docs/research-brief-evidence-reconstruction-2026-07-04.md (ledger entry #398, session `2026-07-04T1612-9ee76f`); GH #251 (perspective-reset rec 5). Posture source: an external agent-governance toolkit's ADR 0018 (reconstructible decision context; partial reconstruction explicitly surfaced).

## Locked Decisions

- **LD-1: join machinery exists and is reused, not duplicated.**
  `grep -nE 'def _extract_seal_sessions' qor/reliability/gate_chain_completeness.py -> 34` (phase->session map from the ledger); `grep -nE 'def verify_sidecar' qor/scripts/gate_provenance.py -> 127`; `grep -nE 'def (record_path|verify)' qor/reliability/intent_lock.py -> record at .qor/intent-lock/<sid>.json (66-139)`; shadow events filter on the `session_id` field (shadow_process.read_all_events).
- **LD-2: output contract is the Phase 165 status_json shape.**
  Human lines then exactly ONE JSON object as the final stdout line; `schema_version: '1'`; exit 0 iff the query resolves to a known session (completeness may be partial -- reported, not failed).
- **LD-3: assembler precedent.**
  `grep -nE 'def do_ai_provenance' qor/cli_handlers/compliance.py -> 55` walks `.qor/gates/<sid>/` per phase -- the per-signal collector shape; evidence_bundle generalizes it without touching compliance.py.
- **LD-4: freeze-lint model is Phase 166's corpus lint.**
  `grep -nE 'def (parse_entries|entry_cites_enforcer|main)' qor/scripts/sg_closure_lint.py -> 34,45,49`; the freeze lint compares `qor/gates/schema/*.schema.json` against `qor/gates/SCHEMA_REGISTRY.json` (new; baselined from today's directory) and flags unregistered schemas lacking a plan-declared justification.
- **LD-5: plan schema gains one optional field.**
  `new_ceremony_artifacts: [{name, justification >= 100 chars}]` -- additive, mirrors the Phase 168 additions; absent field valid (no new schema == nothing to declare).
- **LD-6: generic-runner invocation; no cli.py change.**
  `qor-logic scripts evidence_bundle --session <sid>` / `--phase <N>` and `qor-logic scripts gate_schema_freeze_lint` (Phase 164/165 precedent). Tier-honoring: the bundle reports gate artifacts per the session's declared set via `tier_guard.declared_artifacts` (Phase 168) so a legal short-chain session shows audit as not-required rather than missing.

## Phase 1: Evidence bundle + freeze lint (TDD first)

### Affected Files

- tests/test_evidence_bundle.py - NEW; behavioral tests for join resolution, per-signal collection, completeness reporting, and the final-line JSON contract
- tests/test_gate_schema_freeze_lint.py - NEW; behavioral tests for registry comparison and justification resolution
- qor/scripts/evidence_bundle.py - NEW; resolvers + eight signal collectors + assembler + main
- qor/scripts/gate_schema_freeze_lint.py - NEW; registry-vs-directory lint
- qor/gates/SCHEMA_REGISTRY.json - NEW; baseline of the current schema inventory
- qor/gates/schema/plan.schema.json - optional `new_ceremony_artifacts` field (LD-5)
- qor/skills/governance/qor-audit/SKILL.md - Step 0.6 ladder gains `qor-logic scripts gate_schema_freeze_lint || true`

### Changes

`evidence_bundle.py` (<240 lines, stdlib + in-repo reuse): `resolve_query(ledger_text, session=None, phase=None) -> (phase_num, sid) | None` via `_extract_seal_sessions`; eight collector functions each returning `{found, ...detail, errors}` and NEVER raising (exceptions recorded in errors); `assemble(repo_root, sid, phase_num) -> dict` with `signals` + `completeness: {total, found, missing: [names]}`; `main(argv)` with `--session`/`--phase` (exactly one), `--repo-root`; human summary lines then the final-line JSON; exit 0 on resolved query, 1 on unresolvable.

`gate_schema_freeze_lint.py` (<90 lines): `registered(registry_path) -> set`; `present(schema_dir) -> set`; unregistered set minus the current session's plan-declared `new_ceremony_artifacts` names -> WARN lines + summary; exit 1 iff findings (ladder wraps `|| true`).

### Unit Tests

- tests/test_evidence_bundle.py::test_resolve_query_by_phase_and_session - synthetic ledger: --phase resolves to the sealed session; --session resolves to its phase; unknown returns None
- tests/test_evidence_bundle.py::test_collectors_report_found_and_detail - synthetic session dir (artifacts + sidecars + audit_history + intent-lock + shadow log): each collector returns found=true with the documented detail keys
- tests/test_evidence_bundle.py::test_completeness_names_missing_signals - session with only plan.json + ledger entry: missing[] names exactly the absent signals; nothing fabricated; collectors never raise
- tests/test_evidence_bundle.py::test_short_chain_session_not_penalized - a Phase 168 legal short-chain session reports audit as not-required (declared set honored), not missing
- tests/test_evidence_bundle.py::test_main_final_line_json_and_exit_codes - main() prints parseable final-line JSON, exit 0 on resolved query, exit 1 on unknown phase
- tests/test_gate_schema_freeze_lint.py::test_lint_flags_only_unregistered_undeclared - tmp schema dir + registry: registered schema passes; unregistered+undeclared flagged; unregistered-but-plan-declared passes; exit codes 0/1
- tests/test_gate_schema_freeze_lint.py::test_live_registry_matches_directory - the shipped SCHEMA_REGISTRY.json covers every schema currently in qor/gates/schema/ (baseline integrity; fails if a schema lands without registration)

## Feature Inventory Touches

(empty -- governance tooling only; no user-touchable `src/` feature)

## Definition of Done

### Deliverable: evidence bundle

- **D1**: One command reconstructs a sealed phase's full evidence from already-recorded signals with explicit partial-reconstruction surfacing (GH #251a; ADR-0018 posture).
- **D2**: `evidence_bundle.py` <=240 lines, stdlib + reuse; final-line JSON; collectors never raise.
- **D3**: GH #251 closes with the invocation documented; doctrine artifact-freeze rule via /qor-document.
- **D4**: `test_completeness_names_missing_signals` and `test_main_final_line_json_and_exit_codes` observe the surfacing + contract; `test_short_chain_session_not_penalized` observes Phase 168 interop.

### Deliverable: artifact freeze rule

- **D1**: A net-new ceremony artifact schema cannot land silently -- it is either registered, or plan-justified, or flagged at every audit (GH #251b).
- **D2**: `gate_schema_freeze_lint.py` <90 lines; SCHEMA_REGISTRY.json baseline; plan schema optional justification field.
- **D3**: Wired WARN-only into the audit Step 0.6 ladder; WARN->FAIL flip deferred and recorded.
- **D4**: `test_lint_flags_only_unregistered_undeclared` observes all four cells; `test_live_registry_matches_directory` locks the baseline.

## CI Commands

- `python -m pytest tests/test_evidence_bundle.py tests/test_gate_schema_freeze_lint.py -q` -- new-test determinism (run twice)
- `python -m pytest -q` -- full suite regression
- `python -m qor.scripts.evidence_bundle --phase 168 --repo-root .` -- live self-application (reconstruct the previous seal)
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase169-evidence-reconstruction.md` -- plan-text consistency
