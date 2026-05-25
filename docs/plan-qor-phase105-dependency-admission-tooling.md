# Plan: Phase 105 — Dependency-admission tooling (v0.73.0)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: Phase 103 `qor/references/doctrine-dependency-admission.md` Cluster carry-forward. The doctrine declares two operator obligations -- a 14-day cooling-period check at PR time and a 30-day follow-up re-evaluation -- both performed manually in Phase 103. Phase 105 ships the supporting tooling.

**terms_introduced**:
- term: dependency-admission-lint
  home: qor/references/doctrine-dependency-admission.md
- term: dep-admit-override-tracker
  home: qor/references/doctrine-dependency-admission.md
- term: PyPI Warehouse upload-time query
  home: qor/references/doctrine-dependency-admission.md

**boundaries**:
- limitations: ships two operator-invokable CLI scripts (`qor/scripts/dependency_admission_lint.py`, `qor/scripts/dep_admit_override_tracker.py`) and a small shared helper (`qor/scripts/_dep_admit_common.py`) for ledger override parsing + lockfile diff parsing. Wires the lint into `.github/workflows/pr-dependency-review.yml` as a WARN-only step on PRs that touch `requirements-release.txt`. WARN-only is the V1 rollout per Phase 99 ramp pattern (visibility-first, evidence-second, enforce-third). Adds an additive note to the Phase 103 doctrine pointing at the lint tool.
- non_goals: hard-fail enforcement at PR time (deferred to a V2 phase once operator-evidence on false-positive rate accumulates); PR-label-based override detection (deferred to V2; v1 uses META_LEDGER `**Dependency admission override**:` lines as the single source of truth, matching the doctrine prose verbatim); broadening the cooling-period to direct deps in `pyproject.toml` (lint scope is `requirements-release.txt` only in V1); calendar integration for the tracker (V1 emits a markdown table to stdout; operator runs on their own cadence); auto-creating GitHub issues for due-for-review overrides (V2 candidate); cyclonedx-bom hash-pinning (separate deferred carry-forward; Razor file budget concern documented in Phase 102).
- exclusions: no changes to the doctrine's substantive policy (14-day threshold, 30-day follow-up window, override-procedure structure); no changes to the Phase 102 `requirements-release.txt` lockfile content or the SHA-pinned dependency-review-action; no changes to the Phase 103 cluster-recovery release.yml.

**high_risk_target**: false

## Open Questions

None. User confirmed: single phase covering both tools; WARN-only CI wiring on `pr-dependency-review.yml`; META_LEDGER as the v1 override source of truth (no PR-label check).

## Feature Inventory Touches

Empty. New operator-invokable scripts + workflow step + doctrine-prose additive note. No user-touchable feature added.
`feature_inventory_touches`: `[]`.

## Design notes

### Shared helper module (`qor/scripts/_dep_admit_common.py`)

Three pure functions, no I/O:

- `parse_lockfile_entries(text: str) -> list[LockfileEntry]` -- parses `requirements-release.txt` pip-compile format; each `LockfileEntry` carries `name`, `version`, `hashes: list[str]`. Tolerant of the `package==X.Y.Z \` continuation pattern; rejects malformed entries with an explicit error.
- `diff_lockfile_against_base(current: list[LockfileEntry], base: list[LockfileEntry]) -> list[Bump]` -- returns the set of new + version-bumped entries vs the base. `Bump` is `(name, old_version | None, new_version)`.
- `parse_override_entries(ledger_text: str) -> list[OverrideEntry]` -- walks the META_LEDGER for `**Dependency admission override**:` lines and parses out `package`, `version`, `upload_age_days`, `justification`, `entry_ts` (the IMPLEMENTATION entry timestamp).

These pure functions are individually unit-testable without network or filesystem access.

### Lint (`qor/scripts/dependency_admission_lint.py`)

Operator-invokable + CI-invokable. Flow:

1. Read the current `requirements-release.txt`.
2. Resolve the base ref:
   - CI: `--base <sha>` (passed in via `${{ github.event.pull_request.base.sha }}`).
   - Local: default `merge-base origin/main HEAD` if `--base` is omitted.
3. `git show <base>:requirements-release.txt` -> base lockfile text. Tolerant of `--base` referring to a commit where the file doesn't exist yet (Phase 102 introduced it; pre-Phase-102 bases are treated as empty).
4. Diff via `_dep_admit_common.diff_lockfile_against_base`.
5. For each bump:
   - Query `https://pypi.org/pypi/<name>/<new_version>/json` for `urls[0].upload_time_iso_8601`.
   - Compute age in days vs `now` (UTC).
   - If `age_days < 14`: candidate violation.
6. For each candidate violation, check `parse_override_entries(META_LEDGER)` for a matching `package@version` override entry.
7. Emit:
   - stderr summary line per violation: `WARN: <pkg>@<version> uploaded <N> days ago (within 14d window); override absent`.
   - stdout markdown table summarizing all bumps (column: name, version, age_days, status=`override|violation|clean`).
   - Exit 0 if no violations, 1 if at least one violation absent override.

Network behavior: PyPI query uses `urllib.request` (stdlib), with bounded retry (3 attempts at 5s intervals = 15s budget per package). Graceful network failure: emits `ERROR: PyPI query for <pkg>@<version> failed: <reason>` and exits 2 (distinct from violation exit 1) so CI can distinguish.

CI wiring is WARN-only at first rollout (per Phase 99 V2 ramp pattern):

```yaml
      - name: Dependency admission cooling-period check (WARN-only)
        if: github.event_name == 'pull_request'
        run: |
          python -m qor.scripts.dependency_admission_lint \
            --base "${{ github.event.pull_request.base.sha }}" \
            || true
```

The `|| true` wrap is the WARN-only ramp; a V2 phase will flip it to hard fail after operator-evidence accumulates.

### Tracker (`qor/scripts/dep_admit_override_tracker.py`)

Operator-invokable only (no CI wiring). Flow:

1. Read `docs/META_LEDGER.md`.
2. `parse_override_entries(text)` -> list of overrides with their `entry_ts`.
3. For each override:
   - Compute `(now - entry_ts).days` -> `age_days`.
   - Status:
     - `due` if `age_days >= 30` (re-evaluation overdue per Phase 103 doctrine).
     - `pending` if `0 <= age_days < 30` (within follow-up window).
4. Emit:
   - stdout markdown table with columns: `package`, `version`, `entry_ts`, `age_days`, `status`, `justification`.
   - Exit 0 always (informational tool; non-zero would be misleading for "0 due-for-review" cases).

CLI flags: `--format markdown|csv` (default markdown), `--filter due|pending|all` (default all), `--since YYYY-MM-DD` (only entries newer than).

### Doctrine update

Append a brief note at the end of `qor/references/doctrine-dependency-admission.md` `### Check mechanic` subsection pointing operators at the tool:

> **Phase 105 tooling (V1, WARN-only)**: `python -m qor.scripts.dependency_admission_lint --base <ref>` runs the cooling-period check against the lockfile diff; `python -m qor.scripts.dep_admit_override_tracker` lists overrides due for 30-day re-evaluation. The lint runs WARN-only in `pr-dependency-review.yml` on PRs touching `requirements-release.txt`. V2 will flip the WARN to hard fail once operator-evidence on false-positive rate accumulates.

### Test surface

12 tests across 3 new test files. All tests use mocked PyPI responses + in-memory ledger fixtures; no live network or filesystem dependencies outside the repo.

1. `tests/test_dep_admit_common.py` (NEW, 4 tests)
   - `test_parse_lockfile_entries_extracts_name_version_hashes` -- parses the actual `requirements-release.txt` shape and asserts `LockfileEntry` fields match the pip-compile output.
   - `test_parse_lockfile_entries_rejects_malformed_input` -- explicit assertion that bad input raises a named exception (catches silent corruption).
   - `test_diff_lockfile_returns_new_and_bumped_entries` -- given two lockfile sets, asserts new entries appear with `old_version=None` and bumped entries appear with `old_version` populated.
   - `test_parse_override_entries_extracts_package_version_justification` -- given a synthetic ledger fragment, asserts overrides are parsed with all required fields.

2. `tests/test_dependency_admission_lint.py` (NEW, 5 tests)
   - `test_lint_emits_no_violation_when_all_bumps_outside_window` -- bumps with `age_days >= 14`, exit 0, stderr empty.
   - `test_lint_emits_violation_when_within_window_and_no_override` -- one bump with `age_days = 5`, no matching ledger override, exit 1, stderr names the package.
   - `test_lint_clears_violation_when_override_entry_present` -- same bump but ledger has matching override, exit 0, stdout marks the bump as `override`.
   - `test_lint_handles_pypi_network_failure_with_exit_2` -- mock 3 consecutive failures, assert exit 2 + stderr names the package + reason.
   - `test_lint_handles_pre_phase102_base_with_no_lockfile` -- base ref where `requirements-release.txt` doesn't exist; lint treats it as empty base; all current entries count as new for age check.

3. `tests/test_dep_admit_override_tracker.py` (NEW, 3 tests)
   - `test_tracker_marks_overrides_older_than_30_days_as_due` -- synthetic ledger with entry timestamped 35 days ago + entry 10 days ago; assert tracker output marks them `due` and `pending` respectively.
   - `test_tracker_filter_due_excludes_pending_entries` -- with `--filter due`, only overdue entries appear in output.
   - `test_tracker_markdown_output_has_required_columns` -- output contains the column headers `package | version | entry_ts | age_days | status | justification`.

## Phase 1: shared helper + lint + tracker + CI wiring + doctrine note + tests

### Affected Files

- `qor/scripts/_dep_admit_common.py` -- NEW. ~80 lines. Three pure parsing functions.
- `qor/scripts/dependency_admission_lint.py` -- NEW. ~120 lines. argv-form argparse; uses `urllib.request` for PyPI Warehouse query; bounded retry; markdown + stderr output.
- `qor/scripts/dep_admit_override_tracker.py` -- NEW. ~80 lines. argv-form argparse; markdown/csv output.
- `.github/workflows/pr-dependency-review.yml` -- AMENDED. Add WARN-only lint step after the existing `dependency-review-action` step.
- `qor/references/doctrine-dependency-admission.md` -- AMENDED. Append the Phase 105 tooling note under `### Check mechanic`.
- `tests/test_dep_admit_common.py` -- NEW. 4 tests.
- `tests/test_dependency_admission_lint.py` -- NEW. 5 tests.
- `tests/test_dep_admit_override_tracker.py` -- NEW. 3 tests.
- `docs/plan-qor-phase105-dependency-admission-tooling.md` -- NEW. This plan.

### Unit Tests

See the Test surface section. 12 tests total. Each test invokes the unit and asserts on its output -- behavioral, not presence-only. Network calls in lint tests are mocked via `monkeypatch` against `urllib.request.urlopen`.

### Changes

#### `qor/scripts/_dep_admit_common.py` (NEW)

```python
"""Phase 105: shared helpers for dependency-admission tooling."""
from __future__ import annotations

import dataclasses
import re
from datetime import datetime, timezone
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class LockfileEntry:
    name: str
    version: str
    hashes: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class Bump:
    name: str
    old_version: str | None  # None for newly-added entries
    new_version: str


@dataclasses.dataclass(frozen=True)
class OverrideEntry:
    package: str
    version: str
    entry_ts: datetime
    upload_age_days: int
    justification: str


def parse_lockfile_entries(text: str) -> list[LockfileEntry]:
    """Parse pip-compile --generate-hashes output. Tolerant of comment lines."""
    ...


def diff_lockfile_against_base(
    current: list[LockfileEntry], base: list[LockfileEntry]
) -> list[Bump]:
    """Returns new + version-bumped entries vs the base. Sorted by name."""
    ...


def parse_override_entries(ledger_text: str) -> list[OverrideEntry]:
    """Walks META_LEDGER for `**Dependency admission override**:` lines."""
    ...
```

#### `qor/scripts/dependency_admission_lint.py` (NEW)

Argparse interface:

```
usage: dependency_admission_lint.py [--base REF] [--lockfile PATH] [--ledger PATH]
                                    [--repo-root PATH] [--threshold-days INT]

  --base REF          Base ref to diff against (default: merge-base origin/main HEAD)
  --lockfile PATH     Lockfile path (default: requirements-release.txt)
  --ledger PATH       META_LEDGER path (default: docs/META_LEDGER.md)
  --repo-root PATH    Repo root (default: cwd)
  --threshold-days N  Cooling-period threshold (default: 14)
```

PyPI query helper uses `urllib.request` with `Request(...)`, 5s timeout per attempt, 3 retries:

```python
def _fetch_pypi_upload_time(pkg: str, version: str, retries: int = 3) -> datetime:
    url = f"https://pypi.org/pypi/{pkg}/{version}/json"
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "qor-logic/dep-admit-lint"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.load(resp)
            upload_time = data["urls"][0]["upload_time_iso_8601"]
            return datetime.fromisoformat(upload_time.replace("Z", "+00:00"))
        except (urllib.error.URLError, KeyError, IndexError) as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(5)
    raise NetworkError(f"PyPI query failed after {retries} attempts: {last_err}")
```

Output to stderr (per violation):

```
WARN: cyclonedx-bom@8.0.1 uploaded 3 days ago (within 14d window); override absent
```

Output to stdout (markdown summary table):

```
| Package | Version | Age (days) | Status |
|---|---|---|---|
| cyclonedx-bom | 8.0.1 | 3 | violation |
| lxml | 6.2.0 | 21 | clean |
```

Exit codes: 0 = clean, 1 = violations present, 2 = network/setup error.

#### `qor/scripts/dep_admit_override_tracker.py` (NEW)

```
usage: dep_admit_override_tracker.py [--ledger PATH] [--format markdown|csv]
                                     [--filter due|pending|all] [--since YYYY-MM-DD]
                                     [--follow-up-days INT]

  --ledger PATH         META_LEDGER path (default: docs/META_LEDGER.md)
  --format FMT          Output format (default: markdown)
  --filter STATE        Show only entries in this state (default: all)
  --since DATE          Only entries newer than this date
  --follow-up-days N    Follow-up threshold (default: 30)
```

Output (markdown default):

```
| Package | Version | Entry timestamp | Age (days) | Status | Justification |
|---|---|---|---|---|---|
| openssl-py | 3.1.4 | 2026-04-15T12:00:00Z | 40 | due | CVE-2026-1234 patch |
| requests | 2.32.0 | 2026-05-20T08:00:00Z | 5 | pending | upstream maintainer-coordinated release |
```

Exit code: always 0 (informational).

#### `.github/workflows/pr-dependency-review.yml` (AMENDED)

Add WARN-only step after the dependency-review-action invocation:

```yaml
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065  # v5.6.0
        with:
          python-version: "3.12"
      - run: pip install -e .
      - name: Dependency admission cooling-period check (WARN-only)
        run: |
          python -m qor.scripts.dependency_admission_lint \
            --base "${{ github.event.pull_request.base.sha }}" \
            || true
```

The `|| true` is the V1 WARN-only ramp; a future V2 phase removes it after operator-evidence on false-positive rate accumulates.

#### `qor/references/doctrine-dependency-admission.md` (AMENDED)

Appended near the end of `### Check mechanic`:

```markdown
**Phase 105 tooling (V1, WARN-only)**: `python -m qor.scripts.dependency_admission_lint --base <ref>` runs the cooling-period check against the lockfile diff; `python -m qor.scripts.dep_admit_override_tracker` lists overrides due for 30-day re-evaluation. The lint runs WARN-only in `pr-dependency-review.yml` on PRs touching `requirements-release.txt`. V2 will flip the WARN to hard fail once operator-evidence on false-positive rate accumulates.
```

## Definition of Done

### Deliverable D-105.1: shared parsing helpers

- **D1**: `qor/scripts/_dep_admit_common.py` exports `LockfileEntry`, `Bump`, `OverrideEntry`, `parse_lockfile_entries`, `diff_lockfile_against_base`, `parse_override_entries`.
- **D2**: All four `test_dep_admit_common.py` tests pass twice deterministically.

### Deliverable D-105.2: dependency-admission lint

- **D1**: `qor/scripts/dependency_admission_lint.py` exists with the argparse interface declared above; importable as `python -m qor.scripts.dependency_admission_lint`.
- **D2**: All five `test_dependency_admission_lint.py` tests pass twice deterministically. PyPI calls mocked via `monkeypatch`.
- **D3**: `.github/workflows/pr-dependency-review.yml` carries the WARN-only step invoking the lint with `--base ${{ github.event.pull_request.base.sha }}` and `|| true`.

### Deliverable D-105.3: dep-admit-override tracker

- **D1**: `qor/scripts/dep_admit_override_tracker.py` exists with the argparse interface declared above; importable as `python -m qor.scripts.dep_admit_override_tracker`.
- **D2**: All three `test_dep_admit_override_tracker.py` tests pass twice deterministically.

### Deliverable D-105.4: doctrine additive note

- **D1**: `qor/references/doctrine-dependency-admission.md` `### Check mechanic` subsection carries the Phase 105 tooling note.

## CI Coverage Exemptions

None.

## CI Commands

- `python -m qor.scripts.dependency_admission_lint --base <ref>` -- pr-dependency-review.yml WARN-only step invoking the new lint.
- `python -m pytest tests/test_dep_admit_common.py -q` -- Phase 105 shared-helper tests.
- `python -m pytest tests/test_dependency_admission_lint.py -q` -- Phase 105 lint tests.
- `python -m pytest tests/test_dep_admit_override_tracker.py -q` -- Phase 105 tracker tests.
- `python -m pytest tests/ -v` -- full regression.
- `python qor/scripts/check_variant_drift.py` -- ci.yml.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` -- ci.yml.
- `python -m pytest tests/test_packaging_install.py -v -m integration` -- install-smoke.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` -- gate-chain.
- `python qor/scripts/pr_citation_lint.py` -- pr-lint.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase105-dependency-admission-tooling.md` -- plan-internal.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase105-dependency-admission-tooling.md --workflows-dir .github/workflows` -- Phase 89 ci-coverage.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase105-dependency-admission-tooling.md` -- Phase 92 DoD check.
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` -- Phase 95 skill-corpus-budget lint (WARN-only).
