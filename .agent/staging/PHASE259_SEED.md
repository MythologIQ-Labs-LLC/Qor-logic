# Phase 259 seed: seal binding

Deferred out of Phase 258 by operator decision 2026-09-04, after the Phase 258
iteration-2 VETO (META_LEDGER entry #727). These are audit findings V-6, V-9,
and V-10 in that entry, carried forward rather than fixed in place.

## Scope

The seal-binding surface, entire. Phase 258 ships no ledger parsing.

- `adr-status-stale` and `adr-phase-unsealed` finding kinds
- `meta_ledger_walker.py` gains a plan field
- the union predicate over four label dialects plus body binding
- the consumer-contract fixture amendment

## Established facts (measured, do not re-derive)

Label dialects observed in `docs/META_LEDGER.md`:

1. `SESSION SEAL -- Phase N` (ASCII double hyphen), 204 entries
2. `SESSION SEAL <em-dash> Phase N`, 20 entries
3. `SESSION RECONCILIATION SEAL -- Phase 60`, entry #196 at `:7277`
4. `SUBSTANTIATE <em-dash> Phase 12`, entry #24 at `:723`
5. `SEAL` bare, in `qor/fixtures/consumer-contract/meta_ledger/supported.md:45`

Binding coverage over the 240 phases holding a plan file on disk:

| binding | count |
|---|---|
| both label and plan-citation | 183 |
| label only | 40 |
| plan-citation only | 1 (Phase 63) |
| neither | 16 (phases 2-11, 23, 39, 51, 61, 62, 258) |

Field coverage over the 227 `SESSION SEAL` headings: 225 carry a plan filename,
184 via `**Plan**:` and 41 via `**Target**:`, partitioning cleanly with no entry
carrying both. The 2 misses are entries #8 (`:204`) and #10 (`:260`), which
predate phase numbering and bind to no phase by any method; the doctrine should
declare them out of scope rather than let the detector report them.

Phase 63 is the dispositive case: it sealed at v0.46.0 inside entry #196, whose
label names Phase 60 while its body names phase63 (`:7281`, `:7285`, `:7332`).
No entry label anywhere contains "Phase 63". The mirror sits on that same entry,
so a body-only predicate binds 63 and loses 60. The union is required on one
entry, not merely across the corpus.

## Locked constraints for the walker change

Measured, not estimated. `LedgerRecord` has exactly one construction site,
`meta_ledger_walker.py:63`, and it is all-keyword. Consumers are `_is_audit_class`
(`:87-93`), `tests/test_meta_ledger_walker.py`, `tests/test_consumer_contract_fixtures.py`,
and a `MANIFEST.json` producer reference. All use attribute access; none constructs
positionally; no `astuple`, `asdict`, `fields`, `replace`, or tuple unpacking appears
anywhere in the repository.

1. Append the field with a default: `plan: str | None = None`, after `ts`. The
   existing six carry no defaults on a frozen dataclass, so a mid-list insertion
   without a default is a `TypeError` at definition time.
2. Keep the `**Target**:` fallback inside the new field's resolution and never in
   `_TARGET`, or `tests/test_consumer_contract_fixtures.py:93`
   (`assert all(r.target is not None for r in audit_like)`) fails.

## Open decision for the plan

`qor/fixtures/consumer-contract/meta_ledger/supported.md` is the published fixture
for external consumers and contains zero `**Plan**:` lines; its seal entry is
labelled `### Entry #3: SEAL`. Either bare `SEAL` joins the alternation, or the
fixture is amended. If the fixture changes, that is a consumer-contract change
owing its own declaration, not a test edit.

## Vocabulary note

`docs/META_LEDGER.md` already carries a `**Phase**:` field whose value is a
lifecycle stage rather than a number (`:207`, `:263`, value `SUBSTANTIATE`).
Phase 258 introduces `**Phase:** NNN` in decision records. Different files, no
technical conflict, but two governance artifacts will carry a same-named field
with incompatible value domains. The doctrine should say so explicitly.

## Added after the iteration-2 VETO, from two independent reviewers

Three further facts, each verified by execution in this repository.

### A fifth label dialect, separator-less

`docs/META_LEDGER.md:15336` -> `### Entry #499: SESSION SEAL Phase 205: CodeQL security baseline`

One occurrence. Any predicate making the separator mandatory misses it. Phase 205
is rescued only because entries #500 and #501 re-seal it with the `--` form, so
the dialect count is five, not three, and the rescue is luck rather than design.

### A text scan over this ledger cannot distinguish a seal from narrative about one

The predicate scans the whole file rather than entry headings. Executed for n=12,
it matches twice:

- `docs/META_LEDGER.md:723` -- the real seal, entry #24
- `docs/META_LEDGER.md:21010` -- prose inside the Phase 258 iteration-1 VETO entry,
  which quotes the seal string as evidence

The governance record written to document the predicate's weakness is itself
matched by the predicate. Harmless in this instance because Phase 12 is genuinely
sealed, but the general case is not harmless: any future ledger narrative quoting
a seal string for an unsealed phase silently marks it sealed. The binding must be
anchored to entry headings and their own bodies, not to a whole-file regex.
Pre-existing at `governance_index.py:143`; not introduced by Phase 258.

### The walker parses a verdict for 18% of modern seals

Executed against the live ledger: 227 `SESSION SEAL` records, 42 with a parsed
verdict. Entry #724, the most recent seal, returns `verdict=None`.

`_VERDICT` (`meta_ledger_walker.py:21`) requires a line-initial `**Verdict**`.
The file carries 256 line-initial occurrences but the modern seal nests it as
`**Decision**: **Verdict**`, which occurs 59 times and does not match.

Consequences:

1. `_is_audit_class` (`:87-93`) returns False when `verdict` is None, so
   `last_n_audit_entries` excludes essentially every modern SESSION SEAL. A
   pre-existing defect of the walker, not of this phase, but the phase leans on
   the walker's authority and should not do so silently.
2. The detector must key on the label and the plan filename only, never on
   `verdict`. This deserves its own locked decision.
3. It softens the consumer-fixture concern rather than resolving it: a modern
   dialect entry added to `supported.md` parses to `verdict=None`, so it never
   enters `audit_like` and `tests/test_consumer_contract_fixtures.py:93` does not
   fail. That is worse than a red test, because the fixture would then hold a
   modern seal the suite silently declines to examine.

### Fixture amendment required

`qor/fixtures/consumer-contract/meta_ledger/supported.md` declares
`<!-- qor:meta-ledger-schema=1 -->` at `:2`, which `MANIFEST.json:13` confirms is
current, while its seal entry uses the pre-federation dialect: `### Entry #3: SEAL`
(`:45`), `**Phase**: SUBSTANTIATE` (`:48`), `**Type**: SEAL` (`:49`), `**Target**:`
(`:50`). The fixture certifies the current schema against a field dialect the live
ledger abandoned around entry #198.

Add one modern-dialect entry carrying a `SESSION SEAL -- Phase <N>` heading, a
`**Plan**:` field, and no `**Target**:`. Amend `MANIFEST.json:9`'s note, which
currently claims "well-formed AUDIT/SEAL entries" without naming dialect coverage.
This is a published consumer-contract change and belongs in Locked Decisions, not
in an implementation diff.
