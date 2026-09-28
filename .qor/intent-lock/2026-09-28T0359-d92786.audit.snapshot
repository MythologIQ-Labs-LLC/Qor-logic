# AUDIT REPORT

**Tribunal Date**: 2026-09-28
**Target**: `docs/plan-qor-phase301-shadow-breach-header.md`
**Iteration**: 1 (branch `phase/301-shadow-breach-header`, head `db2d8bd5`, plan-only; base `main` `e062a3dd` = 0.175.4)
**Session**: `2026-09-28T0359-d92786`
**Risk Grade**: L2
**Auditor**: The Qor-logic Judge
**Mode**: Option B fresh-context reviewer, independent of the plan author. `audit_risk_score` reported `option_b_required: true` (flag `high-citation-surface`), and this review is that independent audit. The Codex plugin is unavailable. `external_reviewer.run_external_review` returned `fallback` ("no reviewer configured"). Both `capability_shortfall` events were emitted (`abf45d14...` codex-plugin, `67560839...` external-reviewer). Reviewer toolset: shell, git (local objects, plus `git ls-remote` over the proxy), file read and grep, Python with the in-tree `qor` package on `PYTHONPATH`, and pytest in scratch clones outside the repository. No GitHub API was used.

---

## VERDICT: PASS

---

### Executive Summary

The plan closes GH #474 on all three reachable paths and does what it says. Every evidence statement reproduces at `e062a3dd`: 42 `git show ... | grep` statements, with 0 mismatches. The `git grep`, `merge-base`, ledger-line and remote-tag observations also reproduce.

The Judge rebuilt the Phase 1 test file from the plan text in a scratch clone of the base. The base gives `10 failed, 2 passed`. The Phase 2 code, applied as the plan specifies, gives `12 passed` twice. Mutations M1 to M8 each fail exactly the tests the plan names, with the stated counts (6/1/4/2/2/4/4/1 of 60). The consumer suites give `113 passed`. The full suite with Phases 1 to 3 gives `3627 passed, 3 skipped, 4 deselected`. Ruff and the publication-boundary lint are clean.

The real writer (`check_shadow_threshold.main`) was used to produce each marker, and every marker passes the new LD-6 type check, including one written after an aged-event escalation. The three #474 paths were prototyped end to end:

- `--events` with one severity-1 event is now filed as neutral, with the threshold "not checked".
- A `--mark-resolved` subset followed by a default run files the remainder as neutral, with the threshold "not reached". The writer agrees: `OK: 5 < 10`.
- A `--flip-only` subset with the marker surviving gives the same neutral result. The writer agrees: `OK: 7 < 10`.

The release-state proof is non-vacuous. The CI-view simulation prints `{'0.175.4'} {'0.175.4'}` at the base and `set() {'0.175.4'}` with the entry. The guarded clone proof fails in three cases: at the base, on a bump-only commit, and on a simulated seal commit without the entry (`1 failed, 3 passed`, orphan `0.175.4`). It passes with the entry (`4 passed`, twice). The remote's highest tag is `v0.172.2`.

The plain-sum residual was probed hard (A1). It can still produce a breach title that `check_shadow_threshold` would not agree with. That case is declared in the boundaries, in LD-5 and in the CHANGELOG rule. It is narrower than at the base, where the same filing had the same title, so it is not a reintroduction. The header never contradicts its own printed numbers on any branch.

### Pre-audit gates

- Governance health preflight (`python -m qor.cli governance-health --profile skill-entry`): all 8 artifacts OK.
- Step 0 gate check: plan artifact found and valid (`.qor/gates/2026-09-28T0359-d92786/plan-iter1.json`).
- Step 0.3 `plan_iteration_status_lint`: exit 0.
- Step 0.4 unchanged-plan short-circuit: `should_skip=False` (no prior audit in this session). Plan hash `71a00e948fa28efea5715a4272cec22e3cea134cd5538bcd28ddfe6c695db2d4`.
- Step 0.5 cycle-count escalator: `cce.check` returned None and `cce.check_session_total` returned None.
- Step 0.6 lints (WARN-only):
  - `plan_grep_lint`: 40 citations truth-checked, 0 findings.
  - `workspace_fragility_check`: medium (`dirty_gate_artifact_count=66`, pre-existing).
  - `sg_closure_lint`: 40 entries, 0 without an enforcer citation.
  - `gate_schema_freeze_lint`: 0.
  - `publication_boundary_lint`: 0 findings.
  - All other lints: no findings.
- Step 0.7 spec-delta pre-pass: no `spec_deltas` are declared. The only capability specs are `execution-context-governance` and `spec-corpus`, and neither covers shadow issue filing, so no contracted behavior changes without a delta.
- Version-Applicability Pass: `ok=True`, `hotfix`, target v0.175.5 > current highest v0.175.4.
- Prompt Injection Pass: `prompt_injection_canaries` over ARCHITECTURE_PLAN, META_LEDGER, CONCEPT and the plan exited 0.
- Runtime Contract Walk (WARN-only): 1 backward WARN (`qor.scripts.release_state` has no production importer). This is pre-existing and not touched by the plan.
- `prose_test_lint --tests-dir tests --enforce`: exit 0 (69 exempted with a reason).

### Audit Results

#### Security Pass
**Result**: PASS
The plan adds no auth logic, credentials, bypassed checks or mock returns. The `gh` argv construction is unchanged. The new `SystemExit` on a non-integer threshold fails closed, which is this loader's documented contract.

#### OWASP Top 10 Pass
**Result**: PASS
The plan adds no subprocess call and no deserialization beyond the existing `json.loads`. There is no fail-open: a wrong-typed threshold now stops with a named message instead of raising `TypeError` in the comparison.

#### Ghost UI Pass
**Result**: PASS (not applicable; no UI surface)

#### Section 4 Razor Pass
**Result**: PASS (see A2)
The new functions are short. `_severity_sum` has 1 line, `is_breach` about 8, `build_title` 5 and `_header` 29, all with nesting of 2 or less and no nested ternaries. `build_body` shrinks. The module was already over the file cap at the base (410 lines). The Judge's reconstruction is 464 lines, against the plan's 471, which carries the full docstrings. The plan declares the overage and accepts it (LD-7). `main` was already over the function cap at the base (116 lines), and the plan changes two of its lines with a net change of 0.

#### Self-Application Sub-Pass
**Result**: PASS
`originating_remediation: GH #474`. The discipline has two parts: a claim must be true of the numbers printed beside it, and a value has one owner. Both were applied to the plan itself:
- Every "observed" number the plan prints reproduces: 10 failed/2 passed, 12 passed, the M1 to M8 counts, 113, 34, 3627/3/4, both simulation outputs and the four clone-proof outcomes.
- The plan's CHANGELOG bullet claims no guarantee wider than the rule it implements. It names the plain sum as the compared number, which matches the LD-5 residual.
- The plan restates no owned constant: the `--events` threshold is read from `_cst.THRESHOLD` at call time, and M5 proves that a restated literal fails.

#### Test Functionality Pass
**Result**: PASS

| Test description | Invokes unit? | Asserts on output? | Verdict |
| --- | --- | --- | --- |
| `test_events_selection_never_claims_a_breach` (x2) | yes (`csi.main` via `--dry-run --events`) | yes (exact title, heading, sum line; no `Detected:`; no "breach") | PASS |
| `test_marker_subset_below_threshold_is_not_framed_as_breach` | yes (`csi.mark_resolved`, then `csi.main`) | yes (exact title and four header lines) | PASS |
| `test_marker_at_threshold_keeps_the_breach_title_and_header` | yes (`csi.main`) | yes (exact base title and five base header lines) | PASS |
| `test_breach_is_judged_against_the_marker_threshold` (x2) | yes (`csi.main`) | yes (breach prefix and heading in both directions) | PASS |
| `test_events_threshold_is_read_from_the_writer` (x2) | yes (`csi.main`, with `cst.THRESHOLD` patched) | yes (exact sum line carrying the patched value) | PASS |
| `test_load_marker_rejects_a_non_integer_threshold` (x4) | yes (`csi.load_marker`) | yes (`SystemExit` message naming `threshold` and "expected an integer") | PASS |

Acceptance question: each mutation M1 to M8 turns its named items RED, as observed, so a silent break in behavior would fail a test. The tests use only `tmp_path`, `monkeypatch`, `capsys` and fixed timestamps, with no network and no live state.

#### Dependency Pass
**Result**: PASS
The plan adds no dependency. The new import is the in-package `qor.scripts.check_shadow_threshold`.

#### Macro-Level Architecture Pass
**Result**: PASS
The import adds no cycle. `check_shadow_threshold` imports `session`, `shadow_process` and `workdir`, plus a function-local import of `remediate_mark_addressed`, and nothing under `qor/` imports `create_shadow_issue`. The collector reaches it only through a `--flip-only` subprocess. After the fix the threshold has one owner. The breach predicate stays with `check_shadow_threshold`: the wording rule compares printed numbers and does not recompute the collapsed sum.

#### Feature Test Coverage Pass
**Result**: PASS (exempt; `feature_inventory_touches: []`, governance script only)

#### Infrastructure Alignment Pass
**Result**: PASS (see A4)
- All 42 evidence statements reproduce at `e062a3dd`, and the other quoted outputs reproduce.
- `git grep 'Process threshold breach' -- qor tests` gives one line (384).
- The same grep over the whole tree lists four files, as quoted.
- `.github` has no `qor-shadow` or "threshold breach" match.
- No `qor/*.py` imports `create_shadow_issue`.
- `v0.175.4` is a local ancestor of the base, and the remote's highest tag is `v0.172.2`.
- The ledger lines 24134, 24228, 24381 and 24475 reproduce.
- `docs/release-state.json` line 80 holds `0.175.3` and has no `0.175.4` entry.
- The base `--events` output reproduces the Problem statement exactly: "Process threshold breach", "Severity sum: **1** (threshold 10)" and a filing-time `Detected:`.
- `git log -S'"threshold":'` over the writer shows one introducing commit, and it has always stored the `int` `THRESHOLD`. `.qor/remediate-pending` is gitignored and absent, so no committed marker exists that LD-6 could reject.
- No consumer reads the title or body text. Tests assert only on the collector's own body builder. No skill or compiled variant quotes the header. The only title-bearing sibling is `collect_shadow_genomes`, which is not changed. `ac_close_guard` searches bodies for `#N`, and `nightly-health.yml` searches its own title. `advisory_filing_control.inspect` renders nothing for either new header.
- Delivery-branch currency: the remote `main` is `e062a3dd`, the branch base.

#### Filter-Stage Ordering Coherence
**Result**: PASS
The pipeline in `main` runs in this order: parse, then resolve the marker (or `None`), then read the events, then select the unaddressed events in the target set, then compute `is_breach` over the selection, then build the title and body. The wording predicate runs after the selection it describes, and no stage runs before its precondition.

#### Orphan Detection
**Result**: PASS

| Proposed File | Entry Point Connection | Status |
| --- | --- | --- |
| `tests/test_shadow_issue_header.py` | pytest collection (`tests/`) | Connected |
| `qor/scripts/create_shadow_issue.py` (modified) | `qor-logic scripts create_shadow_issue`; `python -m qor.scripts.create_shadow_issue` | Connected |
| `docs/release-state.json` (modified) | `tests/test_changelog_tag_coverage.py` via `release_state.load_release_state` | Connected |
| `CHANGELOG.md` (modified) | `/qor-substantiate` stamp; `tests/test_changelog_format.py` | Connected |

### Probe record (scratch clones outside the repository)

Each scenario was run through the real writer (`check_shadow_threshold.main --log`), then the named action, then a `create_shadow_issue --dry-run` default run, then a writer `--dry-run` re-check:

- `--events`, one severity-1 event, no marker. Title `Process shadow events - 1 events, sev 1`. Sum line `(threshold 10; not checked: the events were named with --events)`. No time line.
- Two severity-5 events (writer `BREACH 10 >= 10`, marker `threshold` type `int`), then `--mark-resolved` on one. Title `Process shadow events - 1 events, sev 5`. Sum line `(threshold 10; not reached by these events)`. The writer now reports `OK: 5 < 10`.
- Severities 5/5/2 (writer `BREACH 12`), then `--flip-only` on one. Title `Process shadow events - 2 events, sev 7`, "not reached". The writer now reports `OK: 7 < 10`.
- Recurrence residual: two severity-5 events sharing gate `a`, plus a severity-5 event on gate `b` (writer collapsed `10`), then `--mark-resolved` on `b`. Title `Process threshold breach` + em dash + ` 2 events, sev 10` (base breach text). Header `Severity sum: **10** (threshold 10)`. The writer now reports `OK: 5 < 10` (A1).
- Full marker, same three events, no resolution: breach with plain sum 15. The writer still reports a breach.
- Aged severity-3 event escalated to severity 5 (writer collapsed `12`): breach with plain sum 15. The marker passes `load_marker`.

### Violations Found

None.

### Advisories (non-VETO)

- **A1 (declared residual, reproduced)**: the plain-sum rule can still title a filing a threshold breach when `check_shadow_threshold` would not agree. The reproduced case is a partial resolution whose remainder repeats a signature: plain sum 10, collapsed sum 5. The header is consistent with the numbers it prints. It is not consistent with the owner's measure, which the printed "Severity sum" is not. This is exactly what the limitations boundary, LD-5 bullet 1 and the CHANGELOG rule ("the plain sum of the filed events") state. At the base the same filing carried the same breach title, so the fix narrows the defect and does not reintroduce it. The neutral branches cannot err in the other direction: for schema-valid events the plain sum is at least the collapsed sum, so a "not reached" header never covers a selection whose own collapsed sum reaches the threshold.
- **A2 (Razor, pre-existing)**: `create_shadow_issue.py` was 410 lines at the base and grows by about 55 to 61 lines. `main` was 116 lines at the base, with a net change of 0. Both overages are pre-existing, and the plan declares the file-size disposition (LD-7). The same disposition was accepted for the over-cap test files in Phases 279 and 300.
- **A3**: `workspace_fragility_check` reports medium (66 dirty gate-artifact directories), which is pre-existing. The local `main` ref is stale (`15729311`), while the remote `main` and the branch base are `e062a3dd`.
- **A4 (plan precision)**: LD-5 says "the only `gh issue list` search under `qor/` is in `ac_close_guard.py`". `qor/references/github-api-helpers.md` line 44 also carries a documentation example, `gh issue list --state open`. That example is not a search and not a dedup key, so the claim holds in substance.

## Documentation Drift

<!-- qor:drift-section -->
(clean)

## Process Pattern Advisory

<!-- qor:veto-pattern-advisory -->

No repeated-VETO pattern detected in the last 2 sealed phases.

### Report Hash

SHA256(this_report) is recorded as the Content Hash of the GATE TRIBUNAL entry in `docs/META_LEDGER.md`. A report cannot contain its own hash.

---
_This verdict is binding._
