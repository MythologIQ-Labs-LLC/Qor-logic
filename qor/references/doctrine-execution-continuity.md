# Doctrine: Execution Continuity

**Status**: active (Phase 216; GH #285)

Execution providers perform work. Qor-logic owns the durable identity, claim,
checkpoint, continuation, verification, and authority boundaries around that
work. This doctrine states the gate behavior; the executable checkpoint,
reconstruction, and receipt schemas belong to the upstream execution-continuity
contract and are referenced here by version only.

## The distinction that motivates all of it

A provider stopping because it ran out of budget, context, capacity,
credentials, or environment is not a product failure and not automatically a
reason to escalate to a human. If a valid checkpoint exists and an authorized
successor is permitted, the governed claim continues.

Treating exhaustion as failure discards work that was correct. Treating it as
automatic human escalation discards the machine-resumable path the checkpoint
exists to provide. Both are common, and both are refused here.

## `inconclusive` is not `skip`

`skip` is the Phase 75 disclosed-skip: a prerequisite is absent, the gate
deliberately did not run, and the seal proceeds with that fact recorded.

`inconclusive` is the opposite epistemic position. The gate ran and the
evidence environment denied it a conclusion. It routes to environment repair,
not to seal and not to product remediation.

Collapsing the two is the cheapest available implementation and destroys the
distinction this doctrine exists to create. `qor/gates/schema/validate.schema.json`
keeps `status` at `pass | fail | skip`; the continuity outcome occupies its own
`continuity_outcome` field with `verified | rejected | inconclusive`.

## Exact revision, never ancestry

`intent_lock` verifies by git ancestry, deliberately since Phase 43, so an
implement commit may advance HEAD between capture and verify. It answers "is
this still the work that was audited?"

A verification receipt answers a different question: "was this exact tree
verified?" It compares revisions by string equality. A receipt bound to an
ancestor of the current revision is stale and is rejected, which is exactly the
case ancestry semantics would wrongly accept. The two mechanisms sit beside each
other and neither is folded into the other.

Movement of the target revision after verification invalidates the receipt and
requires re-verification.

## Fail-closed conditions

Rule order is the specification, and fail-closed conditions precede acceptance.
A valid checkpoint never outranks a live-writer conflict or a request for
expanded authority.

| Condition | Outcome | Reason |
|---|---|---|
| Authority request in the forbidden set | `rejected` | `authority-expansion` |
| A live writer holds the claim | `rejected` | `live-writer-conflict` |
| Evidence environment unavailable | `inconclusive` | `environment-unavailable` |
| Self-report offered as verification | `rejected` | `self-report-insufficient` |
| Receipt revision differs from current | `rejected` | `receipt-stale` |
| Checkpoint absent under exhaustion | `rejected` | `checkpoint-absent` |
| Checkpoint malformed or tampered | `rejected` | `checkpoint-malformed` |
| Checkpoint bound to another revision | `rejected` | `revision-mismatch` |

Implemented by `qor/scripts/continuity_gate.py`; the forbidden-authority set is
`merge`, `release`, `deployment`, `credential`, `policy_mutation`. A
continuation buys the right to keep working, never new authority.

## Provider neutrality

No gate outcome may depend on which provider produced the evidence. Named
vendors may appear as optional integrations -- the codex-plugin adversarial path
is one -- but never in core semantics.

The property is tested as outcome-independence rather than name absence: two
evidence bundles differing only in provider identity must return equal
decisions. A grep for vendor names would flag legitimate optional integrations
and would still not test the property that matters.

A provider session URL is evidence metadata. It is never durable authority.

## The pin is asserted, not verified

An operator declares a compatibility version in `.qorlogic/config.json` under
`execution_continuity.contract_version`, read through
`continuity_contract.load_pin`. Absence is a disclosed unpinned state, not an
error.

Qor-logic records which version it declares compatibility with. It cannot check
that a received artifact conforms to that version, because conformance checking
requires holding the upstream schema -- and holding it would create the second
semantic authority this boundary exists to prevent.

That ceiling is structural, not an omission, and it is stated wherever the pin
appears. A declaration that reads like a guarantee while delivering an assertion
is the failure shape catalogued in GH #314.

## Non-duplication, stated as a checkable property

The declaration carries only keys in `continuity_contract.QOR_OWNED_KEYS`, and
only scalars or arrays of scalars. `plan.schema.json` sets
`additionalProperties: false` on the block.

Asserting "no upstream field name appears in Qor-logic" would require
enumerating those names, which requires the schema this repository does not
hold. The inverse property is checkable from inside: we carry only our own keys,
and duplication cannot hide inside a declaration that admits no nested
structure.

## Identity

Checkpoints and receipts reference ledger identity derived via
`entry_id.derive_entry_id(ts, phase, content_hash)`, never sequential entry
numbers. GH #51 established this; GH #316 records a live demonstration, where
`docs/META_LEDGER.md` runs #531 to #533 because #532 was allocated in an
abandoned session and never committed.

## Separation of acceptances

Implementation verification, merge authorization, release authorization, and
deployment acceptance are four decisions, not one. A `verified` continuity
outcome speaks only to the first.
