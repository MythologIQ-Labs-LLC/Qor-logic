# Plan: Phase 2 — Compile Pipeline + Drift Guard

**Status**: Active (scope-limited)
**Author**: QoreLogic Governor
**Date**: 2026-04-15
**Scope**: Regenerate per-variant outputs under `qor/dist/variants/{claude,kilo-code,codex}/` from `qor/skills/` and `qor/agents/` SSoT. Prevent hand-edits via pre-commit hook + CI drift check.
**Base spec**: `docs/plan-qor-migration-final.md` §Phase 2

## Open Questions

None. Format decision: for v1, emit **identical content** to claude and kilo-code variants (both platforms accept the same SKILL.md format). Codex target writes only `.gitkeep`. Format divergence between claude and kilo-code deferred until a concrete need surfaces.

## Deliverables

### 1. `qor/scripts/compile.py`

Python 3.11 stdlib only.

- Walk `qor/skills/**/SKILL.md`. For each skill directory, copy the entire directory tree (including `references/`, any other bundled files) to:
  - `qor/dist/variants/claude/skills/<skill-name>/`
  - `qor/dist/variants/kilo-code/skills/<skill-name>/`
- Walk `qor/agents/**/*.md`. Each agent is a single `.md` file. Flatten:
  - `qor/dist/variants/claude/agents/<name>.md`
  - `qor/dist/variants/kilo-code/agents/<name>.md`
- Codex target: `qor/dist/variants/codex/.gitkeep` (idempotent touch).
- **Clean before write**: `shutil.rmtree` each variant root before emitting (ensures removed source skills propagate as dist deletions).
- **Exit code**: 0 on success; nonzero on any I/O error.
- CLI: `python qor/scripts/compile.py` (no args for basic run; `--dry-run` lists intended operations without writing).

### 2. `qor/scripts/check_variant_drift.py`

- Create a `tempfile.TemporaryDirectory()`.
- Run compile into the tempdir (compile.py gains `--out-root` parameter).
- `filecmp.dircmp(qor/dist, tempdir)` — recursive compare.
- Exit 0 if identical; exit non-zero with diff report on drift.
- Called by CI and by the pre-commit hook (optionally) to verify commits.

### 3. `.githooks/pre-commit`

Bash hook. On commit:
- Collect staged files via `git diff --cached --name-only`.
- If any match `^qor/dist/`:
  - If `$BUILD_REGEN` != `1`: reject commit with instruction to run `BUILD_REGEN=1 python qor/scripts/compile.py` then re-stage.
  - Else: append timestamp + user + changed files to `.qor/override.log`; allow commit.

### 4. `docs/hooks-install.md`

One-time-per-clone setup: `git config core.hooksPath .githooks`. Document that the CI drift check is authoritative regardless of hook install state.

### 5. `tests/test_compile.py`

- `test_compile_emits_claude_variant` — fixture skill + agent; after compile, both appear at expected paths
- `test_compile_emits_kilocode_variant`
- `test_codex_stub_writes_gitkeep` — only `.gitkeep` under codex/
- `test_compile_cleans_stale_outputs` — pre-existing stray file in dist removed on recompile
- `test_compile_copies_skill_references` — skill with `references/` subdir; contents replicated
- `test_drift_detector_flags_manual_edit` — tamper a dist file; drift check exits non-zero
- `test_drift_detector_clean_after_recompile` — after recompile, drift check exits 0

### 6. Initial `qor/dist/` commit

Run `BUILD_REGEN=1 python qor/scripts/compile.py` to generate the first variant outputs; commit them.

## Constraints

- **Python 3.11+ stdlib only** (`shutil`, `pathlib`, `filecmp`, `tempfile`, `argparse`, `os`).
- **Atomic behavior**: `shutil.rmtree` + fresh write per variant (no partial-state dist).
- **No format transforms in v1**: source content reaches dist unchanged (identity compile). Divergence is a future concern.
- **Hook is advisory, CI is authoritative**: drift check runs in CI regardless of whether the hook is installed locally.

## Success Criteria

- [ ] `python qor/scripts/compile.py` emits populated `qor/dist/variants/{claude,kilo-code}/` + `codex/.gitkeep`
- [ ] `python qor/scripts/check_variant_drift.py` exits 0 on clean checkout
- [ ] Manual edit to `qor/dist/` causes drift check to exit non-zero
- [ ] Pre-commit hook blocks direct edits to `qor/dist/**` without `BUILD_REGEN=1`
- [ ] `pytest tests/test_compile.py` all pass
- [ ] `ledger_hash.py verify` still OK
- [ ] Committed + pushed

## CI Commands

```bash
python -m pytest tests/test_compile.py -v
python qor/scripts/check_variant_drift.py
```
