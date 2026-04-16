## Phase 16 — Governance Polish (3 tracks: doctrine wiring, housekeeping, SKILL.md trim)

**change_class**: feature
**Status**: Active
**Author**: QorLogic Governor
**Date**: 2026-04-16
**Branch**: `phase/16-governance-polish`

## Open Questions

None. Three tracks, file-disjoint, bundled into a single phase to minimize governance overhead. Track B's new wiring is the reason for `feature` change class; A and C are refactor/cleanup within the same phase.

## Track A — Housekeeping (pure doc cleanup, no tests)

### Affected Files

- `docs/BACKLOG.md` — fix stale B13 checkbox; update stale `ingest/internal/` inventory paths
- `qor/skills/governance/qor-shadow-process/SKILL.md` — remove stale " — deferred" comment

### Changes

**`docs/BACKLOG.md:24`**: change `- [ ] [B13]` to `- [x] [B13] (Complete — doctrine-code-quality.md, audit checklist + implement patterns updated)` (matching the existing line 62 confirmation).

**`docs/BACKLOG.md` "Final Inventory" table (lines ~48-57)**: the table references paths under `ingest/internal/` which no longer exist (repo uses `qor/skills/`, `qor/references/`, etc.). Replace the Location column values with current canonical paths, OR remove the table entirely with a note "inventory maintained live in the repo tree; see `qor/` root." Recommend removal — inventory maintenance is a grep away.

**`qor/skills/governance/qor-shadow-process/SKILL.md:27`**: change
```
(see `qor/scripts/check_shadow_threshold.py` and `create_shadow_issue.py` — deferred).
```
to
```
(see `qor/scripts/check_shadow_threshold.py` and `create_shadow_issue.py`).
```
Both scripts exist and work (verified in Phase 14).

## Track B — Wire countermeasures doctrine into `qor-audit`

### Affected Files

- `qor/skills/governance/qor-audit/SKILL.md` — insert 3-line pointer at top of Step 3
- `tests/test_shadow_genome_doctrine.py` — 1 new test

### Changes

Insert between the existing `### Step 3: Adversarial Audit` header (line 88) and its first subsection `#### Security Pass` (line 90):

```markdown
Before running the passes below, consult `qor/references/doctrine-shadow-genome-countermeasures.md` — the catalog of known failure patterns the Judge checks against. Cite specific SG IDs in the verdict when they apply.
```

Net delta to `qor-audit/SKILL.md`: +3 lines (the paragraph + surrounding blank). Current file size needs verification before implementing.

### Unit Tests

- `test_qor_audit_skill_cites_countermeasures_doctrine` — assert `qor/skills/governance/qor-audit/SKILL.md` body contains `doctrine-shadow-genome-countermeasures.md`. Mirrors existing `test_qor_plan_skill_cites_countermeasures_doctrine`.

## Track C — Trim `qor-plan/SKILL.md` to ≤250 lines

### Affected Files

- `qor/skills/sdlc/qor-plan/references/step-extensions.md` (new) — extracted prose
- `qor/skills/sdlc/qor-plan/SKILL.md` — replace extracted sections with 2 pointers
- `tests/test_shadow_genome_doctrine.py` — 1 new test

### Changes

Extract two verbose sections verbatim into a new companion reference:

- Step 0.5 (lines 89-110 of `qor-plan/SKILL.md`, ~22 lines): "Phase branch creation (Phase 13 wiring)" — pre-checkout interdiction, phase-branch naming, dirty-tree handling.
- Step 1.a (lines 124-149 of `qor-plan/SKILL.md`, ~26 lines): "Capability check (agent-teams parallel mode, Phase 8 wiring)" — solo vs. parallel mode dispatch.

Both sections copied verbatim into `qor/skills/sdlc/qor-plan/references/step-extensions.md` under `## Step 0.5: ...` and `## Step 1.a: ...` headers.

In `qor-plan/SKILL.md`, replace each extracted section body with a 3-line pointer (keeping the original `### Step X.Y: ...` headers for discoverability):

```markdown
### Step 0.5: Phase branch creation (Phase 13 wiring)

See `qor/skills/sdlc/qor-plan/references/step-extensions.md#step-05` for the full protocol.
```

```markdown
### Step 1.a — Capability check (agent-teams parallel mode, Phase 8 wiring)

See `qor/skills/sdlc/qor-plan/references/step-extensions.md#step-1a` for the full protocol.
```

Net delta to `qor-plan/SKILL.md`: -48 + 8 = **-40 lines**. File size 278 → ~238. Under Razor 250 limit.

### Unit Tests

- `test_qor_plan_step_extensions_reference_exists` — assert `qor/skills/sdlc/qor-plan/references/step-extensions.md` exists AND contains both "Step 0.5" and "Step 1.a" substrings AND that `qor-plan/SKILL.md` cites the reference path.

## Affected Files (summary)

### New (1)
- `qor/skills/sdlc/qor-plan/references/step-extensions.md`

### Modified — docs (1)
- `docs/BACKLOG.md`

### Modified — skills (3)
- `qor/skills/governance/qor-shadow-process/SKILL.md`
- `qor/skills/governance/qor-audit/SKILL.md`
- `qor/skills/sdlc/qor-plan/SKILL.md`

### Modified — tests (1)
- `tests/test_shadow_genome_doctrine.py` (+2 tests)

## Constraints

- **No behavior changes**: Tracks A and C are pure refactor; Track B is documentation wiring (no runtime impact).
- **Tests before code** for Track B and Track C new tests.
- **Track C extraction must be verbatim**: step-extensions.md body matches the extracted SKILL.md sections character-for-character (prevents semantic drift). Grep-verify after extraction.
- **Razor compliance**: `qor-plan/SKILL.md` must be ≤250 lines after trim. Verify with `wc -l`.
- **Reliability**: pytest 2x consecutive identical results before commit.

## Success Criteria

- [ ] Track A: BACKLOG.md B13 checked; stale `ingest/internal/` removed or updated; qor-shadow-process deferred comment removed.
- [ ] Track B: qor-audit/SKILL.md Step 3 cites countermeasures doctrine.
- [ ] Track C: step-extensions.md exists; qor-plan/SKILL.md ≤250 lines and cites the reference.
- [ ] Tests: +2 new. Baseline 228 → **230 passing**, skipped unchanged.
- [ ] `check_variant_drift.py` clean after `BUILD_REGEN=1`.
- [ ] `ledger_hash.py verify` chain valid.
- [ ] Substantiation: `0.5.0 → 0.6.0`; annotated tag `v0.6.0`.

## CI Commands

```bash
python -m pytest tests/test_shadow_genome_doctrine.py -v
python -m pytest tests/
BUILD_REGEN=1 python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
wc -l qor/skills/sdlc/qor-plan/SKILL.md
git tag --list 'v*' | tail -3
```
