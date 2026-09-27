# AUDIT REPORT

**Target**: `docs/plan-qor-phase297-sealed-unpublished-release-state.md` (iter 2)
**Branch**: `phase/297-sealed-unpublished-release-state` at `07a50d20` (base `main` `15729311`)
**Session**: `2026-09-27T2225-1d09cf` (prior session `2026-09-25T2350-e05ce1`, VETO #809)
**Auditor**: The Qor-logic Judge (Option B fresh-context reviewer)
**Date**: 2026-09-27
**Plan content hash**: `421c615287e1e3092b48f970f880cea043eb5944daa193e4c9c753c7c3e88992`

---

## VERDICT: VETO

**Risk Grade**: L2
**Audit mode**: Option B. `audit_risk_score` reports `option_b_required: true` (flag `high-citation-surface`). This audit ran as a fresh-context reviewer with no plan-authoring or iteration-1 audit context; it received the plan, the iteration-1 report, and the brief only. Declared toolset: shell, git, repository file access, network through the proxy (used only for `git ls-remote --tags origin`). Every verification below was executed by this reviewer. No codex plugin and no external reviewer are configured; both capability shortfalls were emitted.

Iteration 1's V1 and V2 are resolved as written. LD-10's remediation mechanism is exact and was reproduced end to end in a scratch clone. The plan is rejected on one plan-internal contradiction. LD-9 instructs `/qor-implement` to restore every Phase 1 Affected File to its base `15729311` content. Phase 1 Affected Files include `docs/META_LEDGER.md` and `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`. Executed as written, that deletes append-only governance records and also deletes the event that LD-10 must edit.

## Mechanical ladder

- Preflight `governance-health --profile skill-entry`: all OK.
- Step 0: plan artifact found and valid in the current session (`plan-iter1.json`).
- Step 0.3 `plan_iteration_status_lint`: rc 0.
- Step 0.4: no prior audit carries hash `421c6152...` in either session. No short-circuit.
- Step 0.5: `cce.check` and `cce.check_session_total` return None for both `2026-09-27T2225-1d09cf` and `2026-09-25T2350-e05ce1`.
- Step 0.6: all lints rc 0, with these exceptions:
  - `plan_grep_lint`: 17 citations truth-checked, no WARN (iteration-1 A1 resolved).
  - `ci_coverage_lint`: 10 WARN on workflow commands outside the plan's CI Commands.
  - `workspace_fragility_check`: medium (`dirty_gate_artifact_count=62`).
  - `publication_boundary_lint`: rc 1, one finding at `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md:75`. The plan targets it under LD-10.
- Step 0.7: no `spec_deltas`. Judge half: the contracted behavior that changes is the tag-coverage rule and `doctrine-changelog.md`. Both are Affected Files, and no spec document governs them. No finding.
- Step 3 mechanical checks:
  - `prompt_injection_canaries`: rc 0.
  - `prose_test_lint --enforce`: rc 0.
  - `runtime_contract_walk`: 1 WARN, no production caller of `qor.scripts.release_state`. LD-6 accepts this.
  - `version_applicability.validate`: ok, "target v0.175.1 > current highest v0.172.2".

## Citation re-run against `15729311`

All 22 evidence statements reproduce byte-for-byte:

- `tests/test_changelog_tag_coverage.py`: 29, 56, 59, 70, and 36.
- `pyproject.toml`: 7.
- `CHANGELOG.md`: 11, 13, 3083, 3072, and 2894.
- `qor/references/doctrine-changelog.md`: 5 and 22.
- `.github/workflows/ci.yml`: 31.
- `git merge-base --is-ancestor` returns 1 for `v0.24.1`, `v0.25.0`, and `v0.39.0`.
- `qor/scripts/shadow_process.py`: 40 and 129.
- `qor/scripts/ledger_emit.py`: 70.

All four CI jobs that run pytest check out with `fetch-depth: 0`.

## Focus findings

1. **V1 (iteration 1, version applicability): resolved.** `git tag -l 'v0.175*'` is empty. The worktree shares refs with the main checkout, and the operator deleted `v0.175.1` there. `git ls-remote --tags origin` (425 lines) has no `v0.173`-`v0.175` tag. `version_applicability.validate` is ok. `phase/298` (`af0ae68c`, version 0.175.1) is unmerged. LD-8 records the operator ordering, and it records that the substantiate guard still reads all local tags.
2. **V2 (iteration 1, reachable-tag coverage, LD-7): resolved.** A scratch prototype of the LD-2/LD-7 computation was run on the live checkout:
   - Reachable tags: 211. All SemVer tags: 214. Unreachable: exactly `0.24.1`, `0.25.0`, `0.39.0`.
   - With the LD-4 entries: no missing section, no orphan.
   - Without the three `unreachable_tag` entries: exactly those three orphans.
   - Simulated seal (project 0.175.1, section and reachable tag v0.175.1): clean. Dropping the `0.175.0` entry makes `0.175.0` an orphan, as LD-4 states.
   - A fixture repository with git 2.43 confirms the rule. `git tag --merged HEAD` excludes a side-branch tag. A `--depth 1` clone through a `file://` URL reports `--is-shallow-repository` true and lists no merged tags. The shallow guard is therefore necessary.
3. **`unreachable_tag` state: truthful, minimal, closed, tested, in scope.**
   - `git ls-remote` shows `v0.24.1`, `v0.25.0`, and `v0.39.0` exist on origin. Their peeled commits sit only on remote side branches. So "a tag exists off this line of history" is true.
   - The state claims no publication, which is weaker than the truth. No publication claim is smuggled.
   - `legacy_untagged` would be false for these versions, and widening inverse membership would reopen V2. A distinct state is the minimal truthful option.
   - The enum is closed at three values. Each value has an accepted-load test, and an unsupported state is rejected (inverse coverage). The side-branch orphan-then-exempt fixture test exercises the new state.
   - The versions are the forced consequence of the operator's reachable-only decision, so they are within GH #520 scope. See A2.
4. **LD-10: exact and disclosed.** Verified in a scratch clone:
   - Line 75 parses, and its id equals `compute_id` (`70f04c84...`).
   - Replacing only the worktree-root prefix with `<repo-root>` yields `6c2548c1e5116925fc5da35e5899c8905d6a679f7631ddcc2d0c1d7c99ccb437`, which matches the plan.
   - The compact re-serialization equals the original line shape. `git diff` shows one changed line.
   - A prototype of the integrity invariants was RED only on the UPSTREAM boundary check before the edit and GREEN after.
   - After the edit, `publication_boundary_lint` exits 0. A `ledger_emit.append` AMENDMENT verifies under `ledger_hash.py verify`. The full suite (3566 passed, 3 skipped) stays green.
   - No tracked file other than the plan cites the old id. No ledger entry binds the file's bytes. `.qor/` holds no reference to the id.
   - The AMENDMENT shape matches precedent Entry #806.
5. **LD-9: contradicts LD-10 and the append-only ledger. See V1 below.**
6. **Hotfix scope.** The operator decision fixes 0.175.1. The work is release-integrity only, with no remote tag, publication, or workflow change. The new invariant test is the proof obligation for LD-10. No scope finding.

## Passes

- Prompt Injection: PASS.
- Version-Applicability: PASS.
- Security / OWASP: no auth, credential, or network surface. Git is invoked through list-form argv, and the record is parsed with `json.loads` against a closed shape and fails closed. PASS.
- Ghost UI / Live-Progress: no UI. PASS.
- Section 4 Razor: the base test is 143 lines, and the new module and tests are each well under 250 lines. No nesting or ternary pressure. PASS.
- Self-Application (`originating_remediation: GH #520`): no rule treats an unreachable or remote-unknown tag as publication, and LD-8 uses the remote tag list for its publication statement. PASS. See A1.
- Test Functionality: every described test invokes `load_release_state`, `merged_semver_tags`, `coverage_violations`, `shadow_process`, or `scan_text` and asserts on the result. PASS.
- Closed-enum coverage: forward (each state loads) and inverse (unsupported state rejected) are both present. PASS.
- Dependency: none added. PASS.
- Macro-Level Architecture: the owner module is in `qor/scripts` and the tests consume it. No cycle. PASS.
- Feature Test Coverage: `feature_inventory_touches` is empty, which is legitimate for governance/test maintenance. Exempt.
- Infrastructure Alignment: all citations reproduce, NEW files are declared, and `shadow_process.read_events`, `validate`, `compute_id`, `publication_boundary_lint.scan_text(rel, text, terms)`, and `ledger_emit.append` exist with the cited signatures. The Step 4.6.14 fail-closed claim holds (`qor-substantiate/SKILL.md:249`). PASS.
- Filter-Stage Ordering: validation, then reachable-tag read, then missing sections, then ceiling, then candidate and disposition exemption. The order is coherent. PASS.
- Orphan Detection: `release_state.py` is connected through the CI test gate. PASS.
- Plan-internal consistency: **FAIL (V1)**.
- Execution-Continuity: not declared; not applicable.

## Violations Found

| ID | Category | Location | Description |
| --- | --- | --- | --- |
| V1 | specification-drift | LD-9; Phase 1 Changes step 1; Phase 1 Affected Files; LD-10 step 1 | LD-9 says `/qor-implement` "starts by restoring each Phase 1 and Phase 2 Affected File to its base `15729311` content", and Phase 1 step 1 repeats it for "the Affected Files of both phases". Phase 1 Affected Files list `docs/META_LEDGER.md` and `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`. At base, `META_LEDGER.md` has no Entry #809, and this audit's #810 would also be erased. At base, `PROCESS_SHADOW_GENOME_UPSTREAM.md` has 71 lines, not 78, and does not contain the `70f04c84...` event. Executed as written, the restore rewrites the append-only ledger and deletes seven Shadow Genome events. After that, LD-10 step 1 ("Confirm that its `id` is `70f04c84...`; if either check fails, stop") cannot pass. The prose before the instruction names only the five pre-audit files, but the operative instruction does not. For a phase whose subject is governance-record integrity, that ambiguity cannot go to implementation. |

## Per-ground directives

#### Plan-text

V1. The restore instruction in LD-9 and Phase 1 Changes step 1 must name its exact file set. It must exclude the append-only records (`docs/META_LEDGER.md`, `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`), which the plan changes only by LD-10's one-line edit and one appended AMENDMENT.

**Required next action:** Governor: amend plan text, re-run `/qor-audit`

## Advisories (non-blocking)

- **A1**: A reachable local-only seal tag still covers its version locally, while CI sees only origin tags. For example, once Phase 298 rebases, `0.175.1` is covered locally but is an orphan in CI until an entry is added. This split is inherent to offline checks (LD-3), and the operator scoped the rule to reachability. The doctrine text should say that CI is the enforcement point.
- **A2**: nothing checks that an `unreachable_tag` entry names a version whose tag exists and is unreachable. This matches the other two states, which are operator-asserted dispositions.
- **A3**: the base Phase 42 regression tests for `_released_orphans` encode the removed "above the highest tag is exempt" rule. The plan replaces them implicitly but does not name their removal.
- **A4**: git fixtures should isolate global git config (for example `commit.gpgsign`) as well as pinning identity. The `file://` URL should come from `Path.as_uri()` for the Windows matrix leg.
- **A5**: the shallow-skip test mechanism for the live tests is unspecified.

## Documentation Drift

None (`render_drift_section` returned empty).

## Process Pattern Advisory

<!-- qor:veto-pattern-advisory -->

No repeated-VETO pattern detected in the last 2 sealed phases.

### Verdict Hash

Recorded as the Content Hash of the GATE TRIBUNAL ledger entry for this session.

---
_This verdict is binding._
