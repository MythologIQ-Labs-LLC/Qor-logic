# Research Brief

**Date**: 2026-09-09
**Analyst**: The Qor-logic Analyst
**Target**: `nightly-health.yml` exit-code contract; `github_surface` advisory
posture; GH #432, #431, #465 as one unit
**Scope**: why the nightly job has failed five consecutive nights, what the
current findings actually are, and which of the three issues is a code defect

---

## Executive Summary

The nightly-health job has failed every night from 2026-09-05 to 2026-09-09.
It dies at the publication-boundary step, which is **documented as advisory in
three independent places and implemented as enforcing**. Every step after it --
the governance aggregate, the packaging smoke, and both halves of the
health-issue lifecycle -- has not run on any of those nights.

The harm is live and measured, not hypothetical: `status_json` exits 1 today
with a real `governance-index` failure, and the lifecycle step that would have
filed it never executed. No health issue is open.

Of the eighteen current findings, **none is a code defect**. Five are the
detector's own specification examples, twelve are genuine outside-repository
references awaiting the human anonymization the doctrine reserves to an
operator, and one is a drive-letter path inside an issue body. Exactly one of
the three issues in scope, GH #432, is fixable in code.

## Findings

### 1. The advisory contract is stated three times and implemented once, inverted

| Where | Statement |
|---|---|
| `qor/scripts/github_surface.py:13` | "Read-only by design. A finding is reported for a human to anonymize" |
| `.github/workflows/nightly-health.yml:48` | "Reports only; a finding is for a human to anonymize." |
| `qor/references/doctrine-publication-boundary.md:82` | "The scheduled scan is read-only and reports for a human to anonymize" |

Against that, `qor/scripts/github_surface.py:130` returns `1 if findings else 0`,
and `.github/workflows/nightly-health.yml:51` consumes it as a bare `run:` with
no `continue-on-error` and no `set +e`. A finding therefore fails the step, and
a failed step ends the job.

The inversion is visible **within the same file**. The two steps whose verdicts
are genuinely enforcing both refuse to fail:

- `nightly-health.yml:57` (`Aggregate governance health`) -- `set +e`, capture
  `$?` into `health_failed`
- `nightly-health.yml:74` (`Packaging smoke`) -- `set +e`, capture `$?` into
  `smoke_failed`

They do this precisely so the lifecycle steps at `:79` and `:97` can read the
verdict and act on it. The one step documented as advisory is the only step in
the job that hard-fails.

### 2. Measured harm: real drift is live and was never reported

Run today against a clean checkout of `main`:

```
python -m qor.scripts.status_json --repo-root .   -> exit 1
  FAIL [governance-index/stale-tier1]: docs/GOVERNANCE_INDEX.md --
  Last Reviewed 2026-09-08 predates latest seal 2026-09-09
  overall_ok: false
```

`nightly-health.yml:79` fires when `health_failed != '0'`, so this drift should
have opened or updated the "Nightly governance health" issue. No such issue is
open. The self-test at `:41` passes, so the checker is trustworthy and the
verdict is real -- the job simply never reached it.

This is the concrete cost of the defect: the repository's only automated
governance watchdog has been silent for five nights while there was something
to say.

### 3. `continue-on-error: true` is the wrong fix -- exit 2 must survive

`github_surface.main` has a three-valued contract:

- `:123` returns **2** when the surface could not be read (`RuntimeError`,
  `OSError`, `ValueError` -- including `gh` absent from PATH)
- `:130` returns **1** when the scan succeeded and found something
- `:130` returns **0** when the scan succeeded and found nothing

`continue-on-error: true` -- the shape used at `oss-sast.yml:38` -- swallows 1
and 2 alike, converting "the boundary was never checked" into silence. That
trades a loud wrong failure for a quiet wrong success. The fix must keep 2
fatal while making 1 advisory, which is what the `set +e` + captured-`$?` idiom
already in this file expresses.

### 4. Composition of the eighteen findings, measured

From the 2026-09-09 run log, classified against the doctrine:

| Class | Count | What it is | Disposition |
|---|---|---|---|
| A. Detector specification examples | 5 | Synthetic identifiers in one pull-request body, written as the expected-flagged rows of the detector's own test table | Marker on the surface copy; no code change |
| B. Genuine outside-repository references | 12 | References to three distinct outside repositories across five pull-request bodies and three issue comments | Human anonymization; `doctrine-publication-boundary.md:82-83` reserves this to an operator |
| C. Drive-letter absolute path | 1 | One issue body, inside a fenced block quoting console output | Human edit of that body |

None of the three classes is a defect in code. The detector is behaving to
specification in all eighteen cases.

### 5. Class A is a doctrine-granted exception whose mechanism exists and was dropped on one surface

`doctrine-publication-boundary.md:69-71` names "a specification describing the
detector" as a legitimate use of the `boundary-lint: ok=<reason>` marker.
`publication_boundary_lint.py:51` compiles that marker and
`publication_boundary_lint.py:108` applies it per line inside `scan_text`, which
is the function both surfaces share -- so a pull-request body line can carry the
marker exactly as a tracked file line does.

The tracked plan file for the phase that introduced these examples carries the
marker on every affected line
(`docs/plan-qor-phase268-self-reference-detector.md:111-112`, among others). The
same table, copied into the pull-request body that shipped it, carries none.
The exception was applied correctly to one copy of the text and dropped on the
other. Five of the eighteen findings clear with an edit to that body.

### 6. Sibling-plan check: Phase 268 documented this defect and explicitly declined it

`docs/plan-qor-phase268-self-reference-detector.md:233-236`:

> **Neither number changes the job's colour.** `github_surface.py:130` returns
> `1 if findings else 0`, and `nightly-health.yml` sets no `continue-on-error`,
> so the step fails at 17 and fails at 12. The benefit is that all 12 are
> actionable; there is no gate-state improvement and this plan does not claim
> one.

The defect was seen, stated accurately, scoped out, and filed as GH #432. No
plan in the corpus holds a mechanism for it. Nothing here supersedes Phase 268;
this work completes what that plan deliberately left.

### 7. GH #465's stated premise does not survive measurement

The issue's title and summary claim two `audit.json` gate artifacts record a
gate-artifact path in `target`, one as an absolute local path. Measured:

- Both cited files are `remediate-iter1.json`, not `audit.json`
  (`.qor/gates/2026-08-17T2208-4a255f/`, `.qor/gates/2026-08-17T2146-7136d4/`)
- Neither has a top-level `target`. Both carry
  `proposed_changes[0].target = "docs/PROCESS_SHADOW_GENOME closure citation (single event)"`
  -- prose, not a path of any kind
- Neither contains an absolute path. `git grep` for the drive-letter prefix over
  all tracked files returns nothing

The absolute path exists **only in the issue's own body**, at line 12, inside a
fenced block quoting the sweep's console output. So the boundary finding is
against the issue text, and the premise that a writer emits absolute paths into
gate artifacts is unsupported. No writer needs changing.

The other half of GH #465 -- whether `.agent/staging/AUDIT_REPORT.md` versions
pair correctly with their artifacts -- is untouched by this and remains open on
its own terms.

### 8. No test pins the advisory contract

`tests/test_nightly_health_wiring.py` pins the cron trigger, the permission
ceiling, self-test-before-verdict ordering, the three lifecycle idioms, and the
Actions script-injection surface. It does not pin that a step documented as
reports-only cannot fail the job. That absence is why the contradiction shipped
and stayed.

### 9. The repository has already diagnosed this exact failure mode

`doctrine-publication-boundary.md:92-95`, written about this control's own
predecessor:

> Before Phase 208 it could express neither standing exception above, so it
> reported granted exceptions as violations, stayed permanently red, and was
> wired to no gate -- a control nobody can satisfy is a control nobody enforces.

The control has regressed into that state, with one difference that makes it
worse: it is now wired to a gate, and it takes the gate down with it.

## Blueprint Alignment

| Blueprint Claim | Actual Finding | Status |
|---|---|---|
| The scheduled boundary scan is read-only and reports for a human (`doctrine-publication-boundary.md:82`) | `github_surface.py:130` returns 1 on findings; the workflow step has no failure suppression | **DRIFT** |
| `nightly-health` keeps exactly one health issue in sync with the verdict (`nightly-health.yml:3-6`) | Lifecycle has not executed for five nights; a live `governance-index` failure is unreported | **DRIFT** |
| Both surfaces share one detector set and one marker idiom (`github_surface.py:8-10`) | True in code; the marker was applied to the tracked copy of a specification table and omitted from the surface copy | MATCH (code) / DRIFT (application) |
| GH #465: a writer emits a gate-artifact path, one absolute, into `audit.json` `target` | Artifacts are `remediate-iter1.json`, hold no such field, and contain no absolute path | **DRIFT** (issue premise) |
| Phase 268 improved the nightly job's state | Phase 268 explicitly disclaims this (`:233-236`) | MATCH |

## Recommendations

1. **P0 -- Fix GH #432 in code.** Make the boundary step non-fatal on findings
   while keeping exit 2 fatal, using the `set +e` + captured-`$?` idiom already
   present at `nightly-health.yml:57` and `:74`. Carry the finding count into
   the health-issue body so an advisory finding is *reported to a human* rather
   than merely not fatal -- that is the second half of what #432 names, and
   dropping it would leave the findings invisible in a passing job.
2. **P0 -- Write the missing test first.** A red test in
   `tests/test_nightly_health_wiring.py` asserting that the step documented as
   reports-only cannot fail the job. This is the property; the YAML edit is the
   implementation.
3. **P1 -- Clear Class A on the surface (5 findings).** Add
   `boundary-lint: ok=detector-specification` to the affected lines of the
   pull-request body that carries the detector's specification table, matching
   the tracked copy. No code change.
4. **P1 -- Operator pass for Class B and C (13 findings).** Twelve genuine
   outside-repository references and one drive-letter path require human
   anonymization; `doctrine-publication-boundary.md:82-83` reserves this to an
   operator and a lint must not do it unattended. This keeps GH #431 and the
   boundary half of GH #465 open until an operator acts.
5. **P2 -- Correct GH #465's premise in a comment.** The writer-side claim does
   not survive measurement; leaving it as filed sends the next reader after a
   defect that is not there. The audit-report pairing half stays open.
6. **P2 -- Note the empty issue bodies.** GH #432 and GH #431 both have a
   literal `@-` as their body: a `--body-file @-` invocation whose stdin never
   arrived. The substance of #431 survives in a comment; #432 has none at all.
   Worth a filing-path check before the next batch of issues.

## Updated Knowledge

For `qor/references/doctrine-publication-boundary.md`: the doctrine states the
scheduled scan is advisory but does not say what a consumer must do with its
exit code. The three-valued contract (0 clean / 1 findings / 2 could-not-scan)
is the load-bearing detail -- an advisory consumer must suppress 1 and must not
suppress 2 -- and it is currently documented nowhere. Recording it prevents the
next consumer from reaching for `continue-on-error` and silently disabling the
control.

For `docs/SHADOW_GENOME.md`: a control documented as advisory in prose and
implemented as enforcing in its exit code is a distinct failure shape from the
reverse. It fails loudly at the wrong boundary, so the noise reads as the
control working. Five nights of red were legible as "the boundary scan is
finding things", which was true, while the actual consequence -- the governance
watchdog was dead -- was nowhere in the signal.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
