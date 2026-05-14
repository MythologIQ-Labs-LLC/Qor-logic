# Plan: Phase 76 - META_LEDGER federation entry IDs + duplicate detection V1 (GH #51)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #51 -- META_LEDGER sequential entry numbering incompatible with concurrent federation workers. Phase 78 ideation (session `2026-05-14T2235-830921`) selected Option 1 (content-addressable IDs + topological sort) but flagged retroactive renumbering of past entries as forbidden.

**terms_introduced**:
- term: content-addressable entry ID
  home: qor/scripts/entry_id.py
- term: SG-ConcurrentLedgerRace-A
  home: qor/references/doctrine-shadow-genome-countermeasures.md

**high_risk_target**: true

**impact_assessment**:
  purpose: META_LEDGER concurrent-federation safety. Add forward-only content-addressable entry IDs + previous_hash uniqueness detection so concurrent federation workers cannot silently produce duplicate-numbered entries that corrupt the audit-readable ledger structure.
  affected_stakeholders:
    - Federation operators running concurrent SDLC cycles
    - Downstream auditors reading sealed META_LEDGER entries
    - Tools that parse the ledger (seal_entry_check, ledger_hash.verify, badge_currency)
    - Qor-logic maintainers
  identified_risks:
    - "RISK-1: Content-addressable ID collision corrupts new-entry identification"
    - "RISK-2: Forward-only design means existing #16a/b, #17a/b, #18a/b duplicates remain unfixed; observed-but-unresolved state"
    - "RISK-3: previous_hash uniqueness check produces false-positive on legitimate fork-merge patterns"
    - "RISK-4: Schema extension breaks existing META_LEDGER parsers in consumer workspaces"
    - "RISK-5: ID format drift across phases if helper signature changes"
  mitigations:
    - "RISK-1 mitigation: SHA256[:12] = 48-bit space; collision-resistant for any realistic ledger size. Test fixture covers synthetic-collision attempts. Backstop: full 64-char hash available via opt-in flag."
    - "RISK-2 mitigation: V1 EXPLICITLY DEFERS reconciliation of past duplicates to V2 with operator authorization. Forbidden-interpretation guard in plan: retroactive renumbering of Entries #1-#207 is prohibited."
    - "RISK-3 mitigation: previous_hash uniqueness check fires only at substantiate-time inside a single session's seal cycle; cross-session race detection is operator-discretion only."
    - "RISK-4 mitigation: Content-addressable ID is an ADDITIVE field on new entries; existing entry-header format (`### Entry #N: ...`) is preserved verbatim. Past parsers continue to work; only new parsers can read the additional field."
    - "RISK-5 mitigation: ID format anchored in qor/scripts/entry_id.py with tests asserting backward-compatibility of helper signature."
  residual_risks:
    - "RISK-2 (deferred): past duplicate entries #16a/b, #17a/b, #18a/b remain in the ledger with their duplicate numbering. Documented in SG-ConcurrentLedgerRace-A as known-unresolved instance pending V2 operator-authorized reconciliation."

**boundaries**:
- limitations:
  - V1 ships content-addressable IDs as **forward-only**: new entries (Phase 76+) carry an additional `Entry ID:` field; past entries (#1-#207) are unchanged. The display format becomes `### Entry #N: ...` followed by `**Entry ID**: \`<12-char-hex>\`` line in the entry body.
  - V1 ships `previous_hash` uniqueness detection as a `seal_entry_check` extension. Existing single-session race detection runs at `/qor-substantiate` Step 7.7 (no new step).
  - V1 does NOT renumber existing duplicate Entries #16a/b, #17a/b, #18a/b. Reconciliation pass is operator-authorized V2 work.
  - The 12-character ID truncation provides 48 bits of collision resistance (~10^14 entries before 50% birthday-collision probability). Operator can opt into 64-char full hash via env var if their federation scales past 10^7 entries.
- non_goals:
  - NOT building a distributed-consensus protocol (Raft / Paxos / Tendermint).
  - NOT introducing session-scoped ledger segments (ideation Option 2 was rejected).
  - NOT replacing sequential `Entry #N` labels with content-addressable IDs as primary identifier.
- exclusions:
  - No changes to `chain_hash` / `content_hash` algorithms or the Merkle chain semantics.
  - No changes to past Entries #1-#207 (forbidden by plan + doctrine).
  - No new `/qor-substantiate` steps (extension to existing Step 7.7 only).
- forbidden_interpretations:
  - This is NOT permission to renumber past sealed entries. Retroactive renumbering of Entries #1-#207 is structurally forbidden by SG-ConcurrentLedgerRace-A doctrine entry; any such commit is automatically reverted.
  - Content-addressable IDs are ADDITIVE, not REPLACEMENT. `Entry #N` remains the canonical human-readable identifier; the new ID is supplementary.

## Open Questions

None. Ideation packet `2026-05-14T2235-830921` decided Option 1 with explicit forbidden-interpretation guards.

## Phase 1: Content-addressable ID helper

### Affected Files

- `qor/scripts/entry_id.py` - NEW (~60 LOC). Pure-function module: `derive_entry_id(ts: str, phase: str, content_hash: str, length: int = 12) -> str` returns SHA256(f"{ts}|{phase}|{content_hash}")[:length]. Tests cover determinism, collision-resistance characterization, env-var override for full-hash mode.
- `tests/test_entry_id_helper.py` - NEW. 3 tests: same inputs produce same ID (determinism); different inputs produce different IDs (collision-resistance characterization on small synthetic dataset); 64-char full-hash mode via env var.

### Changes

Pure-function helper isolated from ledger I/O. The derivation formula is anchored here so any consumer (ledger writer, seal_entry_check, test fixtures) computes the same ID from the same inputs.

### Unit Tests

- `tests/test_entry_id_helper.py::test_derive_entry_id_deterministic` - calls `derive_entry_id("2026-05-14T22:00:00Z", "substantiate", "abc...64hex")` twice with the same inputs; asserts byte-identical output across both invocations.
- `tests/test_entry_id_helper.py::test_derive_entry_id_distinguishes_inputs` - generates 1000 synthetic (ts, phase, content_hash) triples with single-byte differences; asserts all 1000 produced unique 12-char IDs (no collisions on the small synthetic dataset; characterizes the function's distinguishing behavior).
- `tests/test_entry_id_helper.py::test_derive_entry_id_full_hash_mode_via_env_var` - sets `QOR_ENTRY_ID_FULL_HASH=1` via monkeypatch; asserts `derive_entry_id` returns a 64-char hex string instead of 12-char.

## Phase 2: previous_hash uniqueness detection at seal_entry_check

### Affected Files

- `qor/reliability/seal_entry_check.py` - extend `check()` (or add a new `check_previous_hash_uniqueness(ledger_path)` function) to walk all entries, group by `previous_hash`, and report any `previous_hash` value claimed by more than one entry. Single-session races (the GH #51 failure signature) produce two entries claiming the same `previous_hash`.
- `tests/test_seal_entry_check_previous_hash_uniqueness.py` - NEW. 3 tests: synthetic ledger with unique previous_hash values returns ok=True; synthetic ledger with intentional duplicate previous_hash returns ok=False with the duplicate entry numbers named; the canonical META_LEDGER.md (Phase 76 implementation state, past Entries #1-#207) returns ok=True (no detected concurrent-race signature).

### Changes

`seal_entry_check.py` gains the uniqueness check. Invoked at `/qor-substantiate` Step 7.7 as part of the existing post-seal verification. No new step; the existing `check()` function returns a `SealEntryResult(ok, errors)` where `errors` now includes any duplicate-previous_hash findings.

### Unit Tests

- `tests/test_seal_entry_check_previous_hash_uniqueness.py::test_unique_previous_hash_passes` - synthetic ledger fixture with 5 entries, each with distinct previous_hash; asserts `check_previous_hash_uniqueness(ledger_path).ok is True`.
- `tests/test_seal_entry_check_previous_hash_uniqueness.py::test_duplicate_previous_hash_fails_with_entry_names` - synthetic ledger fixture where Entry #3 and Entry #4 both claim the same previous_hash (the GH #51 race signature); asserts `check_previous_hash_uniqueness` returns `ok=False` AND `errors` contains both entry numbers (3 and 4) AND the duplicated hash prefix.
- `tests/test_seal_entry_check_previous_hash_uniqueness.py::test_canonical_meta_ledger_has_no_race_signature` - reads the live `docs/META_LEDGER.md`; asserts `check_previous_hash_uniqueness(...)` returns `ok=True` (the past duplicate-numbering of #16a/b etc. was on sequential numbers, not previous_hash; this regression-protects the canonical ledger).

## Phase 3: SKILL.md prose + ledger header format + SG doctrine entry

### Affected Files

- `qor/skills/governance/qor-substantiate/SKILL.md` - extend Step 7 (Final Merkle Seal) prose to require the seal entry body include an `**Entry ID**: \`<12-char-hex>\`` line derived via `entry_id.derive_entry_id`. Extend Step 7.7 (Post-seal verification) to reference the new previous_hash uniqueness check.
- `qor/references/doctrine-shadow-genome-countermeasures.md` - new `SG-ConcurrentLedgerRace-A` entry with the originating recurrence (Entry #16a/b, #17a/b, #18a/b in cross-workspace federation) + forward-only design + retroactive-renumber prohibition.
- `tests/test_qor_substantiate_entry_id_prose.py` - NEW. 2 tests: Step 7 prose names `entry_id.derive_entry_id` + `**Entry ID**:` format; Step 7.7 prose references previous_hash uniqueness check.
- `tests/test_doctrine_sg_concurrent_ledger_race_a.py` - NEW. 2 tests: doctrine entry exists with originating recurrence (Entry #16/17/18 duplicates) + countermeasure cross-reference; SG entry body forbids retroactive renumbering of past entries.

### Changes

Step 7 prose: "Each new SESSION SEAL entry body MUST include an `**Entry ID**: \`<12-char-hex>\`` line derived via `entry_id.derive_entry_id(ts, phase, content_hash)`. The Entry ID is content-addressable and survives concurrent federation append because it does not require entry-number-allocation coordination."

Step 7.7 prose: "Phase 76 wiring: the previous_hash uniqueness check is included in `check()`. Two entries claiming the same `previous_hash` signal a concurrent federation race; the check raises `SealEntryResult(ok=False, errors=...)` and the operator must reconcile."

SG-ConcurrentLedgerRace-A: catalogues the Entry #16a/b, #17a/b, #18a/b duplicate-numbering recurrence; describes the V1 forward-only countermeasure (content-addressable IDs + previous_hash uniqueness detection); explicitly forbids retroactive renumbering of past sealed entries.

### Unit Tests

- `tests/test_qor_substantiate_entry_id_prose.py::test_step_7_names_entry_id_derivation` - asserts qor-substantiate SKILL.md Step 7 region contains `entry_id.derive_entry_id` reference AND the `**Entry ID**:` body-line format.
- `tests/test_qor_substantiate_entry_id_prose.py::test_step_7_7_names_previous_hash_uniqueness_check` - asserts qor-substantiate SKILL.md Step 7.7 region contains `previous_hash uniqueness` phrase AND cross-references SG-ConcurrentLedgerRace-A.
- `tests/test_doctrine_sg_concurrent_ledger_race_a.py::test_doctrine_carries_sg_concurrent_ledger_race_a` - reads doctrine, asserts SG entry exists with `Entry #16` or `#17` or `#18` originating-recurrence reference AND `previous_hash uniqueness` countermeasure language.
- `tests/test_doctrine_sg_concurrent_ledger_race_a.py::test_doctrine_forbids_retroactive_renumber` - asserts SG entry body contains explicit prohibition of retroactive renumbering of past Entries (#1-#207 or "past sealed entries" language).

## CI Commands

- `python -m pytest tests/test_entry_id_helper.py tests/test_seal_entry_check_previous_hash_uniqueness.py tests/test_qor_substantiate_entry_id_prose.py tests/test_doctrine_sg_concurrent_ledger_race_a.py -v` - validates Phase 76 tests.
- `python -m qor.scripts.dist_compile` - regenerates dist variants.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase76-meta-ledger-federation.md` - self-application.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite.
