# Research Brief

**Date**: 2026-09-11
**Analyst**: The Qor-logic Analyst
**Target**: GH #463 -- a wired ABORT gate produced no effect across a run of sealed phases
**Scope**: whether the claim holds after Phase 275; how much of the gate surface is prose; what execution evidence exists; relationship to #462, #451, #459

---

## Executive Summary

The claim holds and its evidence has already eroded, exactly as the issue
predicted. Re-derived against correctly paired sealed phases, `verdict_reconcile`
now produces a finding on **3 of 38** (7 percent), not the 84 of 189 (~44 percent)
the issue cites. Phase 275 fixed the parser between the filing and now. #463
warned that this would happen: "fixing the parser makes this particular gate stop
mis-firing, which would also make its silence permanently invisible." It did.

The wider measurement is the finding. Across 32 `SKILL.md` files there are **119**
statements that a condition ABORTs, VETOes, or must not proceed. **Twelve** sit on
a line carrying a runnable command. **Eleven** of those twelve express the gate as
`|| ABORT`, which is prose occupying a shell position. The repository holds **29
tests that verify a gate step is written down** and **none** that verify one ran.

The mechanism #463 asks for already exists and produces nothing. Phase 242 shipped
a governed-procedure execution-evidence contract -- schema, evaluator, two test
files. Zero artifacts of that kind exist on disk and no skill, workflow or script
calls it. That is by design rather than by neglect, and the design is the gap.

## Findings

### 1. The claim survives; the rate does not

Method: for each seal commit, take the audit report **and** the gate artifact from
that same commit, pairing by the single `.qor/gates/<sid>/` directory the commit
adds. This matters -- two earlier pairings gave 8/60 and a meaningless 39/40, the
second because forty sessions' artifacts were reconciled against one report.

Correctly paired, over the 50 most recent seal commits (38 yielding a clean pair):

| | |
|---|---|
| sealed phases checked | 38 |
| producing at least one reconcile finding | **3** (7%) |
| finding kinds | `target-mismatch` x2, `report-unreadable` x1 |

Named: `seal: phase 267 discarded validation`, `seal: phase 240 execution-context
adaptive`, `seal: phase 228 reviewer toolset declaration`.

Three phases sealed carrying a finding the wired gate says must ABORT. The
existence is the claim; the rate is not. #462's ~44 percent was measured against a
different population (189 intent-lock-accepted reports) and before Phase 275.

### 2. The gate surface is prose by a ratio of roughly ten to one

`grep` over `qor/skills/**/SKILL.md` for `ABORT`, `VETO`, `must not proceed`,
`fail-closed`, `halts the skill`:

| | count |
|---|---|
| total statements | **119** |
| on a line carrying a runnable command | 12 |
| of those, expressed as `\|\| ABORT` | **11** |

Concentration: `qor-audit/SKILL.md` 58, `qor-substantiate/SKILL.md` 31,
`qor-implement/SKILL.md` 4.

`|| ABORT` is not decorative. Executed as shell it fails closed by accident of
syntax:

> `bash -c 'false || ABORT; echo "exit=$?"'`
> -> `bash: ABORT: command not found` / `exit=127`

A passing check short-circuits to 0; a failing one reaches a non-existent command
and yields 127. So the idiom works **if the step is executed as shell**. Nothing
requires that. A skill step is markdown addressed to an agent, and the agent may
read it, paraphrase it, or run it. The construct's correctness is conditional on a
behaviour the repository cannot check.

### 3. Twenty-nine tests verify wiring; none verify execution

`tests/` holds **32** `*_wiring.py` files, **29** of which read a `SKILL.md`. Their
assertion shape is that the step text is present -- that removing a section breaks
the assertion. They are the mechanised form of "the gate is wired" and cannot
distinguish it from "the gate ran", which is precisely the distinction #463 draws.

### 4. No artifact records execution

Provenance sidecars carry `alg`, `hmac_tag`, `payload_sha256`, `phase`,
`session_id`. That is tamper-evidence over a payload an agent wrote; it attests
that the artifact was not altered after writing, not that any check produced it.

Across all 22 gate schemas, no field records which checks ran. `plan.schema.json`
carries `ci_commands` and `required_gate_artifacts` -- both declarations of intent.
`substantiate.schema.json` carries `reality_check`. None is an execution record.

An agent that skipped every gate and wrote plausible artifacts would produce a
gate chain indistinguishable from one that ran them all, and would pass
`gate_chain_completeness`, `seal_entry_check`, and the provenance verification.

### 5. The answer exists, produces nothing, and that is deliberate

`qor/gates/schema/procedure_execution_evidence.schema.json` -- "Governed Procedure
Execution Evidence Contract", required fields `contractVersion`, `requirements`,
`evidence`. Implemented at `qor/compliance/procedure_evidence.py` with
`evaluate_contract`, `validate_contract`, `canonical_claim_digest`. Covered by
`tests/test_procedure_evidence.py` and `tests/test_portable_governance_boundary.py`.

Artifacts of this kind on disk: **zero**. Production callers in `qor/skills/`,
`qor/scripts/` or `.github/`: **zero**.

This is not #459's shape. Phase 242's plan scopes it explicitly:

> `docs/plan-qor-phase242-governed-procedure-evidence.md:17` -- "Phase 242
> implements portable evidence **meaning and satisfaction semantics**. It does not
> implement a universal signer, hosted observer, GitHub integration, or enterprise
> trust service."
> `:30` -- "Execution hosts / trusted wrappers own:"

The evaluator half was built deliberately; the producer half was assigned to an
execution host. No such host exists for this repository, so the contract has a
consumer and no producer, and evaluates nothing. The gap is a design boundary
nobody stands on, not a forgotten wire.

### 6. Relationships, precisely

- **#462** (parser) is *upstream evidence* for #463, not a subset. Fixing it
  reduced the observable symptom from ~44 to 7 percent while leaving the
  underlying property untouched. #463 anticipated this in its own text.
- **#459** (`validate_event_id` ships, tested, no production path) is an
  *instance* of the general property #463 names, in a different subsystem.
- **#451** (gate-artifact set completeness at seal) is *adjacent and weaker*: it
  asks whether the four artifacts exist, which an agent can satisfy by writing
  them. It cannot distinguish execution either.
- **Phase 242** is the *partial answer*, consumer-side only.

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| `/qor-implement` Step 2 ABORTs on any reconcile finding | 3 of 38 sealed phases carry one | **DRIFT** |
| #462's ~44 percent finding rate | 7 percent on correct pairing post-Phase-275 | **DRIFT (eroded)** |
| Gates are enforced | 119 declarations, 11 conditionally-executable, 0 verifiable | **DRIFT** |
| Provenance attests the phase | It attests the artifact against tampering only | **DRIFT** |
| No execution-evidence mechanism exists | One exists, deliberately producer-less | **DRIFT** |

## Recommendations

1. **P0 -- do not close #463 by fixing #462.** The parser fix already halved the
   visible symptom. Further parser work makes the property less observable, not
   more true.
2. **P1 -- the decision is who produces evidence.** Phase 242 assigned production
   to an execution host. Either this repository becomes that host for its own
   cycles, or the contract stays inert and #463 cannot be closed. That is an
   operator decision about scope, not an implementation detail.
3. **P2 -- the 29 wiring tests are worth keeping and worth renaming.** They assert
   a real property (the step is declared) and their names invite reading them as
   more. Nothing about them is wrong except what a reader infers.
4. **P2 -- `|| ABORT` deserves either enforcement or honesty.** It fails closed
   when executed and does nothing when read. A construct whose correctness depends
   on an unobservable choice should not look like a shell guarantee.

## Updated Knowledge

For `docs/SHADOW_GENOME.md`: a control can be correct, tested, documented, and
still unobservable -- and the tests that cover it can themselves be the reason
nobody notices. Twenty-nine passing wiring tests are evidence that gates are
declared, and reading them as evidence that gates run is the error this
repository has now made at least four times in one session: the nightly step that
died before its verdict, a fail-closed gate with no module, a release that cannot
publish, and a session that orphans its own chain. Each looked exactly like
success from outside.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
