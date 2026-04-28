# Plan: Phase 45 — Attribution Trailer Convention

**change_class**: feature

Implements [#18](https://github.com/MythologIQ-Labs-LLC/Qor-logic/issues/18) — a documented convention for crediting QorLogic SDLC in commit trailers, PR footers, and CHANGELOG attribution lines, plus a pure Python helper as the canonical source of the strings.

## Open Questions

None. All design decisions resolved during dialogue:

- Scope: doc + helper only; no skill wiring (no `/qor-document`, `/qor-substantiate`, or `changelog_stamp.py` changes in this phase).
- Doc placement: root `ATTRIBUTION.md` (quick-ref) plus `qor/references/doctrine-attribution.md` (full doctrine).
- Helper config shape: module-level constants in `attribution.py`; functions accept kwargs to override; `model` is the only required per-call argument.
- Strings adopt issue suggestions verbatim, including the leading `🤖` emoji. The doctrine carves a narrow, named exception to the CLAUDE.md "no non-ASCII chars in code/data" rule, scoped to bot-attribution trailers.
- Canonical QorLogic URL: `https://github.com/MythologIQ-Labs-LLC/qor-logic`.
- PR footer takes `defects_list` and optional `comparison_doc_path` as caller-supplied placeholders, not module constants.
- CHANGELOG attribution surfaces as a separate italic line beneath the existing version header (`_Built via [QorLogic SDLC](url)._`); the helper exposes the line, no caller in this phase inserts it. `changelog_stamp.py` regex is untouched.

## Phase 1: Helper module + tests

### Affected Files

- `tests/test_attribution.py` — new; pure-function tests for the three helpers.
- `qor/scripts/attribution.py` — new; module-level constants and three pure string-returning functions.

### Unit Tests (write first)

- `tests/test_attribution.py` — covers:
  - `test_commit_trailer_default_emits_canonical_string` — exact byte-equality against the locked string for `commit_trailer(model="Claude Opus 4.7 (1M context)")`. Includes the leading `🤖`, the `[QorLogic SDLC](...)` link with the canonical URL, the `on [Claude Code](https://claude.com/claude-code)` clause, the blank separator line, and the `Co-Authored-By:` line with `<noreply@anthropic.com>`.
  - `test_commit_trailer_model_arg_changes_only_coauthor_line` — passing a different `model` shifts only the `Co-Authored-By:` line; the attribution line stays identical.
  - `test_commit_trailer_kwargs_override_constants` — `sdk_name`, `sdk_url`, `qor_url`, `model_email` kwargs each replace the corresponding default; non-overridden fields keep the constant value (proves single source of truth).
  - `test_pr_footer_substitutes_defects_list` — `pr_footer(model=..., defects_list="1. foo\n2. bar")` produces the issue's claim-with-evidence shape with the supplied list inlined.
  - `test_pr_footer_omits_comparison_link_when_none` — when `comparison_doc_path=None`, the trailing `See <path> for the side-by-side.` sentence is absent; when supplied, the path appears verbatim.
  - `test_pr_footer_uses_canonical_qor_url` — default URL in the rendered footer is the locked canonical.
  - `test_changelog_attribution_line_is_locked_format` — exact byte-equality: `_Built via [QorLogic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._` (single line, italic, trailing period inside the underscore).
  - `test_no_em_dash_in_any_emitted_string` — invokes all three functions with default and overridden inputs, asserts `"—"` (em-dash) and `"–"` (en-dash) appear in none of the outputs. Guards against drift toward smart-punctuation.
  - `test_module_constants_are_the_only_default_source` — invokes each function with no overrides, then mutates the module constants via `monkeypatch.setattr` and re-invokes; asserts the second call reflects the mutation. Confirms there are no shadow defaults inside function bodies.

Run: `python -m pytest tests/test_attribution.py -v` (matches CI's `python -m pytest tests/ -v`).

### Implementation

`qor/scripts/attribution.py`:

```python
"""Canonical attribution strings for QorLogic-SDLC-authored work.

Pure functions returning trailer/footer/CHANGELOG-line strings. Module-level
constants hold the SDK identity and canonical QorLogic URL; pass kwargs to
override per-call. The model name is the only required argument.

The leading "\U0001F916" (robot emoji) on commit trailers and PR footers is a
documented exception to the project ASCII-only rule, scoped to bot-attribution
text. See qor/references/doctrine-attribution.md for the rationale.
"""
from __future__ import annotations

_SDK_NAME = "Claude Code"
_SDK_URL = "https://claude.com/claude-code"
_QOR_URL = "https://github.com/MythologIQ-Labs-LLC/qor-logic"
_MODEL_EMAIL = "noreply@anthropic.com"


def commit_trailer(
    model: str,
    *,
    sdk_name: str = _SDK_NAME,
    sdk_url: str = _SDK_URL,
    qor_url: str = _QOR_URL,
    model_email: str = _MODEL_EMAIL,
) -> str:
    ...


def pr_footer(
    model: str,
    *,
    defects_list: str,
    comparison_doc_path: str | None = None,
    sdk_name: str = _SDK_NAME,
    sdk_url: str = _SDK_URL,
    qor_url: str = _QOR_URL,
) -> str:
    ...


def changelog_attribution_line(*, qor_url: str = _QOR_URL) -> str:
    ...
```

Functions are pure: no I/O, no env reads, no time/random. Each returns a `str` whose exact format the tests pin.

Constraints satisfied:

- Pure values, no state (Hickey: prefer values).
- Zero coupling to harness env, gate artifacts, or session state — separable from skill wiring (Hickey: avoid complecting attribution-text generation with session detection).
- Single source of truth: changing `_QOR_URL` or `_SDK_NAME` updates every emitted string.

## Phase 2: Doctrine + ATTRIBUTION.md + Authority link

### Affected Files

- `tests/test_attribution_docs_consistency.py` — new; asserts doc files contain the canonical strings the helper emits.
- `qor/references/doctrine-attribution.md` — new; full doctrine.
- `ATTRIBUTION.md` — new; root quick-ref.
- `CLAUDE.md` — edit the `Authority` line at the bottom to add a link to the new doctrine alongside the existing four.

### Unit Tests (write first)

- `tests/test_attribution_docs_consistency.py` — covers:
  - `test_root_attribution_md_contains_canonical_commit_trailer` — invokes `commit_trailer("Claude Opus 4.7 (1M context)")` and asserts the returned string appears verbatim inside `ATTRIBUTION.md`. Drift guard between code and doc.
  - `test_root_attribution_md_contains_canonical_changelog_line` — same pattern for `changelog_attribution_line()`.
  - `test_doctrine_file_contains_canonical_commit_trailer` — same verbatim check against `qor/references/doctrine-attribution.md`.
  - `test_claude_md_authority_line_links_doctrine_attribution` — reads `CLAUDE.md`, asserts the substring `[attribution](qor/references/doctrine-attribution.md)` appears on the Authority line.
  - `test_pr_footer_template_in_doctrine_uses_placeholders` — asserts the doctrine's PR-footer example uses literal `{defects_list}` and `{comparison_doc_path}` (not pre-substituted text), so readers see the helper's contract, not a one-off rendering.

Run: `python -m pytest tests/test_attribution_docs_consistency.py -v`.

### Doctrine content (`qor/references/doctrine-attribution.md`)

Sections:

1. **Purpose.** When work is shaped by the QorLogic SDLC gates, attribution should name the framework alongside the model. Names what gets credited (the audit gate, Section 4 razor, Merkle ledger), not just who pressed the keys.
2. **When to apply.** Only on commits/PRs/releases produced under a QorLogic gate sequence (`/qor-plan` → `/qor-audit` → `/qor-implement` → `/qor-substantiate`). Ad-hoc Claude Code sessions keep the existing `Generated with [Claude Code]` trailer. No automatic detection in this phase — caller decides.
3. **Canonical strings.** The three rendered outputs of `qor/scripts/attribution.py`, shown verbatim. Each is captioned with the function name that produces it.
4. **Helper API contract.** Function signatures, default constants, override semantics. Notes that the model arg is required (varies per session) and everything else has a sensible default (rarely changes).
5. **Emoji exception (narrow).** The CLAUDE.md "no non-ASCII chars in code/data" rule excepts bot-attribution trailer text. Rationale: the `🤖` is the visual GitHub-UI signal that a trailer is bot-authored; dropping it loses continuity with the existing `Generated with [Claude Code]` convention readers already recognize. Exception is scoped — does not extend to commit subject lines, code identifiers, log messages, or any other surface.
6. **CHANGELOG placement.** The italic attribution line goes beneath the version header, not on it. Preserves the `## [X.Y.Z] - YYYY-MM-DD` parser contract in [changelog_stamp.py](qor/scripts/changelog_stamp.py). Insertion is out of scope for Phase 45; helper exposes the line for future wiring.
7. **Worked example.** Cites issue #18's BicameralAI MCP PR as the originating use case.

### Root `ATTRIBUTION.md` content

One screen. Three sections:

1. One-paragraph summary: "If your commit/PR/release was produced via the QorLogic SDLC gates, use these strings instead of the default Claude Code trailer."
2. The three canonical strings, fenced, copy-pasteable.
3. Pointers: link to the doctrine for rationale, link to `qor/scripts/attribution.py` for the canonical source.

No rationale duplicated from the doctrine. If the doctrine moves, this file's links are the only thing to update.

### `CLAUDE.md` Authority line

Current:

```
Full doctrines: [token-efficiency](qor/references/doctrine-token-efficiency.md), [test-discipline](qor/references/doctrine-test-discipline.md), [governance-enforcement](qor/references/doctrine-governance-enforcement.md).
```

Change: append `, [attribution](qor/references/doctrine-attribution.md)` before the period. No other CLAUDE.md change.

## CI Commands

To validate this plan locally before pushing:

```
python -m pytest tests/test_attribution.py tests/test_attribution_docs_consistency.py -v
python -m pytest tests/ -v
python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
```

The first command is the focused phase-45 suite; the remaining three match the gates in `.github/workflows/ci.yml`.
