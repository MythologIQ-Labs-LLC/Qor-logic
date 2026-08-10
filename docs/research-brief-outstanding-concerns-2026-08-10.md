# Research Brief

**Date**: 2026-08-10
**Analyst**: The Qor-logic Analyst
**Target**: The outstanding-concerns cluster carried in conversation from the Phase 206-211 session
**Scope**: Which items are real defects vs accepted debt; which line owns each; the correct GitHub recording shape

---

## Executive Summary

Six items were carried. **Four are real and untracked; two are not defects at all.** One of the two, skill-size headroom, was already closed by GH #266 with a test-enforced lock that is currently holding, so re-filing it would have re-opened solved work. Item 3 is materially larger than "a missing CI step": ruff is not a declared project tool anywhere, so this is an adopt-or-decline decision carrying 254 pre-existing findings, not a gap to fill.

**No umbrella issue.** The #247 pattern fits a cluster with a shared cause; these four have none. Four independent issues is the honest shape.

All four real items belong to the public, solo-developer-first line. None route to the enterprise line.

## Findings

### 1. `test_merge_velocity_check` flake — REAL, three recorded occurrences

Not the one-off it was described as. Three distinct incidents appear in the record:

- `829d17c` — "seal: phase 161 - deterministic merge-velocity test naming (v0.110.3)": `hash()` collisions produced duplicate `feat-<n>` branch names, exit 128. Fixed by sha1 in `_feat_suffix`.
- `58fe2fa` — "diagnosable merge_velocity git error (PR #284 CI)", on the Phase 194 seal.
- The Phase 206 merge commit: `git merge --no-ff feat-b8c90baa` exit 2, passed on re-run.

Three occurrences across three phases is a recurrence pattern, not noise. Phase 209 removed one mechanism (ambient git config; `tests/test_merge_velocity_check.py:19` now imports `run_git, scratch_env`) and made fixture failures report git's own reason. It was never reproduced locally, so the removal is unproven.

**Status**: real, mechanism-removed, unverified. Needs a watch condition rather than a fix.

### 2. Branch backlog — REAL, and an order of magnitude larger than reported

`git ls-remote --heads origin` -> 129 heads. `git branch -r --merged origin/main` -> **111 merged**, 18 unmerged. The "6 merged phase branches" figure counted only this session's. `workspace_fragility_check` has been returning `branch_only` all session on `active_branch_count >= 10`.

**Status**: real housekeeping. Deleting merged branches is low-risk and mechanical; the 18 unmerged need per-branch judgment and are a separate question.

### 3. Ruff — NOT adopted, and therefore a decision rather than a defect

`grep -rn "ruff" pyproject.toml setup.cfg .pre-commit-config.yaml` returns nothing. The dev extra is `dev = ["pytest>=8"]` (`pyproject.toml:28`). Ruff appears in no workflow, no pre-commit config, and no dependency declaration. `python -m ruff check qor/ tests/` -> **254 errors, 210 auto-fixable**.

Every "ruff clean" claim during the session was made with a locally installed ruff against individually touched files. Those claims were true and incidental; they were never project-enforced.

**Status**: not a gap in an adopted control. Adopting ruff means adding a dependency, triaging 254 findings, and choosing a rule set. Declining it and removing the assumption is equally legitimate.

### 4. Governance-skill headroom — NOT a defect; the existing control is holding

GH **#266** ("qor-audit + qor-substantiate SKILL.md within 1 KB of the 40 KB EXCEEDED budget") is CLOSED, shipped in Phase 178 (v0.122.1, released v0.130.0 via PR #276), and its closure comment records a progressive-disclosure pass plus a **test-enforced headroom lock**.

Measured now, LF-normalized:

| Skill | bytes | lock | slack |
|---|---|---|---|
| `qor-audit` | 39416 | 39936 | 520 |
| `qor-substantiate` | 39576 | 39936 | 360 |

Both under the lock. Phase 207 breached it, the test failed immediately, and the edit was trimmed — the control functioning exactly as designed, not evidence of a problem. Slack is thin, but thin-and-enforced is a different state from thin-and-silent.

**Status**: accepted, actively controlled debt. Filing an issue would re-open work whose closure is holding.

### 5. `sg_closure_lint` uncited enforcers — REAL, a bounded legacy retrofit

10 of 40 entries: SG-016, 017, 019, 021, 032, 034, 035, 036, 037, 038. All ten are in the **numeric-ID generation**; every later entry uses a named ID (`SG-I...`, `SG-S...`, `SG-V...`). They predate the rule GH #249 introduced, which produced `sg_closure_lint` itself.

They are not empty — SG-035 for example carries a "Verification hint" naming a regex approach and a negative-path test — but the prose is not a machine-citable enforcer reference. The lint accepts either a test/module/gate citation or a `cannot-automate:` decision (`qor/scripts/sg_closure_lint.py:27`), and is WARN-only, wrapped `|| true` at audit Step 0.6.

**Status**: real, bounded, ten entries. This is the "advisory shipped, enforcer deferred" shape catalogued under umbrella GH #147.

### 6. Operator install drift — NOT a repository concern

`install_drift_check` reports one missing install (`qor-research`) under `.claude/skills/`, which Phase 208 untracked and gitignored precisely because it is operator-local state regenerated by `qor-logic install --host claude --scope repo`.

**Status**: machine state, one command, no repository defect. Should not be a GitHub issue.

### Live GitHub state

- **#285 / #286** — legitimate open governance features, opened 2026-07-14, correctly scoped to public-line doctrine with the executable contracts cited as owned elsewhere. Anonymized earlier today. No action beyond normal prioritization.
- **PR #296** — dependabot bump of `pypa/gh-action-pypi-publish`, 12 checks pass / 1 skipping, `MERGEABLE` but `BLOCKED` by the same base-branch policy every PR this session hit. Ready to merge; touches the release path exercised repeatedly today.

## Blueprint Alignment

| Claim carried in conversation | Actual finding | Status |
|---|---|---|
| "6 merged phase branches on origin" | 111 of 129 remote heads merged | DRIFT — understated ~18x |
| "ruff runs in no workflow" | ruff is not a declared project tool at all; 254 findings | DRIFT — understated the scope |
| "both skills near the ceiling" (implied concern) | closed #266 shipped a test-enforced lock; both under it | DRIFT — already solved and holding |
| "the flake bit once, passed on re-run" | three recorded occurrences across phases 161/194/206 | DRIFT — understated recurrence |
| "install drift" (implied repo concern) | operator machine state, gitignored by design | DRIFT — not a repository item |
| sg_closure 10 uncited entries | confirmed; all in the legacy numeric-ID generation | MATCH |

## Recommendations

1. **File four issues, not six, and no umbrella.** The #247 umbrella pattern fits a cluster with a shared cause (research entry #378 drove all six of its follow-ons). These four share only the session that surfaced them. An umbrella here would be cargo-culting the shape.
   - Flake watch condition (recurrence, mechanism removed, unproven)
   - Merged-branch cleanup (111 deletable; 18 unmerged triaged separately)
   - Ruff adopt-or-decline decision (254 findings; frame as a decision, not a fix)
   - `sg_closure_lint` legacy retrofit (10 entries, each an enforcer citation or a `cannot-automate:` decision)
2. **File nothing for skill headroom or install drift**, and record why, so the next sweep does not re-raise them.
3. **All four are public-line.** Nothing here is org-scoped, multi-repo, or enterprise-shaped.
4. **Merge PR #296** independently of this cluster; it is unrelated and ready.
5. Sequence the four by risk: the flake watch first (it can silently degrade CI trust), branch cleanup next (mechanical, immediately reduces the standing `branch_only` signal), then the ruff decision, then the retrofit.

## Updated Knowledge

Two corrections worth carrying into `docs/SHADOW_GENOME.md` as a process observation rather than a code countermeasure:

- **Conversation-carried debt drifts.** Four of six carried items were misstated in magnitude or status by the time they were re-examined — one was already solved. Debt that lives only in a session summary decays, which is the argument for recording it in GitHub at the moment it is found rather than at the end.
- **"Clean" claims must name their instrument.** "ruff clean" was true of individually checked files and false as a project property, in the same way "boundary clean" was true of 17 identity terms and false of the boundary. Both overstatements share a shape: reporting a tool's result as a property of the system.

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
