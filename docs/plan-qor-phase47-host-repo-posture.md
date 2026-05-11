# Plan: Phase 47 — Host-repo posture (substantiate portability + install-freshness)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: docs/research-brief-open-issues-grouping-2026-05-09.md (δ-bundle: GH issue #38 + operator backlog item B23)

**terms_introduced**:
- term: host_capability
  home: qor/scripts/host_capability.py
- term: prerequisite_absent
  home: qor/gates/schema/shadow_event.schema.json
- term: qor_logic_stale_install
  home: qor/gates/schema/shadow_event.schema.json
- term: host-repo posture
  home: qor/references/doctrine-host-repo-posture.md
- term: prerequisite skip event
  home: qor/skills/governance/qor-substantiate/SKILL.md

**boundaries**:
- limitations:
  - V1 prereq checks cover Python toolkit module presence + file presence (`pyproject.toml`, `CHANGELOG.md`, `qor.scripts.X`). Pluggable backends per #38 option (2) — `version_bump: python | node | rust`, `changelog_stamp: keepachangelog | release-please | none` — are deferred to a V2 phase.
  - V1 freshness check compares pyproject.toml `qor-logic` version against a known-latest reference. Manifest-hash-based comparison (per-file artifact integrity) is deferred to V2.
  - Substantiate skill body documents prerequisites and prereq-skip behavior; per-step `requires:` machine-readable declarations are deferred to V2.
  - Freshness check is advisory WARN at session start; non-blocking.
- non_goals:
  - Two-track substantiate split (`-core` + `-release`) per #38 option (3); option (1) skill capability declaration is the smallest-scope path.
  - Cross-repo install-state synchronization (e.g., shared manifest registry).
- exclusions:
  - No CI workflow changes; freshness check fires at session start of each lifecycle skill.
  - No changes to the `qorlogic install` command itself; freshness check uses pyproject.toml as source of truth.

## Open Questions

None at submission.

---

## Phase 1: `host_capability` helper module + shadow event schema additions

### Affected Files

- `qor/scripts/host_capability.py` — NEW. Stdlib-only helper exposing prereq + freshness checks.
- `qor/gates/schema/shadow_event.schema.json` — add `prerequisite_absent` and `qor_logic_stale_install` to event_type enum.
- `tests/test_host_capability.py` — NEW.
- `tests/test_shadow_event_phase47_types.py` — NEW.

### Changes

**`qor/scripts/host_capability.py`** V1 surface:

```python
@dataclass(frozen=True)
class CheckResult:
    name: str            # human-readable identifier (e.g., "qor.scripts.secret_scanner")
    present: bool
    detail: str = ""     # extra info (e.g., import error message, file path)

@dataclass(frozen=True)
class PrereqSummary:
    step_name: str
    checks: tuple[CheckResult, ...]
    can_proceed: bool    # True if all checks present; False otherwise

@dataclass(frozen=True)
class FreshnessResult:
    installed_version: str | None    # parsed from pyproject.toml
    latest_known: str | None         # passed by caller or read from .qor/freshness/latest_known
    drift: bool
    detail: str = ""

def check_module(name: str) -> CheckResult: ...   # importlib.util.find_spec wrapper
def check_file(path: str | Path) -> CheckResult: ...
def check_step_prerequisites(step_name: str, prereqs: list[dict]) -> PrereqSummary:
    """prereqs is a list of {kind: "module"|"file", target: str}."""
    ...
def check_qor_logic_freshness(repo_root: str | Path, latest_known: str | None = None) -> FreshnessResult: ...
def emit_prerequisite_absent_event(step_name: str, missing: list[CheckResult], session_id: str, log_path: str | Path) -> None: ...
def emit_freshness_event(result: FreshnessResult, session_id: str, log_path: str | Path) -> None: ...
```

The two emit functions produce JSON lines conforming to `shadow_event.schema.json`. Pure-Python, no subprocess for prereq checks (use `importlib.util.find_spec` + `Path.exists`).

**`qor/gates/schema/shadow_event.schema.json`** — extend `event_type` enum:

```diff
       "specification_drift",
+      "prerequisite_absent",
+      "qor_logic_stale_install",
       ...
```

(Insertion order at end of enum to preserve backward compat of indices for any consumer that may rely on enum position — though the schema does not require positional consumers.)

### Unit Tests

- `tests/test_host_capability.py`:
  - `test_check_module_present_for_known_stdlib` (e.g., `json`).
  - `test_check_module_absent_for_nonexistent` (e.g., `qor.scripts.nonexistent_module_xyz`).
  - `test_check_file_present_returns_true_for_pyproject_toml`.
  - `test_check_file_absent_returns_false_for_missing_path`.
  - `test_check_step_prerequisites_aggregates_results`.
  - `test_check_step_prerequisites_can_proceed_true_when_all_present`.
  - `test_check_step_prerequisites_can_proceed_false_when_any_missing`.
  - `test_check_qor_logic_freshness_returns_drift_false_when_versions_match`.
  - `test_check_qor_logic_freshness_returns_drift_true_when_versions_differ`.
  - `test_check_qor_logic_freshness_handles_missing_pyproject`.
  - `test_emit_prerequisite_absent_event_writes_jsonl_with_correct_event_type`.
  - `test_emit_freshness_event_writes_jsonl_with_correct_event_type`.

- `tests/test_shadow_event_phase47_types.py`:
  - `test_event_type_enum_contains_prerequisite_absent`.
  - `test_event_type_enum_contains_qor_logic_stale_install`.
  - `test_shadow_event_with_new_type_validates_against_schema`.

---

## Phase 2: Substantiate skill prereq declarations + lifecycle skill freshness hooks

### Affected Files

- `qor/skills/governance/qor-substantiate/SKILL.md` — add §"Step Prerequisites" before Step 1 documenting which Python toolkit modules each step requires; per-step prereq-skip behavior; emit `prerequisite_absent` event when missing.
- `qor/skills/sdlc/qor-plan/SKILL.md` — add Step 0.7 "Install freshness check" between Step 0.6 (lint) and Step 1.
- `qor/skills/governance/qor-audit/SKILL.md` — add Step 0.7 "Install freshness check" between Step 0.6 (lint) and Step 1.
- `qor/skills/sdlc/qor-implement/SKILL.md` — add session-start freshness check hook.
- `qor/references/doctrine-host-repo-posture.md` — NEW.
- `qor/references/doctrine-governance-enforcement.md` — append §10.7 documenting host-repo posture discipline.
- `tests/test_substantiate_prereq_declarations.py` — NEW.
- `tests/test_lifecycle_skill_freshness_hook.py` — NEW.
- `tests/test_doctrine_host_repo_posture_present.py` — NEW.

### Changes

**`qor/skills/governance/qor-substantiate/SKILL.md`** — new §"Step Prerequisites" inserted before Step 1:

```markdown
### Step Prerequisites (Phase 47 wiring — #38)

The substantiate ceremony makes several language-specific assumptions (Python toolkit modules, pyproject.toml, Keep-a-Changelog format). When the host repo lacks these prerequisites, the affected steps SKIP and emit a `prerequisite_absent` shadow event (severity-2) instead of failing or silently no-opping.

| Step | Prerequisite | Skip behavior |
|---|---|---|
| 4.6 Reliability sweep — intent_lock | `qor.reliability.intent_lock` module | emit event; skip step |
| 4.6.5 Secret scan | `qor.scripts.secret_scanner` module | emit event; skip step |
| 4.7 Doc Integrity | `qor.scripts.doc_integrity` module | emit event; skip step |
| 7.4 SSDF tagger | `qor.scripts.ssdf_tagger` module | emit event; skip step |
| 7.5 Version bump | `pyproject.toml` file | emit event; skip; surface in seal entry as "version bump deferred (Python pyproject absent)" |
| 7.6 CHANGELOG stamp | `CHANGELOG.md` file with `## [Unreleased]` section | emit event; skip; surface in seal entry |
| 7.7 Seal entry check | `qor.reliability.seal_entry_check` module | emit event; skip |
| 7.8 Gate chain completeness | `qor.reliability.gate_chain_completeness` module | emit event; skip |
| 8.5 Dist recompile | `qor.scripts.dist_compile` module | emit event; skip |
| 9.5.5 Seal tag | `qor.scripts.governance_helpers.create_seal_tag` available + version source from 7.5 | emit event; skip |

Invocation pattern:

\`\`\`python
from qor.scripts import host_capability as hc
summary = hc.check_step_prerequisites("4.6.5", [{"kind": "module", "target": "qor.scripts.secret_scanner"}])
if not summary.can_proceed:
    hc.emit_prerequisite_absent_event("4.6.5", [c for c in summary.checks if not c.present], sid, ".qor/session/shadow.jsonl")
    # skip step body
\`\`\`

The seal entry under Step 9 surfaces a `Prerequisites: N steps SKIPPED (`step_4.6.5, step_7.4, ...`)` line when any step skipped, so the operator sees gate-state coverage at a glance. Per `qor/references/doctrine-host-repo-posture.md`.
```

**`qor/skills/sdlc/qor-plan/SKILL.md`**, **`qor/skills/governance/qor-audit/SKILL.md`** — add Step 0.7:

```markdown
### Step 0.7: Install freshness check (Phase 47 wiring — B23)

```python
from qor.scripts import host_capability as hc
result = hc.check_qor_logic_freshness(repo_root=".")
if result.drift:
    print(f"WARN: qor-logic install may be stale (installed: {result.installed_version}, latest: {result.latest_known}). Consider `qorlogic install --host claude --scope repo`.")
    hc.emit_freshness_event(result, sid, ".qor/session/shadow.jsonl")
```

Advisory WARN; non-blocking. Per `qor/references/doctrine-host-repo-posture.md`. Closes operator backlog B23.
```

**`qor/skills/sdlc/qor-implement/SKILL.md`** — same session-start hook (Step 0.7 or similar slot before Step 1).

**`qor/references/doctrine-host-repo-posture.md`** — new doctrine:

- Defines "host-repo posture" as the set of assumptions a Qor-logic lifecycle skill makes about the consuming repo (Python toolkit modules, CHANGELOG format, version source).
- Documents the V1 contract: each substantiate step declares its prerequisite; missing prereq emits `prerequisite_absent` (severity-2) and skips; seal entry surfaces SKIPPED list.
- Documents the install-freshness contract: each lifecycle skill checks `qor-logic` version against latest_known at session start; drift emits `qor_logic_stale_install` (severity-1, advisory).
- V2 path: pluggable backends + machine-readable `requires:` declarations.

**`qor/references/doctrine-governance-enforcement.md`** §10.7:

```markdown
### §10.7 Host-repo posture (Phase 47)

Qor-logic lifecycle skills make assumptions about the consuming repo (Python toolkit, CHANGELOG, pyproject). Phase 47 introduces option (1) per GH #38: explicit prerequisite declarations at each `/qor-substantiate` step, with skip-and-emit on missing. Substantiate seal entry surfaces the SKIPPED list so the operator sees which gates ran vs which were prereq-deferred.

Install-freshness check (B23): each lifecycle skill (`/qor-plan`, `/qor-audit`, `/qor-implement`, `/qor-substantiate`) runs `host_capability.check_qor_logic_freshness()` at session start. Drift emits `qor_logic_stale_install` event (severity-1, advisory WARN). Operator decides whether to run `qorlogic install` before proceeding.

Per `qor/references/doctrine-host-repo-posture.md`. V2 deferrals: pluggable language backends (#38 option 2), machine-readable `requires:` declarations, manifest-hash-based freshness comparison.
```

### Unit Tests

- `tests/test_substantiate_prereq_declarations.py`:
  - `test_substantiate_skill_has_step_prerequisites_section`
  - `test_section_lists_at_least_5_steps_with_prereq_columns`
  - `test_section_cites_prerequisite_absent_event_type`
  - `test_section_documents_skip_behavior_emit_then_skip`

- `tests/test_lifecycle_skill_freshness_hook.py`:
  - `test_qor_plan_has_step_0_7_freshness_check`
  - `test_qor_audit_has_step_0_7_freshness_check`
  - `test_qor_implement_has_freshness_check_section`
  - `test_freshness_check_cites_b23_label`

- `tests/test_doctrine_host_repo_posture_present.py`:
  - `test_doctrine_file_exists`
  - `test_doctrine_defines_term_host_repo_posture`
  - `test_doctrine_documents_prereq_skip_contract`
  - `test_doctrine_documents_freshness_check_contract`
  - `test_governance_doctrine_section_10_7_added`

---

## Phase 3: Integration tests + worked example

### Affected Files

- `tests/test_host_capability_integration.py` — NEW. End-to-end scenarios.
- `qor/scripts/host_capability_example.md` — NEW. Operator-facing one-pager with three example outputs.

### Changes

Integration scenarios:

1. All prereqs present → all checks return `present=True`, `can_proceed=True`, no events emitted.
2. Missing module → `present=False` with import-error detail; event written; `can_proceed=False`.
3. Missing file → `present=False` with absolute-path detail; event written.
4. Freshness match → drift=False, no event.
5. Freshness mismatch → drift=True, event written with `qor_logic_stale_install` type.
6. Pyproject missing → freshness check returns `installed_version=None`, drift=False (cannot determine drift).

### Unit Tests

- `tests/test_host_capability_integration.py`:
  - All 6 scenarios above, each one parameterized test.

---

## CI Commands

- `python -m pytest tests/test_host_capability.py tests/test_shadow_event_phase47_types.py -v`
- `python -m pytest tests/test_substantiate_prereq_declarations.py tests/test_lifecycle_skill_freshness_hook.py tests/test_doctrine_host_repo_posture_present.py -v`
- `python -m pytest tests/test_host_capability_integration.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase47-host-repo-posture.md`
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md`
