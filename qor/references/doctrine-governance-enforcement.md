# Doctrine: Governance Enforcement (Phase 13)

Phase-lifecycle discipline: branching, versioning, tagging, push/merge, GitHub hygiene.
Canonical, consolidated. `docs/PHASE_HISTORY.md` intentionally absent (V-1): phase
history lives in GitHub-native machinery (labeled issues + branches + PRs + tags).

## 1. Behavior

After substantiation passes, commit automatically; do not offer continuation menus
when work is sealable. The next decision is push/merge, not "what next phase."

## 2. Branching

One branch per phase: `phase/<NN>-<slug>`, cut from `main`.

Pre-checkout interdiction: `git status --porcelain` must be clean, or the operator
chooses stash / commit / abandon. Dirty-tree checkout is rejected with
`InterdictionError`.

## 3. Versioning

Plan headers declare canonical `**change_class**: hotfix|feature|breaking` (bold
markdown — V-2). Substantiate bumps `pyproject.toml` `[project].version` per class:

- `hotfix` → patch (0.2.0 → 0.2.1)
- `feature` → minor (0.2.0 → 0.3.0)
- `breaking` → major (0.2.0 → 1.0.0)

`bump_version` interdicts two conditions:

- target tag already exists (`v<new>` in `git tag --list`);
- target is a downgrade (`<=` highest existing tag).

## 4. Tag

Annotated tag `v{X.Y.Z}` at substantiation, with message template:

```
v{version}

Merkle seal: {seal_hash}
Ledger entry: #{entry_number}
Phase: {phase_number}
Class: {change_class}
```

## 5. Push/Merge

Four operator options (V-9 safety):

1. push only — `git push origin <branch>`
2. push + open PR — `gh pr create`
3. merge to main locally — **dry-run first** via `git merge --no-commit --no-ff <branch>`; abort on conflict
4. hold local

## 6. GitHub hygiene

Phase lifecycle indexed by GitHub-native machinery, not a parallel doc.

- **Issue label**: `phase:NN`, `class:hotfix|feature|breaking` (matches plan header).
  One issue per phase, titled `Phase {NN}: {slug}`, opened at plan authoring.
- **Branch name**: `phase/<NN>-<slug>` (enforced by §2).
- **PR description template**: must cite (a) plan file path `docs/plan-qor-phase<NN>*.md`,
  (b) ledger entry number `#<n>`, (c) Merkle seal hash.
- **Tag annotation**: annotated tag created at substantiation per §4; the tag's
  annotation message links back to the PR number or commit SHA.
