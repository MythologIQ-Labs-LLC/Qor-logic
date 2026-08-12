# Research Brief

**Date**: 2026-08-12
**Analyst**: The Qor-logic Analyst
**Target**: The open issue set after Phase 222 -- #330 (grep-evidence truth check), #320 (skill-corpus drift enforcement), #286 (resource-aware admission and evidence reuse)
**Scope**: Which issue is the next phase, and what the first non-zero skill-corpus drift count actually measures

---

## Executive Summary

#330 is ripe, bounded, and mechanically feasible: the lint it fixes already extracts the citation kind whose truth is checkable, and the defect it closes was demonstrated against this project's own plan four hours ago. It is the recommendation.

The more consequential finding is about #320. Its V1 disclosure has now produced its first non-zero drift count -- 26 at Phase 222, after five consecutive zeros -- which reads as the data its entry criteria were waiting for. It is not. **All 26 drifted skills are byte-identical to a different distribution's shipped copies; zero are genuinely edited.** Enforcement built on this signal today would fail closed on every seal for a packaging reason with no governance content.

#286 is unblocked on the constraint that blocked it (this file now has 2,783 B where it had 24) but is the largest of the three and depends on contracts this repository does not hold. It follows #330, not precedes it.

---

## Findings

### Category 1: #320 -- the first non-zero drift count measures the wrong thing

#### The signal, as recorded

Every seal since Phase 217 carries a `**Skill Corpus**:` line. Six now exist:

| phase | drift_count |
|---|---|
| 217 | 0 |
| 218 | 0 |
| 219 | 0 |
| 220 | 0 |
| 221 | 0 |
| 222 | **26** |

Read at face value, Phase 222 is the first observation the issue's entry criteria ask for.

#### What the 26 actually are

Attribution, computed by comparing each installed `SKILL.md` against the `RECORD` digests of both distributions present in the active environment:

```
drifted skills:                     26
  installed copy == PLUS package:   26
  installed copy == LOGIC package:   0
  neither (genuinely edited):        0
```

Worked example for the seal skill itself, all four digests in one view:

```
installed  ~/.claude/skills sha: 3aL6cu0kHGB5djv1JBcFuDAzqFbmxttMSNVL3OdMNOc
plus  package RECORD sha       : 3aL6cu0kHGB5djv1JBcFuDAzqFbmxttMSNVL3OdMNOc   <- match
logic package RECORD sha       : umOSzlrGLvIyxSpUfg8_z75XTz0Gn4afACsuEoAgo5g
repo source sha                : umOSzlrGLvIyxSpUfg8_z75XTz0Gn4afACsuEoAgo5g   <- match
```

The installed corpus is not a drifted copy of this project's skills. It is a
different product's corpus occupying the same install target, because both
distributions own the top-level `qor/` package and the host skills directory.
Root cause and remediation are tracked upstream; this repository cannot fix it.

#### Why this matters to #320 specifically

The issue's second open question is "what threshold means drifted." The data
says the prior question is unanswered: **drifted how?** Three conditions produce
a non-zero count and want different responses:

| condition | what it means | correct response |
|---|---|---|
| corpus edited | someone changed an installed skill | the case #320 exists for; investigate |
| corpus replaced | another distribution owns the path | packaging fix; blocking the seal is wrong |
| corpus absent | no install to compare | already handled -- `digest()` returns `None` |

V1 collapses the first two into one integer. An enforcement built on that
integer would have failed closed on Phase 222's seal, on a machine where no
skill had been edited at all.

The issue anticipated something adjacent -- "the drift most worth catching is
the drift that removes the catcher" -- but the observed failure is the inverse:
a count that fires when nothing governance-relevant happened. Both are reasons
the V1-to-V2 step needs the attribution, not just more samples.

**Status: still correctly deferred, and its acceptance criteria now have a
concrete amendment to absorb before it opens.**

### Category 2: #330 -- ripe, and the fix is already half-built

Filed this session after the Phase 222 audit VETOed a plan whose grep-evidence
was typed rather than executed (ledger #565). The lint that exists to prevent
exactly that returned exit 0 on the offending plan.

The mechanism is confirmed present:

```
qor/scripts/plan_grep_lint.py:97   _EVIDENCE_RE   = re.compile(r"grep\b.*->")
qor/scripts/plan_grep_lint.py:99   _GIT_SHOW_RE   = re.compile(r"git show\s+\S+:\S+")
qor/scripts/plan_grep_lint.py:100  _MIGRATION_RE  = re.compile(r"\b\d{8,}[_-][\w-]+\.sql\b")
qor/scripts/plan_grep_lint.py:101  _FILE_LINE_RE  = re.compile(r"\b[\w./-]+\.(?:py|ts|tsx|sql|rs|go|js):\d+\b")
```

`_FILE_LINE_RE` already parses `path.py:NN` out of a Locked-Decision block --
the citation kind whose truth is mechanically checkable. `_EVIDENCE_RE` already
locates the evidence statement. What is missing is the comparison between them:
read the cited path at the cited line, compare to the quoted text.

The scope is one module, one new function, and a fixture pair.

The counterfactual must be **purpose-built**, not recovered. Only the corrected
plan was ever committed:

```
$ git log --oneline --all -- docs/plan-qor-phase222-seal-ladder-as-data.md
85a9077 seal: phase 222 - seal gate ladder as data (v0.145.0)

$ git show 85a9077:docs/plan-qor-phase222-seal-ladder-as-data.md | grep -c "\-> 39:"
0
```

The iteration-1 text existed only in the working tree between authoring and the
audit that rejected it. A fixture reproducing the shape -- an evidence statement
citing a line whose content does not match -- is a few lines to write and does
not depend on history that was never recorded.

**Status: ripe. No gating entry criteria. Recommended next phase.**

### Category 3: #286 -- unblocked, but not next

Phase 222 freed the constraint that blocked it. `qor-substantiate/SKILL.md` now
holds 2,783 B under the headroom bound where it held 24; the plan sized #286's
need at roughly 1,600 B for this file.

Two reasons it should not be next:

1. **It is the largest of the three by an order of magnitude.** It declares two
   contract layers, twelve audit verification clauses, and eight substantiation
   requirements, against Phase 216's measured cost of one layer at +1,084 B in
   `qor-audit` and +807 B in `qor-substantiate`.

   ```
   $ python -c "from pathlib import Path; p=Path('qor/skills/governance/qor-audit/SKILL.md'); s=p.stat().st_size; print(s, 39*1024-s)"
   39473 463
   ```

   `qor-audit` holds **463 B** of slack against the ~2,200 B two layers of audit
   prose would need -- less than a quarter of one layer. **The audit-side
   constraint Phase 222 did not address is still binding, and is tighter than
   the seal-side one ever was at the point it forced this work.**
2. **Its dependencies are contracts this repository does not hold**, consumed by
   version reference only. #330 is entirely internal and can ship without
   coordinating anything.

**Status: ripe on entry criteria, second in sequence. Note that a phase for
#286 will need to free headroom in `qor-audit` the way Phase 222 did for
`qor-substantiate`, and the ladder-as-data pattern is directly transferable to
its pre-audit lint ladder.**

---

## Blueprint Alignment

| Claim | Actual Finding | Status |
|---|---|---|
| #320: V1 disclosure will eventually produce drift data | It produced a count; the count has no governance content | **DRIFT** |
| #320: the open question is what threshold means "drifted" | The prior question, "drifted how", is unanswered | **DRIFT** |
| #330: the `file:line` citation kind is mechanically checkable | `_FILE_LINE_RE` at `plan_grep_lint.py:101` already extracts it | MATCH |
| #330: `plan_grep_lint` checks presence, not truth | `_EVIDENCE_RE` at `:97` matches the statement's shape only | MATCH |
| #286: blocked on `qor-substantiate` headroom | Resolved -- 2,783 B available | MATCH |
| #286: `qor-audit` also needs ~2,200 B | 39,473 B, **463 B** of slack -- short by a factor of five | **DRIFT** |
| Phase 222 seal recorded `drift_count 26` honestly | Confirmed; disclosed rather than resolved | MATCH |

---

## Recommendations

1. **P0 -- Take #330 as the next phase.** Bounded, internal, no gating criteria,
   and it closes a control that demonstrably failed against this project's own
   plan this session. The counterfactual fixture already exists in git history.
2. **P0 -- Amend #320 before it is ever opened.** Add the attribution
   requirement to its acceptance criteria: a drift count must distinguish
   *corpus edited* from *corpus replaced by another distribution*, because the
   only non-zero count observed to date is entirely the latter. Post the Phase
   222 measurement to the issue so the next reader does not mistake 26 for the
   signal the criteria were waiting for.
3. **P1 -- Sequence #286 after #330, and scope it to include `qor-audit`
   headroom.** The `qor-substantiate` constraint is gone; the `qor-audit` one is
   not. The ladder-as-data pattern transfers directly to its Step 0.6 pre-audit
   lint ladder, which is the same shape: a list of module invocations with a
   uniform `|| true` posture.
4. **P2 -- Do not treat the installed-corpus drift as a repository defect.**
   It is a packaging collision tracked upstream. Reinstalling does not clear it,
   and a seal-time reaction to it would be a reaction to the wrong thing.

---

## Updated Knowledge

No Shadow Genome entry proposed. The #320 finding is not a failure that occurred
-- it is a measurement that would have caused one had enforcement shipped on
schedule, caught by attributing a count before trusting it. Cataloguing a
pattern that did not fire spends the corpus signal it exists to preserve, which
is the same judgment recorded for the option-A defect at ledger #564.

The durable fact -- that a skill-corpus drift count must be attributed before it
is interpreted -- belongs on #320 itself, where the V2 decision will be made,
and is posted there rather than added to a doctrine no one will read at that
moment.

---

## Corrections of record

**Two**, both in this brief, both the pattern this brief is about.

**1. `qor-audit` size.** A draft stated 38,722 B with 1,214 B of slack. Measured:
39,473 B and 463 B. The draft figure was a half-remembered intermediate from
Phase 222's own compression pass, not a reading. The correction strengthens
Recommendation 3: the audit-side headroom is short by a factor of five, not by a
third.

**2. The #330 counterfactual is not in git history.** A draft of Category 2 said
the Phase 222 iteration-1 plan text, carrying line 39 against an actual line 42,
was "preserved in git history" as a ready-made failing fixture. It is not. Only
the corrected plan was ever committed (`git log --all` on that path returns the
single seal commit; grepping it for `-> 39:` returns 0). The iteration-1 text
existed only in the working tree between authoring and the audit that rejected
it. The same claim was published to GH #330 and is corrected there.

Both were caught by running the check rather than trusting the recollection.
The second is the more instructive: it was written **into the brief that argues
for mechanical citation verification**, one section away from a correction notice
about the first. Recalled facts read as observed facts from the inside, which is
the entire reason #330 should not be satisfied by a human promising to be
careful.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
