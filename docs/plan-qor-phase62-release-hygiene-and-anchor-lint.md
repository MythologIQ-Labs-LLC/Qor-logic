# Plan: Phase 62 - Release hygiene and anchor lint

**change_class**: feature

**doc_tier**: system

**originating_remediation**: post-Phase-61 residual remediation sweep

**terms_introduced**:
- term: legacy local tag quarantine
  home: docs/operations.md
- term: skill_anchor_lint
  home: qor/scripts/skill_anchor_lint.py

**boundaries**:
- limitations:
  - V1 documents the tag/worktree cleanup decision path; it does not delete tags or remove worktrees automatically.
  - V1 lint checks markdown skill headings and required anchor placement only.
- non_goals:
  - Automatic worktree merge.
  - GitHub issue closure.
  - Rewriting historical ledger entries.
- exclusions:
  - No network operations.

## Open Questions

None.

## Phase 1: Release hygiene runbook

### Affected Files

- `docs/operations.md` - add local tag/worktree collision runbook.
- `tests/test_release_hygiene_runbook.py` - NEW.

### Changes

Document the decision tree:

1. Inspect each `.claude/worktrees/*` worktree for dirty files.
2. Archive or commit any unique operator-approved changes.
3. If branch patches are already represented on `main`, abandon the worktree.
4. Delete local-only tags that point exclusively into abandoned worktree history.
5. Re-run `tests/test_changelog_tag_coverage.py`.

The recommended default is abandon + cleanup for branches whose patch content is already represented on `main`.

### Unit Tests

- `test_operations_documents_worktree_tag_collision_runbook`
- `test_runbook_requires_dirty_worktree_inspection_before_delete`
- `test_runbook_requires_changelog_tag_coverage_after_cleanup`

## Phase 2: Skill anchor lint

### Affected Files

- `qor/scripts/skill_anchor_lint.py` - NEW.
- `tests/test_skill_anchor_lint.py` - NEW.

### Changes

Public surface:

```python
def lint_skill(path: Path) -> tuple[str, ...]: ...
def main(argv: list[str] | None = None) -> int: ...
```

Checks:

- required top-level anchors exist: `<skill>`, `## Execution Protocol`, `## Constraints`, `## Success Criteria`
- each `### Step` heading starts at column 0
- `### Step Z:` appears exactly once as a top-level heading
- required anchors are not trapped inside bullet lists or code fences

### Unit Tests

- `test_lint_skill_accepts_qor_substantiate`
- `test_lint_skill_rejects_missing_step_z`
- `test_lint_skill_rejects_step_z_inside_bullet_list`
- `test_lint_skill_rejects_duplicate_step_z`
- `test_cli_returns_one_on_anchor_error`

## Phase 3: Audit integration

### Affected Files

- `qor/skills/governance/qor-audit/SKILL.md` - add anchor lint to Pre-audit lints for skill-touching plans.
- `tests/test_audit_skill_anchor_lint_wiring.py` - NEW.

### Changes

When a plan touches `qor/skills/**/SKILL.md`, `/qor-audit` runs:

```bash
python -m qor.scripts.skill_anchor_lint <changed-skill-path>
```

Findings VETO as `specification-drift` because the skill body no longer matches the expected protocol structure.

### Unit Tests

- `test_audit_skill_mentions_skill_anchor_lint`
- `test_audit_skill_routes_anchor_failures_to_specification_drift`
- `test_audit_skill_runs_anchor_lint_only_for_skill_paths`

## CI Commands

- `python -m pytest tests/test_release_hygiene_runbook.py tests/test_skill_anchor_lint.py tests/test_audit_skill_anchor_lint_wiring.py -v`
- `python -m pytest tests/test_changelog_tag_coverage.py -v`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase62-release-hygiene-and-anchor-lint.md`
