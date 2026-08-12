# Research Brief

**Date**: 2026-08-11
**Analyst**: The Qor-logic Analyst
**Target**: The three open GitHub issues -- #327 (seal-skill size remedy), #320 (skill-corpus drift enforcement), #286 (resource-aware admission and evidence reuse)
**Scope**: Which issues are ripe against their own stated entry criteria, and what the measured repository state says about the options each issue proposes

---

## Executive Summary

Three issues are open. Two carry self-imposed entry criteria written specifically to
stop them being opened for the wrong reason. Measured against those criteria: #320 is
not ripe (five seals of drift data against a precedent that required thirty-six
phases), and #286 is ripe by its own terms but cannot physically ship, because it
requires roughly 2,200 bytes in `qor-audit` and 1,600 bytes in `qor-substantiate`,
which currently hold 463 and 24 bytes of slack respectively.

That makes #286 blocked behind #327, and being blocked behind it is precisely #327's
entry criterion. The ordering is therefore forced rather than chosen.

One correction to #327 itself: **option A does not work as written.** Composition
cannot reduce the artifact the size lint measures, because that lint and the install
drift check both walk `qor/skills/**/SKILL.md` -- the composed output is the governed
file. This is a new finding; the issue's options analysis does not account for it.

---

## Findings

### Category 1: Issue ripeness against stated entry criteria

#### #320 -- skill-corpus drift enforcement: NOT RIPE

Entry criterion, quoted from the issue: "Do not open this until V1 has produced drift
counts across a meaningful number of seals. The precedent is `merge_velocity_check`,
which shipped WARN at Phase 93 and reached fail-closed at Phase 129 on the strength of
observed data."

V1 shipped at Phase 217. Every seal since records a `**Skill Corpus**:` line:

| ledger line | phase | digest | drift_count |
|---|---|---|---|
| `docs/META_LEDGER.md:16491` | 217 | `3d8a50aa83de060d` | 0 |
| `docs/META_LEDGER.md:16650` | 218 | `b8656107dcced368` | 0 |
| `docs/META_LEDGER.md:16750` | 219 | `427fab4737524588` | 0 |
| `docs/META_LEDGER.md:16898` | 220 | `35d140b442e0e0bf` | 0 |
| `docs/META_LEDGER.md:17051` | 221 | `901e90338ab8ee1d` | 0 |

Five seals. Zero observed drift. The cited precedent spanned thirty-six phases before
the data justified fail-closed. Five samples of a constant cannot answer either of the
two questions the issue defers -- what threshold means "drifted", and whether a
`verified` corpus should be ledger-distinguishable -- because no seal has yet produced
a non-zero count to characterise.

**Status: correctly deferred. No action.**

#### #286 -- resource-aware admission and evidence reuse: RIPE, BLOCKED

No gating entry criteria. Its stated predecessor, #285 (execution-continuity
semantics), is CLOSED as of 2026-08-11T06:36:53Z and shipped at Phase 216. No merged
or open PR addresses #286 (Step 2.5 pre-check: `gh pr list --search "286"` returns only
PR #129, a Phase 105 dependency-admission phase, unrelated).

The Phase 216 delivery is the template #286 would follow, and it exists in full:

- `qor/references/doctrine-execution-continuity.md` (5,992 B) -- gate behavior, with the
  upstream schema referenced by version only
- `qor/scripts/continuity_contract.py:27` -- `QOR_OWNED_KEYS`, a closed frozenset, so
  non-duplication is checkable from inside rather than by enumerating names this
  repository does not hold
- `qor/scripts/continuity_gate.py` (118 lines) -- the ordered fail-closed ladder
- `qor/scripts/plan_continuity_lint.py` (116 lines) -- plan-declaration lint
- `qor/gates/schema/plan.schema.json` -- one `execution_continuity` block among 22
  top-level properties, `additionalProperties: false`
- `qor/skills/governance/qor-audit/SKILL.md:630` -- the Execution-Continuity Pass
- `qor/skills/governance/qor-substantiate/SKILL.md:316` -- Step 4.6.12, the receipt gate

**Status: ripe on its own terms, blocked on skill headroom. See Category 2.**

#### #327 -- seal-skill size remedy: RIPE VIA CRITERION (b)

Entry criteria, quoted: open it when "a phase genuinely cannot fit a required gate
after a full disclosure pass, or someone is prepared to spend a phase on option A or B
as the deliverable rather than as a means to something else."

The second criterion is an operator choice and is available now. The first is
satisfied prospectively by #286, which is the next ungated work and cannot fit. The
issue's own warning -- "Do not open this to satisfy a size breach in the moment. That
is how the wrong option gets built" -- is honored by opening it *before* #286 rather
than during it.

**Status: ripe. This is the recommended next phase.**

### Category 2: The measured collision between #286 and the size ceiling

`skill_size_budget_lint.py:23-24` sets `WARN_BYTES = 25 * 1024` and
`EXCEEDED_BYTES = 40 * 1024`. `HEADROOM_BYTES = 39 * 1024` (39,936) is the tighter
test-enforced bound, canonical in `tests/test_substantiate_staging_gates.py` and
asserted single-source by `tests/test_headroom_constant_single_source.py:29`.

Current sizes of the two skills #286 must modify:

| skill | bytes | slack to 39,936 |
|---|---|---|
| `qor/skills/governance/qor-substantiate/SKILL.md` | 39,912 | **24** |
| `qor/skills/governance/qor-audit/SKILL.md` | 39,473 | **463** |

Phase 216 is the empirical cost of adding **one** contract layer of this exact shape.
Measured from git object sizes across the seal commits:

| skill | before (Phase 215, `90b6c9e`) | after (Phase 216, `93a9405`) | delta |
|---|---|---|---|
| `qor-audit/SKILL.md` | 38,389 | 39,473 | **+1,084** |
| `qor-substantiate/SKILL.md` | 38,816 | 39,623 | **+807** |

#286 consumes **two** further contract layers (execution admission, and validation
budget / evidence reuse), and enumerates twelve audit verification clauses and eight
substantiation requirements -- strictly more surface than #285's single layer. A
conservative projection of two Phase-216-sized layers is ~2,168 B in `qor-audit`
against 463 B of slack, and ~1,614 B in `qor-substantiate` against 24 B.

Both skills are already at their compressed form. Step 4.6.12 is six lines of prose
that delegate all rationale to `references/seal-gate-ladder.md`
(`qor-substantiate/SKILL.md:316-325`); the audit pass does the same to
`qor/references/doctrine-execution-continuity.md` (`qor-audit/SKILL.md:649`). There is
no second disclosure pass left to run on these two blocks.

**#286 cannot ship before a structural remedy exists. The dependency is arithmetic, not
judgment.**

### Category 3: DRIFT -- #327's option A does not work as written

Option A proposes: "Skill bodies gain includes; the ladder becomes a composed fragment;
guardrail tests read the composed artifact rather than the single file."

Two controls in this repository walk `qor/skills/**/SKILL.md` directly:

1. `qor/scripts/skill_size_budget_lint.py:42` -- `for skill in sorted(skills_root.rglob("SKILL.md"))`,
   measuring `skill.stat().st_size`
2. `qor/scripts/install_drift_check.py:24` -- `sorted((repo_root / "qor" / "skills").rglob("SKILL.md"))`,
   byte-identical SHA256 against the operator's installed counterpart

The consequence is a closed loop. Whatever composition produces must land as a single
`SKILL.md` under `qor/skills/`, because that is the file the operator installs and the
file `install_drift_check` compares. If the composed output is the checked-in file,
`skill_size_budget_lint` measures the composed output and its size is unchanged --
composition has bought nothing. If instead the fragment stays outside the checked-in
`SKILL.md`, then the harness never loads it at execution time, and a gate in an unloaded
fragment is unreachable.

That second branch is not hypothetical. Phase 221 (ledger entry #563) found exactly it:
Step 4.6.12 had drifted to 92 percent of the file, after the templates, and "an operator
executing the ladder in order went 4.6.10, 4.6.13, 4.6.14, 4.7 and never saw it." A
fail-closed gate that no reader reaches provides no coverage. Option A as written
converts an ordering hazard into a structural one.

`qor/scripts/dist_compile.py` confirms no composition mechanism exists to build on: it
copies whole trees per variant, and its claude variant "is an identity copy of source
(it is the install mirror that install_drift_check compares against qor/skills)"
(`dist_compile.py:3-5`). Adding includes there would break that identity property for
every operator simultaneously.

**Option B survives this analysis and option A does not.** A sub-skill is a load unit
the harness actually invokes, so reachability is preserved; it carries its own 40 KB
budget; and `install_drift_check` sees it as one more source skill with an installed
counterpart, which is the case it already handles. Its stated costs -- a two-hop
ceremony, and a delegation-table row for a skill that is not a lifecycle phase -- are
real but are contract-shaped rather than mechanism-shaped.

Option C (accept the ceiling, route new gates elsewhere) remains viable and cheapest,
but it does not unblock #286: #286's audit and substantiation clauses are seal-ceremony
clauses by nature, and routing them to CI would reproduce the enforcement-location
problem #320 already documents.

---

## Blueprint Alignment

| Claim | Actual Finding | Status |
|---|---|---|
| #320: V1 has not yet produced meaningful drift data | 5 seals, all `drift_count 0`, vs a 36-phase precedent | MATCH |
| #286: #285 remains authoritative for continuity semantics | #285 CLOSED, Phase 216, all six artifacts present | MATCH |
| #286: Qor-logic must reference and not duplicate upstream schemas | `continuity_contract.QOR_OWNED_KEYS` closed frozenset; `additionalProperties: false` | MATCH |
| #327: 36 of 54 asserted strings live inside the gate ladder | Not re-counted this pass; accepted from entry #559 | UNVERIFIED |
| #327: `dist_compile` has no include support | Confirmed: whole-tree copy, claude variant is an identity copy | MATCH |
| #327 option A: guardrail tests can read a composed artifact instead of the single file | The size lint and drift check both walk `qor/skills/**/SKILL.md`; the composed output *is* the governed file | **DRIFT** |
| #327: the next phase needs a structural remedy rather than a trim | Confirmed and quantified: 24 B slack against a ~1,600 B requirement | MATCH |

---

## Recommendations

1. **P0 -- Take #327 as the next phase, with option B as the deliverable.** Entry
   criterion (b) is met by choosing it deliberately, which is exactly the discipline the
   issue asks for. Before planning, post the Category 3 finding to #327 so option A is
   retired on evidence rather than silently skipped.
2. **P0 -- Do not attempt #286 first.** The 24-byte slack makes it a guaranteed
   mid-phase size breach, which is the failure mode #327's entry criteria exist to
   prevent, and which has now occurred in Phases 217, 219, and 220.
3. **P1 -- Leave #320 closed to work.** Revisit when a non-zero `drift_count` appears in
   a seal, or after roughly twenty further seals produce a characterised baseline.
   Consider adding the "seals observed / non-zero counts" tally to the issue as data
   accumulates, so ripeness is checkable rather than remembered.
4. **P1 -- When #286 is planned, size it as two Phase-216-shaped layers, not one.**
   Budget ~2,200 B of audit prose and ~1,600 B of seal prose, and confirm the remedy
   from recommendation 1 has actually freed that room before the plan is audited.
5. **P2 -- Re-verify the 36-of-54 assertion count from entry #559 during #327 planning.**
   It is the load-bearing constraint on any extraction and was accepted here rather than
   re-measured.

---

## Correction of record

The Category 3 citation above originally read
`qor/scripts/skill_size_budget_lint.py:39`. The `rglob("SKILL.md")` construct is
at line 42; line 39 holds `if not skills_root.is_dir():`. The number was read off
an unnumbered `sed -n '25,50p'` window and written as though produced by
`grep -n`. Corrected here from executed output:

```
$ grep -n 'rglob("SKILL.md")' qor/scripts/skill_size_budget_lint.py
42:    for skill in sorted(skills_root.rglob("SKILL.md")):
```

Caught by the Phase 222 audit (ledger #565, VETO). The finding does not change
Category 3's conclusion -- the construct exists and the loop it closes is real --
but the citation was not reproducible as published, and the same wrong number
reached a comment on GH #327, corrected there as well. Ledger entry #564 is
content-hash-bound to the uncorrected text and is not amended; this section is
the correction of record. Shadow Genome: candidate `SG-TranscribedEvidence-A`.

## Updated Knowledge

Added to `qor/references/doctrine-token-efficiency.md`: a section recording that
progressive disclosure is bounded by the two controls that walk
`qor/skills/**/SKILL.md`, so relocating prose out of a `SKILL.md` reduces the measured
artifact only when the destination is a file the harness still loads at execution time.
Moving a gate to a location no reader reaches is a size reduction that costs coverage,
which Phase 221 observed in the live corpus.

No Shadow Genome entry is proposed. The option-A defect has not occurred; it was caught
in analysis before a phase committed to it, and cataloguing a pattern that never fired
would weaken the corpus's signal.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
