# Phase 269: three unverified assumptions about external state

**change_class**: hotfix
**Issues**: GH #427, GH #429, GH #445
**Research**: docs/research-brief-unverified-external-state-2026-09-07.md
**Iteration**: 7 (iterations 1-3 VETOed; 4, 5 and 6 PASSED; 6 amended during implementation -- see below)
**Session**: 2026-09-07T1643-325626

## Changes after the iteration-4 and iteration-5 verdicts

Iteration 4 received a PASS. These three edits were made afterwards, from the reviewer's non-blocking notes, and were therefore NOT part of the audited document. They are the reason this iteration exists rather than proceeding to implementation on iteration 4's verdict.

- `PlatformMarkerError`'s base class was raised against iteration 2 and left undeclared in iterations 2 through 4. Now stated as `Exception`, with why neither alternative works.
- The Affected-files enumeration for `qor_platform.py` named two CLI surfaces where the design section changes four.
- The `Set-Content` row asserted `UnicodeDecodeError` unconditionally in its summary cell while its own middle cell said otherwise.

Two of the three are corrections to the record. The third is not: the audited document contained no decision about the exception hierarchy, so declaring the base class does not change a decision, it supplies one that was absent. That makes this re-audit substantive rather than ceremonial, because nobody had reviewed the thing that now exists. An amendment filling a gap the audited text left open is exactly the kind that needs review.

They are recorded here because an amended plan is a different artifact from the one that passed, and proceeding on the earlier verdict would bind the seal to a document nobody audited.

**After the iteration-5 verdict**, five further edits, and they differ in kind from the three above. Four were pre-authorised: the reviewer specified their wording in the verdict itself, so they were reviewed before they were made. They are the undercount at the head of this section, the sentence immediately above, the packaging bullet in Limitations, and the deletion of a probe count that restated an enumeration two lines below it. The fifth was not pre-authorised: the `_canonical` comment was rewritten from a non-blocking nit for which no wording was given, and it was read and confirmed afterwards.

The distinction matters more than the edits do. The post-iteration-4 amendments were unreviewed when made, which is what forced iteration 5. The post-iteration-5 edits were not, with one exception that was reviewed after the fact. A reader following this section should be able to reconstruct which text carried a verdict and which did not.

## Changes during implementation

Implementation was carried out against iteration 6, which had a PASS. Three things were found while doing it, all of the same class, and the design changed in response. They are recorded here rather than folded in silently.

**The rule replaced the enumeration.** Iteration 6's D1 caught `(OSError, TOMLDecodeError, UnicodeDecodeError)`. That list was wrong twice more. `tomllib` is recursive-descent, so a deeply nested foreign pyproject raises `RecursionError`, measured at nesting depth 2000; an oversized one raises `MemoryError`. Both escape, both stop every gate write. The fix is not a fourth exception. It is one rule applied to both readers: every call into external state is wrapped in `except Exception`, and none of our own logic sits inside a handler. Enumeration is the wrong tool for a total contract because it predicts an open set, and it failed three times in this function alone.

**The second reader had the same defect, plus one nobody predicted.** `importlib.metadata.version` was guarded by `PackageNotFoundError` alone. Measured against damaged `.dist-info` directories: an undecodable `METADATA` raises `UnicodeDecodeError` and escapes; and in three of four damaged states the call RETURNS `None` rather than raising. `_read_system_version` is annotated `-> str` and the provenance schema requires a non-empty string, so a damaged install produced a schema-invalid gate artifact rather than a visible failure. Enumerating exits means enumerating return values, not only raises.

**The third reader had it too.** `_read_marker`'s `except json.JSONDecodeError` misses `RecursionError`, measured at nesting depth 5000 on CPython 3.11. The test injects the failure rather than provoking it: CPython 3.12 parses inputs 3.11 rejects, so asserting a depth would test the runtime rather than this code, which CI proved by failing on 3.12 and 3.13 while 3.11 and Windows passed. Its parse step is now total over content, while its read step still enumerates deliberately, because that step classifies three ways (absent, unreadable, propagate) rather than promising totality. The two differ for a stated reason.

**And the rule was not applied to `current()` itself.** It propagated every `OSError` except `FileNotFoundError`. `ai_provenance._detect_host` calls `current()` outside its import guard, so `build_manifest` raised and no gate artifact could be written -- measured, a permission-denied marker killed the write. That is the identical consequence this section cites as decisive for D1, retained in D2 with the difference in judgement defended nowhere. `current()` is now total by contract; `_read_marker` keeps the three-way classification, and the surfaces that can act on it (`set_capability`, CLI `get`, CLI `check`) call it directly, so an operator diagnosing a permission-broken marker still gets a true answer.

Five instances of one class in one change, four of them found after the design had passed review. What closes it is the rule, not the patches -- and the fifth was found by asking where the rule had NOT been applied.

## Problem

Three readers trust external state without checking it. Environments, measurements and the sweep that scopes #445 are in the research brief and are not restated here.

## What the earlier iterations got wrong

Recorded because the corrections define the design.

- **Iteration 1's D1 parsed the foreign file before deciding it was foreign.** A malformed pyproject at the computed path raised out of `_read_system_version`, which `build_manifest` calls unconditionally, turning "wrong version stamped" into "no gate artifact can be written" in the exact installed environment the phase exists to protect.
- **Iteration 1's D2 introduced silent data loss.** `set_capability` is `current(marker) or {defaults}` followed by a write (`qor_platform.py:177-187`). Returning `None` for a corrupt marker makes it synthesise defaults and overwrite. Demonstrated: a marker declaring three capabilities was rewritten to one, with no error.
- **Both are the same error.** The plan checked that `None` was an accepted value and never asked what each caller DOES with it. Consistency, not reach.
- **A direction of mine between iterations, narrowing D2 to `JSONDecodeError` alone, was also wrong.** It would have left GH #429 unfixed in its likeliest shape. See D2.
- **Iteration 2 deleted the only test of the no-file path** in the same edit that made that path depend on an exception hierarchy rather than a visible branch. Restored below.

## Design

### D1: establish that the file is ours before trusting anything in it (GH #427)

Requires `import re` and `import importlib.metadata`; `ai_provenance.py:15-22` currently imports neither, and `import importlib` alone does not bind the submodule.

```python
_PROJECT_NAME = "qor-logic"

def _canonical(name: str) -> str:
    # PEP 503, applied to the UNTRUSTED name out of the foreign file. The
    # metadata call below passes _PROJECT_NAME, already canonical, so this is
    # the only side that normalises: its job is to stop us rejecting a spelling
    # that metadata itself would have resolved.
    return re.sub(r"[-_.]+", "-", name).lower()


def _read_system_version() -> str:
    """Resolve this project's version, from the only sources that can know it.

    Phase 269 (GH #427): _REPO_ROOT resolves to site-packages under an installed
    package, so _PYPROJECT may be a FOREIGN project's file that merely sits at
    the path we computed. EVERY failure to establish the file as ours falls
    through to metadata: nothing about a stranger's file, not even an exception,
    may escape a provenance helper, because build_manifest calls this on every
    gate artifact and a raise here means no gate can be written at all.

    Order is load-bearing. pyproject is authoritative in a source checkout;
    metadata reports the last install and would under-report a working tree.
    """
    # One rule, applied to both readers: every call into external state is
    # wrapped in `except Exception`, and none of our own logic sits inside a
    # handler. Enumerating exceptions is the wrong tool for a total contract
    # because it predicts an open set -- three escapes were found that way
    # here (UnicodeDecodeError from the decode tomllib owns, RecursionError
    # from its recursive-descent parse, MemoryError on an oversized file).
    # Any Exception from the call means we could not read a stranger's file.
    try:
        with _PYPROJECT.open("rb") as fh:
            data = tomllib.load(fh)
    except Exception:
        data = None

    # Outside every handler from here down, so our own bugs stay loud.
    if isinstance(data, dict):
        project = data.get("project", {})
        if isinstance(project, dict) and _canonical(str(project.get("name", ""))) == _PROJECT_NAME:
            version = project.get("version")
            if isinstance(version, str) and version:
                return version
            # Ours, but dynamic = ["version"]. The name selects the SOURCE, not
            # the RESULT; metadata knows what this file does not state.
    try:
        version = importlib.metadata.version(_PROJECT_NAME)
    except Exception:
        # Same rule as above. metadata parses METADATA out of a .dist-info,
        # so a damaged install raises past PackageNotFoundError; an undecodable
        # METADATA gives UnicodeDecodeError. Any Exception here means we could
        # not obtain a version, which is what a total function needs.
        return "unknown"
    # version() returns None for a .dist-info with no METADATA, or one with no
    # Version field. The schema requires a non-empty string, so a None here
    # would emit an invalid gate artifact rather than an ugly one.
    return version if isinstance(version, str) and version else "unknown"
```

`exists()` is gone: `open()` raises `FileNotFoundError`, a subclass of `OSError`, which removes a stat-then-read race rather than adding a branch. That makes the clean-install path depend on three implicit facts instead of one visible conditional, which is why its test is restored rather than dropped.

The claim that `_canonical` agrees with `importlib.metadata`'s internal normalisation is measured, not assumed. Probed with `qor-logic`, `qor_logic`, `qor.logic`, `QOR-LOGIC`, `Qor_Logic`, and the adversarial `qor__logic` and `qor-.-logic`: each canonicalises to this project's name and each resolves through metadata. The negative control `qorlogic` canonicalises differently and raises `PackageNotFoundError`. No disagreement. The sentence was supplied by the reviewer, believed by both of us, and unverified until checked; it is destined for a shipped code comment, which is why it was checked rather than carried.

Both readers are wrapped in `except Exception`, and none of this function's own logic sits inside a handler. That is one rule rather than two lists, and it is here because three enumerations failed: `UnicodeDecodeError` from the decode `tomllib` owns, `RecursionError` from its recursive-descent parse, and the metadata handler that caught only `PackageNotFoundError`. The coercion on the last line sits OUTSIDE the `try` deliberately, so a bug in `_canonical` or in the coercion still raises rather than degrading to "unknown".

`importlib.metadata.version` also RETURNS `None` for a `.dist-info` with no `METADATA` or no `Version` field, which no exception handling reaches. The schema requires a non-empty string, so that path emitted an invalid gate artifact rather than a visible failure. Enumerating exits means enumerating return values, not only raises.

`isinstance(project, dict)` guards a shape assumption inherited from the current code (`ai_provenance.py:58`): `project = "text"` is legal TOML and makes the subsequent `.get` raise.

The "our own broken manifest should be loud" property cannot live in this function, which by construction does not know whose file it holds until after the parse. It moves to a test asserting the checkout's own pyproject parses and names this project.

**The fallback now warns.** `host` and `model_family` each `_warn_once` when they fall back to `"unknown"` (`ai_provenance.py:124-132`); `version` has no equivalent, and the docstring at `:120` already advertises `QOR_PROVENANCE_QUIET=1`, so `version` is the single field outside an established convention. D1 makes `"unknown"` more reachable, not less: a vendored tree fails the name check and then finds no installed distribution. The warning goes inside the `if system_version is None:` block at `:134-135`, so a caller passing an explicit value is never second-guessed.

### D2: one reader that distinguishes absent from unreadable (GH #429)

The distinction that matters is not the exception type. It is **"the bytes are not our state"** versus **"we could not read the bytes."** Discard the first; do not let the second silently become absence **at the surfaces that write or diagnose**. See Limitations for the read-only callers where the two remain conflated.

```python
def _read_marker(marker: Path) -> tuple[dict | None, str]:
    """Return (state, status) where status is 'ok', 'absent' or 'unreadable'.

    Phase 269 (GH #429). The distinction that matters is not the exception type
    but "the bytes are not our state" versus "we could not read the bytes".
    Discard the first; never let the second masquerade as absence at a surface
    that writes or diagnoses.

    One read, so no caller re-stats the file and races itself.
    """
    try:
        raw = marker.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, "absent"
    except UnicodeDecodeError:
        # A Windows operator hand-editing the marker does not necessarily write
        # UTF-8: Out-File on stock PowerShell 5.1 emits UTF-16LE, and
        # Set-Content emits the ANSI codepage, which fails to decode whenever
        # the content is not pure ASCII. A UTF-8 BOM fails at json instead.
        return None, "unreadable"
    # Any other OSError propagates: unreadable-for-permissions is not absence.
    # The READ above classifies deliberately, so it enumerates. The PARSE below
    # does not: content that cannot be parsed is "not our state" whatever the
    # reason, so it is total over content. json.loads is recursive, so depth
    # alone raises RecursionError, which an enumeration of JSONDecodeError
    # misses -- the same class that escaped two readers in ai_provenance.
    try:
        data = json.loads(raw)
    except Exception:
        return None, "unreadable"
    if not isinstance(data, dict):
        # Valid JSON that is not an object reaches no exception handler at all,
        # which is why this lives in the reader rather than in each caller.
        return None, "unreadable"
    return data, "ok"


def current(marker: Path | None = None) -> dict | None:
    """Platform state, or None if it cannot be obtained for any reason.

    Total by contract. Every caller of this shim sits in a gate-writing or
    capability-gating path that has a correct degraded answer, and a raise here
    means no gate artifact can be written at all -- the same consequence that
    made an enumeration unusable in ai_provenance._read_system_version.

    The three-way classification is not lost. Callers that can act on the
    difference -- set_capability, and the CLI get and check handlers -- call
    _read_marker directly, so an operator diagnosing a permission-broken marker
    still gets a true answer from the surfaces they would use.
    """
    try:
        return _read_marker(marker or MARKER_PATH)[0]
    except OSError:
        return None
```

`UnicodeDecodeError` is included deliberately, because a Windows operator hand-editing the marker does not necessarily write UTF-8. Measured on this workspace:

| Written by | Encoding | Surfaces as |
|---|---|---|
| `Set-Content` | ANSI codepage | `UnicodeDecodeError`, but only when the content carries non-ASCII |
| `Out-File` on stock PowerShell 5.1 | UTF-16LE | `UnicodeDecodeError` |
| `Out-File` as configured on this workspace | UTF-8 with BOM | `JSONDecodeError` |

Excluding `UnicodeDecodeError` leaves GH #429 unfixed for UTF-16 outright, and for the ANSI case whenever the content is not pure ASCII. The BOM case is already covered. Non-dict JSON reaches no exception handler at all today, which is why the isinstance check lives in the reader rather than in a wider `except`.

The same argument applies harder to D1, where the encoding is chosen by someone else entirely: Latin-1 with an accented author name is at least as likely in a stranger's pyproject as UTF-16 is on a marker this repo writes itself.

**The write path is what protects the data, not the exception tuple.** With that separated, the read path is free to be forgiving:

```python
def set_capability(name: str, value, marker: Path | None = None) -> dict:
    marker = marker or MARKER_PATH
    state, status = _read_marker(marker)
    if status == "unreadable":
        # detect.md and capabilities.md both state that user declarations are
        # never overwritten, and apply/clear are the only documented resets.
        # Synthesising defaults here would discard every declared capability.
        raise PlatformMarkerError(
            f"{marker} exists but cannot be read as platform state; "
            f"refusing to overwrite. Inspect it, or run `clear` to reset."
        )
    state = state or {  # defaults exactly as today
```

`PlatformMarkerError` derives from `Exception`, and specifically not from `OSError` or `ValueError`. An `OSError` subclass would collide with `_read_marker`'s "any other OSError propagates" contract above; a `ValueError` subclass would become catchable by the `_parse_bool` guard at `qor_platform.py:283-285` the moment anyone reorders those lines.

Obligatory rather than optional: `qor/platform/detect.md:30` and `qor/platform/capabilities.md:85` both state in bold that user declarations are **never** overwritten, and `detect.md:40-44` names `apply` and `clear` as the only reset paths. Iteration 1's behaviour contradicted a shipped contract in two files.

The refusal cannot strand an operator: `clear()` is exists-then-unlink (`qor_platform.py:207-211`) and `apply_profile()` builds fresh state and writes (`:158-172`). Neither reads the marker, so both documented remedies survive a `PlatformMarkerError`.

**All three CLI surfaces need work, and one is not what iteration 2 claimed.** `set_capability` is called OUTSIDE the `try` in the `set` handler (`qor_platform.py:282-289`), and that `try` catches `ValueError` from `_parse_bool` only, so `PlatformMarkerError` would escape `main()` and print a traceback rather than the message above. The `apply` handler at `:274-278` is the pattern to copy: catch, print `ERROR: {e}` to stderr, return 2. The `get` handler (`:255-259`) prints "(no platform marker)" for a corrupt marker sitting on disk, which is actively false and is the one surface an operator uses to diagnose this; it gains a distinct message and keeps a nonzero exit. The `check` handler (`:291-294`) prints "not available" and exits 1 on a corrupt marker, which is the same false statement on the surface a script is likeliest to call; it gains a distinct message and exit code 2, so a caller can tell "not available" from "cannot tell". A third code cannot break an `if`-style consumer, which treats every nonzero alike, and the only documented expectation of `check` is "non-zero" (`docs/plan-qor-phase6-platform.md:130`); nothing in `qor/`, `tests/`, CI or skill prose shells out to it.

### D3: delete the figure, keep the clause (GH #445)

In `ledger_hash._report_sequence`, "a pre-existing Section 4 violation at 97 lines" becomes "a pre-existing Section 4 length violation". The normative clause a contributor acts on survives; the number that rots does not.

**No guard is built, and none is claimed.** An earlier iteration proposed an AST sweep asserting no docstring claims a stale line count. After D3 that assertion runs over an empty corpus, giving it two indistinguishable green states: nothing is wrong, or the sweep is broken. A regex typo, a changed root, a shifted layout or a swallowed parse error all leave it green. Making it honest would need a positive control, a wider pattern than `<name> ... at N lines`, and fail-closed handling of names it cannot resolve, which is more machinery than a single-instance defect earns. The research brief already concluded that the cure here is deletion rather than a checker; a half-checker would contradict that while advertising coverage the suite does not have.

D3 rides in this phase because it is now a one-line docstring edit with no machinery of its own, and it is the same defect family as D1 and D2: a statement about external state that nothing re-derives. Splitting it would cost a full ceremony for one deleted number.

## Tests

Metadata is monkeypatched in every row that can reach it. CI installs editable, so `importlib.metadata.version("qor-logic")` resolves there but returns a stale value on a developer workspace; a row asserting against it unmocked would compare different values in the two places, which this project's test discipline forbids.

| Test | Pins | Red before |
|---|---|---|
| `test_version_ignores_a_foreign_pyproject` | a foreign-named pyproject is not read for version; asserts NOT the foreign value | yes |
| `test_version_survives_a_malformed_foreign_pyproject` | falls through to metadata, does not raise | yes |
| `test_version_survives_a_non_table_project_key` | `project = "text"` does not raise | yes |
| `test_version_survives_a_non_utf8_pyproject` | a stranger's file in any encoding cannot stop a gate write | yes |
| `test_version_falls_back_to_metadata_when_no_pyproject` | the clean wheel install, and the OSError fall-through it now depends on | yes |
| `test_version_falls_through_when_ours_declares_dynamic_version` | name selects source, not result | yes |
| `test_version_warns_once_when_it_falls_back_to_unknown` | the missing warning; clears `_warned_keys` first | yes |
| `test_version_accepts_pep503_spellings_of_the_name` | `qor_logic` and `qor.logic` recognised | no |
| `test_project_name_constant_matches_this_repos_pyproject` | a rename cannot silently disarm the discriminator | no |
| `test_this_repos_pyproject_parses_and_names_this_project` | the "our manifest is loud" property, where it belongs | no |
| `test_current_returns_none_on_a_corrupt_marker` | truncated write degrades | yes |
| `test_current_returns_none_on_utf16_bytes` | the Windows hand-edit shape | yes |
| `test_current_returns_none_on_non_dict_json` | a list is no longer returned as state | yes |
| `test_current_returns_none_on_a_permission_error` | current() is total; its callers write gates | yes |
| `test_set_capability_refuses_to_overwrite_an_unreadable_marker` | the data-loss defect | yes |
| `test_set_capability_still_creates_a_marker_when_absent` | the fix does not break first run | no |
| `test_is_available_is_false_on_a_corrupt_marker` | caller-level degradation | yes |
| `test_cli_get_distinguishes_absent_from_unreadable` | the diagnosis surface | yes |
| `test_cli_set_reports_an_unreadable_marker_without_a_traceback` | the refusal reaches the operator as a message | yes |
| `test_cli_check_distinguishes_unavailable_from_unreadable` | the exit code a script branches on | yes |
| `test_version_survives_a_damaged_metadata_lookup` | the second reader escapes its own guard | yes |
| `test_version_is_a_string_when_metadata_returns_none` | metadata RETURNS None, which no handler reaches | yes |
| `test_build_manifest_stays_schema_valid_when_no_version_resolves` | the consequence: an invalid gate artifact, not an ugly one | yes |
| `test_version_survives_a_deeply_nested_foreign_pyproject` | RecursionError from a recursive-descent parse | yes |
| `test_read_system_version_is_total` | build_manifest calls it unconditionally, so it may never raise | yes |
| `test_a_bug_in_our_own_coercion_still_raises` | the other half of the rule: our bugs stay loud | no |
| `test_version_reads_a_pyproject_that_names_this_project` | the source-checkout path still works | yes |
| `test_version_is_unknown_when_neither_source_answers` | the terminal fallback | yes |
| `test_version_does_not_warn_when_explicitly_passed` | a caller's explicit value is not second-guessed | no |
| `test_platform_marker_error_is_not_an_oserror_or_valueerror` | the base class is load-bearing | yes |
| `test_current_returns_none_on_a_non_jsondecodeerror_parse_failure` | the fourth instance, in the third reader | yes |
| `test_read_marker_still_propagates_permission_errors` | widening the parse must not swallow the read classification | no |
| `test_diagnosis_surfaces_still_see_a_permission_error` | loudness stays where an operator can act on it | no |
| `test_build_manifest_survives_a_permission_denied_platform_marker` | a marker we cannot read must not kill every gate write | yes |

Rows marked "no" in the column pin invariants that already hold and exist so a later change cannot break them silently. They are labelled rather than presented as regression evidence.

Measured at implementation: the D2 rows produced exactly the predicted split, nine red with both "no" rows passing. Two D1 rows labelled "no", `test_project_name_constant_matches_this_repos_pyproject` and `test_this_repos_pyproject_parses_and_names_this_project`, did fail before the change, but for a trivial reason rather than a behavioural one: they call `_canonical`, which did not yet exist. The property each pins was already true. That is the mirror of the vacuity problem, a red that demonstrates nothing, and the column keeps "no" because the alternative would claim regression evidence the rows do not carry.

`test_current_propagates_permission_errors` monkeypatches `Path.read_text` to raise `PermissionError` rather than using `os.chmod(path, 0)`, which does not make a file unreadable to its owner on Windows and would exercise nothing on this workspace. It asserts the error escapes `current()`, the surface every caller uses, not `_read_marker`.

`test_version_warns_once_when_it_falls_back_to_unknown` clears `ai_provenance._warned_keys` first, matching `tests/test_ai_provenance_helper.py:83, 102, 120`; the set is a module global and a test that does not clear it passes or fails according to what ran before it.

## Affected files

- `qor/scripts/ai_provenance.py` (D1, plus the version fallback warning and two new imports)
- `qor/scripts/qor_platform.py` (D2: `_read_marker`, `current`, `set_capability`, CLI `get`, `set` and `check`, new `PlatformMarkerError` deriving from `Exception`)
- `qor/scripts/ledger_hash.py` (D3, docstring only)
- `qor/gates/schema/_provenance.schema.json` (D1: the `version` description says "read from pyproject.toml at manifest-build time", true only in a checkout after this change)
- `qor/platform/detect.md`, `qor/platform/capabilities.md` (D2: the never-overwritten invariant gains a refusal path; `is_available`'s enumerated conditions gain a corrupt-marker case; `check`'s three exit codes documented, since neither file lists them today and a new code discoverable only from source is a signal nobody knows to look for)
- `tests/test_ai_provenance_helper.py`, `tests/test_platform.py`

## CI Commands

```
python -m pytest tests/test_ai_provenance_helper.py tests/test_platform.py -q
python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md
python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .
python -m qor.scripts.publication_boundary_lint
python -m qor.scripts.gate_provenance verify-committed
python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto
python -m pytest -q
```

## Limitations

- **D2's distinction is drawn at the write and diagnosis surfaces only.** `current()` returns `None` for unreadable, so `is_available`, `availability`, `qor_audit_runtime.should_run_adversarial_mode`, `ai_provenance._detect_host` and `execution_context._platform_context` still treat unreadable as absent. The consequence is not cosmetic: a corrupt marker makes `should_run_adversarial_mode` return False and `emit_capability_shortfall` record that a capability "is not available on this host" when the truth is that platform state could not be read, so a gate artifact carries a false cause. That is against the Phase 252 rationale at `qor_platform.py:303-308` in its own terms. Not fixed here; naming it rather than leaving the headline to imply the class is closed.
- If the marker is unreadable for permissions, `clear`'s `unlink()` may itself fail, since deletion depends on directory rights rather than file rights. The refusal message still points at the right remedy; the operator may need to fix permissions first.
- `set_capability` gaining a raise is a behaviour change, not purely a fix. It restores the documented invariant, and the alternative is data loss, but a caller that today survives a corrupt marker by accident will now see an exception. It has one non-test caller, the CLI `set` handler.
- D1 is unverifiable from the checkout alone: the failing environment is an installed package beside a foreign pyproject, and the tests reach it with a synthetic path rather than a real install. They pin the discriminator, not the deployment.
- **D3 removes one instance and guards nothing.** GH #445 is closed on that basis, not on a claim of class coverage.
- `create_shadow_issue.py:56` reads a DIFFERENT marker with the same unguarded `json.loads` shape. Same class, out of scope here, unfiled.
- The installed-environment witness is confirmed first-hand by the author, who imported the installed module and read the file it resolves to, and is unverified by the reviewer, who holds read-only tools. What is open is not whether the file is there but how typical that placement is: a package shipping `pyproject.toml` to the site-packages root is unusual. The defect does not depend on the answer, because `_REPO_ROOT` provably resolves to site-packages under an install, so whatever sits at that path is read regardless of what put it there.
- No committed artifact's `version` field changes, for the reason in the brief's Reach section.
