# Research Brief

**Date**: 2026-08-11
**Analyst**: The Qor-logic Analyst
**Target**: GH #319 cluster -- #313, #316, #318, plus #321
**Scope**: Verify each claim against source and by counterfactual, not against the issue text

---

## Executive Summary

All four claims hold, and two are more precise than filed. Every one was verified
by running the check against a deliberately broken input rather than by reading
the code, because twice today an issue written from reading was wrong.

The unifying property is narrower than "a claim nothing checks". In each case a
check **exists and passes** on input it should reject. A failing check is a
working control; a passing check on bad input is a control that certifies the
defect.

## Findings

### 1. #316 is a missing cross-entry assertion, not a missing contiguity check

The filed issue said `ledger_hash verify` "checks linkage, not entry-number
contiguity." Linkage is in fact checked, indirectly and effectively:

```
corrupt #545's previous_hash -> rc=1
```

Because `chain_hash = f(content_hash, previous_hash)`, altering `previous_hash`
invalidates the recorded chain hash. Tampering is caught.

Deletion is not:

```
excise Entry #544 entirely -> rc=0, "OK Entry #545: chain hash verified"
```

Every surviving entry remains internally consistent. Nothing asserts that entry
N's `previous_hash` is the chain hash *produced by entry N-1*, so removing an
entry leaves a ledger that verifies clean. The `#531 -> #533` gap already present
in this repository is the benign case; the same blindness covers a deliberate
excision.

**The defect is the absence of a sequence assertion.** Entry-number contiguity is
one symptom, and the weaker one -- an attacker renumbering is visible, an
attacker deleting is not.

### 2. #318 confirmed at the line

`qor/reliability/intent_lock.py:31`:

```python
return _sha256_bytes(path.read_bytes())
```

Raw bytes. `ledger_hash.content_hash` normalizes CRLF to LF first
(`ledger_hash.py:37`) with a docstring naming GAP-GOV-03 as the reason. One
hasher learned the lesson; the other did not.

Failure mode is a **false ABORT**, the safe direction, but it fires on entirely
normal Windows events -- `autocrlf`, an editor, `Path.write_text`. The operator
response to a false ABORT is to re-capture, which is also the action that masks a
real drift. This phase's own seal hit it and had to prove the change was
encoding-only before re-capturing.

### 3. #313 confirmed; the report is a cross-session artifact

`qor-implement/SKILL.md:134-139` reads `.agent/staging/AUDIT_REPORT.md` and
branches on the verdict string alone. Nothing compares the report's `**Target**`
line to the audit gate artifact's `target`.

`.agent/staging/` is not session-scoped. This session hit the mismatch three
times -- a Phase 206 report survived into Phase 215, a Phase 215 report into
Phase 216, and a stale VETO into Phase 217's implement. Each time the interdiction
would have passed on a PASS belonging to another phase.

Both records already exist; the gate artifact carries `target` and
`target_content_hash`. The comparison needs no new data.

### 4. #321 confirmed, and the exclusion looks incidental

`gate_provenance.py:44`:

```python
_REQUIRED_PHASES = ("plan", "audit", "implement", "substantiate")
```

consumed at `:226` as the set walked. `<phase>-iterN.json` does not match those
names, so iteration artifacts are outside Layer B entirely.

Demonstrated accidentally during the Phase 217 seal: a sidecar written with a
wrong digest formula passed `verify-committed` with **OK: provenance verified for
49 sessions**. The check reported success over a sidecar that did not recompute.

Iteration artifacts are not scratch -- entry #542 binds a vetoed plan and #543 the
amendment, and the `-iter` files are what a reader consults to reconstruct why.
The shape of `_REQUIRED_PHASES` (a completeness list reused as a verification
scope) suggests reuse rather than a decision.

### 5. Only #313 needs skill wiring, and it fits

| Skill | size | slack |
|---|---|---|
| `qor-implement` | 19,849 | 20,087 |
| `qor-substantiate` | 39,908 | **28** |
| `qor-audit` | 39,473 | 463 |

The cross-check belongs in `/qor-implement` Step 2, which has room. Nothing in
this cluster needs `qor-substantiate`, which is at its practical ceiling after
Phase 217 and cannot absorb a step without a disclosure pass first.

## Blueprint Alignment

| Claim as filed | Verified finding | Status |
|---|---|---|
| #316: linkage checked, contiguity not | linkage IS checked; **deletion** is not | DRIFT -- sharpen |
| #318: raw-byte hashing | confirmed at `intent_lock.py:31` | MATCH |
| #313: no report/artifact reconciliation | confirmed; 3 occurrences this session | MATCH |
| #321: iterN outside Layer B | confirmed at `gate_provenance.py:44`; demonstrated | MATCH |
| Cluster needs seal-time wiring | only #313, and it targets `qor-implement` | DRIFT -- no ceiling risk |

## Recommendations

1. **#316: assert the sequence, not the numbering.** Verify each entry's
   `previous_hash` equals the preceding entry's `chain_hash`. Entry-number
   contiguity becomes a WARN with a declared exceptions list seeded with 532,
   since closing that hole would require rewriting every downstream chain hash.
2. **#318: apply `ledger_hash.content_hash`'s treatment** in `_hash_file`. Sweep
   for other hashers that missed GAP-GOV-03; this is the second found.
3. **#313: compare `target_content_hash`**, not just the target path -- that also
   catches a report written against a since-amended plan.
4. **#321: separate the completeness list from the verification scope.** Walk
   every `*.json` with a sidecar rather than reusing `_REQUIRED_PHASES`.
5. **Test each by counterfactual.** Every fix here must ship a test that feeds the
   check the input it currently accepts and asserts rejection. A test that only
   confirms the good path would pass today.

## Updated Knowledge

The `SG-InertControl-A` entry recorded in Phase 217 covers a control wired so it
cannot fire. This cluster is adjacent but distinct: these controls fire, run, and
return success on input they should reject. Suggested framing if it recurs --
a control validated only against inputs it was built to accept, so its silence
means "not asked" rather than "verified".

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
