# Plan: Phase 52 — structural enforcement + retroactive remediation

**change_class**: feature
**target_version**: v0.38.0
**doc_tier**: standard
**pass**: 1

**Scope**: Consolidated remediation phase absorbing 6 deliverables surfaced by the three-skill audit corpus (RESEARCH_BRIEF + /qor-debug Phase 1+2 + /qor-audit retroactive on Phases 46/48/49/50/51-WIP). One branch (`phase/52-structural-enforcement-and-remediation`), one new version (v0.38.0). Supersedes Phase 51 WIP (which carried VETO grounds for infrastructure-mismatch and recursive SG-Phase47-A).

**Two structural deliverables, three retroactive remediations, one doctrine promotion, one CI gate, one G-1 closure.**

**Rationale**:

- **Root cause of session-wide bypass** (per /qor-debug Phase 1): `qor/scripts/gate_chain.py:115` `write_gate_artifact()` accepts payloads from any caller without provenance binding; no `.qor/gates/<sid>/*.json` artifacts exist anywhere in repo history (`git log --diff-filter=A --name-only --all -- ".qor/gates/"` returns 0 hits). Phase 47's `seal_entry_check` verifies the ledger but not the gate chain. Without a structural enforcement layer, every future phase is silently bypassable.

- **G-1 SSDF tag emission** (originally Phase 51 scope): the v0.32.0+ PyPI publishes ship with zero `**SSDF Practices**:` tags despite Phase 23 doctrine declaring the contract. `qor.cli compliance report` reports "Coverage: 0". External NIST auditors see no per-decision evidence.

- **Three retroactive VETO mandates** from /qor-audit corpus review: Phase 46 razor-overage (test file 285 > 250 lines); Phase 48 presence-only test (substring check, never invokes unit); Phase 49 self-exempting cutoff (lint vacuous at first run because cutoff exempts the only commits in scope at write time).

**terms_introduced**:
- term: gate-chain completeness check
  home: qor/reliability/gate_chain_completeness.py
- term: skill-active provenance
  home: qor/scripts/gate_chain.py
- term: SSDF tag emission
  home: qor/scripts/ssdf_tagger.py
- term: vacuous cutoff lint
  home: qor/references/doctrine-shadow-genome-countermeasures.md

**boundaries**:
- limitations: SSDF tag emission is forward-only from Phase 52 seal entry forward (immutable Merkle chain forbids retroactive edit of historical entries; Phase 47 `seal_entry_check` would reject any rebuild). Gate-chain completeness check applies to phases ≥ 52 only; existing phases 1-51 grandfathered. `QOR_SKILL_ACTIVE` env var is operator-set or harness-set; this plan does NOT modify the Claude Code harness — `write_gate_artifact` simply refuses to write when env var missing/wrong. The operator's documented workflow is "set env, then invoke skill."
- non_goals: rewriting the Merkle chain; auto-running gate-chain completeness on PRs targeting other branches (main-targeting only); promoting `gate_chain.write_gate_artifact` from advisory to interdiction at every call site (skills already define their own write call in Step Z; we add provenance at the helper, not the call sites).
- exclusions: `intent_lock` provenance binding (sibling problem; separate phase per /qor-debug F3); `workflow-bundles.md` enforcement (per /qor-debug F4, separate); F8 cleanup of stale `.qor/gates/sess-12345/` test pollution (cosmetic, separate); F4 `gate_override` event-emission test on real overrides (auto-resolves once runtime fires real overrides post-Phase-52).

## Open Questions

None.

---

## Phase 1: Structural enforcement (the keystone)

The two structural primitives that make the bypass mechanically catchable. Lands first; downstream phases depend on it.

### Affected Files

Tests authored first (TDD; verified RED before any source edit):

- `tests/test_gate_chain_provenance.py` — new. 6 tests for `QOR_SKILL_ACTIVE` provenance binding on `write_gate_artifact`. All invoke the helper directly and assert on returned/raised values.
- `tests/test_gate_chain_completeness.py` — new. 8 tests for `qor.reliability.gate_chain_completeness.check()` against synthetic-fixture sessions (clean / missing-audit / missing-implement / chain-discontinuity).

Source (in TDD order):

- `qor/reliability/gate_chain_completeness.py` — new ~110 lines. Pure functions: `check(repo_root, session_id, base_ref) -> CompletenessResult`; reads ledger entries on the branch, extracts referenced session_ids, asserts all four artifacts (`plan|audit|implement|substantiate`).json) exist for each sealed phase. CLI entrypoint `python -m qor.reliability.gate_chain_completeness`.
- `qor/scripts/gate_chain.py` — modified. `write_gate_artifact()` reads `os.environ.get("QOR_SKILL_ACTIVE")` and refuses (raises `ProvenanceError`) if unset or doesn't match `phase` argument. Backwards-compat env var `QOR_GATE_PROVENANCE_OPTIONAL=1` permits soft-mode for tests + grandfathered fixtures (set in `tests/conftest.py` for the test suite; production refuses without the gate).

### Changes

#### 1. `qor/reliability/gate_chain_completeness.py` (new)

Pure-function module, no I/O outside `pathlib` reads + `subprocess` for git. Section 4 Razor compliant: `check()` ~30 lines, all helpers ≤ 25 lines, max nesting 2.

```python
"""Phase 52: gate-chain completeness verifier.

Walks ledger entries on the current branch since divergence from base_ref;
extracts session_ids from SESSION SEAL entries; asserts each sealed phase
has plan/audit/implement/substantiate.json gate artifacts. ABORTs the
caller (typically /qor-substantiate Step 7.8 or pre-merge CI) on any gap.

Closes the bypass surface where Phases 46/48/49/50 sealed without
writing gate artifacts at all.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_PHASES = ("plan", "audit", "implement", "substantiate")
SESSION_LINE_RE = re.compile(r"^\*\*Session\*\*:\s*`?([0-9a-zA-Z-]+)`?", re.MULTILINE)
SEAL_HEADER_RE = re.compile(r"^### Entry #(\d+):\s*SESSION SEAL", re.MULTILINE)
PHASE_NUM_RE = re.compile(r"Phase\s+(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class CompletenessResult:
    ok: bool
    missing: list[tuple[int, str]]   # (phase_num, missing_artifact)
    sessions_checked: list[str]


def _phase_seal_session_ids(ledger_path: Path, phase_min: int) -> dict[int, str]:
    """Extract {phase_num: session_id} from SESSION SEAL entries with phase >= phase_min."""
    text = ledger_path.read_text(encoding="utf-8")
    out: dict[int, str] = {}
    parts = re.split(r"^### Entry #\d+:\s*SESSION SEAL", text, flags=re.MULTILINE)
    headers = SEAL_HEADER_RE.findall(text)
    for entry_num, body in zip(headers, parts[1:]):
        phase_match = PHASE_NUM_RE.search(body[:500])
        sess_match = SESSION_LINE_RE.search(body[:1500])
        if phase_match and sess_match:
            phase_num = int(phase_match.group(1))
            if phase_num >= phase_min:
                out[phase_num] = sess_match.group(1)
    return out


def check(
    repo_root: Path,
    *,
    phase_min: int = 52,
    ledger_path: Path | None = None,
    gates_root: Path | None = None,
) -> CompletenessResult:
    """Assert every sealed phase >= phase_min has plan/audit/implement/substantiate.json."""
    ledger = ledger_path or repo_root / "docs" / "META_LEDGER.md"
    gates = gates_root or repo_root / ".qor" / "gates"
    if not ledger.is_file():
        return CompletenessResult(ok=False, missing=[(0, f"ledger missing: {ledger}")], sessions_checked=[])
    by_phase = _phase_seal_session_ids(ledger, phase_min)
    missing: list[tuple[int, str]] = []
    for phase_num, sid in sorted(by_phase.items()):
        sess_dir = gates / sid
        for required in REQUIRED_PHASES:
            artifact = sess_dir / f"{required}.json"
            if not artifact.is_file():
                missing.append((phase_num, f"{sid}/{required}.json"))
    return CompletenessResult(ok=not missing, missing=missing, sessions_checked=list(by_phase.values()))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--phase-min", type=int, default=52)
    args = ap.parse_args(argv)
    result = check(args.repo_root, phase_min=args.phase_min)
    if result.ok:
        print(f"OK: gate-chain complete for {len(result.sessions_checked)} sessions (phase >= {args.phase_min})")
        return 0
    print(f"FAIL: gate-chain incomplete; {len(result.missing)} missing artifacts:")
    for phase_num, what in result.missing:
        print(f"  phase {phase_num}: {what}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

#### 2. `qor/scripts/gate_chain.py` modification

Insert at top of `write_gate_artifact()`:

```python
def write_gate_artifact(phase: str, payload: dict, session_id: str | None = None) -> "Path":
    # Phase 52: provenance binding. Refuse writes from non-skill contexts.
    if not os.environ.get("QOR_GATE_PROVENANCE_OPTIONAL"):
        active = os.environ.get("QOR_SKILL_ACTIVE")
        if active is None:
            raise ProvenanceError(
                f"write_gate_artifact called without QOR_SKILL_ACTIVE env. "
                f"Set QOR_SKILL_ACTIVE=<phase> when invoking the skill, or "
                f"QOR_GATE_PROVENANCE_OPTIONAL=1 to bypass (tests only)."
            )
        if active != phase:
            raise ProvenanceError(
                f"QOR_SKILL_ACTIVE={active!r} but write_gate_artifact called "
                f"with phase={phase!r}; skill-phase mismatch."
            )
    # ... existing schema validation + atomic write ...
```

`ProvenanceError` is a new module-level exception class (5 lines):

```python
class ProvenanceError(Exception):
    """Raised when write_gate_artifact is called without QOR_SKILL_ACTIVE provenance."""
```

`tests/conftest.py` autouse fixture sets `QOR_GATE_PROVENANCE_OPTIONAL=1` for all test runs (so the existing 866 tests using `monkeypatch.setattr(GATES_DIR, tmp_path)` continue to function unmodified).

### Unit Tests

TDD order. Each test invokes the unit under test directly and asserts on output, per `qor/references/doctrine-test-functionality.md`. No self-exempting cutoffs. Tests authored RED first.

`tests/test_gate_chain_provenance.py` (new, ~140 lines, ≤250):

- `test_write_gate_artifact_refuses_without_qor_skill_active` — clear env, call `write_gate_artifact("plan", {...})`; assert `ProvenanceError` raised. Negative-path: with `QOR_GATE_PROVENANCE_OPTIONAL=1` set, the same call succeeds — confirms the bypass works for tests.
- `test_write_gate_artifact_refuses_when_qor_skill_active_mismatches` — set `QOR_SKILL_ACTIVE="audit"`, call `write_gate_artifact("plan", ...)`; assert `ProvenanceError` raised with mismatch message.
- `test_write_gate_artifact_succeeds_when_qor_skill_active_matches` — set `QOR_SKILL_ACTIVE="plan"`, call `write_gate_artifact("plan", valid_payload, session_id=sid)`; assert returned `Path` exists and contains the payload.
- `test_provenance_error_is_subclass_of_exception` — `assert issubclass(ProvenanceError, Exception)`.
- `test_qor_gate_provenance_optional_bypass` — `monkeypatch.setenv("QOR_GATE_PROVENANCE_OPTIONAL", "1")`, no `QOR_SKILL_ACTIVE`; call succeeds. Confirms test-suite bypass works.
- `test_provenance_check_does_not_consume_payload_or_session_args` — verify the new check is a guard (raises early, doesn't mutate args). Functional invocation; assert payload dict unmodified after `ProvenanceError`.

`tests/test_gate_chain_completeness.py` (new, ~180 lines, ≤250):

- `test_completeness_check_module_importable_with_canonical_api` — `from qor.reliability import gate_chain_completeness`; assert `callable(check)`, `callable(main)`.
- `test_check_returns_ok_for_clean_synthetic_session` — synthetic ledger with one Phase 52 SESSION SEAL referencing session `s52`; create `tmp_path/.qor/gates/s52/{plan,audit,implement,substantiate}.json`; call `check(tmp_path, phase_min=52)`; assert `result.ok is True` and `result.missing == []`.
- `test_check_reports_missing_audit_artifact` — same fixture but no `audit.json`; assert `result.ok is False` and `("audit.json" in m[1] for m in result.missing)`.
- `test_check_reports_missing_implement_artifact` — same shape, missing implement.
- `test_check_reports_missing_substantiate_artifact` — same shape, missing substantiate.
- `test_check_skips_phases_below_phase_min` — synthetic ledger with Phase 50 SESSION SEAL (no artifacts); `check(phase_min=52)` returns `ok=True` (Phase 50 grandfathered).
- `test_check_handles_missing_ledger_gracefully` — call against a tmp_path with no `docs/META_LEDGER.md`; assert `ok=False` with descriptive `missing` entry.
- `test_main_exit_codes_for_clean_and_failing_states` — invoke `main()` via `monkeypatch.chdir(tmp_path)` + arg parsing; assert exit 0 on clean, exit 1 on missing artifacts. Functional: invokes the CLI entry point.

Negative-path coverage by construction: every "missing artifact" test explicitly fabricates the missing condition and asserts `result.ok is False`. No self-exempting cutoffs (per `SG-VacuousLint` countermeasure introduced in Phase 3).

---

## Phase 2: SSDF tag emission + CI gate-chain-completeness check (closes G-1)

Builds on Phase 1's enforcement primitive. Forward-only emission per Merkle-chain immutability.

### Affected Files

Tests authored first:

- `tests/test_ssdf_tagger.py` — new. 8 tests for `qor.scripts.ssdf_tagger.compute_tags()` and `format_tag_line()`. Each invokes the unit and asserts on returned values.
- `tests/test_substantiate_step_7_4_ssdf_emission.py` — new. 4 defensive wiring tests with proximity-anchor + strip-and-fail per Phase 46 doctrine.
- `tests/test_compliance_report_post_phase52.py` — new. 2 tests with **fixture-based** positive-path (synthetic ledger with tags) — NOT pytest.skip on absence. Closes the SG-VacuousLint family preemptively.
- `tests/test_ci_workflow_gate_chain_completeness.py` — new. 2 tests verifying `.github/workflows/ci.yml` declares the new `gate-chain-completeness` job and runs `python -m qor.reliability.gate_chain_completeness` on PR + push events.

Source:

- `qor/scripts/ssdf_tagger.py` — new ~85 lines. Pure functions; pattern-rule + class-rule mapping.
- `qor/skills/governance/qor-substantiate/SKILL.md` — new Step 7.4 between existing Step 7 (Final Merkle Seal) and Step 7.5 (Version bump). Pure-Python invocation; **no `python -c "..."${VAR}"` interpolation** (per SG-Phase47-A countermeasure).
- `qor/skills/governance/qor-substantiate/SKILL.md` — new Step 7.8 between existing Step 7.7 (Phase 47 seal-entry-check) and Step 8 (Cleanup Staging). Invokes `python -m qor.reliability.gate_chain_completeness`.
- `qor/references/doctrine-nist-ssdf-alignment.md` — extend §"Evidence Collection" with "**Phase 52 wiring (forward-only emission)**" subsection.
- `qor/gates/chain.md` lines 34, 74 — replace "future wiring" / "future work" prose with "wired in Phase 52".
- `.github/workflows/ci.yml` — new `gate-chain-completeness` job runs on `push` to main and `pull_request` against main; invokes `python -m qor.reliability.gate_chain_completeness --phase-min 52`. Job in `paths-ignore: ['docs/archive/**']` per repo convention.

### Changes

#### 1. `qor/scripts/ssdf_tagger.py` (new)

```python
"""Phase 52: NIST SSDF practice tag emission.

Pure functions mapping (change_class, files_touched) to SSDF practice IDs
per qor/references/doctrine-nist-ssdf-alignment.md §"Evidence Collection".
Invoked by /qor-substantiate Step 7.4 to emit `**SSDF Practices**:` block
into SESSION SEAL entries before Merkle hash computation.

Forward-only: Phase 52+ entries get tags; Phase ≤ 51 entries grandfathered
(immutable Merkle chain forbids retroactive edit).
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

_PATTERN_RULES: list[tuple[re.Pattern, list[str]]] = [
    (re.compile(r"qor/skills/governance/qor-audit/"),       ["PW.4.1", "PS.3.2"]),
    (re.compile(r"qor/skills/governance/qor-substantiate/"), ["PS.2.1", "PW.4.1"]),
    (re.compile(r"qor/skills/governance/qor-validate/"),    ["PW.9.1"]),
    (re.compile(r"qor/skills/sdlc/qor-plan/"),              ["PW.1.1"]),
    (re.compile(r"qor/skills/sdlc/qor-implement/"),         ["PW.1.1", "PW.5.1"]),
    (re.compile(r"qor/scripts/(shadow_process|create_shadow_issue)|PROCESS_SHADOW_GENOME"), ["RV.1.1", "RV.1.2"]),
    (re.compile(r"qor/scripts/remediate_"),                 ["RV.2.1"]),
    (re.compile(r"qor/policies/.*\.cedar"),                 ["PW.7.1"]),
    (re.compile(r"qor/references/doctrine-"),               ["PO.1.3"]),
    (re.compile(r"qor/reliability/"),                       ["PS.3.1"]),
    (re.compile(r"qor/scripts/.*\.py$"),                    ["PW.5.1"]),
    (re.compile(r"^tests/test_"),                           ["PW.5.1"]),
]

_CLASS_RULES = {
    "feature":  ["PO.1.4", "PW.1.1"],
    "breaking": ["PO.1.4", "PW.1.1", "PW.4.1"],
    "hotfix":   ["RV.2.1"],
}


def compute_tags(change_class: str, files_touched: list[str], *, include_seal: bool = True) -> list[str]:
    tags: set[str] = set(_CLASS_RULES.get(change_class, []))
    for f in files_touched:
        norm = f.replace("\\", "/")
        for pattern, practices in _PATTERN_RULES:
            if pattern.search(norm):
                tags.update(practices)
    if include_seal:
        tags.add("PS.2.1")
    return sorted(tags)


def format_tag_line(tags: list[str]) -> str:
    return f"**SSDF Practices**: {', '.join(tags)}"


def files_touched_from_git(repo_root: Path, base_ref: str = "origin/main") -> list[str]:
    """Compute files_touched via `git diff --name-only base_ref...HEAD`.

    Replaces the VETO'd Phase 51 approach of reading from a non-existent
    gate_chain.read_phase_artifact('implement') artifact.
    """
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        cwd=str(repo_root), capture_output=True, text=True, check=False,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--change-class", required=True, choices=["feature", "breaking", "hotfix"])
    ap.add_argument("--files", help="comma-separated file list; if omitted, computed via git diff")
    ap.add_argument("--base-ref", default="origin/main")
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--include-seal", action=argparse.BooleanOptionalAction, default=True)
    args = ap.parse_args(argv)
    if args.files:
        files = [f.strip() for f in args.files.split(",") if f.strip()]
    else:
        files = files_touched_from_git(args.repo_root, args.base_ref)
    tags = compute_tags(args.change_class, files, include_seal=args.include_seal)
    print(format_tag_line(tags))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

#### 2. `/qor-substantiate` Step 7.4 (between Step 7 and Step 7.5)

Pure-Python invocation. **No bash variable interpolation into Python literals** (per SG-Phase47-A countermeasure):

```bash
# Compute SSDF tag line (Phase 52 wiring; G-1 closure).
# Invokes pure-python helper directly; files_touched derived from git diff.
# No shell-variable interpolation into python -c literals.
SSDF_LINE=$(python -m qor.scripts.ssdf_tagger \
  --change-class "$CHANGE_CLASS" \
  --base-ref origin/main \
  --repo-root .)
# Operator pastes $SSDF_LINE into the SESSION SEAL entry body before the
# content_hash and chain_hash are computed in Step 7.
echo "$SSDF_LINE"
```

The `$CHANGE_CLASS` shell variable is consumed only as an argv argument to a Python module — never interpolated into a `python -c "..."` literal. The Python module argparse-validates against a closed enum (`feature|breaking|hotfix`), eliminating the injection vector.

#### 3. `/qor-substantiate` Step 7.8 (between Step 7.7 and Step 8)

```bash
# Phase 52 wiring: gate-chain completeness check.
# ABORT seal if any sealed phase >= 52 lacks plan/audit/implement/substantiate.json.
QOR_SKILL_ACTIVE=substantiate python -m qor.reliability.gate_chain_completeness \
  --repo-root . \
  --phase-min 52 \
  || { echo "ABORT: gate-chain completeness violated; missing artifacts surface bypass"; exit 1; }
```

#### 4. `qor/gates/chain.md` lines 34 + 74

```diff
-## Skill integration (for future wiring)
+## Skill integration (Phase 52 wiring)
```

```diff
-Skill-layer enforcement (phase 3 provides the schema; skill wiring is future work).
+Skill-layer enforcement (Phase 52 wiring): `QOR_SKILL_ACTIVE` env-var provenance binding in `gate_chain.write_gate_artifact` + `gate_chain_completeness.check()` in /qor-substantiate Step 7.8 + pre-merge CI gate.
```

#### 5. `qor/references/doctrine-nist-ssdf-alignment.md` § Evidence Collection extension

Append:

```markdown
### Phase 52 wiring (forward-only emission)

Starting with Phase 52's SESSION SEAL entry (target #169), every SEAL entry carries `**SSDF Practices**: <tags>`. The tagger (`qor/scripts/ssdf_tagger.py`) computes practices from `change_class` + `files_touched` (derived via `git diff --name-only origin/main...HEAD`).

**Grandfathering**: entries < #169 do not carry tags. The Merkle chain is content-addressed and append-only; retroactive edits would invalidate the chain (Phase 47's `seal_entry_check` would reject the rebuild). `qor.cli compliance report` shows coverage starting from Phase 52's seal.

**Operator workflow**: at /qor-substantiate Step 7.4, the skill runs `python -m qor.scripts.ssdf_tagger --change-class <c>` and pastes the printed tag line into the SESSION SEAL entry body before content_hash is computed in Step 7.
```

#### 6. `.github/workflows/ci.yml` new `gate-chain-completeness` job

```yaml
  gate-chain-completeness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # need full history for git diff origin/main...HEAD
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -e .
      - name: Verify gate-chain completeness for sealed phases >= 52
        run: python -m qor.reliability.gate_chain_completeness --phase-min 52
```

Job is required for merges to main per the existing CI ruleset (operator authorizes once).

### Unit Tests

`tests/test_ssdf_tagger.py` (new, ~150 lines, ≤250):

- `test_tagger_module_importable` — assert `compute_tags`, `format_tag_line`, `files_touched_from_git`, `main` all callable.
- `test_compute_tags_feature_implementation_includes_pw_practices` — call with `("feature", ["qor/skills/sdlc/qor-implement/SKILL.md", "tests/test_x.py"])`; assert `"PW.1.1" in result and "PW.5.1" in result`.
- `test_compute_tags_breaking_change_includes_pw_4_1` — call with `("breaking", [])`; assert `"PW.4.1" in result`.
- `test_compute_tags_hotfix_includes_rv_2_1` — call with `("hotfix", [])`; assert `"RV.2.1" in result`.
- `test_compute_tags_audit_skill_change_includes_ps_3_2` — call with `("feature", ["qor/skills/governance/qor-audit/SKILL.md"])`; assert `"PS.3.2" in result`.
- `test_compute_tags_shadow_genome_change_includes_rv_practices` — call with `("feature", ["qor/scripts/shadow_process.py"])`; assert `"RV.1.1" in result and "RV.1.2" in result`.
- `test_format_tag_line_canonical_block` — `format_tag_line(["PW.1.1", "PS.2.1"])` returns exactly `"**SSDF Practices**: PS.2.1, PW.1.1"` (sorted).
- `test_extract_ssdf_practices_round_trips_emitted_block` — emit via `format_tag_line`, write to fixture, parse via `ledger_hash.extract_ssdf_practices`; assert round-trip equality.

`tests/test_substantiate_step_7_4_ssdf_emission.py` (new, ~120 lines, ≤250):

- `test_step_7_4_invokes_ssdf_tagger_module_form` — proximity-anchored on `### Step 7.4` header; assert phrase `python -m qor.scripts.ssdf_tagger` within span. Strip-and-fail negative-path paired.
- `test_step_7_4_does_not_use_python_c_shell_interpolation` — proximity-anchored; assert `python -c` does NOT appear within the Step 7.4 bash block (SG-Phase47-A countermeasure). Synthetic-fixture negative-path: assert a fabricated bash with `python -c "...${VAR}..."` would fail this check.
- `test_step_7_4_runs_between_step_7_and_step_7_5` — positional check: Step 7 < Step 7.4 < Step 7.5 header offsets in the skill body.
- `test_step_7_8_invokes_gate_chain_completeness` — proximity-anchored on `### Step 7.8` header; phrases `gate_chain_completeness`, `ABORT`, `phase-min 52` within span. Strip-and-fail.

`tests/test_compliance_report_post_phase52.py` (new, ~80 lines, ≤250):

- `test_compliance_report_finds_tags_in_synthetic_ledger_with_tags` — write a synthetic ledger to `tmp_path` with one entry containing `**SSDF Practices**: PW.1.1, PS.2.1`; invoke `qor.cli._do_compliance_report(ledger_path=tmp_ledger)`; assert returned report mentions `PW.1.1` and counts `>= 1`.
- `test_compliance_report_reports_zero_for_synthetic_ledger_without_tags` — synthetic ledger with no tag lines; assert returned report is `"No SSDF practice tags found in ledger. Coverage: 0"`. Functional: invokes the report function with controlled input.

NO `pytest.skip` in either test. Both invoke the unit with a fixture and assert on output. (Closes the SG-VacuousLint anti-pattern that was queued in Phase 51 WIP.)

`tests/test_ci_workflow_gate_chain_completeness.py` (new, ~60 lines, ≤250):

- `test_ci_workflow_declares_gate_chain_completeness_job` — parse `.github/workflows/ci.yml` via `yaml.safe_load`; assert `data["jobs"]["gate-chain-completeness"]` exists with non-empty `steps`.
- `test_ci_gate_chain_job_invokes_canonical_module` — assert any step's `run` contains `python -m qor.reliability.gate_chain_completeness`.

---

## Phase 3: Retroactive remediation + SG promotion (closes Phase 46/48/49 VETO mandates)

Targeted fixes for the three retroactive VETOes. Lands last; depends on Phase 1's helpers being available for any test that needs them.

### Affected Files

Tests authored first:

- `tests/test_attribution_tiered_negative_paths.py` — new. 4 fixture-based negative-path tests fabricating violating commit bodies and asserting the existing lints catch them. Closes SG-VacuousLint.
- `tests/test_install_drift_check_subprocess.py` — new. Replaces the presence-only test; subprocess-invokes `install_drift_check.main()` and captures stdout.

Source edits:

- `tests/_helpers.py` — new shared module (~70 lines, ≤250). Houses `_proximity()`, `_strip_section()`, `_fenced_block_after()` helpers extracted from `tests/test_doctrine_test_functionality.py`.
- `tests/test_doctrine_test_functionality.py` — refactored. Imports helpers from `tests._helpers`; reduces from 285 → ~210 lines (≤250). Splits the 20 test cases into 2 files if needed; preferred approach is helper extraction (single-file shrink).
- `tests/test_doctrine_test_functionality_negative_paths.py` — new. If single-file shrink doesn't get under 250, the 10 negative-path tests move here. Author after the helper extraction; only ship if needed.
- `tests/test_cli_rename.py::test_install_drift_check_emits_qor_logic_fix_string` — DELETED (replaced by `tests/test_install_drift_check_subprocess.py`).
- `qor/references/doctrine-shadow-genome-countermeasures.md` — append three new structured SG entries (`SG-SkillProtocolBypass`, `SG-VacuousLint`, `SG-RecursiveBashInjection`).

### Changes

#### 1. `tests/_helpers.py` (new shared module)

```python
"""Shared test helpers extracted to satisfy Section 4 Razor (file ≤ 250 lines)
on tests/test_doctrine_test_functionality.py and reusable across other lint tests.
"""
from __future__ import annotations

import re


def proximity(body: str, header_pattern: str, phrase_pattern: str, span: int = 1500) -> bool:
    m = re.search(header_pattern, body, re.MULTILINE)
    if not m:
        return False
    window = body[m.end(): m.end() + span]
    return re.search(phrase_pattern, window, re.IGNORECASE | re.DOTALL) is not None


def strip_section(body: str, header_pattern: str, span: int = 4000) -> str:
    m = re.search(header_pattern, body, re.MULTILINE)
    if not m:
        return body
    start = m.end()
    end = min(len(body), start + span)
    filler = "\n# stripped\n" * ((end - start) // 12 + 1)
    return body[:start] + filler[: end - start] + body[end:]


def fenced_block_after(body: str, header_pattern: str) -> str | None:
    m = re.search(header_pattern, body, re.MULTILINE)
    if not m:
        return None
    rest = body[m.end():]
    fence = re.search(r"```[a-z]*\n(.*?)\n```", rest, re.DOTALL)
    return fence.group(1) if fence else None
```

#### 2. `tests/test_doctrine_test_functionality.py` refactor

Replace duplicated `_proximity` / `_strip_section` definitions with `from tests._helpers import proximity, strip_section`. Net delta ≈ -70 lines, bringing the file to ~215 lines (under the 250 razor cap).

If the helper extraction alone doesn't get under 250, split the 10 negative-path tests into `tests/test_doctrine_test_functionality_negative_paths.py`. Decision deferred to implementation; ship the smallest split that achieves compliance.

#### 3. `tests/test_install_drift_check_subprocess.py` (new, ~80 lines)

```python
"""Phase 52: replace presence-only test_install_drift_check_emits_qor_logic_fix_string
with a real subprocess invocation per Phase 46 doctrine."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_install_drift_check_main_emits_qor_logic_fix_string_via_subprocess(tmp_path, monkeypatch):
    """Invoke install_drift_check.main() in a subprocess against a synthetic
    drift-detected fixture; capture stdout; assert 'qor-logic install' present."""
    # Set up a synthetic source dir + installed dir with a deliberate drift.
    src = tmp_path / "src" / "qor" / "skills" / "demo"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("source content", encoding="utf-8")
    installed = tmp_path / ".claude" / "skills" / "demo"
    installed.mkdir(parents=True)
    (installed / "SKILL.md").write_text("DIFFERENT content", encoding="utf-8")  # drift
    monkeypatch.chdir(tmp_path)
    env = {**os.environ, "QOR_GATE_PROVENANCE_OPTIONAL": "1"}
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.install_drift_check",
         "--host", "claude", "--scope", "repo"],
        capture_output=True, text=True, check=False, env=env,
    )
    # Drift detected → exit 1, fix line printed
    assert result.returncode != 0, f"expected drift detection to exit non-zero; stdout={result.stdout!r}"
    assert "qor-logic install" in result.stdout, (
        f"main() must emit 'qor-logic install' on drift; got: {result.stdout!r}"
    )
    assert "qorlogic install" not in result.stdout, (
        f"main() must NOT emit legacy 'qorlogic install'; got: {result.stdout!r}"
    )
```

#### 4. `tests/test_attribution_tiered_negative_paths.py` (new, ~110 lines)

Fixture-based negative-path tests fabricating violating commit bodies:

- `test_seal_lint_catches_synthetic_violator` — fabricate a synthetic commit body with subject `seal: phase 99 - test` and body lacking the QorLogic SDLC line; apply the same proximity-anchored regex used by `test_seal_commits_have_full_canonical_trailer`; assert the lint regex reports the violation.
- `test_plan_audit_implement_lint_catches_synthetic_violator` — same shape for plan/audit/implement subjects with bodies missing `Co-Authored-By:`.
- `test_changelog_attribution_lint_catches_synthetic_violator` — already exists in `test_changelog_attribution_negative_path`; this test is preserved as-is (was already correct).
- `test_phase_cutoff_logic_isolated_unit_test` — direct unit test of `_phase_num_from_subject` (the helper that decides cutoff inclusion); fabricate a commit subject with phase 99, assert the helper returns `99`; with subject lacking phase number, assert returns `None`.

#### 5. `qor/references/doctrine-shadow-genome-countermeasures.md` appended SG entries

```markdown
## SG-SkillProtocolBypass: skill markdown executed without runtime provenance

Skills are markdown documents under `qor/skills/**/SKILL.md`. Helper functions (`gate_chain.write_gate_artifact`, `intent_lock.capture`, etc.) accept payloads from any caller. There is no runtime check that a skill's protocol was actually executed vs a hand-written audit/seal pasted into ledger.

**Source incidents**: Phases 46, 48, 49, 50 (this session). All sealed without writing `.qor/gates/<sid>/*.json` artifacts; `git log --diff-filter=A --name-only --all -- ".qor/gates/"` returned 0 hits across entire repo history.

**Countermeasure** (codified Phase 52): `gate_chain.write_gate_artifact` requires `QOR_SKILL_ACTIVE=<phase>` env var (matches `phase` arg). `qor.reliability.gate_chain_completeness.check()` walks ledger entries and asserts all four gate artifacts exist for sealed phases ≥ 52. Wired into `/qor-substantiate` Step 7.8 + pre-merge CI gate.

**Verification hint**: `git log --diff-filter=A --name-only --all -- ".qor/gates/"` should be non-empty for any sealed phase ≥ 52. CI job `gate-chain-completeness` blocks merge on violation.

## SG-VacuousLint: self-exempting cutoff in commit-walking lints

A lint that walks `git log` and applies a "phase >= N: continue # grandfathered" cutoff at the same N where the lint was introduced is structurally vacuous on first run — there are no inputs that could fail. The lint passes by definition until a violator commits *after* the cutoff in some future phase.

**Source incident**: Phase 49's `tests/test_attribution_tiered_usage.py` lines 128, 147 (`if phase_num < 49: continue`). Authored at Phase 49 itself; only Phase 49 commits in scope at write time, all of which the same author wrote to comply.

**Countermeasure** (codified Phase 52): every cutoff lint MUST be paired with a fixture-based negative-path test that fabricates a synthetic violating input and asserts the lint catches it. The negative-path test does NOT walk real git history — it constructs a synthetic input and exercises the lint regex/parser directly.

**Verification hint**: for any test using `if phase_num < N: continue # grandfathered`, search the same test file for a sibling test with a fabricated synthetic input (no `git log` invocation). If absent, the lint is presence-only on its own subject.

## SG-RecursiveBashInjection: plan that forbids shell-interpolation reintroduces it

A plan whose `non_goals` or doctrine citation forbids `python -c "..."${VAR}"` patterns (per SG-Phase47-A) but whose `## Changes` section specifies bash that interpolates shell variables into a `python -c` literal. The pattern is recursive: the plan's text correctly identifies the anti-pattern and then commits it.

**Source incident**: Phase 51 WIP (`docs/plan-qor-phase51-ssdf-tag-emission.md`) §"Source surfaces" §2 specified `python -c " ... json.loads('''${FILES_TOUCHED_JSON}''') ... "`. Plan was VETO'd retroactively by /qor-audit before merge.

**Countermeasure** (codified Phase 52): `/qor-audit` Step 3 Infrastructure Alignment Pass adds an explicit grep: search the plan body for `python -c "[^"]*\$\{` patterns; any hit is an automatic VETO with `infrastructure-mismatch` category citing SG-RecursiveBashInjection. The countermeasure is enforceable at the plan-text layer before implementation.

**Verification hint**: `grep -E 'python -c "[^"]*\$\{' docs/plan-qor-phase*.md` should be empty for any post-Phase-52 plan.
```

### Unit Tests

(See Phase 1 + Phase 2 sections; Phase 3 tests listed under Affected Files above. Each invokes the unit and asserts on output. Negative-path tests use synthetic fixtures, not pytest.skip.)

---

## CI Commands

Operator must run locally before substantiate:

- `python -m pytest tests/test_gate_chain_provenance.py tests/test_gate_chain_completeness.py tests/test_ssdf_tagger.py tests/test_substantiate_step_7_4_ssdf_emission.py tests/test_compliance_report_post_phase52.py tests/test_ci_workflow_gate_chain_completeness.py tests/test_attribution_tiered_negative_paths.py tests/test_install_drift_check_subprocess.py -v` — phase-specific tests (8 files), run twice for determinism per `qor/references/doctrine-test-discipline.md`.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52 --repo-root .` — manual invocation; should report OK once the Phase 52 substantiate writes its gate artifacts.
- `python -m qor.scripts.ssdf_tagger --change-class feature` — manual invocation; should print `**SSDF Practices**: ...` line.
- `QOR_SKILL_ACTIVE=plan python -c "from qor.scripts.gate_chain import write_gate_artifact, ProvenanceError; print('provenance ok')"` — confirm new env-var binding works; without env var, import-and-call should raise.
- `python -m pytest tests/test_skill_doctrine.py tests/test_plan_schema_ci_commands.py tests/test_doctrine_test_functionality.py tests/test_compile.py tests/test_release_doc_currency.py tests/test_workflow_budget.py tests/test_attribution_tiered_usage.py tests/test_readme_badge_currency.py tests/test_substantiate_badge_currency_wiring.py tests/test_skill_prose_filesystem_validation.py -v` — schema/doctrine/compile/Phase49+50 guards.
- `python -m qor.scripts.dist_compile && python -m qor.scripts.check_variant_drift` — variant currency.
- `python -m qor.scripts.badge_currency --repo-root . --ledger docs/META_LEDGER.md` — Phase 49 enforcement (will catch the new test count + ledger entries).
- `python -m pytest tests/ -v` — full suite.
- `python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --plan docs/plan-qor-phase52-structural-enforcement-and-remediation.md` — Phase 47 chain-integrity check post-substantiate.
- `git log --diff-filter=A --name-only -- ".qor/gates/"` — must show entries for the Phase 52 session post-substantiate (proves Phase 1 enforcement is operational).
