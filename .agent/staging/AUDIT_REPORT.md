# AUDIT REPORT

**Tribunal Date**: 2026-10-05
**Target**: docs/plan-qor-phase305-package-data-ships-dist.md (iteration 1; base 2f3017807a707272cdc0f0bb464a2a13229cbdeb; plan head 003346dc; plan sha256 d49a236886b34644bb7af21d528fa42311dc74cee25ec24938392b1e6602cb3c)
**Risk Grade**: L2
**Auditor**: The Qor-logic Judge
**Mode**: solo, Option B fresh-context reviewer (audit_risk_score option_b_required: true, flag high-citation-surface). The Judge did not author the plan. Declared toolset: shell, git, repository file access, network (package index and `git ls-remote` only; GitHub API not used). Every verification below was executed with this toolset.

---

## VERDICT: VETO

---

### Executive Summary

The packaging half of the plan holds. All 83 quoted evidence and `prints` statements reproduce at the base. A test file rebuilt from the LD-5 text gives `5 failed, 3 passed` at the base and `8 passed` after Phase 2, twice each. M1 to M8 turn exactly the items the plan names RED. Real wheels built with `build` 1.6.1 (setuptools 84.0.0) reproduce 578 and 599 selected files, set-equal to the simulation, and 392 and 413 of 413 tracked dist files. Installed wheels reproduce `list --available` exit 1 and then 0, with 47 ids in order, and installs of 73 and then 78 files. The full suite gives `3679 passed`, and the freeze check, CI-view simulation and clone proof all reproduce. The release-state half fails: its premise is false at audit time. `qor-logic` 0.176.0 is on PyPI. The package index lists it as the newest version, with a wheel uploaded at 2026-10-05T21:31:10Z and an sdist at 21:31:12Z. `pip download --no-deps qor-logic==0.176.0` succeeds. So LD-9's `sealed_unpublished` disposition would record a published version as "never published", which doctrine-changelog does not allow. The README line, the `### Changed` bullet and the Problem and LD-9 observations state as fact things that are now false. The owner's statement that the run was cancelled before anything was published conflicts with the index.

### Audit Results

#### Governance preflight and Step 0 lints
**Result**: PASS. governance-health skill-entry: all OK. Step 0 gate check: plan artifact found and valid (`plan-iter1.json`). plan_iteration_status_lint exit 0. Step 0.4: no prior audit for this session, so no short-circuit. Step 0.5: cycle-count and session-total escalators both None. WARN-only ladder: plan_grep_lint truth-checked 62 citations, exit 0. plan_test_lint, enumeration, text-consistency, delivery-branch, ci_coverage, signature-widening, data-round-trip, live-progress and feature-tdd: no findings. sg_closure_lint: 0 without enforcer. gate_schema_freeze_lint: 0. publication_boundary_lint: 0 findings, structural scope. workspace_fragility_check: medium (dirty gate artifacts, branch count), advisory only. Step 0.7: the plan declares no spec delta (LD-12), so spec_lint has no delta to lint.

#### Prompt Injection Pass
**Result**: PASS. prompt_injection_canaries over ARCHITECTURE_PLAN, META_LEDGER, CONCEPT and the plan: exit 0.

#### Version-Applicability Pass
**Result**: PASS. `validate`: target v0.176.1 > current highest v0.176.0.

#### Security Pass
**Result**: PASS. No auth logic, credentials or bypasses.

#### OWASP Top 10 Pass
**Result**: PASS. The new test uses `tomllib` and `json` (no unsafe deserialization, A08). It has no subprocess (A03). The CI clone-proof command is an operator shell command with fixed argv and no untrusted input.

#### Ghost UI Pass
**Result**: PASS (no UI).

#### Section 4 Razor Pass
**Result**: PASS

| Check | Limit | Blueprint Proposes | Status |
|---|---|---|---|
| Max function lines | 40 | rebuilt test max ~12 | OK |
| Max file lines | 250 | plan 93; rebuilt 83 | OK |
| Max nesting depth | 3 | 3 | OK |
| Nested ternaries | 0 | 0 | OK |

#### Self-Application Sub-Pass
**Result**: N/A. The plan artifact has no `originating_remediation`.

#### Test Functionality Pass
**Result**: PASS

| Test description | Invokes unit? | Asserts on output? | Verdict |
|---|---|---|---|
| list test: `_do_list(available=True)` on the staged dist | yes | rc 0 and the exact ordered de-duplicated ids | PASS |
| install test x6: `_do_install` on the staged dist | yes | rc 0, one record, record count equals live manifest count | PASS |
| guard: manifest paths with dot-prefixed, RCS, CVS or _darcs segments | reads the live manifests that install consumes | the offending list is empty | PASS (M5 to M8 discriminate) |
| test_packaging fragment `dist/` | reads the live globs | fragment present | PASS (weakening declared in LD-6; behavior carried by LD-5) |

Rebuilt from the plan text and run twice per state: base `5 failed, 3 passed`, with the failing items and assertions as planned (`assert 1 == 0`, and `assert 73 == 78` four times); after Phase 2, `8 passed`. Mutations: M1 5F/3P, M2 4F/4P, M3 1F/7P, M4 1F/4P, M5 1F/7P (79 entries), M6 2F/6P, M7 1F/7P, M8 1F/7P. Each failing set is exactly the one named. prose_test_lint --enforce exit 0. Windows: `Path(rel).as_posix()` normalizes the backslash results of `glob`. `.gitattributes` pins `qor/dist/** text eol=lf`, so staged bytes match the manifest sha256 on a Windows checkout. No clock, network or random coupling.

#### Dependency Pass
**Result**: PASS. No new dependency; `tomllib` is stdlib (requires-python >= 3.11).

#### Macro-Level Architecture Pass
**Result**: PASS. One packaging line, one new test module, one test fragment, two notice lines, one data record. No Python source change.

#### Feature Test Coverage Pass
**Result**: PASS. FX003 and FX001 cite the new file, and their descriptors name the asserted output. FX028 cites `tests/test_freeze_check.py`, and K4 and K5 discriminate.

#### Infrastructure Alignment Pass
**Result**: FAIL (V1)

What reproduces:
- All 83 backticked `->` and `prints` repository statements at 2f301780, including the six-host count loop (78 78 78 78 47 47) and the `git grep -lE '0[.]176[.]0'` file list.
- The setuptools 84.0.0 and 68.0.0 source lines (build_py glob and isfile; implicit patterns, manifest_files and exclude lines; the sdist, egg_info and `_distutils` prune lines; 68.0.0 `(RCS|CVS|`, `_darcs` count 0).
- `git ls-remote` lists `refs/tags/v0.176.0` peeled to 39974233, and no v0.175.x tag.

What does not reproduce:
- `python -m pip index versions qor-logic` prints `qor-logic (0.176.0)` as its first line, where LD-9 quotes `qor-logic (0.172.2)`.
- `python -m pip download --no-deps qor-logic==0.176.0` succeeds, where LD-9 quotes `ERROR: No matching distribution found`.
- The pypi.org JSON for 0.176.0 lists `qor_logic-0.176.0-py3-none-any.whl` (uploaded 2026-10-05T21:31:10Z) and `qor_logic-0.176.0.tar.gz` (21:31:12Z).
- The downloaded wheel's file list equals that of a wheel built locally from the base. It lacks `qor/dist/manifest.json` and all 20 YAML files, and its long description carries the base README notice ("continues to install and work as documented").

#### Freeze amendment, release state and CHANGELOG
**Result**: FAIL (V1); the other checks pass.
- With Phases 1 to 3 applied in a scratch clone: `freeze_check: OK`, exit 0. freeze_check, release_state, tag-coverage and changelog-format tests give `43 passed` (9 + 29 + 5). check_variant_drift gives `OK: 413 files, no drift`. ruff is clean. The edited README and AGENTS lines and the new test are ASCII.
- Only the two notice lines change. Headings, `freeze_check.py`, its tests, the classifier, dependabot and the schedules are untouched. CLAUDE.md ("frozen and superseded ... unless the owner lifts the freeze") and CONTRIBUTING.md ("frozen and superseded; contributions are no longer accepted") stay true.
- The CI-view simulation prints `None True set() set() {'0.175.7'}` at the base and `sealed_unpublished True set() set() {'0.175.7'}` after.
- The clone proof:
  - base: exit 1, guard;
  - bump without stamp: exit 1, guard;
  - simulated seal: exit 0 with `4 passed`, twice;
  - seal without the 0.175.7 entry: exit 1 on orphan 0.175.7, while the plain local run gives `4 passed`;
  - seal without the 0.176.0 entry: exit 0.
  So the proof discriminates. Coverage does not depend on the 0.176.0 entry: the remote tag is reachable.
- The disposition itself is false (V1).

#### Filter-Stage Ordering / Execution-Continuity
**Result**: N/A (no pipeline-shaped selection; no `execution_continuity`).

#### Orphan Pass
**Result**: PASS

| Proposed File | Entry Point Connection | Status |
|---|---|---|
| tests/test_package_data_ships_dist.py | pytest `testpaths = ["tests"]`; first CI Commands entry | Connected |
| docs/release-state.json entry | `tests/test_changelog_tag_coverage.py` via `release_state.load_release_state` | Connected |

#### Executed reproduction (scratch clones outside the repository)
- Full suite with Phases 1 to 3: `3679 passed, 3 skipped, 4 deselected, 4 warnings`, exit 0. The consumer set gives `58 passed`.
- Wheels: base 578 non-.py files under qor/ (set-equal to the simulation); sdist and wheel each 392 of 413 tracked; the 21 missing are the root manifest and the 20 YAML files. Fixed: 599 (set-equal); sdist and wheel each 413 of 413 tracked; no other dist file.
- Installed wheels in fresh venvs: base `list --available` exit 1 with the `No manifest` line; installs 73, 73, 73 and 47. Fixed: exit 0, 47 lines equal to the de-duplicated ids; installs 78, 78, 78 and 47.

#### Publication boundary
**Result**: PASS. The plan names no outside repository. Boundary lint: 0 findings.

### Violations Found

| ID  | Category | Location | Description |
| --- | -------- | -------- | ----------- |
| V1  | infrastructure-mismatch | Problem items 1 and 3 (lines 34, 36); boundaries limitation (line 10, LD-9 clause); LD-7 bullet (line 219); LD-8 decision (line 256); LD-9 (lines 262 to 316); LD-11 `### Changed` bullet and clause-to-proof (lines 346, 355, 357); Phase 3 README line (line 467) and record entry (line 457); Phase 3 Unit Tests simulation expectation (line 483); DoD release-state deliverable (lines 515 to 520); CI Commands simulation expectation (line 532); Declared Residuals (line 558) | The plan's premise that 0.176.0 was never published is false at audit time: 0.176.0 is on PyPI. The `sealed_unpublished` disposition would record a published version as never published, and the README and CHANGELOG text state the false premise as fact |

### Advisories (non-blocking)

- A1: The Phase 3 README line says "The owner lifted the freeze for that one packaging fix". Nothing earlier in the README paragraph mentions a packaging fix, so "that" refers to nothing. The AGENTS line names it ("the Phase 305 packaging fix that 0.176.1 carries").
- A2 (carried from the earlier Phase 304 design audit): the title, the LD-4 heading and the packaging DoD D1 say in the present tense that wheels "carry" every tracked file, without the setuptools-version qualifier that the boundaries and LD-7 carry. Observed at 84.0.0 here; the 68.0.0 observation was not re-run by this Judge.
- A3: The amended AGENTS line keeps "Do not start ... releases", but publishing 0.176.1 is still to come as the owner's post-merge action (LD-10). An agent asked to push `v0.176.1` would read a prohibition. The owner can act, but the notice does not say so.
- A4: Pre-existing and out of scope (LD-7). The README Quick Start says to repeat the install command for `cursor` or `cline`, but `--host` offers neither.
- A5: runtime_contract_walk gives 3 backward WARNs (dist_compile, freeze_check, release_state have no production importer). These are pre-existing CLI-dispatched modules, not plan-introduced.

### Per-ground directives

#### Plan-text

V1 (infrastructure-mismatch). The plan states in many places that 0.176.0 was tagged but never published and that 0.172.2 is the newest version on the package index:

- Problem items 1 and 3;
- the boundaries' LD-9 clause;
- LD-7, LD-8 and LD-9;
- the LD-11 `### Changed` bullet and its clause-to-proof;
- the Phase 3 README line;
- the release-state deliverable;
- the CI-view expectation.

LD-9 rests the `sealed_unpublished` disposition on that premise, together with two quoted observations: `pip index versions` first line `qor-logic (0.172.2)`, and a failing `pip download ... ==0.176.0`. At audit time neither observation reproduces:

- `python -m pip index versions qor-logic` prints `qor-logic (0.176.0)`;
- `python -m pip download --no-deps qor-logic==0.176.0 -d <scratch>` downloads `qor_logic-0.176.0-py3-none-any.whl`;
- the pypi.org JSON lists the 0.176.0 wheel (upload 2026-10-05T21:31:10Z) and sdist (21:31:12Z), with `info.version` `0.176.0`.

The published wheel has the packaging fault: no `qor/dist/manifest.json`, no YAML.

doctrine-changelog defines `sealed_unpublished` as "sealed by /qor-substantiate, never published", and "Publishing the version later removes or changes the entry". Implementing LD-9 would therefore write a false operator-asserted record. Implementing the Phase 3 README line and the `### Changed` bullet would publish false statements: "version 0.176.0 was tagged but never published", "no 0.176.0 package is on PyPI", and "0.172.2, the newest version on PyPI". The plan's own coverage proof shows the entry is not needed for coverage, because the remote `v0.176.0` tag is reachable.

The owner statement relayed for this audit ("cancelled before anything was published; PyPI latest 0.172.2") conflicts with the package index. Its premise must be re-established with the owner before the plan restates the disposition.

Required correction:
- re-establish with the owner what happened to the v0.176.0 release;
- re-observe the package index;
- restate every passage listed in V1 to match the observed state, including whether any `docs/release-state.json` entry is warranted;
- correct forward the published 0.176.0 long description's "continues to install and work as documented" claim;
- re-derive the CI-view expectations from the corrected record.

**Required next action:** Governor: amend plan text, re-run `/qor-audit`

<!-- qor:drift-section -->
## Documentation Drift

(clean)

## Process Pattern Advisory

<!-- qor:veto-pattern-advisory -->

No repeated-VETO pattern detected in the last 2 sealed phases.

### Verdict Hash

SHA256(this_report) = [computed by orchestrator at ledger entry]

---
_This verdict is binding._
