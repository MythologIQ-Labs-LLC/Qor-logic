# AUDIT REPORT

**Tribunal Date**: 2026-10-05
**Target**: docs/plan-qor-phase305-package-data-ships-dist.md (iteration 2; base 2f3017807a707272cdc0f0bb464a2a13229cbdeb; plan head 643fa480; plan sha256 79217554a0d78d746c91925903e66575cdc9095d5dad083cc9d5b3828ff3d01b)
**Risk Grade**: L2
**Auditor**: The Qor-logic Judge
**Mode**: solo, Option B fresh-context reviewer (audit_risk_score option_b_required: true, flag high-citation-surface). The Judge did not author the plan or its iteration 2 revision. codex-plugin and external-reviewer capability shortfalls recorded. Declared toolset: shell, git, repository file access, network (package index and `git ls-remote` only; GitHub API not used). Every verification below was executed with this toolset, from the plan text, in scratch clones outside the repository.

---

## VERDICT: PASS

---

### Executive Summary

V1 of VETO #847 is cured. Every statement the plan makes about publication state is true at audit time (re-observed 2026-10-05T21:58Z). `0.176.0` and `0.172.2` are the two newest versions on the package index. Both published wheels and sdists lack `qor/dist/manifest.json` and all YAML files. Installed in fresh virtual environments, both fail `list --available` with exit 1 and install 73, 73, 73 and 47 files. Earlier versions are declared unchecked. No "never published" or "cancelled" claim remains, except as the superseded iteration 1 history. With no 0.176.0 entry, release state and tag coverage after the seal hold through the remote `v0.176.0` tag. The CI-view simulation and the clone proof reproduce and discriminate, including the scratch bare-remote case. The freeze amendment is two lines and truthful, and the AGENTS exception permits only the 0.176.1 release. The packaging half reproduces in full:
- 81 of 81 citations;
- RED and GREEN, twice each;
- M1 to M8;
- the full suite at base, after Phase 1 and after Phases 1 to 3;
- fixed wheels with setuptools 84.0.0 and 68.0.0;
- the installed fixed wheel.

### Audit Results

#### Governance preflight and Step 0 lints
**Result**: PASS.
- governance-health skill-entry: all OK.
- Step 0: plan artifact found and valid (`plan-iter2.json`, plan.json).
- plan_iteration_status_lint exit 0.
- Step 0.4: the plan hash 79217554... differs from the prior audit's target_content_hash d49a2368..., so there is no short-circuit.
- Step 0.5: the cycle-count and session-total escalators both return None.
- WARN-only ladder:
  - plan_grep_lint: 59 citations truth-checked, exit 0;
  - test, enumeration, text-consistency, delivery-branch, ci_coverage, signature-widening, data-round-trip, live-progress and feature-tdd lints: no findings;
  - sg_closure_lint: 0 without enforcer;
  - gate_schema_freeze_lint: 0;
  - publication_boundary_lint: 0 findings, structural scope;
  - workspace_fragility_check: medium (dirty gate artifacts, branch count), advisory only.
- Step 0.7: the plan declares no spec delta. No spec under `qor/specs` covers packaging or the freeze.

#### Prompt Injection Pass
**Result**: PASS. prompt_injection_canaries over ARCHITECTURE_PLAN, META_LEDGER, CONCEPT and the plan: exit 0.

#### Version-Applicability Pass
**Result**: PASS. `validate`: target v0.176.1 > current highest v0.176.0.

#### Security Pass
**Result**: PASS. No auth logic, credentials or bypasses.

#### OWASP Top 10 Pass
**Result**: PASS. The new test uses `tomllib` and `json` (A08 clean) and runs no subprocess (A03). The CI-view commands are operator commands with fixed argv and no untrusted input.

#### Ghost UI Pass
**Result**: PASS (no UI).

#### Section 4 Razor Pass
**Result**: PASS

| Check | Limit | Blueprint Proposes | Status |
|---|---|---|---|
| Max function lines | 40 | rebuilt test max ~12 | OK |
| Max file lines | 250 | plan 93; rebuilt 84 | OK |
| Max nesting depth | 3 | 3 | OK |
| Nested ternaries | 0 | 0 | OK |

#### Self-Application Sub-Pass
**Result**: N/A. The plan artifact has no `originating_remediation`.

#### Test Functionality Pass
**Result**: PASS

| Test description | Invokes unit? | Asserts on output? | Status |
|---|---|---|---|
| list test: `_do_list(available=True)` on the staged dist | yes | rc 0 and the exact ordered de-duplicated ids | PASS |
| install test x6: `_do_install` on the staged dist | yes | rc 0, one record, record count equals live manifest count | PASS |
| guard: manifest paths with dot-prefixed, RCS, CVS or _darcs segments | reads the live manifests install consumes | offending list empty | PASS (M5 to M8 discriminate) |
| test_packaging fragment `dist/` | reads the live globs | fragment present | PASS (weakening declared in LD-6) |

The test file was rebuilt independently from LD-5 and Phase 1:
- base: `5 failed, 3 passed` twice (`assert 1 == 0`, and `assert 73 == 78` four times);
- after Phase 2: `8 passed` and test_packaging `5 passed`, twice.

Mutations, each failing set exactly as named:
- M1: 5 failed, 3 passed;
- M2: 4 failed, 4 passed;
- M3: 1 failed, 7 passed;
- M4: 1 failed, 4 passed;
- M5: 1 failed, 7 passed (79 entries);
- M6: 2 failed, 6 passed;
- M7: 1 failed, 7 passed;
- M8: 1 failed, 7 passed.

prose_test_lint --enforce exit 0. The tests have no clock, network or random coupling.

#### Dependency Pass
**Result**: PASS. No new dependency; `tomllib` is stdlib.

#### Macro-Level Architecture Pass
**Result**: PASS. The change is one packaging line, one new test module, one test fragment, two notice lines and two CHANGELOG bullets. No Python source changes, and no release-state change.

#### Feature Test Coverage Pass
**Result**: PASS.
- FX003 and FX001 (lines 14 and 12 at base) cite the new file, with descriptors naming the asserted output.
- FX028 (line 39) cites `tests/test_freeze_check.py`, where K4 and K5 discriminate.

#### Infrastructure Alignment Pass (full re-walk)
**Result**: PASS
- All 81 backticked `->`, `prints` and `printing` repository statements reproduce at 2f301780. Also reproduced:
  - the six-host loop (78 78 78 78 47 47);
  - the `git grep -lE '0[.]176[.]0'` file list;
  - the empty `git grep` for `dist/variants/[*][*]`;
  - the FEATURE_INDEX row lines.
- The setuptools 84.0.0 and 68.0.0 source lines reproduce from wheels fetched into scratch (all 26 greps quoted in LD-5).
- Package index (2026-10-05T21:58Z):
  - `pip index versions` stdout first line `qor-logic (0.176.0)`, followed by 0.172.2, 0.169.2 and older;
  - JSON `info.version` 0.176.0, with the wheel uploaded 21:31:10Z and the sdist 21:31:12Z, neither yanked.
- Published wheels 0.176.0 and 0.172.2:
  - each holds 392 files under `qor/dist`, with no root manifest and no YAML;
  - the claude, codex, cursor and kilo-code manifests list 78 files each (5 YAML), and cline and gemini list 47 each;
  - each sdist holds the same 392 files;
  - the 0.176.0 METADATA carries "continues to install and work as documented".
  - Installed in fresh venvs: `list --available` prints the `No manifest` line and exits 1, and install records list 73, 73, 73 and 47 files, for both versions.
- `git ls-remote --tags origin`: `refs/tags/v0.176.0` peeled to 39974233, an ancestor of the base, with 216 tag names.
- Skill step references (/qor-substantiate Steps 7.6, 9.5.5 and 9.6) and the `release_state` and test-module signatures used by the CI commands exist.

#### Freeze amendment, release state and CHANGELOG
**Result**: PASS
- Phases 2 and 3 were applied verbatim from the plan's fenced blocks. A word diff shows that AGENTS line 8 keeps its prohibition and last sentence and only adds the three plan clauses. The README line names the packaging fix (A1 cured), and every factual clause in it was observed above.
- `freeze_check: OK`, exit 0. Test results:
  - test_freeze_check: `9 passed`;
  - release_state with tag coverage: `29 passed`;
  - changelog_format: `5 passed`;
  - the consumer set: `58 passed`.
- check_variant_drift gives `OK: 413 files, no drift`, and ruff is clean. The new lines are ASCII; the CHANGELOG's non-ASCII lines are pre-existing.
- CLAUDE.md ("frozen and superseded ... unless the owner lifts the freeze") and CONTRIBUTING.md stay true. The other freeze mentions name no version and stay true: docs/architecture.md, FEATURE_INDEX FX028, nightly-health.yml and doctrine-publication-boundary.
- The CI-view simulation prints `None True set() {'0.176.0'} {'0.175.7'}` at the base and with Phases 1 to 3 applied.
- Clone proof on simulated commits (scratch, TMPDIR in scratch):
  - base: exit 1, guard;
  - bump without stamp: exit 1, guard;
  - simulated seal (stamped by `changelog_stamp.apply_stamp`, local v0.176.1): exit 0, `4 passed`, twice;
  - seal without the 0.175.7 entry: exit 1 on orphan 0.175.7, where the plain local run gives `4 passed`;
  - seal with origin a scratch bare repo holding 215 of the 216 tag names (all but v0.176.0): exit 1 on orphan 0.176.0;
  - real remote again: exit 0.
  The remote tag, not a disposition, covers 0.176.0.
- The CHANGELOG bullets match the implementation and doctrine-changelog: user-facing, allowed labels, and no ledger number, hash or issue number. They say nothing false about 0.176.0 or earlier releases, and the dated [0.176.0] section is corrected forward, not edited.

#### Filter-Stage Ordering / Execution-Continuity
**Result**: N/A (no pipeline-shaped selection; no `execution_continuity`).

#### Orphan Pass
**Result**: PASS

| Proposed File | Entry Point Connection | Status |
|---|---|---|
| tests/test_package_data_ships_dist.py | pytest `testpaths = ["tests"]`; first CI Commands entry | Connected |

#### Executed reproduction (scratch clones outside the repository)
- Full suite results:
  - base: `3671 passed, 3 skipped, 4 deselected, 4 warnings`, exit 0;
  - Phase 1 only: `5 failed, 3674 passed`, exit 1, with exactly the five RED items failing;
  - Phases 1 to 3: `3679 passed, 3 skipped, 4 deselected, 4 warnings`, exit 0.
- Fixed wheel, `build` 1.6.1, `Generator: setuptools (84.0.0)`:
  - 599 non-.py files under qor/, set-equal to the simulation;
  - sdist and wheel each hold 413 of 413 tracked dist files and no other dist file.
- The same tree built with `PIP_CONSTRAINT` setuptools==68.0.0 (build log `setuptools==68.0.0`, `Generator: bdist_wheel (0.48.0)`): sdist and wheel each hold 413 of 413 tracked dist files and no other.
- Fixed wheel installed in a fresh venv:
  - `list --available` exits 0 and prints 47 lines, equal in order to the de-duplicated ids;
  - installs list 78, 78, 78 and 47 files.

#### Publication boundary
**Result**: PASS. The plan names no outside repository. Boundary lint: 0 findings.

### Violations Found

| ID | Category | Location | Description |
| --- | -------- | -------- | ----------- |
| - | - | - | None |

### Advisories (non-blocking)

- A1: LD-7 (line 221, "Versions already on the package index, 0.176.0 and 0.172.2 among them, keep the packaging fault") and the Declared Residuals (line 544, "Published versions on the package index keep the packaging fault") speak for every published version. Problem item 1 says earlier versions were not checked. The Judge spot-checked 0.169.2, 0.150.0, 0.120.0, 0.80.0, 0.40.0 and 0.13.0, and none ships `qor/dist/manifest.json` or any YAML. The text that ships (README, AGENTS, the CHANGELOG bullets) names only 0.176.0 and 0.172.2.
- A2: The `### Fixed` bullet's "a wheel built from these sources with the release build tools carried every tracked file" carries no setuptools-version qualifier. Release builds do not pin setuptools (LD-7). The clause is a true past-tense observation (84.0.0 and 68.0.0, re-observed above).
- A3 (carried A4 of #847, pre-existing, out of scope per LD-7): the README Quick Start names `cursor` and `cline`, which `--host` does not offer.
- A4 (carried A5 of #847): runtime_contract_walk gives 6 WARNs. The 3 backward WARNs are pre-existing CLI-dispatched modules. The 2 forward WARNs read the function references `qor.cli._default_dist_root` and `qor.hosts.resolve` as module paths. The backward WARN on `_default_dist_root` is a monkeypatch target, not a production import.

<!-- qor:drift-section -->
## Documentation Drift

(clean)

## Process Pattern Advisory

<!-- qor:veto-pattern-advisory -->

No repeated-VETO pattern detected in the last 2 sealed phases.

### Verdict Hash

SHA256(this_report) = recorded as the Content Hash of the META_LEDGER GATE TRIBUNAL entry for this audit

---
_This verdict is binding._
