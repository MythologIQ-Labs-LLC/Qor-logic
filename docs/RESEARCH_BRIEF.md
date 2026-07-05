# RESEARCH BRIEF — PyPI Packaging Readiness

**Scope**: `/qor-deep-audit` Phase 2 synthesis for `pip install qor-logic` + agent-agnostic harness
**Repo**: `<path-to-local-clone>` @ main `e282ffb` (post-reorg)
**Date**: 2026-04-16
**Bundle state**: Phase 1 recon complete (5 parallel agents, ~25 findings); Phase 1.5 `/qor-organize` branch resolved structural issues; Phase 2 synthesis this document; Phase 3 verification pending; Phases 4-6 remediation pending operator approval

## Executive Summary

After the reorganization branch, **4 of the original CRITICAL findings are closed** (dual-root resolved, `__init__.py` stubs added, `legacy/` deleted, skill references updated). **18 findings remain**, dominated by two intertwined themes: (1) **import migration** — 13 sibling imports + 11 `parent.parent.parent` path computations + 8 hardcoded runtime paths all assume repo-root CWD and break under site-packages install; (2) **CI/CD greenfield** — no `.github/`, no lint, no release automation, no PyPI trusted publisher. Harness substrate (compile, drift, ledger, platform detect, profiles) is library-callable and ready to wrap behind a `qorlogic` CLI entry point. **Top-5 GA-blockers**: GAP-PKG-01 (no package discovery config), GAP-PKG-02 (no package-data for MD/JSON resources), GAP-IMP-01 (sibling-import cascade), GAP-IMP-02 (REPO_ROOT via `__file__.parent.parent.parent`), GAP-CI-01 (no tests-on-PR workflow).

## Gap Categories (post-reorg)

### PKG — Packaging configuration (6 gaps)

| ID | Severity | Effort | Blocks GA | Summary |
|---|---|---|---|---|
| GAP-PKG-01 | CRITICAL | S | ✓ | `pyproject.toml` has no `[tool.setuptools.packages.find]` — setuptools auto-discovery fails |
| GAP-PKG-02 | CRITICAL | S | ✓ | No `[tool.setuptools.package-data]` — 27 SKILL.md + 24 doctrine MD + 9 schemas won't ship |
| GAP-PKG-03 | HIGH | XS | ✓ | No `[project.scripts]` — no `qorlogic` CLI after install |
| GAP-PKG-04 | HIGH | XS | — | `[project]` missing `readme = "README.md"` — blank PyPI listing |
| GAP-PKG-05 | MEDIUM | XS | — | Missing classifiers, keywords, urls, authors; license text = "Proprietary" conflicts with README BSL-1.1 badge |
| GAP-PKG-06 | MEDIUM | XS | — | `.gitignore` lacks `build/`, `dist/`, `*.egg-info/` — first `python -m build` litters untracked artifacts |

### IMP — Import hygiene (5 gaps)

| ID | Severity | Effort | Blocks GA | Summary |
|---|---|---|---|---|
| GAP-IMP-01 | CRITICAL | M | ✓ | 13 bare sibling imports (`import shadow_process`) across 9 files in `qor/scripts/` fail under install |
| GAP-IMP-02 | HIGH | L | ✓ | 11 `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` sites resolve to `site-packages/` under install — schema loading + I/O break |
| GAP-IMP-03 | HIGH | M | ✓ | 8 hardcoded relative path strings (`"docs/..."`, `"qor/scripts/..."`) are CWD-dependent |
| GAP-IMP-04 | MEDIUM | XS | — | `qor/scripts/compile.py` name collides with Python stdlib `compile()` builtin semantics |
| GAP-IMP-05 | MEDIUM | S | — | `tests/conftest.py` injects `sys.path` to find loose modules — zero coverage for installed-package surface |

### HAR — Harness / CLI (3 gaps)

| ID | Severity | Effort | Blocks GA | Summary |
|---|---|---|---|---|
| GAP-HAR-01 | HIGH | M | ✓ | No `qorlogic install --host <x>` command; variant deployment is manual `cp -r` (README:36-44) |
| GAP-HAR-02 | HIGH | S | — | No host → install-path resolver (`~/.claude/skills/` vs `~/.kilo-code/skills/` vs OS-specific paths) |
| GAP-HAR-03 | MEDIUM | S | — | No variant MANIFEST emitted by compile.py — installer can't enumerate or uninstall without walking the tree |

### CI — CI/CD pipeline (4 gaps)

| ID | Severity | Effort | Blocks GA | Summary |
|---|---|---|---|---|
| GAP-CI-01 | CRITICAL | S | ✓ | `.github/` directory absent — no tests on PR, no multi-Python matrix |
| GAP-CI-02 | CRITICAL | S | ✓ | No release workflow on `v*.*.*` tags — all PyPI pushes manual |
| GAP-CI-03 | HIGH | XS | — | `check_variant_drift.py` exists but not wired to CI; drift can slip through |
| GAP-CI-04 | HIGH | XS | — | `ledger_hash.py verify` exists but not wired to CI; ledger integrity unenforced in-repo |

### DIST — Distribution artifact policy (0 gaps; all decisions deferred to remediation plan)

Decisions needed (not gaps per se):
- `qor/dist/variants/` — ship as package-data OR regenerate at install time via post-install hook
- `qor/vendor/` 9MB — exclude from wheel AND sdist (third-party cache)
- `qor/experimental/` — exclude from wheel; include in sdist (optional)
- `tests/` — exclude from wheel; include in sdist (convention)
- `docs/` — exclude from both except README

## Summary Matrix

| ID | Category | Severity | Effort | Blocks GA | Status |
|---|---|---|---|---|---|
| GAP-PKG-01 | PKG | CRITICAL | S | ✓ | OPEN |
| GAP-PKG-02 | PKG | CRITICAL | S | ✓ | OPEN |
| GAP-PKG-03 | PKG | HIGH | XS | ✓ | OPEN |
| GAP-PKG-04 | PKG | HIGH | XS | — | OPEN |
| GAP-PKG-05 | PKG | MEDIUM | XS | — | OPEN |
| GAP-PKG-06 | PKG | MEDIUM | XS | — | OPEN |
| GAP-IMP-01 | IMP | CRITICAL | M | ✓ | OPEN |
| GAP-IMP-02 | IMP | HIGH | L | ✓ | OPEN |
| GAP-IMP-03 | IMP | HIGH | M | ✓ | OPEN |
| GAP-IMP-04 | IMP | MEDIUM | XS | — | OPEN |
| GAP-IMP-05 | IMP | MEDIUM | S | — | OPEN |
| GAP-HAR-01 | HAR | HIGH | M | ✓ | OPEN |
| GAP-HAR-02 | HAR | HIGH | S | — | OPEN |
| GAP-HAR-03 | HAR | MEDIUM | S | — | OPEN |
| GAP-CI-01 | CI | CRITICAL | S | ✓ | OPEN |
| GAP-CI-02 | CI | CRITICAL | S | ✓ | OPEN |
| GAP-CI-03 | CI | HIGH | XS | — | OPEN |
| GAP-CI-04 | CI | HIGH | XS | — | OPEN |

**Totals**: 18 open gaps. 5 CRITICAL + 7 HIGH + 6 MEDIUM + 0 LOW. **9 GA-blockers**.

## Closed by /qor-organize branch

- `tools/` as dual root → consolidated to `qor/reliability/`
- Dashed filenames duplicated in `qor/scripts/legacy/` → deleted
- `qor/__init__.py`, `qor/scripts/__init__.py`, `qor/reliability/__init__.py` → added
- Skill references (qor-implement Step 5.5, qor-substantiate Step 4.6) → updated
- Test references (test_reliability_scripts.py, test_skill_doctrine.py) → updated

## Sprint Plan (draft — subject to verification round)

**Sprint 1 — Packaging foundation** (~2 days; GA-blockers only)
- GAP-PKG-01: add `[tool.setuptools.packages.find]` with include/exclude
- GAP-PKG-02: add `[tool.setuptools.package-data]` for MD/JSON/YAML globs + `include-package-data = true`
- GAP-PKG-03: add `[project.scripts] qorlogic = "qor.cli:main"` + create `qor/cli.py` thin dispatcher
- GAP-CI-01: add `.github/workflows/ci.yml` — pytest on 3.11/3.12/3.13 × ubuntu/windows/macos
- GAP-CI-02: add `.github/workflows/release.yml` on `v*.*.*` tags — `python -m build` + `pypa/gh-action-pypi-publish@release/v1`

**Sprint 2 — Import migration** (~2 days; unblocks install)
- GAP-IMP-01: convert 13 bare sibling imports to `from qor.scripts import X`
- GAP-IMP-02: split `REPO_ROOT` into (a) `importlib.resources` for packaged assets, (b) `$QOR_ROOT`/CWD/`git rev-parse` for working-dir state
- GAP-IMP-03: route subprocess script invocations through `python -m qor.scripts.X` or entry points
- GAP-IMP-05: add CI job `pip install . && pytest --rootdir=/tmp tests/` to smoke-test installed wheel

**Sprint 3 — Harness CLI** (~1.5 days; agent-agnostic install)
- GAP-HAR-01: implement `qorlogic install/uninstall --host <x>` using existing compile.py + manifest
- GAP-HAR-02: add host → install-path resolver (OS-specific paths for Claude Code, Kilo Code, Codex)
- GAP-HAR-03: emit `manifest.json` from compile.py (reuse `ledger_hash.write_manifest`)

**Sprint 4 — Polish + release rehearsal** (~0.5 day)
- GAP-PKG-04: `readme = "README.md"` in `[project]`
- GAP-PKG-05: PyPI metadata (classifiers, keywords, urls, authors, reconciled license)
- GAP-PKG-06: `.gitignore` build artifacts
- GAP-IMP-04: rename `compile.py` → `dist_compile.py`
- GAP-CI-03: variant drift check in CI
- GAP-CI-04: ledger verify in CI
- Rehearse TestPyPI push

**Blast radius note**: Sprints 1 and 2 have hard ordering dependency (IMP-01 requires PKG-01's `__init__.py` + discovery). Sprint 3 depends on Sprint 1. Sprint 4 runs last.

## Verification status

**Round 1 (this document)**: findings carried forward from Phase 1 recon subagents with file:line citations in each agent's output. Main-session grep spot-checks verified key counts (9 `sys.path.insert` sites, 13 bare imports, 11 `parent.parent.parent` sites, 0 `.github/` workflows). Reorg-closed findings removed.

**Round 2 (complete 2026-04-16)**: architecture + hallucination scan.
- No premature `pip install qor-logic` claims in skills or README (grep-verified).
- `importlib.resources.files()` available in Python 3.10+; repo requires 3.11+ → GAP-IMP-02 remediation path is safe.
- Architecture split `QOR_ROOT` (working state) + `importlib.resources` (packaged assets) is standard Python idiom; no cleaner alternative.
- `qorlogic install --host <x>` pattern matches `pipx`/`pre-commit`/`ansible-galaxy` precedents; sound.
- No new attack surface introduced by packaging; earlier OWASP audit holds (0 HIGH, 3 MEDIUM, 6 LOW — `docs/security-audit-2026-04-16.md`).

**Round 3 (complete 2026-04-16)**: blast-radius validation.
- Sprint 1 → 2 hard dependency confirmed: `__init__.py` + `packages.find` must land before import migration is testable against installed wheel.
- Sprint 3 (CLI) gates on Sprint 2.
- Sprint 1 internal tracks (packaging config / CI baseline / MANIFEST emitter) are independent — parallel-subagent candidates.
- Minimal `pip install -e .` slice: GAP-PKG-01 alone. Editable install tolerates sibling imports because files stay on disk at original paths. Full `pip install .` (wheel-based) requires Sprint 1 + Sprint 2.
- No hidden cross-gap dependencies beyond what's documented in the sprint plan.

All 3 rounds complete per `qor-deep-audit` SKILL.md MINIMUM requirement. Brief is implementation-ready.

## Next actions

Per bundle protocol, this is the **after-synthesis checkpoint**. Options:

- **continue** → Phase 3 verification rounds (2 more rounds before remediation planning)
- **compress** → skip to Phase 4 remediation plan, treating Round 1 as sufficient (plan-time adversarial audit catches any miscalled gaps)
- **branch** → pause, bring in a specific specialist (e.g., `/qor-refactor` for the import migration)
- **stop** → exit; resume marker saved
