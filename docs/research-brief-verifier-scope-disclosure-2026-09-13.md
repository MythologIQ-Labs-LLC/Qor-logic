# Research Brief

**Date**: 2026-09-13
**Analyst**: The Qor-logic Analyst
**Target**: the six issues labelled `reliability` -- whether they are one defect class, and what closes them
**Scope**: GH #463, #487, #486, #476, #461, #455; the scope-disclosure idiom shipped in Phase 219

---

## Executive Summary

**The cluster is three, not six.** The labelling pass proposed that all six
`reliability` issues share one root cause and that one phase closes them.
Measured, that is wrong: three are instances of a single property and three are
unrelated to it and to each other. The correction is the most useful finding
here, because acting on the six-as-one framing would have produced a phase whose
deliverable could not cover half its scope.

The three that do share a property -- **#487, #461, #476** -- are all verifiers
that report success over a scope that is empty, author-supplied, or partial,
without the result saying so.

**The countermeasure already exists in this repository and was never
generalised.** Phase 219 (GH #309 gap 2) established that a green result must
carry its own scope, implemented it on `publication_boundary_lint`, wrote it into
doctrine, and gave it a dedicated test file. One verifier has it. The three above
do not.

## Findings

### 1. The six do not share a root cause

| issue | what is actually wrong | class |
|---|---|---|
| **#487** | the citation truth-checker's block regex matches no plan written to the house convention, so it examines 0 citations and exits 0 | scope |
| **#461** | the checked set is supplied by the audited party, and the gate returns clean on an empty set | scope |
| **#476** | the sync gate compares `SKILL.md` only and is silent about the rest | scope |
| #463 | gate *declarations* are prose; nothing records that any check executed | execution evidence |
| #486 | the override path raises before it can log | ordinary defect |
| #455 | readers whose callers cannot handle the failures they enumerate | error handling |

The first three are one property. The last three are three properties, and one of
them (#463) is a design boundary another phase deliberately left open.

### 2. The three, measured

**#487** -- `plan_grep_lint` reports `0 citation(s) truth-checked` against every
recent plan and exits 0. Cause is `plan_evidence.py:32`: `_LD_HEADING_RE` matches
`## Locked Decisions` but not `### LD-<n>`, and the block ends at the next
heading of any level, so every Locked Decision body falls outside the scanned
region.

**#461** -- `ledger_commitment.stale_commitments(repo_root, touched)` checks what
`touched` names, and `touched` is `files_touched` from the implement artifact,
written by whoever ran the phase. Measured now: **105 of 204** implement
artifacts name a plan or brief at all, so roughly half of all sealed phases ran
this gate over source and test files only. Called with an empty list it returns
`[]` -- a clean pass over nothing.

**#476** -- `tests/test_install_sync_with_source.py` globs `SKILL.md` only.
Measured: **32 `SKILL.md` against 26 `references/*.md`**, so the gate covers
**55 percent** of the installed markdown surface and reports no shortfall. The
uncovered half is the progressive-disclosure surface this repository's own
doctrine directs new prose into, which makes it the material most likely to be
edited and least likely to be checked.

### 3. The property, and the precedent that already implements it

Phase 219 shipped exactly this for the boundary lint:

> `grep -n 'scope: str' qor/scripts/publication_boundary_lint.py` -> `147:    scope: str`

`BoundaryResult` carries the detector scope that produced its findings, the CLI
prints it -- `publication_boundary_lint: 0 finding(s) [scope: structural+identity]`
-- the doctrine states the rule at line 114 ("a bare 'clean' would overstate"),
and `tests/test_boundary_scope_disclosure.py` pins it as a property rather than a
formatting choice.

Its own docstring states the general form:

> "an unqualified '0 findings' from CI and from a local run mean different things
> and currently look identical. The scope travels with the result."

That is the property the three issues need, stated two years of phases ago, for
one module. Nothing generalised it, and nothing prevents the next verifier from
shipping without it.

### 4. What generalising it requires, and what it does not

It does **not** require making the three verifiers check more. #461's scope is
author-declared by design, and widening it is a separate argument; #476's
`references/` coverage is a real extension but is not what makes the gate
misleading. What makes all three misleading is that a narrow or empty scope is
indistinguishable from a thorough one in the result.

So the deliverable is disclosure plus a floor: a verifier reports the size of
what it examined, and an empty examination does not read as a pass. #487 already
prints its count and still exits 0, which shows disclosure alone is insufficient
-- the floor is the second half.

### 5. #486 is a one-line fix and should not wait for this

`merge_velocity_check.py:251` calls `append_event` with neither `attribution=`
nor `log_path=`, so the documented escape from a fail-closed seal gate raises
`ValueError`. Unrelated to scope. It is small enough to ride along with any phase
touching the ladder, and it should, because a seal gate with no working escape is
worse than the throughput it guards.

### 6. #463 and #455 stay where they are

#463 is the execution-evidence gap already briefed on 2026-09-11: Phase 242 built
the evaluator half and assigned production to an execution host, deliberately. It
is an operator decision about scope, not a defect to close inside a scope phase.

#455 asks for a checkable property about exception handling in readers. It is a
genuine reliability issue and shares nothing mechanical with scope disclosure.

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| The six `reliability` issues share one root cause | Three do; three do not | **DRIFT -- corrects this session's own labelling** |
| Scope disclosure is a `publication_boundary_lint` implementation detail | Phase 219 established it as a property, with doctrine and a dedicated test | **DRIFT** |
| A verifier that prints its count is adequately disclosed | #487 prints `0` and exits 0 | **DRIFT** |
| #461's gate is broken | It works; its scope is supplied by the party it audits | MATCH (issue is accurate) |
| #476 covers the installed skill surface | 32 of 58 markdown files, 55 percent | **DRIFT** |

## Recommendations

1. **P0 -- scope the phase to three, not six.** #487, #461, #476. Closing six in
   one phase was this session's own framing and the measurement refutes it.
2. **P0 -- generalise Phase 219's property rather than inventing one.** A result
   type that carries the size and kind of what was examined, and a floor that
   makes an empty examination fail rather than pass.
3. **P1 -- carry #486 along.** One line plus a test that drives `--override` to
   completion; the current coverage cannot distinguish "the flag parses" from
   "the flag works".
4. **P2 -- leave #463 and #455.** Each is a distinct property and #463 is an
   operator scope decision, not an implementation gap.
5. **P2 -- the `reliability` label is still correct for all six.** They share a
   symptom -- a control that reports more assurance than it delivers -- without
   sharing a mechanism. The label should group triage, not scope a phase.

## Updated Knowledge

For `docs/SHADOW_GENOME.md`: a label is a symptom, not a cause, and this session
converted one into a phase scope within a single message. Six issues carrying the
same label produced an appealing story -- "one property, six instances, net minus
six" -- that survived until the first measurement and then decomposed into three
and three. The countermeasure is that a proposed scope is a claim like any other
and gets checked before it is offered, not after it is accepted.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
