# Plan: Phase 193 - Canonical ledger emit API + retroactive attestation + structured health (GH #278)

**change_class**: feature

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-ledger-emit-api-2026-07-13.md (ledger entry #490, session `2026-07-13T1815-6e2843`); GH #278 (carrying #271's emit-API remainder, #268's structured-output remainder, and the operator-directed retroactive-normalization requirement).

## Locked Decisions

- **LD-1: one typed renderer; render must round-trip the verifier's parser.**
  `grep -nE 'def _resolve_recorded' qor/scripts/ledger_hash.py -> 306` (the parse contract); `grep -nE 'def content_hash|def chain_hash' -> 25,39` (the hash primitives); `grep -nE 'def derive_entry_id' qor/scripts/entry_id.py -> 16`. New `qor/scripts/ledger_emit.py`: `LedgerEntry` dataclass (number, title, fields: ordered mapping, body) + `render(entry) -> str` producing exactly the canonical markup + `append(ledger_path, entry) -> tuple[str, str]` that reads the tail chain hash, computes the content hash over the entry's bound target (or its body when self-bound), computes the chain hash, injects the three hash fields, ASCII-asserts via `assert_sealable_text`, and inserts before the chain-integrity tail marker. The round-trip test is the contract: render -> _resolve_recorded parses -> verify accepts.
- **LD-2: retroactive normalization by attestation, never by rewriting.**
  Retro-chaining is chain-impossible (the first verifiable entry's recorded Previous Hash is historical; editing it violates the operator acceptance). New `qor/scripts/ledger_attest_legacy.py`: `collect_unverifiable(ledger_path) -> [(num, digest12)]` (exactly the entries verify's skip path takes: sub-cutoff AND _resolve_recorded None; digest = LF-normalized sha256 of the entry body, truncated 12); `build_attestation_entry(...)` -> a `MIGRATION ATTESTATION` LedgerEntry whose body lists `#<num>=<digest12>` per line; CLI `--ledger PATH [--write]` emits it THROUGH ledger_emit (self-application). verify extension (`grep -nE '_attested_reconciled' qor/scripts/ledger_hash.py -> 293` is the precedent): parse `MIGRATION ATTESTATION` entries' `**Attested Entries**` blocks; a skipped-band entry whose recomputed digest matches prints `OK Entry #N: attested by migration entry #M` and does NOT count as skipped; a digest MISMATCH is a FAIL (tamper-evidence backwards). Acceptance: `ledger_hash verify docs/META_LEDGER.md` reports zero skipped on the live ledger after this cycle's migration.
- **LD-3: structured health output composes with the snapshot.**
  `governance_health --format json`: findings as objects (path, reason, legal_next, state) plus profile + overall; exit semantics unchanged; the Phase 191 snapshot keeps its ladder-level health section (no duplication -- the snapshot embeds verdicts, this exposes findings detail).
- **LD-4: the live migration is this cycle's seal act.**
  The real 32-entry attestation entry is emitted through the new API inside this session's ceremony, exactly as Phase 192's fold was -- the retroactive requirement is met by the sealed artifact, not by a promise.

## Phase 1: Typed renderer (TDD first)

### Affected Files

- tests/test_ledger_emit.py - NEW (red first)
- qor/scripts/ledger_emit.py - NEW per LD-1

### Unit Tests

- tests/test_ledger_emit.py - test_render_round_trips_verifier_parser: render a fields+body entry with hash trio -> _resolve_recorded returns exactly the three values (red today)
- tests/test_ledger_emit.py - test_append_links_chain_and_verifies: append two entries to a fixture ledger -> ledger_hash verify exits 0 with both OK and zero skips (red today)
- tests/test_ledger_emit.py - test_append_rejects_non_ascii_body: assert_sealable_text propagates (the ASCII seal rule holds at the API)
- tests/test_ledger_emit.py - test_append_preserves_tail_marker: the chain-integrity tail lines remain after the inserted entry

## Phase 2: Legacy attestation (TDD first)

### Affected Files

- tests/test_ledger_attest_legacy.py - NEW (red first)
- qor/scripts/ledger_attest_legacy.py - NEW per LD-2
- qor/scripts/ledger_hash.py - verify extension per LD-2

### Unit Tests

- tests/test_ledger_attest_legacy.py - test_collect_matches_verify_skip_set: on a fixture with 3 pre-cutoff unmarked entries, collect returns exactly those numbers (red today)
- tests/test_ledger_attest_legacy.py - test_attestation_clears_skips: emit the migration entry -> verify exits 0, prints attested lines, reports zero skipped (red today)
- tests/test_ledger_attest_legacy.py - test_tampered_legacy_body_fails_after_attestation: edit an attested body -> verify FAILs with the digest mismatch (the backwards tamper-evidence)
- tests/test_ledger_attest_legacy.py - test_attestation_entry_itself_chain_verifies: the migration entry links off the prior tail and verifies like any modern entry
- tests/test_ledger_attest_legacy.py - test_live_ledger_zero_skips: docs/META_LEDGER.md verify output contains no skip summary line (red until the LD-4 live migration lands in this session's seal; asserted green in the post-seal suite)

## Phase 3: Structured health output (TDD first)

### Affected Files

- tests/test_governance_health_json.py - NEW (red first)
- qor/scripts/governance_health.py - --format json per LD-3

### Unit Tests

- tests/test_governance_health_json.py - test_json_findings_shape: on a fixture repo, --format json emits one JSON object with profile, overall, findings[] carrying path/reason/legal_next/state (red today)
- tests/test_governance_health_json.py - test_exit_semantics_unchanged: json mode exits exactly as prose mode does on the same fixture

## Feature Inventory Touches

(empty -- governance tooling)

## Definition of Done

### Deliverable: canonical emission + whole-ledger verifiability

- **D1**: Every future ledger entry can be emitted through one typed API whose output the verifier round-trips; the legacy band becomes tamper-evident by attestation; health findings are machine-readable (GH #278 incl. the operator's retroactive requirement).
- **D2**: ledger_emit.render/append; ledger_attest_legacy collect/build/CLI; the verify attestation extension; governance_health --format json.
- **D3**: Ledger entries for plan/audit/implement/seal; the LIVE migration attestation entry in docs/META_LEDGER.md emitted through the new API (LD-4); CHANGELOG feature entry.
- **D4**: The eleven tests observe round-trip parsing, chain linkage, skip-set equality, zero-skip attestation, backwards tamper detection, live-ledger zero skips, and JSON shape/exit parity; red-then-green twice.

## CI Commands

- `python -m pytest tests/test_ledger_emit.py tests/test_ledger_attest_legacy.py tests/test_governance_health_json.py -q` - focused suites (run twice for determinism)
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - zero skips after the live migration
- `python -m pytest -q` - full suite
