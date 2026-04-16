## Phase 16 v2 — Governance Polish (remediation of Entry #40 VETO)

**change_class**: feature
**Status**: Active
**Author**: QorLogic Governor
**Date**: 2026-04-16
**Branch**: `phase/16-governance-polish`
**Supersedes**: `docs/plan-qor-phase16-governance-polish.md` (VETO'd — Entry #40)

## Open Questions

None. All Entry #40 violations are mechanical fixes prescribed verbatim in the audit.

## Delta from v1 (inline-grounded per SG-016/SG-036)

v2 is v1 with 3 surgical changes closing Entry #40 violations. All grounding greps run inline during authoring — no deferrals.

### V-1 closure: inline size citation (Track B)

**Audit prescription** (verbatim): "In Track B, replace 'Current file size needs verification before implementing' with the verified line count citation: `qor-audit/SKILL.md` is 237 lines (grounded 2026-04-16 via `wc -l`); 237 + 3 = 240, under 250 Razor."

v2 Track B Changes section (replaces v1's unverified claim):

> Insert 3-line pointer between `### Step 3: Adversarial Audit` (line 88) and `#### Security Pass` (line 90).
>
> Current state (grounded 2026-04-16 via `wc -l qor/skills/governance/qor-audit/SKILL.md`): **237 lines**. Post-edit: 237 + 3 = **240 lines**. Under Razor 250 limit.

Net delta: +3 (verified).

### V-2 closure: content-movement test (Track C)

**Audit prescription** (verbatim): "Before extraction, capture a distinguishing phrase from each extracted block... Post-extraction test asserts these phrases appear in `step-extensions.md` AND do NOT appear in `qor-plan/SKILL.md` (guaranteeing the content moved rather than being copied). Name: `test_step_extensions_content_moved_not_copied`."

Distinguishing phrases verified section-unique via grep (grounded 2026-04-16):

- Step 0.5 anchor: `"InterdictionError"` — `qor/skills/sdlc/qor-plan/SKILL.md:101` only (inside Step 0.5 code block; nowhere else in the file).
- Step 1.a anchors: `"capability_shortfall"` — `qor/skills/sdlc/qor-plan/SKILL.md:137,140` only (inside Step 1.a body; nowhere else).

Note: `"agent-teams"` appears in the Step 1.a header (line 124) which remains after extraction, so it is NOT a valid movement anchor. `"capability_shortfall"` is body-only — safe.

v2 Track C test spec (replaces v1's substring-presence test):

- `test_step_extensions_content_moved_not_copied`:
  - `"InterdictionError" in step_extensions_body AND "InterdictionError" NOT in qor_plan_skill_body`
  - `"capability_shortfall" in step_extensions_body AND "capability_shortfall" NOT in qor_plan_skill_body`

Closes V-2 (Rule 4 alignment: the "verbatim extraction" rule now has a test that fails if content is copied-but-not-moved).

### V-3 closure: omit anchors (Track C)

**Audit prescription** (verbatim): "Pick one: (a) omit anchors, pointers become `See `qor/skills/sdlc/qor-plan/references/step-extensions.md` for the full protocol.` — matches Phase 15's Step 2b pointer style exactly; (b) use correct GitHub-generated anchors. Recommend (a) — symmetric with existing Step 2b precedent."

v2 Track C pointer format (picks option (a)):

```markdown
### Step 0.5: Phase branch creation (Phase 13 wiring)

See `qor/skills/sdlc/qor-plan/references/step-extensions.md` for the full protocol.
```

```markdown
### Step 1.a — Capability check (agent-teams parallel mode, Phase 8 wiring)

See `qor/skills/sdlc/qor-plan/references/step-extensions.md` for the full protocol.
```

No anchors. Matches Phase 15's Step 2b pointer exactly (same file-path-only style).

## Restated Track A — Housekeeping (unchanged from v1)

Grounded 2026-04-16:

- `docs/BACKLOG.md:24` currently reads `- [ ] [B13] Encode AI code quality doctrine...`; `docs/BACKLOG.md:62` confirms `- [x] [B13]` (Complete). Update line 24 to `- [x] [B13] (Complete — doctrine-code-quality.md, audit checklist + implement patterns updated)`.
- `docs/BACKLOG.md` "Final Inventory" table lines ~48-57 reference `ingest/internal/` paths which no longer exist (repo uses `qor/skills/`). Recommend removal; replace with one-line note referring reader to the live repo tree.
- `qor/skills/governance/qor-shadow-process/SKILL.md:27` currently reads `(see ... — deferred)`; remove " — deferred" (both referenced scripts exist; grounded Phase 14).

No tests (pure doc cleanup). Razor unaffected.

## Restated Track B — Wire doctrine into `qor-audit` (v2 with inline citation)

### Affected Files

- `qor/skills/governance/qor-audit/SKILL.md` — insert 3-line pointer at top of Step 3 (current: 237 lines, post-edit: 240)
- `tests/test_shadow_genome_doctrine.py` — 1 new test

### Changes

Insert between line 88 (`### Step 3: Adversarial Audit` header) and line 90 (`#### Security Pass` subsection):

```markdown
Before running the passes below, consult `qor/references/doctrine-shadow-genome-countermeasures.md` — the catalog of known failure patterns the Judge checks against. Cite specific SG IDs in the verdict when they apply.
```

Net delta: +3 lines. File size transition: 237 → 240 (grounded; under Razor 250).

### Unit Tests

- `test_qor_audit_skill_cites_countermeasures_doctrine` — assert `qor/skills/governance/qor-audit/SKILL.md` body contains `doctrine-shadow-genome-countermeasures.md`.

## Restated Track C — Trim `qor-plan/SKILL.md` (v2 with content-movement test)

### Affected Files

- `qor/skills/sdlc/qor-plan/references/step-extensions.md` (new) — extracted prose (~48 lines)
- `qor/skills/sdlc/qor-plan/SKILL.md` — replace Step 0.5 body (lines 90-110) and Step 1.a body (lines 125-148) with 3-line pointers; keep headers at lines 89 and 124
- `tests/test_shadow_genome_doctrine.py` — 2 new tests

### Changes

Grounded line ranges (verified 2026-04-16 via `grep -n "^### Step"`):

- Step 0.5 header: line 89; body: lines 90-110 (21 lines including trailing blank)
- Step 1.a header: line 124; body: lines 125-149 (25 lines including trailing blank)

Extract both section bodies verbatim into new file `qor/skills/sdlc/qor-plan/references/step-extensions.md` under `## Step 0.5: Phase branch creation` and `## Step 1.a: Capability check` headings.

Replace each extracted body in `qor-plan/SKILL.md` with the anchor-free pointer (see V-3 closure above).

Delta math (grounded):
- Current file size: 278 lines (verified Phase 15 + `wc -l` 2026-04-16)
- Remove Step 0.5 body: -20 lines (keep header)
- Remove Step 1.a body: -24 lines (keep header)
- Add 2 pointers (3 lines each): +6 lines
- **Net: 278 - 44 + 6 = 240 lines.** Under Razor 250.

### Unit Tests

- `test_qor_plan_step_extensions_reference_exists` — assert `qor/skills/sdlc/qor-plan/references/step-extensions.md` exists AND contains `"Step 0.5"` AND `"Step 1.a"` substrings AND `qor-plan/SKILL.md` cites the reference path.
- `test_step_extensions_content_moved_not_copied` — V-2 closure (see above): `"InterdictionError"` and `"capability_shortfall"` both appear in `step-extensions.md` AND NOT in `qor-plan/SKILL.md`. Closes SG-035 recurrence and Rule 4 gap.

## Affected Files (v2 complete)

### New (1)
- `qor/skills/sdlc/qor-plan/references/step-extensions.md`

### Modified — docs (1)
- `docs/BACKLOG.md`

### Modified — skills (3)
- `qor/skills/governance/qor-shadow-process/SKILL.md`
- `qor/skills/governance/qor-audit/SKILL.md`
- `qor/skills/sdlc/qor-plan/SKILL.md`

### Modified — tests (1)
- `tests/test_shadow_genome_doctrine.py` (+3 tests: cite, existence, movement)

## Constraints

- **Inline grounding**: every file-size claim in this plan is grounded via `wc -l` at authoring time (2026-04-16). SG-016 + SG-036 active.
- **Tests before code** for the 3 new tests.
- **Verbatim extraction enforced by test**: `test_step_extensions_content_moved_not_copied` fails if Track C copies instead of moves content.
- **Razor compliance**: `qor-plan/SKILL.md` reaches 240 lines post-edit (verified via delta math); `qor-audit/SKILL.md` reaches 240 (verified via delta math). Both under 250.
- **Reliability**: pytest 2x consecutive identical results before commit.

## Success Criteria

- [ ] Track A: BACKLOG.md B13 checked; stale `ingest/internal/` removed; qor-shadow-process deferred comment removed.
- [ ] Track B: qor-audit/SKILL.md Step 3 cites countermeasures doctrine. File at 240 lines.
- [ ] Track C: step-extensions.md exists with both sections; qor-plan/SKILL.md at 240 lines and cites the reference (no anchor syntax).
- [ ] Tests: +3 new. Baseline 228 → **231 passing**, skipped unchanged.
- [ ] `check_variant_drift.py` clean after `BUILD_REGEN=1`.
- [ ] `ledger_hash.py verify` chain valid.
- [ ] Substantiation: `0.5.0 → 0.6.0`; annotated tag `v0.6.0`.

## CI Commands

```bash
python -m pytest tests/test_shadow_genome_doctrine.py -v
python -m pytest tests/
BUILD_REGEN=1 python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
wc -l qor/skills/sdlc/qor-plan/SKILL.md qor/skills/governance/qor-audit/SKILL.md
git tag --list 'v*' | tail -3
```
