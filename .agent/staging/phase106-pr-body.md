# Phase 106: dependency-admission lint V1.1 extensions (v0.74.0)

Closes 3 of 5 Phase 105 V2 carry-forward items as a cohesive lint V1.1 surface. The remaining 2 items have legitimate blockers (operator-evidence accumulation, maintainer-team provisioning) and remain explicit carry-forward.

## Summary

Three additive extensions on top of Phase 105's V1 dependency-admission lint:

### D-106.1 PR-label override

The lint accepts the `dep-admit-override` GitHub PR label as a supplementary override signal alongside the existing META_LEDGER `**Dependency admission override**:` entry. CI context is detected via standard GitHub Actions env vars (`GITHUB_EVENT_NAME=pull_request` + `GITHUB_REPOSITORY` + PR number from `GITHUB_REF`); the lint shells out to `gh pr view <n> --repo <owner>/<name> --json labels`. **Fails open**: any gh non-zero exit emits a stderr fallback note `"WARN: PR label query failed; falling back to META_LEDGER-only override check"` and continues with META_LEDGER-only behavior — a failed network query must not introduce a spurious within-window violation when the operator has done the right thing via ledger entry. New `--skip-pr-labels` flag for local testing.

### D-106.2 pyproject.toml exact-pin coverage

New `parse_pyproject_exact_pins(text)` pure function in `_dep_admit_common.py` uses stdlib `tomllib` (Python 3.11+) to extract PEP 440 exact-pin entries (`package==X.Y.Z`) from `[project] dependencies` and `[project.optional-dependencies]`. Range pins (`>=4`, `~=2.1`) and unbounded specifiers are skipped because the resolved version is not knowable until install time. The lint's `run_lint()` signature gains `current_pyproject_text` + `base_pyproject_text` parameters; pyproject bumps union with lockfile bumps before the PyPI query loop.

### D-106.3 Session ID convention lint

New `qor/scripts/session_id_lint.py` (~46 lines). Emits a non-blocking stderr WARN at `/qor-substantiate` Step 4.6 when `.qor/session/current` doesn't match `qor.scripts.session.SESSION_ID_PATTERN` (canonical 6-hex slug format `\d{4}-\d{2}-\d{2}T\d{4}-[0-9a-f]{6}$`). Always exits 0; the WARN names the canonical format and points operators at `session.rotate()`. Closes the fall-through-to-default pattern observed in Phase 105 substantiate where event provenance fragmented under the `default` session.

## Changes

- `qor/scripts/_dep_admit_common.py` (amend; +`parse_pyproject_exact_pins` + `tomllib` import)
- `qor/scripts/dependency_admission_lint.py` (amend; +`_query_pr_labels` + `--skip-pr-labels` + run_lint signature extensions)
- `qor/scripts/session_id_lint.py` (NEW)
- 3 test files: `tests/test_dep_admit_common.py` (+3), `tests/test_dependency_admission_lint.py` (+3), `tests/test_session_id_lint.py` (NEW, 3 tests)
- `qor/skills/governance/qor-substantiate/SKILL.md` (Step 4.6 wires the new lint with `|| true`)
- `qor/references/doctrine-dependency-admission.md` (Phase 106 V1.1 extensions note)
- `qor/references/doctrine-governance-enforcement.md` (NEW §7.1 "Session ID convention")
- `qor/references/glossary.md` (3 new term entries + `referenced_by` populated)
- `docs/plan-qor-phase89-ci-commands-reconciliation.md` (forward-maintenance bullet)
- `pyproject.toml` (0.73.0 → 0.74.0; feature minor bump)
- `CHANGELOG.md` (`## [0.74.0]`)
- `README.md` (Tests 1937 → 1946; Ledger 287 → 290)
- `docs/SYSTEM_STATE.md` (Phase 106 section)
- `docs/META_LEDGER.md` (entries #288 audit, #289 implementation, #290 seal)

## Phase 106 conventions self-applied at seal

- Session ID `2026-05-25T2035-c8f105` is the **first conforming 6-hex slug** under the new convention; session_id_lint is silent (no WARN).
- The new session_id_lint step at `/qor-substantiate` Step 4.6 ran for the first time during this seal cycle (exit 0).
- doc_integrity strict passes cleanly with the 3 new glossary terms wired to their `referenced_by` paths (no drift remediation needed at substantiate, unlike Phase 105 which surfaced 14 + 1 pre-existing drift findings).

## SG-StructureWithoutPolicy-A countermeasure progress

At the dependency-admission surface, the pattern is now **fully closed** across the structure → declaration → enforcement chain:

- **Phase 103** declared the 3-component override procedure (META_LEDGER entry + PR label + 30-day re-eval)
- **Phase 105** shipped the META_LEDGER signal detection + 30-day tracker
- **Phase 106** closes the PR label signal detection

The doctrine's three documented components all have operational tooling.

## Test plan

- [ ] CI green: full pytest suite passes (target: 1946 collected; 9 new behavioral tests; mocked PyPI + gh CLI)
- [ ] Workflow run on this PR: existing `dependency-review` action passes; the lint step (with `|| true` wrap) emits markdown summary
- [ ] After merge: subsequent PRs that touch `requirements-release.txt` OR `pyproject.toml` exact pins trigger the V1.1 lint surface
- [ ] After merge + tag: v0.74.0 release workflow succeeds (Phase 104 publish-step fix carries forward)

## Carry-forward (unchanged from Phase 105; not shipped here)

- WARN→hard-fail flip on cooling-period lint (needs operator-evidence from V1.1 first PR runs)
- Broaden CODEOWNERS reviewer pool (needs maintainer team)
- `cyclonedx-bom` hash-pinning (Razor file-budget concern)
- Future V2: calendar / GH-issue integration for tracker; broaden cooling-period to non-exact pyproject specifiers

## Citations

- **Plan**: `docs/plan-qor-phase106-dep-admit-lint-extensions.md`
- **Audit**: `.agent/staging/phase106-AUDIT_REPORT.md` (PASS, L2 iter-1)
- **META_LEDGER entries**: #288 (audit gate tribunal), #289 (implementation), #290 (session seal)
- **Merkle seal**: `72f12d2f7ff3ec2e20a1aec38efe2e74e5faf0d6383db84253deadadecdde1ed`

🤖 Authored via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic) on [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
