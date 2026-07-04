# Plan: Phase 168 - Risk-tiered gate depth (GH #248)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: (none)

**boundaries**:
- limitations: The short chain omits ONLY the audit phase (`[plan, implement, substantiate]`); research/ideation remain advisory as today; substantiate's fail-closed gate ladder is unchanged for every tier. The guard consumes the EXISTING axes (risk routing over affected files + change_class) -- no new taxonomy field.
- non_goals: No change to audit itself; no auto-classification of historical phases (absent field == full chain, grandfathering all 393 entries by construction); no CI workflow change (completeness already runs in CI and reads the new declaration transparently).
- exclusions: chain.md / delegation-table / doctrine updates via /qor-document at seal; PAMA M-classes cited as rationale only.

## Open Questions

(none -- both Governor decisions recorded in research entry #394: Shape 3 declared artifact set; audit-skip only for L1 + non-release with severity-1 shadow event)

## Origin

Research brief docs/research-brief-risk-tiered-gate-depth-2026-07-04.md (ledger entry #394, session `2026-07-04T1541-18963c`); GH #248 (perspective-reset rec 1). Evidence: ~8 effective gate evaluations per change at the measured VETO rate (entry #378).

## Locked Decisions

- **LD-1: prior-resolution seam.**
  `grep -nE 'def (prior_phase|check_prior_artifact|_check_ideation_predecessor)' qor/scripts/gate_chain.py -> 50, 59, 102`; the Phase 59 ideation carve-out (102-117) is the exact pattern the implement-prior carve-out mirrors: when `current_phase == "implement"` and `audit.json` is absent, a plan.json that legitimately declares the short chain is accepted as the prior (validated via `vga.validate_one("plan", ...)`).
- **LD-2: completeness seam.**
  `grep -nE 'REQUIRED_PHASES|def check' qor/reliability/gate_chain_completeness.py -> 20 (tuple), 52 (check)`; per-session loop at 73-82 validates each required artifact. The declaration is read from `.qor/gates/<sid>/plan.json` payload key `required_gate_artifacts`; absent -> the existing tuple (default-full grandfather).
- **LD-3: guard inputs already exist.**
  `grep -nE 'def route_risk' qor/capabilities/risk.py -> 55`; `_RULES` (17-44) route L3 (substantiate skill, ledger_hash, hash_guard) and L2 (META_LEDGER, implement skill, dependency manifests, compiler paths); L1 default. `change_class` regex lives at `qor/scripts/governance_helpers.py:20` (`hotfix|feature|breaking`).
- **LD-4: schema shape mirrors existing conditionals.**
  `grep -n 'additionalProperties' qor/gates/schema/plan.schema.json -> present`; the new `required_gate_artifacts` property (array of the four phase names) + `allOf` rules: when present it MUST contain plan/implement/substantiate; when `change_class` is feature/breaking it MUST contain audit.
- **LD-5: shadow-event discipline.**
  Short-chain declaration emits a severity-1 `gate_override` event (`details.gate = "audit"`, reason "short-chain declared: L1 non-release") via `qor.scripts.shadow_process.append_event` -- the Phase 59/75 never-silent precedent.
- **LD-6: caller enumeration.**
  `grep -rn 'REQUIRED_PHASES' qor/ -> gate_chain_completeness.py:20,75 AND qor/scripts/gate_provenance.py:45,221` -- the provenance `verify-committed` CI merge gate walks its own `_REQUIRED_PHASES` copy per sealed session (221-224, "artifact missing" on absence) and would fail a legal short-chain session; it gains the SAME declared-set resolution (read the session's plan.json `required_gate_artifacts`, default full). `check_prior_artifact` callers are skill prose only (behavior unchanged when audit.json exists). Test fixtures in tests/test_gate_chain_completeness.py build all four artifacts; the additive default keeps them green. No existing plan.json carries the new key -- additive-only.

## Phase 1: Tier guard + schema (TDD first)

### Affected Files

- tests/test_tier_guard.py - NEW; behavioral tests for the guard, schema rules, prior carve-out, completeness declaration, provenance declaration, and the shadow event
- qor/gates/schema/plan.schema.json - `required_gate_artifacts` property + two allOf rules (LD-4)
- qor/scripts/tier_guard.py - NEW; allowed-set computation + declaration check + shadow-event emission + shared declared-set reader
- qor/scripts/gate_chain.py - implement-prior carve-out (LD-1)
- qor/reliability/gate_chain_completeness.py - per-session declared-set resolution (LD-2)
- qor/scripts/gate_provenance.py - verify-committed gains the same declared-set resolution (LD-6)

### Changes

`qor/scripts/tier_guard.py` (<120 lines, stdlib + risk/governance_helpers/shadow_process reuse):

- `SHORT_CHAIN = ("plan", "implement", "substantiate")`, `FULL_CHAIN = ("plan", "audit", "implement", "substantiate")`.
- `allowed_artifact_set(changed_files, change_class) -> tuple[str, ...]` -- `route_risk` over the files; short chain iff grade == "L1" AND change_class == "hotfix"; else full.
- `check_declaration(declared, changed_files, change_class) -> list[str]` -- mismatch strings when a declared short chain is not allowed (names the offending grade/class); empty when legal or when declared is the full set.
- `emit_short_chain_event(session_id, declared, reason) -> None` -- the LD-5 severity-1 event.
- `verify_session(session_id, repo_root) -> list[str]` -- reads `.qor/gates/<sid>/plan.json`, applies `check_declaration` using the payload's `affected_files` + `change_class` (the implement-time fail-closed consumer).

`gate_chain.check_prior_artifact`: after the existing missing-artifact branch for `current_phase == "implement"`, mirror the ideation carve-out -- if `plan.json` exists, validates, declares `required_gate_artifacts` without `"audit"`, AND `tier_guard.verify_session` returns no mismatches, return the plan GateResult; otherwise the legacy missing-prior error.

`gate_chain_completeness.check`: inside the per-session loop, read the session's plan.json payload once; `required = tuple(payload.get("required_gate_artifacts") or REQUIRED_PHASES)`; reject (as a completeness failure) any declared set that is not a subset of REQUIRED_PHASES or omits plan/implement/substantiate; then validate exactly the resolved set.

### Unit Tests

- tests/test_tier_guard.py::test_allowed_set_short_only_for_l1_hotfix - L1+hotfix -> SHORT_CHAIN; L1+feature -> FULL; hash_guard path (L3)+hotfix -> FULL; META_LEDGER path (L2)+hotfix -> FULL
- tests/test_tier_guard.py::test_check_declaration_names_the_violation - declared short on an L3 path returns a mismatch naming the grade; declared full always passes
- tests/test_tier_guard.py::test_schema_rules_for_required_gate_artifacts - plan payload with short set + hotfix validates; short set + feature fails; set omitting implement fails; absent field validates (grandfather)
- tests/test_tier_guard.py::test_implement_prior_accepts_legal_short_chain - tmp gates dir (GATES_DIR patched): plan.json with legal short declaration and NO audit.json -> check_prior_artifact("implement") returns found+valid pointing at plan.json; illegal declaration -> missing-prior error preserved
- tests/test_tier_guard.py::test_completeness_honors_declared_set - synthetic ledger + session with 3 artifacts + short-declaring plan.json -> ok; same session with default (undeclared) plan.json -> audit.json reported missing; declared set omitting implement -> completeness failure
- tests/test_tier_guard.py::test_short_chain_event_emitted - emit_short_chain_event appends a severity-1 gate_override event with details.gate == "audit" (tmp log via shadow_process patch)
- tests/test_tier_guard.py::test_provenance_verify_committed_honors_declared_set - synthetic session with 3 artifacts+sidecars and a short-declaring plan.json: verify-committed reports no missing-audit mismatch; an undeclared session still requires all four

## Feature Inventory Touches

(empty -- governance tooling only; no user-touchable `src/` feature)

## Definition of Done

### Deliverable: risk-tiered gate depth

- **D1**: A low-risk hotfix can traverse plan -> implement -> substantiate with the skipped audit evidenced (never silent), while any release-class change or L2/L3 path is structurally forced onto the full ceremony (GH #248).
- **D2**: `tier_guard.py` (<120 lines) + the two seam edits (gate_chain carve-out ~15 lines; completeness resolution ~12 lines) + schema property with two allOf rules.
- **D3**: chain.md and delegation-table rows updated via /qor-document; GH #248 closes with the Governor decisions cited; seal entry records the self-application note (Phase 168 itself is full-chain: it touches L3 paths).
- **D4**: `test_implement_prior_accepts_legal_short_chain` and `test_completeness_honors_declared_set` observe the two consumers end-to-end; `test_allowed_set_short_only_for_l1_hotfix` observes every guard cell.

## CI Commands

- `python -m pytest tests/test_tier_guard.py -q` -- new-test determinism (run twice)
- `python -m pytest -q` -- full suite regression
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase168-risk-tiered-gate-depth.md` -- plan-text consistency
