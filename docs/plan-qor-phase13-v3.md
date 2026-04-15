## Phase 13 v3 — Governance Enforcement (VETO remediation, Entry #26)

**change_class**: feature
**Status**: Active (post-VETO v2 remediation; operator ratified V-1 option (b) — single doctrine file)
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Supersedes**: `docs/plan-qor-phase13-v2.md` (v2, VETO — Ledger #26)

## Open Questions

None. Audit prescriptions quoted verbatim below; V-1 architectural choice resolved to option (b).

## Audit remediation (V-1..V-7 from Entry #26 AUDIT_REPORT §Required Remediation, quoted verbatim)

| ID | Audit instruction | Plan §addressing |
|---|---|---|
| V-1 | "Drop `docs/PHASE_HISTORY.md`, `append_phase_history_row()` helper, and `test_phase_history_lists_every_plan` doctrine test. Replace with `docs/PHASE_HYGIENE.md` (or section in `doctrine-governance-enforcement.md`) specifying GitHub conventions: One issue per phase (title: `Phase {NN}: {slug}`); Issue labels: `phase:NN`, `class:hotfix\|feature\|breaking`; Branch named per the existing rule (`phase/<NN>-<slug>`); PR descriptions cite the plan file + ledger entry + Merkle seal; Annotated tag at substantiation links back to the PR or commit; Doctrine test (replacement): `test_governance_doctrine_documents_github_hygiene` — verifies `doctrine-governance-enforcement.md` contains the keywords (issue label, PR description, branch name, tag annotation)" | §A.1 (§6 GitHub hygiene added to doctrine) + §C.1 (helper dropped) + §D.3 (test replaced) |
| V-2 | "Mandate canonical `**change_class**: <class>` (bold). Update `parse_change_class()` regex to enforce. Update doctrine test to reject non-bold variant." | §C.1 (regex) + §D.1 (`test_plans_declare_change_class` asserts bold form) |
| V-3 | "Update §D.2 header from '8 tests' to '9 tests'." | §D.2 header (9 tests) |
| V-4 | "Either define `InterdictionError` in `governance_helpers.py` (`class InterdictionError(RuntimeError): pass`) or use `RuntimeError` directly. Plan must state which." | §C.1 (define `InterdictionError(RuntimeError)` in `governance_helpers.py`) |
| V-5 | "Replace mtime tiebreak with lexicographic-suffix rule. Document: 'When multiple plans match `phase<NN>*.md`, the one with the highest sortable suffix wins (`-v3.md` > `-v2.md` > base filename). Tiebreak deterministic across CI/local.'" | §C.1 (`current_phase_plan_path` — lexicographic suffix) + §D.2 (tie-break test) |
| V-6 | "Update §A.4 citation from 'Phase 11D S-1' to `docs/research-brief-full-audit-2026-04-15.md §S-1` (verified file)." | §A.4 (Rule 4 citation) — verified: `docs/research-brief-full-audit-2026-04-15.md:15,23` |
| V-7 | "Resolves automatically if V-1 accepted." | Resolved (see V-1) |

## Track A — Doctrines + CLAUDE.md

### A.1 `qor/references/doctrine-governance-enforcement.md` (new, 6 sections)

Sections: (1) Behavior, (2) Branching, (3) Versioning, (4) Tag, (5) Push/Merge, (6) GitHub hygiene.

- **Behavior**: agent does not offer continuation menus when work is sealable. Substantiate-and-commit auto on green; operator decides push/merge.
- **Branching**: per-phase, `phase/<NN>-<slug>` from main. Pre-checkout interdiction: `git status --porcelain` must be clean OR operator chooses (stash/commit/abandon).
- **Versioning**: plan header declares canonical `**change_class**: hotfix|feature|breaking` (V-2: bold markdown). Substantiate bumps `pyproject.toml [project].version`:
  - hotfix → patch (0.2.0 → 0.2.1)
  - feature → minor (0.2.0 → 0.3.0)
  - breaking → major (0.2.0 → 1.0.0)
- **Tag** (V-8 template): annotated tag `v{X.Y.Z}`:
  ```
  v{version}

  Merkle seal: {seal_hash}
  Ledger entry: #{entry_number}
  Phase: {phase_number}
  Class: {change_class}
  ```
- **Push/merge optionality (V-9 safety)**: 4 operator options:
  1. push only (`git push origin <branch>`)
  2. push + open PR (`gh pr create`)
  3. merge to main locally — dry-run first: `git merge --no-commit --no-ff <branch>`; on conflict, abort with prompt
  4. hold local
- **GitHub hygiene (V-1 replacement for PHASE_HISTORY.md)**: phase lifecycle indexed by GitHub-native machinery, not a parallel doc. Conventions:
  - **Issue per phase**: title `Phase {NN}: {slug}`; opened at plan authoring.
  - **Issue labels**: `phase:NN`, `class:hotfix|feature|breaking` (matches plan header).
  - **Branch name**: `phase/<NN>-<slug>` (enforced by §Branching).
  - **PR description template**: must cite (a) plan file path `docs/plan-qor-phase<NN>*.md`, (b) ledger entry number `#<n>`, (c) Merkle seal hash.
  - **Annotated tag**: created at substantiation (§Tag); tag message links back to the PR number or commit SHA.

### A.2 `CLAUDE.md` update

New "Governance flow" section (3 bullets):
- After substantiation passes, commit automatically; do not offer continuation.
- Each `/qor-plan` starts a new `phase/<NN>-<slug>` branch (digit phase numbers).
- Each substantiation bumps version per plan-declared `**change_class**:` and creates `v{X.Y.Z}` tag.

### A.3 [REMOVED — V-1]

`docs/PHASE_HISTORY.md` dropped. Phase index lives in GitHub issues/labels/branches/PRs/tags per §A.1 §6.

### A.4 `qor/references/doctrine-test-discipline.md` Rule 4 (V-6 citation fix)

New Rule 4 added: **"Rule = Test"**

> When a plan introduces a new rule (a constraint, format, requirement, or convention), the same plan MUST add the doctrine test enforcing it. Rule without test = optional. Verified instances: `docs/research-brief-full-audit-2026-04-15.md §S-1` (`gate_writes` declared without execution test); Phase 13 V-1 (`change_class:` declared without parser test).

## Track B — Skill wiring

### B.1 `qor/skills/sdlc/qor-plan/SKILL.md`

Add Step 0.5 (per V-5 of Entry #25, retained from v2):

```python
# Phase 13 wiring: dirty-tree check + per-phase branch
import subprocess, sys
sys.path.insert(0, 'qor/scripts')
import governance_helpers as gh

result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
if result.stdout.strip():
    raise gh.InterdictionError(
        "Working tree dirty; operator must choose stash/commit/abandon before plan branch"
    )

phase_num, slug = gh.derive_phase_metadata(plan_path)  # raises on letter-suffix legacy plans
subprocess.run(["git", "checkout", "-b", f"phase/{phase_num:02d}-{slug}"], check=True)
```

Plan header MUST declare `**change_class**: hotfix | feature | breaking` (bold — V-2). Doctrine test `test_plans_declare_change_class` enforces.

### B.2 `qor/skills/governance/qor-substantiate/SKILL.md`

**Verbatim current Step 9.6 (V-10 quote, verified at `qor/skills/governance/qor-substantiate/SKILL.md:245-247`)**:

> "### Step 9.6: Merge Options
>
> Prompt user with three options: (1) merge to main, (2) create PR, (3) stay on branch. If version changed, offer to create annotated tag."

**Replacement**: 4-option menu per Track A.1 §Push/Merge (push only / push+PR / local-merge with dry-run / hold).

Add Step 7.5 (between Final Merkle Seal and Cleanup):

```python
# Phase 13 wiring: bump version + tag (no history-row append — V-1 dropped that)
import sys; sys.path.insert(0, 'qor/scripts')
import governance_helpers as gh

plan_path = gh.current_phase_plan_path()              # V-5: lexicographic suffix
change_class = gh.parse_change_class(plan_path)       # V-2: bold-form enforced
new_version = gh.bump_version(change_class)           # V-6: target > current tag
tag = gh.create_seal_tag(
    new_version, merkle_seal, ledger_entry_num, phase_num, change_class,
)
```

Constraint update: "NEVER offer continuation menus when work is sealable; the next decision is push/merge, not 'what next phase'."

## Track C — Script helpers

### C.1 `qor/scripts/governance_helpers.py` (new)

Module-level exception + 7 functions (was 8 in v2; `append_phase_history_row` dropped per V-1):

```python
class InterdictionError(RuntimeError):
    """Raised when a governance precondition blocks an operation (V-4)."""
```

- `current_branch() -> str` — `git rev-parse --abbrev-ref HEAD`.
- `derive_phase_metadata(plan_path: Path) -> tuple[int, str]` — parses `plan-qor-phase(\d+)-([a-z0-9-]+)\.md`. Raises `ValueError` on letter-suffix legacy plans (11d grandfathered).
- `current_phase_plan_path() -> Path` — V-5: parses current branch (`phase/<NN>-...`); globs `docs/plan-qor-phase<NN>*.md`; returns the entry with the **highest lexicographic filename** (so `-v3.md` > `-v2.md` > `-governance-enforcement.md`). Deterministic across CI/local — independent of mtime.
- `parse_change_class(plan_path: Path) -> str` — V-2: regex `r'^\*\*change_class\*\*:\s+(hotfix|feature|breaking)\s*$'` (multiline, anchored). Returns one of `{hotfix, feature, breaking}`. Raises `ValueError` on missing, non-bold, or invalid.
- `bump_version(change_class: str, pyproject_path: Path = ...) -> str` — reads pyproject; computes new version per class; raises `InterdictionError` if tag `v<new>` already exists OR if target <= current tag (V-6). Writes pyproject atomically via `os.replace`. Returns new version.
- `create_seal_tag(version, seal, entry, phase, klass) -> str` — V-8: annotated tag with templated message.
- `create_phase_branch(phase: int, slug: str) -> str` — pre-checks dirty tree; checks out.

All atomic; no in-place mutation if any step fails.

## Track D — Tests

### D.1 `tests/test_skill_doctrine.py` (extend with 3 new — per v2 V-1)

- `test_plan_skill_documents_branch_creation` — `qor-plan/SKILL.md` body contains `phase/` branch reference.
- `test_substantiate_skill_documents_version_bump` — `qor-substantiate/SKILL.md` body references `bump_version` or `create_seal_tag`.
- `test_plans_declare_change_class` — every `docs/plan-qor-phase<digits>*.md` (digits-only; 11d/12-v2 legacy filenames excluded by pattern) header contains canonical `**change_class**: <hotfix|feature|breaking>` with bold markers (V-2).

### D.2 `tests/test_governance_helpers.py` (new — 9 tests per V-3)

- `test_derive_phase_metadata_from_digit_filename` — `plan-qor-phase13-governance-enforcement.md` → `(13, "governance-enforcement")`.
- `test_derive_phase_metadata_rejects_letter_suffix` — `plan-qor-phase11d-doctrine-tests.md` → `ValueError`.
- `test_current_phase_plan_path_prefers_highest_suffix` — V-5: when `plan-qor-phase13-governance-enforcement.md`, `-v2.md`, `-v3.md` coexist in tmp dir on branch `phase/13-x`, returns `-v3.md`.
- `test_parse_change_class_feature` — synthetic plan with `**change_class**: feature` → `"feature"`.
- `test_parse_change_class_invalid_raises` — `**change_class**: xyz` → `ValueError`.
- `test_parse_change_class_rejects_non_bold` — V-2: plan with `change_class: feature` (no bold) → `ValueError`.
- `test_bump_version_hotfix` — 0.2.0 + hotfix → 0.2.1.
- `test_bump_version_feature` — 0.2.0 + feature → 0.3.0.
- `test_bump_version_breaking` — 0.2.0 + breaking → 1.0.0.

(9 tests total; header count matches body — V-3 closed.)

### D.3 `tests/test_skill_doctrine.py` extra (V-1 replacement)

- `test_governance_doctrine_documents_github_hygiene` — `qor/references/doctrine-governance-enforcement.md` body contains all four keywords: `issue label`, `PR description`, `branch name`, `tag annotation` (case-insensitive substring match).

(Total new doctrine tests: 4 — same count as v2, but `test_phase_history_lists_every_plan` replaced by the hygiene test.)

## Affected Files

### Track A (3 new + 1 modified)
- `qor/references/doctrine-governance-enforcement.md` (new, 6 sections)
- `qor/references/doctrine-test-discipline.md` (modified — Rule 4 added with V-6 citation)
- `CLAUDE.md` (modified — Governance flow section)
- ~~`docs/PHASE_HISTORY.md`~~ **DROPPED (V-1)**

### Track B (2 modified)
- `qor/skills/sdlc/qor-plan/SKILL.md`
- `qor/skills/governance/qor-substantiate/SKILL.md`

### Track C (1 new)
- `qor/scripts/governance_helpers.py` (7 functions + `InterdictionError` class)

### Track D (1 new + 1 modified)
- `tests/test_governance_helpers.py` (9 tests — per V-3)
- `tests/test_skill_doctrine.py` (4 new tests — 3 from D.1 + 1 hygiene from D.3)

## Constraints

- **No GitHub Actions workflows**.
- **All atomic writes via `os.replace`**.
- **Tests before code** for `governance_helpers` (per `doctrine-test-discipline.md`).
- **Reliability check mandatory**: pytest 2x consecutive identical results before commit (per CLAUDE.md test-discipline).
- **Plan eats its own dogfood**: header declares `**change_class**: feature` (V-7 / bold per V-2) ✓.
- **Phase 13 implemented on `main` directly** (bootstrap exception); subsequent phases use new branching rule.
- **V-1 enforced**: no `docs/PHASE_HISTORY.md` file anywhere; phase index is GitHub-native only.

## Success Criteria

- [ ] `qor/references/doctrine-governance-enforcement.md` exists with 6 sections including §6 GitHub hygiene (4 mandated keywords present).
- [ ] `qor/references/doctrine-test-discipline.md` Rule 4 "Rule = Test" present; citation reads `docs/research-brief-full-audit-2026-04-15.md §S-1`.
- [ ] **No `docs/PHASE_HISTORY.md` file exists** (V-1 enforcement).
- [ ] `CLAUDE.md` Governance flow section added.
- [ ] `qor-plan/SKILL.md` Step 0.5 documents dirty-tree check + branch creation + bold `**change_class**:` requirement.
- [ ] `qor-substantiate/SKILL.md` Step 7.5 documents bump+tag (no history append); Step 9.6 quotes existing text verbatim + provides 4-option replacement.
- [ ] `qor/scripts/governance_helpers.py` exists with `InterdictionError` class + 7 functions.
- [ ] `tests/test_governance_helpers.py` 9 tests passing (header count matches body).
- [ ] `tests/test_skill_doctrine.py` 4 new tests passing (including `test_governance_doctrine_documents_github_hygiene`).
- [ ] Full suite: 200 passing + 6 skipped (baseline 187 + 9 helper + 4 doctrine = 200).
- [ ] `check_variant_drift.py` clean.
- [ ] `ledger_hash.py verify` chain valid.
- [ ] Substantiation produces version `0.2.0 → 0.3.0` + annotated tag `v0.3.0`.
- [ ] Operator prompted with 4-option push/merge menu (not 3-option).

## CI Commands

```bash
python -m pytest tests/test_skill_doctrine.py tests/test_governance_helpers.py -v
python -m pytest tests/
python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
git tag --list 'v*' | tail -3
```
