# Research Brief

**Date**: 2026-09-04T21:10:00Z
**Analyst**: The Qor-logic Analyst
**Target**: `qor.scripts.ledger_hash.verify_post_anchor` and its divergence from `verify()` -- GH #425, #430, #443
**Scope**: contract fidelity, consumer-tolerance feasibility, phase sizing
**Session**: 2026-09-04T2057-9575a7
**Base**: `main` at d07daac3 (Phase 262 / v0.169.1)

---

## Executive Summary

The three open issues against `verify_post_anchor` are not three feature requests. They are three respects in which the function fails to implement a contract this repository already ships in writing, at `qor/references/doctrine-governance-enforcement.md:332-347`. Measured against that section's four contract bullets plus its mode definitions, `verify_post_anchor` honors two fully, one partially, and one not at all, and additionally omits the per-link chain check that the raw-mode definition at line 336 names explicitly. The omission is reachable: a fixture whose entries are each internally self-consistent but wrongly linked returns exit 0 from `verify_post_anchor` and exit 1 from `verify`, and `verify_post_anchor` is the mode both the seal-time gate and the skill-entry preflight consume.

The fix is feasible here and constrained elsewhere. This repository's live 737-entry ledger carries zero linkage breaks, so adding the check costs it nothing; but a re-anchored consumer ledger of the shape GH #55 describes carries a linkage break by construction, at the re-anchor point itself, so the check must inherit pre-anchor tolerance rather than run unconditionally. That single measurement rules out the naive fix.

## Findings

### F-1. The contract is written, and the implementation diverges from it

`doctrine-governance-enforcement.md:332` opens section 14, "Post-anchor ledger invariant (Phase 66)". It defines raw mode at line 336 as: "every entry verifies under canonical or Session Seal markup, every chain link math-checks against its recorded predecessor, every hash passes placeholder-pattern detection." It defines post-anchor mode at line 338 as the same surface partitioned: "pre-boundary failures are reported as `DISCLOSED_PRE_ANCHOR` and tolerated, post-boundary failures remain hard errors."

The partition language presupposes that the checks are the same and only their consequence differs by side of the boundary. Audited bullet by bullet against `ledger_hash.py:615-725`:

| Contract element | Source | Implemented in `verify_post_anchor` |
|---|---|---|
| Consumer may release at exit 0 while raw exits non-zero | line 342 | YES |
| Pre-anchor disclosure printed, not concealed | line 343 | YES |
| `TAINTED` propagates downstream from every FAIL | line 344 | **NO** |
| Placeholder hashes flagged with the offending field named | line 345 | **PARTIAL** |
| Every chain link math-checks against its recorded predecessor | line 336 | **NO** |

- `TAINTED`: an `awk` slice of lines 615-725 piped to `grep -c TAINTED` returns `0`. The same count over the whole file returns `5`, all inside `verify()`. This is GH #430's root, and line 344 is explicit that math consistency alone is not trust.
- Placeholder field naming: `ledger_hash.py:671` calls `_find_placeholder_field(content_val, previous_val, recorded)` in a bare truth test and discards the returned field name; the entry is classified `fail` and later printed as the generic `FAIL Entry #N: post-anchor verification failure`. `verify()` binds the same call's result at `ledger_hash.py:345` and reports the field. The check runs; the diagnostic the contract promises does not.
- Chain-link math: see F-2.

### F-2. verify_post_anchor runs no linkage pass at all

The linkage pass is `_sequence_breaks` (`ledger_hash.py:368`), reached through `_report_sequence` (`ledger_hash.py:440`, which calls it at `ledger_hash.py:461`). Repository-wide, `_report_sequence` has exactly one call site: `ledger_hash.py:594`.

Function spans were resolved by AST rather than by reading, so the boundary numbers are not eyeballed:

```
line 594 is inside: verify() spanning 473-595
verify_post_anchor() spans 615-725
```

An `awk` slice of 615-725 piped to `grep -c` for either linkage symbol returns `0`.

The classification loop at `ledger_hash.py:650-679` is per-entry only: it recomputes `chain_hash(content_val, previous_val)` and compares to the recorded chain. An entry that chains from the wrong predecessor still satisfies its own arithmetic and classifies `ok`.

### F-3. The consequence is reachable, and demonstrated

Two four-entry fixtures, identical except for linkage. In the forked one, `#3` records `#2`'s content hash as its `previous_hash` and `#4` records `#2`'s chain hash, skipping `#3`; each entry's own chain math is recomputed so it stays self-consistent. Run twice consecutively for determinism, identical both times:

```
run 1 ledger_good     verify=0 post_anchor=0 breaks=0
run 1 ledger_forked   verify=1 post_anchor=0 breaks=2
run 2 ledger_good     verify=0 post_anchor=0 breaks=0
run 2 ledger_forked   verify=1 post_anchor=0 breaks=2
```

`verify` names both breaks on stderr. `verify_post_anchor` prints all four entries `OK` and `post-anchor clean (boundary=#4)`.

The mode is not a diagnostic backwater. It is what two gates call:

- `qor/reliability/seal_entry_check.py:149` -- `/qor-substantiate` Step 7.7, the post-seal ledger gate.
- `qor/scripts/governance_health.py:149` -- the skill-entry preflight every governance-reading skill runs.

Both were pointed there deliberately, by GH #88 and GH #199 respectively. Neither change enumerated what else was being given up.

### F-4. Scope of the claim, stated precisely

A fork of exactly this shape occurred in this repository's working tree during the Phase 258-262 session and persisted across eight ledger entries before being repaired at entries #737 and #738. It is not evidence of an observed gate miss: no seal ran between the break and the repair, so `seal_entry_check` was never invoked on the forked file. The break was found by `verify` and fixed. F-3's fixture establishes what the gate would do; it does not report what it did.

A hypothesis raised earlier in this session -- that GH #425's one-entry duplicate window explained that fork -- was refuted by measurement. The fork used distinct entry numbers, so `_duplicate_entry_numbers` returns nothing for it; called against the live ledger it returns an empty list. It is #443's class, not #425's.

### F-5. Feasibility here: free

Measured against `docs/META_LEDGER.md` at d07daac3:

```
entries          : 737
reconciled set   : 0
breaks (no tol)  : 0
breaks (verify)  : 0
duplicate numbers: []
```

`reconciled` is the intersection of `_attested_reconciled(entries)` and `_duplicate_previous_hash_members(entries)`, the tolerance set `verify()` itself uses at `ledger_hash.py:594`. Adding a linkage pass to `verify_post_anchor` would not change this repository's own result.

### F-6. Feasibility elsewhere: the constraint that rules out the naive fix

GH #55, the originating issue, describes a consumer ledger with a documented pre-anchor edit cluster at entries #156, #158, #159, #161, #162, #164, #165, #167, #168, #169 and a clean surface through #250. Hand-editing an entry body changes its content hash, hence its chain hash, hence the value its successor recorded as `previous_hash`. A re-anchored ledger should therefore be expected to carry at least one linkage break at the re-anchor seam.

Confirmed by constructing an eight-entry fixture of that shape -- entries #3 and #4 edited in place, #5 re-anchoring on the pre-edit chain value:

```
re-anchored consumer fixture: entries = 8
linkage breaks reported      = 1
    BREAK Entry #5: previous_hash 949ecc0aa9adfd6a was not produced by the
    preceding entry (chain dd4dd66066be1f7d); an entry may have been removed
verify_post_anchor rc        = 0
boundary line                = post-anchor clean (boundary=#8)
```

The break lands at #5, below the auto-detected boundary of #8. So the proposed rule -- linkage breaks at or below the boundary are `DISCLOSED_PRE_ANCHOR`, above it are errors -- preserves the GH #55 contract for this shape, while an unconditional `_report_sequence` call would fail every consumer the mode exists to serve.

### F-7. The boundary is max(ok), which makes one failure path dead

`ledger_hash.py:681-684`:

```
    # Auto-detect boundary: highest entry id that classified ok.
    if boundary_entry is None:
        ok_entries = [n for (n, status) in classifications if status == "ok"]
        boundary_entry = max(ok_entries) if ok_entries else 0
```

Because the boundary is the maximum `ok` entry, the reporting loop's error branch at `ledger_hash.py:690` can only fire for an entry numbered above every `ok` entry. Whenever the newest entry classifies `ok`, the post-boundary band is empty and no entry can fail there. GH #425's one-entry duplicate window and GH #430's "empty band is indistinguishable from a clean band" are two consequences of that one line.

### F-8. Existing coverage, and a test that pins the defect

- `tests/test_post_anchor_verify.py`: a count of `def test` lines returns **11**. A count of lines mentioning sequence, linkage, or BREAK returns **0**. No test covers linkage in post-anchor mode, so F-2 is uncovered rather than deliberately traded away.
- `tests/test_ledger_hash_duplicate_entry.py`: 5 tests, of which `test_post_anchor_tolerates_duplicate_number_strictly_before_boundary` asserts the #425 behaviour as intended. Any fix for #425 must amend an existing green test, which changes the shape of that work: it is a contract revision, not a gap fill.

An earlier statement in this session put the first count at 12. That was wrong; the measured value is 11.

## Blueprint Alignment

| Blueprint claim | Actual finding | Status |
|---|---|---|
| doctrine section 14: post-anchor differs from raw only in pre-boundary tolerance | No linkage pass, no taint propagation | **DRIFT** |
| doctrine line 344: TAINTED propagates from every FAIL | 0 occurrences in `verify_post_anchor` | **DRIFT** |
| doctrine line 345: placeholder FAIL names the offending field | Field computed at line 671, discarded | **DRIFT** |
| glossary "post-anchor boundary": default is highest cleanly-verifying entry | `max(ok_entries)` at line 684 | MATCH |
| GH #55: consumer may release on a clean post-anchor surface | Preserved under the tolerance rule (F-6) | MATCH |

## Post-Brief Correction (2026-09-04T21:40:00Z)

**F-6's conclusion and recommendations R-1 and R-2 below are WITHDRAWN.** They were refuted by measurement taken during the `/qor-plan` pass that consumed this brief, before any plan text was written. The findings F-1 through F-5, F-7 and F-8 stand as recorded.

What was wrong: F-6 concluded that a tolerance rule -- linkage breaks at or below `boundary_entry` disclosed, above it errors -- would close GH #443 while preserving the GH #55 consumer contract. It would do neither, for a reason F-6 did not test.

**The rule is inert on the fork it exists to catch.** `boundary_entry` is `max(ok_entries)`, and a linkage fork leaves every entry chain-math-consistent, so every entry classifies `ok` and the boundary lands at the ledger's tail. Measured on the two fixtures this brief already used:

```
ledger_forked        boundary=#4  break_ids=[3, 4]  above_boundary=[]
ledger_reanchored    boundary=#8  break_ids=[5]     above_boundary=[]
```

Zero breaks fall above the boundary in either case. Under the proposed rule the forked ledger reports both breaks as `DISCLOSED_PRE_ANCHOR` and still returns 0, which is what it does today. The fix would have shipped, passed its own review, and closed nothing.

This is F-7 asserting itself: the same `max(ok)` line that empties the post-boundary band for GH #425 and GH #430 empties it for linkage too. F-6 treated #443 as independent of the boundary; it is not. #443 is downstream of the boundary's definition, so the ordering recommended in R-1 and R-2 is backwards.

**A second measurement closes the obvious repair.** Feeding linkage breaks into the classification -- so a broken entry classifies `fail`, lowering the boundary beneath it -- does catch `ledger_forked`. It also turns `ledger_reanchored`'s legitimate seam break into an error, breaking the GH #55 contract. The existing tolerance path cannot rescue it: `verify()` computes its tolerated set as `_attested_reconciled(entries) & _duplicate_previous_hash_members(entries)` (`ledger_hash.py:518`), and a re-anchor seam is a single entry whose `previous_hash` does not follow its predecessor, not an entry sharing a `previous_hash` with another. The intersection is empty for a seam however it is attested.

A third measurement, taken while designing the composition, is worth keeping because it rules out the implementation that looks most natural. `_sequence_breaks(entries, tolerated)` does not merely suppress a message for a tolerated id; it resets `previous_chain` to `None` (`ledger_hash.py:399-401`), so continuity is unknown across a tolerated entry and its successor cannot break. Passing the pre-boundary id set as `tolerated` therefore erases a break at the first entry above the boundary -- the seam where a fork is most likely:

```
no tolerance          : ['BREAK Entry #5: ...']
tolerate {1,2,3,4}    : []
tolerate {1,2,3}      : ['BREAK Entry #5: ...']
```

**Revised direction, offered as a candidate rather than a conclusion.** GH #443 needs either a new way for a ledger to declare a re-anchor seam so that exactly that link may be tolerated, or a different routing decision: `seal_entry_check` and `governance_health` could call strict `verify()` for a repository that declares no re-anchor, and reserve `verify_post_anchor` for those that do. The second is far smaller and would restore linkage detection to this repository's seal gate immediately. It also partly inverts the GH #88 decision, so it needs its own research pass; how a repository declares itself re-anchored has not been checked, and this brief must not assert an answer it did not measure.

**Sequencing that follows from the above**: no phase should be planned against #443 until the boundary question is settled or the routing candidate is researched. GH #430 is the more tractable entry point, and GH #425 remains independent of both.

## Recommendations

1. **P0 -- WITHDRAWN, see Post-Brief Correction.** Two phases, not one and not three.** Phase A takes GH #443 plus the F-1 field-naming gap: add the linkage pass with pre-anchor tolerance. It is self-contained, measured feasible at both ends (F-5, F-6), amends no existing green test, and carries live evidence. Phase B takes GH #425 and GH #430 together: both are consequences of the `max(ok)` boundary (F-7), both revise the boundary's meaning, and both must amend existing green tests. Splitting A from B keeps each plan's claim surface small, which is what this session's record argues for -- Phases 258 and 261 reached five-attempt caps on breadth, Phase 262 was two files and passed on attempt 1. Splitting B into two would instead put two plans against the same four lines.
2. **P0 -- WITHDRAWN, see Post-Brief Correction.** Order A before B.** A is correct under the current boundary and inherits any improvement B makes to it; A needs no test amended, so it cannot be blocked by a contract argument. Running B first would make A's tolerance predicate change meaning mid-cycle.
3. **P1 -- Pin mode parity by property, not by example.** The durable shape is a test that, for a corpus of fixtures, asserts: if `verify_post_anchor` returns 0, then every error `verify` reports is at an entry at or below the detected boundary. That is a generated relation rather than an enumerated case list, so it fails on the next divergence rather than only on the three now known. It would have caught F-2 on the day it was introduced.
4. **P2 -- Treat section 14 as the specification under test.** The three issues were each filed as behavioural defects. They are more precisely specification drift against a doctrine section that already says the right thing, which means the fix is verifiable against a written contract rather than against judgment.
5. **P2 -- Record the diagnostic gap from F-1 with the field-naming fix.** `FAIL Entry #N: post-anchor verification failure` names no cause. GH #428, separately filed, is the same complaint from a different direction.

## Updated Knowledge

For `docs/SHADOW_GENOME.md`: a hypothesis was formed about a defect's cause from the shape of an incident (the #425 window explaining the #729/#730 fork), and refuted by executing the classifier against a fixture of the actual shape. The correction cost one measurement and would have become a false Locked Decision in a plan had it gone unchecked. The general form is that an incident and an open issue describing a nearby symptom are not evidence for each other.

For `qor/references/doctrine-governance-enforcement.md` section 14: no doctrine change is recommended here. The section is correct as written; the implementation is what diverges. Recording that direction matters, because the cheaper resolution -- amending the doctrine to describe what the code does -- would ratify the defect.

---

_Research complete. Findings are advisory; implementation decisions remain with the Governor._
