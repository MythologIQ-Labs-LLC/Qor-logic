# AUDIT REPORT -- Phase 206 (GH #293 / PR #294), iteration 2

**Verdict**: PASS
**Risk Grade**: L2
**Target**: docs/plan-qor-phase206-badge-layout-resolution.md
**Session**: 2026-08-01T1437-73f42e
**Branch**: fix/293-badge-layout-resolution
**Mode**: solo (audit_risk_score option_b_required=false; codex/external reviewer not configured)
**Prior verdict**: VETO at ledger entry #502 (grounds: `razor-overage`, `specification-drift`)

## Scope note

As in iteration 1, the Judge audits the plan AND the branch state the plan proposes to carry to seal.
Iteration 1 VETOed on two grounds; both are re-walked below against measured branch state, not against
the plan's claims about itself.

## Prior-ground disposition

**Ground 1 (`razor-overage`) -- CLEARED.** Re-measured with `ast` spans and `splitlines()`:

| Unit | Cap | iter-1 branch | iter-2 branch | Verdict |
|---|---|---|---|---|
| `qor/scripts/seal_artifacts.py` (file) | 250 | 323 | **249** | CLEAR |
| `qor/scripts/badge_currency.py` (file) | 250 | 250 | **249** | CLEAR |
| `qor/scripts/badge_layout.py` (file, NEW) | 250 | -- | **62** | CLEAR |
| `seal_artifacts.main` | 40 | 63 | **21** | CLEAR |
| `seal_artifacts.update_files` | 40 | 42 | **29** | CLEAR |
| `badge_currency.check_currency` | 40 | 41 | **32** | CLEAR |

Longest function across all three modules is `count_tests` at 33 (pre-existing, unchanged). Max nesting
depth 3 (`badge_currency`), 2 (`seal_artifacts`), 0 (`badge_layout`) -- all within the cap of 3. Zero
nested ternaries in all three.

The remedy matches the one the VETO named: the six loose parameters collapsed to one frozen
`BadgeLayout` value threaded as a single keyword, and the value plus its CLI plumbing moved to a new
`badge_layout` module when folding it into `badge_currency` pushed that file to 275. CLI flag names,
defaults, and rendered output bytes are unchanged.

**Ground 2 (`specification-drift`) -- CLEARED.** The plan no longer claims a red-then-green transition
for the `update_files` change. LD-3 is restated correctly and now carries the second, decisive fact the
first iteration missed: the `counts=None` fallback is not merely unreachable from `main`, it is
unusable in any synthetic repository, because `collect_counts` reaches `count_tests`, which shells out
to `pytest tests/ --collect-only` and raises when there is no `tests/` directory. The plan's closure
changed accordingly, from "forward a layout into the fallback" to "delete the fallback". Phase 2 D4
states explicitly that no red-then-green claim is made and names what is verified instead.

## Mechanical Gates

| Gate | Result |
|---|---|
| governance-health --profile skill-entry | OK (all 8 artifacts) |
| plan_iteration_status_lint | rc 0 (ready) |
| prompt_injection_canaries (ARCHITECTURE_PLAN, META_LEDGER, CONCEPT, PLAN) | rc 0 (clean) |
| plan_test_lint | rc 0 |
| plan_grep_lint | rc 0 |
| plan_text_consistency_lint | rc 0 |
| plan_signature_widening_caller_lint | rc 0 |
| plan_data_round_trip_lint | rc 0 |
| plan_feature_tdd_lint | rc 0 |
| prose_test_lint --enforce | rc 0 (54 pre-existing exemptions) |
| ruff (three touched modules) | All checks passed |
| audit_risk_score | option_b_required=false |
| runtime_contract_walk | 1 WARN (advisory; V2 WARN-only) |
| full suite | 2721 passed, 5 skipped, 4 deselected |

## Adversarial Passes

- **Prompt Injection**: PASS. Canary scan clean over the four governance files.
- **Security L3**: PASS. The refactor moved `BadgeLayoutError`, `BadgeLayout`, and the CLI helpers
  without touching `_resolve_count_root` or `_count_matching`, so every confinement check is
  byte-identical: a traversing `configured_root` fails `relative_to(repository)`; an absolute or
  `..`-bearing pattern is rejected before any glob; a symlinked match raises; a regular file reached
  through a symlinked parent resolves outside the repository and raises. `update_files` narrowing
  `counts` to required removes a path that could silently re-derive a layout the caller did not
  declare, which tightens rather than relaxes. No auth surface, no credentials, no SQL.
- **OWASP Top 10**: PASS. A03: `count_tests` retains list-form argv with `sys.executable`, no
  `shell=True`, unchanged. A04: the branch removes a fail-open (synthetic zero) and now removes a
  second implicit-default path. A05: no secrets. A08: no pickle/eval/exec/unsafe yaml.
- **Ghost UI / Live-Progress**: PASS (no UI surface).
- **Section 4 Razor**: PASS. See the disposition table above.
- **Self-Application**: PASS. No `originating_remediation` declared.
- **Test Functionality**: PASS. Every described test invokes the unit and asserts on output.
  `test_seal_write_regenerates_badges_for_declared_layout` seeds a stale `Skills-99` badge into a repo
  with no `qor/` roots and asserts the written README carries `Skills-1` and no longer carries
  `Skills-99` -- an assertion on rendered bytes, which fails if the layout does not reach the counters
  (the process would abort instead of writing). The extension to
  `test_declared_non_qor_layout_counts_actual_files` asserts `count_by_layout` returns the exact
  three-key count dict. The Judge notes that a signature-introspection test was drafted for the
  `update_files` narrowing and correctly withheld: it would have asserted structure, not behavior.
  No closed-enum taxonomy is declared, so inverse-coverage discipline does not apply.
- **Dependency Audit**: PASS. No new dependencies; `dataclasses` is stdlib.
- **Macro-Level Architecture**: PASS. Layering is one-directional and acyclic:
  `badge_layout` (what a layout is) <- `badge_currency` (counting) <- `seal_artifacts` (writing).
  `badge_currency` re-exports the five layout names through an explicit `__all__`, so the import
  surface every existing caller depends on is preserved and there is a single source of truth for the
  defaults (`DEFAULT_LAYOUT`), replacing the eighteen restatements of `badge_currency.DEFAULT_*` that
  iteration 1 carried.
- **Feature Test Coverage**: PASS. `feature_inventory_touches: []`; the plan touches `qor/scripts/` and
  `tests/` only. Exempt per the docs/governance carve-out.
- **Infrastructure Alignment**: PASS. LD-1 and LD-2 citations re-verified at the cited lines. LD-3's
  citation is now historical (it cites the pre-refactor call site as the ground for deletion) and is
  labelled as such in the plan. LD-4 and LD-5 cite measurements reproduced above. The one NEW file,
  `qor/scripts/badge_layout.py`, is declared NEW in Phase 2 Affected Files.
- **Filter-Stage Ordering**: PASS. `_count_matching` is untouched and its execution order remains a
  valid topological sort: pattern validation -> root resolution and confinement -> glob -> symlink
  rejection -> regular-file filter -> per-match confinement -> increment.
- **Orphan Detection**: PASS. `qor/scripts/badge_layout.py` is reachable:
  `qor/scripts/badge_currency.py:20: from qor.scripts.badge_layout import (...)`, and `badge_currency`
  is imported by `seal_artifacts`, which is on the substantiate and CI paths.

## Signature-narrowing disclosure

`seal_artifacts.update_files` changes from `counts: dict[str, int] | None = None` to
`counts: dict[str, int]` (required). Every call site was enumerated: `seal_artifacts.main` and
`tests/test_seal_artifacts.py`, both of which already pass `counts`. No caller breaks. The Judge
records that this is a narrowing of an importable function signature and considered whether it forces
`change_class: breaking`. It does not: the module is an internal script module, the removed default was
unusable outside a repository containing a `tests/` directory, and the CLI contract -- the surface
consumers actually invoke -- is unchanged in flags, defaults, and output. The operator-declared
`feature` class stands. This disclosure carries into the seal entry.

## Advisory Findings (non-binding)

- `runtime_contract_walk`: 1 WARN, "backward: `qor.scripts.badge_currency` -- no production caller
  imports/invokes". WARN-only in V2. `seal_artifacts` does import it; classifier artifact.
- `ci_coverage_lint`: WARNs for workflow commands not named in the plan's `## CI Commands`. Generic to
  any narrow plan.
- `sg_closure_lint`: 40 entries, 10 without enforcer citation. Pre-existing corpus debt.
- `workspace_fragility_check`: fragility=medium, `recommended_action=branch_only`. Scope stayed narrow.
- Live-repo `seal_artifacts --check` currently reports `ledger: README declares 501, truth 502`. This is
  the expected consequence of appending the iteration-1 VETO entry; the seal ceremony regenerates it.
- Operator environment: the locally installed `qor-audit` and `qor-refactor` skill copies name a
  `qor-logic-plus` CLI while the repo source names `qor-logic`. Install drift; outside this plan's scope.
- Shadow Genome: iteration 1 recorded `Parameter-smear` as a candidate pattern
  (`SG-ParameterSmear-A`, first observed instance). No pre-audit lint measures function or file length,
  which is why the overage surfaced only at the manual Razor pass after a full CI cycle had been spent.

## Documentation Drift

`doc_integrity.render_drift_section` returned empty.

## Process Pattern Advisory

<!-- qor:veto-pattern-advisory -->
No repeated-VETO pattern detected in the last 2 sealed phases.

## Findings Categories

None (PASS).

## Verdict

**PASS** at L2. Both iteration-1 grounds cleared against measured branch state. Next: `/qor-implement`.
