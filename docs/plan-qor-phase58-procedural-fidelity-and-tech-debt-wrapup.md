# Plan: Phase 58 — Procedural-fidelity check + tech-debt wrap-up

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: procedural-fidelity check
  home: qor/references/doctrine-procedural-fidelity.md
- term: procedural deviation
  home: qor/references/doctrine-procedural-fidelity.md
- term: doc-surface coverage
  home: qor/references/doctrine-procedural-fidelity.md

**boundaries**:
- limitations:
  - The procedural-fidelity check is a **best-effort static analyzer** over skill prose + git diff + implement-gate `files_touched`. It does not execute the skill's logic; it pattern-matches "does Step N of skill K mention file F or function G, and does the seal commit's diff touch F/G accordingly?". Subtle drift (e.g., function called with the right name but wrong arguments) is out of scope for v1.
  - Deviation severity is rule-based (severity 3 for missing-step, severity 2 for documentation-update gap, severity 1 for ordering drift). Operator-tunable via doctrine; not LLM-classified.
  - Doc-surface coverage check verifies that when a phase's plan declares it touches files in `qor/skills/`, `qor/scripts/`, `qor/references/doctrine-*`, or `qor/gates/schema/`, the seal commit also updates at least one system-tier doc (`docs/SYSTEM_STATE.md`, `docs/operations.md`, `docs/architecture.md`, `docs/lifecycle.md`). Threshold-based; operator can override with documented rationale.
  - Phase 58 ships forward-only enforcement starting at the Phase 58 seal. Pre-Phase-58 historical seals are not retroactively scanned for procedural deviations.
- non_goals:
  - Runtime tracing of skill execution. Out of scope; the check is static-analysis over prose + diff.
  - Auto-remediation of detected deviations. Phase 58 detects + records; operator drives remediation in the next seal cycle.
  - Replacing the existing reliability sweep (Phase 17 wiring) at substantiate Step 4.6. The procedural-fidelity check at Step 4.6.6 is additive.
  - Mandating doc-surface coverage for `change_class: hotfix` plans (matches the Phase 8 advisory-gate posture for hotfixes).
- exclusions:
  - Modifying `qor-research`, `qor-plan`, `qor-implement`, or `qor-audit` skill bodies beyond what's needed to declare the new step at substantiate. The check operates on existing skill prose; it does not require new prose to function.
  - Retroactive backfill of Process Shadow Genome events for past sealed phases. New events are appended forward-only.

## Sprint context

Operator request (2026-05-01 substantiate-cycle observation): Phase 57 substantiate sealed successfully but the operator manually identified that `docs/SYSTEM_STATE.md`, `docs/operations.md`, and `docs/architecture.md` were not updated for Phase 57's surface (gate_written observer channel). Substantiate Step 6 mandates `SYSTEM_STATE.md` update; the seal flow did not catch the omission structurally. The operator's directive: "wrap this up so that there are no more imminent needs."

Phase 58 closes three accumulated tech-debt classes:
1. **Procedural-fidelity gap** (B23): substantiate doesn't structurally verify every step of every called function was followed. Manual operator review is the only catch.
2. **SYSTEM_STATE.md drift**: missing entries for 13 sealed phases (40, 41, 45-50, 52-57; gaps where no seal occurred — 42-44, 51 — are documented as such, not backfilled).
3. **Test session pollution**: `.qor/gates/test-session*` directories accumulate from running tests that don't sandbox to `tmp_path`. New conftest.py teardown sweeps these between test sessions.

Plus a structural rename: the previously-committed `docs/plan-qor-phase58-ideation-readiness-phase.md` (Issue #20 `/qor-ideate`) gets renamed to `docs/plan-qor-phase59-ideation-readiness-phase.md` since Phase 58 is now this tech-debt wrap-up. Issue #20 implementation can proceed at Phase 59 independently.

## Open Questions

1. **Procedural-fidelity check enforcement posture**: WARN (advisory; like Phase 8) or BLOCK (interdiction; like Phase 56 secret-scan)? Default: **WARN at Step 4.6.6, append severity-3 to Process Shadow Genome, do not abort substantiate**. Operators learn from accumulated events; future phase can tighten to BLOCK once the false-positive rate is characterized.
2. **Doc-surface coverage threshold**: when a phase touches a system-tier-affecting file, must it update **all** of (SYSTEM_STATE + operations + architecture + lifecycle), or **at least one**? Default: **at least one** — different phases legitimately affect different doc surfaces; mandating all would cause spurious BLOCK / WARN.
3. **Procedural-fidelity output location**: `dist/procedural-fidelity.findings.json` (matches Phase 55 SBOM + Phase 56 secrets pattern) or `<root>/.qor/gates/<sid>/procedural-fidelity.json` (sidecar to gate dir)? Default: **`dist/procedural-fidelity.findings.json`** for downstream tool symmetry; operator-overridable via `--out`.

Defaults will be encoded unless overridden during audit.

## Phase 1: Procedural-fidelity check module + substantiate Step 4.6.6 wiring

### Affected Files

- `tests/test_procedural_fidelity_module.py` — NEW: locks the public API (`Deviation` frozen dataclass, `check_seal_commit(repo_root, session_id) -> list[Deviation]`, `to_findings_json(deviations) -> list[dict]`).
- `tests/test_procedural_fidelity_substantiate_wiring.py` — NEW: Phase 50 co-occurrence behavior invariant — every SKILL.md whose `phase: substantiate` MUST invoke `python -m qor.scripts.procedural_fidelity --session "$SESSION_ID"`.
- `tests/test_procedural_fidelity_doc_surface_coverage.py` — NEW: behavioral regression — when a fixture seal commit's synthetic `files_touched` list contains a skill-path entry AND a script-path entry but not any of the four system-tier docs (SYSTEM_STATE / operations / architecture / lifecycle), `check_seal_commit` returns a `Deviation` with class `doc-surface-uncovered`. Fixture uses synthetic path strings that do not resolve at HEAD; the function operates on the strings, not the files.
- `tests/test_procedural_fidelity_writes_to_shadow_genome.py` — NEW: behavioral regression — invoking the CLI against a fixture seal commit with deviations appends one severity-3 event per deviation to `<root>/.qor/process-shadow-genome.jsonl` (or whatever path `shadow_process.append_event` resolves to in the live repo).
- `qor/scripts/procedural_fidelity.py` — NEW (~180 LOC). Public API:
  - `Deviation` frozen dataclass: `(deviation_class: str, severity: int, step_id: str | None, description: str, files_referenced: tuple[str, ...])`.
  - `DEVIATION_CLASSES: frozenset[str] = frozenset({"missing-step", "doc-surface-uncovered", "ordering-drift", "argv-shape-divergence"})` — initial Phase 58 catalog; future phases extend.
  - `check_seal_commit(repo_root: Path, session_id: str) -> list[Deviation]` — reads the implement gate artifact, extracts `files_touched`, walks each touched skill body / doctrine / script, applies the four detectors, returns aggregated deviations.
  - `_detect_doc_surface_coverage(touched: list[str], repo_root: Path) -> list[Deviation]` — primary Phase 58 detector. Rule: when `touched` contains any file matching `qor/skills/**/SKILL.md`, `qor/scripts/*.py`, `qor/references/doctrine-*.md`, or `qor/gates/schema/*.json`, AND `touched` does NOT contain at least one of `docs/SYSTEM_STATE.md`, `docs/operations.md`, `docs/architecture.md`, `docs/lifecycle.md`, emit a `doc-surface-uncovered` deviation. Severity 2.
  - `_detect_missing_step(touched: list[str], repo_root: Path) -> list[Deviation]` — secondary detector. Walks substantiate skill body; for each numbered step that mentions a specific file path, asserts the file is in `touched` OR the step is on the operator's `_MAY_SKIP` allowlist. Severity 3.
  - `_detect_ordering_drift` and `_detect_argv_shape_divergence` — stubs in v1, return `[]`. Implementation lands in future phases as the failure-mode catalog grows.
  - `to_findings_json(deviations: list[Deviation]) -> list[dict]` — converts to gate_chain-compatible JSON for downstream tooling. Each finding carries `class`, `severity`, `step_id`, `description`, `files_referenced`, `addressed: false` (operator drives addressed flag in remediation cycle).
  - CLI entry point: `python -m qor.scripts.procedural_fidelity [--session SID] [--repo-root PATH] [--out PATH]`. Exit 0 on no deviations; exit 0 with WARN to stderr on deviations (advisory-gate posture per Open Question 1 default); exit 2 on input rejection (missing implement gate artifact, malformed `files_touched`).
- `qor/skills/governance/qor-substantiate/SKILL.md` — APPEND new substep `### Step 4.6.6: Procedural-fidelity check (Phase 58 wiring)` between the existing Step 4.6.5 (Phase 56 secret-scan) and Step 4.7 (doc integrity check). Body:
  ```bash
  python -m qor.scripts.procedural_fidelity --session "$SESSION_ID" \
    --out dist/procedural-fidelity.findings.json
  ```
  WARN-only semantics (matches Phase 55 pre-audit lints): non-zero exit does NOT abort substantiate, but findings JSON populated → severity-3 events appended to Process Shadow Genome → seal report surfaces a `### Procedural Fidelity` section.

### Changes

The procedural-fidelity check operates on the implement gate artifact (`.qor/gates/<sid>/implement.json`) and the live skill prose. It is purely static — no execution of any function. The four-class deviation catalog is the v1 starting point; subsequent phases extend it as failure modes are observed.

The doc-surface coverage detector resolves the operator-identified Phase 57 gap directly: any seal commit touching skills/scripts/doctrines/schemas without updating at least one system-tier doc gets a `doc-surface-uncovered` event. The operator can override with documented rationale (e.g., "Phase 57 was a contract change with no operator-facing surface" — though Phase 57 actually did affect `docs/operations.md`, so that override would be invalid).

`shadow_process.append_event` already exists in the codebase and writes to `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` with severity tagging. Phase 58 reuses this mechanism; no new sink.

The substantiate skill prose addition is bounded to ~12 lines (the bash invocation + ABORT-or-WARN explanation paragraph + cross-link to doctrine).

### Unit Tests

- `tests/test_procedural_fidelity_module.py`:
  - `test_deviation_is_frozen_dataclass` — `dataclasses.is_dataclass(Deviation)`; mutation raises `FrozenInstanceError`.
  - `test_deviation_classes_constant_includes_v1_set` — `DEVIATION_CLASSES` frozenset contains `{"missing-step", "doc-surface-uncovered", "ordering-drift", "argv-shape-divergence"}`.
  - `test_check_seal_commit_returns_empty_for_clean_fixture` — fixture: implement gate artifact with `files_touched` that includes `docs/SYSTEM_STATE.md`; `check_seal_commit` returns `[]`.
  - `test_to_findings_json_emits_required_fields` — invoke `to_findings_json([Deviation(...)])`; assert each dict has `class`, `severity`, `step_id`, `description`, `files_referenced`, `addressed`.
- `tests/test_procedural_fidelity_substantiate_wiring.py`:
  - `test_substantiate_skill_invokes_procedural_fidelity_at_step_4_6_6` — Phase 50 co-occurrence rule: any SKILL.md whose `phase: substantiate` MUST invoke `python -m qor.scripts.procedural_fidelity --session`. Anchored to actual frontmatter, not single-skill substring.
  - `test_step_4_6_6_uses_warn_not_abort_semantics` — walks substantiate SKILL.md; asserts the procedural_fidelity invocation is NOT followed by `|| ABORT` (matches Phase 55 pre-audit-lint WARN idiom). Distinguishes from Phase 56 secret-scan which IS followed by `|| ABORT`.
- `tests/test_procedural_fidelity_doc_surface_coverage.py`:
  - `test_detects_uncovered_when_skill_changed_without_system_state` — synthetic `files_touched` containing one skill-path string (e.g. a SKILL.md under qor/skills/sdlc/); assert one `doc-surface-uncovered` deviation, severity 2.
  - `test_detects_uncovered_when_doctrine_changed_without_operations` — analogous for a doctrine path string under qor/references/.
  - `test_passes_when_at_least_one_system_doc_updated` — synthetic `files_touched` with a skill-path string AND `docs/SYSTEM_STATE.md`; assert no deviation.
  - `test_passes_when_only_test_files_touched` — synthetic `files_touched = ["tests/test_x.py"]`; assert no deviation (tests-only changes don't require system-doc updates).
  - `test_respects_threshold_at_least_one` — synthetic `files_touched` with a skill-path string AND `docs/operations.md`; assert no deviation (one is sufficient per Open Question 2 default).
- `tests/test_procedural_fidelity_writes_to_shadow_genome.py`:
  - `test_cli_appends_severity_3_event_for_each_doc_surface_deviation` — fixture worktree with synthetic implement gate + uncovered files_touched; subprocess-invoke the CLI; assert `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` has new severity-2 (doc-surface-uncovered) records (per the rule, severity 2 not 3 for this class).
  - `test_cli_exit_0_with_warn_on_deviations` — fixture with deviations; assert exit code 0 but stderr contains `WARN`.
  - `test_cli_exit_2_on_missing_implement_gate` — fixture without implement.json; assert exit 2 + stderr `ERROR`.

## Phase 2: SYSTEM_STATE.md backfill + drift-prevention test

### Affected Files

- `tests/test_system_state_phase_coverage.py` — NEW: forward-only drift-prevention. Conditional rule: every META_LEDGER entry with body matching `### Entry #\d+: SESSION SEAL -- Phase \d+ feature substantiated` MUST have a corresponding `## Phase N (vX.Y.Z)` heading in `docs/SYSTEM_STATE.md`. Pre-Phase-58 entries are grandfathered (test reads a `_GRANDFATHERED_PHASES` set and skips them).
- `docs/SYSTEM_STATE.md` — APPEND backfill entries for 13 sealed phases not currently covered: Phase 40 (v0.30.x), Phase 41 (v0.31.0), Phase 45 (v0.32.0), Phase 46 (v0.33.0), Phase 47 (v0.34.0), Phase 48 (v0.35.0), Phase 49 (v0.36.0), Phase 50 (v0.37.0), Phase 52 (v0.38.0), Phase 53 (v0.39.0), Phase 54 (v0.40.0), Phase 55 (v0.41.0), Phase 56 (v0.42.0). Each entry follows the existing pattern (heading + Decision paragraph + key files + tests + razor compliance summary). Entries are extracted/synthesized from the corresponding META_LEDGER seal entries (Entries #143, #149, #152, #157, #160, #163, #166, #169, #174, #178, #182, #185).

### Changes

The drift-prevention test is the structural countermeasure. After Phase 58, no future seal can land without a SYSTEM_STATE.md entry — `test_system_state_phase_coverage.py` enforces it at every test run. Pre-Phase-58 grandfathering (the `_GRANDFATHERED_PHASES` set) shrinks each time an operator chooses to backfill an older entry; Phase 58 backfills 13, leaving Phase 42/43/44/51 (no-seal phases) explicitly documented as such in the test rationale.

The test reads META_LEDGER entries via the existing `qor/scripts/ledger_hash.ENTRY_RE` regex. For each `Phase N feature substantiated` entry, it greps SYSTEM_STATE.md for `## Phase N (v`. Missing → assertion failure with the phase number in the message.

Backfill content for each missing phase is concise: 5-10 lines per phase summarizing the seal's `Decision` paragraph + key files. This is ledger-anchored documentation; each entry cites its Entry # in META_LEDGER.

### Unit Tests

- `tests/test_system_state_phase_coverage.py`:
  - `test_every_sealed_phase_has_system_state_entry` — walks META_LEDGER, identifies phases with `Phase N feature substantiated` entries; asserts each is present in SYSTEM_STATE.md OR in the `_GRANDFATHERED_PHASES` set. After Phase 58 ships, `_GRANDFATHERED_PHASES = {42, 43, 44, 51}` (no-seal gaps); all sealed phases must have entries.
  - `test_grandfathered_phases_are_documented` — asserts each member of `_GRANDFATHERED_PHASES` has a corresponding rationale in the test docstring or a comment in SYSTEM_STATE.md (e.g., "Phase 42-44: skipped — Phase 41 + 45 covered the same surface; Phase 51: skipped — incremental Phase 52 absorbed the planned scope").
  - `test_system_state_phase_57_entry_present_after_phase_57_seal` — regression sanity: explicit assertion that Phase 57's entry exists. Confirms the Phase 58 plan author actually backfilled (this test would fail in this current branch if Phase 57's entry hadn't already been added in the prior commit).

## Phase 3: Test isolation + ideation plan rename + doctrine + glossary + self-application

### Affected Files

- `tests/test_no_test_session_pollution.py` — NEW: regression — `.qor/gates/test-session*` and `.qor/gates/test-*` directories MUST NOT exist after the test suite finishes. Conditional cleanup hook in conftest.py removes any matching directories at session-end.
- `tests/conftest.py` — UPDATE: add session-scope autouse fixture that, in `yield`-then-teardown, walks `.qor/gates/` and removes any directory matching `test*` or `test-session*` patterns. Idempotent; safe to re-run.
- `docs/plan-qor-phase58-ideation-readiness-phase.md` → `docs/plan-qor-phase59-ideation-readiness-phase.md` — RENAME. Update plan body header from "Phase 58" to "Phase 59" wherever it appears.
- `docs/plan-qor-phase58-ideation-readiness-phase.md` reference in META_LEDGER Entry #188 — leave as-is. Past ledger entries are immutable; the rename is forward-only. Add a note in the new Phase 59 plan front-matter: "Originally drafted as Phase 58; renumbered to Phase 59 per Phase 58 = tech-debt-wrap-up scope reassignment."
- `qor/references/doctrine-procedural-fidelity.md` — NEW (~140 LOC). Sections: `## Applicability`, `## The four v1 deviation classes` (one subsection per class with detection signal + severity + remediation), `## Doc-surface coverage rule`, `## Operator workflow on deviation` (review the findings JSON, fix + amend in next seal cycle, OR document override rationale in the seal report), `## Phase 58 changes vs. ad-hoc operator review`, `## Future extensions` (ordering-drift detector, argv-shape detector, runtime tracing).
- `qor/references/doctrine-shadow-genome-countermeasures.md` — APPEND new SG entry `SG-DocSurfaceUncovered-A` codifying the documentation-update gap risk class + Phase 58 countermeasure (procedural-fidelity check `_detect_doc_surface_coverage` + the SYSTEM_STATE.md drift-prevention test).
- `qor/references/glossary.md` — APPEND 3 new terms: `procedural-fidelity check`, `procedural deviation`, `doc-surface coverage`.
- `CHANGELOG.md` — APPEND `[0.44.0] - 2026-05-XX` entry summarizing Phase 58.

### Changes

The conftest fixture is idempotent and runs at session-end (after all tests in the suite complete). Pattern-match keeps it conservative: only directories whose name starts with `test-session` or `test-` are swept, never user/CI session IDs (which are timestamp-prefixed `2026-...`).

The ideation plan rename is a flat file move. The plan body's Phase 58/Phase 59 references update to "Phase 59" throughout (~6 occurrences expected). The terms_introduced and boundaries blocks remain identical; the substantive content is unchanged.

`SG-DocSurfaceUncovered-A` is the Phase 58 capstone: codifies the failure mode the operator caught manually in Phase 57 substantiate, and the structural countermeasure (doc-surface coverage detector + SYSTEM_STATE drift test) that prevents recurrence.

### Unit Tests

- `tests/test_no_test_session_pollution.py`:
  - `test_qor_gates_test_session_dirs_do_not_exist` — runs at end-of-session; asserts `.qor/gates/test-session*` and `.qor/gates/test-*` directories are absent.
  - `test_conftest_cleanup_fixture_is_session_scope_autouse` — static introspection: `tests/conftest.py` source contains a `pytest.fixture(scope="session", autouse=True)` decorator AND the function body references `.qor/gates/test`.
- `tests/test_doctrine_procedural_fidelity_anchored.py`:
  - `test_doctrine_declares_all_4_v1_deviation_classes` — heading-tree integrity: 4 subsections under `## The four v1 deviation classes`; section names match `DEVIATION_CLASSES` frozenset literal-by-literal.
  - `test_doctrine_doc_surface_coverage_rule_section_lists_all_4_system_docs` — round-trip: `## Doc-surface coverage rule` body literally mentions `docs/SYSTEM_STATE.md`, `docs/operations.md`, `docs/architecture.md`, `docs/lifecycle.md`.
- `tests/test_phase58_self_application.py`:
  - `test_phase58_implement_gate_carries_ai_provenance` — Phase 54 provenance discipline.
  - `test_secret_scanner_clean_against_phase58_plan_and_doctrine` — Phase 56 carry-forward; auto-mask for `.md`.
  - `test_pre_audit_lints_clean_against_phase58_plan` — Phase 55 lints clean.
  - `test_glossary_round_trips_against_phase58_terms` — all 3 new terms with `home: qor/references/doctrine-procedural-fidelity.md` + `introduced_in_plan: phase58-procedural-fidelity-and-tech-debt-wrapup`.
  - `test_phase58_seal_commit_passes_own_procedural_fidelity_check` — meta-coherence: the Phase 58 seal commit's own `files_touched` must NOT trigger any deviation. The seal commit itself dogfoods the new check.
  - `test_phase59_ideation_plan_file_exists_at_renamed_path` — regression: `docs/plan-qor-phase59-ideation-readiness-phase.md` exists; `docs/plan-qor-phase58-ideation-readiness-phase.md` does NOT.

## CI Commands

- `python -m pytest tests/test_procedural_fidelity_*.py -v` — Phase 1 lock.
- `python -m pytest tests/test_system_state_phase_coverage.py -v` — Phase 2 lock.
- `python -m pytest tests/test_no_test_session_pollution.py tests/test_doctrine_procedural_fidelity_anchored.py tests/test_phase58_self_application.py -v` — Phase 3 lock.
- `python -m pytest -x` — full suite; expect 1175 + ~26 new = ~1201 passing twice (deterministic).
- `python -m qor.scripts.prompt_injection_canaries --mask-code-blocks --files docs/plan-qor-phase58-procedural-fidelity-and-tech-debt-wrapup.md qor/references/doctrine-procedural-fidelity.md` — Phase 53 self-application.
- `python -m qor.scripts.plan_test_lint --plan docs/plan-qor-phase58-procedural-fidelity-and-tech-debt-wrapup.md` — Phase 55 self-application.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase58-procedural-fidelity-and-tech-debt-wrapup.md --repo-root .` — Phase 55 self-application.
- `python -m qor.scripts.secret_scanner --mask-blocks --files docs/plan-qor-phase58-procedural-fidelity-and-tech-debt-wrapup.md qor/references/doctrine-procedural-fidelity.md qor/scripts/procedural_fidelity.py` — Phase 56 self-application.
- `python -m qor.scripts.procedural_fidelity --session "$SESSION_ID"` — Phase 58 self-application against the seal commit.
- `python -m qor.reliability.skill_admission qor-substantiate` — admit modified substantiate skill.
- `python -m qor.reliability.gate_skill_matrix` — handoff integrity post-edits.
- `python -m qor.scripts.dist_compile && python -m qor.scripts.check_variant_drift` — variant drift OK after substantiate skill body extension.
- `python -m qor.scripts.badge_currency --repo-root . --ledger docs/META_LEDGER.md` — badges current.
