# AUDIT REPORT -- Phase 218 (GH #319 cluster), iteration 2

**Verdict**: PASS
**Risk Grade**: L2
**Target**: docs/plan-qor-phase218-unreconciled-record-cluster.md
**Session**: 2026-08-11T1304-400282
**Branch**: phase/218-unreconciled-record-cluster
**Mode**: solo (audit_risk_score option_b_required=false)
**Prior verdict**: VETO at ledger entry #547 (`infrastructure-mismatch`, `specification-drift`, `coverage-gap`); all three cleared below
**Categories**: `infrastructure-mismatch`, `specification-drift`, `coverage-gap`

## Prior-ground disposition

### Ground 1 -- `infrastructure-mismatch`: the exceptions list is factually wrong

LD-1 seeds `KNOWN_ENTRY_GAPS = frozenset({532})`. The ledger has **two** gaps:

```
gaps in numbering: [510, 532]
```

Entry #510 is absent between `#509: SESSION SEAL -- Phase 207` and
`#511: IMPLEMENTATION -- Phase 208`, and its file-order link is intact
(`#511.previous == #509.chain`). Neither the research brief (#546) nor GH #316
mentions it; both name only 532.

An exceptions list that omits a real exception makes the contiguity WARN fire on
the repository's own ledger from the first run -- reproducing, in the fix, the
noise defect Phase 217 was sealed to remove.

The Judge notes how this surfaced: the ambiguity in Ground 2 was being tested
empirically, and enumerating the gaps to test it exposed the second one. Reading
the plan would not have found it.

**Required next action:** Governor: enumerate the gaps from the ledger rather
than asserting them, seed the list with both, and state why each is exempt.
**Plan-text** ground.

### Ground 2 -- `specification-drift`: LD-1 admits two incompatible implementations

LD-1 says the assertion is that "entry N's `previous_hash` equals entry N-1's
`chain_hash`." That phrasing does not distinguish:

- **file order** -- the entry physically preceding it, or
- **number order** -- the entry numbered N-1.

The two differ materially on this repository's own data:

```
file-order   (#533.prev == #531.chain): True
number-order (#533.prev == #532.chain): #532 absent -> FAIL
```

Number-order fails the live ledger at both gaps. File-order passes. A plan whose
central Locked Decision admits an implementation that red-lights the repository
it ships in is underspecified, and DoD D3 would catch it only after the
implementation was written.

**Required next action:** Governor: state file order explicitly in LD-1, and say
why -- deletion is detectable in file order precisely because numbering is not
load-bearing. **Plan-text** ground.

### Ground 3 -- `coverage-gap`: the new module has no wiring coupling

Phase 3 ships `qor/scripts/verdict_reconcile.py` and adds a call to
`/qor-implement` Step 2. Four tests cover the module. None asserts the skill text
actually invokes it.

Phase 217 shipped exactly this coupling for the same reason and recorded it in
the seal: a producer that can be deleted while its consumer remains is a slot
nothing fills. `test_seal_step_invokes_the_check` exists one phase back as the
precedent. Its absence here repeats a defect this project fixed last phase.

The gap is sharper than usual because `/qor-implement` Step 2 is prose: nothing
mechanical fails if the call is dropped, and the module would sit in the tree
looking like coverage.

**Required next action:** Governor: declare a test asserting the skill text names
`verdict_reconcile`, then re-run `/qor-audit`. **Plan-text** ground.

## Passes

| Pass | Result |
|---|---|
| Prompt Injection | PASS (canary scan, exit 0) |
| Security / OWASP | PASS -- local file reads and digests; no network, no subprocess on untrusted input |
| Test Functionality | PASS -- every declared test invokes the unit and asserts on returned findings or exit codes |
| Filter-Stage | PASS |
| Infrastructure Alignment | Ground 1 (see above); the four LD grep citations themselves re-verified at the cited lines |
| Feature Test Declaration | PASS -- both rows carry `test_path` and `test_descriptor` |
| Razor / self-application | PASS -- additions are small; `ledger_hash.py` is the largest touched and has room |
| Publication boundary | PASS -- 0 findings |
| pre-audit lint ladder | all rc=0; `dod_check` rc=0 |

## Grounds considered and rejected

**LD-5 over-constrains by demanding a failing test per fix.** Rejected, and it is
the plan's strongest clause. All four checks currently PASS on the input they
should reject, so a good-path test would pass at HEAD and prove nothing. Requiring
a test that fails against HEAD is the only construction that demonstrates the
defect existed.

**The cluster is too broad for one phase.** Rejected. Four corrections to four
independent modules, no shared state, each with its own counterfactual. Splitting
would multiply ceremony without reducing risk.

**#316's fix cannot detect tail truncation, so it is incomplete.** Rejected as a
ground; the plan states this limit explicitly in `## Boundaries` rather than
implying coverage it lacks. Naming the ceiling is the correct handling.

**`change_class: feature` is wrong for bug fixes.** Rejected. Two new modules
ship with new invocable surfaces; `feature` is the honest class.

## Verdict

**PASS** at L2. All three grounds are cleared, and two of the remedies are
stronger than the VETO required.

**Ground 1** -- `KNOWN_ENTRY_GAPS` is now `frozenset({510, 532})`, and both are
verified absent from every commit rather than recalled (`git log --all -S "Entry
#510"` returns nothing). The plan goes further than asked: a new test,
`test_live_ledger_gap_set_matches_declared_exceptions`, enumerates gaps from the
live ledger and asserts equality with the constant. That test goes red both when
a new gap appears AND when someone widens the constant to silence one -- closing
the exact mechanism by which 510 went unnoticed. An exception list that can drift
from reality is the defect this cluster exists to fix; the plan now refuses to let
its own remedy become an instance.

**Ground 2** -- LD-1 states file order explicitly, shows the two candidate
semantics against live data, and argues the merits: the chain is built by
appending, so adjacency in the artifact is the real structure and entry numbers
are labels. That reasoning also explains why deletion is the detectable case.

**Ground 3** -- `test_implement_step_invokes_the_reconciler` is declared, citing
the Phase 217 precedent and naming why the coupling matters more here: Step 2 is
prose, so nothing mechanical fails if the call is dropped.

The stale `frozenset({532})` left in Phase 1's Affected Files after the LD-1
amendment was corrected before this verdict; the plan now states the constant
identically at both sites.

Implementation may proceed. LD-5 is binding: each of the four fixes ships a test
that FAILS against `HEAD`. A fix whose test passes before the change has not
demonstrated the defect and does not satisfy this plan.
