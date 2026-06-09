# Plan: Phase 140 -- governance-health + ledger-seal robustness (GH #199, #200, #201)

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations:
  - #201 gate rejects non-ASCII sealable text; it does not auto-rewrite already-sealed
    historical entries (repair of an existing corrupted entry remains a separate manual re-chain).
  - #199 tolerance reuses `verify_post_anchor`'s auto-detected boundary; a tampered entry that
    sits at or below that boundary is tolerated by the health gate exactly as the release gate
    already tolerates it (no new exposure beyond the existing release posture).
- non_goals:
  - No change to `qor-validate` (the strict Merkle validator) -- it stays strict by design.
  - No retroactive migration of pre-Phase-140 plans or entries.
  - No silent normalization of sealable text inside the hash boundary (would desync the hash);
    `normalize_punctuation` is an opt-in authoring helper, the gate only rejects.
- exclusions:
  - `docs/FEATURE_INDEX.md` (pre-existing MISSING, separate `/qor-remediate` scope).

## Open Questions

None. Design is fully grounded in the research brief
(`docs/research-brief-governance-health-ledger-seal-robustness-2026-06-09.md`) and the cited source.

## Phase 1: Ledger-seal UTF-8/ASCII validity gate (GH #201, P0)

### Affected Files

- `tests/test_ledger_seal_utf8_validation.py` (NEW) - behavior tests for the validity gate + normalizer + write-boundary wiring.
- `qor/scripts/ledger_hash.py` - add `normalize_punctuation(text)` and `assert_sealable_text(text)`.
- `qor/scripts/ledger_fragment.py` - call `assert_sealable_text` in `write_fragment` (before the
  `_body_hash` check) and in `canonicalize_fragments` (per formatted appendix part, before
  `write_text`).

### Changes

`ledger_hash.normalize_punctuation(text: str) -> str`: pure map of the common non-ASCII
punctuation set to ASCII equivalents -- em-dash U+2014 -> `--`, en-dash U+2013 -> `-`,
right/left single quote U+2019/U+2018 -> `'`, right/left double quote U+201D/U+201C -> `"`,
arrow U+2192 -> `->`, ellipsis U+2026 -> `...`. Output is ASCII for the mapped set; idempotent.

`ledger_hash.assert_sealable_text(text: str, *, label: str = "entry body") -> None`: raises
`ValueError` naming the first offending character, its codepoint (`U+XXXX`), and its index when
`not text.isascii()`. No-op for ASCII input. This is the load-bearing prevention: a sealable body
must be ASCII before its content hash is computed, so codepoint-truncated / cp1252 / invalid-UTF-8
bytes can never be committed to a hash.

Grep-evidence (LD-201a, current reality the gate is encoded against):
> `grep -nE "def content_hash|open\(path" qor/scripts/ledger_hash.py`
> -> `25:def content_hash(path: Path) -> str:` / `27:    with open(path, "rb") as f:`
> (raw-byte hash, no decode -- confirms no existing validity assertion)

Grep-evidence (LD-201b, write boundary):
> `grep -nE "def write_fragment|content_hash != _body_hash" qor/scripts/ledger_fragment.py`
> -> `40:def write_fragment(...)` / `48:    if fragment.content_hash != _body_hash(fragment.body):`

`write_fragment`: insert `assert_sealable_text(fragment.body, label=f"fragment {fragment.uid} body")`
as the first statement after `validate_entry_uid`, before the content-hash equality check.

`canonicalize_fragments`: call `assert_sealable_text` on each `f"### Entry #{N}: {f.title}\n\n{f.body}\n"`
appendix part before joining/`write_text`, so a non-ASCII title or body fails the canonical
META_LEDGER write and leaves the ledger and fragment store untouched (no partial write, no consume).

### Unit Tests

- `tests/test_ledger_seal_utf8_validation.py`:
  - `test_assert_sealable_rejects_em_dash_with_codepoint_and_index` - feeding `"a -- b"` with a real
    U+2014 raises `ValueError` whose message contains `U+2014` and the offending index; asserts the
    exception, not a substring of a file.
  - `test_assert_sealable_accepts_clean_ascii` - returns None for a normal ASCII entry body.
  - `test_normalize_punctuation_maps_to_ascii_and_is_idempotent` - input built from the U+2014 /
    U+2013 / U+2019 / U+201C / U+201D / U+2192 / U+2026 codepoints becomes ASCII
    (`result.isascii()` True) and `normalize(normalize(x)) == normalize(x)`.
  - `test_write_fragment_rejects_non_ascii_body` - calling `write_fragment` with a U+2019 in the
    body raises `ValueError` (assert via `pytest.raises`); the message names the offending codepoint.
  - `test_canonicalize_rejects_non_ascii_and_leaves_ledger_unchanged` - calling
    `canonicalize_fragments` with a fragment whose body holds a U+0092-class char raises `ValueError`;
    re-reading the ledger returns text byte-identical to the pre-call value and the fragment is still
    returned by `read_fragments` (rollback verified by invoking the units, not by inspecting artifacts).

## Phase 2: skill-entry disclosed-pre-anchor tolerance (GH #199, P1)

### Affected Files

- `tests/test_governance_health_post_anchor_tolerance.py` (NEW) - behavior tests with synthetic ledgers.
- `qor/scripts/governance_health.py` - add `_verify_post_anchor(ledger_path)` wrapper; in
  `_ledger_damage`, on strict-verify failure fall back to post-anchor classification.

### Changes

Grep-evidence (LD-199a):
> `grep -nE "def _verify_ledger_chain|ledger_hash.verify" qor/scripts/governance_health.py`
> -> `118:def _verify_ledger_chain(...)` / `121:    return ledger_hash.verify(ledger_path)` (strict, no tolerance)

Grep-evidence (LD-199b):
> `grep -nE "def verify_post_anchor" qor/scripts/ledger_hash.py` -> `390:def verify_post_anchor(`
> (emits `DISCLOSED_PRE_ANCHOR` for entries <= auto-detected boundary; returns 0 when post-anchor clean)

Add `_verify_post_anchor(ledger_path) -> int` mirroring `_verify_ledger_chain` but calling
`ledger_hash.verify_post_anchor`. In `_ledger_damage`, when strict `_verify_ledger_chain` returns
non-zero, call `_verify_post_anchor` under the same stdout redirect: return the damage reason only
when the post-anchor surface is ALSO dirty (`rc_post != 0`, i.e. a genuine post-boundary failure);
when post-anchor is clean (`rc_post == 0`) the failure is a disclosed pre-anchor residual and the
ledger is NOT classified DAMAGED. This gives the skill-entry preflight the same tolerance the
release gates already apply, closing the asymmetry where strict verify rejects single-lineage
manual-era residuals that `verify_post_anchor` tolerates.

### Unit Tests

- `tests/test_governance_health_post_anchor_tolerance.py`:
  - `test_disclosed_pre_anchor_residual_is_not_damaged` - synthetic ledger with one broken
    single-lineage early entry (strict verify fails) but every entry above the auto boundary chains
    cleanly; `_classify_one` / `_ledger_damage` returns OK (status not DAMAGED). Built with
    `chain_hash` so the post-anchor band is genuinely valid.
  - `test_post_anchor_failure_is_still_damaged` - synthetic ledger whose newest (post-boundary)
    entry has a wrong chain hash; `_ledger_damage` returns the `"ledger chain verification failed"`
    reason and `_classify_one` yields DAMAGED.
  - `test_fully_valid_ledger_is_ok` - a clean chain returns OK (regression guard: tolerance path
    is not entered when strict verify already passes).

## Phase 3: placeholder check -- template-form matching (GH #200, P2)

### Affected Files

- `tests/test_governance_health.py` (EXTEND) - add prose-vs-template placeholder cases.
- `qor/scripts/governance_health.py` - replace bare-substring `_PLACEHOLDER_MARKERS` with
  compiled template-form patterns; update `_incomplete_reason` to `pattern.search`.

### Changes

Grep-evidence (LD-200a):
> `grep -nE "_PLACEHOLDER_MARKERS|if marker in text" qor/scripts/governance_health.py`
> -> `63:_PLACEHOLDER_MARKERS = (` / `147:        if marker in text:` (raw substring test)

Replace `_PLACEHOLDER_MARKERS` with `_PLACEHOLDER_PATTERNS`, a tuple of compiled regexes that each
require a structural cue rather than a bare word:
- `re.compile(r"\bTODO\s*:")` and `re.compile(r"\bFIXME\s*:")` -- label form only.
- `re.compile(r"<!--\s*(?:TODO|FIXME)")` -- HTML-comment scaffold.
- `re.compile(r"\{\{\s*verify")`, `re.compile(r"INSTRUCTION:")`, `re.compile(r"\[Your ")`,
  `re.compile(r"\[Keyword")`, `re.compile(r"\[ISO 8601")`, `re.compile(r"\[Why ")` -- existing
  structural markers, preserved.

`_incomplete_reason`: iterate patterns; on `m := pattern.search(text)` return
`f"contains unresolved placeholder marker {m.group(0)!r}"`. Prose containing the bare letters
`TODO`/`FIXME` (no colon, no comment, no mustache) no longer trips INCOMPLETE; the ledger path
(`_ledger_incomplete`) is unchanged.

### Unit Tests

- `tests/test_governance_health.py` (extend):
  - `test_prose_todo_is_not_incomplete` - a non-ledger artifact containing `"TODO stubs"`,
    `"cosmetic TODOs"`, and `"a TODO list disguised as code"` classifies OK (not INCOMPLETE).
  - `test_template_todo_label_is_incomplete` - artifact containing `"TODO: fill this in"` classifies
    INCOMPLETE with the matched marker named in the reason.
  - `test_html_comment_and_bracket_placeholders_still_flag` - `"<!-- TODO"` and `"[Your name]"`
    each classify INCOMPLETE (existing structural markers preserved).

## Definition of Done

### Deliverable: D201 -- ledger-seal validity gate

- **D1**: A sealable ledger entry body/title that is not ASCII cannot have its content hash computed
  or be written to META_LEDGER.
- **D2**: `ledger_hash.assert_sealable_text(text, *, label="entry body") -> None` (raises ValueError
  with codepoint+index) and `ledger_hash.normalize_punctuation(text) -> str`; wired into
  `ledger_fragment.write_fragment` and `canonicalize_fragments`.
- **D3**: Ledger SESSION SEAL entry records the gate; no doctrine term added (existing symbols).
- **D4**: `test_canonicalize_rejects_non_ascii_and_leaves_ledger_unchanged` asserts the raise AND
  ledger-bytes-unchanged + fragment-not-consumed.

### Deliverable: D199 -- skill-entry post-anchor tolerance

- **D1**: The skill-entry health gate tolerates a disclosed pre-anchor residual (parity with release
  gates) but still flags a genuine post-anchor failure.
- **D2**: `governance_health._verify_post_anchor(ledger_path) -> int`; `_ledger_damage` returns a
  damage reason on strict failure only when post-anchor is also dirty.
- **D3**: Ledger entry notes the asymmetry closure; no schema change.
- **D4**: `test_disclosed_pre_anchor_residual_is_not_damaged` + `test_post_anchor_failure_is_still_damaged`
  assert OK vs DAMAGED on the two synthetic ledgers.

### Deliverable: D200 -- template-form placeholder matching

- **D1**: Prose containing the bare word TODO/FIXME no longer reports INCOMPLETE; template forms do.
- **D2**: `_PLACEHOLDER_PATTERNS` (compiled regex) replaces `_PLACEHOLDER_MARKERS`; `_incomplete_reason`
  uses `pattern.search`.
- **D3**: Ledger entry records the matching-discipline change; no doctrine term added.
- **D4**: `test_prose_todo_is_not_incomplete` + `test_template_todo_label_is_incomplete` assert the
  OK-vs-INCOMPLETE split.

## Feature Inventory Touches

None. This phase touches governance tooling under `qor/scripts/` only (no user-facing `src/`
feature surface); `docs/FEATURE_INDEX.md` is absent and out of scope (separate remediation).

## CI Commands

- `python -m pytest tests/test_ledger_seal_utf8_validation.py tests/test_governance_health_post_anchor_tolerance.py tests/test_governance_health.py -q` -- the three new/extended suites.
- `python -m pytest -q` -- full suite green (no regression).
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` -- chain still verifies.
- `qor-logic governance-health --profile skill-entry` -- preflight unaffected on this clean ledger.
