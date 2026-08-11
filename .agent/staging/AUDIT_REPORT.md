# AUDIT REPORT -- Phase 217 (GH #314, rescoped), iteration 2

**Verdict**: PASS
**Risk Grade**: L2
**Target**: docs/plan-qor-phase217-installed-skill-drift.md
**Session**: 2026-08-11T0639-f954d2
**Branch**: phase/217-installed-skill-drift
**Mode**: solo (audit_risk_score option_b_required=false)
**Prior verdict**: VETO at ledger entry #542 (ground: `coverage-gap`); cleared below

## Prior-ground disposition -- `coverage-gap`: LD-4 defers enforcement to an unfiled V2

**Category note.** The finding is a half-measure deferral, and `audit.schema.json`
carries no such category. Its enum is deliberately closed with no `other` escape
hatch, so an unmappable finding must either map honestly or force a schema
amendment. Recorded as `coverage-gap`, which fits on the merits: the Definition
of Done gives the deferred enforcement no empirical tier and no `D4.d` waiver.
Whether "half-measure deferral" warrants its own category is worth a separate
decision -- GH #147 catalogued eleven instances and GH #319 was filed today --
but inventing one mid-audit is exactly the deliberate-amendment discipline the
closed enum exists to enforce.

LD-4 ships disclosure and states:

> Enforcement is a V2 decision informed by real drift counts, following the
> WARN-then-enforce precedent (`merge_velocity_check` Phase 93 -> 129).

The architectural reasoning is sound and the Judge accepts it: the skill running
the check is part of the corpus under test, so a drifted `qor-substantiate`
could carry a weakened or absent check, and CI cannot enforce because CI has no
operator install. Disclosure genuinely is the honest V1.

The defect is that the V2 exists only as a sentence. No issue is filed, no
follow-on phase is named, and the `## Definition of Done` carries no `D4.d`
waiver recording the deferral with its rationale and successor.

This is the exact pattern this repository has documented against itself. GH #147
catalogued eleven closed issues that shipped advisory-only and deferred the
enforcer to an unfiled V2. GH #319 was filed **today** about governance records
asserting properties nothing checks. `dod_check` exists specifically to catch a
deliverable that declares no empirical tier or waiver.

A plan that names the WARN-then-enforce precedent should also honor what made
that precedent work: `merge_velocity_check` reached fail-closed at Phase 129
because the follow-on was tracked, not because the V1 mentioned a V2.

Left as written, the deferral is indistinguishable at seal from an enforcement
that was considered and rejected.

**Required next action:** Governor: file the V2 enforcement issue, cite it in
LD-4 and in a `D4.d` waiver with rationale and named follow-up, then re-run
`/qor-audit`. Per `qor/references/doctrine-audit-report-language.md` this is a
**Plan-text** ground.

## Passes

| Pass | Result |
|---|---|
| Prompt Injection | PASS (canary scan, exit 0) |
| Security / OWASP | PASS -- digest over local files; no network, no subprocess on untrusted input |
| Ghost UI / Live-Progress | N/A |
| Test Functionality | PASS -- nine declared tests, each invoking the unit and asserting on returned findings or digest values |
| Filter-Stage | PASS |
| Infrastructure Alignment | PASS -- three LD citations carry paired grep evidence, re-verified at the cited lines |
| Feature Test Declaration | PASS -- both rows carry `test_path` and `test_descriptor` |
| Razor / self-application | PASS -- `install_drift_check.py` is ~70 lines; additions stay far under 250 |
| Publication boundary | PASS -- 0 findings |
| pre-audit lint ladder | all rc=0 |
| sg_closure_lint | 40 entries, 0 without enforcer citation |

## Grounds considered and rejected

**LD-1 rewrites a finding the research brief already sealed.** Rejected, and the
correction is to the plan's credit. Entry #541 records that the brief's first
draft called the repo-scope check a silent pass, and that running it returned 30
findings at exit 1. LD-1 states the corrected fact and draws the right
consequence: an absent scope is one fact, not thirty defects. A plan that
inherited the uncorrected premise would have built the wrong remedy.

**LD-5 sequences a destructive operation last for convenience.** Rejected. The
27 live mismatches are the only real fixture for the new check, and resyncing
first would destroy the evidence the phase exists to act on. Sequencing is
methodological, not convenient. Operator has explicitly authorized overwrite of
installed skills as generated artifacts.

**Phase 5 has no verifiable deliverable.** Rejected as a ground, noted as a
limit. The resync mutates a directory outside the repository, so no test can
assert its effect. The seal entry recording pre-resync drift count and
post-resync digest is the available evidence, and the plan already requires it.

**`change_class: feature` is wrong.** Rejected. Two new user-invocable
surfaces ship (`scope="auto"`, `skill_corpus.digest`); the schema field is
optional and no existing artifact breaks.

## Noted risk, not a ground

`qor-substantiate` carries 313 bytes of slack against the 39,936-byte lock, and
Phase 3 adds a step to it. The plan pre-commits to moving rationale into
`references/seal-gate-ladder.md` if the step does not fit. Phase 216 consumed
807 bytes of that file's slack against a 360-byte estimate, so the estimate
class has already been wrong once in the direction that hurts. Measure before
and after; if the inline step exceeds the remaining slack, the relocation is
mandatory, not optional.

## Verdict

**PASS** at L2. The ground is cleared.

GH #320 is filed and carries substance rather than a placeholder: three named
decisions V2 owes -- where enforcement can honestly live given the checker sits
inside the corpus it validates, what threshold constitutes drift, and whether
the ledger should distinguish clean-corpus from drifted-corpus seals at query
time -- plus entry criteria requiring observed drift data before the enforcement
point is chosen. LD-4 now cites it, and the Definition of Done carries a `D4.d`
waiver with architectural rationale and a named follow-up. `dod_check` returns
exit 0 against the amended plan.

The deferral is now distinguishable at seal from an enforcement considered and
rejected, which is the whole of what the VETO asked for.

Implementation may proceed. Binding: the noted risk above is not advisory --
`qor-substantiate` has 313 bytes of slack and Phase 216 overran a same-class
estimate by more than double. Measure before and after; relocate on overflow.
