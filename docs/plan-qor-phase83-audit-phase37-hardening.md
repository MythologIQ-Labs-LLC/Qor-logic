# Plan: Phase 83 — qor-audit Phase 37 Infrastructure Alignment hardening

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #83 + GH #87

**boundaries**:
- limitations: the citation consumer-trace sub-check is an auditor-executed
  prose procedure, not mechanically enforced; the delivery-branch helper
  verifies branch *existence* on the remote only — release-branch *open/closed*
  state is not git-derivable and is surfaced to the operator for confirmation.
- non_goals: not building a cross-language transitive-import tracer; not
  auto-resolving release-branch lifecycle (open vs closed) state.
- exclusions: the GH #87 comment's sibling facet — `/qor-plan` Step 0.5
  branching from `main` unconditionally regardless of unmerged predecessor
  phases — is out of scope; it belongs in its own issue/phase.

## Open Questions

None. The build shape (hybrid: #83 prose sub-check, #87 tested helper plus
prose) was settled in the planning dialogue.

## Design notes

The Phase 37 Infrastructure Alignment Pass is an LLM-executed prose procedure
in `qor/skills/governance/qor-audit/SKILL.md`, not a Python module. Both new
sub-checks are therefore realized as audit-pass prose, with one mechanical
slice (#87 branch existence) extracted into a tested helper. Per GH #92, the
extended procedure prose lands in a new qor-audit reference file rather than
inline in SKILL.md; SKILL.md gains only short pointers.

## Phase 1: Citation consumer-trace sub-check (GH #83)

The Phase 37 pass verifies a cited `file:line` / symbol EXISTS; it never
verifies the cited symbol is the one CONSUMED by the entry-point surface the
plan claims to fix. A plan can cite dead code and PASS audit.

### Affected Files

- `tests/test_audit_phase37_subpasses.py` - NEW. Wiring assertions for the
  consumer-trace sub-check.
- `qor/skills/governance/qor-audit/references/phase37-subpasses.md` - NEW.
  Holds the full consumer-trace procedure (progressive disclosure per GH #92).
- `qor/skills/governance/qor-audit/SKILL.md` - add a short consumer-trace
  pointer to the Step 3 Infrastructure Alignment Pass section.

### Changes

`phase37-subpasses.md` documents the **citation consumer-trace** procedure:
for every cited code symbol in a plan Locked Decision that claims to fix a
defect at a named UI / entry-point surface, the auditor (1) identifies the
entry-point file named in the plan, (2) greps for the cited symbol's
identifier within that file or its transitive import graph, (3) if the cited
symbol is not reached from the entry point, records an `infrastructure-mismatch`
finding (the symbol may be dead code or the wrong symbol was cited). The
procedure names the `infrastructure-mismatch` `findings_categories` value and
the per-ground directive (Governor amends the plan, re-runs `/qor-audit`).

`SKILL.md` Step 3 Infrastructure Alignment Pass gains one bullet pointing to
the consumer-trace sub-check in `references/phase37-subpasses.md`.

### Unit Tests

Tests authored and observed failing before the prose is written.

- `tests/test_audit_phase37_subpasses.py` -
  `test_skill_step3_points_to_consumer_trace_subpass`. Reads
  `qor-audit/SKILL.md`, locates the Step 3 Infrastructure Alignment Pass
  section, asserts it contains a reference to `references/phase37-subpasses.md`
  and the string `consumer-trace`. Confirms the audit skill is wired to invoke
  the sub-check; fails if the pointer is removed.
- `tests/test_audit_phase37_subpasses.py` -
  `test_consumer_trace_procedure_documented`. Reads
  `phase37-subpasses.md`, asserts the consumer-trace section names the three
  procedure steps (entry-point identification, grep-reachability, unreachable
  -> finding) and maps the failure to the `infrastructure-mismatch` category.
  Verifies the procedure a downstream auditor executes is fully specified, not
  a stub. This is the strongest unit-level coverage available for an
  LLM-executed prose sub-check: it asserts the wiring and procedure content,
  not the auditor's runtime reasoning.

## Phase 2: Delivery-Branch Currency sub-check (GH #87)

The Phase 37 pass grep-verifies cited infrastructure against the branch the
plan NAMES; it never challenges whether that branch is still an open delivery
target. A plan can PASS audit while its entire delivery premise is stale.

### Affected Files

- `tests/test_delivery_branch_lint.py` - NEW. Behavior tests for the helper.
- `tests/test_audit_phase37_subpasses.py` - extend with delivery-branch
  wiring + SG-doctrine round-trip assertions.
- `qor/scripts/delivery_branch_lint.py` - NEW. Pre-audit lint helper.
- `qor/gates/schema/plan.schema.json` - add optional `pr_target` string field.
- `qor/skills/governance/qor-audit/references/phase37-subpasses.md` - add the
  delivery-branch currency procedure.
- `qor/skills/governance/qor-audit/SKILL.md` - run `delivery_branch_lint` in
  the Step 0.6 pre-audit lint block; add a delivery-branch pointer to Step 3.
- `qor/references/doctrine-shadow-genome-countermeasures.md` - append
  `SG-DeliveryBranchDrift-A`.

### Changes

`delivery_branch_lint.py` — a pre-audit lint modeled on `plan_grep_lint.py`.
CLI: `python -m qor.scripts.delivery_branch_lint --plan <path> [--repo-root .]`.
It reads the plan markdown, extracts a `**pr_target**:` front-matter value via
regex. Before any subprocess call, `pr_target` is validated against the
conservative branch-name pattern `^[A-Za-z0-9._/][A-Za-z0-9._/-]*$` — this
rejects empty values, `-`-prefixed values (which `git` parses as options,
including the command-specifying `--upload-pack`), and values containing
characters outside a safe ref-name set. An invalid `pr_target` is reported as
a `LintWarning` and is **never** passed to `git` (closes the iter-1 OWASP A03
argument-injection finding). Core logic is a pure function
`check_delivery_branch(plan_path, branch_resolver)` where
`branch_resolver(branch_name) -> bool` reports whether the branch exists on
the remote; the default resolver shells `git ls-remote --heads origin
<pr_target>` (list-form argv, no shell=True) and is invoked **only after**
`pr_target` passes validation. When `pr_target` is absent the function returns
no findings (no-op — most plans target `main`). When `pr_target` is present
and valid but the resolver reports the branch absent, it returns one
`LintWarning` naming the branch. `main()` prints warnings to stderr and exits
non-zero on any finding; the qor-audit Step 0.6 wiring calls it with `|| true`
(WARN-only, consistent with the existing lint trio).

`plan.schema.json` gains `"pr_target": { "type": "string", "minLength": 1 }`
as an optional property — legitimizing `pr_target` as a declarable plan field.

`phase37-subpasses.md` documents the **delivery-branch currency** procedure:
the auditor (1) resolves the plan's `pr_target`, (2) confirms it exists on the
remote (the `delivery_branch_lint` result), (3) surfaces `pr_target` to the
operator for an explicit still-open confirmation — release-branch open/closed
state is not git-derivable, (4) grep-verifies cited migrations / schema
objects against `git show origin/<pr_target>:<path>` specifically. A citation
that resolves only against a non-target branch is an `infrastructure-mismatch`
VETO.

`SKILL.md` Step 0.6 adds `python -m qor.scripts.delivery_branch_lint --plan
"$PLAN_PATH" --repo-root . || true` to the pre-audit lint block; Step 3 gains
one delivery-branch pointer bullet.

`SG-DeliveryBranchDrift-A` is appended to the countermeasures doctrine with
the standard structure (Pattern / Originating recurrence / Countermeasure /
Cross-reference), citing GH #87 and the Accountable-App-3.0 `RC1.4` evidence.

### Unit Tests

Tests authored and observed failing before the helper is written.

- `tests/test_delivery_branch_lint.py` -
  `test_no_pr_target_yields_no_findings`. A fixture plan with no `pr_target`
  front-matter, passed to `check_delivery_branch` with a resolver that would
  raise if called; asserts the returned finding list is empty (the no-op path).
- `tests/test_delivery_branch_lint.py` -
  `test_existing_pr_target_yields_no_findings`. A fixture plan declaring
  `**pr_target**: RC1.4`; resolver returns `True`; asserts no findings.
- `tests/test_delivery_branch_lint.py` -
  `test_dash_prefixed_pr_target_rejected_without_resolver`. A fixture plan
  declaring `**pr_target**: --upload-pack=evil`; `check_delivery_branch` is
  called with a resolver that raises if invoked; asserts exactly one finding
  identifying the invalid `pr_target` and that the resolver was never called.
  Confirms the OWASP A03 argument-injection surface is closed — an invalid
  value never reaches `git`.
- `tests/test_delivery_branch_lint.py` -
  `test_absent_pr_target_yields_finding`. A fixture plan declaring
  `**pr_target**: RC9.9`; resolver returns `False`; asserts exactly one
  finding whose text names `RC9.9`.
- `tests/test_delivery_branch_lint.py` -
  `test_cli_exits_nonzero_on_absent_branch`. Invokes the module CLI via
  subprocess against the absent-branch fixture with an env-injected fake
  resolver; asserts exit code is non-zero and stderr names the branch.
- `tests/test_delivery_branch_lint.py` -
  `test_plan_schema_accepts_pr_target`. Loads `plan.schema.json`, validates a
  minimal plan payload carrying `pr_target: "RC1.4"`; asserts validation
  passes, and that a non-string `pr_target` is rejected.
- `tests/test_audit_phase37_subpasses.py` -
  `test_skill_step0_6_runs_delivery_branch_lint`. Asserts `qor-audit/SKILL.md`
  Step 0.6 invokes `qor.scripts.delivery_branch_lint`.
- `tests/test_audit_phase37_subpasses.py` -
  `test_delivery_branch_procedure_documented`. Asserts `phase37-subpasses.md`
  documents the four delivery-branch procedure steps and the operator
  open/closed confirmation.
- `tests/test_audit_phase37_subpasses.py` -
  `test_sg_delivery_branch_drift_entry_present`. Asserts
  `doctrine-shadow-genome-countermeasures.md` contains an
  `SG-DeliveryBranchDrift-A` entry with `**Pattern**`, `**Countermeasure**`,
  and `**Cross-reference**` segments.

## Feature Inventory Touches

None. The plan touches `qor/scripts/`, `qor/skills/`, `qor/gates/schema/`,
`qor/references/`, and `tests/`; it introduces no `src/` user-facing feature.

## CI Commands

- `python -m pytest tests/test_delivery_branch_lint.py -v` — behavior tests
  for the delivery-branch helper, including the no-op, existing, absent, CLI,
  and schema cases.
- `python -m pytest tests/test_audit_phase37_subpasses.py -v` — wiring and
  procedure-content assertions for both sub-checks plus the SG doctrine entry.
- `python -m qor.reliability.gate_skill_matrix` — confirms the qor-audit
  SKILL.md edits leave all skill handoff references resolvable.
