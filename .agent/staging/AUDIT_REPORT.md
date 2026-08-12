# AUDIT REPORT

**Verdict**: PASS
**Target**: docs/plan-qor-phase222-seal-ladder-as-data.md

**Iteration**: 2
**Date**: 2026-08-12
**Judge**: The Qor-logic Judge
**Mode**: solo (`audit_risk_score` -> `option_b_required: false`; codex-plugin and external reviewer absent, shortfall recorded)
**Phase**: 222 (GH #327)
**Risk Grade**: L2
**Prior verdict**: VETO at ledger #565 (`infrastructure-mismatch`, `specification-drift`, `test-failure`)

---

## Verdict Summary

All three iter-1 findings are closed, and each was closed by changing the
mechanism rather than the wording. The amendment also surfaced a defect the first
audit missed: iter-1's evidence blocks, even once corrected, were not in the form
`plan_grep_lint` accepts, so the enforcer had been reporting a different failure
than the one the Judge found. Both are now resolved.

Per Phase 72, this iteration triggers a **full re-walk of the entire Locked
Decision set**, not a diff against iter-1. Every citation below was re-executed
for this report.

---

## V1 -- `infrastructure-mismatch` -- CLOSED

Re-executed, full LD set, iter-2:

| LD | Citation | Executed result | Status |
|---|---|---|---|
| LD-1 | ladder extent | `awk .. \| wc -c` -> `6194`; `grep -n` -> `227:### Step 4.6:`, `346:### Step 4.7:` | REPRODUCES |
| LD-2 | `skill_size_budget_lint.py` rglob | `git show 6424413:.. \| grep -nE 'rglob'` -> `42:` | REPRODUCES |
| LD-2 | `install_drift_check.py` rglob | `git show 6424413:.. \| grep -nE 'rglob'` -> `24:` | REPRODUCES |
| LD-3 | `parse_step_prerequisites` | `git show 6424413:.. \| grep -nE 'def parse_step_prerequisites'` -> `45:` | REPRODUCES |
| LD-4 | baseline token extraction | 13 fenced commands + 42 backticked spans, union `55` | REPRODUCES |
| LD-5 | 4.6.11 absence | `grep -c "4\.6\.11"` -> `0` | REPRODUCES |

The line-42 correction also reached the two artifacts that carried the wrong
number: `docs/research-brief-open-issue-triage-2026-08-11.md` now carries a
"Correction of record" section, and GH #327 carries a correction comment
(`issuecomment-5260283433`). Ledger #564 is chain-bound to the uncorrected text
and correctly was not amended.

**Second-order finding, now also closed.** After correction, `plan_grep_lint`
still reported three warnings against the LD block. `_EVIDENCE_RE` is
`re.compile(r"grep\b.*->")` -- no `DOTALL` -- so the evidence statement must place
the command and its observed output **on one line**, which is the form
`qor/references/doctrine-shadow-genome-countermeasures.md` specifies for P1 and
which iter-1 never used. The plan had been failing the enforcer's actual contract
while appearing to satisfy the doctrine's prose. Reformatted to single-line
canonical form; `plan_grep_lint` now exits 0 with zero warnings, and each line was
re-run to confirm the quoted output is what the command prints.

## V2 -- `specification-drift` -- CLOSED

The claimed seal-ceremony consumer now exists. Phase 2's ladder preamble runs
`qor-logic scripts substantiate_gates --skill <this file> || ABORT` before the
table, so a malformed ladder halts the seal instead of only reddening CI.

Dispatch verified rather than assumed:

```
qor/cli.py:278  def _do_module_dispatch(family, args)
qor/cli.py:285  target = f"qor.{family}.{args.module}"
qor/cli.py:286  completed = subprocess.run([sys.executable, "-m", target, *args.args])
```

Generic dispatch, no registration required -- the module needs only a `__main__`,
which Phase 1 declares. List-form argv with no shell and an f-string family prefix
confining targets to `qor.scripts` / `qor.reliability`: OWASP A03 clean.

`test_ceremony_parses_the_ladder_before_executing_it` asserts **position** -- the
invocation precedes the table's first row -- not presence. A validation that runs
after the gates it validates is not a validation, and the test says so.
`test_a_malformed_table_fails_the_ceremony_entry_point` proves the wired command
can actually halt a seal.

The Feature Inventory justification now names both consumers and states that both
are created by this plan.

## V3 -- `test-failure` -- CLOSED

No hand-authored token list remains anywhere in the plan or the tests. The set is
extracted by `substantiate_gates.extract_ladder_tokens` from the ladder region of
pinned revision `6424413`: fenced non-comment command lines unioned with
backticked spans, executed count **55**.

Three properties make it non-vacuous:

- `test_extract_ladder_tokens_returns_the_pinned_baseline_count` pins 55, so an
  extractor returning the empty set fails rather than passing everything downstream.
- `test_removing_a_command_shrinks_the_extracted_set` proves the extractor reads
  what it claims to read.
- `test_the_survival_check_can_fail` blanks a Command cell in a post-rewrite
  fixture and requires the corresponding token be reported missing.

The set is 55, not the 16 iter-1 enumerated. Two of the ten gate commands
(`install_drift_check`, `publication_boundary_lint`) are backticked inline rather
than fenced -- exactly the kind of detail a hand list loses, and direct evidence
for why the derivation was the right remedy.

The fidelity property is correctly stated as survival into **the ladder table or
`references/seal-gate-ladder.md`**. Rationale pointers such as `SG-DoDImplicit-A`
legitimately relocate; asserting they survive into a table cell would have forced
either a false assertion or a padded table.

`6424413` verified as a commit and an ancestor of HEAD; CI checks out at
`fetch-depth: 0`, so the pinned read resolves there.

---

## Pass Results

| Pass | Result | Note |
|---|---|---|
| Prompt Injection | PASS | `prompt_injection_canaries` exit 0 over 4 files |
| Version-Applicability | PASS | `change_class: feature`; v0.144.0 -> minor, not release-class-blocked |
| Security (L3) | PASS | No auth, credential, or secret surface |
| OWASP Top 10 | PASS | A03 re-checked against the new dispatch: list-form argv, no shell, family prefix confines targets. No deserialization, no config surface |
| Ghost UI / Live-Progress | N/A | No UI surface |
| Section 4 Razor | PASS | Five small pure functions plus a dataclass and `__main__`; well under 250 lines, none near 40 |
| Self-Application | PASS | The plan's own discipline -- derive, do not enumerate -- is now applied to its own token set. iter-1 failed this and was VETOed for it |
| Test Functionality | PASS | Every planned test invokes a unit and asserts on output; the two presence-shaped assertions are justified and allowlisted (below) |
| Dependency Audit | PASS | No new dependencies |
| Macro-Level Architecture | PASS | Sits beside `substantiate_capability`, same layer, no cycle, single source of truth per table |
| Feature Test Coverage | PASS | `feature_inventory_touches` empty and truthfully justified; governance-only surface |
| Infrastructure Alignment | PASS | Full LD re-walk above; all six citations reproduce |
| Filter-Stage Ordering | PASS | The one ordering constraint -- parse before execute -- is asserted positionally by test |
| Orphan Detection | PASS | Two consumers, both built by this plan |
| Execution-Continuity | N/A | Plan declares no `execution_continuity` block |

### Presence-shaped assertions, adjudicated

Two assertions in this plan are textual rather than behavioral. Both are
legitimate because the property under test **is** textual, and both are declared:

| Assertion | Why it is not presence-only | Handling |
|---|---|---|
| `test_step_4_6_11_is_absent` raw-token half | The property is an absence in the artifact; there is no unit whose behavior could stand in for it | `# prose-lint: ok=locks LD-5, the absence is the assertion` |
| `test_every_baseline_token_survives_the_rewrite` | Reads parsed rows and a reference file, over a set derived from a pinned revision rather than authored | Behavioral by construction; no allowlist needed |

`prose_test_lint --tests-dir tests --enforce` is now in `## CI Commands`, closing
iter-1 advisory 1.

### Lint ladder, iter-2

| Lint | exit | WARN |
|---|---|---|
| `plan_iteration_status_lint` | 0 | 0 |
| `plan_grep_lint` | 0 | **0** (was 1, then 3) |
| `plan_test_lint` | 0 | 0 |
| `plan_text_consistency_lint` | 0 | 0 |
| `delivery_branch_lint` | 0 | 0 |
| `ci_coverage_lint` | 0 | **0** (was 2, then 10) |
| `plan_feature_tdd_lint` | 0 | 0 |
| `sg_closure_lint` | 0 | 40 entries, 0 without enforcer citation |
| `prose_test_lint --enforce` | 0 | 59 exempted |
| `publication_boundary_lint` | 0 | 0 at `structural+identity` |

`ci_coverage_lint` warnings went up before they went down: adding
`prose_test_lint` to the CI list caused the lint to re-evaluate and surface ten
uncovered standing workflow steps, not two. All ten are branch-wide governance and
packaging controls over surfaces this plan does not modify, and each is now named
individually in `## CI Coverage Exemptions` rather than waved through.

The iter-1 `plan_grep_lint` warning on a fixture value is gone: the
deliberately-wrong module path now lives only in
`tests/fixtures/seal_ladder_prereq_drift.md`, not in plan prose. A non-existent
module path in a plan is indistinguishable from a bad citation to both the lint
and a reader, and iter-1 was asking the reader to tell them apart.

---

## Advisory (non-binding)

1. **The pinned baseline couples two tests to full git history.**
   `6424413` is an ancestor of HEAD and CI uses `fetch-depth: 0`, so this holds
   today. A future move to shallow checkout would break the read loudly rather
   than silently, which is the acceptable failure direction, but the coupling is
   worth knowing before someone tunes checkout depth for speed.

2. **`plan_grep_lint` checks presence, not truth.** This audit found the falsified
   citation manually; the enforcer of that very discipline passed the plan
   carrying it. Extending it from "an evidence block exists" to "the cited
   `file:line` carries the quoted text" is mechanically checkable for the
   `file:line` citation kind and is recorded as the remedy candidate under
   candidate `SG-TranscribedEvidence-A`. Out of scope here; this plan should not
   grow a second deliverable.

3. **Open Question 2 remains correctly open.** Whether `doc_integrity` term-drift
   fires on the Policy column vocabulary is real and routed to pre-audit
   verification rather than seal-time discovery.

---

## Documentation Drift

None. `doc_tier: system` with two `terms_introduced`, both carrying `home:` paths
into an existing reference file; `boundaries` complete. Glossary `referenced_by`
registration is scheduled in Phase 3, the correct phase for it.

---

## Process Pattern Advisory

<!-- qor:veto-pattern-advisory -->
No repeated-VETO pattern detected in the last 2 sealed phases.

One VETO in this phase, resolved in one iteration. `cycle_count_escalator.check`
and `check_session_total` both return `None`.

---

_PASS. `/qor-implement` may proceed against iteration 2._
