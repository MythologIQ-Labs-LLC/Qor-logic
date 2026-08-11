# Research Brief

**Date**: 2026-08-11
**Analyst**: The Qor-logic Analyst
**Target**: Phase B of GH #285 -- provider-neutral execution-continuity semantics for the lifecycle gates
**Scope**: What the existing seams actually do, where they conflict with the requirement, and what the issue's own test bar forces Qor-logic to ship

---

## Executive Summary

Headroom is no longer the constraint. Phase A left `qor-audit` 1,547 bytes and
`qor-substantiate` 1,120 bytes of slack against the 39,936-byte lock, roughly 3x
the 520/360 the issue needs.

Three findings reshape the work:

1. **`intent_lock` is the wrong seam.** It verifies by git *ancestry*, deliberately,
   since Phase 43. Exact-revision receipt semantics are the opposite requirement.
   Extending it would either break its tolerance or silently inherit ancestry into
   receipt checking -- which accepts exactly the stale receipt #285 says must fail.
2. **`inconclusive` cannot reuse `skip`.** Every outcome enum in the repository is
   binary or binary-plus-`skip`, and `skip` already means "we chose not to run this."
   `inconclusive` means "we ran it and the environment prevented a conclusion."
   Collapsing them destroys the distinction the issue exists to create.
3. **The issue's test bar forces executable code, not prose.** Its final required
   test rejects presence-only assertions where runtime behavior is claimed. Several
   required behaviors -- resumability, fail-closed rejection, staleness -- have
   nothing to invoke unless Qor-logic ships its own classifier.

## Findings

### 1. Post-Phase-A headroom is sufficient

| Skill | size | slack to 39,936 | #285 needs |
|---|---|---|---|
| `qor-audit` | 38,389 B | 1,547 | 520 |
| `qor-substantiate` | 38,816 B | 1,120 | 360 |
| `qor-plan` | 24,920 B | 15,016 | -- |

The other four lifecycle skills are all under 20 KB. MATCH; Phase A did its job.

### 2. `intent_lock` verifies by ancestry, and #285 requires exact equality

`qor/reliability/intent_lock.py:113-116` captures `plan_hash`, `audit_hash`, and
`head_commit`. Verification at `:152-167` does **not** compare HEAD for equality:

> `# Phase 43: ancestry check instead of strict equality.`
> `# Allows legitimate forward progress (the implement commit advancing HEAD`
> `# between Step 5.5 capture and substantiate Step 4.6 verify)`

It runs `git merge-base --is-ancestor <captured> HEAD` and passes whenever the
captured commit remains reachable.

#285 requires the inverse in three places: "the verification target is the exact
revision under review"; "reject or mark stale any receipt whose revision differs
from the current head"; "revision movement after verification: require
re-verification."

An earlier note called `intent_lock` the seam to extend rather than duplicate.
That is wrong on inspection, and wrong in the dangerous direction. Extending it
either removes the Phase 43 tolerance that legitimate implement commits depend
on, or it lets receipt verification inherit ancestry semantics -- under which a
receipt cut at commit A still verifies after HEAD advances to B. That is
precisely the stale-receipt acceptance the issue forbids.

**DRIFT.** The receipt binding must be exact-equality and must live alongside
`intent_lock`, not inside it. The two answer different questions: `intent_lock`
asks "is this still the work that was audited?", the receipt asks "was this exact
tree verified?"

### 3. `inconclusive` is genuinely new, and `skip` is a trap

Every outcome enum in `qor/gates/schema/`:

| schema | field | enum |
|---|---|---|
| `validate` | `status` | `pass` / `fail` / `skip` |
| `qa` | `verdict` | `PASS` / `FAIL` |
| `qa` | `status` | `pass` / `fail` / `skip` |
| `substantiate` | `verdict` | `PASS` / `FAIL` |

`inconclusive` appears nowhere in `qor/`, `tests/`, or `docs/` outside one unrelated
prose mention.

`skip` in this repository already carries a settled meaning: the Phase 75
disclosed-skip path, where a prerequisite is absent and the gate deliberately does
not run. Phase 215 used it exactly that way. `inconclusive` is the opposite
epistemic position -- the gate ran and the environment denied it a conclusion.

Reusing `skip` would be the cheapest implementation and would silently defeat the
requirement, because a disclosed-skip is already treated as acceptable-to-seal
while `inconclusive` must route to evidence-environment repair.

**DRIFT.** A third value is required. This is the one place the phase adds a new
concept rather than wiring an existing one.

### 4. Stable ledger identity already exists; checkpoints must use it

`qor/reliability/ledger_base_currency.py:104` derives identity via
`entry_id.derive_entry_id(e["ts"], e["phase"], e["content_hash"])`, and the module
docstring at `:15` states new entries are identified by chain-hash rather than
number. GH #51 (sequential numbering incompatible with concurrent workers) is
CLOSED, so this is settled authority.

#285 requires checkpoints and receipts to "reference stable ledger identity rather
than assume sequential entry numbers are globally unique."

This is not hypothetical. `docs/META_LEDGER.md` currently runs #531 -> #533; entry
#532 was allocated in an abandoned session, never committed, and the chain is
intact because #533 links to #531's chain hash. `ledger_hash verify` reports OK,
having no contiguity check (filed as GH #316). A checkpoint citing "entry #532"
would reference nothing, and nothing would detect it.

**MATCH on availability, with a live demonstration of why.**

### 5. The contract pin has a precedent and an honesty problem

`.qorlogic/config.json` read through `qorlogic_config.load_section` is the
established surface for operator-declared external integrations; `external_reviewer`
(`qor/scripts/external_reviewer.py:32-43`) is the working precedent, and it degrades
to a disclosed fallback rather than failing when unconfigured.

The problem is verification, not placement. #285 says implementation "must pin a
reviewed compatibility version" of the upstream contract. Qor-logic can record that
it *declares* compatibility with version X. It cannot check that the artifact it
received conforms to version X without the upstream schema in hand, which the
ownership boundary forbids duplicating.

So the pin is **assertable but not verifiable from this repository**. A declaration
that reads like a guarantee and delivers an assertion is the exact shape of GH #314,
filed today: a fail-closed step whose enforcer does not exist. The phase must state
the ceiling plainly rather than let the pin imply a check it cannot perform.

**DRIFT -- not in the requirement, in how it is likely to be implemented.**

### 6. The test bar forces an executable classifier

The issue's final required test: "real validators/commands are invoked in tests where
executable behavior is claimed; presence-only assertions are insufficient."

Of the 13 required behavioral tests, these have nothing to invoke if Qor-logic ships
only skill prose: provider-budget exhaustion remains resumable; missing or malformed
checkpoint fails closed; live competing writer rejected; revision mismatch prevents
continuation; receipt accepted only for the current revision; receipt goes stale after
head movement; environment outage yields `inconclusive`; self-report cannot satisfy
verification; worker authority cannot expand.

Every one is a *decision over typed inputs*. The ownership boundary gives the upstream
line the schemas and their validators, but gives Qor-logic "audit classifications and
fail-closed checks." Those are not the same artifact. Qor-logic needs a classifier that
consumes contract-shaped inputs it does not define and returns a routing outcome.

`qor/scripts/` already has fail-closed decision modules of this shape --
`remediate_pattern_match.py`, `governance_health.py`, `ledger_hash.py` -- so the
pattern is established, and eight `plan_*_lint.py` modules establish the
plan-declaration enforcement pattern.

**Without this module the phase degrades into thirteen prose assertions and becomes
another #314.**

### 7. The no-named-provider test needs a distinction, not a grep

`qor-audit/SKILL.md` carries 3 vendor-name occurrences and `qor-remediate/SKILL.md`
carries 2. All are optional-integration references -- the codex-plugin adversarial
path, which falls back to solo and logs a capability shortfall.

#285 forbids named vendors in *core semantics*, not their mention as optional
integrations. A naive "no vendor names in skills" test goes red on legitimate
existing text. The test must assert that no gate *outcome* depends on a named
provider, which is a narrower and harder property than a grep.

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| Headroom permits Phase B | 1,547 / 1,120 vs 520 / 360 | MATCH |
| `intent_lock` is the seam to extend | ancestry semantics conflict with exact-revision | **DRIFT** |
| `inconclusive` is a new concept | absent everywhere; `skip` means something else | MATCH, with a trap |
| Checkpoints reference stable identity | `derive_entry_id` exists; #51 closed | MATCH |
| Upstream contract can be pinned | placement yes; verification no | **DRIFT** |
| Skill prose satisfies the test bar | 9 of 13 tests have nothing to invoke | **DRIFT** |
| Vendor-neutrality is grep-testable | existing optional references are legitimate | **DRIFT** |

## Recommendations

1. **Do not extend `intent_lock`.** Add an exact-revision receipt binding beside it
   and state in the plan why ancestry is correct for one and wrong for the other.
2. **Add `inconclusive` as a third enum value**, and write the `skip`-vs-`inconclusive`
   distinction into the glossary, because the cheap implementation is the wrong one.
3. **Ship an executable classifier** consuming contract-shaped inputs and returning
   `verified` / `rejected` / `inconclusive` plus a routing directive. Without it the
   thirteen tests cannot meet the bar the issue itself sets.
4. **Pin by declaration and say so.** Record the compatibility version in
   `.qorlogic/config.json` per the `external_reviewer` precedent, and state in the
   plan and the seal that Qor-logic asserts rather than verifies conformance.
5. **Reference ledger identity via `derive_entry_id`**, never entry numbers; cite
   GH #316 as the demonstration.
6. **Write the vendor-neutrality test against outcome dependence**, not name presence,
   and record the existing optional references as the accepted baseline.
7. **Expect this to be large.** Seven skills, a schema change, a lint, a classifier,
   glossary terms, docs, and thirteen tests, delivered atomically per the acceptance
   criteria. The failure mode to guard is declaration-without-enforcer, which this
   repository produced three times this week (#313, #314, #316).

## Updated Knowledge

`docs/SHADOW_GENOME.md` warrants an entry for the pattern behind #313/#314/#316 and
the risk this phase carries: a governance record that asserts a property nothing
checks. Existing `SG-HalfSealedClaim-A` covers disclosed skips on absent
prerequisites; it does not cover a declaration whose enforcer was never written.
Recommend `SG-UnenforcedDeclaration-A` if the audit agrees the pattern is distinct.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
