# Plan: Per-feature TDD mechanical lint (plan_feature_tdd_lint)

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Ships the V2 mechanical lint `#41` deferred: `qor.scripts.plan_feature_tdd_lint` parses a plan's `## Feature Inventory Touches` block and, for each row whose `operation` is `NEW` or `MODIFIED` (a src-touching feature), requires a failing-test-first declaration — a real `test_path` (not `n/a`/empty) and a behavioral `test_descriptor` (not presence-only). It also flags a plan that touches `src/` in its Affected Files while declaring NO Feature Inventory Touches block. Plan-text lint only (it reads the plan's declared intent, mirroring the doctrine's plan-time contract); it does not inspect git diffs or assert the test was authored chronologically first.
- non_goals: Verifying the cited test actually fails first / exists on disk (that is the implement-time per-feature TDD + audit Feature Test Coverage Pass); diff/commit-order analysis; flagging `n/a-justified` rows (explicitly exempt); making the lint a hard VETO (it is WARN-only at Step 0.6; the binding VETO remains the audit Feature Test Coverage Pass).
- exclusions: Docs/governance-only plans (no `src/` Affected Files, empty/absent FIT block) produce zero findings.

## Open Questions

None. The lint operates on the same `feature_inventory_touches` contract the audit Feature Test Coverage Pass consumes; `NEW`/`MODIFIED` operations are the src-touch trigger, `n/a-justified` is exempt (per `doctrine-feature-inventory.md`). Presence-only descriptor detection reuses the established acceptance-question heuristic; WARN-only keeps false positives non-blocking.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/scripts` + tests.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_plan_feature_tdd_lint.py` · test_descriptor: `check_feature_tdd flags a NEW/MODIFIED FIT row whose test_path is n/a (missing-failing-test) and a presence-only descriptor, exempts n/a-justified rows, flags a src-touching plan with no FIT block, and returns [] for a docs-only plan`

## Phase 1: Lint logic + CLI (`qor/scripts/plan_feature_tdd_lint.py`)

### Affected Files

- `tests/test_plan_feature_tdd_lint.py` - NEW. Behavioral tests over synthetic plan text (see Unit Tests). Written first; red before the module exists.
- `qor/scripts/plan_feature_tdd_lint.py` - NEW. FIT-block parser + lint + `main(argv)` dispatchable via `qor-logic scripts plan_feature_tdd_lint`.

### Changes

```python
KNOWN_FINDING_KINDS = ("missing-failing-test", "presence-only-feature-test", "undeclared-feature-tdd")
_SRC_AFFECTED_RE = re.compile(r"^[-*]\s+`(src/[^`]+)`", re.MULTILINE)
_PRESENCE_ONLY_RE = re.compile(r"\b(exists|is defined|appears in|present|defined in|has a row)\b", re.IGNORECASE)

@dataclass(frozen=True)
class FeatureTddFinding:
    kind: str
    entry_id: str
    detail: str

def parse_fit_rows(plan_text: str) -> list[dict]:
    """Parse the `## Feature Inventory Touches` block: one dict per bullet with
    entry_id / operation / test_path / test_descriptor (the `·`-delimited
    backtick row format)."""

def check_feature_tdd(plan_text: str) -> list[FeatureTddFinding]:
    """For each NEW/MODIFIED row: missing/`n/a` test_path -> missing-failing-test;
    presence-only test_descriptor -> presence-only-feature-test. `n/a-justified`
    rows are exempt. A plan with src/ Affected Files but no FIT block ->
    undeclared-feature-tdd."""

def main(argv: list[str] | None = None) -> int:
    """--plan PATH [--repo-root .]. Print findings; exit 1 on any finding else 0
    (WARN-only at Step 0.6 via `|| true`)."""
```

De-complecting: `parse_fit_rows` (pure parse) is separate from `check_feature_tdd` (policy) and `main` (process). Trigger is `operation`-based (NEW/MODIFIED), matching the FIT contract.

### Unit Tests

- `tests/test_plan_feature_tdd_lint.py::test_new_row_with_test_clears` - FIT row `operation: NEW`, real `test_path`, behavioral descriptor; `check_feature_tdd` returns `[]`.
- `::test_new_row_missing_test_path_flagged` - `operation: NEW`, `test_path: n/a`; returns a `missing-failing-test` finding.
- `::test_presence_only_descriptor_flagged` - `operation: MODIFIED`, real `test_path`, descriptor `route exists`; returns `presence-only-feature-test`.
- `::test_na_justified_row_exempt` - `operation: n/a-justified`, `test_path: n/a`; returns `[]`.
- `::test_src_touch_without_fit_block_flagged` - plan with `## Affected Files` listing `src/foo.ts` and NO `## Feature Inventory Touches` heading; returns `undeclared-feature-tdd`.
- `::test_docs_only_plan_clean` - a plan with no `src/` Affected Files and no FIT block; returns `[]`.
- `::test_parse_fit_rows_extracts_columns` - a 2-row block; `parse_fit_rows` returns dicts with the four keys populated.
- `::test_main_exit_1_on_finding` + `::test_main_exit_0_clean` - CLI exit codes over tmp plan files.

## Phase 2: Audit wiring

### Affected Files

- `tests/test_plan_feature_tdd_lint.py` - add `test_audit_invokes_feature_tdd_lint` (prompt-contract).
- `qor/skills/governance/qor-audit/SKILL.md` - add `qor-logic scripts plan_feature_tdd_lint --plan "$PLAN_PATH" --repo-root . || true` to the Step 0.6 pre-audit lint ladder (WARN-only), with a one-line wiring note.
- `qor/dist/variants/**` - regenerated.

### Changes

Add the lint to the Step 0.6 ladder under the same `|| true` WARN-only contract as its siblings; the binding VETO stays the Step 3 Feature Test Coverage Pass. Note the lint enforces `doctrine-feature-tdd.md`'s plan-time half mechanically.

### Unit Tests

- `tests/test_plan_feature_tdd_lint.py::test_audit_invokes_feature_tdd_lint` - read `qor-audit/SKILL.md`; assert it names `plan_feature_tdd_lint`.

## Definition of Done

### Deliverable: per-feature TDD lint

- **D1**: a plan that touches src via a NEW/MODIFIED feature row without a failing-test declaration is mechanically flagged at the pre-audit layer; docs-only plans are unaffected.
- **D2**: `qor/scripts/plan_feature_tdd_lint.py` with `parse_fit_rows`, `check_feature_tdd`, `main`; dispatchable as `qor-logic scripts plan_feature_tdd_lint`.
- **D3**: audit Step 0.6 wiring; META_LEDGER seal entry; version bump; variants recompiled.
- **D4**: `tests/test_plan_feature_tdd_lint.py::test_new_row_missing_test_path_flagged` + `::test_na_justified_row_exempt` + `::test_src_touch_without_fit_block_flagged` + `::test_docs_only_plan_clean`.

## CI Commands

- `python -m pytest tests/test_plan_feature_tdd_lint.py -q` — lint + wiring.
- `python -m qor.cli scripts plan_feature_tdd_lint --plan docs/plan-qor-phase130-feature-tdd-lint.md --repo-root .` — self-applies clean (its FIT row declares a real test).
- `python -m pytest -q` — full suite green before substantiate.
