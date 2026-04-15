# Plan: Phase 13 — Governance Enforcement (Branching + Versioning + Behavior)

**change_class**: feature
**Status**: Superseded by v4 (Entry #28). Historical retention; retroactive `change_class` added for forward-boundary test scope (NN >= 13).
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Triggered by**: Operator governance correction — agent had been offering "keep going" instead of substantiating-and-committing. Plus push/merge optionality, per-phase branching, version-bump-on-seal.

## Open Questions

None. All three Qs ratified pre-draft.

## Doctrine corrections

1. **No "keep going" offers**. When a phase passes substantiation, the agent commits automatically (push/merge are operator decisions). The agent's report ends with "sealed; commit `<sha>` created. Push/merge?" — not "Hold here, or continue?".
2. **Per-phase branching**. Each `/qor-plan` invocation creates `phase/<NN>-<slug>` branch off main. Substantiation merges to main only on operator decision.
3. **Version-bump on substantiation**. Plan declares change class (hotfix/feature/breaking); substantiate bumps `pyproject.toml [project].version` per class, commits the bump, creates annotated tag `v<X.Y.Z>` as the seal artifact.

## Track A — Doctrine + CLAUDE.md

### A.1 `qor/references/doctrine-governance-enforcement.md` (new)

Codifies:

- **Behavior**: agent must not offer continuation menus when work is sealable; substantiate-and-commit is automatic on green; push/merge prompts are operator-facing.
- **Branching**: `git checkout -b phase/<NN>-<slug>` at plan-write time. Branch lives until merge or abandon. No work on main.
- **Versioning**: plan header declares `change_class: hotfix|feature|breaking`. Substantiate reads pyproject version, bumps per class:
  - `hotfix` → patch (0.2.0 → 0.2.1)
  - `feature` → minor (0.2.0 → 0.3.0)
  - `breaking` → major (0.2.0 → 1.0.0)
- **Tag**: substantiate creates `v<X.Y.Z>` annotated tag pointing at the seal commit. Tag message includes Merkle seal hash + ledger entry number.
- **Push/merge optionality**: substantiate ends with prompt: `(1) push only`, `(2) push + open PR`, `(3) merge to main locally`, `(4) hold local`. Operator picks; agent does not advocate.

### A.2 `CLAUDE.md` update

3 new bullets in a new "Governance flow" section:

- After substantiation passes, commit automatically; do not offer continuation.
- Each `/qor-plan` starts a new `phase/<NN>-<slug>` branch.
- Each substantiation bumps version per plan-declared change class and creates a tag.

## Track B — Skill wiring

### B.1 `qor/skills/sdlc/qor-plan/SKILL.md`

Add Step 0.5 (after gate check, before plan dialogue):

```python
# Phase 13 wiring: create per-phase branch
phase_num, slug = derive_from_plan_filename()  # e.g., 13, governance-enforcement
import subprocess
subprocess.run(["git", "checkout", "-b", f"phase/{phase_num:02d}-{slug}"], check=True)
```

Plan header MUST declare `change_class: hotfix | feature | breaking` (default: feature). Doctrine test enforces.

### B.2 `qor/skills/governance/qor-substantiate/SKILL.md`

Add Step 7.5 (between Final Merkle Seal and Cleanup):

```python
# Phase 13 wiring: bump version + tag
import sys; sys.path.insert(0, 'qor/scripts')
import governance_helpers as gh

new_version = gh.bump_version(change_class)  # reads pyproject, computes, writes back
tag = gh.create_seal_tag(new_version, merkle_seal, ledger_entry_num)
```

Replace existing Step 9.6 "Merge Options" with explicit operator-decision prompt: 4 options (push only, push + PR, local merge, hold).

Constraint update: "NEVER offer continuation menus when work is sealable; the next decision is push/merge, not 'what next phase'."

## Track C — Script helpers

### C.1 `qor/scripts/governance_helpers.py` (new)

Library:
- `derive_phase_metadata(plan_path: Path) -> tuple[int, str]` — parse `plan-qor-phaseNN-<slug>.md` filename
- `bump_version(change_class: str, pyproject_path: Path = ...) -> str` — read pyproject, bump per class, write back, return new version
- `create_seal_tag(version: str, merkle_seal: str, ledger_entry: int) -> str` — `git tag -a v<version> -m "..."`, return tag name
- `current_branch() -> str` — `git rev-parse --abbrev-ref HEAD`
- `create_phase_branch(phase: int, slug: str) -> str` — `git checkout -b phase/<NN>-<slug>`

All atomic; no in-place mutation if any step fails.

## Track D — Doctrine tests + helper tests

### D.1 `tests/test_skill_doctrine.py` (extend with 2 new)

- `test_plan_skill_documents_branch_creation` — `qor-plan/SKILL.md` body contains "phase/" branch reference
- `test_substantiate_skill_documents_version_bump` — `qor-substantiate/SKILL.md` body references `bump_version` or `pyproject` or `tag`

### D.2 `tests/test_governance_helpers.py` (new)

5 tests:

- `test_derive_phase_metadata_from_filename` — input `plan-qor-phase13-governance-enforcement.md` → `(13, "governance-enforcement")`
- `test_bump_version_hotfix` — 0.2.0 + hotfix → 0.2.1
- `test_bump_version_feature` — 0.2.0 + feature → 0.3.0
- `test_bump_version_breaking` — 0.2.0 + breaking → 1.0.0
- `test_bump_version_invalid_class_raises` — `xyz` → ValueError

Per doctrine-test-discipline: synthetic inputs, no live state coupling.

## Affected Files

### Track A (2 new)
- `qor/references/doctrine-governance-enforcement.md`
- `CLAUDE.md` (modified — add Governance flow section)

### Track B (2 modified)
- `qor/skills/sdlc/qor-plan/SKILL.md` (add Step 0.5; require change_class header)
- `qor/skills/governance/qor-substantiate/SKILL.md` (add Step 7.5; rewrite Step 9.6; update constraints)

### Track C (1 new)
- `qor/scripts/governance_helpers.py`

### Track D (1 new + 1 modified)
- `tests/test_governance_helpers.py`
- `tests/test_skill_doctrine.py` (add 2 tests)

## Constraints

- **No GitHub Actions workflows added** (CI budget doctrine still in force)
- **All atomic writes via os.replace** (per token-efficiency + test discipline doctrines)
- **Tests before code** for the helper module (TDD per doctrine-test-discipline)
- **Reliability check mandatory**: pytest 2x consecutive identical results before commit
- **Plan header for THIS plan**: change_class = feature (introduces new behavior)

## Success Criteria

- [ ] `qor/references/doctrine-governance-enforcement.md` exists with 5 sections (behavior, branching, versioning, tag, push/merge)
- [ ] `CLAUDE.md` Governance flow section added with 3 bullets
- [ ] `qor-plan/SKILL.md` Step 0.5 + change_class requirement documented
- [ ] `qor-substantiate/SKILL.md` Step 7.5 + Step 9.6 rewrite + constraint update
- [ ] `qor/scripts/governance_helpers.py` exists with 5 functions
- [ ] `tests/test_governance_helpers.py` 5 tests passing
- [ ] `tests/test_skill_doctrine.py` 2 new tests passing
- [ ] Full suite 194/194 passing (187 prior + 5 helper + 2 doctrine + 6 skipped workflow tests)
- [ ] Drift clean
- [ ] Ledger chain verified
- [ ] Phase 13 substantiates → version 0.2.0 → 0.3.0 (feature class) → tag `v0.3.0` created
- [ ] Operator prompted with 4-option push/merge menu

## CI Commands

```bash
python -m pytest tests/test_skill_doctrine.py tests/test_governance_helpers.py -v
python -m pytest tests/
python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
git tag --list 'v*' | tail -3
```
