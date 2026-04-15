## Phase 13 v4 — Governance Enforcement (VETO remediation, Entry #27)

**change_class**: feature
**Status**: Active (post-VETO v3 remediation; 4 W-* spec patches applied)
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Supersedes**: `docs/plan-qor-phase13-v3.md` (v3, VETO — Ledger #27)

## Open Questions

None. Audit prescriptions quoted verbatim and applied.

## Audit remediation (W-1..W-4 from Entry #27 AUDIT_REPORT §Required Remediation)

| ID | Audit instruction (quoted) | Plan §addressing |
|---|---|---|
| W-1 | "Either rewrite §A.1 §6 bullet from 'Annotated tag: created at substantiation...' to 'Tag annotation: annotated tag created at substantiation...' (preserves meaning, satisfies keyword). OR change D.3 keyword from 'tag annotation' to 'annotated tag' in test spec. Recommend the former (audit verbiage in Entry #26 used 'tag annotation' — keeping test keyword stable preserves cross-entry traceability)." | §A.1 §6 bullet reworded (former option) |
| W-2 | "Constrain `test_plans_declare_change_class` scope. Recommended spec: 'every `docs/plan-qor-phase<NN>*.md` where `NN >= 13` (Phase 13 is the forward-boundary; pre-13 plans authored before the rule existed, grandfathered).' Similarly specify: `test_derive_phase_metadata_rejects_letter_suffix` uses `plan-qor-phase11d-*` as the single exemplar of letter-suffix legacy (no other letter-suffix plans exist in repo)." | §D.1 + §D.2 (numeric boundary + single exemplar) |
| W-3 | "Insert in §B.2 Step 7.5 snippet between `plan_path = ...` and `new_version = ...`: `phase_num, slug = gh.derive_phase_metadata(plan_path)`" | §B.2 Step 7.5 snippet |
| W-4 | "Add to §D.2 test list: `test_bump_version_raises_on_tag_collision`... `test_bump_version_raises_on_downgrade`... Update §D.2 header from '9 tests' to '11 tests'. Update Success Criteria arithmetic: baseline 187 + 11 helper + 4 doctrine = 202 passing + 6 skipped." | §D.2 (11 tests) + §Success Criteria (202) |

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
  - **Issue label**: `phase:NN`, `class:hotfix|feature|breaking` (matches plan header). Issue per phase titled `Phase {NN}: {slug}`, opened at plan authoring.
  - **Branch name**: `phase/<NN>-<slug>` (enforced by §Branching).
  - **PR description template**: must cite (a) plan file path `docs/plan-qor-phase<NN>*.md`, (b) ledger entry number `#<n>`, (c) Merkle seal hash.
  - **Tag annotation** (W-1 literal): annotated tag created at substantiation per §Tag; the tag's annotation message links back to the PR number or commit SHA.

### A.2 `CLAUDE.md` update

New "Governance flow" section (3 bullets):
- After substantiation passes, commit automatically; do not offer continuation.
- Each `/qor-plan` starts a new `phase/<NN>-<slug>` branch (digit phase numbers).
- Each substantiation bumps version per plan-declared `**change_class**:` and creates `v{X.Y.Z}` tag.

### A.3 [REMOVED — V-1]

`docs/PHASE_HISTORY.md` dropped. Phase index lives in GitHub issues/labels/branches/PRs/tags per §A.1 §6.

### A.4 `qor/references/doctrine-test-discipline.md` Rule 4

New Rule 4 added: **"Rule = Test"**

> When a plan introduces a new rule (a constraint, format, requirement, or convention), the same plan MUST add the doctrine test enforcing it. Rule without test = optional. Verified instances: `docs/research-brief-full-audit-2026-04-15.md §S-1` (`gate_writes` declared without execution test); Phase 13 V-1 (`change_class:` declared without parser test); Phase 13 W-4 (`bump_version` interdiction declared without test).

## Track B — Skill wiring

### B.1 `qor/skills/sdlc/qor-plan/SKILL.md`

Add Step 0.5:

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
# Phase 13 wiring: bump version + tag (W-3 fix: phase_num derived explicitly)
import sys; sys.path.insert(0, 'qor/scripts')
import governance_helpers as gh

plan_path = gh.current_phase_plan_path()              # V-5: lexicographic suffix
phase_num, slug = gh.derive_phase_metadata(plan_path) # W-3: derive before use
change_class = gh.parse_change_class(plan_path)       # V-2: bold-form enforced
new_version = gh.bump_version(change_class)           # V-6 + W-4: tag-collision + downgrade interdiction
tag = gh.create_seal_tag(
    new_version, merkle_seal, ledger_entry_num, phase_num, change_class,
)
```

Constraint update: "NEVER offer continuation menus when work is sealable; the next decision is push/merge, not 'what next phase'."

## Track C — Script helpers

### C.1 `qor/scripts/governance_helpers.py` (new)

Module-level exception + 7 functions:

```python
class InterdictionError(RuntimeError):
    """Raised when a governance precondition blocks an operation (V-4)."""
```

- `current_branch() -> str` — `git rev-parse --abbrev-ref HEAD`.
- `derive_phase_metadata(plan_path: Path) -> tuple[int, str]` — parses `plan-qor-phase(\d+)-([a-z0-9-]+)\.md`. Raises `ValueError` on letter-suffix legacy plans (11d single known exemplar; grandfathered).
- `current_phase_plan_path() -> Path` — V-5: parses current branch (`phase/<NN>-...`); globs `docs/plan-qor-phase<NN>*.md`; returns the entry with the **highest lexicographic filename** (so `-v4.md` > `-v3.md` > `-v2.md` > `-governance-enforcement.md`). Deterministic across CI/local — independent of mtime.
- `parse_change_class(plan_path: Path) -> str` — V-2: regex `r'^\*\*change_class\*\*:\s+(hotfix|feature|breaking)\s*$'` (multiline, anchored). Returns one of `{hotfix, feature, breaking}`. Raises `ValueError` on missing, non-bold, or invalid.
- `bump_version(change_class: str, pyproject_path: Path = ...) -> str` — reads pyproject; computes new version per class; raises `InterdictionError` if (a) tag `v<new>` already exists in `git tag --list`, OR (b) `new <= current_tag_version` (downgrade guard). Writes pyproject atomically via `os.replace`. Returns new version string.
- `create_seal_tag(version, seal, entry, phase, klass) -> str` — V-8: annotated tag with templated message.
- `create_phase_branch(phase: int, slug: str) -> str` — pre-checks dirty tree; checks out.

All atomic; no in-place mutation if any step fails.

## Track D — Tests

### D.1 `tests/test_skill_doctrine.py` (extend with 3 new)

- `test_plan_skill_documents_branch_creation` — `qor-plan/SKILL.md` body contains `phase/` branch reference.
- `test_substantiate_skill_documents_version_bump` — `qor-substantiate/SKILL.md` body references `bump_version` or `create_seal_tag`.
- `test_plans_declare_change_class` — **W-2 fix**: every `docs/plan-qor-phase<NN>*.md` where `NN >= 13` (Phase 13 is the forward-boundary; pre-13 plans grandfathered — authored before the rule existed) header contains canonical `**change_class**: <hotfix|feature|breaking>` with bold markers (V-2). Test derives `NN` via `re.match(r'plan-qor-phase(\d+)', filename)` and filters.

### D.2 `tests/test_governance_helpers.py` (new — 11 tests per W-4)

- `test_derive_phase_metadata_from_digit_filename` — `plan-qor-phase13-governance-enforcement.md` → `(13, "governance-enforcement")`.
- `test_derive_phase_metadata_rejects_letter_suffix` — **W-2 fix**: uses `plan-qor-phase11d-doctrine-tests.md` as the single known exemplar of letter-suffix legacy; expects `ValueError`.
- `test_current_phase_plan_path_prefers_highest_suffix` — V-5: when `plan-qor-phase13-governance-enforcement.md`, `-v2.md`, `-v3.md`, `-v4.md` coexist in tmp dir on branch `phase/13-x` (monkeypatched `current_branch`), returns `-v4.md`.
- `test_parse_change_class_feature` — synthetic plan with `**change_class**: feature` → `"feature"`.
- `test_parse_change_class_invalid_raises` — `**change_class**: xyz` → `ValueError`.
- `test_parse_change_class_rejects_non_bold` — V-2: plan with `change_class: feature` (no bold) → `ValueError`.
- `test_bump_version_hotfix` — pyproject 0.2.0, no existing tags; `bump_version("hotfix")` → `"0.2.1"`; pyproject updated.
- `test_bump_version_feature` — pyproject 0.2.0, no existing tags; `bump_version("feature")` → `"0.3.0"`.
- `test_bump_version_breaking` — pyproject 0.2.0, no existing tags; `bump_version("breaking")` → `"1.0.0"`.
- `test_bump_version_raises_on_tag_collision` — **W-4 fix**: pyproject 0.2.0; monkeypatched `git tag --list` returns `v0.3.0` already present; `bump_version("feature")` raises `InterdictionError`.
- `test_bump_version_raises_on_downgrade` — **W-4 fix**: pyproject 0.2.0; monkeypatched `git tag --list` returns `v0.5.0` as current highest; `bump_version("hotfix")` would produce 0.2.1 which is < 0.5.0; raises `InterdictionError` (downgrade guard).

(11 tests total; header count matches body — V-3 + W-4 closed.)

### D.3 `tests/test_skill_doctrine.py` extra (V-1 replacement)

- `test_governance_doctrine_documents_github_hygiene` — `qor/references/doctrine-governance-enforcement.md` body contains all four keywords (case-insensitive substring match): `issue label`, `PR description`, `branch name`, `tag annotation`. Keywords are literal strings; W-1 verified by grep: §A.1 §6 bullets contain each literal.

(Total new doctrine tests: 4.)

## Affected Files

### Track A (2 new + 2 modified)
- `qor/references/doctrine-governance-enforcement.md` (new, 6 sections)
- `qor/references/doctrine-test-discipline.md` (modified — Rule 4 added)
- `CLAUDE.md` (modified — Governance flow section)

### Track B (2 modified)
- `qor/skills/sdlc/qor-plan/SKILL.md`
- `qor/skills/governance/qor-substantiate/SKILL.md`

### Track C (1 new)
- `qor/scripts/governance_helpers.py` (7 functions + `InterdictionError` class)

### Track D (1 new + 1 modified)
- `tests/test_governance_helpers.py` (11 tests — per W-4)
- `tests/test_skill_doctrine.py` (4 new tests — 3 from D.1 + 1 hygiene from D.3)

## Constraints

- **No GitHub Actions workflows**.
- **All atomic writes via `os.replace`**.
- **Tests before code** for `governance_helpers` (per `doctrine-test-discipline.md`).
- **Reliability check mandatory**: pytest 2x consecutive identical results before commit.
- **Plan eats its own dogfood**: header declares `**change_class**: feature` (bold per V-2) ✓.
- **Phase 13 implemented on `main` directly** (bootstrap exception); subsequent phases use new branching rule.
- **V-1 enforced**: no `docs/PHASE_HISTORY.md` file anywhere; phase index is GitHub-native only.
- **W-1 discipline**: doctrine §6 keyword strings are literal copies of test substrings (no paraphrase between test and doctrine).

## Success Criteria

- [ ] `qor/references/doctrine-governance-enforcement.md` exists with 6 sections; §6 contains literal substrings `issue label`, `PR description`, `branch name`, `tag annotation` (grep-verified).
- [ ] `qor/references/doctrine-test-discipline.md` Rule 4 "Rule = Test" present; citation reads `docs/research-brief-full-audit-2026-04-15.md §S-1` + includes W-4 instance.
- [ ] **No `docs/PHASE_HISTORY.md` file exists** (V-1 enforcement).
- [ ] `CLAUDE.md` Governance flow section added.
- [ ] `qor-plan/SKILL.md` Step 0.5 documents dirty-tree check + branch creation + bold `**change_class**:` requirement.
- [ ] `qor-substantiate/SKILL.md` Step 7.5 documents `derive_phase_metadata` + bump + tag (no history append); Step 9.6 quotes existing text verbatim + provides 4-option replacement.
- [ ] `qor/scripts/governance_helpers.py` exists with `InterdictionError` class + 7 functions; `bump_version` interdicts tag collision AND downgrade.
- [ ] `tests/test_governance_helpers.py` 11 tests passing (header matches body; tag-collision + downgrade covered per W-4).
- [ ] `tests/test_skill_doctrine.py` 4 new tests passing (including `test_governance_doctrine_documents_github_hygiene`; `test_plans_declare_change_class` scoped to `phase >= 13`).
- [ ] Full suite: **202 passing + 6 skipped** (baseline 187 + 11 helper + 4 doctrine = 202).
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
