# Plan: Phase 61 — Unified path-match helper (closes qor-debug M6)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: qor-debug Phase 60 review M6 (adversarial-mode trigger conditions are operator-judgment substrings, no structured matcher)

**terms_introduced**:
- term: path_match.matches
  home: qor/scripts/path_match.py
- term: ADVERSARIAL_REVIEW_TRIGGERS
  home: qor/scripts/audit_triggers.py
- term: trigger source-of-truth
  home: qor/skills/governance/qor-audit/references/adversarial-mode.md

**boundaries**:
- limitations:
  - V1 covers prefix-with-boundary matching (`/`, `.`, exact equality). Glob patterns and regex are out of scope.
  - V1 unifies 3 existing call sites: `qor/capabilities/risk.py::_matches_any`, `qor/capabilities/context.py::_prefix_match`, and the audit-side trigger detection. Other prefix-matching sites in the codebase remain untouched.
- non_goals:
  - Replacing the gitignore-style pattern matcher (`fnmatch`).
  - Network or remote-path matching.
- exclusions:
  - No changes to existing `Cargo.toml` / `pyproject.toml` parsing logic.

## Open Questions

None at submission.

## Phase 1: Unified path_match helper

### Affected Files

- `qor/scripts/path_match.py` — NEW. Shared boundary-aware matcher.
- `tests/test_path_match.py` — NEW.

### Changes

Public surface:

```python
def matches(path: str, prefix: str) -> bool: ...
def matches_any(path: str, prefixes: tuple[str, ...]) -> bool: ...
def find_matching_prefix(path: str, prefixes: tuple[str, ...]) -> str | None: ...
```

`matches(path, prefix)`:
- Exact equality → True.
- `path.startswith(prefix)` AND the next char is `/` or `.` → True.
- Otherwise → False.

`matches_any`: short-circuits over `prefixes`.

`find_matching_prefix`: returns the FIRST matching prefix (for use cases where the caller needs to know which rule fired).

### Unit Tests

- `test_matches_exact_equality`
- `test_matches_directory_boundary`
- `test_matches_extension_boundary`
- `test_matches_rejects_sibling_lookalike` (the M1 regression case: `ledger_hash` does not match `ledger_hash_v2.py`)
- `test_matches_rejects_partial_segment_match`
- `test_matches_any_returns_true_on_first_hit`
- `test_matches_any_returns_false_when_no_hit`
- `test_find_matching_prefix_returns_first_match`
- `test_find_matching_prefix_returns_none_when_no_match`

## Phase 2: Migrate existing call sites + introduce ADVERSARIAL_REVIEW_TRIGGERS

### Affected Files

- `qor/capabilities/risk.py` — `_matches_any` delegates to `path_match.matches_any`.
- `qor/capabilities/context.py` — `_prefix_match` delegates to `path_match.matches`.
- `qor/scripts/audit_triggers.py` — NEW. Structured trigger list:

  ```python
  @dataclass(frozen=True)
  class AdversarialTrigger:
      label: str
      prefixes: tuple[str, ...]
      reason: str

  ADVERSARIAL_REVIEW_TRIGGERS: tuple[AdversarialTrigger, ...] = (
      AdversarialTrigger("governance-skills", ("qor/skills/governance/",), "L2/L3 audit surface"),
      AdversarialTrigger("ledger", ("docs/META_LEDGER.md", "qor/scripts/ledger_hash", "qor/scripts/ledger_fragment", "qor/scripts/ledger_entry_id"), "chain integrity"),
      AdversarialTrigger("schemas", ("qor/gates/schema/",), "gate contract changes"),
      AdversarialTrigger("substantiate-core", ("qor/skills/governance/qor-substantiate/",), "seal ceremony"),
      AdversarialTrigger("audit-core", ("qor/skills/governance/qor-audit/",), "audit ceremony"),
  )

  def matches_any_trigger(changed_files: tuple[str, ...]) -> tuple[AdversarialTrigger, ...]: ...
  ```

- `tests/test_audit_triggers.py` — NEW.

### Unit Tests

- `test_risk_routing_still_works_after_migration` (regression: 4-5 existing risk-routing tests must still pass)
- `test_context_recommended_checks_still_works_after_migration`
- `test_adversarial_triggers_governance_skills_fires_on_qor_skills_governance`
- `test_adversarial_triggers_ledger_fires_on_meta_ledger_or_ledger_hash`
- `test_adversarial_triggers_schemas_fires_on_qor_gates_schema`
- `test_adversarial_triggers_does_not_fire_on_unrelated_path`
- `test_matches_any_trigger_returns_all_matching_classes`

## Phase 3: adversarial-mode.md cross-references the structured trigger list

### Affected Files

- `qor/skills/governance/qor-audit/references/adversarial-mode.md` — trigger conditions section becomes the prose narrative; cross-references `qor/scripts/audit_triggers.py::ADVERSARIAL_REVIEW_TRIGGERS` as the machine-readable source of truth.
- `qor/skills/governance/qor-audit/SKILL.md` — Step 1.a prose cross-references the trigger module.
- `tests/test_adversarial_mode_trigger_crossref.py` — NEW.

### Changes

`adversarial-mode.md` Trigger conditions section: keep the prose enumeration AND add a single line:

```markdown
**Machine-readable source of truth**: `qor/scripts/audit_triggers.py::ADVERSARIAL_REVIEW_TRIGGERS`. The prose enumeration MUST stay in sync with the structured tuple; `tests/test_adversarial_mode_trigger_crossref.py` enforces.
```

The crossref test reads both prose and structured list and asserts every prefix in `ADVERSARIAL_REVIEW_TRIGGERS` is mentioned in the prose enumeration (subset check; prose may include explanatory text not in the tuple).

### Unit Tests

- `test_adversarial_mode_md_cites_audit_triggers_module`
- `test_every_structured_trigger_prefix_appears_in_adversarial_mode_prose`
- `test_audit_skill_step_1a_references_audit_triggers_module`

## CI Commands

- `python -m pytest tests/test_path_match.py tests/test_audit_triggers.py tests/test_adversarial_mode_trigger_crossref.py -v`
- `python -m pytest tests/test_risk_routing_report.py tests/test_governance_context_packet.py -v` (regression suite)
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase61-unified-path-match.md`
