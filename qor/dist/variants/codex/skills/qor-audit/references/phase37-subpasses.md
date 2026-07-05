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
2. **Trace the reachability (runnable since Phase 126; GH #157).** Run the
   executable consumer-trace instead of a manual grep:

   ```bash
   qor-logic scripts citation_consumer_trace --entry <surface-file> --symbol <cited-symbol> --repo-root .
   ```

   `qor.scripts.citation_consumer_trace` greps the entry-point file for the
   cited symbol and follows the file's transitive in-repo import graph. Exit 1
   means the symbol is not reached (dead code or wrong symbol cited); a missing
   entry file prints `SKIP` and exits 0.
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

---

# Step 3 Infrastructure Alignment — extended rationale

## Runtime Contract Walk (Phase 99 wiring; GH #108 V2)

After the grep-verify checks in the Step 3 Infrastructure Alignment Pass, the
auditor runs the Runtime Contract Walk against the plan to catch runtime-contract
drift that grep cannot see — module imports that don't resolve at runtime,
callers whose own imports fail to parse, etc. The walk runs one hop forward
(callees: cited module's own imports must parse) and one hop backward (callers:
at least one production caller must parse) for each Python module path cited in
the plan. WARN-only in V2 (`qor-logic scripts runtime_contract_walk --plan
<plan-path> || true`); a future V2-of-V2 phase converts to hard VETO once
operator evidence on Phase 96 V1 false-positive rate is in. See
`qor/references/audit-runtime-contract-walk.md` for the detailed two-direction
protocol and `SG-GrepShapedRunclaim-A` for the binding doctrine.

## iter-N>1 full re-walk (Phase 72 wiring; GH #56; SG-CitationDrift-A)

On iterations after the first (iter-N>1), the Judge re-walks the **FULL Locked
Decision set**, not the diff-from-iter-N-1. Every sealed-infrastructure citation
(migration name, function signature, file:line, schema, env var, edge-function
path) is grep-verified against current code, including LDs that were not modified
in this iteration. Citations that lack the inline grep-evidence statement
required by `/qor-plan` Step 2 Infrastructure Citation Inventory trigger
immediate VETO with `infrastructure-mismatch` category — regardless of whether
the LD was amended in the current iteration. This closes the drift surface where
an unverified citation in an unchanged LD propagates across iterations without
re-challenge.

## Phase 83 extended sub-passes (GH #83 + GH #87)

- **Citation consumer-trace**: for every cited code symbol in an LD that claims
  to fix a defect at a named entry-point surface, verify the cited symbol is
  reachable from that entry point. An unreached citation (dead code, or the
  wrong symbol cited) is an `infrastructure-mismatch` VETO. (Full procedure: the
  consumer-trace sub-check section above.)
- **Delivery-Branch Currency**: when the plan declares a `pr_target`, verify the
  branch exists on the remote (the Step 0.6 `delivery_branch_lint` reports a
  missing branch), is still open for merges (operator confirmation — not
  git-derivable), and that cited infrastructure resolves against `pr_target`
  specifically. A stale delivery premise is an `infrastructure-mismatch` VETO.
  (Full procedure: the Delivery-Branch Currency section above.)

---

# Step 3 Ghost-UI Live-Progress Invariant (Phase 74 wiring; GH #58)

For every UI element with progress semantics (progress bar, spinner, phase
indicator, step list), the audit verifies that the element's state reflects the
underlying operation's progress at intermediate points, not only at start and
end. The inline SKILL.md checklist is the operative form; this is the rationale.

**Any violation -> VETO with `ghost-ui` category, sub-tag `live-progress-fake`**.
The sub-tag is prose-only (no `findings_categories` schema enum addition); the
existing `ghost-ui` enum value absorbs the new sub-rule. The implementing surface
MUST subscribe to the backing progress event stream and re-render on each event;
per-phase intermediate states are required. Per
`qor/references/doctrine-shadow-genome-countermeasures.md` SG-FakeProgress-A.

---

# Step 3 Filter-Stage Ordering Coherence — heuristic + procedure (Phase 78 wiring; GH #47)

For any function or method with a pipeline shape — candidate set -> multiple
filter stages -> selection — the Judge constructs the **pipeline stage dependency
graph** and verifies the code executes a topological sort of that graph. Catches
the consumer-workspace-class composition defect from META_LEDGER #209: stage-by-stage
correctness review (Wave 2 multi-agent or single-reviewer audit) passes each
filter individually, but `validate()` is invoked elsewhere instead of as the
first stage of `decide()`; invalid manifests with low cost score dominate
selection over valid candidates. Per GH #47.

Heuristic for V1 (operator-judgment-based): a pipeline shape is present when the
audited code uses any of:
- Rust functional chains: `.filter(...).filter(...).map(...)` over a candidate iterator
- Sequential `let after_X = filter_X(after_prev)` blocks composing a candidate set into a winner
- Python chained `filter(predicate, ...)` or comprehension stacks producing a selection
- TypeScript `.filter().filter().reduce()` over a candidate array

For each pipeline so identified, the Judge runs the 4-step **filter-stage
ordering coherence** procedure:

1. **Identify each filter stage's preconditions** — what invariants must hold on
   inputs for the stage's logic to be sound (e.g., "manifest has passed schema
   validation"; "user has an authenticated session"; "row is owned by current
   tenant").
2. **Identify each filter stage's invariants** — what the stage enforces on
   outputs (e.g., "candidate's `tier` matches request"; "candidate's
   `cost_score` is in [0, 1]"; "candidate is non-quarantined").
3. **Construct the dependency graph** — stage N depends on stage M iff M enforces
   an invariant that N's correctness *assumes*. If a filter references a struct
   field that is also referenced inside a separate validation / `check` /
   `verify` / `is_valid` function, raise the question: "did that validation run
   before this filter?"
4. **Verify the actual code order is a topological sort** of the dependency
   graph. Any inversion — stage N runs before stage M where N depends on M — is a
   defect.

Doctrinal precedent: this is structurally analogous to read-before-write checks
in static analyzers, lifted to the pipeline-stage abstraction. See
`qor/references/doctrine-shadow-genome-countermeasures.md`
`SG-FilterOrderInversion-A` for the originating consumer-workspace recurrence (skill_forge
dispatcher tier -> classification -> vendor -> cost without validator-first) and
the operator-fix regression test
(`test_dispatch_skips_invalid_skill_and_selects_valid_candidate`).
