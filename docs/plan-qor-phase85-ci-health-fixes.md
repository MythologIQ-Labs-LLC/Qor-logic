# Plan: Phase 85 — CI-health fixes (canonical-trailer integrity + drift-report scan hoist)

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: GH #96

**boundaries**:
- limitations: the two non-compliant historical seal commits (`ce138b2`
  phase 83, `fb052e4` phase 82) are NOT fixed in place. Rewriting published
  `main` history is rejected as destructive and disproportionate; they are
  disclosed as a grandfathered exception instead. The seal-trailer guard
  inspects commit-message text only; it does not parse git trailers via
  `git interpret-trailers`.
- non_goals: not changing the squash-vs-merge PR-merge policy (squash
  preserves the trailer — the earlier squash-merge hypothesis was
  disconfirmed); not optimizing other live-repo CLI tests; not raising the
  `doc_integrity_drift_report` test timeout (the perf fix removes the need).
- exclusions: `_excluded_by_scope_fence` semantics, the glossary parser,
  and the drift-finding message text are unchanged — the scan hoist is
  behavior-preserving.

## Open Questions

None.

## Design notes

**Cutoff: exception set, not a floor raise.** The `/qor-debug` analysis
offered two readings of the FIX A cutoff change — raise the `phase < 49`
floor to `phase < 85`, OR keep the floor and add an explicit grandfather
exception set. This plan chooses the **exception set** (`frozenset({82, 83})`,
floor stays 49). Raising the floor to 85 would silently drop trailer
coverage for every phase 49-84 seal — most of which (75-81, 84) are
compliant and worth keeping under test, and a future regression at e.g.
phase 86 would still be caught only because 86 > 85. The exception set
gets CI green identically while keeping strict coverage for all phases
except the two provably non-compliant historical commits. This is the
Simple/precise choice: it removes exactly the failing input, nothing more.

**Single source of truth for "full trailer".** The test currently inlines
the trailer check (`"Qor-logic" in body and "Authored via" in body` plus a
`Co-Authored-By:` regex). FIX A introduces `attribution.message_has_full_trailer`
as the one definition, consumed by BOTH the doctrine test and the new
substantiate-time guard, so the test and the guard cannot drift apart.

## Phase 1: Canonical-trailer integrity (GH #96 FIX A)

The `test_seal_commits_after_cutoff_have_full_canonical_trailer` test is red
on `main`: phase 82/83 seal commits carry only the compact `Co-Authored-By:`
line, missing the `Authored via [Qor-logic SDLC]` line of the canonical
trailer. The test is correct — it caught a real doctrine violation. This
phase disclosure-grandfathers the two historical commits and adds a
substantiate-time guard so a seal commit can never again be created without
the full trailer.

### Affected Files

- `tests/test_seal_trailer_guard.py` - NEW. Behavior tests for
  `attribution.message_has_full_trailer` and the `seal_trailer_check` CLI.
- `tests/test_attribution_tiered_usage.py` - add `_GRANDFATHERED_SEAL_PHASES`
  frozenset + `_seal_phase_in_scope` helper + helper unit tests; route the
  seal test through `attribution.message_has_full_trailer`; correct the
  inaccurate squash-merge comment.
- `qor/scripts/attribution.py` - add `message_has_full_trailer(message)`
  pure function.
- `qor/scripts/seal_trailer_check.py` - NEW. CLI wrapper that reads a
  commit message and verifies the full trailer.
- `qor/skills/governance/qor-substantiate/SKILL.md` - add Step 9.5.4
  (post-seal-commit trailer verification) and update the Step 9.5
  example-commit-message prose to mandate the full `commit_trailer()` output.
- `qor/references/doctrine-attribution.md` - document the `{82, 83}`
  grandfather exception with rationale and the phase-49 / v0.36.0 dual
  cutoff representation.

### Unit Tests

- `tests/test_seal_trailer_guard.py`
  - `test_message_has_full_trailer_accepts_full_trailer` — call
    `message_has_full_trailer` on the exact output of
    `commit_trailer("Claude Opus 4.7")`; assert it returns `True`.
  - `test_message_has_full_trailer_rejects_compact_only` — call it on a
    message carrying only the `Co-Authored-By:` line (no `Authored via`
    line); assert it returns `False` (this is the phase 82/83 defect shape).
  - `test_message_has_full_trailer_rejects_missing_coauthor` — call it on a
    message with the `Authored via [Qor-logic SDLC]` line but no
    `Co-Authored-By:` line; assert `False`.
  - `test_message_has_full_trailer_accepts_lowercase_coauthor` — call it on
    a full-trailer message whose co-author key is the git/GitHub lowercase
    `Co-authored-by:`; assert `True` (git trailer keys are case-insensitive).
  - `test_cli_exits_zero_on_compliant_seal_commit` — in a tmp git repo,
    create a commit whose message contains the full trailer; run
    `python -m qor.scripts.seal_trailer_check --commit HEAD`; assert
    returncode 0.
  - `test_cli_exits_nonzero_and_names_missing_part` — in a tmp git repo,
    create a commit whose message has only the compact line; run the CLI;
    assert returncode 1 and that stderr names the missing `Authored via`
    line and points at re-committing with the full `commit_trailer()`.

- `tests/test_attribution_tiered_usage.py` (additions)
  - `test_seal_phase_in_scope_excludes_grandfathered` — call
    `_seal_phase_in_scope(82)` and `(83)`; assert both `False` (grandfathered).
  - `test_seal_phase_in_scope_includes_recent_compliant_phases` — call
    `_seal_phase_in_scope(84)` and `(85)`; assert both `True` (a precise
    exception set must NOT blanket-disable checking — this guards against a
    botched "exclude everything" change).
  - `test_seal_phase_in_scope_excludes_below_floor` — call
    `_seal_phase_in_scope(48)`; assert `False` (pre-Phase-49 grandfather).

### Changes

`qor/scripts/attribution.py` — add:

```python
def message_has_full_trailer(message: str) -> bool:
    """True iff a commit message carries the full canonical trailer:
    the `Authored via [Qor-logic SDLC]` line AND a `Co-Authored-By:` line.
    Single source of truth consumed by seal_trailer_check and by
    tests/test_attribution_tiered_usage.py."""
```

It checks `"Authored via" in message and "Qor-logic" in message` and a
case-insensitive multiline `^Co-authored-by:` match — the same predicate
the doctrine test uses today, lifted to one definition.

`qor/scripts/seal_trailer_check.py` — NEW, structured like the existing
`qor/scripts/*_check.py` CLIs. `argparse` with `--commit` (default `HEAD`)
and optional `--repo-root`. Reads the message via
`git log -1 --format=%B <commit>` (argv-form subprocess, list args, no
shell), calls `attribution.message_has_full_trailer`, and on failure prints
to stderr which trailer part is missing plus the remedy (amend the seal
commit so its message contains the full `commit_trailer()` output).
`main()` returns 0 when compliant, 1 otherwise.

`tests/test_attribution_tiered_usage.py` — add module-level
`_GRANDFATHERED_SEAL_PHASES = frozenset({82, 83})` with a comment citing
GH #96 (locally-authored seal commits missing the `Authored via` line;
disclosed not fixed in place). Add `_seal_phase_in_scope(phase_num)` →
`phase_num is not None and phase_num >= 49 and phase_num not in
_GRANDFATHERED_SEAL_PHASES`. `test_seal_commits_after_cutoff_have_full_canonical_trailer`
uses `_seal_phase_in_scope` for the skip decision and
`attribution.message_has_full_trailer(body)` for the trailer verdict. The
inaccurate squash-merge comment is replaced with an accurate one (the
case-insensitive `Co-authored-by:` match handles git/GitHub trailer-key
casing; no claim that squash drops or normalizes the trailer).

`qor/skills/governance/qor-substantiate/SKILL.md` — insert Step 9.5.4
"Seal-commit trailer verification" between Step 9.5 (seal commit) and Step
9.5.5 (annotated tag): run `python -m qor.scripts.seal_trailer_check
--commit HEAD`; on non-zero exit ABORT before tagging, instruct the
operator to amend the seal commit with the full trailer, then re-run. Update
the Step 9.5 example-commit-message prose to state the seal commit message
MUST contain the full `qor.scripts.attribution.commit_trailer()` output
(both lines), not the compact form.

`qor/references/doctrine-attribution.md` — under the tiered-usage section,
add a short note: phases 82-83 seal commits predate the Step 9.5.4 guard
and are a disclosed grandfathered exception in
`test_attribution_tiered_usage.py`; and a note that the Phase-49 enforcement
boundary is represented as `phase >= 49` for commit walks and
`version >= 0.36.0` for CHANGELOG sections (the same boundary, two surfaces).

## Phase 2: Drift-report scan hoist (GH #96 FIX B/C)

`check_term_drift` and `check_cross_doc_conflicts` in
`qor/scripts/doc_integrity_strict.py` call `_iter_scan_files()` inside the
per-term loop, re-walking the tree and re-reading every file once per
glossary term — O(terms x files), ~156k iterations, 68-81s locally. The
`test_doc_integrity_drift_report_cli.py` tests exceed their 60s subprocess
cap. This phase hoists the corpus scan out of the term loop.

### Affected Files

- `tests/test_doc_integrity_strict_corpus_scan.py` - NEW. Fixture-based
  behavior tests proving the hoisted functions return the correct findings.
- `qor/scripts/doc_integrity_strict.py` - add a `_scan_corpus` helper;
  `check_term_drift` and `check_cross_doc_conflicts` materialize the corpus
  once before the term loop.

### Unit Tests

- `tests/test_doc_integrity_strict_corpus_scan.py`
  - `test_check_term_drift_flags_out_of_scope_term_use` — build a tmp repo
    (glossary YAML defining a term whose `referenced_by` omits a doc, plus
    that doc using the term in scope); call `check_term_drift`; assert the
    returned findings list contains exactly the expected
    `Term '<t>' used in <rel> not declared as referenced_by` message.
  - `test_check_term_drift_clean_when_term_in_scope` — same tmp repo but
    with the doc listed in `referenced_by`; call `check_term_drift`; assert
    the returned list is empty.
  - `test_check_cross_doc_conflicts_flags_divergent_definition` — tmp repo
    with a doc defining a glossary term with a body diverging from the
    canonical definition; call `check_cross_doc_conflicts`; assert the
    finding is returned.
  - `test_check_term_drift_strict_raises_on_finding` — call
    `check_term_drift(..., strict=True)` on the out-of-scope fixture;
    assert it raises `ValueError` (strict-mode path unchanged by the hoist).
  - `test_scan_corpus_reads_each_file_once` — call `_scan_corpus` on a tmp
    repo with N markdown files; assert it returns N `(rel, text)` tuples
    and each `text` equals the file's content (proves the materialized
    corpus is correct and de-duplicated — one entry per file).

### Changes

`qor/scripts/doc_integrity_strict.py` — add:

```python
def _scan_corpus(repo_root: str, repo: Path) -> list[tuple[str, str]]:
    """Materialize the in-scope markdown corpus once as (rel_posix, text)."""
    return [
        (f.relative_to(repo).as_posix(),
         f.read_text(encoding="utf-8", errors="replace"))
        for f in _iter_scan_files(repo_root)
    ]
```

`check_term_drift` and `check_cross_doc_conflicts` each call
`_scan_corpus(repo_root, repo)` ONCE before `for entry in entries:`, then
iterate `for rel, text in scanned:` instead of
`for f in _iter_scan_files(...)`. The per-`(entry, rel)`
`_excluded_by_scope_fence` check stays in the inner loop (it is per-term,
cheap, no I/O). Findings content and append order are unchanged — same
files in the same `_iter_scan_files` order, same regex, same scope fence —
so output is byte-identical; only the redundant walks and reads are
removed (~156k -> ~2k file operations).

## CI Commands

- `python -m pytest tests/test_seal_trailer_guard.py tests/test_attribution_tiered_usage.py -q` — Phase 1 guard behavior, CLI exit codes, cutoff-scope helper, and the now-green seal-trailer doctrine test.
- `python -m pytest tests/test_doc_integrity_strict_corpus_scan.py tests/test_doc_integrity_drift_report_cli.py -q` — Phase 2 hoisted-scan findings correctness plus the previously-timing-out CLI tests as the regression proof.
- `python -m pytest tests/ -q` — full regression suite.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase85-ci-health-fixes.md` — plan-internal text-consistency.
