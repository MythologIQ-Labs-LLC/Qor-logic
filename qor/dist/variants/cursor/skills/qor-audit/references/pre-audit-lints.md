# Pre-audit lint ladder — per-lint wiring rationale

Extended rationale for the `/qor-audit` Step 0.6 pre-audit lint ladder. Held
here (not inline in `SKILL.md`) per GH #92 progressive disclosure: the auditor
loads this file only when investigating why a particular Step 0.6 lint exists or
what recurrence it closes. SKILL.md carries the runnable command block + a
one-line pointer to this file. All Step 0.6 lints are WARN-only (`|| true`); the
binding VETOs remain the Step 3 passes (Test Functionality, Infrastructure
Alignment, Filter-Stage). The ladder catches these classes earlier so the
Governor can remediate without consuming an audit cycle.

The base closure: the cross-session recurrence pattern flagged across Phase
53/54/55 first audits per `qor/references/doctrine-shadow-genome-countermeasures.md`
SG-PreAuditLintGap-A.

---

## Phase 110 wiring (GH #133 + #134) — `plan_signature_widening_caller_lint` + `plan_data_round_trip_lint`

These two lints catch the SG-AffectedFilesContract-A cascade family — caller
files unenumerated on a signature widening, and persistence-layer touchpoints
unenumerated on a struct-field addition — before the binding Step 3 passes
consume an audit cycle. WARN-only V1 (`|| true`); escape hatches
`<!-- signature-widening-exempt: <fn> -->` and
`<!-- transient-field: Struct.field reason: ... -->`. Per
`qor/references/doctrine-shadow-genome-countermeasures.md` SG-AffectedFilesContract-A.

## Phase 67 wiring (GH #42) — `plan_text_consistency_lint`

Catches the consumer-workspace-class drift pattern — same operation specified differently
at multiple plan sites (commands, dependencies, paths). WARN-only at audit time;
the operator amends drift before the binding Infrastructure Alignment Pass in
Step 3 would consume an audit cycle. Per
`qor/references/doctrine-shadow-genome-countermeasures.md` SG-PlanTextDrift-A.

## Phase 89 wiring (GH #91) — `ci_coverage_lint`

Reconciles the plan's `## CI Commands` bullets against the Python-fingerprint
`run:` steps discovered in `.github/workflows/*.yml`. Catches the consumer-workspace-class
credibility failure where a phase seals "all CI green" while a real GitHub
Actions job — one the operator simply forgot to enumerate — would fail. WARN-only;
tag-only workflows are skipped; environment-setup boilerplate is filtered. The
plan may declare a `## CI Coverage Exemptions` block (bullet list with substring
patterns) to justify CI jobs that are pre-existing infrastructure not
phase-relevant. Per `qor/references/doctrine-shadow-genome-countermeasures.md`
SG-CICoverageDrift-A.

## Phase 130 wiring (GH #159) — `plan_feature_tdd_lint`

Mechanically enforces the plan-time half of `doctrine-feature-tdd.md`: for each
`## Feature Inventory Touches` row whose `operation` is `NEW`/`MODIFIED` (a
src-touch), it requires a real `test_path` + a behavioral `test_descriptor`
(failing-test-first), and flags a plan that touches `src/` with no FIT block.
`n/a-justified` rows + docs-only plans are exempt. WARN-only; the binding VETO
stays the Step 3 Feature Test Coverage Pass.

## Phase 127 wiring (GH #156) — `plan_live_progress_lint`

The mechanical SG-FakeProgress-A detector: it scans the target repo's frontend
source for the fake-jump (`0%`->`100%` with no intermediate width write),
missing-event-subscription, and error-without-dismiss patterns the Ghost-UI
Live-Progress sub-rule describes. WARN-only at this layer; the binding VETO
remains the Step 3 Ghost-UI pass (`ghost-ui` category, `live-progress-fake`
sub-tag, now a `findings_categories` enum value). Backend-only repos produce
zero findings. Escape: `// qor:live-progress-ok`. Per
`qor/references/doctrine-shadow-genome-countermeasures.md` SG-FakeProgress-A.

## Phase 94 wiring (GH #90) — `workspace_fragility_check`

Inspects local workspace signals (untracked file count, dirty gate artifacts
whose sessions are not yet sealed, ledger chain-math failures, active local
branch count, branch-diff size since divergence from `origin/main`) and surfaces
a stabilization-capacity grade (`low` / `medium` / `high`) before the audit
consumes a cycle. Companion to Phase 93's macro `merge_velocity_check` (Step
4.6.8): Phase 93 looks at `origin/main`'s recent merge history (BACKWARD); Phase
94 looks at the LOCAL working tree (FORWARD pre-merge). WARN-only V1; CLI exits 1
on `high` so V2 can convert to a hard ABORT by removing the `|| true` wrap. Per
`qor/references/doctrine-shadow-genome-countermeasures.md` SG-MergePaceThrottle-A
inline-companion sub-paragraph.
