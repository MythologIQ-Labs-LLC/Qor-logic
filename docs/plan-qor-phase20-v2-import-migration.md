## Phase 20 v2 — Import Migration (Sprint 2 of 4, remediation of Entry #60 VETO)

**change_class**: feature
**Status**: Active
**Author**: QorLogic Governor
**Date**: 2026-04-16
**Branch**: `phase/20-import-migration`
**Supersedes**: `docs/plan-qor-phase20-import-migration.md` (VETO'd — Entry #60)
**Derived from**: `docs/RESEARCH_BRIEF.md` Sprint 2
**Closes gaps**: GAP-IMP-01, GAP-IMP-02, GAP-IMP-03, GAP-IMP-05 (**4 of 18**; 7 open after this phase)

## Open Questions

None. All 3 Entry #60 violations are mechanical arithmetic fixes.

## Delta from v1 (Entry #60 closures)

v2 fixes 3 SG-038 arithmetic recurrences. No scope changes; no design changes.

**V-1 closure (scripts count)**: header updated from "Scripts (12):" to "Scripts (15):" — matches the 15-path enumeration.

**V-2 closure (total modified count)**: header updated from "Modified (14)" to "Modified (20)" — matches 15 scripts + 2 reliability + 2 tests + 1 CI.

**V-3 closure (remaining-gap arithmetic)**: header updated from "11 open after this phase" to "7 open after this phase" — 18 total − 7 Phase 19 − 4 Phase 20 = 7.

**Deferred to Phase 22 (polish)**: plan-linter test `tests/test_plan_self_consistency.py` proposed in SHADOW_GENOME.md Entry #17 as mechanical SG-038 mitigation. Not included in this v2 to avoid scope-expansion during remediation (SG-036 discipline). Phase 22 Sprint 4 scope note added.

## Scope (unchanged from v1)

All four IMP gaps close in one phase because import and path-computation fixes are tightly coupled per file. Non-SDLC scope respected.

Out of scope:
- Sprint 3 (Phase 21): `qorlogic install/uninstall/list/info/compile/verify-ledger` real logic, host → install-path resolver, MANIFEST emitter, `--profile=<sdlc|filesystem|data|research>` selector
- Sprint 4 (Phase 22): `.gitignore` build artifacts, `compile.py` → `dist_compile.py` rename, drift/ledger CI wiring, TestPyPI rehearsal, macOS in CI matrix, **plan-linter test `tests/test_plan_self_consistency.py` (SG-038 mechanical mitigation per SHADOW_GENOME Entry #17)**

## Grounded state (2026-04-16 via `grep -n` / `wc -l` / `find`)

- `sys.path.insert` sites in production: **9** files (Judge-reverified via `grep -l "^sys.path.insert" qor/scripts/*.py qor/reliability/*.py`)
- Bare sibling imports (`import shadow_process` etc.): **13** across 9 files in `qor/scripts/` (Judge-reverified via regex count)
- `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` sites: **13 total** (11 in `qor/scripts/` + 2 in `qor/reliability/`) (Judge-reverified via `grep -rn | wc -l` → 13)
- Hardcoded runtime path strings: **8** (4 in `calculate-session-seal.py`, 4 in `collect_shadow_genomes.py`)
- `sys.path.insert` in tests: **3** (`tests/conftest.py:6`, `tests/conftest.py:7`, `tests/test_governance_helpers.py:15`)
- Current test count: 278 passed (post-Phase 19, commit `c57a821`)

## Track A — New module: `qor/resources.py`

### Affected Files
- `qor/resources.py` (new)

### Changes

Thin wrapper around `importlib.resources.files("qor")` that exposes packaged assets as `Path`-like objects.

```python
"""Packaged-asset access for QorLogic.

Resolves to the installed package's resource tree via importlib.resources.
Use for: schemas, doctrine .md, skill .md, agent .md, templates, variants.
Do NOT use for: consumer working-dir state (.qor/, docs/PROCESS_SHADOW_GENOME.md).
For those, use qor.workdir.
"""
from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def asset(*parts: str) -> Path:
    """Return a Path to a packaged resource under qor/<parts>."""
    root = files("qor")
    for p in parts:
        root = root / p
    return Path(str(root))


def schema(name: str) -> Path:
    return asset("gates", "schema", name)


def doctrine(name: str) -> Path:
    return asset("references", name)
```

**Razor check**: ~25 lines, 3 functions all under 5 lines.

## Track B — New module: `qor/workdir.py`

### Affected Files
- `qor/workdir.py` (new)

### Changes

Working-dir anchor with fallback chain: `$QOR_ROOT` → `Path.cwd()`. No git default.

```python
"""Working-directory anchor for consumer-state paths.

Consumer-state paths (.qor/, docs/META_LEDGER.md, shadow logs) anchor to the
operator's governance root. Default chain:

1. $QOR_ROOT env var (explicit; highest precedence)
2. Path.cwd() (universal fallback)

Use case agnostic: SDLC repos, filesystem governance, data pipelines,
research projects. For SDLC-specific git-repo detection, call
detect_git_root() explicitly.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def root() -> Path:
    env = os.environ.get("QOR_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def detect_git_root() -> Path | None:
    """Opt-in SDLC helper. Returns None if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip()).resolve()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def gate_dir() -> Path:
    return root() / ".qor" / "gates"


def shadow_log() -> Path:
    return root() / "docs" / "PROCESS_SHADOW_GENOME.md"


def shadow_log_upstream() -> Path:
    return root() / "docs" / "PROCESS_SHADOW_GENOME_UPSTREAM.md"


def meta_ledger() -> Path:
    return root() / "docs" / "META_LEDGER.md"
```

**Razor check**: ~45 lines, longest function ~12 lines.

## Track C — Migrate 13 sibling imports (IMP-01)

### Affected Files
- `qor/scripts/validate_gate_artifact.py`
- `qor/scripts/remediate_read_context.py`
- `qor/scripts/remediate_mark_addressed.py`
- `qor/scripts/qor_audit_runtime.py`
- `qor/scripts/gate_chain.py`
- `qor/scripts/create_shadow_issue.py`
- `qor/scripts/collect_shadow_genomes.py`
- `qor/scripts/check_variant_drift.py`
- `qor/scripts/check_shadow_threshold.py`

### Changes

For each file: delete `sys.path.insert(0, ...)` line; convert `import shadow_process` → `from qor.scripts import shadow_process`; same for `session`, `gate_chain`, `qor_platform`, `compile as compile_mod`.

## Track D — REPO_ROOT split (IMP-02)

### Affected Files
- `qor/scripts/shadow_process.py` (SCHEMA_PATH → `qor.resources.schema`; LOG_PATH → `qor.workdir.shadow_log()`)
- `qor/scripts/validate_gate_artifact.py` (schema → `qor.resources`)
- `qor/scripts/session.py` (session markers → `qor.workdir`)
- `qor/scripts/remediate_emit_gate.py` (gate output → `qor.workdir.gate_dir()`)
- `qor/scripts/qor_platform.py` (platform marker → `qor.workdir`)
- `qor/scripts/gate_chain.py` (GATES_DIR → `qor.workdir.gate_dir()`)
- `qor/scripts/create_shadow_issue.py` (log paths → `qor.workdir`)
- `qor/scripts/compile.py` (skills source → `qor.resources`; dist → `qor.workdir`)
- `qor/scripts/collect_shadow_genomes.py` (schema → `qor.resources`; per-repo paths stay literal)
- `qor/scripts/check_variant_drift.py` (source + dist roots)
- `qor/scripts/check_shadow_threshold.py` (marker path → `qor.workdir`)
- `qor/reliability/intent-lock.py` (fingerprint dir → `qor.workdir`)
- `qor/reliability/skill-admission.py` (skill-registry read → `qor.resources.asset("skills")`)

### Changes

Delete every `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` declaration. Each use-site chooses `qor.resources.X()` (packaged) or `qor.workdir.X()` (consumer state) based on what the path means.

## Track E — Hardcoded path cleanup (IMP-03)

### Affected Files
- `qor/scripts/calculate-session-seal.py` (4 hardcoded paths)
- `qor/scripts/collect_shadow_genomes.py` (4: CHECK_SCRIPT/ISSUE_SCRIPT + 2 log path literals)

### Changes

- `calculate-session-seal.py`: replace `"docs/CONCEPT.md"` etc. with `qor.workdir.root() / "docs" / "CONCEPT.md"`
- `collect_shadow_genomes.py`: replace `CHECK_SCRIPT = "qor/scripts/check_shadow_threshold.py"` with module-form invocation `[sys.executable, "-m", "qor.scripts.check_shadow_threshold"]`

## Track F — Test infrastructure + CI smoke test (IMP-05)

### Affected Files
- `tests/conftest.py` (remove `sys.path.insert`)
- `tests/test_governance_helpers.py` (remove `sys.path.insert`)
- `tests/test_packaging_install.py` (new) — 4 `@pytest.mark.integration` tests
- `.github/workflows/ci.yml` (append install-smoke job)

### Changes

**`tests/test_packaging_install.py`** (new, ~40 lines, 4 tests marked `@pytest.mark.integration`):
- `test_installed_wheel_imports_package`
- `test_installed_wheel_ships_schemas`
- `test_installed_wheel_ships_skills`
- `test_cli_entry_point_runs`

**`.github/workflows/ci.yml`** — append install-smoke job using `${{ runner.temp }}` for cross-platform temp path (per dialogue decision).

## Track G — Test expectations

- Baseline: 278 passed + 0 skipped (post-Phase 19).
- **+4 new** integration tests (skipped by default).
- Default target: 278 → **278 passed + 4 skipped**.
- Integration target: **282 passing** when `-m integration` enabled in CI.

## Affected Files (summary)

### New (3)
- `qor/resources.py`
- `qor/workdir.py`
- `tests/test_packaging_install.py`

### Modified (20)

Scripts (15):
- `qor/scripts/shadow_process.py`
- `qor/scripts/validate_gate_artifact.py`
- `qor/scripts/session.py`
- `qor/scripts/remediate_read_context.py`
- `qor/scripts/remediate_mark_addressed.py`
- `qor/scripts/remediate_emit_gate.py`
- `qor/scripts/qor_audit_runtime.py`
- `qor/scripts/qor_platform.py`
- `qor/scripts/gate_chain.py`
- `qor/scripts/create_shadow_issue.py`
- `qor/scripts/collect_shadow_genomes.py`
- `qor/scripts/compile.py`
- `qor/scripts/check_variant_drift.py`
- `qor/scripts/check_shadow_threshold.py`
- `qor/scripts/calculate-session-seal.py`

Reliability (2):
- `qor/reliability/intent-lock.py`
- `qor/reliability/skill-admission.py`

Tests (2):
- `tests/conftest.py`
- `tests/test_governance_helpers.py`

CI (1):
- `.github/workflows/ci.yml`

Total: 3 new + 20 modified.

## Constraints

- **Inline grounding**: every count cites `grep` / `wc -l` / `find` with date 2026-04-16.
- **Tests before code** for `test_packaging_install.py`.
- **SG-038 lockstep**: header + Tracks + Affected Files + Success Criteria cite the same 4 gap IDs, 3 new + 20 modified files, +4 new tests, 0.10.0 → 0.11.0, 7 remaining after phase.
- **Non-SDLC scope**: `qor/workdir.py` uses `$QOR_ROOT` → `Path.cwd()` only.
- **No new runtime dependencies**: stdlib only.
- **Reliability**: pytest 2x deterministic before commit.

## Success Criteria

- [ ] `qor/resources.py` + `qor/workdir.py` created; both under 50 lines.
- [ ] 13 sibling imports converted to `from qor.scripts import X`.
- [ ] 13 `REPO_ROOT = parent.parent.parent` declarations removed.
- [ ] 9 `sys.path.insert` sites in `qor/scripts/` removed.
- [ ] 8 hardcoded path strings routed through `qor.workdir` or `python -m qor.scripts.X`.
- [ ] 3 `sys.path.insert` sites in tests removed.
- [ ] `tests/test_packaging_install.py` with 4 integration tests.
- [ ] `.github/workflows/ci.yml` install-smoke job added.
- [ ] Tests default: 278 passed + 4 skipped.
- [ ] Tests integration: 282 passing in CI smoke.
- [ ] `python -m build` builds cleanly at 0.11.0.
- [ ] `check_variant_drift.py` clean.
- [ ] `ledger_hash.py verify` chain valid.
- [ ] Substantiation: `0.10.0 → 0.11.0`; annotated tag `v0.11.0`.
- [ ] **4 gaps closed** (GAP-IMP-01, GAP-IMP-02, GAP-IMP-03, GAP-IMP-05); **7 remaining in RESEARCH_BRIEF.md after this phase**.

## CI Commands

```bash
python -m pytest tests/ -v
python -m pytest tests/ -m integration -v
BUILD_REGEN=1 python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
python -m build
git tag --list 'v*' | tail -5
```
