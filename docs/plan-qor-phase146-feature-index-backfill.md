# Plan: Phase 146 -- FEATURE_INDEX backfill (FX002/FX003/FX005 -> verified)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. Follows the Phase 145 research brief (docs/research-brief-stash-triage-feature-backfill-2026-06-09.md;
ledger #351). The brief found the 3 `unverified` FEATURE_INDEX rows resolve to ONE inventory drift plus
TWO genuine coverage gaps:

- **FX002 `uninstall`** is a DRIFT, not a gap: `tests/test_cli_install_gemini.py::test_gemini_uninstall_cleans_commands_dir`
  already exercises `qor/install.py:114 _do_uninstall` behaviorally; the row just carries an empty `Test path`.
  Correct the row to cite the existing test and flip to `verified`. No new test.
- **FX003 `list`** (`qor/install.py:171 _do_list`) and **FX005 `info`** (`qor/cli.py:25 _do_info`) have no test.
  Add one behavioral test each (invoke the handler, assert return code + output), then flip to `verified`.

Both new tests are **regression-coverage backfill** (the handlers already ship and work): the tests are
written to lock in current behavior, so they pass on first run. Classified explicitly per CLAUDE.md test
discipline; each is run twice to confirm determinism.

## Phase 1: backfill list + info coverage and correct the uninstall row

### Affected Files

- `tests/test_cli_feature_index_backfill.py` (NEW) - behavioral tests for `_do_list` and `_do_info`.
- `docs/FEATURE_INDEX.md` - flip FX002/FX003/FX005 to `verified`, fill `Test path` for each.

### Changes

`tests/test_cli_feature_index_backfill.py` (NEW):
- `_stage_manifest(dist_root, ids)` helper writes a top-level `manifest.json` with the given skill ids.
- `_stage_skill(dist_root, name, body)` helper writes `variants/claude/skills/<name>/SKILL.md`.
- `_do_list` tests monkeypatch `qor.cli._default_dist_root` to a tmp dist root.
- `_do_info` tests monkeypatch `qor.cli._default_dist_root` to a tmp dist root.

`docs/FEATURE_INDEX.md`:
- FX002 `uninstall`: `Test path` -> `tests/test_cli_install_gemini.py::test_gemini_uninstall_cleans_commands_dir`; status -> `verified`.
- FX003 `list`: `Test path` -> `tests/test_cli_feature_index_backfill.py::test_do_list_available_enumerates_skills`; status -> `verified`.
- FX005 `info`: `Test path` -> `tests/test_cli_feature_index_backfill.py::test_do_info_prints_known_skill`; status -> `verified`.

### Unit Tests

- `tests/test_cli_feature_index_backfill.py`:
  - `test_do_list_available_enumerates_skills` - stage a manifest with ids `qor-plan`, `qor-audit`;
    invoke `_do_list(Namespace(available=True))`; assert rc==0 and stdout contains both ids (de-duplicated).
  - `test_do_list_no_flag_errors` - invoke `_do_list(Namespace())` with neither flag; assert rc==1 and
    stderr names the required flags (confirms the dispatch guard, not just the happy path).
  - `test_do_info_prints_known_skill` - stage `variants/claude/skills/qor-plan/SKILL.md` with a known
    marker line; invoke `_do_info(Namespace(skill="qor-plan"))`; assert rc==0 and stdout contains the marker.
  - `test_do_info_missing_skill_returns_1` - invoke `_do_info(Namespace(skill="no-such-skill"))` against
    an empty dist root; assert rc==1 and stderr contains `not found`.

## Definition of Done

### Deliverable: D-feature-backfill

- **D1**: every CLI feature in FEATURE_INDEX has a cited, passing verifying test (17/17 verified).
- **D2**: `tests/test_cli_feature_index_backfill.py` invokes `_do_list` and `_do_info` and asserts return
  code + captured output; no presence-only assertions.
- **D3**: ledger SEAL records the backfill; FEATURE_INDEX rows FX002/FX003/FX005 read `verified` with
  non-empty `Test path`; SESSION SEAL body reports `Feature Inventory: Total: 17 / verified: 17 / unverified: 0`.
- **D4**: `test_do_list_available_enumerates_skills` (rc==0 + ids), `test_do_list_no_flag_errors` (rc==1),
  `test_do_info_prints_known_skill` (rc==0 + marker), `test_do_info_missing_skill_returns_1` (rc==1 + "not found").

## CI Commands

- `python -m pytest tests/test_cli_feature_index_backfill.py -q` -- new behavioral tests (run twice for determinism).
- `python -m pytest -q` -- full suite green.
