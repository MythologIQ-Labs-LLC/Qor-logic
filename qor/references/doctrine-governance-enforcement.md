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

**seal_tag_timing** (Phase 33 wiring): the tag is created at `/qor-substantiate` Step 9.5.5, AFTER the seal commit is made at Step 9.5 — not at Step 7.5. `governance_helpers.create_seal_tag` takes a required `commit: str` parameter; the caller captures the seal SHA via `git rev-parse HEAD` between the commit and the tag call. The pre-Phase-33 flow (tagging at Step 7.5) placed the tag on the pre-seal HEAD, producing off-by-one tags across v0.19.0–v0.22.0 where `git show <tag>:pyproject.toml` showed the version one behind the tag name. See SG-Phase33-A for the historical record.

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
  Mechanically enforced by `.github/workflows/pr-lint.yml` (Phase 31 wiring):
  the `pr-lint` CI job pipes the PR body through `qor/scripts/pr_citation_lint.py`
  and fails the PR if any of the three citations is absent.
- **Tag annotation**: annotated tag created at substantiation per §4; the tag's
  annotation message links back to the PR number or commit SHA.

## 7. Session Rotation

`/qor-substantiate` Step Z calls `session.rotate()` after writing the
substantiate gate artifact. The rotate writes a fresh session_id (format
`<YYYY-MM-DDTHHMM>-<6hex>`) to the session marker, so the next `/qor-plan`
starts with a clean `.qor/gates/<session_id>/` directory.

**Why**: Phase 28 and Phase 29 sealed on the same session_id
(`2026-04-17T2335-f284b9`), and each phase's plan/audit/implement/substantiate
artifacts overwrote the prior phase's in the shared session directory. The
ledger preserves the chain, but per-phase gate-artifact archaeology is lost
when directories collide.

**How**: `qor/scripts/session.py::rotate()` calls `generate_id()` and
atomically writes the result to `MARKER_PATH`. No deletion of the prior
session's directory -- operators choose when to prune `.qor/gates/<old_sid>/`
archives.

**Enforcement**: Phase 30 substantiate Step Z is the canonical call site.
Manual session rotation (e.g., via `python qor/scripts/session.py new`) is
permitted outside the seal flow but SHOULD be rare.

**Anti-pattern**: do NOT rotate at `/qor-plan` entry (Step 0.5). Rotation at
plan-time would invalidate downstream gate checks within a single phase if
the plan needs to be re-authored after audit VETO. Rotation belongs strictly
at end-of-phase seal.

## 8. Install Currency

Source truth lives under `qor/skills/` in the repo. The operator runs
`qorlogic install --host <host>` to copy skills into the host's install
directory (`.claude/skills/`, `.kilo-code/skills/`, `.codex/skills/`, or
`.gemini/commands/`). When source changes (e.g., after pulling a new
release), the installed copy lags and the operator may unknowingly run
stale governance instructions.

**Install drift check**: `qor/scripts/install_drift_check.py` compares
byte-identical SHA256 of every `qor/skills/**/SKILL.md` against its
installed counterpart at `<skills_dir>/<skill-name>/SKILL.md`. Returns a
drift list (empty = clean). Non-blocking; WARN semantics.

**Invocation sites**:

- Ad-hoc: `python -m qor.scripts.install_drift_check --host claude --scope repo`
- Pre-phase nudge: `/qor-plan` Step 0.2 runs the check and emits a WARNING
  if drift detected. Does not abort; operator decides whether to run
  `qorlogic install` before proceeding.

**Why**: Qor-logic is a prompt system; the operator runs the INSTALLED
skills, not the repo source. Drift between installed and source means the
operator is executing older governance, which can diverge from the current
audit/enforcement layer. Detection is cheap (SHA256 scan); the fix is one
CLI invocation. Silent drift is the failure mode to prevent.

**Scope**: the check covers the SKILL.md catalog only. Reference docs,
patterns, ql-templates, and the glossary are not verified because they
are not currently installed by `qorlogic install` into the host's
runtime surface.
