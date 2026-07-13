# Plan: Phase 185 - Keyword-only lint resolves definitions by scope (GH #265)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-keyword-lint-scoping-2026-07-13.md (ledger entry #458, session `2026-07-13T0919-7937b6`); GH #265.

## Locked Decisions

- **LD-1: multimap + three-tier resolution inside the lint's helpers.**
  `grep -nE 'def _collect_keyword_only_functions' tests/test_shadow_genome_doctrine.py -> 15`; `grep -nE 'def _find_positional_violations' tests/test_shadow_genome_doctrine.py -> 35`. Collection becomes `dict[str, list[tuple[Path, int, list[str]]]]` (`setdefault(...).append(...)`). Per call site: candidates = same-file defs when any exist; else the single def when the name is tree-unique; else SKIP (ambiguous bare name). A violation requires exceeding EVERY consulted candidate's positional arity.
- **LD-2: the production lint test itself is the acceptance net.**
  `test_no_positional_calls_to_keyword_only_functions` continues to run over qor/scripts + tests unchanged in invocation; the live `check`/`scan` collisions stop being coin-toss attributions. New synthetic-fixture tests (tmp trees fed to the helpers directly) prove: collision false-positive eliminated; same-file violation still flagged; unique-name cross-module violation still flagged.

## Phase 1: Resolution rule + fixture tests (TDD first)

### Affected Files

- tests/test_shadow_genome_doctrine.py - helpers updated per LD-1; three synthetic-fixture tests appended

### Changes

`_collect_keyword_only_functions` returns the multimap. `_find_positional_violations` resolves candidates per LD-1 (a small `_candidates_for(name, py, kwonly_fns)` local helper keeps nesting <= 3) and flags only when `all(len(concrete) > len(positional) for each candidate)`.

### Unit Tests

- tests/test_shadow_genome_doctrine.py::test_cross_module_name_collision_not_flagged - tmp tree: module A defines 5-positional `_emit` (no kwonly), module B defines 1-positional keyword-only `_emit`; a 5-arg call in A is NOT flagged (the GH #265 consumer reproduction; red today)
- tests/test_shadow_genome_doctrine.py::test_same_file_violation_still_flagged - a 2-positional call to the same file's 1-positional keyword-only def IS flagged (SG-033 core preserved)
- tests/test_shadow_genome_doctrine.py::test_unique_name_cross_module_violation_still_flagged - a unique-name keyword-only def in one module, positional-overflow call in another: flagged (coverage retention)

## Feature Inventory Touches

(empty -- lint precision)

## Definition of Done

### Deliverable: scope-aware SG-033 lint

- **D1**: A new module reusing a common private helper name can no longer trip 7 false positives against another module's keyword-only signature (GH #265), while same-file and unique-name violations keep flagging.
- **D2**: LD-1 multimap + three-tier resolution; helper keeps razor limits.
- **D3**: Ledger entries for plan/audit/implement/seal; GH #265 disposition records the ambiguous-skip trade-off and the attribute-resolution follow-on.
- **D4**: The three fixture tests observe the tiers (collision test red today).

## CI Commands

- `python -m pytest tests/test_shadow_genome_doctrine.py -q` - focused suite (run twice for determinism)
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
