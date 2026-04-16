# Plan: Phase 21 -- CLI Harness + Polish

**change_class**: feature
**version**: 0.11.0 -> 0.12.0
**branch**: `phase/21-cli-harness-polish`
**date**: 2026-04-15
**baseline**: 278 passed, 4 deselected

## Objective

Close all 7 remaining gaps from `docs/RESEARCH_BRIEF.md` (Sprint 3 + Sprint 4). Ship `pip install qor-logic && qorlogic install --host claude`.

## Gaps Closed (7)

| # | ID | Category | Severity | Track |
|---|---|---|---|---|
| 1 | GAP-HAR-01 | HAR | HIGH | A |
| 2 | GAP-HAR-02 | HAR | HIGH | A |
| 3 | GAP-HAR-03 | HAR | MEDIUM | A |
| 4 | GAP-CI-03 | CI | HIGH | B |
| 5 | GAP-CI-04 | CI | HIGH | B |
| 6 | GAP-IMP-04 | IMP | MEDIUM | C |
| 7 | GAP-PKG-06 | PKG | MEDIUM | D |

**Remaining after phase**: 0 of 18 original gaps (11 closed in Phases 19-20, 7 closed here).

## Track A: CLI Harness (GAP-HAR-01, GAP-HAR-02, GAP-HAR-03)

### A1: Host resolver -- `qor/hosts.py` (new, ~60 lines)

`HostTarget` dataclass: `name`, `skills_dir`, `agents_dir`. Factory `resolve(host_name, target_override=None)` returns a `HostTarget`.

Built-in hosts (3):
1. `claude` -- `~/.claude/skills/` + `~/.claude/agents/` (or `$CLAUDE_PROJECT_DIR/.claude/` if set)
2. `kilo-code` -- `~/.kilo-code/skills/` + `~/.kilo-code/agents/`
3. `codex` -- placeholder, raises `NotImplementedError("codex paths TBD")`

`--target <path>` overrides `skills_dir` and `agents_dir` to `<path>/skills/` and `<path>/agents/`. Extensible: any host can be added by instantiating `HostTarget` directly.

### A2: Manifest emission -- extend `qor/scripts/dist_compile.py`

After `compile_all`, emit `manifest.json` to `<out>/manifest.json`. Format:

```json
{
  "schema_version": "1",
  "generated_ts": "2026-04-15T...",
  "files": [
    {"id": "qor-plan", "source_path": "skills/qor-plan/SKILL.md", "install_rel_path": "skills/qor-plan/SKILL.md", "sha256": "..."},
    ...
  ]
}
```

Reuses `qor/scripts/ledger_hash.py:content_hash` for SHA256.

### A3: Wire CLI subcommands -- `qor/cli.py` (~120 lines total)

6 subcommands wired to real logic:

1. `qorlogic install --host <claude|kilo-code|codex> [--target <path>] [--dry-run]` -- compile if needed, read manifest, copy files to host target
2. `qorlogic uninstall --host <x> [--target <path>]` -- read `.qorlogic-installed.json` from target, remove listed files
3. `qorlogic list --available` / `--installed [--host <x>]` -- enumerate from manifest / installed record
4. `qorlogic info <skill>` -- parse SKILL.md frontmatter from compiled variants
5. `qorlogic compile [--dry-run]` -- delegates to `dist_compile.compile_all`
6. `qorlogic verify-ledger` -- delegates to `ledger_hash.verify`

Install writes `.qorlogic-installed.json` into `target.skills_dir.parent` recording installed file paths + sha256 for uninstall.

## Track B: CI Wiring (GAP-CI-03, GAP-CI-04)

Add 2 steps to `.github/workflows/ci.yml` under the existing `test` job:

1. `python qor/scripts/check_variant_drift.py` -- variant drift gate
2. `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` -- ledger chain gate

Both run after `pip install -e ".[dev]"`, before or after pytest (order-independent).

### Grounded state

- `ci.yml`: 46 lines (verified `wc -l .github/workflows/ci.yml` = 46, 2026-04-15)
- 2 new steps added, each 1 line of `run:`

## Track C: Rename compile.py (GAP-IMP-04)

Rename `qor/scripts/compile.py` -> `qor/scripts/dist_compile.py`.

### Blast radius (3 Python import sites + 1 shell reference + docs)

Python imports to update (3):
1. `qor/scripts/check_variant_drift.py:14` -- `from qor.scripts import compile as compile_mod` -> `from qor.scripts import dist_compile as compile_mod`
2. `tests/test_compile.py:9` -- same pattern
3. `tests/test_e2e.py:241` -- same pattern

Shell reference (1):
1. `.githooks/pre-commit:21` -- `python qor/scripts/compile.py` -> `python qor/scripts/dist_compile.py`

Docs references: update in `docs/plan-qor-migration-final.md`, `docs/plan-qor-migration-v2.md`, `docs/plan-qor-migration-v3.md`, `docs/RESEARCH_BRIEF.md`, `docs/META_LEDGER.md` (historical -- leave as-is, these are audit records).

Decision: historical docs (plan-qor-migration-*.md, META_LEDGER.md, RESEARCH_BRIEF.md) keep original references as-is. Only executable code + hooks get updated.

## Track D: .gitignore cleanup (GAP-PKG-06)

Add 4 patterns to `.gitignore`:
1. `build/`
2. `dist/`
3. `*.egg-info/`
4. `*.whl`

Note: `*.tar.gz` omitted -- no tar.gz artifacts expected and pattern is too broad.

### Grounded state

- `.gitignore`: 19 lines (verified `wc -l .gitignore` = 19, 2026-04-15)

## Tests (expected +20 new)

### Track A tests (14):
1. `test_host_resolver_claude_default` -- skills_dir = `~/.claude/skills/`
2. `test_host_resolver_kilo_default` -- skills_dir = `~/.kilo-code/skills/`
3. `test_host_resolver_codex_raises` -- NotImplementedError
4. `test_host_resolver_target_override` -- custom path wins
5. `test_host_resolver_claude_project_dir_env` -- $CLAUDE_PROJECT_DIR overrides
6. `test_host_resolver_unknown_host_raises` -- ValueError
7. `test_manifest_emission_format` -- keys: schema_version, generated_ts, files; each file has id, source_path, install_rel_path, sha256
8. `test_manifest_sha256_matches_content` -- at least 1 file sha256 matches manual hash
9. `test_install_copies_files_to_target` -- files appear in target dir
10. `test_install_writes_installed_record` -- .qorlogic-installed.json created
11. `test_uninstall_removes_installed_files` -- files gone after uninstall
12. `test_cli_install_integration` -- main(["install", "--host", "claude", "--target", ...])
13. `test_cli_compile_returns_zero` -- main(["compile"]) returns 0
14. `test_cli_verify_ledger_returns_zero` -- main(["verify-ledger"]) returns 0

### Track B tests (2):
15. `test_ci_yml_has_drift_step` -- grep ci.yml for check_variant_drift
16. `test_ci_yml_has_ledger_step` -- grep ci.yml for ledger_hash.py verify

### Track C tests (3):
17. `test_dist_compile_importable` -- `from qor.scripts import dist_compile`
18. `test_no_old_compile_module` -- `qor/scripts/compile.py` does not exist
19. `test_drift_check_uses_dist_compile` -- check_variant_drift imports dist_compile

### Track D tests (1):
20. `test_gitignore_has_build_patterns` -- 4 patterns present

**Total**: 20 new tests. Expected final: 298 passed, 4 deselected.

## Files Modified/Created

### Created (2):
1. `qor/hosts.py` -- host resolver
2. `docs/plan-qor-phase21-cli-harness-polish.md` -- this plan

### Modified (7):
1. `qor/cli.py` -- wire 6 subcommands
2. `qor/scripts/dist_compile.py` -- renamed from compile.py, add manifest emission
3. `qor/scripts/check_variant_drift.py` -- update import
4. `tests/test_compile.py` -- update import
5. `tests/test_e2e.py` -- update import
6. `.github/workflows/ci.yml` -- add drift + ledger steps
7. `.gitignore` -- add build artifact patterns

### Deleted (1):
1. `qor/scripts/compile.py` -- renamed to dist_compile.py

### Test files created (1):
1. `tests/test_phase21_harness.py` -- 20 new tests

**Total**: 2 created + 7 modified + 1 deleted + 1 test file = 11 file operations.

## Constraints

- All 12 SGs active
- Razor: every file < 250 lines, every function < 40 lines
- No new runtime deps beyond stdlib + jsonschema
- SG-038: this plan has 7 gaps (table above lists 7 rows), 4 tracks (A/B/C/D), 20 tests (numbered 1-20), 11 file operations (2+7+1+1)

## Success Criteria

- [ ] 7 gaps closed (GAP-HAR-01, GAP-HAR-02, GAP-HAR-03, GAP-CI-03, GAP-CI-04, GAP-IMP-04, GAP-PKG-06)
- [ ] 298 passed, 4 deselected (278 baseline + 20 new)
- [ ] `qorlogic install --host claude --target /tmp/test --dry-run` exits 0
- [ ] `python qor/scripts/check_variant_drift.py` exits 0
- [ ] `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` exits 0
- [ ] `qor/scripts/compile.py` does not exist (renamed)
- [ ] `.gitignore` contains `build/`, `dist/`, `*.egg-info/`, `*.whl`
- [ ] Version 0.12.0 tagged
- [ ] Ledger chain valid through seal entry
