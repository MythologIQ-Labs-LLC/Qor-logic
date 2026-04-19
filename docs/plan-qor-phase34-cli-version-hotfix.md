# Plan: Phase 34 — CLI `__version__` hotfix

**change_class**: hotfix
**target_version**: v0.24.1
**doc_tier**: minimal
**terms_introduced**: none

## Context

`qor/cli.py:13` hardcodes `__version__ = "0.18.0"`. The string has not been updated across v0.18.0 → v0.24.0 (six releases). `pip show qor-logic` reports the correct version (`0.24.0`) because it reads pyproject; `qorlogic --version` reports `0.18.0` because it reads the hardcoded constant. Same family as SG-Phase32-B (README) and SG-Phase33-A (seal-tag): state duplicated away from source of truth, drifts silently.

## Phase 1: Single fix + regression guard

### Unit Tests (TDD — already green post-fix)

- `tests/test_cli_version_from_metadata.py` — NEW
  - `test_cli_version_matches_package_metadata`: asserts `qor.cli.__version__ == importlib.metadata.version("qor-logic")`.
  - `test_cli_version_not_hardcoded_literal`: Rule-4 structural guard — `cli.py` must not carry a `"X.Y.Z"` SemVer literal on any `__version__ = ...` line. Prevents regression to hardcoding.

### Affected Files

- `tests/test_cli_version_from_metadata.py` (NEW)
- `qor/cli.py` — remove hardcoded `__version__ = "0.18.0"`; read via `importlib.metadata.version("qor-logic")` with `PackageNotFoundError` fallback to `"0+unknown"`.
- `docs/SHADOW_GENOME.md` — Entry #24 SG-Phase34-A.

### Changes

```python
# qor/cli.py (imports updated)
from importlib import metadata

try:
    __version__ = metadata.version("qor-logic")
except metadata.PackageNotFoundError:
    __version__ = "0+unknown"
```

## CI Validation

```bash
python -m pytest tests/test_cli_version_from_metadata.py -q
python -m pytest -q  # full suite stays green
qorlogic --version  # should print installed version, not "0.18.0"
```
