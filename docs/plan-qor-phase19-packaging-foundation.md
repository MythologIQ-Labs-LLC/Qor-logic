## Phase 19 — PyPI Packaging Foundation (Sprint 1 of 4)

**change_class**: feature
**Status**: Active
**Author**: QorLogic Governor
**Date**: 2026-04-16
**Branch**: `phase/19-packaging-foundation`
**Derived from**: `docs/RESEARCH_BRIEF.md` (deep-audit Sprint 1)
**Closes gaps**: GAP-PKG-01, GAP-PKG-02, GAP-PKG-03, GAP-CI-01, GAP-CI-02 (5 of 18)

## Open Questions

None. Two load-bearing decisions locked in dialogue: (a) ship pre-built variants as package-data (bloat is ~1MB, zero-setup install); flat layout (don't move to `src/qor/` — reorg just committed `qor/__init__.py` at flat root).

## Scope

Phase 19 is the first of four sprints. Delivers the minimum set that makes `pip install .` (editable) produce a valid wheel with all resources included, and lands CI so subsequent phases run under machine enforcement.

Out of scope (future phases):
- Sprint 2 (Phase 20): 13 sibling-import conversions, 11 `REPO_ROOT` site rewrites to `importlib.resources`, 8 hardcoded-path cleanups, tests-from-foreign-CWD smoke test
- Sprint 3 (Phase 21): `qorlogic install/uninstall/list/info` subcommands, host → install-path resolver, MANIFEST emitter in compile.py
- Sprint 4 (Phase 22): PyPI metadata polish, `.gitignore` build artifacts, `compile.py` → `dist_compile.py` rename, drift/ledger CI wiring, TestPyPI rehearsal

## Grounded state (2026-04-16 via `wc -l` / `find` / `grep`)

- `pyproject.toml`: 21 lines — `[project]` only; no packaging config, no package-data, no scripts, no readme, no classifiers.
- `qor/__init__.py`, `qor/scripts/__init__.py`, `qor/reliability/__init__.py` — present (added in `/qor-organize` reorg, commit `e282ffb`).
- Resource counts: 42 skill `.md` under `qor/skills/**`, 24 doctrine `.md` under `qor/references/*.md`, 9 schemas `qor/gates/schema/*.json`, 13 agent `.md` under `qor/agents/**`, 6 `qor/templates/*`, 3 gates `qor/gates/*.md` (chain, delegation-table, workflow-bundles), 5 platform profile `.md` under `qor/platform/**`. Variant trees: `qor/dist/variants/{claude,kilo-code,codex}/`.
- `.github/` directory: absent (verified `ls .github/` returns "No such file or directory").
- Tests passing: 263 + 6 skipped (deterministic 2x at reorg commit).
- `qor/scripts/qor_platform.py`: present (host profile + capability detection module).

## Track A — Packaging config (`pyproject.toml`)

### Affected Files

- `pyproject.toml` — extend from 21 lines to ~70 lines

### Changes

Add after existing `[project.optional-dependencies]`:

```toml
[project.scripts]
qorlogic = "qor.cli:main"

[project.urls]
Homepage = "https://github.com/MythologIQ-Labs-LLC/Qor-logic"
Repository = "https://github.com/MythologIQ-Labs-LLC/Qor-logic"
Issues = "https://github.com/MythologIQ-Labs-LLC/Qor-logic/issues"

[tool.setuptools.packages.find]
include = ["qor*"]
exclude = ["qor.vendor*", "qor.experimental*", "tests*"]

[tool.setuptools.package-data]
qor = [
    "skills/**/*.md",
    "references/*.md",
    "agents/**/*.md",
    "gates/*.md",
    "gates/schema/*.json",
    "platform/**/*.md",
    "templates/*",
    "dist/variants/**/*.md",
    "dist/variants/**/*.json",
]

[tool.setuptools]
include-package-data = true
```

Update existing `[project]` block:

```toml
readme = "README.md"
license = { text = "BSL-1.1" }
authors = [{ name = "MythologIQ Labs, LLC" }]
keywords = ["governance", "ai", "claude-code", "kilo-code", "codex", "sdlc", "skills"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: Other/Proprietary License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: Quality Assurance",
]
```

Closes GAP-PKG-01, GAP-PKG-02, GAP-PKG-03 (scripts entry), GAP-PKG-04 (readme), GAP-PKG-05 (metadata).

**Razor check**: `pyproject.toml` grows 21 → ~70 lines, under 250.

## Track B — CLI entry point stub

### Affected Files

- `qor/cli.py` (new)

### Changes

Thin dispatcher. Subcommands stubbed with "coming in Phase 21" messages. Real logic lands in Sprint 3.

```python
"""QorLogic CLI — agent-agnostic skill distribution harness."""
from __future__ import annotations

import argparse
import sys

__version__ = "0.10.0"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="qorlogic",
        description="S.H.I.E.L.D. governance skills for AI coding hosts.",
    )
    parser.add_argument("--version", action="version", version=f"qorlogic {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    for cmd, help_text in (
        ("install", "install skills into an AI coding host (Phase 21)"),
        ("uninstall", "remove installed skills (Phase 21)"),
        ("list", "enumerate available or installed skills (Phase 21)"),
        ("info", "show skill metadata (Phase 21)"),
        ("compile", "regenerate variants from source (Phase 21)"),
        ("verify-ledger", "verify META_LEDGER.md chain (Phase 21)"),
    ):
        sp = sub.add_parser(cmd, help=help_text)
        sp.set_defaults(func=_not_implemented)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    return args.func(args)


def _not_implemented(args: argparse.Namespace) -> int:
    print(f"qorlogic {args.command}: not yet implemented (Phase 21)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

Closes GAP-PKG-03 (stub dispatcher).

**Razor check**: ~40 lines, under 250. One function (`main`) ~20 lines, under 40.

## Track C — CI baseline

### Affected Files

- `.github/workflows/ci.yml` (new)
- `.github/workflows/release.yml` (new)

### Changes

**`.github/workflows/ci.yml`** — run pytest on every PR + push to main:

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.11", "3.12", "3.13"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: python -m pytest tests/ -v
```

Matrix: 6 jobs (3 Python × 2 OS). Skips macOS for Sprint 1 (Phase 22 polish can add it).

**`.github/workflows/release.yml`** — trigger on `v*.*.*` tags:

```yaml
name: Release
on:
  push:
    tags: ['v*.*.*']

permissions:
  id-token: write
  contents: read

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

Uses OIDC trusted publisher (no API token needed — must be registered on PyPI side; out of scope for this phase).

Closes GAP-CI-01, GAP-CI-02.

**Razor check**: both YAMLs under 50 lines each.

## Track D — Tests (TDD)

### Affected Files

- `tests/test_packaging.py` (new)
- `tests/test_cli.py` (new)

### Changes

**`tests/test_packaging.py`** — verify pyproject config declares required fields:

- `test_pyproject_declares_packages_find` — parse `pyproject.toml`, assert `[tool.setuptools.packages.find]` present with `include` and `exclude`.
- `test_pyproject_declares_package_data` — assert `qor` key in `[tool.setuptools.package-data]` includes globs for `skills/`, `references/`, `agents/`, `gates/schema/`, `platform/`, `templates/`, `dist/variants/`.
- `test_pyproject_declares_entry_point` — assert `[project.scripts].qorlogic == "qor.cli:main"`.
- `test_pyproject_declares_readme` — assert `readme = "README.md"` in `[project]`.
- `test_pyproject_declares_classifiers` — assert Python 3.11/3.12/3.13 classifiers present.

**`tests/test_cli.py`** — smoke test the dispatcher:

- `test_qor_cli_main_importable` — `from qor.cli import main` succeeds (validates package install path).
- `test_qor_cli_help_returns_zero` — `main(["--help"])` via SystemExit 0 or returns 0.
- `test_qor_cli_version_prints_version` — `main(["--version"])` prints the version string.
- `test_qor_cli_unknown_command_errors` — `main(["install"])` returns exit code 2 (not-yet-implemented stub).

**`tests/test_packaging.py`** uses `tomllib` (stdlib 3.11+; verified repo requires 3.11+). **`tests/test_cli.py`** uses `capsys` for stdout capture and `SystemExit` handling. No new dependencies.

## Affected Files (summary)

### New (5)
- `qor/cli.py`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `tests/test_packaging.py`
- `tests/test_cli.py`

### Modified (1)
- `pyproject.toml` (21 → ~70 lines)

## Constraints

- **Inline grounding**: every file-size claim, line count, resource count carries `wc -l` / `find` / `grep` provenance inline with date 2026-04-16 (SG-016 + SG-036 active).
- **Tests before code** for `test_packaging.py` and `test_cli.py`.
- **SG-038 lockstep**: prose + code blocks + success criteria cite the same 5 gap IDs, same +9 tests, same version bump.
- **Razor compliance**: all new files under 250 lines; all functions under 40 lines.
- **No new runtime dependencies**: stdlib `argparse`, `tomllib`, `sys`.
- **Reliability**: pytest 2x consecutive identical results before commit.
- **Variant drift + ledger verify**: run manually in Phase 19; CI wiring deferred to Phase 22 (Sprint 4).

## Success Criteria

- [ ] `pyproject.toml` declares packages.find, package-data (8 globs), scripts entry, readme, classifiers, keywords, urls, authors.
- [ ] `qor/cli.py` imports cleanly and `main(["--version"])` prints `qorlogic 0.10.0`.
- [ ] `.github/workflows/ci.yml` exists (6-job matrix: 3 Python × 2 OS).
- [ ] `.github/workflows/release.yml` exists (triggers on `v*.*.*`, uses OIDC trusted publisher).
- [ ] Tests: +9 new (5 packaging + 4 cli). Baseline 263 → **272 passing**, skipped unchanged.
- [ ] `python -m build` succeeds locally (manual spot-check; CI enforcement in Phase 22).
- [ ] `check_variant_drift.py` clean after `BUILD_REGEN=1`.
- [ ] `ledger_hash.py verify` chain valid.
- [ ] Substantiation: `0.9.0 → 0.10.0`; annotated tag `v0.10.0`.

## CI Commands

```bash
python -m pytest tests/test_packaging.py tests/test_cli.py -v
python -m pytest tests/
BUILD_REGEN=1 python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
python -m build  # manual smoke test; must produce qor_logic-0.10.0-py3-none-any.whl
git tag --list 'v*' | tail -5
```
