# AUDIT REPORT

**Tribunal Date**: 2026-10-05
**Target**: `docs/plan-qor-phase303-boundary-lint-scope.md`
**Iteration**: 1 (branch `phase/303-boundary-lint-scope`, head `bcd331a3`, plan-only; base `main` `25babc0e` = 0.175.6)
**Session**: `2026-10-05T1620-2b159a`
**Risk Grade**: L2
**Auditor**: The Qor-logic Judge
**Mode**: Option B fresh-context reviewer, independent of the plan author. `audit_risk_score` reported `option_b_required: true` (flag `high-citation-surface`); this review is that independent audit, run by a subagent with no plan-authoring context. The Codex plugin is unavailable (`should_run_adversarial_mode` False) and `external_reviewer.run_external_review` returned `fallback` ("no reviewer configured"); both `capability_shortfall` events were emitted (`d8e5f9a9...` codex-plugin, `e4c763e1...` external-reviewer). Reviewer toolset: shell, git (local objects, plus `git ls-remote` over the proxy), file read and grep, Python with the in-tree `qor` package on `PYTHONPATH`, pytest in scratch clones outside the repository. No GitHub API was used.

---

## VERDICT: VETO

---

### Executive Summary

The engineering of the plan holds in every executed check. The veto rests on one plan-text ground in LD-6.

LD-6 edits line 316 of the sealed Phase 89 plan. META_LEDGER Entry #237 (IMPLEMENTATION, Phase 89) commits that file by content hash: `SHA256(plan-qor-phase89-ci-commands-reconciliation.md) = b98d4ff9...`, and that value equals the file at the Phase 89 seal commit `4a34b08e`. `qor/references/doctrine-ledger-commitment.md` says that a phase which changes an artifact already committed by content hash MUST append an AMENDMENT that records the superseded and current hashes and the reason.

The plan does not mention Entry #237. It plans no amendment and gives no reason why the rule does not apply. It also contradicts its own boundaries:

- `non_goals` names "rewriting sealed plans".
- LD-3 refuses to edit 17 sealed plans because "they are ledger-bound evidence".
- LD-6 then edits a sealed plan that is ledger-bound in the same way.

The seal gate cannot catch the omission. `ledger_commitment._CONTENT_RE` does not parse Entry #237's legacy `SHA256(...) =` form, so `latest_commitments` holds no commitment for this path. `stale_commitments_scoped` would therefore count the file as examined and report it clean (observed: `ScopedResult(findings=[], examined=1)`). A content-hash binding would be reported as checked when it was not. That is a testimonial pass, the defect class this review was asked to rule on.

### LD-6 ruling (explicit)

1. **Binding search.**
   - `docs/META_LEDGER.md` names the Phase 89 plan in Entries #236 (GATE TRIBUNAL: its content hash binds the audit report, not the plan), #237 (IMPLEMENTATION: its content hash binds the plan, `b98d4ff926a655fa...`) and #238 (SESSION SEAL), and in later entries' files-touched lists (Phases 105, 106, 164 and 233).
   - No AMENDMENT for the path exists.
   - The Phase 89 gate artifacts (`.qor/gates/2026-05-22T2305-dc33d5/*.json`) carry no `target_content_hash`.
   - No intent-lock record covers Phase 89. The other gate artifacts that name the path list it as a file touched; none binds its hash.
   - So the only binding is Entry #237.
2. **Is the binding verifiable today?**
   - The file has been edited 13 times since the seal (Phases 105, 106, 156, 158, 162 and 164, the ungoverned Phase 164 follow-up `4be56cd2`, then Phases 165, 172, 208, 211, 213 and 233).
   - The live file has not matched `b98d4ff9` since 2026-05-25. At the base it hashes to `239a2820...`.
   - The binding is verifiable only as bound to a revision: `git show 4a34b08e:<path>` reproduces `b98d4ff9`, and `4a34b08e` is an ancestor of HEAD.
   - The Phase 303 edit does not change that, so it does not by itself degrade a binding that is verifiable today.
   - It does extend a drift that has never been disclosed. It is also the first edit of this file since the ledger-commitment doctrine (Phase 251) made disclosure mandatory; Phase 233 was the last edit before it.
3. **Precedent check.**
   - `git log --format=%s 25babc0e -- <path>` does list the seals of Phases 233, 213, 211 and 208 first, so the claim reproduces literally.
   - Diffed against their first parents, all four are append-only: each adds one new bullet (`-0 +1`). None replaced an existing bullet's code span.
   - Phase 303 modifies the bullet that Phase 208 authored. The only earlier modification of an existing bullet is `4be56cd2` (a non-seal fix commit; it also added the BOM and the mojibake now in the file).
   - So the cited precedents support adding a bullet, not modifying one.
4. **Alternatives.**
   - An exemption in the Phase 89 plan's `## CI Coverage Exemptions` section is also an edit to the sealed plan.
   - Repointing `test_lint_self_applies_to_phase_89_plan` at another registry changes a self-application contract and goes beyond the owner-narrowed hotfix scope.
   - Keeping the bullet edit is consistent with the forward-maintenance convention the ledger records, provided the doctrine's disclosure is made.
   - The edit itself is therefore not the defect. The undisclosed edit of a content-hash-committed sealed artifact, contradicting the plan's own boundaries, is the defect.
5. **Ruling.** VETO on LD-6 (V1, `specification-drift`).

### Engineering verification (all reproduced; not veto grounds)

- **Citations.** All 42 `git show ... | grep` -> statements and all 6 `prints` statements re-run at `25babc0e`: 0 mismatches. `plan_grep_lint` also checked 42 citations with no finding.
  - The `git grep` no-match claim (LD-9) reproduces: 0 lines.
  - The LD-3 enumeration reproduces with a case-sensitive search: 69 files, 30 gates, 10 intent-lock, 17 plans, the ledger, the process shadow genome, the 2 sources and the 8 compiled copies.
- **Scope.** The case-sensitive scope is exactly the two source lines (151 and 457) plus their eight compiled copies, one occurrence each. The plan touches no other occurrence and leaves none of the three owner-narrowed items out.
- **Dist regeneration.** `python -m qor.cli compile` after the two source edits rewrote exactly 15 files under `qor/dist/`:
  - the 8 copies, with one line each;
  - the 7 manifests: two sha256 values in each of the top-level, claude, codex, cursor and kilo-code manifests, and `generated_ts` in all 7.
  - `check_variant_drift` then gave `OK: 413 files, no drift`.
- **Tests (rebuilt from the plan text).**
  - Base: `19 failed, 2 passed`.
  - With Phases 2 to 4: `21 passed`, twice.
  - Test file plus the 17 consumer files: `217 passed`, twice after restore.
  - Mutations, each failing exactly its named set: M1 3, M2 2, M3 2, M4 1, M5 1, M6 1, M7 1 failed.
- **`--expect-scope` semantics.** It fails closed in both directions. In a fresh clone of the scratch implementation:
  - CI form with no overlay: `0 finding(s) [scope: structural]`, exit 0.
  - With an overlay: a mismatch line and exit 1.
  - Expecting `structural+identity` with no overlay: a mismatch line and exit 1.
  - An invalid choice is rejected by argparse.
  - Findings are not masked by the flag.
- **CI wiring.** The step `publication boundary` is the last step of `gate-chain-completeness` (`runs-on: ubuntu-latest`, no `if:`, no `continue-on-error`). The workflow triggers on push to main and on pull_request, so the flag runs.
- **Release state.**
  - CI-view simulation: `{'0.175.6'} {'0.175.6'}` at the base and `set() {'0.175.6'}` with the LD-12 entry.
  - The post-seal clone proof equals Phase 302's command with `0.175.7` substituted and `printf '%s'` in place of `printf '%s\n'` (diffed). The change is equivalent because `$R` is newline-separated and `grep -x` matches a final line that has no newline.
  - The proof discriminates: base, guard FAIL (0.175.6), exit 1; bump without stamp, guard FAIL (0.175.7), exit 1; simulated seal without the entry, `1 failed, 3 passed` (orphan 0.175.6), exit 1; with the entry, `4 passed`, exit 0, twice.
  - The remote's highest tag is `v0.172.2`.
  - `test_release_state`, `test_changelog_tag_coverage` and `test_changelog_format` with Phase 5: `34 passed`.
- **CHANGELOG.** The LD-11 bullet's clauses match the implementation. It is ASCII, carries no ledger number or hash, and does not spell the outside name.
- **Full suite** (scratch, Phases 1 to 4): `3662 passed, 3 skipped, 4 deselected`. Ruff is clean. `prose_test_lint --enforce` exits 0. After the suite and a manifest restore, the drift check gives `OK: 413 files`.

### Audit Results

#### Security Pass
**Result**: PASS. No auth, secrets or bypassed checks. The change narrows a lint and adds a fail-closed assertion.

#### OWASP Top 10 Pass
**Result**: PASS.
- A03: no subprocess change, and the tests use list-form argv.
- A04: `--expect-scope` fails closed in both directions.
- A05: none.
- A08: the test plan uses `yaml.safe_load`.

#### Ghost UI Pass
**Result**: PASS. There is no UI surface.

#### Section 4 Razor Pass
**Result**: PASS. The lint module grows from 194 to 207 lines. `main` stays under 40 lines, nesting is 2 or less, and there are no nested ternaries.

#### Dependency Pass
**Result**: PASS. No new dependency (`yaml` is already used; `shlex` is stdlib).

#### Orphan Pass
**Result**: PASS. The new test file is collected by pytest. Every edited file is on the build or CI path.

#### Macro-Level Architecture Pass
**Result**: PASS. `SCOPES` is the single source for the scope strings. `_load_terms` is shared unchanged by `github_surface` and `advisory_filing_control`.

#### Test Functionality Pass
**Result**: PASS. The lint tests invoke `_load_terms`, `collect_findings` and `main` and assert on their output. The CI test executes CI's own argv. The CLI-form tests assert the token of the shipped instruction line, and M5 and M6 prove they discriminate. `prose_test_lint --enforce` exits 0.

#### Infrastructure Alignment Pass
**Result**: PASS on citations; finding V1 is recorded under Plan-text. `runtime_contract_walk` gives 1 WARN (backward: `release_state` has no production caller), which predates this plan.

#### Self-Application Sub-Pass (originating_remediation GH #457)
**Result**: PASS. Neither the plan nor its commit carries the outside name (a case-insensitive search found 0 occurrences). The plan file is ASCII, and `publication_boundary_lint` reports 0 findings.

#### Version-Applicability Pass
**Result**: PASS. `target v0.175.7 > current highest v0.175.6`.

#### Spec-delta pre-pass
**Result**: PASS. No `spec_deltas` are declared. No contracted capability spec covers the lint (LD-9).

### Violations Found

| ID | Category | Location | Description |
| --- | --- | --- | --- |
| V1 | specification-drift | LD-6; Phase 3; boundaries `non_goals`; LD-3 | Edits the sealed Phase 89 plan, whose bytes Entry #237 commits by content hash (`b98d4ff9...`). The plan neither discloses the commitment nor plans the AMENDMENT that doctrine-ledger-commitment mandates, and it contradicts its own `non_goals` ("rewriting sealed plans") and the LD-3 rationale ("ledger-bound evidence"). The seal's Step 3 cannot parse Entry #237's legacy hash form and would report the file examined and clean. The cited precedents (Phases 208, 211, 213 and 233) only append bullets; none modifies one. |

Advisories (not grounds):

- A1: LD-3 counts the outside name case-sensitively. A case-insensitive search finds 3 more tracked files: an intent-lock snapshot, the Phase 268 plan and `tests/test_portable_governance_boundary.py`, which is a live test asserting absence. The owner's narrowing keeps them out of scope, but the residual statement ("59 files") understates them.
- A2: under pytest's assertion rewriting, a test of the form `assert tok == "qor-logic", rel` prints the compared token. The reconstruction printed the outside name once at the base. LD-7's "failure message names the file only" holds only if the comparison is reduced to a boolean before the assert, and the plan does not say so.
- A3: `workspace_fragility_check` flags 68 dirty gate artifacts and 10 active branches. Both predate this plan.

### Per-ground directives

#### Plan-text

V1. Make LD-6 and Phase 3 account for Entry #237's content-hash commitment of `docs/plan-qor-phase89-ci-commands-reconciliation.md`:

- State the commitment, and that the live file has diverged since Phase 105.
- Either record the AMENDMENT that `qor/references/doctrine-ledger-commitment.md` requires, with Superseded Content Hash `b98d4ff926a655fa1e7f78a4a003428ac066f223a969eb842210f1826d6baaf4`, the post-edit hash and the reason, or cite a doctrine ground for why the rule does not apply.
- Reconcile the boundaries `non_goals` and the LD-3 rationale with the edit.
- State the precedent accurately: the four cited seals append bullets, and this edit modifies one.

**Required next action:** Governor: amend plan text, re-run `/qor-audit`

## Process Pattern Advisory

<!-- qor:veto-pattern-advisory -->

No repeated-VETO pattern detected in the last 2 sealed phases.

### Verdict Hash

SHA256(this_report) is recorded as the Content Hash of the META_LEDGER GATE TRIBUNAL entry for this audit.

---
_This verdict is binding._
