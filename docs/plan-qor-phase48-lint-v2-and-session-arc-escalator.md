# Plan: Phase 48 — `plan_text_consistency_lint` V2 + cross-session cycle-count escalator

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: docs/research-brief-open-issues-grouping-2026-05-09.md (β-bundle: GH issues #43, #46)

**terms_introduced**:
- term: identity-based grouping
  home: qor/scripts/plan_text_consistency_lint.py
- term: dep_name operation kind
  home: qor/scripts/plan_text_consistency_lint.py
- term: cross-session escalation
  home: qor/scripts/cycle_count_escalator.py
- term: cross_session_check
  home: qor/scripts/cycle_count_escalator.py
- term: --strict mode
  home: qor/scripts/plan_text_consistency_lint.py

**boundaries**:
- limitations:
  - V2.3 `--apply` mode (mechanical drift correction) is DEFERRED. V2 ships `--check` only plus the new `--strict` flag (preserves V1 broad-rule for debugging).
  - V2.4 type-annotation consistency is DEFERRED (speculative, lower priority per GH #46).
  - `dep_name` cross-check reads `Cargo.toml` `[dependencies]` and `requirements.txt` / `requirements-dev.txt` only. `pyproject.toml [project.dependencies]` parsing deferred to V3.
  - Cross-session escalator walks the last 5 SESSION SEAL entries (configurable via `WINDOW_SIZE`). Earlier history not consulted to avoid stale-signal noise.
- non_goals:
  - Auto-detection of which projection-table column is the import column. V2 assumes a `Imports` column header literal (case-insensitive); plans with different naming use V1 `--strict` until V3 generalizes.
  - Suppression of cross-session escalator via existing `escalation_suppressed` marker. V2 adds independent `cross_session_suppressed` marker (separate decision surface).
- exclusions:
  - No changes to `audit.schema.json` or `plan.schema.json` (V2 is a lint + escalator behavior change, not a gate-payload change).
  - No new SKILL.md amendments beyond a one-line cross-reference in `qor-audit` Step 0.5 and `qor-plan` Step 2c.

## Open Questions

None at submission.

---

## Phase 1: Lint V2 — identity-based grouping + `dep_name` kind + `--strict` flag

### Affected Files

- `qor/scripts/plan_text_consistency_lint.py` — V2 evolution: new `_identity_for` function returns grouping key per kind; `_detect_drift` switches between broad-rule (V1 / `--strict`) and identity-based (V2 default); new `dep_name` operation kind detector reads `Cargo.toml` / `requirements*.txt` from `--repo-root` (defaults to plan's parent's parent).
- `tests/test_plan_text_consistency_lint_v2.py` — NEW. V2 behavior tests including the V1 false-positive class becoming clean.

### Changes

**`qor/scripts/plan_text_consistency_lint.py`** additions:

```python
# New operation kind appended:
OPERATION_KINDS = (
    "cargo_test", "cargo_build", "python_module", "python_script",
    "filesystem_path", "dep_name",   # NEW
)

# New identity function: returns a hashable key that groups equivalent operations.
# Per-kind contract:
#   cargo_test / cargo_build : (subcommand, sorted_positional)
#     -> "cargo test --features X coreforge::skill" and
#        "cargo test --features Y coreforge::skill" share identity
#        ("test", ("coreforge::skill",))
#   python_module: dotted module path only
#   python_script: (script_relpath, first_arg_or_empty)
#     -> "python scripts/lint.py --apply X" and
#        "python scripts/lint.py --check Y" have DIFFERENT identities (--apply vs --check)
#   filesystem_path: unchanged (normalized path)
#   dep_name: (manifest_kind, dep_name) — e.g., ("cargo", "schemars")

def _identity_for(kind: str, site: Site) -> tuple: ...

# _detect_drift V2 logic:
#   For non-filesystem_path kinds:
#     - Group by identity (V2 default) OR by kind (V1 --strict)
#     - Drift = same group + 2+ distinct normalized
#   For filesystem_path: unchanged (same normalized + 2+ distinct raw_text)
#   For dep_name: drift = name in plan but absent from manifest

def _detect_drift_v2(sites: list[tuple[Site, str]], strict: bool, repo_root: Path | None) -> list[DriftFinding]: ...

# CLI:
#   --check <path>: existing behavior (now uses V2 grouping by default)
#   --strict: opt-in to V1 broad-rule (preserves debugging path)
#   --repo-root <path>: where to find Cargo.toml / requirements*.txt for dep_name kind
```

**Projection-table import row extraction** for `dep_name`:

```python
_IMPORT_HEADER = re.compile(r"^\|.*Imports.*\|", re.IGNORECASE | re.MULTILINE)
_DEP_NAME = re.compile(r"\b([a-z][a-z0-9_-]+)\b")

def _extract_dep_names_from_imports(plan_text: str) -> list[tuple[int, str, str]]:
    """Walk plan markdown for projection-table rows whose header contains 'Imports'.
    Returns (line, dep_name, manifest_kind) where manifest_kind ∈ {cargo, python}.
    Heuristic: dotted_path with 'qor.' or 'std.' → skip (own module); lowercase
    identifier → candidate.
    """
    ...
```

**Manifest reading**:

```python
def _cargo_dep_names(repo_root: Path) -> set[str]:
    """Parse Cargo.toml [dependencies] section. Stdlib only (manual scan)."""
    ...

def _python_dep_names(repo_root: Path) -> set[str]:
    """Parse requirements.txt + requirements-dev.txt. PEP 508 prefix only."""
    ...
```

`Cargo.toml` parsing: scan for `[dependencies]` header and `[dev-dependencies]`; extract `name = "..."` or `name = { ... }` lines until next `[section]`. PEP 508: each line's leading identifier before `==`, `>=`, `~=`, `[`, `;`, or whitespace.

### Unit Tests

- `tests/test_plan_text_consistency_lint_v2.py`:
  - `test_v2_default_groups_pytest_invocations_by_identity` — same plan with `python -m pytest tests/a.py` and `python -m pytest tests/b.py`; V2 default returns NO drift (different identities). Same plan with `--strict` returns drift (V1 broad-rule).
  - `test_v2_default_groups_pytest_same_target_different_flags` — `python -m pytest tests/a.py -v` and `python -m pytest tests/a.py` (different normalized); V2 returns 1 finding (same identity).
  - `test_v2_python_script_apply_vs_check_distinct_identity` — `python scripts/lint.py --apply X` + `python scripts/lint.py --check Y` → no drift (different first-arg).
  - `test_v2_cargo_test_same_target_different_flags_is_drift` — same test target, different `--features`; V2 returns 1 finding.
  - `test_v2_cargo_test_different_targets_no_drift` — different positional, same flags; V2 no drift.
  - `test_dep_name_kind_drift_when_named_but_not_declared` — plan with `Imports (schemars, chrono)` row; Cargo.toml lacks `schemars`; V2 returns 1 dep_name finding.
  - `test_dep_name_kind_no_drift_when_all_declared` — Cargo.toml has both; V2 returns no finding.
  - `test_dep_name_handles_missing_cargo_toml` — repo_root with no Cargo.toml; dep_name detector returns no findings.
  - `test_dep_name_handles_python_requirements` — `requirements.txt` listing `pydantic==2.0`; plan names `pydantic` and `numpy`; numpy flagged.
  - `test_v2_strict_flag_preserves_v1_broad_rule` — fixture that V1 broad-rule flags as drift; under `--strict`, V2 returns same finding count.
  - `test_v2_phase45_plan_no_longer_flags_pytest_ci_commands` — load `docs/plan-qor-phase45-...md` as fixture (or a synthetic equivalent); V2 default returns 0 findings on the multi-pytest CI commands section.

---

## Phase 2: Cross-session cycle-count escalator

### Affected Files

- `qor/scripts/cycle_count_escalator.py` — new `cross_session_check(session_id, window_size=5)` function; existing `check(session_id)` extended to invoke both per-session and cross-session checks and return whichever fires first.
- `qor/scripts/meta_ledger_walker.py` — NEW. Stdlib-only helper that parses `docs/META_LEDGER.md` SESSION SEAL entries (or VETO/audit entries) and returns the last N records with `(verdict, signature, ts, plan_target)`.
- `tests/test_cross_session_escalator.py` — NEW.
- `tests/test_meta_ledger_walker.py` — NEW.
- `qor/references/doctrine-governance-enforcement.md` — extend §10.4 with the cross-session dimension.

### Changes

**`qor/scripts/meta_ledger_walker.py`** V1 surface:

```python
@dataclass(frozen=True)
class LedgerRecord:
    entry_id: int
    phase_label: str         # "AUDIT" | "SESSION SEAL" | "RESEARCH BRIEF" | ...
    target: str | None       # plan path or None
    verdict: str | None      # "PASS" | "VETO" | None
    signature: str | None    # findings_signature (16-hex prefix) or LEGACY
    ts: str | None
    raw_block: str           # entry markdown block for re-parsing if needed

def walk(ledger_path: str | Path) -> list[LedgerRecord]: ...     # parse all entries
def last_n_audit_entries(ledger_path: str | Path, n: int) -> list[LedgerRecord]: ...
```

Parser walks `### Entry #(\d+):` anchors, extracts phase label from the heading suffix, parses `Verdict:` and `Findings categories:` (or `Findings:`) lines from the body. Stdlib regex only.

**`qor/scripts/cycle_count_escalator.py`** additions:

```python
CROSS_SESSION_THRESHOLD = 3
CROSS_SESSION_WINDOW = 5    # walk last N audit entries

@dataclass(frozen=True)
class EscalationRecommendation:
    suggested_skill: str
    escalation_reason: str          # "cycle-count" | "cross-session"
    signature: str
    cycle_count: int
    artifacts: tuple[str, ...] = ()   # NEW: distinct targets contributing

def cross_session_check(
    session_id: str,
    ledger_path: str | Path = "docs/META_LEDGER.md",
    window_size: int = CROSS_SESSION_WINDOW,
) -> EscalationRecommendation | None:
    """Walk last N audit entries; count same-signature VETO streak across ≥2 distinct targets."""
    ...

def check(session_id: str) -> EscalationRecommendation | None:
    """Per-session OR cross-session. Returns the first recommendation that fires."""
    per = _per_session_check(session_id)   # rename of current check() body
    if per:
        return per
    return cross_session_check(session_id)
```

**Cross-session reset conditions** (mirror per-session walker semantics):

- Newest entry not a VETO audit → no streak.
- Signature differs from in-progress run → break.
- Entry with `LEGACY` sentinel signature → break.
- Distinct targets count < 2 → not a cross-session pattern (per-session would have fired).
- Suppression marker `.qor/session/<sid>/cross_session_suppressed` newer than `first_match_ts` → suppress.

**Doctrine update** (`qor/references/doctrine-governance-enforcement.md` §10.4):

Append sub-section "Cross-session signature accumulation (Phase 48 wiring)":

> Per-session cycle-count escalation catches recurring discipline gaps within one session. A second tracker dimension catches the same pattern across sessions: when an operator's recurring discipline gap manifests across multiple plans (each in its own session post-`session.rotate()`), the per-session counter resets at session boundaries but the META_LEDGER chain preserves the signal. `cross_session_check` walks the last 5 audit entries in `docs/META_LEDGER.md`; threshold is 3 consecutive same-signature VETOs across ≥2 distinct targets. Suppression marker is independent of the per-session marker (`.qor/session/<sid>/cross_session_suppressed`).

### Unit Tests

- `tests/test_meta_ledger_walker.py`:
  - `test_walk_parses_session_seal_entries_with_target_and_verdict`
  - `test_walk_parses_audit_veto_entries`
  - `test_walk_handles_legacy_entries_without_signature`
  - `test_walk_skips_research_brief_entries`
  - `test_last_n_audit_entries_returns_newest_n_in_order`
  - `test_last_n_audit_entries_returns_all_when_fewer_than_n`

- `tests/test_cross_session_escalator.py`:
  - `test_cross_session_check_returns_none_on_empty_ledger`
  - `test_cross_session_check_returns_none_on_single_veto`
  - `test_cross_session_check_returns_none_on_two_vetos_one_artifact` — per-session would handle.
  - `test_cross_session_check_fires_on_three_same_sig_across_two_artifacts`
  - `test_cross_session_check_fires_on_four_same_sig_across_three_artifacts` — COREFORGE scenario.
  - `test_cross_session_check_resets_on_pass_break` — PASS audit in window breaks streak.
  - `test_cross_session_check_resets_on_different_signature` — non-matching sig breaks streak.
  - `test_cross_session_check_respects_window_size` — entries outside window not counted.
  - `test_cross_session_check_returns_distinct_artifacts_in_recommendation`
  - `test_cross_session_check_honors_suppression_marker` — marker newer than first_match_ts suppresses.

---

## Phase 3: Skill cross-references + final integration

### Affected Files

- `qor/skills/governance/qor-audit/SKILL.md` — Step 0.5 cross-reference: cycle-escalator now reports cross-session pattern.
- `qor/skills/sdlc/qor-plan/SKILL.md` — Step 2c cross-reference: same.
- `tests/test_skill_cross_session_anchor.py` — NEW. Asserts both SKILL.md files cite "cross-session" pattern + reference the §10.4 sub-section.

### Changes

**`qor-audit` Step 0.5 amendment** (after existing `cce.check(sid)` block):

```markdown
The escalator now reports both per-session and cross-session patterns (Phase 48 wiring per `qor/references/doctrine-governance-enforcement.md` §10.4). `EscalationRecommendation.escalation_reason` distinguishes `"cycle-count"` (per-session) from `"cross-session"`. Operator-decline path is identical; cross-session suppression marker is independent.
```

**`qor-plan` Step 2c amendment** — same cross-reference block.

### Unit Tests

- `tests/test_skill_cross_session_anchor.py`:
  - `test_qor_audit_step_0_5_references_cross_session`
  - `test_qor_plan_step_2c_references_cross_session`
  - `test_both_skills_cite_doctrine_section_10_4`

---

## CI Commands

- `python -m pytest tests/test_plan_text_consistency_lint_v2.py -v`
- `python -m pytest tests/test_meta_ledger_walker.py tests/test_cross_session_escalator.py -v`
- `python -m pytest tests/test_skill_cross_session_anchor.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase48-lint-v2-and-session-arc-escalator.md`
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md`
