# Doctrine: Ledger commitment

A META_LEDGER entry that records a `**Content Hash**` for an artifact makes a
claim about that artifact's bytes at that moment. This doctrine governs what
happens when the artifact later changes.

Origin: GH #408, reported from a consumer workspace whose research brief was
corrected under audit pressure. The correction was right and the audit worked;
what failed is that nothing recorded the change, and no gate noticed.

## Why the chain does not cover this

Chain hashes commit to the recorded hex string, not to live bytes. So
`verify-ledger` passes and correctly reports nothing wrong: the chain proves
entries were not reordered or edited. It proves nothing about whether the
artifacts they name still say what they said.

This is a property of the chain, not a defect in it. A chain that re-read every
committed artifact would fail whenever any file legitimately moved on, which
would make it useless as a tamper record.

## The rule

When a phase corrects an artifact that a ledger entry has already committed by
content hash, it MUST append an `AMENDMENT` entry before the next gate artifact
is written. The amendment records:

- `**Amends**: Entry #<N>` -- the entry whose commitment is superseded.
- `**Superseded Content Hash**: <64-hex>` -- the value that no longer describes
  the file. A full lowercase digest; a fragment is not a supersession.
- `**Content Hash**: <64-hex>` -- the artifact's current bytes.
- A decision body stating *why* the artifact changed.

An amendment is a later commitment for the same artifact, so the most recent
one is authoritative.

## Enforcement

`/qor-substantiate` Step 3 runs `ledger_commitment.stale_commitments` over the
implement gate's `files_touched`. An artifact whose latest commitment no longer
matches its bytes ABORTs the seal. An artifact whose latest commitment is an
amendment recording the current bytes passes, because the drift was disclosed.

That pairing is what makes this self-policing rather than an instruction
someone has to remember. A correction made under audit pressure is exactly when
a manual bookkeeping step gets skipped, so the gate has to be the thing that
remembers.

## Scope, and what stays out of it

Enforcement covers artifacts named by a ledger entry **and** touched in the
session under seal. Two deliberate exclusions:

- An artifact edited outside a governed session is beyond any seal-time check
  and remains a `/qor-validate` concern.
- The seal does not re-verify every historical commitment. A full sweep would
  make seal cost grow with ledger length, and the seal's job is this phase.

## Malformed commitments

A `**Superseded Content Hash**` that is present but not a full 64-character
lowercase digest raises rather than being read as a valid supersession.
Accepting a fragment would let a malformed amendment silently clear a real
staleness -- the amendment would appear to disclose a change it does not
actually pin.

Where such a value was already written and cannot be reconstructed from a
computed digest, the honest repair is to retract the field rather than
substitute a plausible one. Entry #682 of this repository's ledger is the
worked example: it recorded an eight-character fragment, and Phase 251 retracted
it rather than inventing a value that would have looked correct.

## Relationship to the chain gates

This doctrine sits beside chain verification rather than inside it.
`ledger_hash.verify` answers "was this record tampered with"; ledger-commitment
integrity answers "does this record still describe reality". A ledger can be
perfectly intact and entirely stale, which is the state GH #408 found.
