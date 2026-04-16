## Phase 20 — Import Migration (Sprint 2 of 4)

**change_class**: feature
**Status**: Active
**Author**: QorLogic Governor
**Date**: 2026-04-16
**Branch**: `phase/20-import-migration`
**Derived from**: `docs/RESEARCH_BRIEF.md` Sprint 2 + `/qor-deep-audit` Phase 5 follow-on
**Closes gaps**: GAP-IMP-01, GAP-IMP-02, GAP-IMP-03, GAP-IMP-05 (**4 of 18**; 11 open after this phase)

## Open Questions

None. Design locked in dialogue:
- All 4 IMP gaps land in one monolithic phase (Phase 14-style) because import and path-computation fixes are tightly coupled per file
- Working-dir anchor: `$QOR_ROOT` env var → `Path.cwd()` fallback (no git-rev-parse default — avoids SDLC assumption that breaks filesystem-governance / data-pipeline / research use cases)
- Packaged-asset anchor: `importlib.resources.files("qor") / "..."` (stdlib Python 3.9+; repo requires 3.11+)
- Cross-platform CI temp: `${{ runner.temp }}` (not `/tmp`)
- Non-SDLC scope acknowledged: Phase 21 CLI (Sprint 3) will grow `--profile=<sdlc|filesystem|data|research>` selector; Phase 20 must not bake in SDLC assumptions

## Grounded state (2026-04-16 via `grep -n` / `wc -l` / `find`)

- `sys.path.insert` sites in production: **9** (`qor/scripts/{validate_gate_artifact,remediate_read_context,remediate_mark_addressed,qor_audit_runtime,gate_chain,create_shadow_issue,collect_shadow_genomes,check_variant_drift,check_shadow_threshold}.py`)
- Bare sibling imports (`import shadow_process` etc.): **13** across 9 files in `qor/scripts/`
- `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` sites: **11** in `qor/scripts/` + **2** in `qor/reliability/` = **13 total**
- Hardcoded runtime path strings: **8** (4 in `qor/scripts/calculate-session-seal.py`, 4 in `qor/scripts/collect_shadow_genomes.py`)
- `sys.path.insert` in tests: **3** (`tests/conftest.py:6`, `tests/conftest.py:7`, `tests/test_governance_helpers.py:15`)
- Current test count: 278 passed (post-Phase 19, commit `c57a821`)
- Packaged resources confirmed in `qor/dist/variants/claude/...` after `python -m build` (verified Phase 19)

## Track A — New module: `qor/resources.py`

### Affected Files
- `qor/resources.py` (new)

### Changes

Thin wrapper around `importlib.resources.files("qor")` that exposes packaged assets as `Path`-like objects. Hides the stdlib ceremony so call sites stay readable.

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
    """Return a Path to a packaged resource under qor/<parts>.

    Example:
        asset("gates", "schema", "shadow_event.schema.json")
    """
    root = files("qor")
    for p in parts:
        root = root / p
    return Path(str(root))


def schema(name: str) -> Path:
    return asset("gates", "schema", name)


def doctrine(name: str) -> Path:
    return asset("references", name)
```

**Razor check**: ~25 lines, 3 functions all under 5 lines. Under 250.

## Track B — New module: `qor/workdir.py`

### Affected Files
- `qor/workdir.py` (new)

### Changes

Working-dir anchor with fallback chain: `$QOR_ROOT` → `Path.cwd()`. No git by default (non-SDLC use cases are first-class).

```python
"""Working-directory anchor for consumer-state paths.

Consumer-state paths (.qor/, docs/META_LEDGER.md, shadow logs) are anchored
to the operator's governance root, not to the installed package. Default
chain:

1. $QOR_ROOT env var (explicit; highest precedence)
2. Path.cwd() (universal fallback)

Use case agnostic: works for SDLC repos, filesystem governance, data
pipelines, research projects. For SDLC-specific git-repo detection,
call detect_git_root() explicitly.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def root() -> Path:
    """Return the governance working-dir root."""
    env = os.environ.get("QOR_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def detect_git_root() -> Path | None:
    """Opt-in helper for SDLC users. Returns None if not in a git repo."""
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

**Razor check**: ~45 lines, longest function (`detect_git_root`) ~12 lines. Under 250.

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

For each file:
1. Delete `sys.path.insert(0, str(Path(__file__).resolve().parent))` line
2. Convert `import shadow_process` → `from qor.scripts import shadow_process`
3. Convert `import session` → `from qor.scripts import session`
4. Convert `import gate_chain` → `from qor.scripts import gate_chain`
5. Convert `import qor_platform` → `from qor.scripts import qor_platform`
6. Convert `import compile as compile_mod` → `from qor.scripts import compile as compile_mod` (rename to `dist_compile` is Phase 22)

No functional changes; purely import namespace rewrite.

## Track D — REPO_ROOT split (IMP-02)

### Affected Files
- `qor/scripts/shadow_process.py` (SCHEMA_PATH → `qor.resources.schema("shadow_event.schema.json")`; LOG_PATH → `qor.workdir.shadow_log()`)
- `qor/scripts/validate_gate_artifact.py` (schema lookups → `qor.resources`)
- `qor/scripts/session.py` (session markers → `qor.workdir`)
- `qor/scripts/remediate_emit_gate.py` (gate output → `qor.workdir.gate_dir()`)
- `qor/scripts/qor_platform.py` (platform marker → `qor.workdir.root() / ".qor" / "platform.json"`)
- `qor/scripts/gate_chain.py` (GATES_DIR → `qor.workdir.gate_dir()`)
- `qor/scripts/create_shadow_issue.py` (log paths → `qor.workdir`)
- `qor/scripts/compile.py` (skills source → `qor.resources.asset("skills")`; dist output stays at `qor.workdir.root() / "qor" / "dist"`)
- `qor/scripts/collect_shadow_genomes.py` (schema → `qor.resources`; per-repo paths stay literal)
- `qor/scripts/check_variant_drift.py` (source + dist roots)
- `qor/scripts/check_shadow_threshold.py` (marker path → `qor.workdir`)
- `qor/reliability/intent-lock.py` (fingerprint dir → `qor.workdir.root() / ".qor" / "intent-lock"`)
- `qor/reliability/skill-admission.py` (skill-registry read → `qor.resources.asset("skills")`)

### Changes

Delete every `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` declaration. Each use-site chooses `qor.resources.X()` (packaged) or `qor.workdir.X()` (consumer state) based on what the path means.

Example migration in `shadow_process.py`:

```python
# BEFORE
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = REPO_ROOT / "qor" / "gates" / "schema" / "shadow_event.schema.json"
LOCAL_LOG_PATH = REPO_ROOT / "docs" / "PROCESS_SHADOW_GENOME.md"
UPSTREAM_LOG_PATH = REPO_ROOT / "docs" / "PROCESS_SHADOW_GENOME_UPSTREAM.md"
LOG_PATH = LOCAL_LOG_PATH

# AFTER
from qor import resources as _resources
from qor import workdir as _workdir

SCHEMA_PATH = _resources.schema("shadow_event.schema.json")
LOCAL_LOG_PATH = _workdir.shadow_log()
UPSTREAM_LOG_PATH = _workdir.shadow_log_upstream()
LOG_PATH = LOCAL_LOG_PATH
```

## Track E — Hardcoded path cleanup (IMP-03)

### Affected Files
- `qor/scripts/calculate-session-seal.py` (4 hardcoded paths)
- `qor/scripts/collect_shadow_genomes.py` (4: CHECK_SCRIPT / ISSUE_SCRIPT invocations + 2 log path literals)

### Changes

- `calculate-session-seal.py`: replace `"docs/CONCEPT.md"` etc. with `qor.workdir.root() / "docs" / "CONCEPT.md"`
- `collect_shadow_genomes.py`: replace `CHECK_SCRIPT = "qor/scripts/check_shadow_threshold.py"` with module-form invocation — `[sys.executable, "-m", "qor.scripts.check_shadow_threshold"]` in the `subprocess.run` call sites. Same for `ISSUE_SCRIPT`.

## Track F — Test infrastructure + CI smoke test (IMP-05)

### Affected Files
- `tests/conftest.py` (remove `sys.path.insert` — no longer needed post-migration)
- `tests/test_governance_helpers.py` (remove `sys.path.insert`)
- `tests/test_packaging_install.py` (new) — smoke test that validates installed-wheel behavior
- `.github/workflows/ci.yml` (add install-smoke job)

### Changes

**`tests/conftest.py`** — drop the path-injection block (lines 5-7).

**`tests/test_governance_helpers.py`** — drop line 15's `sys.path.insert`.

**`tests/test_packaging_install.py`** (new, ~40 lines):

- `test_installed_wheel_imports_package` — subprocess installs the built wheel into a tmp venv, asserts `python -c "import qor.scripts.shadow_process"` succeeds.
- `test_installed_wheel_ships_schemas` — asserts `qor.resources.schema("shadow_event.schema.json")` resolves to an existing file post-install.
- `test_installed_wheel_ships_skills` — asserts at least 27 `SKILL.md` files reachable via `qor.resources.asset("skills")`.
- `test_cli_entry_point_runs` — runs `qorlogic --version` via subprocess, asserts returncode 0.

Marked `@pytest.mark.integration` (opt-in via `-m integration`) because it requires an isolated install. Regular `pytest tests/` skips them; CI runs them explicitly.

**`.github/workflows/ci.yml`** — append an install-smoke job:

```yaml
  install-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install build
      - run: python -m build --wheel
      - run: pip install dist/*.whl pytest
      - run: |
          mkdir -p ${{ runner.temp }}/qor-smoke
          cp -r tests ${{ runner.temp }}/qor-smoke/
          cd ${{ runner.temp }}/qor-smoke
          python -m pytest tests/test_packaging_install.py -m integration -v
```

Uses `${{ runner.temp }}` for cross-platform compatibility per dialogue decision.

## Track G — Test expectations

### Changes

- Baseline: 278 passed + 0 skipped (post-Phase 19).
- **+4 new** `test_packaging_install.py` integration tests (skipped by default, run in CI smoke job).
- **0 tests removed.**
- Target: 278 → **282 passing** when `-m integration` enabled; **278 passing + 4 skipped** under default pytest.

## Affected Files (summary)

### New (3)
- `qor/resources.py`
- `qor/workdir.py`
- `tests/test_packaging_install.py`

### Modified (14)

Scripts (12):
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
- `.github/workflows/ci.yml` (append install-smoke job)

## Constraints

- **Inline grounding**: every count cites `grep -n` / `wc -l` / `find` with date 2026-04-16 (SG-016 + SG-036 active).
- **Tests before code** for `test_packaging_install.py`.
- **SG-038 lockstep**: header + Tracks + Success Criteria all cite the same 4 gap IDs, same +4 new tests, same version bump 0.10.0 → 0.11.0.
- **SG-033 discipline**: no new keyword-only signatures; grep callers if any introduced.
- **Razor compliance**: `qor/resources.py` ~25 lines; `qor/workdir.py` ~45 lines; other files shrink (REPO_ROOT declarations deleted).
- **Non-SDLC scope**: `qor/workdir.py` does NOT prefer git-rev-parse; `$QOR_ROOT` → `Path.cwd()` only. Documented in module docstring.
- **No new runtime dependencies**: `importlib.resources` + `subprocess` + stdlib.
- **Reliability**: pytest 2x consecutive identical results before commit.

## Success Criteria

- [ ] `qor/resources.py` + `qor/workdir.py` created; both under 50 lines.
- [ ] All 13 sibling imports converted to `from qor.scripts import X`.
- [ ] All 13 `REPO_ROOT = parent.parent.parent` declarations removed; each use-site uses `qor.resources` or `qor.workdir`.
- [ ] All 9 `sys.path.insert` sites in `qor/scripts/` removed.
- [ ] 8 hardcoded path strings routed through `qor.workdir` or `python -m qor.scripts.X`.
- [ ] `tests/conftest.py` + `tests/test_governance_helpers.py` no longer inject `sys.path`.
- [ ] `tests/test_packaging_install.py` with 4 `@pytest.mark.integration` tests.
- [ ] `.github/workflows/ci.yml` install-smoke job added.
- [ ] Tests (default): 278 → 278 passed + 4 skipped (integration).
- [ ] Tests (integration): 4 additional passing in CI smoke.
- [ ] `python -m build` still builds cleanly.
- [ ] `check_variant_drift.py` clean.
- [ ] `ledger_hash.py verify` chain valid.
- [ ] Substantiation: `0.10.0 → 0.11.0`; annotated tag `v0.11.0`.
- [ ] 4 gaps closed: GAP-IMP-01, GAP-IMP-02, GAP-IMP-03, GAP-IMP-05 (11 remaining in RESEARCH_BRIEF.md).

## CI Commands

```bash
python -m pytest tests/ -v                                  # default: 278 + 4 skipped
python -m pytest tests/ -m integration -v                   # integration: 4 more passing
BUILD_REGEN=1 python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
python -m build                                             # must still produce 0.11.0 wheel
git tag --list 'v*' | tail -5
```
