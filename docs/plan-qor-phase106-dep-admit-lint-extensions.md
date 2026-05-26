# Plan: Phase 106 — dependency-admission lint V1.1 extensions (v0.74.0)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: Phase 105 V2 carry-forward (3 of 5 items). Phase 105 shipped V1 of the cooling-period lint + override tracker with documented carry-forward for PR-label override detection (item 2), broader `pyproject.toml` coverage (item 3), and session-ID convention enforcement (item 6). Phase 106 ships items 2 + 3 + 6 as a cohesive lint V1.1 surface. Items 1 (WARN→hard-fail flip) and 5 (broaden CODEOWNERS pool) have legitimate blockers (operator-evidence accumulation, maintainer-team provisioning) and remain carry-forward.

**terms_introduced**:
- term: PR-label override
  home: qor/references/doctrine-dependency-admission.md
- term: pyproject exact-pin admission
  home: qor/references/doctrine-dependency-admission.md
- term: session ID convention lint
  home: qor/references/doctrine-governance-enforcement.md

**boundaries**:
- limitations: Three additive extensions to the Phase 105 lint surface. (1) **PR-label override** -- when `dependency_admission_lint.py` runs in CI context (detected via `GITHUB_EVENT_NAME == 'pull_request'` + `GITHUB_REPOSITORY` + PR number from `GITHUB_REF`), it invokes `gh pr view <number> --repo <owner>/<repo> --json labels` and treats the presence of the `dep-admit-override` label as an override signal (in addition to the existing META_LEDGER override check). New `--skip-pr-labels` flag lets operators bypass the gh query in local testing. Fails open: any non-zero gh exit logs a stderr note and falls back to META_LEDGER-only. (2) **pyproject.toml exact-pin coverage** -- new `parse_pyproject_exact_pins(text)` in `_dep_admit_common.py` extracts `[project] dependencies` and `[project.optional-dependencies]` entries matching `package==X.Y.Z` (PEP 440 exact-pin form only); range pins (`>=4`, `~=2.1`) and unbounded names are skipped. The lint's diff now considers both lockfile changes AND pyproject exact-pin changes. (3) **Session ID convention lint** -- new `qor/scripts/session_id_lint.py` emits a stderr WARN (non-blocking) when the active session ID doesn't match `SESSION_ID_PATTERN`. Wired into `/qor-substantiate` Step 4.6 between intent_lock verify and skill_admission. Doctrine note added to `doctrine-governance-enforcement.md` documenting the canonical 6-hex slug format.
- non_goals: WARN -> hard-fail flip on the cooling-period lint (Phase 105 carry-forward item 1; requires operator-evidence on false-positive rate that V1.1 begins accumulating); broadening CODEOWNERS reviewer pool (Phase 101 carry-forward item 5; needs an actual maintainer team in GitHub); calendar / GH-issue integration for the override tracker; `cyclonedx-bom` hash-pinning (Phase 102 carry-forward; Razor file-budget concern unchanged; deferred to its own cycle).
- exclusions: no changes to the V1 lint exit-code semantics (0/1/2); no changes to the V1 override-tracker behavior; no changes to the `pr-dependency-review.yml` workflow trigger paths (still triggers on `pyproject.toml` + `requirements-release.txt` + `.github/workflows/**`); no changes to the 14-day cooling-period threshold or 30-day re-evaluation window.

**high_risk_target**: false

## Open Questions

None. User confirmed all three implementation choices via /qor-plan dialogue: gh CLI for PR-label query (fails open), exact-pin-only pyproject coverage, WARN-only session ID lint at substantiate time.

## Feature Inventory Touches

Empty. Tooling + workflow + doctrine extensions.
`feature_inventory_touches`: `[]`.

## Design notes

### PR-label override

The Phase 105 lint already checks META_LEDGER for `**Dependency admission override**:` entries. Phase 106 adds a second signal: the GitHub PR label `dep-admit-override`. Either signal clears a within-window admission.

CI context detection uses the standard GitHub Actions env vars:
- `GITHUB_EVENT_NAME == "pull_request"`
- `GITHUB_REPOSITORY` ("owner/name")
- `GITHUB_REF` for PR number (`refs/pull/<n>/merge`)

When all three are present, the lint shells out to `gh pr view <n> --repo <owner>/<name> --json labels`. The gh CLI is pre-installed on GitHub Actions runners and the default GITHUB_TOKEN has read access to PR labels.

Fails-open semantics: if `gh` exits non-zero (network glitch, token issue, etc.), the lint emits a stderr note `"WARN: PR label query failed; falling back to META_LEDGER-only override check"` and continues. This is intentional -- a failed label query must not introduce a spurious within-window violation when the operator has done the right thing via ledger entry. Phase 105's three-way exit semantics (0/1/2) are preserved; exit 2 is reserved for PyPI Warehouse network failure only.

A new `--skip-pr-labels` flag lets operators bypass the gh query when testing locally with PR context env vars set.

### pyproject.toml exact-pin coverage

The Phase 105 lint operates only on `requirements-release.txt` (the hash-pinned build lockfile). Phase 106 broadens to also scan `[project] dependencies` and `[project.optional-dependencies]` in `pyproject.toml`. The lint parses each entry; only those matching the PEP 440 exact-pin form (`package==X.Y.Z`) are checked. Range pins (`>=4`, `~=2.1`, `<5`) and unbounded specifiers (`requests`) are skipped because the resolved version is not knowable until install time -- checking them would either inflate false-positive rate (assume the version that pip-compile picked) or be operationally useless.

`qor-logic` today carries only range-pinned deps (`jsonschema>=4`, `PyYAML>=6`), so V1.1 lint output against the current pyproject is the empty set. The check becomes operative the first time a maintainer pins an exact version -- which is precisely when cooling-period attention is warranted (an explicit pin is an explicit admission decision).

`parse_pyproject_exact_pins(text)` is a new pure function in `_dep_admit_common.py` returning `[LockfileEntry]` (re-using the existing dataclass; `hashes` will be the empty tuple for pyproject entries). The lint's diff loop treats lockfile entries and pyproject entries identically once parsed.

### Session ID convention lint

`session.current()` returns `None` when `.qor/session/current` doesn't match `SESSION_ID_PATTERN`, and downstream tooling silently falls back to the string `"default"`. The fall-through is operationally benign (intent_lock and procedural_fidelity still work under the default session) but produces fragmented event provenance: events from a non-conforming session land under `default` rather than the operator's intended slug. Phase 106 surfaces the mismatch with a WARN.

New `qor/scripts/session_id_lint.py` (~40 lines) reads `.qor/session/current`, compares against the pattern, emits stderr WARN if non-conforming, and exits 0 (non-blocking). Wired into `/qor-substantiate` Step 4.6 as an additional command between `intent_lock verify` and `skill_admission`. The WARN message names the canonical 6-hex format and points operators at `session.rotate()` for compliant generation.

Pattern formal: `^\d{4}-\d{2}-\d{2}T\d{4}-[0-9a-f]{6}$` (e.g., `2026-05-25T2035-c8f105`). Documented in `qor/references/doctrine-governance-enforcement.md`.

### Test surface

8 new tests across two new files + amendments to two existing test files.

1. `tests/test_dep_admit_common.py` (amended)
   - `test_parse_pyproject_exact_pins_extracts_pinned_entries` -- given a synthetic `[project] dependencies` block with mixed forms (exact, range, unbounded), assert only `==`-pinned entries are returned with correct name + version.
   - `test_parse_pyproject_exact_pins_handles_optional_dependencies` -- assert entries from `[project.optional-dependencies]` groups are included.
   - `test_parse_pyproject_exact_pins_returns_empty_for_no_exact_pins` -- assert qor-logic's current pyproject (range-only) returns the empty list.

2. `tests/test_dependency_admission_lint.py` (amended)
   - `test_lint_pr_label_override_clears_within_window` -- mock `subprocess.run` for gh CLI to return a label list containing `dep-admit-override`; assert a within-window bump is reported as `override` status (exit 0).
   - `test_lint_pr_label_query_fails_open_to_ledger_only` -- mock gh to exit non-zero; assert lint continues with META_LEDGER-only check and emits the documented stderr fallback note.
   - `test_lint_pyproject_exact_pin_within_window_triggers_violation` -- synthetic pyproject diff with a within-window `==`-pinned entry; assert exit 1 + violation.

3. `tests/test_session_id_lint.py` (NEW)
   - `test_session_id_lint_emits_warn_when_pattern_mismatch` -- write a non-conforming session marker; invoke lint; assert stderr names the pattern + exits 0.
   - `test_session_id_lint_silent_when_pattern_matches` -- write a conforming marker; invoke lint; assert stderr empty + exit 0.

All tests invoke the unit and assert on output -- behavioral, surviving the SG-035 acceptance question.

## Phase 1: parser extension + lint extensions + session lint + tests

### Affected Files

- `qor/scripts/_dep_admit_common.py` -- amended. Add `parse_pyproject_exact_pins(text) -> list[LockfileEntry]` (~25 lines).
- `qor/scripts/dependency_admission_lint.py` -- amended. Add CI-mode PR-label query (`_query_pr_labels` ~20 lines) + `--skip-pr-labels` flag + integrate pyproject parsing into the diff loop (~15 lines). Argparse adds `--pyproject` (default `pyproject.toml`) + `--skip-pr-labels`.
- `qor/scripts/session_id_lint.py` -- NEW. ~40 lines. argparse: `--marker PATH` (default `.qor/session/current`).
- `qor/skills/governance/qor-substantiate/SKILL.md` -- amended. Step 4.6 gains a 4th line invoking `python -m qor.scripts.session_id_lint` (between intent_lock verify and skill_admission).
- `qor/references/doctrine-dependency-admission.md` -- amended. Append Phase 106 note under `### Check mechanic` documenting the PR-label override + pyproject exact-pin coverage extensions.
- `qor/references/doctrine-governance-enforcement.md` -- amended. New short subsection "Session ID convention" documenting the regex format + the `session_id_lint` WARN surface.
- `qor/references/glossary.md` -- 3 new term entries (`PR-label override`, `pyproject exact-pin admission`, `session ID convention lint`).
- `tests/test_dep_admit_common.py` -- amended. +3 tests.
- `tests/test_dependency_admission_lint.py` -- amended. +3 tests.
- `tests/test_session_id_lint.py` -- NEW. 2 tests.
- `docs/plan-qor-phase106-dep-admit-lint-extensions.md` -- NEW. This plan.
- `docs/plan-qor-phase89-ci-commands-reconciliation.md` -- amended. Forward-maintenance bullet for `python -m qor.scripts.session_id_lint` (new operator-runnable Python invocation; same pattern as the Phase 105 forward-maintenance for `dependency_admission_lint`).

### Unit Tests

See "Test surface" section above. 8 new tests total. All tests use `monkeypatch` for gh CLI + urllib mocks; no live network or filesystem dependencies outside the repo and tmp_path fixtures.

### Changes

#### `qor/scripts/_dep_admit_common.py` (amend)

Add to imports: `tomllib` (Python 3.11+ stdlib).

```python
def parse_pyproject_exact_pins(text: str) -> list[LockfileEntry]:
    """Extract `==X.Y.Z` exact pins from pyproject [project].dependencies
    and [project.optional-dependencies].*. Range / unbounded forms skipped.

    Returns LockfileEntry instances with empty hashes tuple (pyproject deps
    are not hash-pinned at this layer).
    """
    data = tomllib.loads(text)
    pins: list[LockfileEntry] = []
    project = data.get("project") or {}
    deps_lists = [project.get("dependencies") or []]
    for group in (project.get("optional-dependencies") or {}).values():
        deps_lists.append(group)
    pin_re = re.compile(r"^([a-zA-Z0-9][a-zA-Z0-9._-]*)\s*==\s*([0-9][^\s;,]*)\s*$")
    for deps in deps_lists:
        for entry in deps:
            m = pin_re.match(str(entry).strip())
            if m:
                pins.append(
                    LockfileEntry(name=m.group(1).lower(), version=m.group(2), hashes=())
                )
    return pins
```

#### `qor/scripts/dependency_admission_lint.py` (amend)

New CI-mode label query helper:

```python
def _query_pr_labels(skip: bool = False) -> set[str] | None:
    """Returns set of label names on the active PR, or None if not in PR context
    or skip requested. Fails open: any error returns None (caller treats as
    'no label override available') rather than raising.
    """
    if skip:
        return None
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    ref = os.environ.get("GITHUB_REF", "")
    if event != "pull_request" or not repo:
        return None
    # GITHUB_REF for PRs is "refs/pull/<n>/merge"
    m = re.search(r"refs/pull/(\d+)/", ref)
    if not m:
        return None
    pr_num = m.group(1)
    try:
        out = subprocess.run(
            ["gh", "pr", "view", pr_num, "--repo", repo, "--json", "labels"],
            capture_output=True, text=True, check=True, timeout=10,
        )
        data = json.loads(out.stdout)
        return {lbl["name"] for lbl in data.get("labels", [])}
    except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"WARN: PR label query failed; falling back to META_LEDGER-only override check: {e}", file=sys.stderr)
        return None
```

Integration into `run_lint`: when a violation is candidate, check BOTH (a) ledger override and (b) `dep-admit-override` in PR labels. Either clears.

`main()` adds new flags: `--pyproject` (default `pyproject.toml`), `--skip-pr-labels`. The diff loop unions lockfile bumps + pyproject exact-pin bumps before the PyPI query loop.

#### `qor/scripts/session_id_lint.py` (NEW)

```python
"""Phase 106: WARN when the active session ID doesn't match SESSION_ID_PATTERN."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from qor.scripts.session import SESSION_ID_PATTERN


def lint(marker_path: Path) -> tuple[bool, str | None]:
    """Returns (conforming, message). Pure; no I/O beyond the marker read."""
    if not marker_path.is_file():
        return True, None  # no marker -> nothing to lint
    content = marker_path.read_text(encoding="utf-8").strip()
    if SESSION_ID_PATTERN.match(content):
        return True, None
    msg = (
        f"WARN: session ID {content!r} does not match SESSION_ID_PATTERN "
        f"'{SESSION_ID_PATTERN.pattern}'; intent_lock + procedural_fidelity "
        f"fall through to 'default'. Use session.rotate() to generate a compliant ID."
    )
    return False, msg


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--marker", default=".qor/session/current")
    args = p.parse_args(argv)
    ok, msg = lint(Path(args.marker))
    if msg:
        print(msg, file=sys.stderr)
    return 0  # non-blocking
```

#### `qor/skills/governance/qor-substantiate/SKILL.md` Step 4.6 (amend)

```bash
# Phase 106 wiring: WARN-only session ID convention lint
python -m qor.scripts.session_id_lint || true
```

Inserted between the existing `intent_lock verify` and `skill_admission` lines. The `|| true` is belt-and-suspenders (the script already exits 0 unconditionally) -- documents intent for future readers that this is non-blocking.

#### Doctrine + glossary additions

`doctrine-dependency-admission.md` adds a Phase 106 paragraph under `### Check mechanic`:

> **Phase 106 V1.1 extensions**: the lint now also accepts a `dep-admit-override` GitHub PR label as an override signal when running in CI context (queried via `gh pr view --json labels`; fails open to META_LEDGER-only on any error). The cooling-period check additionally walks `[project] dependencies` and `[project.optional-dependencies]` in `pyproject.toml`, applying the 14-day threshold to entries pinned in PEP 440 exact form (`package==X.Y.Z`); range and unbounded specifiers are skipped because the resolved version is not knowable until install time. Both extensions are additive on top of the V1 lockfile + ledger surface.

`doctrine-governance-enforcement.md` gains a new subsection "Session ID convention":

> Session IDs are the directory key under `.qor/gates/<sid>/` and the value written to `.qor/session/current`. The canonical format is `SESSION_ID_PATTERN = \d{4}-\d{2}-\d{2}T\d{4}-[0-9a-f]{6}` (e.g., `2026-05-25T2035-c8f105`). When a session ID doesn't match, `qor.scripts.session.current()` returns `None` and downstream tooling falls back to the string `"default"`, fragmenting event provenance. `qor.scripts.session_id_lint` emits a non-blocking stderr WARN at `/qor-substantiate` Step 4.6 when the active marker doesn't match. Generate compliant IDs via `session.rotate()`.

## Definition of Done

### Deliverable D-106.1: PR-label override

- **D1**: `dependency_admission_lint.py` carries `_query_pr_labels(skip)` returning `set[str] | None`; CI-context detection via `GITHUB_EVENT_NAME` + `GITHUB_REPOSITORY` + `GITHUB_REF`; fails open on any error.
- **D2**: `main()` accepts `--skip-pr-labels` flag.
- **D3**: `run_lint` clears candidate violations when either the META_LEDGER override or the `dep-admit-override` PR label is present.
- **D4**: `test_lint_pr_label_override_clears_within_window` + `test_lint_pr_label_query_fails_open_to_ledger_only` pass.

### Deliverable D-106.2: pyproject.toml exact-pin coverage

- **D1**: `_dep_admit_common.parse_pyproject_exact_pins(text) -> list[LockfileEntry]` exists; extracts `==X.Y.Z` from `[project] dependencies` and `[project.optional-dependencies]`; skips range / unbounded forms.
- **D2**: `dependency_admission_lint.run_lint` accepts a `pyproject_current_text` + `pyproject_base_text` pair and unions the resulting bumps with the lockfile bumps before PyPI query.
- **D3**: `test_parse_pyproject_exact_pins_extracts_pinned_entries`, `test_parse_pyproject_exact_pins_handles_optional_dependencies`, `test_parse_pyproject_exact_pins_returns_empty_for_no_exact_pins`, and `test_lint_pyproject_exact_pin_within_window_triggers_violation` pass.

### Deliverable D-106.3: session ID convention lint

- **D1**: `qor/scripts/session_id_lint.py` exists with `lint(marker_path) -> (ok, msg)` pure helper and an argv `main()` that exits 0.
- **D2**: `/qor-substantiate` Step 4.6 wires the lint between `intent_lock verify` and `skill_admission`.
- **D3**: `test_session_id_lint_emits_warn_when_pattern_mismatch` + `test_session_id_lint_silent_when_pattern_matches` pass.

## CI Coverage Exemptions

None.

## CI Commands

- `python -m qor.scripts.dependency_admission_lint --base <ref>` -- pr-dependency-review.yml WARN-only step (Phase 105; unchanged in Phase 106).
- `python -m qor.scripts.session_id_lint` -- /qor-substantiate Step 4.6 (Phase 106; WARN-only).
- `python -m pytest tests/test_dep_admit_common.py -q` -- amended Phase 105 + 106 helper tests.
- `python -m pytest tests/test_dependency_admission_lint.py -q` -- amended Phase 105 + 106 lint tests.
- `python -m pytest tests/test_session_id_lint.py -q` -- Phase 106 session ID lint tests.
- `python -m pytest tests/ -v` -- full regression.
- `python qor/scripts/check_variant_drift.py` -- ci.yml.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` -- ci.yml.
- `python -m pytest tests/test_packaging_install.py -v -m integration` -- install-smoke.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` -- gate-chain.
- `python qor/scripts/pr_citation_lint.py` -- pr-lint.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase106-dep-admit-lint-extensions.md` -- plan-internal.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase106-dep-admit-lint-extensions.md --workflows-dir .github/workflows` -- Phase 89 ci-coverage.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase106-dep-admit-lint-extensions.md` -- Phase 92 DoD check.
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` -- Phase 95 skill-corpus-budget lint (WARN-only).
