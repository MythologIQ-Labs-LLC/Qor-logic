# Plan: plan_text_consistency_lint --apply autofix + type-check mode

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Adds the two deferred sub-scopes to `qor.scripts.plan_text_consistency_lint`: (V2.3) an `--apply` mode that rewrites detected command/path drift in place by normalizing every divergent site in a drift group to a single canonical raw text (most-common; tie -> earliest by line); (V2.4) a `--type-check` mode that detects type-annotation drift — the same identifier given conflicting `name: Type` annotations across the plan's fenced code blocks. Dry-run remains the default (report-only, exit 1 on findings); `--apply` is opt-in and rewrites the file. The existing identity-grouping + dep_name cross-check are unchanged.
- non_goals: Rewriting `dep_name` findings (those mean "dep named but not declared" — fixed in Cargo.toml/requirements, not the plan; `--apply` skips them); a full type-inference engine (V2.4 is lexical annotation-consistency, matching the module's text-drift scope); changing the default (non-`--apply`) report behavior the Step 0.6 callers rely on.
- exclusions: Plans with no drift (apply is a no-op); placeholder/`{{verify}}` spans (already excluded by `_is_placeholder`).

## Open Questions

None. `--apply` is backward-compatible (opt-in; dry-run default preserves the current Step 0.6 report contract). Canonical-pick rule is deterministic (most-common, tie -> earliest line). Type-check is the docstring's own deferred "type-annotation consistency", scoped lexically to fenced code blocks to bound false positives.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/scripts` + tests.)

- entry_id: `n/a` · operation: `MODIFIED` · test_path: `tests/test_plan_text_consistency_apply.py` · test_descriptor: `apply_fixes rewrites every divergent drift site to the canonical raw text (dry-run leaves the file unchanged), and --type-check flags an identifier with conflicting type annotations while leaving consistent ones alone`

## Phase 1: --apply autofix + --type-check in `qor/scripts/plan_text_consistency_lint.py`

### Affected Files

- `tests/test_plan_text_consistency_apply.py` - NEW. Behavioral tests for apply + type-check (see Unit Tests). Written first; red before the functions exist.
- `qor/scripts/plan_text_consistency_lint.py` - add `apply_fixes`, `_detect_type_annotation_drift`; extend `main` with `--apply` and `--type-check`.

### Changes

```python
def _canonical_raw(sites) -> str:
    """Most-common raw_text; tie -> earliest by line. The rewrite target."""

def apply_fixes(plan_text: str, findings: list[DriftFinding]) -> tuple[str, int]:
    """Rewrite each non-dep_name drift group's divergent sites to the canonical
    raw text by replacing the backtick-delimited span `<raw>` -> `<canonical>`.
    Returns (new_text, rewrite_count). dep_name findings are skipped (not a
    plan-text fix)."""

_TYPE_ANNOT_RE = re.compile(r"\b([A-Za-z_]\w*)\s*:\s*([A-Za-z_][\w\[\], .|]*?)\s*[=,)\n]")

def _detect_type_annotation_drift(plan_text: str) -> list[DriftFinding]:
    """Within fenced code blocks, group `name: Type` annotations by name; emit a
    `type_annotation` DriftFinding for any name with >=2 distinct Type strings."""
```

`main` gains `--apply` (after computing findings: rewrite + write the file, print the rewrite count, exit 0) and `--type-check` (include `_detect_type_annotation_drift` in the findings). Without `--apply` the behavior is unchanged (report + exit 1). De-complecting: detection (`_detect_type_annotation_drift`) is separate from mutation (`apply_fixes`); mutation is opt-in.

### Unit Tests

- `tests/test_plan_text_consistency_apply.py::test_apply_rewrites_path_drift` - plan citing `` `docs/x.md` `` and `` `docs\x.md` `` (same normalized path, divergent raw -> drift); `apply_fixes(text, lint(text))` returns text where both render as the canonical `docs/x.md`, rewrite_count >= 1.
- `::test_apply_noop_when_no_drift` - a consistent plan; `apply_fixes` returns the text unchanged, count 0.
- `::test_apply_skips_dep_name` - a dep_name finding present; `apply_fixes` does not rewrite it (count unaffected by that finding).
- `::test_main_dry_run_does_not_write` - write a drifted plan to tmp; `main(["--check", p])` (no `--apply`) returns 1 and the file bytes are unchanged.
- `::test_main_apply_writes_canonical` - same tmp plan; `main(["--check", p, "--apply"])` returns 0 and the file no longer contains the divergent raw form.
- `::test_type_check_flags_conflicting_annotation` - code blocks with `count: int` and `count: str`; `_detect_type_annotation_drift` returns a `type_annotation` finding naming `count`.
- `::test_type_check_consistent_not_flagged` - `count: int` twice; returns `[]`.
- `::test_main_type_check_includes_type_findings` - `main(["--check", p, "--type-check"])` returns 1 on a type-conflict plan; without `--type-check` the same plan (no other drift) returns 0.

## Phase 2: Doc note

### Affected Files

- `qor/scripts/plan_text_consistency_lint.py` - update the module docstring: V2.3 `--apply` + V2.4 `--type-check` are shipped (move them out of the "V3 deferrals" line).

### Changes

Docstring-only: reflect that `--apply` and type-check now exist; keep the CLI usage line current. No behavioral change beyond Phase 1.

## Definition of Done

### Deliverable: apply + type-check

- **D1**: `plan_text_consistency_lint --apply` rewrites command/path drift to a canonical form (dry-run default); `--type-check` flags conflicting type annotations.
- **D2**: `apply_fixes`, `_detect_type_annotation_drift`, `_canonical_raw` in `qor/scripts/plan_text_consistency_lint.py`; `--apply` + `--type-check` flags in `main`.
- **D3**: module docstring updated (V2.3/V2.4 shipped); META_LEDGER seal entry; version bump.
- **D4**: `tests/test_plan_text_consistency_apply.py::test_main_apply_writes_canonical` + `::test_main_dry_run_does_not_write` + `::test_type_check_flags_conflicting_annotation`.

## CI Commands

- `python -m pytest tests/test_plan_text_consistency_apply.py tests/test_plan_text_consistency_lint.py -q` — new modes + existing lint (no regression).
- `python -m qor.cli scripts plan_text_consistency_lint --check docs/plan-qor-phase128-plan-consistency-apply-typecheck.md` — self-applies clean (dry-run, no drift).
- `python -m pytest -q` — full suite green before substantiate.
