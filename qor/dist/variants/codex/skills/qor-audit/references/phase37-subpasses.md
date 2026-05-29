# Phase 37 Infrastructure Alignment — extended sub-passes

Extended procedures for the `/qor-audit` Step 3 Infrastructure Alignment Pass.
Held here (not inline in `SKILL.md`) per GH #92 progressive disclosure: the
auditor loads this file only when the Phase 37 pass runs. SKILL.md carries a
one-line pointer to each sub-pass below.

---

## Citation consumer-trace sub-check (Phase 83 wiring; GH #83)

The base Phase 37 pass verifies a cited `file:line` / symbol EXISTS. It does
not verify the cited symbol is the one actually CONSUMED by the entry-point
surface the plan claims to fix. A plan can cite dead code — a symbol that
exists but has no consumer chain reaching the surface under repair — and the
existence check passes. The defect surfaces only at implement time.

For every cited code symbol in a plan Locked Decision that claims to fix a
defect at a named UI / page / endpoint / entry-point surface, the auditor
performs the **consumer-trace** procedure:

1. **Identify the entry point.** Locate the file the plan names as the surface
   it fixes (the component, page, route handler, or CLI entry the defect is
   observed at).
2. **Grep the reachability.** Search for the cited symbol's identifier within
   that entry-point file and its transitive import graph. The cited symbol
   must be reached from the entry point.
3. **Verdict.** If the cited symbol is not reached from the entry point, the
   symbol is either dead code or the wrong symbol was cited. Record an
   `infrastructure-mismatch` finding.

**Any unreached citation -> VETO with `infrastructure-mismatch` category.**
**Required next action:** Governor: amend the plan to cite the symbol actually
consumed by the named entry point (or correct the named entry point), re-run
`/qor-audit`. Per `qor/references/doctrine-audit-report-language.md`, this is a
**Plan-text** ground.

Originating evidence (GH #83): a consumer-repo plan cited a hook at line 85
that had zero consumers (an internal wrapper only); the hook actually consumed
by the named Home-tab surface was a different symbol entirely. The cite-exists
check passed; the mismatch was caught only mid-implementation.

---

## Delivery-Branch Currency sub-check (Phase 83 wiring; GH #87)

The base Phase 37 pass grep-verifies cited infrastructure against the branch
the plan NAMES. It never challenges whether that branch is still an open
delivery target. A plan can PASS audit while its entire delivery premise is
stale — cited infrastructure existing only on a branch that has closed for
new merges.

When the plan declares a `pr_target` (the branch it will merge into, when not
the default branch), the auditor performs the **delivery-branch currency**
procedure:

1. **Resolve `pr_target`.** Read the plan's `pr_target` value. When absent,
   the plan targets the default branch and this sub-check is a no-op.
2. **Confirm the branch exists on the remote.** The Step 0.6 pre-audit lint
   `qor-logic scripts delivery_branch_lint --plan "$PLAN_PATH"
   --repo-root .` runs `git ls-remote --heads origin <pr_target>` and reports
   a missing branch. (`pr_target` is allowlist-validated before reaching git;
   an invalid value is itself a finding.)
3. **Confirm the branch is still OPEN.** Release-branch open/closed state is
   NOT git-derivable — a branch can exist on the remote yet be closed for new
   merges. The auditor surfaces `pr_target` to the operator and obtains an
   explicit confirmation that the branch is still an open delivery target.
4. **Grep cited infrastructure against `pr_target` specifically.** For every
   cited migration / schema object / file, verify it resolves against the
   target branch — `git show origin/<pr_target>:<path>` — not merely against
   some branch. A citation that resolves only against a non-target branch is a
   stale-delivery-premise defect.

**A `pr_target` that is missing on the remote, closed for merges, or carries
citations that resolve only off-target -> VETO with `infrastructure-mismatch`
category.** **Required next action:** Governor: re-target the plan to a
currently-open delivery branch and re-verify all cited infrastructure against
it, re-run `/qor-audit`. Per `qor/references/doctrine-audit-report-language.md`,
this is a **Plan-text** ground.

See `qor/references/doctrine-shadow-genome-countermeasures.md`
`SG-DeliveryBranchDrift-A` for the originating recurrence and countermeasure.
