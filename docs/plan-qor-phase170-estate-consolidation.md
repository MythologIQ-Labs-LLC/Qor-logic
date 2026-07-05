# Plan: Phase 170 - Estate consolidation (GH #252)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: (none)

**boundaries**:
- limitations: The tool NEVER writes in place (`--output` required and must differ from `--input`); applying the migration to Qor-logic's own META_LEDGER.md is explicitly OUT of this phase's scope (operator decision later). Partial/no-hash entries are left byte-identical and reported.
- non_goals: No public-repo mirroring code (design-only upstream; five operator decisions surfaced on #252 at close); no SQLite adapter absorption (a sibling repository's shipped product -- interchange documented instead); no cli.py change (generic runner).
- exclusions: The estate-patterns documentation section via /qor-document at seal.

## Open Questions

(none -- the premise correction and slicing are recorded in research entry #402)

## Origin

Research brief docs/research-brief-estate-consolidation-2026-07-04.md (ledger entry #402, session `2026-07-04T1633-f0d980`); GH #252 (perspective-reset rec 6, final series item). Source tool: a sibling repository's scripts/migrate_ledger_v0_14.py (read in full).

## Locked Decisions

- **LD-1: the transform is ported faithfully, canonical output re-homed.**
  Source mechanics verified by full read: `ENTRY_RE` split (:30), 13 `PATTERNS` across formats A/B/C (:34-66), `extract` first-match-wins (:69-84), `strip_hash_blocks` fenced+inline removal (:87-116), separator-aware injection (:167-172), dual-formula mismatch REPORTING (:150-161). The ported canonical block emits Qor's current form -- `**Content Hash**: \`h\`` / `**Previous Hash**: \`h\`` / `**Chain Hash (Merkle seal)**: \`h\`` -- which `ledger_hash` regexes parse (CHAIN_HASH_RE accepts the parenthetical suffix, Phase 44).
- **LD-2: house discipline added on port.**
  `--dry-run` (Phase 167 contract: full transform + stats, no write, `[dry] would write <output>` line); idempotence (canonical input re-migrates byte-stable -- tested); exit codes honest (0 = all entries canonical after migration or dry-run clean; 1 = partial/no-hash/mismatch entries remain, reported); `--input == --output` rejected.
- **LD-3: verification round-trip is the acceptance bar.**
  A synthetic legacy ledger (one entry per format A/B/C with consistent chain math) must go from `Skipped ... non-verifiable markup` to fully `OK` under `qor.scripts.ledger_hash verify` after migration -- the tool's value proposition, tested end-to-end via the real verifier.
- **LD-4: generic-runner invocation.**
  `qor-logic scripts ledger_migrate --input <ledger> --output <path> [--dry-run]` (Phase 164-169 precedent; `qor/cli.py` untouched).
- **LD-5: caller surface is empty.**
  New leaf module; no existing code imports it. Registry untouched (`ledger_migrate` is a script, not a gate schema -- the Phase 169 freeze lint is unaffected).

## Phase 1: Ledger migration tool (TDD first)

### Affected Files

- tests/test_ledger_migrate.py - NEW; behavioral tests over all three legacy formats, idempotence, dry-run, exit codes, and the LD-3 verify round-trip
- qor/scripts/ledger_migrate.py - NEW; the ported transform + house discipline

### Changes

`qor/scripts/ledger_migrate.py` (<250 lines, stdlib only): the LD-1 transform with `migrate(text) -> (text, stats)` pure; `main(argv)` per LD-2/LD-4. Stats include migrated / unchanged_partial / unchanged_no_hash counts, mismatch list (dual-formula), and partial-entry detail -- all printed; the machine-readable summary line is final (`ledger_migrate: total=N migrated=M partial=P no_hash=Q mismatches=R`).

### Unit Tests

- tests/test_ledger_migrate.py::test_migrates_all_three_legacy_formats - synthetic ledger with one entry per format A (inline), B (fenced), C (session-seal labels): all three normalize to the canonical block with hashes preserved verbatim
- tests/test_ledger_migrate.py::test_canonical_input_is_byte_stable - migrating an already-canonical ledger returns byte-identical text (idempotence)
- tests/test_ledger_migrate.py::test_partial_and_no_hash_entries_left_verbatim_and_reported - entries missing one/all hashes are byte-identical in output and counted in stats; exit 1
- tests/test_ledger_migrate.py::test_chain_math_mismatch_reported_not_rejected - an entry whose chain hash matches neither formula still migrates, with the mismatch in stats
- tests/test_ledger_migrate.py::test_dry_run_writes_nothing_and_reports - --dry-run: output file absent, `[dry] would write` printed, stats identical to wet run
- tests/test_ledger_migrate.py::test_main_exit_codes_and_same_path_rejected - clean migration exits 0; residual partials exit 1; --input == --output errors before any read
- tests/test_ledger_migrate.py::test_migrated_ledger_becomes_verifiable - LD-3: the synthetic legacy ledger is Skipped-reported by `ledger_hash` verify before migration and fully OK after (invoking the real verifier over both files)

## Feature Inventory Touches

(empty -- governance tooling only; no user-touchable `src/` feature)

## Definition of Done

### Deliverable: ledger_migrate

- **D1**: Any estate repo can normalize a legacy-markup ledger to the canonical verifiable form with a safe rehearsal path (GH #252a; ends per-repo re-solving).
- **D2**: `qor/scripts/ledger_migrate.py` <=250 lines, stdlib; never-in-place; dry-run; honest exit codes.
- **D3**: GH #252 closes with the corrected premise recorded (b: design-blocked on five named operator decisions; c: a sibling repository pointer); estate-patterns doc section via /qor-document.
- **D4**: `test_migrated_ledger_becomes_verifiable` observes the skipped->verified round-trip through the real verifier; `test_canonical_input_is_byte_stable` observes idempotence.

## CI Commands

- `python -m pytest tests/test_ledger_migrate.py -q` -- new-test determinism (run twice)
- `python -m pytest -q` -- full suite regression
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase170-estate-consolidation.md` -- plan-text consistency
