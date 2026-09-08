# Research brief: the gate mode is weaker than the mode it replaced

**Date**: 2026-09-07
**Session**: 2026-09-07T2035-2f4c25
**Issues**: GH #443, GH #425, GH #430

## The shared defect

`verify_post_anchor()` exists so re-anchored consumer ledgers can carry disclosed pre-anchor failures without failing a release gate. Two gates were pointed at it deliberately -- `seal_entry_check.check()` at `qor/reliability/seal_entry_check.py:149`, and the skill-entry preflight via `governance_health._verify_post_anchor` at `qor/scripts/governance_health.py:149` -- and neither change enumerated what else was being surrendered.

Three checks that `verify()` performs are absent or unreachable in the mode the gates actually consume. Each was measured, not argued.

| Issue | `verify()` | `verify_post_anchor()` |
|---|---|---|
| #443 linkage fork | 1, names both breaks | **0**, "post-anchor clean" |
| #425 duplicate, two entries later | 1 | **0**, "tolerated pre-boundary residual" |
| #430 tainted anchor | 1, `TAINTED Entry #4` | **0**, `OK Entry #4`, boundary **= #4** |

## #443: no linkage pass

`verify()` runs one at `ledger_hash.py:594`, which calls `_report_sequence` and thence `_sequence_breaks` at `:368`, adding each break to the count that sets the return value. `verify_post_anchor` at `:615-725` references neither. Its loop is per-entry only: it recomputes `chain_hash(content, previous)` and compares to the recorded chain. **An entry that chains from the wrong predecessor still satisfies its own arithmetic.**

Reproduced with four entries, each internally self-consistent, where #3 records #2's *content* hash as its previous and #4 records #2's *chain* hash, skipping #3.

## #425: the duplicate check has a one-entry window

The boundary is `max(ok_entries)` at `:682-684`. The duplicate check fires only when `n >= boundary_entry` at `:704-716`. Because the boundary IS the maximum, that condition can hold only while the duplicated number is itself the high-water mark. **In an append-only ledger that is a one-entry window.**

Reproduced with the same fork twice: exit 1 while it is the newest entry, exit 0 once two entries are appended after it, downgraded to `DISCLOSED_PRE_ANCHOR ... tolerated (pre-boundary residual)`. The originating incident the guard was built for -- two branches each appending a different #597, with #598 to #601 landing afterwards -- is the second row. It exits 0.

## #430 is #443 wearing a different hat

This is the scoping fact that matters, and it was established by fixture rather than assumed.

A tainted entry becomes the anchor **because** no linkage check runs. With three entries carrying labeled-but-unrecognised hash values and a fourth whose previous is valid hex unrelated to its predecessor, `verify()` reports `TAINTED Entry #4: depends on failed predecessor #3`. `verify_post_anchor` classifies that same entry `ok` on its own arithmetic, selects it as the boundary, and tolerates everything before it. **The entry `verify()` distrusts is the one that certifies the rest.**

So #430 is not an independent defect. Closing the linkage gap changes which entries can classify `ok`, which changes boundary selection. Whether it closes #430 entirely is the open question the plan must answer rather than assume.

## Reach: what strengthening costs on the real ledger

The measurement that decides whether this can be made strict, run against `docs/META_LEDGER.md` at 757 parsed entries:

```
verify()                     exit 0
verify_post_anchor()         exit 0   (boundary=#759, 10 disclosed pre-anchor)
duplicate entry numbers      none
sequence breaks              0
```

Both missing checks would find nothing here, so adding them leaves this repository's seal gate and skill-entry preflight green. The strengthening is safe to make strict rather than advisory, and no grandfathering of existing state is required.

The 10 disclosed pre-anchor entries (#1-#5, #7, #8, #10, #109, #111) fail per-entry classification and are tolerated as pre-boundary. That tolerance is the feature and must survive: the two modes already disagree in both directions, and this phase should close only the direction where the gate is weaker, not remove the pre-anchor concession.

## Consumers, and why the blast radius is wider than one function

Four call sites, of which two are governance gates:

- `qor/reliability/seal_entry_check.py:149` -- `/qor-substantiate` Step 7.7
- `qor/scripts/governance_health.py:149` -- the preflight every `/qor-*` skill runs
- `qor/cli.py:70` -- `verify-ledger --post-anchor`
- `qor/scripts/ledger_upgrade.py:71` -- upgrade validation

The upgrade path is the one to think hardest about: `ledger_upgrade` validates a rewritten ledger with this function, so a stricter check could reject an upgrade that previously succeeded. Whether that is correct behaviour or a regression is a question for the plan.

## The class this belongs to

A check was pointed at a narrower surface for a good reason, and what it stopped covering was never enumerated. That is the same shape as the phase sealed immediately before this one, where enumerated exception handlers missed cases nobody listed. The remedy there was a rule rather than a list; the question here is whether the remedy is to make `verify_post_anchor` share `verify()`'s passes rather than reimplement a subset of them.
