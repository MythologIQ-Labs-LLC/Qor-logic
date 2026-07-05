# Plan: Phase 41 — ledger_hash verifier regex robustness

**change_class**: feature
**target_version**: v0.31.0
**doc_tier**: minimal
**pass**: 3

**Pass 3 delta**: Reclassified from `hotfix`/v0.30.1 to `feature`/v0.31.0 per operator guidance. The scope is not "patch a broken regex" but "new capability" on three axes: (1) fenced-form Content/Previous Hash parsing is a behavior the verifier could not do before; (2) bounded-span discipline eliminates a whole class of ledger-format accidents rather than one reported instance; (3) the shipped `qor-validate` SKILL now points at a real implementation for the first time. Under Phase 33 doctrine (`qor/references/doctrine-governance-enforcement.md` §4), feature-class plans require `README.md` and `CHANGELOG.md` entries in `implement.files_touched`; both added to Phase 1 Affected Files here. Depends on PR #10 (v0.29.0) and PR #11 (v0.30.0) landing first so main's pyproject reaches 0.30.0 and `bump_version('feature')` computes v0.31.0 cleanly.

**Pass 2 delta** (superseded but retained for chain clarity): Added Phase 1 "Fixture updates" subsection listing the five unanchored `Chain Hash = {hash}` lines in existing tests that must be rewritten to bold-anchored form. Addresses audit VETO V1 (coverage-gap) documented in `.agent/staging/AUDIT_REPORT.md` (Phase 41 Pass 1) and `docs/SHADOW_GENOME.md` Entry #31.

**Scope**: Localized fix to four defects in `qor/scripts/ledger_hash.py` and one stale path reference in the shipped `qor-validate` SKILL. No public API changes; no ledger migration.

**Rationale**: GitHub issue #13. The three hash-field regexes in the verifier are structurally unsound against real markdown ledgers:

- `CHAIN_HASH_RE` lacks the `\*\*...\*\*` bold anchor that `CONTENT_HASH_RE` and `PREV_HASH_RE` carry, so prose containing the phrase "Chain Hash" captures the wrong hex value.
- All three regexes use `.*?` under `re.DOTALL`, which sweeps across field boundaries when the immediate field value is fenced rather than inline; subsequent unrelated hex fields (Plan Hash, Audit Hash) are captured instead.
- `CONTENT_HASH_RE` and `PREV_HASH_RE` accept only the inline-backtick form, not the fenced `= <hex>` form that `CHAIN_HASH_RE` accepts.

Impact documented against a sibling consumer workspace's ledger Entries #127–#128: verifier returns FAIL on ledgers whose chains are actually correct. The downstream workaround is to scrub prose or rename fields, which is a content-level band-aid over a parser-level bug.

Issue #13 also flags three stale references in `qor/skills/governance/qor-validate/SKILL.md` to `.claude/commands/scripts/validate-ledger.py`, a path that `qorlogic install` does not produce.

## Open Questions

None.

## Phase 1 — verifier regex robustness

### Affected Files

- `tests/test_ledger_hash.py` — NEW test cases (listed below) for the four defects. Tests written first and made to fail before touching `ledger_hash.py`.
- `qor/scripts/ledger_hash.py` — tighten `CONTENT_HASH_RE`, `PREV_HASH_RE`, and `CHAIN_HASH_RE`; anchor on `\*\*Field\*\*`; bound the non-greedy span; accept both inline-backtick and fenced forms on all three fields.
- `CHANGELOG.md` — add `## [0.31.0] - <seal-date>` section under `## [Unreleased]`. Content: three bullets matching the Pass 3 delta's three axes (fenced Content/Previous parsing; bounded-span discipline; SKILL canonical references). References META_LEDGER seal entry number (placeholder `#[N]` filled at substantiate time).
- `README.md` — refresh the test-count badge (currently `Tests: 602 passing`, actual post-Phase-41 is `729 passing`) and the ledger-entry-count badge (currently `104 entries sealed`, actual is the sealed entry count at substantiate time). No version-specific prose added; the existing "Latest release" section points at CHANGELOG.md as source of truth and the convention is to avoid README drift by keeping the README version-agnostic.

### Unit Tests

TDD order — each test is added first, confirmed RED, then the regex patch makes it GREEN.

- `test_verify_chain_anchor_rejects_prose_mention` — Synthetic ledger where entry body contains the phrase `Chain Hash` in prose before the real `**Chain Hash**:` metadata line, with an unrelated backtick-hex value in the prose. Current (buggy) regex captures the prose hex; patched regex must capture only the metadata hex. Verifier returns 0.
- `test_verify_fenced_content_with_trailing_inline_hash` — Synthetic ledger where `**Content Hash**:` is followed by a fenced `SHA256(...)\n= <hex>` block (no inline backtick), then a later `**Plan Hash**: \`<plan-hex>\`` line. Current regex captures the plan-hex as content; patched regex must capture the fenced content-hex. Verifier returns 0.
- `test_verify_fenced_previous_with_trailing_inline_hash` — Same pattern as above but for `**Previous Hash**:` fenced form. Verifier returns 0.
- `test_verify_bounded_span_stops_at_next_field` — Entry where the hex value for a field is genuinely absent (markup broken). Current regex sweeps into the next field and accepts its hex; patched regex must stop at the next `\*\*[A-Z]...\*\*:` marker and the entry is reported as skipped (not falsely verified).
- `test_verify_accepts_fenced_content_hash` — `**Content Hash**:` in fenced `= <hex>` form verifies clean (symmetric with the existing `test_verify_accepts_inline_backtick_chain_hash`).
- `test_verify_accepts_fenced_previous_hash` — Same, for `**Previous Hash**:`.
- `test_verify_accepts_mixed_content_hash_forms` — A ledger with one entry using inline-backtick `**Content Hash**:` and another using fenced `= <hex>` verifies clean.
- `test_verify_real_ledger_still_passes` — Regression: the repo's own `docs/META_LEDGER.md` still verifies after the regex changes (reuses the existing `test_verify_passes_on_current_ledger` expectation; explicit duplicate kept here to catch regressions introduced by the new bounded-span rule).

### Fixture updates (existing tests)

Five lines in `tests/test_ledger_hash.py` currently use the unanchored `Chain Hash = {hash}` markup that becomes un-matchable under the new `\*\*Chain Hash\*\*` anchor. The containing tests assert only `rc == 0`, which is also satisfied when all entries are silently skipped; left unchanged, these tests would degrade to vacuously green and stop exercising chain verification. They must be rewritten to bold-anchored form as part of Phase 1.

Affected lines and the test bodies they belong to:

- `test_verify_clean_synthetic_ledger` (lines 194-214):
  - Line 206 `Chain Hash = {chain_a}` → `**Chain Hash**: \`{chain_a}\``
  - Line 211 `Chain Hash = {chain_b}` → `**Chain Hash**: \`{chain_b}\``

- `test_verify_handles_non_monotonic_entry_numbers` (lines 235-260):
  - Line 250 `Chain Hash = {chain_a}` → `**Chain Hash**: \`{chain_a}\``
  - Line 256 `Chain Hash = {chain_a}` → `**Chain Hash**: \`{chain_a}\``

- `test_verify_accepts_mixed_chain_hash_forms` (lines 307-327): this test's "EQUATION FORM" entry (line 319 `Chain Hash = {chain_a}`) must be rewritten to the fenced form so the test name's claim of mixed-form acceptance remains accurate after the anchor tightens:

  ```
  **Chain Hash**:
  \`\`\`
  SHA256(content_hash + previous_hash)
  = {chain_a}
  \`\`\`
  ```

  The "INLINE FORM" entry on line 324 is already bold-anchored (`**Chain Hash**: \`{chain_b}\``) and needs no change.

After the fixture updates, each affected test must still assert `rc == 0` **and** must additionally assert that the expected number of entries verified (not skipped). To detect vacuous-green regression, amended tests parse stdout via pytest's `capsys` fixture and assert that each expected `OK   Entry #N:` line appears in the captured output. `verify()` already prints one `OK` line per verified entry; no change to `verify()` is needed. `capsys` is a stock pytest fixture used elsewhere in this test suite (`tests/test_cli.py`, `tests/test_collect.py`, etc.); no new infrastructure is introduced.

### Changes

In `qor/scripts/ledger_hash.py`, replace the three regex module-level constants:

```python
# Field value may be inline-backtick `<hex>` on the same line, or the fenced
# `= <hex>` form inside a code block. The non-greedy span is bounded: it MUST
# NOT cross into the next **FieldName**: marker (two line-leading asterisks
# followed by capitalized field header), nor across a blank-line-separated
# paragraph that does not contain a hex value.
_HASH_SPAN = r"(?:(?!\n\s*\*\*[A-Z])[\s\S])*?"
_HASH_VALUE = r"(?:`([0-9a-f]{64})`|=\s*([0-9a-f]{64})\b)"

CONTENT_HASH_RE = re.compile(rf"\*\*Content Hash\*\*{_HASH_SPAN}{_HASH_VALUE}")
PREV_HASH_RE    = re.compile(rf"\*\*Previous Hash\*\*{_HASH_SPAN}{_HASH_VALUE}")
CHAIN_HASH_RE   = re.compile(rf"\*\*Chain Hash\*\*{_HASH_SPAN}{_HASH_VALUE}")
```

In `verify()`, update the match-group extraction to handle two alternation groups uniformly for all three regexes:

```python
ch_m = CONTENT_HASH_RE.search(body)
ph_m = PREV_HASH_RE.search(body)
xh_m = CHAIN_HASH_RE.search(body)
if not (ch_m and ph_m and xh_m):
    skipped += 1
    continue
content_val  = ch_m.group(1) or ch_m.group(2)
previous_val = ph_m.group(1) or ph_m.group(2)
recorded     = xh_m.group(1) or xh_m.group(2)
```

All three regexes now require the `**Field**` bold anchor (symmetry), accept both value forms (symmetry), and cannot sweep across the next field marker (bounded span). The `re.DOTALL` flag is no longer needed because `[\s\S]` is explicit about newline inclusion inside the bounded span.

## Phase 2 — qor-validate SKILL.md reference cleanup

### Affected Files

- `tests/test_qor_validate_skill_references.py` — NEW. Doctrine-style lint: the source SKILL.md and every shipped variant under `qor/dist/variants/*/skills/qor-validate/SKILL.md` must not contain the stale path `.claude/commands/scripts/validate-ledger.py`, and must reference `qor.scripts.ledger_hash` or `qorlogic verify-ledger`.
- `qor/skills/governance/qor-validate/SKILL.md` — replace the three stale references in Steps 3, 4, and 7 with the canonical module/CLI path.

### Unit Tests

- `test_qor_validate_skill_has_no_stale_path` — Grep the source SKILL.md and every variant dist SKILL.md; `assert ".claude/commands/scripts/validate-ledger.py" not in text` for each.
- `test_qor_validate_skill_references_canonical_path` — `assert "qor.scripts.ledger_hash" in text or "qorlogic verify-ledger" in text` for each of Steps 3, 4, and 7.

### Changes

Source edit (`qor/skills/governance/qor-validate/SKILL.md`):

- Step 3 "Parse Entries": replace `Reference implementation: \`.claude/commands/scripts/validate-ledger.py\`.` with `Reference implementation: \`qor/scripts/ledger_hash.py\` — exposes \`ENTRY_RE\`, \`CONTENT_HASH_RE\`, \`PREV_HASH_RE\`, \`CHAIN_HASH_RE\` and the \`verify()\` entrypoint. CLI: \`qorlogic verify-ledger docs/META_LEDGER.md\`.`
- Step 4 "Verify Chain": same replacement pattern.
- Step 7 "Content Hash Verification (Deep Audit)": same replacement pattern.

Variant dist SKILL.md files are regenerated by the existing install/build pipeline; no hand-edit of `qor/dist/variants/*` required in this plan (the regen will be triggered during substantiate).

## CI Commands

Operator must run all of the following locally before substantiate; these match the CI matrix in `.github/workflows/ci.yml`:

- `python -m pytest tests/test_ledger_hash.py -v`
- `python -m pytest tests/test_qor_validate_skill_references.py -v`
- `python -m pytest tests/ -v` (full suite — catch doctrine-test regressions)

Determinism check: each new test is run twice in a row locally to confirm no flake before claiming green (per `qor/references/doctrine-test-discipline.md` Rule 3).
