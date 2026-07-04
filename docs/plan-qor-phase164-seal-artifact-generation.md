# Plan: Phase 164 - Seal-artifact generation (generate, don't assert)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: (none -- the module name `seal_artifacts` is a file path, not a glossary term)

**boundaries**:
- limitations: The SYSTEM_STATE `**Phase**` narrative prose remains authored; only the phase number and snapshot date are generated. CHANGELOG stamping stays in substantiate Step 7.6 (`changelog_backends.stamp`) -- already scripted, deliberately not folded in.
- non_goals: No `qor/cli.py` subcommand (the generic `qor-logic scripts seal_artifacts` runner suffices); no badge additions or README restructuring; no change to `badge_currency.check_currency` semantics.
- exclusions: Doctrine files, FEATURE_INDEX, and glossary are untouched except via /qor-document currency updates at seal.

## Open Questions

(none -- all design decisions below are locked with grep evidence)

## Origin

Research brief `docs/research-brief-sdlc-perspective-reset-2026-07-04.md` (ledger entry #378, session `2026-07-04T0600-6a2a11`), recommendation 2: the seal-fragile test class asserts generated-artifact state and breaks on nearly every seal (bit phases 121/122/123/140). Fix: substantiate deterministically GENERATES the presentation artifacts; repo-state currency moves to the seal-time gate (where `--write` has just made it true) and a CI step; the pytest suite keeps only behavioral tests of the generator against synthetic fixtures.

## Locked Decisions

- **LD-1: reuse `badge_currency` counters; add no write logic to it.**
  `git show HEAD:qor/scripts/badge_currency.py | grep -nE '^def ' -> 22:def count_tests, 56:def count_ledger_entries, 62:def count_skills, 70:def count_agents, 78:def count_doctrines, 86:def parse_readme_badges, 95:def check_currency, 135:def main` -- checker-only module (151 lines); the writer imports its counters, keeping check and write un-complected.
- **LD-2: README badge surface is exactly 5 generated badges.**
  `git show HEAD:README.md | grep -nE 'img.shields.io/badge/(Tests|Skills|Agents|Doctrines|Ledger)' -> 10:Tests-2500%20passing, 14:Skills-30, 15:Agents-13, 16:Doctrines-36, 17:Ledger-377%20entries%20sealed` (each with matching `alt` text).
- **LD-3: SYSTEM_STATE generated fields are the Snapshot date and Phase number only.**
  `git show HEAD:docs/SYSTEM_STATE.md | grep -nE '\*\*(Phase|Snapshot)\*\*' -> 3:**Snapshot**: 2026-06-10, 5:**Phase**: Phase 163 (hotfix; ...narrative...)` -- narrative after the phase number is authored content and is preserved verbatim.
- **LD-4: no CLI registration change.**
  `qor-logic scripts <module>` executes any `qor/scripts/*.py` `main()` through the CLI interpreter (observed: `qor-logic scripts install_drift_check`, `qor-logic scripts workspace_fragility_check` both resolve); `qor/cli.py` is already 383 lines (over the 250 razor) and must not grow.
- **LD-5: the 13 fragile tests to remove.**
  `grep -nE '^def test_' tests/test_readme_badge_currency.py -> 41,52,61,70,87` (5 equality tests vs live counts); `tests/test_system_state_freshness.py -> 37,47` (2 header-currency tests); `tests/test_substantiate_badge_currency_wiring.py -> 40,50,56,63,69,79` (6 prose-pattern tests). Kept: `test_badge_currency_module_importable` (16), `test_parse_readme_badges_returns_all_keys` (28), synthetic `check_currency` tests (96, 129), `test_existing_phase_coverage_helpers_still_resolve` (53).
- **LD-6: substantiate wiring points.**
  `grep -nE '^### Step (6|6\.5)' qor/skills/governance/qor-substantiate/SKILL.md -> 346:### Step 6: Sync System State, 384:### Step 6.5: Documentation Currency Check (Phase 31 wiring)`.
- **LD-7: dist recompile after SKILL.md edit.**
  `grep -nE '^def main' qor/scripts/dist_compile.py -> 166:def main` (flags `--out-root`, `--dry-run`); compiled variants live under `qor/dist/`.
- **LD-8: changelog generator is the model, not a target.**
  `grep -nE '^def apply_stamp' qor/scripts/changelog_stamp.py -> apply_stamp(path, version, date)` -- pure, atomic, behaviorally tested in `tests/test_changelog_stamp.py`; Phase 164 copies this pattern for badges + header.

## Phase 1: Generator module (TDD first)

### Affected Files

- tests/test_seal_artifacts.py - NEW; behavioral tests for the generators (synthetic fixtures, no live-repo state assertions)
- qor/scripts/seal_artifacts.py - NEW; pure renderers + file updaters + `main()` with `--write` / `--check`

### Changes

`qor/scripts/seal_artifacts.py` (target <200 lines, all functions <=40):

- `render_readme_badges(text: str, counts: dict[str, int]) -> str` -- pure; substitutes the count in each of the 5 badge URLs and their `alt` attributes (LD-2 formats, including `Tests-<N>%20passing` and `Ledger-<N>%20entries%20sealed` encodings). Unknown badges pass through untouched.
- `render_system_state_header(text: str, phase: int, snapshot: str) -> str` -- pure; rewrites the `**Snapshot**: YYYY-MM-DD` date and the leading `**Phase**: Phase <N>` number token, preserving all narrative after the number (LD-3). Raises `ValueError` if either marker is absent.
- `collect_counts(repo_root: Path) -> dict[str, int]` -- thin wrapper over `badge_currency.count_*` (LD-1).
- `update_files(repo_root: Path, phase: int, snapshot: str) -> list[str]` -- applies both renderers; atomic write (tmp + `os.replace`, same discipline as `apply_stamp` per LD-8); returns the list of files actually changed (empty == already current).
- `check_files(repo_root: Path) -> list[str]` -- returns mismatch descriptions: delegates badges to `badge_currency.check_currency` and adds the header check (phase number == latest ledger seal phase per `badge_currency.count_ledger_entries`-style parse, snapshot parseable ISO date).
- `main(argv) -> int` -- `--write --phase N --snapshot YYYY-MM-DD [--repo-root .]` (explicit inputs; no clock or ledger inference inside `--write`, keeping it deterministic) and `--check [--repo-root .]` (exit 1 on any mismatch, printing each). Exactly one mode required.

### Unit Tests

- tests/test_seal_artifacts.py::test_render_readme_badges_updates_all_five_counts - synthetic README with LD-2 badge lines; asserts each URL and alt text carries the new count
- tests/test_seal_artifacts.py::test_render_readme_badges_is_idempotent - applying the renderer twice with the same counts yields byte-identical output
- tests/test_seal_artifacts.py::test_render_readme_badges_preserves_unknown_badges - PyPI/License/NIST badge lines pass through byte-identical
- tests/test_seal_artifacts.py::test_render_system_state_header_updates_number_and_date - synthetic header; phase number and snapshot date change, narrative preserved verbatim
- tests/test_seal_artifacts.py::test_render_system_state_header_raises_on_missing_marker - text without `**Phase**:` raises ValueError
- tests/test_seal_artifacts.py::test_update_files_writes_and_reports_changed_paths - tmp repo copy; first call returns both paths, second call returns empty (write-side idempotence)
- tests/test_seal_artifacts.py::test_check_files_clean_after_write - tmp repo; `check_files` returns [] immediately after `update_files` (write/check round-trip contract)
- tests/test_seal_artifacts.py::test_check_files_reports_stale_badge_and_header - tmp repo with drifted count and old phase number; both mismatches named
- tests/test_seal_artifacts.py::test_main_write_then_check_exit_codes - `main(['--write',...])` returns 0, `main(['--check',...])` returns 0 after write and 1 after synthetic drift (stdin-free CLI behavior)

## Phase 2: Wiring + fragile-test retirement

### Affected Files

- tests/test_substantiate_seal_artifacts_wiring.py - NEW; single structural test replacing the 6 prose-pattern wiring tests
- tests/test_readme_badge_currency.py - remove the 5 live-equality tests (LD-5 lines 41/52/61/70/87); keep module/parse/synthetic tests
- tests/test_system_state_freshness.py - remove the 2 header-currency tests (LD-5 lines 37/47); keep helper-resolution test
- tests/test_substantiate_badge_currency_wiring.py - DELETE (superseded by the new single wiring test)
- qor/skills/governance/qor-substantiate/SKILL.md - Step 6 and Step 6.5 (LD-6) become scripted: Step 6 runs `qor-logic scripts seal_artifacts --write --phase <N> --snapshot <date>` (narrative still authored in the same step), Step 6.5 runs `qor-logic scripts seal_artifacts --check` and ABORTs the seal on exit 1 for feature/breaking (hotfix exemption retained, badge semantics unchanged per non_goals)
- .github/workflows/ci.yml - new step `seal-artifacts currency` running `qor-logic scripts seal_artifacts --check` (hard fail; PR state is sealed state in this flow, so mid-phase fragility does not recur in CI)
- qor/dist/** - recompiled via `qor-logic scripts dist_compile` (LD-7)

### Changes

The SKILL.md edit replaces manual-update prose with the two commands above; the ABORT/hotfix-exemption sentences are retained verbatim where possible to minimize wiring-token churn. Documentation currency for README and governance docs is executed via /qor-document (operator-directed constraint for this cycle).

### Unit Tests

- tests/test_substantiate_seal_artifacts_wiring.py::test_substantiate_steps_6_and_6_5_invoke_seal_artifacts - the installed skill text contains `seal_artifacts --write` in Step 6 and `seal_artifacts --check` + ABORT semantics in Step 6.5 (single structural guard; regression lock for this phase, named for it). Carries `# prose-lint: ok=wiring regression lock; skill prose has no invokable unit` per `qor/references/doctrine-verification-closure-integrity.md` so the enforced `prose_test_lint` records it as exempted-with-reason, not an unexplained finding.

## Feature Inventory Touches

(empty -- governance tooling and test refactor only; no user-touchable `src/` feature)

## Definition of Done

### Deliverable: seal_artifacts generator module

- **D1**: Seal presentation artifacts (README badges, SYSTEM_STATE header fields) are generated deterministically, never hand-edited.
- **D2**: `qor/scripts/seal_artifacts.py` with `render_readme_badges`, `render_system_state_header`, `update_files`, `check_files`, `main`; <=200 lines; stdlib only.
- **D3**: Seal entry cites this plan; ledger entry records the generate-not-assert decision; README/governance docs updated via /qor-document.
- **D4**: `test_main_write_then_check_exit_codes` observes write->check round-trip returning 0 and synthetic drift returning 1.

### Deliverable: fragile-test retirement

- **D1**: The pytest suite no longer asserts live repo presentation state; currency is enforced at seal time and in CI where state is stable.
- **D2**: 13 tests removed per LD-5; 9 behavioral + 1 structural added; net suite count change recorded in the seal entry.
- **D3**: CI workflow carries the `seal-artifacts currency` step.
- **D4**: `python -m pytest -q` green twice consecutively with zero references to the removed test names (`grep -rn 'badge_matches' tests/` returns nothing).

### Deliverable: substantiate wiring

- **D1**: Substantiate Steps 6/6.5 are scripted, not manual operator duties.
- **D2**: SKILL.md invokes `seal_artifacts --write` (Step 6) and `--check` (Step 6.5); dist variants recompiled.
- **D4**: `test_substantiate_steps_6_and_6_5_invoke_seal_artifacts` fails when either invocation is removed from the skill text.

## CI Commands

- `python -m pytest tests/test_seal_artifacts.py tests/test_substantiate_seal_artifacts_wiring.py -q` -- new-test determinism (run twice)
- `python -m pytest -q` -- full suite regression
- `qor-logic scripts seal_artifacts --check` -- currency gate self-application on the sealed tree
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase164-seal-artifact-generation.md` -- plan-text consistency
- `qor-logic scripts dist_compile --dry-run` -- dist compilation validity after SKILL.md edit
