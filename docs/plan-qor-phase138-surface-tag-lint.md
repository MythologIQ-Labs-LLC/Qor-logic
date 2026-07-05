# Plan: Surface-tag WARN-only lint in the FEATURE_INDEX verification pass (GH #196 V1)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: Surface tag
  home: qor/references/doctrine-feature-inventory.md

**boundaries**:
- limitations: V1 ships a schema-optional, WARN-only presence lint only. It runs over `FEATURE_INDEX.md` and, when the header declares a `Surface` column, flags each non-`n/a` row whose `surface` cell is empty by emitting one severity-2 `degradation` shadow event (`details.gate = feature_index_surface_lint`) and exiting 0. When the header lacks a `Surface` column it prints `SKIP` + emits one `gate_skipped_prerequisite_absent` event and exits 0 (Phase 75 disclosed-skip). A missing `FEATURE_INDEX.md` is a silent skip (exit 0), unchanged.
- non_goals: Governing the *set* of valid surface values (a surface vocabulary registry — deferred follow-on); per-surface coverage ratios/gates; promoting the lint to fail-closed (V2); reconciling the `governance_health` required-vs-`doctrine` optional FEATURE_INDEX classification drift; verifying the `release` half (already resolvable via verification status + ledger linkage). Surface lint never aborts a seal in V1.
- exclusions: Repos without `FEATURE_INDEX.md`, and adopters whose header has no `Surface` column, produce zero blocking output (skip/disclosed-skip). The existing `verified -> unverified` regression ABORT (`main()` default mode) is untouched.

## Open Questions

None. The lint reuses the existing header-driven parser (`parse_index_rows`), the established WARN-only severity-2 event convention (`procedural_fidelity` / `dod_check`), and the Phase 75 disclosed-skip convention (`governance_index`). The motivating data is the sibling governance repository's (an external repository's issue); the gate is owned here. Grounding in `docs/research-brief-surface-tag-feature-index-2026-06-08.md`.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; qor-logic maintains no FEATURE_INDEX of its own — this is framework governance tooling, not a user-product feature. Declared for traceability. Touches `qor/scripts` + tests.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_feature_index_surface_lint.py` · test_descriptor: `surface_lint() returns untagged=("FX002",) when the header declares a Surface column and FX002 (status verified) has an empty surface cell; untagged=() when every non-n/a row is tagged; column_present=False (no findings) when the header omits a Surface column; and the --surface-lint CLI exits 0 in all three cases while appending a degradation event on untagged rows and a gate_skipped_prerequisite_absent event when the column is absent`

## Phase 1: Surface-tag lint logic + CLI mode (`qor/scripts/feature_index_verify.py`)

### Affected Files

- `tests/test_feature_index_surface_lint.py` (NEW) - unit tests for `index_has_surface_column`, `surface_lint`, and the `--surface-lint` CLI mode (event emission asserted by reading back the shadow-event log).
- `qor/scripts/feature_index_verify.py` - add `index_has_surface_column(text)`, `surface_lint(repo_root, index_path)`, `SurfaceLintResult` dataclass, and a `--surface-lint` branch in `main()` that is always WARN (exit 0).

### Changes

Add a pure header-detector (does not disturb `parse_index_rows`, which discards the header after building rows):

```python
def index_has_surface_column(text: str) -> bool:
    """True when the FEATURE_INDEX markdown table's header row declares a
    `Surface` column (case-insensitive, exact cell match after strip)."""
    for line in text.splitlines():
        s = line.rstrip()
        if not _TABLE_ROW.match(s) or _SEPARATOR.match(s):
            continue
        cells = [c.strip().lower() for c in s.strip("|").split("|")]
        return "surface" in cells   # first table row is the header
    return False
```

```python
@dataclass(frozen=True)
class SurfaceLintResult:
    column_present: bool
    missing_index: bool = False
    untagged: tuple[str, ...] = ()   # ids of non-n/a rows with an empty surface cell
```

```python
def surface_lint(repo_root, index_path="docs/FEATURE_INDEX.md") -> SurfaceLintResult:
    path = Path(repo_root) / index_path
    if not path.exists():
        return SurfaceLintResult(column_present=False, missing_index=True)
    text = path.read_text(encoding="utf-8")
    if not index_has_surface_column(text):
        return SurfaceLintResult(column_present=False)
    rows = parse_index_rows(text)
    untagged = tuple(
        r["id"] for r in rows
        if r["status"] != "n/a" and not r.get("surface", "").strip()
    )
    return SurfaceLintResult(column_present=True, untagged=untagged)
```

`main()` gains `--surface-lint` and `--session` args. When `--surface-lint` is set, `main()` early-returns through this WARN-only branch (no braid with the regression-ABORT path):

- `missing_index` -> `print("feature_index_surface: skip (no <index_path>)")`, return 0.
- `not column_present` -> print `SKIP [feature_index_surface]: no Surface column; recording gate_skipped_prerequisite_absent (Phase 75)`, emit one `gate_skipped_prerequisite_absent` event (severity 1, `details.gate = feature_index_surface_lint`), return 0.
- `untagged` -> print one `WARN [feature_index_surface]: <id> missing surface tag` per id, emit one `degradation` event (severity 2, `details.gate = feature_index_surface_lint`, `details.untagged = [...]`), print `feature_index_surface: WARN-only; not aborting`, return 0.
- else -> `print("feature_index_surface: ok (all non-n/a rows tagged)")`, return 0.

Events emit via `shadow_process.append_event(event, attribution="LOCAL")` (canonical form per `qor/scripts/orchestration_override.py:50`), session id from `--session` (default `"feature-index-surface"`).

### Unit Tests

- `tests/test_feature_index_surface_lint.py`:
  - `test_header_detector_true_when_surface_column_present` - `index_has_surface_column` returns True for a 7-col header containing `Surface`, False for the canonical 6-col header. Confirms the gating predicate's output, not substring presence.
  - `test_surface_lint_flags_untagged_non_na_row` - a table with a Surface column where one `verified` row has an empty surface cell -> `untagged == ("FX002",)`; the `n/a` row with an empty surface cell is NOT flagged. Confirms the non-`n/a`-and-empty selection logic.
  - `test_surface_lint_clean_when_all_tagged` - every non-`n/a` row carries a surface value -> `untagged == ()`, `column_present is True`.
  - `test_surface_lint_skips_when_no_surface_column` - 6-col table -> `column_present is False`, `untagged == ()` (the disclosed-skip precondition).
  - `test_cli_surface_lint_warns_and_emits_degradation_exit_zero` - run `main(["--surface-lint", "--repo-root", tmp, "--session", sid])` against an untagged-row fixture; assert rc == 0 AND a `degradation` event with `details.gate == "feature_index_surface_lint"` and `FX002` in `details.untagged` was appended to the LOCAL shadow log (read back from the log path). Confirms WARN-not-abort + the side effect.
  - `test_cli_surface_lint_skip_emits_prerequisite_absent_exit_zero` - run the CLI against a no-Surface-column fixture; assert rc == 0 AND a `gate_skipped_prerequisite_absent` event was appended. Confirms the disclosed-skip behavior, not just the print.

## Phase 2: Schema + doctrine/example/glossary/ladder + SKILL.md wiring

### Affected Files

- `tests/test_feature_index_surface_schema.py` (NEW) - the schema accepts a row with a `surface` value and a row omitting `surface`; rejects an unknown sibling property (guards `additionalProperties: false` stays intact).
- `qor/gates/schema/feature_index.schema.json` - add optional `"surface"` string property.
- `qor/templates/FEATURE_INDEX.example.md` - add a `Surface` column to the worked example (keeps it a valid 7-col demonstration).
- `qor/references/doctrine-feature-inventory.md` - already carries the "Surface column (optional V2 extension; GH #196)" subsection (written in research lead-in); add the lifecycle-hook line that `/qor-substantiate` runs the WARN-only surface lint.
- `qor/references/glossary.md` - add `Surface tag` term with `referenced_by` wiring to `doctrine-feature-inventory.md` (avoids doc_integrity term-drift, Phase 135 lesson).
- `qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md` - add the surface-lint entry with WARN->V2-fail-closed rationale, mirroring the Phase 114->122 feature_index_verify note.
- `qor/skills/governance/qor-substantiate/SKILL.md` - in the FEATURE_INDEX verification pass, add step 7: run `qor-logic scripts feature_index_verify --surface-lint --session "$SESSION_ID" --repo-root .` (WARN-only; never aborts).
- dist variants (`qor/dist/variants/{claude,codex,kilo-code}/skills/qor-substantiate/SKILL.md` + references) - recompiled from source.

### Changes

Schema property (between `test_path` and `status`):

```json
"surface": {
  "type": "string",
  "description": "Optional (GH #196). User-facing product surface the feature ships on (e.g. command, route, settings-card, voice). Free-text in V1; a governed vocabulary is a deferred follow-on."
}
```

`additionalProperties: false` is retained; `surface` is NOT added to `required`. Example template header becomes `| ID | Name | Source-of-truth file:line | Doc citation | Test path | Surface | Verification status |` with surface values populated for the verified/unverified rows and left empty (acceptable) for the `n/a` row.

SKILL.md pass gains, after the existing step 6 regression ABORT:

> 7. Run the surface-tag WARN-only lint (Phase 138; GH #196): `qor-logic scripts feature_index_verify --surface-lint --session "$SESSION_ID" --repo-root .`. When the index declares a `Surface` column, non-`n/a` rows missing a surface value append a severity-2 `degradation` event (never abort). No `Surface` column -> disclosed-skip. See `references/seal-gate-ladder.md`.

### Unit Tests

- `tests/test_feature_index_surface_schema.py`:
  - `test_schema_accepts_row_with_surface` - jsonschema-validate a row dict carrying `surface="route"` -> valid (no error raised). Confirms the property is accepted.
  - `test_schema_accepts_row_without_surface` - a row omitting `surface` validates (surface stays optional). Confirms non-required.
  - `test_schema_still_rejects_unknown_property` - a row with `bogus="x"` fails validation. Confirms `additionalProperties: false` is intact after the edit.
- Existing guards re-run (must stay green): `tests/test_feature_index_example_template.py`, `tests/test_feature_index_verify_helper.py`, `tests/test_feature_index_verify_gate.py`, `tests/test_doctrine_feature_inventory.py`, `tests/test_glossary_*`, the doc_integrity suite, and the qor-substantiate wiring tests.

## Definition of Done

### Deliverable: Surface-tag WARN-only lint

- **D1**: When a governed `FEATURE_INDEX.md` declares a `Surface` column, the seal surfaces (without blocking) every non-`n/a` feature that has not declared the product surface it ships on, so per-surface projections become trustworthy by construction. Schema-optional and WARN-only so no existing repo breaks.
- **D2**: `surface_lint(repo_root, index_path) -> SurfaceLintResult` and `index_has_surface_column(text) -> bool` in `qor/scripts/feature_index_verify.py`; `main()` `--surface-lint` branch always exits 0; new optional `surface` property in `qor/gates/schema/feature_index.schema.json` with `additionalProperties: false` retained.
- **D3**: SKILL.md FEATURE_INDEX pass step 7 + `seal-gate-ladder.md` entry + doctrine lifecycle-hook line + glossary `Surface tag` term with `referenced_by`; dist variants recompiled; META_LEDGER SESSION SEAL entry records the feature with `change_class: feature`.
- **D4**: `test_cli_surface_lint_warns_and_emits_degradation_exit_zero` asserts rc == 0 and a `degradation` event with `details.gate == "feature_index_surface_lint"` appended; `test_cli_surface_lint_skip_emits_prerequisite_absent_exit_zero` asserts rc == 0 and a `gate_skipped_prerequisite_absent` event appended; `test_surface_lint_flags_untagged_non_na_row` asserts `untagged == ("FX002",)`.

## CI Commands

- `python -m pytest tests/test_feature_index_surface_lint.py tests/test_feature_index_surface_schema.py -q` — new behavior, run twice for determinism.
- `python -m pytest tests/test_feature_index_example_template.py tests/test_feature_index_verify_helper.py tests/test_feature_index_verify_gate.py tests/test_doctrine_feature_inventory.py -q` — regression guard on the touched surfaces.
- `python -m pytest -q` — full suite green before substantiate.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase138-surface-tag-lint.md` — plan self-consistency.
- `qor-logic scripts doc_integrity --repo-root .` — glossary/term-drift integrity after the new term lands.
