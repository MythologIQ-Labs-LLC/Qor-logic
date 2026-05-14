# Plan: Phase 66 - qor-validate integrity bundle

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #54 (qor-validate skips session seals + reports downstream placeholder-chain entries as OK) and GH #55 (qor-validate skill should honor post-anchor ledger invariant instead of raw verifier failure).

**terms_introduced**:
- term: TAINTED entry
  home: qor/scripts/ledger_hash.py
- term: DISCLOSED_PRE_ANCHOR
  home: qor/scripts/ledger_hash.py
- term: post-anchor boundary
  home: qor/references/doctrine-governance-enforcement.md

**boundaries**:
- limitations:
  - V1 placeholder-pattern detection uses conservative heuristics (ascending hex sequences, repeating bigrams, low-entropy runs). It accepts that determined fabrication can defeat any pattern detector; the defense-in-depth comes from Phase 64's Step 6.8 gate at write time.
  - V1 post-anchor boundary defaults to the highest-numbered entry whose chain hash verifies cleanly under canonical or session-seal markup. Operator override via explicit `--boundary <entry-num>` is supported.
  - V1 Session Seal markup recognition is a one-way pattern: `**Session Seal**: ... SHA256(content_hash + previous_hash) = \`<hex>\``. Future variant markups are out of scope.
- non_goals:
  - Backfilling historical entries to canonical Chain Hash markup. The chain is immutable; old Session Seal entries are recognized in place.
  - Cross-repo ledger validation (each consumer ledger is verified against its own history).
  - Repairing tainted downstream entries; the validator reports tainted status but does not mutate the ledger.
- exclusions:
  - No changes to /qor-substantiate Step 6.8 (Phase 64) or Step 7.7 seal_entry_check (Phase 47). Those gates remain authoritative at seal time.
  - No changes to ledger_hash.chain_hash() algorithm. The hash format is stable.
  - No changes to the META_LEDGER schema or entry layout.

## Open Questions

None. Issue bodies and remediation handoff specify the required behaviors; the open question about CLI path-arg semantics (Issue #55) is resolved by adding `--ledger PATH` as an explicit opt-in flag, keeping the existing flag-less workdir-default in place.

## Phase 1: Verifier core extensions

### Affected Files

- `tests/test_session_seal_markup_recognition.py` - NEW. 5 tests covering Session Seal markup detection, value extraction, and chain math.
- `tests/test_placeholder_pattern_detection.py` - NEW. 6 tests covering ascending-hex, repeating-bigram, low-entropy, and legitimate-digest cases.
- `tests/test_taint_propagation.py` - NEW. 4 tests covering downstream entry classification when a predecessor FAILs.
- `qor/scripts/ledger_hash.py` - extend `verify()`:
  - Add `SESSION_SEAL_RE` regex matching `**Session Seal**: ... = \`<64-hex>\``.
  - Add `is_placeholder_pattern(value: str) -> bool` helper.
  - Track entries through the chain in order; mark FAIL when chain math fails OR placeholder detected; mark TAINTED for any subsequent entry until next OK chain link.
  - Output categorized counts: `verified`, `failed`, `tainted`, `disclosed_pre_anchor`, `skipped_session_seal_only`, `skipped_no_hash_markup`.

### Changes

`SESSION_SEAL_RE = re.compile(r"\*\*Session Seal\*\*[^\n]*?=\s*\`([0-9a-f]{64})\`")` extracts the recorded chain value from Session Seal markup. When `CHAIN_HASH_RE` does not match but `SESSION_SEAL_RE` does, treat the matched value as the chain hash for downstream continuity checks. Entries with neither markup remain in `skipped_no_hash_markup`.

`is_placeholder_pattern(value)` returns True for:
- Strings whose first 16 chars are `0123456789abcdef` in order (or its reverse).
- Strings where the first 16 chars form a pattern `[ab][12][cd][34]...` (the Issue #54 FailSafe failure mode).
- Strings with a single repeating bigram across all 64 chars (e.g., `a1a1a1...`).
- Strings with substring entropy below a conservative threshold (counts of distinct hex digits across 16-char windows).

`verify()` walks entries in chain order. For each entry: parse fields, run placeholder check on all three hashes, compute expected chain math, compare to recorded value. If FAIL: emit `FAIL Entry #N: <reason>`; for each subsequent entry until a fresh chain-link succeeds, emit `TAINTED Entry #M: depends on failed predecessor #N`.

### Unit Tests

- `tests/test_session_seal_markup_recognition.py::test_session_seal_regex_matches_canonical_form` - invokes `SESSION_SEAL_RE.search` on a fixture string and asserts the matched value equals the expected 64-hex digest.
- `tests/test_session_seal_markup_recognition.py::test_verify_recognizes_session_seal_only_entry` - constructs a tiny ledger with one Chain Hash entry chained into one Session Seal entry; asserts `verify()` reports both as OK and not skipped.
- `tests/test_session_seal_markup_recognition.py::test_verify_rejects_session_seal_with_invalid_chain` - constructs a ledger where Session Seal hex does not match recomputed chain; asserts FAIL is reported with the entry number.
- `tests/test_session_seal_markup_recognition.py::test_verify_session_seal_continuity_into_chain_hash` - asserts Entry N+1's previous_hash field equals the Session Seal value parsed from Entry N.
- `tests/test_session_seal_markup_recognition.py::test_skipped_summary_distinguishes_session_seal_only_from_no_markup` - constructs a ledger with one bare-prose entry and one Session-Seal-only entry; asserts categorized skip counts.
- `tests/test_placeholder_pattern_detection.py::test_ascending_hex_pattern_detected` - asserts `is_placeholder_pattern("0123456789abcdef" * 4)` returns True.
- `tests/test_placeholder_pattern_detection.py::test_repeating_bigram_detected` - asserts `is_placeholder_pattern("a1" * 32)` returns True.
- `tests/test_placeholder_pattern_detection.py::test_failsafe_failure_mode_pattern_detected` - asserts the literal Issue-#54 FailSafe placeholder hash `a1b2c3d4e5f6...` returns True.
- `tests/test_placeholder_pattern_detection.py::test_real_sha256_digest_passes` - asserts a real digest computed via `hashlib.sha256()` returns False.
- `tests/test_placeholder_pattern_detection.py::test_low_entropy_threshold` - asserts a 64-hex string using only 3 distinct chars returns True.
- `tests/test_placeholder_pattern_detection.py::test_verify_flags_entry_with_placeholder_content_hash` - constructs ledger with one entry whose content_hash matches placeholder pattern; asserts FAIL with `placeholder_pattern` reason.
- `tests/test_taint_propagation.py::test_downstream_entries_after_fail_marked_tainted` - constructs ledger A->B->C where B fails; asserts C reports TAINTED and not OK.
- `tests/test_taint_propagation.py::test_taint_clears_on_chain_relink` - constructs A->B(FAIL)->C(re-anchored from new content); asserts C is not tainted when its chain math is internally consistent with itself.
- `tests/test_taint_propagation.py::test_taint_reports_root_cause_entry_number` - asserts TAINTED output names the originating FAIL entry number.
- `tests/test_taint_propagation.py::test_taint_propagation_stops_at_session_boundary` - asserts taint does not cross entries that are explicitly re-anchored (operator-supplied boundary marker).

## Phase 2: Post-anchor verify mode + CLI

### Affected Files

- `tests/test_post_anchor_verify.py` - NEW. 8 tests covering boundary detection, pre-anchor tolerance, post-anchor failure, explicit boundary override, empty ledger, all-fail ledger.
- `tests/test_verify_ledger_cli.py` - NEW. 3 tests covering `--ledger PATH` argparse, `--post-anchor` flag, exit codes for each mode.
- `qor/scripts/ledger_hash.py` - add `verify_post_anchor(ledger_md, boundary_entry=None) -> int` function.
- `qor/cli.py` - extend `verify-ledger` subparser with `--ledger PATH` (optional override of `workdir.meta_ledger()`) and `--post-anchor` (switches to `verify_post_anchor`).

### Changes

`verify_post_anchor()` walks entries in chain order. The default boundary is the entry id of the most recent canonically-verifying entry (i.e., the last entry whose chain math matches under Chain Hash or Session Seal markup AND whose hashes pass placeholder detection). Operator may override with an explicit `boundary_entry` argument. For each entry:
- entry id <= boundary AND chain math fails: report `DISCLOSED_PRE_ANCHOR Entry #N`; do not count as error.
- entry id > boundary AND chain math fails: report `FAIL Entry #N`; count as error.
- entry id > boundary AND chain math succeeds: report `OK Entry #N`.

Exit 0 if zero errors across the post-anchor surface; non-zero otherwise.

CLI extension preserves backward compatibility:
- `qor-logic verify-ledger` (existing): raw verifier against `workdir.meta_ledger()`.
- `qor-logic verify-ledger --ledger <path>` (new): explicit path override.
- `qor-logic verify-ledger --post-anchor` (new): post-anchor verification.
- `qor-logic verify-ledger --post-anchor --boundary <entry-num>` (new): operator-pinned boundary.

### Unit Tests

- `tests/test_post_anchor_verify.py::test_post_anchor_clean_when_pre_anchor_fails_tolerated` - constructs a ledger with FAIL at #5 and OK at #6..#10; asserts `verify_post_anchor()` returns 0 and labels #5 as DISCLOSED_PRE_ANCHOR.
- `tests/test_post_anchor_verify.py::test_post_anchor_dirty_when_post_boundary_fails` - constructs a ledger with OK at #5 and FAIL at #6; asserts `verify_post_anchor()` returns non-zero and labels #6 as FAIL.
- `tests/test_post_anchor_verify.py::test_boundary_defaults_to_last_clean_entry` - constructs a mixed ledger; asserts auto-detected boundary equals the last canonically verifying entry id.
- `tests/test_post_anchor_verify.py::test_explicit_boundary_overrides_auto_detection` - asserts passing `boundary_entry=7` shifts the pre/post split regardless of auto-detection.
- `tests/test_post_anchor_verify.py::test_empty_ledger_returns_clean` - asserts a ledger with no entries returns 0 with no output.
- `tests/test_post_anchor_verify.py::test_all_fail_ledger_returns_dirty` - constructs a ledger where every entry fails; asserts non-zero exit and FAILs reported for the post-boundary slice.
- `tests/test_post_anchor_verify.py::test_corefoge_pattern_passes` - constructs the COREFORGE pattern from Issue #55 (pre-anchor #156-#169 FAIL cluster, post-anchor #170+ clean); asserts post-anchor clean.
- `tests/test_post_anchor_verify.py::test_session_seal_entry_counts_as_clean_boundary_candidate` - asserts a Session Seal entry can become the post-anchor boundary when its math verifies.
- `tests/test_verify_ledger_cli.py::test_cli_accepts_explicit_ledger_path` - invokes `cli.main(["verify-ledger", "--ledger", str(tmp_path / "ledger.md")])` and asserts exit code matches the underlying `verify()` return value.
- `tests/test_verify_ledger_cli.py::test_cli_post_anchor_flag_routes_to_post_anchor_verify` - asserts the `--post-anchor` flag invokes `verify_post_anchor()` not `verify()`.
- `tests/test_verify_ledger_cli.py::test_cli_default_uses_workdir_meta_ledger` - asserts the flag-less invocation still resolves the ledger via `workdir.meta_ledger()`.

## Phase 3: qor-validate skill + doctrine refresh

### Affected Files

- `tests/test_qor_validate_skill_post_anchor_prose.py` - NEW. 4 tests covering skill-prose contract: post-anchor mode documented, stale path-arg invocation removed, source URL refreshed, new failure classifications named.
- `qor/skills/governance/qor-validate/SKILL.md` - prose updates:
  - Drop stale `qor-logic verify-ledger docs/META_LEDGER.md` (with path arg) from Steps 3, 4, 7.
  - Add new step or sub-step documenting `--post-anchor` mode and when to use it.
  - Document the new entry classifications (OK / FAIL / TAINTED / DISCLOSED_PRE_ANCHOR / SKIPPED categorized).
  - Update source URL in frontmatter from `MythologIQ/Qor-logic` to `MythologIQ-Labs-LLC/Qor-logic`.
- `qor/skills/governance/qor-validate/references/qor-validate-reports.md` - update report templates for new categories.
- `qor/references/doctrine-governance-enforcement.md` - add §14 "Post-anchor ledger invariant" with the boundary contract, pre-anchor disclosure semantics, and audit trail expectations.
- `qor/dist/variants/{claude,codex,kilo-code,gemini}/...` - regenerated via `dist_compile`.

### Changes

Skill prose adopts the post-anchor mode as the default for consumer workspaces that have re-anchored their ledger; raw mode is documented as the strict-correctness audit. Stale CLI lines are removed; new CLI usage examples cite the correct flag-less default plus the new `--ledger`/`--post-anchor` flags.

Doctrine §14 documents the post-anchor boundary semantics so consumer repos can cite the contract when their ledger has known disclosed pre-anchor failures.

### Unit Tests

- `tests/test_qor_validate_skill_post_anchor_prose.py::test_skill_documents_post_anchor_mode` - asserts the SKILL.md body contains `--post-anchor` and a description of when to use it.
- `tests/test_qor_validate_skill_post_anchor_prose.py::test_skill_no_longer_recommends_stale_path_arg_invocation` - asserts no line containing `qor-logic verify-ledger` also contains `docs/META_LEDGER.md` (the rejected pre-Phase-66 form).
- `tests/test_qor_validate_skill_post_anchor_prose.py::test_skill_source_url_uses_labs_llc` - asserts the frontmatter `repository:` URL is `MythologIQ-Labs-LLC/Qor-logic`, not `MythologIQ/Qor-logic`.
- `tests/test_qor_validate_skill_post_anchor_prose.py::test_skill_names_new_failure_classifications` - asserts the SKILL.md body names `TAINTED` and `DISCLOSED_PRE_ANCHOR` as entry statuses.

## Phase 4: Documentation + release housekeeping

### Affected Files

- `docs/SYSTEM_STATE.md` - prepend Phase 66 entry.
- `docs/operations.md` - add 1 troubleshooting row for `--post-anchor` mode usage with re-anchored ledgers.
- `CHANGELOG.md` - new Unreleased entries; stamped to `[0.47.0]` at seal time.
- `README.md` - badge currency: Ledger to 200, Tests to truth count after Phase 66 tests land.

### Changes

Mechanical doc-currency updates. SYSTEM_STATE.md captures the Phase 66 deliverables for procedural-fidelity coverage. Operations row helps operators know which mode to invoke when their consumer ledger has disclosed pre-anchor failures.

### Unit Tests

None for Phase 4. Existing badge-currency + procedural-fidelity + SYSTEM_STATE-coverage tests are the structural enforcement.

## CI Commands

- `python -m pytest tests/test_session_seal_markup_recognition.py tests/test_placeholder_pattern_detection.py tests/test_taint_propagation.py tests/test_post_anchor_verify.py tests/test_verify_ledger_cli.py tests/test_qor_validate_skill_post_anchor_prose.py -v` - validates the six new Phase 66 test surfaces.
- `python -m qor.scripts.dist_compile` - regenerates dist variants so Phase 3 prose tests find the qor-validate skill updates in each variant.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase66-qor-validate-integrity-bundle.md` - lint this plan file itself.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite minus the flaky tag-coverage test.
