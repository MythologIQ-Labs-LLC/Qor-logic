# Plan: Phase 97 — SKILL_REGISTRY per-category drift reconciliation (F8)

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: F8 (internal prompt-surface review finding)

**boundaries**:
- limitations: V1 reconciles `docs/SKILL_REGISTRY.md` to match the actual
  per-category .md file counts at HEAD, updates the snapshot date, and
  adds a per-category currency test (`tests/test_skill_registry_per_category_currency.py`)
  that fails on any category-level drift instead of relying on
  total-cancellation as the failure mode. V1 covers the FOUR canonical
  categories (governance, sdlc, memory, meta); the `custom/` category
  remains structurally separate (reserved-empty per the registry).
- non_goals: changing the registry's counting methodology (memory
  counts .md files including migrated stubs; other categories count
  SKILL.md inside per-skill dirs; both are .md-file counts on different
  layouts — unified by the new test's counting function);
  cross-referencing the registry to dist variant manifests (separate
  drift surface; not in Phase 97 scope); auto-regenerating the registry
  from disk state (V2 candidate; V1 is operator-actioned reconciliation).
- exclusions: no changes to any SKILL.md content (registry-only edit);
  no changes to existing badge currency tests (Phase 49); no changes to
  `qor/skills/SKILL_REGISTRY.md` (this path does not exist — the actual
  file is `docs/SKILL_REGISTRY.md`; the meta-plan called it
  `qor/skills/SKILL_REGISTRY.md` by typo).

## Open Questions

None. The two unaccounted skills (`qor-ideate` in sdlc, `qor-ab-run` in
meta) are both Active per their frontmatter; no operator decision
required.

## Feature Inventory Touches

Empty. Registry edit + new test.
`feature_inventory_touches`: `[]`.

## Design notes

F8 of the internal prompt-surface review documented that
`docs/SKILL_REGISTRY.md`'s snapshot is stale and the declared per-category
counts disagree with the actual files on disk. The defect surface is
specifically that the declared TOTAL (30) happens to match the actual
TOTAL (30) by offset cancellation — sdlc undercounts by 1, meta
undercounts by 1, and memory is internally consistent — so a
total-only currency test would pass while two categories silently
drift. The dogfooding shipping-correctness anchor for Phase 97 is the
new per-category test catching exactly the drift this phase fixes.

**Reconciliation at HEAD** (counted as `.md` files at depth ≤2):

| Category | Declared | Actual | Drift | Missing from registry |
|---|---|---|---|---|
| governance | 6 | 6 | 0 | — |
| sdlc | 6 | 7 | +1 | qor-ideate |
| memory | 7 | 7 | 0 | — |
| meta | 11 | 12 | +1 | qor-ab-run |
| **Total** | **30** | **32** | **+2** | — |

The actual total is 32 (not 30 as previously declared). The Phase 95
total of 30 was correct only under the cancellation analysis the
meta-plan documented; after Phase 97 reconciliation, the truth is 32
.md files across the four canonical categories.

**V1 reconciliation actions**:

1. Update snapshot date from `2026-04-29` to `2026-05-23`.
2. Add `qor-ideate` row to the sdlc table; update header count `(6)` →
   `(7)`.
3. Add `qor-ab-run` row to the meta table; update header count `(11)` →
   `(12)`.
4. Verify memory section: 5 SKILL.md-bearing subdirs + 2 standalone
   migrated .md files = 7 total .md files; declared count `(7)` is
   correct; no edit needed beyond cross-checking.

**New test** (`tests/test_skill_registry_per_category_currency.py`):

- `test_governance_category_count_matches_declared` — assert declared
  `(N)` count for governance matches actual .md file count at depth ≤2.
- `test_sdlc_category_count_matches_declared` — same for sdlc.
- `test_memory_category_count_matches_declared` — same for memory.
- `test_meta_category_count_matches_declared` — same for meta.
- `test_registry_lists_every_actual_skill_md_for_each_category` —
  positional: for each category, walk depth-≤2 `.md` files and assert
  each one is referenced by name in that category's table. Catches the
  inverse drift (registry references a file that no longer exists).
- `test_no_cross_category_skill_listed` — sweep: a skill listed in
  category X must have its path containing `/skills/X/` (cross-category
  drift guard).
- `test_total_count_matches_sum_of_per_category_declared_counts` —
  arithmetic guard: declared total in any "Total" or summary line
  (when present) matches the sum of per-category declared counts.

Per-category granularity means total-cancellation cannot mask drift in
V2 or later. The test functions as the structural countermeasure for
the F8 defect class.

## Phase 1: registry reconciliation + per-category test

### Affected Files

- `docs/SKILL_REGISTRY.md` — snapshot date update; sdlc +1 row + count;
  meta +1 row + count.
- `tests/test_skill_registry_per_category_currency.py` — NEW. Seven
  assertions covering per-category currency + cross-category drift
  guards.
- `docs/plan-qor-phase97-skill-registry-per-category-drift.md` — NEW.
  This plan.

### Unit Tests

(See "New test" enumeration in Design notes above; seven assertions.)

### Changes

`docs/SKILL_REGISTRY.md` edits described in Design notes section
"V1 reconciliation actions".

`tests/test_skill_registry_per_category_currency.py`:

```python
from pathlib import Path
import re

REGISTRY = Path(__file__).resolve().parent.parent / "docs" / "SKILL_REGISTRY.md"
SKILLS_ROOT = Path(__file__).resolve().parent.parent / "qor" / "skills"

def _count_md_at_depth_le_2(category_dir: Path) -> int:
    """Count .md files immediately under category_dir or one level deeper
    (the canonical skill layout). Excludes references/ subdir contents."""
    count = 0
    for p in category_dir.rglob("*.md"):
        rel = p.relative_to(category_dir)
        if len(rel.parts) > 2:
            continue
        if "references" in rel.parts:
            continue
        count += 1
    return count

def _declared_count(category: str, registry_text: str) -> int:
    match = re.search(rf"^## {re.escape(category)}/ \((\d+)\)", registry_text,
                      re.MULTILINE)
    assert match, f"Registry must declare count for category {category!r}"
    return int(match.group(1))

# ... seven tests against governance/sdlc/memory/meta + cross-checks
```

## Definition of Done

### Deliverable: SKILL_REGISTRY.md reconciliation

- **D1**: The snapshot date is updated to 2026-05-23 and the per-
  category counts match the actual .md file counts on disk.
- **D2**: `docs/SKILL_REGISTRY.md` shows sdlc `(7)` with `qor-ideate`
  row present; meta `(12)` with `qor-ab-run` row present; governance
  `(6)` and memory `(7)` unchanged; snapshot date `2026-05-23`.
- **D3**: Plan + ledger + SYSTEM_STATE Phase 97 entry seal the edit.
- **D4**: `tests/test_skill_registry_per_category_currency.py` carries
  seven assertions; all pass; the per-category granularity is the
  structural countermeasure that prevents total-cancellation masking
  in future cycles.

### Deliverable: per-category currency test

- **D1**: A test exists that asserts each declared per-category count
  matches the actual .md file count, with cross-category drift guards
  preventing inverse forms of the same defect.
- **D2**: `tests/test_skill_registry_per_category_currency.py` exists
  with seven assertions covering: four per-category currency checks
  (governance/sdlc/memory/meta), inverse drift (every actual file is
  referenced), cross-category drift guard, total-matches-sum
  arithmetic guard.
- **D3**: Plan + ledger entry cover the test addition.
- **D4**: All seven tests pass twice deterministically; the test
  itself is the dogfooding shipping-correctness anchor (it would have
  caught the F8 drift the first time it ran).

## CI Coverage Exemptions

None.

## CI Commands

- `python -m pytest tests/test_skill_registry_per_category_currency.py -q` — Phase 97 per-category currency tests.
- `python -m pytest tests/ -v` — full regression.
- `python qor/scripts/check_variant_drift.py` — ci.yml.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ci.yml.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — install-smoke.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — gate-chain.
- `python qor/scripts/pr_citation_lint.py` — pr-lint.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase97-skill-registry-per-category-drift.md` — plan-internal.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase97-skill-registry-per-category-drift.md --workflows-dir .github/workflows` — Phase 89 ci-coverage.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase97-skill-registry-per-category-drift.md` — Phase 92 DoD check.
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` — Phase 95 skill-corpus-budget lint (WARN-only).
