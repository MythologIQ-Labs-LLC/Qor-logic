# Plan: ledger-commitment integrity and conditional terms declaration (GH #408, #414)

**change_class**: feature

**doc_tier**: standard

**terms**: []

No new domain vocabulary. `Ledger commitment` describes the existing
content-hash binding rather than naming a new concept.

**boundaries**:
- limitations: [enforcement covers artifacts named by a ledger entry AND touched in the session under seal, read from the implement gate's `files_touched`; an artifact edited outside a governed session is out of reach of any seal-time check and stays a `/qor-validate` concern]
- non_goals: [does not retro-verify every historical commitment in the 691-entry ledger at every seal -- that is a `/qor-validate` sweep, not a seal gate, and would make seal cost grow with ledger length; does not change the chain-hash math, which correctly commits to recorded values rather than live bytes]
- exclusions: [no change to `hash_guard`'s fail-closed validation of the three chain fields]

## Problem

### GH #408 -- a ledger commitment can go stale and no gate notices

A ledger entry binds an artifact by content hash. When a later phase corrects
that artifact -- which is exactly what an audit VETO is for -- the entry's
commitment silently stops describing the file.

Chain integrity is unaffected and correctly so: chain hashes commit to the
recorded hex string, not to live bytes, so `verify-ledger` passes and reports
nothing wrong. That is the gap. The chain proves entries were not reordered or
edited; it proves nothing about whether the artifacts they name still say what
they said.

`/qor-substantiate` Step 3's reality audit checks that planned files exist and
match the blueprint. It does not recompute the content hashes earlier entries
committed for artifacts touched during the session.

The convention that closes this is already practiced here and codified nowhere:
`docs/META_LEDGER.md` holds six `AMENDMENT` entries recording superseded
hashes, and `grep AMENDMENT qor/references/*.md` returns nothing. A consumer has
no way to learn the convention exists.

### GH #414 -- the omission route into a vacuous glossary check

GH #394 closed the *alias* route: the schema now rejects `terms_introduced`.
The *omission* route stays open. `terms` is absent from `plan.schema.json`'s
`required`, so an artifact declaring neither key validates cleanly,
`plan.get("terms", [])` returns `[]`, and `check_glossary` iterates an empty
list -- the same end state, reached by omitting the field rather than
misnaming it.

`terms` cannot simply become unconditionally required: a plan introducing no
vocabulary legitimately has nothing to declare, and forcing every plan to carry
the key produces reflexive empty declarations that carry no signal. The
distinction that matters is between *declared empty* and *never declared* --
the same shape as GH #405, where "no rows" and "rows I could not read" were
indistinguishable.

## Fix

### GH #408

1. `qor/references/doctrine-ledger-commitment.md` (**new**): codify the
   convention this repository already practices. When a phase corrects an
   artifact a ledger entry has committed by content hash, it MUST append an
   `AMENDMENT` entry recording the superseded hash, the new hash, and the
   reason, before the next gate artifact is written.
2. `qor/scripts/ledger_commitment.py` (**new**): parse the ledger into
   `(artifact_path -> latest committed hash)`, where an `AMENDMENT` carrying a
   `**Superseded Content Hash**` supersedes the entry it amends. Expose
   `stale_commitments(repo_root, touched)` returning the artifacts whose latest
   committed hash no longer matches the file.
3. `/qor-substantiate` Step 3: run the check over the implement gate's
   `files_touched`. An undisclosed mismatch ABORTs the seal. A mismatch whose
   latest commitment is an `AMENDMENT` recording the current hash passes,
   because the drift was disclosed -- which is what makes the doctrine
   self-policing rather than an instruction someone has to remember mid-VETO.
4. **Self-application.** Entry #682's `**Superseded Content Hash**` records a
   truncated prefix (`66347652`) rather than a full digest, written by this
   session. The parser must reject a malformed superseded hash rather than
   silently treating the entry as an amendment, and this phase appends a
   correction amendment recording the full digest. A doctrine whose own
   history violates it is not yet load-bearing.

### GH #414

5. `qor/scripts/doc_integrity.py`: `run_all_checks_from_plan` raises when
   `doc_tier` is `standard` or `system` and the plan declares no `terms` key at
   all. An explicit `[]` satisfies it and means "this phase introduces no
   vocabulary" -- a claim the author made, rather than an absence that could
   equally mean they forgot. `minimal` and `legacy` stay exempt, matching the
   existing tier semantics.

   **Not the schema** (tribunal ground V-1, entry #692). GH #414's suggested
   direction proposed a `doc_tier` `if/then` in `plan.schema.json` and said it
   would need no new Python. That would re-create the Phase 248 release blocker
   at thirty-six times the scale: 109 already-sealed plan artifacts carry
   `doc_tier` standard or system with no `terms` key, and Phase 248's
   `sealed_history` exemption strips only the top-level `not` clause
   (`validate_gate_artifact.py:102`), so an `if/then` reaches sealed history
   unmodified and the fail-closed `gate_chain_completeness` aborts.

   Widening `sealed_history` to strip `if`/`then`/`else` would also work and
   would generalize, but it enlarges an exemption in the middle of a phase whose
   subject is something else, and each keyword added makes the sealed-history
   check weaker in a way that is hard to audit later. The requirement governs
   how a plan is *authored* rather than what shape a plan artifact must always
   have had, and `run_all_checks_from_plan` reads only the current session's
   plan -- so enforcing it there never touches sealed history and needs no
   exemption at all. The issue's diagnosis was right; its proposed remedy was
   not.

### Implementation divergences (amended; re-audited before seal)

- **A duplicate insertion was caught and removed.** The fix-5 check first landed
  in BOTH `run_all_checks_from_plan` and `render_drift_section`. The latter is
  the advisory drift renderer that `/qor-audit` calls non-blockingly, and making
  it raise would have converted an advisory into a hard failure. Only
  `run_all_checks_from_plan` enforces.
- **`_TIERS` and `_TIER_REQUIREMENTS` moved to `layout_paths`.** Adding fix 5
  breached `doc_integrity`'s 250-line Razor cap again. The tier table's natural
  home is now `layout_paths`, which already computed the glossary row from it --
  the move also removes the circular import the Phase 250 placement forced.
  `doc_integrity` is 238 lines.
- **The seal-skill wiring is a pointer, not prose.** `/qor-substantiate` Step 3
  gains one bullet citing `references/seal-gate-ladder.md`, where the contract
  lives, per the progressive-disclosure rule for governance skills.
- **`qor-substantiate/SKILL.md` normalized to LF.** Its size guard uses
  `os.path.getsize`, so CRLF line endings inflated the measurement by 678 bytes
  and reported a false breach.

- **The gate caught a defect in its own parser.** Run against this phase,
  `ledger_commitment` reported the plan as stale. The cause was real: a GATE
  TRIBUNAL entry cites `**Plan**:` but its `**Content Hash**` binds the AUDIT
  REPORT, so the parser was comparing the plan's bytes against the report's
  digest. Left in, it would have produced a false ABORT at every seal that
  follows an audit -- which is every seal. Fixed by restricting commitment
  parsing to the entry kinds whose content hash actually binds the artifact they
  name (`RESEARCH BRIEF`, `IMPLEMENTATION`, `SESSION SEAL`, `AMENDMENT`), with
  `test_gate_tribunal_plan_citation_is_not_a_commitment` as red-proved
  regression coverage. Recorded as regression coverage rather than TDD, because
  the defect was found by running the gate rather than by writing the test
  first.
- **And a category error in this phase's own amendment.** Entry #694 first
  recorded entry #693's *chain* hash as the plan's superseded *content* hash.
  Retracted rather than substituted, for the same reason as entry #682: the
  prior value was never computed, so inventing one would look correct without
  being true.

**Observation for the record, not a defect in this phase**: after this addition
`qor-substantiate/SKILL.md` sits at 2,702 bytes of slack against a 2,700-byte
floor. The next gate that needs a line in that file will require a real
progressive-disclosure extraction rather than compaction. Step 6.8 is the
obvious candidate but is pinned inline by two dedicated test files, so the
extraction is its own phase. Recorded in the Shadow Genome rather than filed,
because it is a known constraint with a known remedy rather than an open defect.

## Tests (written first)

- `tests/test_ledger_commitment.py::test_latest_commitment_wins_over_the_superseded_one`
  -- an artifact committed by an entry and re-committed by a later AMENDMENT
  resolves to the amendment's hash.
- `::test_stale_commitment_is_reported_when_the_file_changed`
  -- an artifact whose file no longer hashes to its latest commitment is
  returned by `stale_commitments`. Red before fix 2.
- `::test_disclosed_amendment_clears_the_staleness`
  -- the same artifact, after an AMENDMENT recording the current hash, is not
  reported. This is the pair that makes disclosure meaningful rather than
  asserted.
- `::test_untouched_artifacts_are_not_inspected`
  -- an artifact stale but absent from `touched` is not reported, pinning the
  declared limitation so the check does not silently become a full-ledger
  sweep whose cost grows with ledger length.
- `::test_malformed_superseded_hash_is_rejected`
  -- an AMENDMENT whose `Superseded Content Hash` is not a full 64-hex digest
  raises rather than being treated as a valid supersession. Red before fix 4;
  entry #682 in this repository's own ledger is the case that motivated it.
- `::test_the_live_ledger_has_no_undisclosed_stale_commitments`
  -- run the check against this repository's real ledger over the artifacts of
  the current session. The anti-recurrence binding: the doctrine's first
  subject is the repository that wrote it.
- `tests/test_doc_integrity.py::test_standard_tier_requires_a_terms_declaration`
  -- `run_all_checks_from_plan` raises for a `doc_tier: standard` plan with no
  `terms` key. Red before fix 5.
- `::test_sealed_plan_artifacts_still_validate_against_the_schema`
  -- every `.qor/gates/**/plan*.json` in this repository still passes
  `validate_one(..., sealed_history=True)`. The permanent guard against fix 5
  migrating back into the schema, where it would abort the seal on 109 sealed
  artifacts. Passes today; it exists to fail loudly if anyone moves it.
- `tests/test_doc_integrity.py::test_standard_tier_accepts_an_explicit_empty_terms`
  -- `terms: []` satisfies the requirement, so declaring no vocabulary stays
  possible and stays a claim.
- `tests/test_doc_integrity.py::test_minimal_tier_does_not_require_terms`
  -- the exemption holds, so the rule does not become the unconditional
  requirement the issue rejects.

Every test invokes the unit and asserts on its return value or raised error.

## Validation

- `python -m pytest tests/test_ledger_commitment.py tests/test_doc_integrity.py -q` -- run twice for determinism
- `python -m pytest -q` (full suite)
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
- `python -m qor.scripts.publication_boundary_lint`
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` -- the correction amendment must not disturb the chain

## CI Commands

- `python -m pytest -q`
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
