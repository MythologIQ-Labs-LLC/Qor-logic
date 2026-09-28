# Plan: Phase 301 - A shadow issue no longer claims a threshold breach its own numbers do not show

**change_class**: hotfix

**doc_tier**: standard

**terms**: `[]` (this plan introduces no new term; the plan gate artifact carries `terms: []`)

**boundaries**:
- limitations: the breach wording is decided by the plain severity sum of the filed events, the number the header prints, compared with the loaded marker's threshold; it is not the collapsed sum `check_shadow_threshold` computes, so a filing whose plain sum reaches the threshold keeps the breach wording even where the collapsed sum of the same events would not (LD-5); a marker whose schema-valid events are all still unaddressed and present in the events read keeps the breach wording whenever its own threshold test held, because the plain sum of a set is never below its collapsed sum (LD-3); `--events` filings never carry the breach wording, even at a plain sum at or above the threshold, because no threshold test ran (LD-2)
- non_goals: recomputing the collapsed sum or any other part of the breach predicate in `create_shadow_issue`; changing when the marker is written or removed; changing `collect_shadow_genomes` (its own title, body and configured threshold); changing the `--flip-only` or `--mark-resolved` paths; the second `MARKER_PATH` definition; release publication
- exclusions: issues already filed, whose titles and bodies this plan does not rewrite (LD-5)

**iteration**: 1 (on branch `phase/301-shadow-breach-header`)

**Issue**: GH #474 ("build_body reports a threshold breach whose own numbers are below the threshold; the threshold constant has two owners")

**Current base**: `e062a3dd8d9499b678ff6f694107dd57a0d7f311` (`main` after Phase 300 merged; project version `0.175.4`, sealed at META_LEDGER #829)

**Target version**: `0.175.5` (hotfix bump from `0.175.4`)

**Citation currency**: every `git show` evidence statement below cites `e062a3dd8d9499b678ff6f694107dd57a0d7f311` and was re-executed against it while authoring (one observed line per statement, 0 mismatches). Each statement's pattern is written exactly as it is run: the patterns use `.` in place of regex metacharacters, so no statement depends on a backslash escape. Lines that carry inline code spans or a non-ASCII dash are not quoted as `->` evidence; they are cited by line number in prose, or by a `grep -noE` command whose printed output is quoted in full and is ASCII. The other command outputs quoted (`git grep`, `git merge-base`, `git ls-remote`, scratch runs) were observed on 2026-09-28. Scratch runs used a clone of the base outside the repository, with the Phase 1 test file, the Phase 2 code and the Phase 3 edits applied exactly as specified below.

## Open Questions

None. GH #474 left two decisions open; both are decided in LD-2 (what the title and header say) and LD-4 (who owns the threshold).

## Problem

`create_shadow_issue` files a GitHub issue for a set of process shadow events. Its title and body header always say "threshold breach", whatever the filed events add up to. The severity sum they print is the plain sum of the events actually selected, while the threshold printed beside it comes from a marker, and on two paths the selected events are not the set any threshold test ran over:

1. `--events <ids>` runs no threshold test at all. It builds its own marker with the current time and the number 10, so one severity-1 event is filed as "Process threshold breach" with "Severity sum: **1** (threshold 10)" and a "Detected:" time that is simply the time of filing.
2. With a marker, the selection is the marker's events that are still unaddressed. The documented `/qor-process-review-cycle` workflow resolves some events with `--mark-resolved --events <ids>`, which leaves the marker in place, and `--flip-only` also leaves the marker in place (Phase 279). A later default run then files only the remainder, still titled a breach, with a printed sum below the printed threshold.

The number 10 in path 1 is a second copy of `check_shadow_threshold.THRESHOLD`, so the threshold has two owners.

Reproduction at the base (scratch clone, Phase 1 test file applied, base `create_shadow_issue.py`): `python -B -m pytest tests/test_shadow_issue_header.py -q` gives `10 failed, 2 passed`. The two passing items are the regression pin for a real breach and the breach direction of the marker-threshold test (Phase 1).

## Locked Decisions

### LD-1: where the contradiction comes from

`build_body` takes the selected events and a marker, sums the events, and prints the marker's threshold and breach time beside that sum:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE 'def build_body'` -> `174:def build_body(events: list[dict], marker: dict) -> str:`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE 'sev_sum = sum'` -> `176:    sev_sum = sum(e["severity"] for e in events)`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE 'Severity sum: '` -> `180:        f"Severity sum: **{sev_sum}** (threshold {marker['threshold']})",`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE 'Detected: '` -> `182:        f"Detected: {marker['breach_ts']}",`

The body heading on line 178 at the base is fixed text; it carries a non-ASCII dash, so it is cited by command: `git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -noE 'threshold breach",'` prints `178:threshold breach",`.

The title is built in `main` from the selected events, also with fixed breach wording and the same non-ASCII dash: `git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -noE 'title = f".qor-shadow. Process threshold breach'` prints `384:title = f"[qor-shadow] Process threshold breach`. Line 384 at the base goes on to interpolate `len(selected)` and the plain severity sum of `selected`.

The `--events` path synthesises its marker; the default path loads the real one and selects its unaddressed events:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE '"threshold": 10}'` -> `370:        marker = {"breach_ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "threshold": 10}`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE 'marker = load_marker'` -> `372:        marker = load_marker()`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE 'target_ids = set.marker'` -> `373:        target_ids = set(marker["event_ids"])`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE 'selected = .e for e in all_events'` -> `379:    selected = [e for e in all_events if e["id"] in target_ids and not e["addressed"]]`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE 'body = build_body'` -> `385:    body = build_body(selected, marker)`

The two paths that shrink the selection below the marker's set leave the marker in place. `--mark-resolved` prints its count and returns before any marker code:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE 'Marked .flipped. event'` -> `320:        print(f"Marked {flipped} event(s) resolved in {log}")`

`--flip-only` keeps the marker by design (Phase 279):

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE 'this path does NOT remove the marker'` -> `334:        # Phase 279 (GH #472): this path does NOT remove the marker.`

The review-cycle skill documents the `--mark-resolved --events <ids>` workflow on line 86 of `qor/skills/governance/qor-process-review-cycle/SKILL.md` at the base (the line carries inline code spans and is paraphrased). The sealed Phase 279 plan accepted this contradiction as a known cost and filed it as GH #474, on line 135 of `docs/plan-qor-phase279-marker-unlink-condition.md` at the base (inline code spans; paraphrased).

Decision: the fix is in how the title and header are worded from the numbers they print. The selection rule, the marker lifecycle and the `--flip-only` and `--mark-resolved` paths stay as they are.

### LD-2: the title and header say breach only when a loaded marker's threshold is reached by the printed sum (GH #474 decision 1)

A new predicate `is_breach(events, marker)` is true only when `marker` is not `None` and the plain severity sum of `events` is at least `marker["threshold"]`. `build_title` and `build_body` both branch on it:

- Breach (`is_breach` true): the title and the five header lines are exactly the base text. The title is `[qor-shadow] Process threshold breach` followed by the base dash, ` N events, sev S`; the header is the base heading, a blank line, `Severity sum: **S** (threshold T)`, `Event count: N`, `Detected: <breach_ts>`.
- Marker loaded, sum below its threshold: title `[qor-shadow] Process shadow events - N events, sev S`; heading `## Process Shadow Genome - unaddressed events`; `Severity sum: **S** (threshold T; not reached by these events)`; `Event count: N`; `Marker written: <breach_ts>`.
- No marker (`--events`): the same neutral title and heading; `Severity sum: **S** (threshold T; not checked: the events were named with --events)`, with T read from `check_shadow_threshold.THRESHOLD` (LD-4); `Event count: N`; no time line.

Everything after the header (event type distribution, events, next action) is unchanged on all three branches.

Why this option. It is the smallest change that makes the header true of its own numbers: the word breach appears only when a threshold test really ran (a marker exists, and the marker is written only on a breach) and the printed sum really reaches the printed threshold. Keeping the breach title and header byte for byte keeps every existing breach filing, and anything that reads one, unchanged. The alternatives are wider or less honest: recomputing the collapsed sum here would make `create_shadow_issue` a second owner of the breach predicate, which the sealed Phase 279 plan rejected on line 39 of `docs/plan-qor-phase279-marker-unlink-condition.md` at the base (inline code spans; paraphrased); refusing to file below the threshold would change what the command does, not what it says; keeping the word breach with a caveat would still title a sub-threshold filing a breach.

`--events` never gets the breach wording, even when the named events add up to the threshold or more, because no threshold test ran on that path. It also no longer prints a "Detected:" time, since there was no detection. The neutral branch still prints the threshold so the reader can compare.

The marker's threshold, not the current constant, judges a loaded marker, because the marker records the threshold its breach test used:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/check_shadow_threshold.py | grep -nE '"threshold": THRESHOLD,'` -> `258:        "threshold": THRESHOLD,`

Decision: `is_breach`, `build_title` and a header helper implement the three branches above; `main` passes `None` as the marker on the `--events` path and calls `build_title` for the title.

### LD-3: a full marker keeps the breach wording

The writer tests the collapsed sum of all unaddressed events and writes the marker only when that sum reaches the threshold:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/check_shadow_threshold.py | grep -nE 'sum_unaddressed = collapsed_severity.combined.'` -> `89:    sum_unaddressed = collapsed_severity(combined)`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/check_shadow_threshold.py | grep -nE 'if sum_unaddr >= THRESHOLD:'` -> `312:    if sum_unaddr >= THRESHOLD:`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/check_shadow_threshold.py | grep -nE 'write_marker.sum_unaddr, unaddr_ids.'` -> `316:            write_marker(sum_unaddr, unaddr_ids)`

`collapsed_severity` only skips or de-duplicates events, and the shadow event schema gives every severity a minimum of 1:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/gates/schema/shadow_event.schema.json | grep -nE '"minimum": 1,'` -> `61:      "minimum": 1,`

(line 61 sits inside the `severity` property that opens on line 59), so for schema-valid events the plain sum of a set is never below its collapsed sum. When every event the marker names is still unaddressed and present in the events read, the selection is that whole set, its plain sum is at least the collapsed sum the writer tested against the threshold it recorded, and the title and header keep the breach wording. The wording changes only when the selection has shrunk (LD-1 paths) or no marker exists. This is proven for the equality boundary by `test_marker_at_threshold_keeps_the_breach_title_and_header` (plain sum 10, threshold 10).

### LD-4: the threshold has one owner (GH #474 decision 2)

The writer declares the constant:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/check_shadow_threshold.py | grep -nE '^THRESHOLD = '` -> `31:THRESHOLD = 10`

and the `--events` path at the base restates it as the literal on line 370 (LD-1). After the fix, `create_shadow_issue` imports the writer module (`from qor.scripts import check_shadow_threshold as _cst`) and reads `_cst.THRESHOLD` when it builds the `--events` header; the literal and the synthesised marker are removed, so no marker-shaped value claims a breach time or a threshold test that did not happen. The value is read from the module at call time rather than bound by `from ... import THRESHOLD`, so a test can change the writer's constant and observe the header follow it (`test_events_threshold_is_read_from_the_writer`, values 7 and 13), which fails for any restated literal.

The import adds no cycle. The writer imports only these `qor` modules at the base:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/check_shadow_threshold.py | grep -nE '^from qor.scripts import shadow_process'` -> `25:from qor.scripts import shadow_process`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/check_shadow_threshold.py | grep -nE '^from qor import workdir'` -> `27:from qor import workdir as _workdir`

plus `validate_session_id` from `qor.scripts.session` on line 23 and a function-local import of `remediate_mark_addressed` in `_pending_discount_applies`. No module under `qor/` imports `create_shadow_issue`: `git grep -n -e 'import create_shadow_issue' -e 'create_shadow_issue import' e062a3dd8d9499b678ff6f694107dd57a0d7f311 -- 'qor/*.py'` prints nothing. The existing import block of `create_shadow_issue` ends:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE '^from qor.scripts import advisory_filing_control'` -> `85:from qor.scripts import advisory_filing_control as advisory`

Decision: the new import goes directly after line 85; nothing else is imported.

### LD-5: residuals and limits

- The breach wording compares the plain sum the header prints with the marker's threshold. It does not recompute the collapsed sum (LD-2), so after a partial resolution the remainder can keep the breach wording when its plain sum reaches the threshold even if its collapsed sum would not. The header is then consistent with its own numbers, which is the GH #474 defect, but it is not a fresh threshold test.
- The marker's threshold is used as recorded. A marker written under an older constant is judged by the threshold it records.
- Issues already filed keep their titles and bodies; nothing is rewritten.
- A non-breach filing's title changes from the breach wording to `[qor-shadow] Process shadow events - ...`. Nothing in the repository matches on the title text: `git grep -n 'Process threshold breach' e062a3dd8d9499b678ff6f694107dd57a0d7f311 -- qor tests` prints one line, line 384 of `qor/scripts/create_shadow_issue.py` (the title itself). The `qor-shadow` label and the `[qor-shadow] ` title prefix stay on every filing. The only `gh issue list` search under `qor/` is in `ac_close_guard.py` and searches issue bodies for `#<number>`, not titles; the only ones under `.github/` are in `nightly-health.yml` and search for "Nightly governance health", and `git grep -n -i -e 'qor-shadow' -e 'threshold breach' e062a3dd8d9499b678ff6f694107dd57a0d7f311 -- .github` prints nothing. So no deduplication key depends on the changed wording. `collect_shadow_genomes` builds its own title and body and is not changed.
- `create_shadow_issue` still defines its own `MARKER_PATH`, as `check_shadow_threshold` does; that duplicate is outside GH #474 and is not changed (Non-goals).

### LD-6: a marker's threshold is now typed

`load_marker` checks that `threshold` is present but types only `event_ids`, and its docstring explains why: the threshold only interpolated into the body.

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE 'missing = .k for k in'` -> `150:    missing = [k for k in ("event_ids", "threshold", "breach_ts") if k not in data]`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/create_shadow_issue.py | grep -nE 'if not isinstance.data..event_ids.., list.:'` -> `153:    if not isinstance(data["event_ids"], list):`

The docstring's reasoning is on lines 131 to 134 at the base (inline code spans; paraphrased): typing is asymmetric by consequence, `event_ids` can produce a wrong verdict, while `threshold` and `breach_ts` only interpolate. After LD-2 the threshold decides the wording, so a string threshold would raise `TypeError` inside the comparison: an unhandled traceback where this loader's contract is to exit naming the fault. Decision: after the event-id loop, `load_marker` raises `SystemExit` naming `threshold` and "expected an integer" unless the value is an `int` and not a `bool`; the docstring sentence is updated to say `threshold` is now typed for the same reason as `event_ids`, and `breach_ts` still only interpolates. The writer stores `THRESHOLD`, an `int` (LD-4), so every marker it writes passes.

### LD-7: tests, determinism and file sizes

The new tests go in a new file, `tests/test_shadow_issue_header.py`, not in `tests/test_shadow.py`, which is 740 lines at the base. They use only `tmp_path`, `monkeypatch` and `capsys`, fixed event timestamps and a fixed marker `breach_ts`, no network and no live repository state. They drive `main()` through `--dry-run`, which prints the title and body without calling `gh`, and `--log`, which reads only the test's own log. The `--events` tests point `MARKER_PATH` at a missing file under `tmp_path`, so a marker in the real repository cannot affect them. The file was observed green twice in a row with the Phase 2 code (`12 passed`, twice).

`qor/scripts/create_shadow_issue.py` is 410 lines at the base, already over the 250-line Razor cap, and grows to 471 (observed in the scratch clone). Disposition: accepted for this hotfix, whose change belongs in the module that composes the issue; splitting the module is unrelated cleanup (Non-goals). The new test file is 173 lines.

The breach strings keep the base output byte for byte, including the non-ASCII dash; in the new source the dash is written as the Python escape `\u2014` so the module source becomes ASCII-only (observed: 0 non-ASCII bytes in the Phase 2 module and the Phase 1 test file).

### LD-8: no spec delta and no documentation change

The only capability specs are `qor/specs/execution-context-governance` and `qor/specs/spec-corpus`; neither covers shadow issue filing, so there is no spec to carry a delta. No documentation, skill or compiled variant states the title or header text: `git grep -l 'Process threshold breach' e062a3dd8d9499b678ff6f694107dd57a0d7f311 -- .` lists four files: `qor/scripts/create_shadow_issue.py` (the code line in LD-5) and three historical records, `docs/plan-qor-phase279-marker-unlink-condition.md`, `docs/research-brief-advisory-filing-control-2026-09-11.md` and the Phase 279 intent-lock snapshot under `.qor/intent-lock/`, which stay true of the breach wording this plan keeps and are not edited. `qor/skills/governance/qor-shadow-process/SKILL.md` says the script "builds structured issue body", which stays true. `check_variant_drift.py` is therefore unaffected.

### LD-9: version target is 0.175.5

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:pyproject.toml | grep -nE '^version = '` -> `7:version = "0.175.4"`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:CHANGELOG.md | grep -nE '^## .0.175.4. - '` -> `13:## [0.175.4] - 2026-09-28`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:docs/META_LEDGER.md | grep -nE '^### Entry #829'` -> `24453:### Entry #829: SESSION SEAL -- Phase 300 a second remediation proposal no longer destroys the first (v0.175.4)`

`change_class: hotfix` bumps `0.175.4` to `0.175.5` at `/qor-substantiate`.

### LD-10: CHANGELOG Unreleased note

`/qor-implement` writes the user-facing note under `## [Unreleased]`; the seal stamps it and refuses an empty section:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:CHANGELOG.md | grep -nE '^## .Unreleased.'` -> `11:## [Unreleased]`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/references/doctrine-changelog.md | grep -nE 'with bullets describing the user-facing effect'` -> `14:  with bullets describing the user-facing effect of their work. Internal`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/references/doctrine-changelog.md | grep -nE 'refactors, ledger entry numbers, and hash values do NOT appear'` -> `15:  refactors, ledger entry numbers, and hash values do NOT appear in the`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/references/doctrine-changelog.md | grep -nE 'changes means this is not a real release'` -> `32:  changes means this is not a real release; check whether a seal is warranted).`

Line 14 continues line 13, which opens the `/qor-implement` rule for `## [Unreleased]`; lines 14 to 16 exclude internal refactors, ledger entry numbers and hash values from the CHANGELOG. Line 32 continues line 31, the rule that an empty `Unreleased` section raises `ValueError` at the stamp. Line 9 allows `Fixed` as a subsection label. (Lines 9, 13, 16 and 31 carry inline code spans and are paraphrased.)

The note is one `### Fixed` bullet with exactly this text:

```markdown
- **Phase 301 (hotfix; a shadow issue no longer claims a threshold breach its own numbers do not show, GH #474)**: `create_shadow_issue` titled every issue it filed "Process threshold breach" and headed its body "threshold breach", including when the filed events' severity sum was below the threshold: an explicit `--events` selection, which runs no threshold check, and what remains of a breach marker's events after some were resolved with `--mark-resolved` or flipped with `--flip-only`. The title and header now say threshold breach only when a breach marker was loaded and the severity sum the header prints, the plain sum of the filed events, reaches that marker's threshold. Otherwise the title reads "Process shadow events" and the header reports the sum against the threshold as not reached or, for `--events`, as not checked. A filing that meets that rule keeps the title and header it had before. The `--events` path no longer invents a breach time or restates the threshold; it reads the threshold from `check_shadow_threshold`. A breach marker whose `threshold` is not an integer now stops with a message naming it. `docs/release-state.json` records `0.175.4` as `sealed_unpublished`.
```

It is ASCII only and states only what Phase 2 implements. It does not claim the breach wording is a fresh threshold test: it names the number compared (the plain sum the header prints), which is the LD-5 residual. Its only `#` number is the issue reference `GH #474`; it carries no ledger entry number and no hash value; it names no private helper. Clause to proof:

- sub-threshold `--events` and marker-remainder filings are no longer titled or headed as a breach: `test_events_selection_never_claims_a_breach`, `test_marker_subset_below_threshold_is_not_framed_as_breach`;
- breach wording only when a marker was loaded and the printed plain sum reaches that marker's threshold: `test_breach_is_judged_against_the_marker_threshold` (both directions), `test_events_selection_never_claims_a_breach` (the `(5, 5)` case reaches the threshold and is still neutral);
- "not reached" and "not checked" reporting: the exact header lines asserted in those two tests;
- a qualifying filing keeps its title and header: `test_marker_at_threshold_keeps_the_breach_title_and_header`;
- no invented breach time, threshold read from `check_shadow_threshold`: `test_events_selection_never_claims_a_breach` (no `Detected:` line), `test_events_threshold_is_read_from_the_writer`;
- a non-integer marker threshold stops with a message naming it: `test_load_marker_rejects_a_non_integer_threshold`;
- the release-state record: LD-11.

Its last sentence has the form of the sealed Phase 300 bullet under `## [0.175.4]`, which ends by recording `0.175.3` as `sealed_unpublished` in `docs/release-state.json`.

### LD-11: release-state continuity for 0.175.4

Once the seal bumps the project version to `0.175.5`, `0.175.4` stops being the implicit candidate, and the coverage rule treats it as an orphan unless a reachable tag or a disposition covers it:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/release_state.py | grep -nE 'v for v in versions - tags - set.exceptions. - .project_version.'` -> `118:        v for v in versions - tags - set(exceptions) - {project_version}`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/release_state.py | grep -nE 'if _semver.v. <= ceiling'` -> `119:        if _semver(v) <= ceiling`

`0.175.4` has no release tag on the remote. At the base, `grep -n` for the sentence "No remote tag is created; the seal tag stays local." over `docs/META_LEDGER.md` prints lines 24134, 24228, 24381 and 24475; line 24475 is the `**Version**:` line of Entry #829 (the other three are Entries #814, #818 and #825). While authoring, `git ls-remote --tags origin` listed no `v0.173` or later tag; the highest remote tag was `v0.172.2` (observation, 2026-09-28; not a test expectation).

The record at the base ends with `0.175.3` and has no `0.175.4` entry:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:docs/release-state.json | grep -nE '"version": "0.175.(3|4)"'` -> `80:      "version": "0.175.3",`

This phase appends exactly one entry after the `0.175.3` entry, mirroring how Phase 300 recorded `0.175.3`:

- `version`: `0.175.4`
- `state`: `sealed_unpublished`
- `reason`: `Sealed by /qor-substantiate (META_LEDGER #829); no release tag was pushed to the remote, so the version is sealed but not published.`

The immediate precedent:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:docs/release-state.json | grep -nE 'META_LEDGER #825'` -> `82:      "reason": "Sealed by /qor-substantiate (META_LEDGER #825); no release tag was pushed to the remote, so the version is sealed but not published."`

The changelog rule that excludes ledger entry numbers (LD-10) governs `CHANGELOG.md`, not this record; `qor/references/doctrine-changelog.md` lines 78 and 79 give the record's closed shape (each entry exactly `version`, `state`, `reason`), and lines 91 to 93 make every state an operator-asserted disposition whose validator checks the shape and the dated CHANGELOG section (cited in prose; the lines carry inline code spans). `0.175.4` has a dated section (LD-9), which the validator requires:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/release_state.py | grep -nE 'has no dated CHANGELOG section'` -> `84:        raise ReleaseStateError(f"{path}: {version} has no dated CHANGELOG section")`

A local seal tag `v0.175.4` is reachable from the base in a local checkout (`git merge-base --is-ancestor v0.175.4 e062a3dd8d9499b678ff6f694107dd57a0d7f311` exits 0). It is not on the remote, so CI does not see it, and it does not void the disposition:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/references/doctrine-changelog.md | grep -nE 'stays authoritative even if a local seal tag exists'` -> `83:  stays authoritative even if a local seal tag exists. Publishing the version`

Because that local tag covers `0.175.4` locally, the plain local tag-coverage run cannot tell whether the entry is present. The proof therefore uses a CI view that ignores every tag absent from the remote, and runs twice (Phase 3): an in-memory simulation at `/qor-implement`, and a guarded clone proof after the seal commit. The suite consumes the live record:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:tests/test_changelog_tag_coverage.py | grep -nE 'exceptions = release_state.load_release_state.RELEASE_STATE, versions.'` -> `54:    exceptions = release_state.load_release_state(RELEASE_STATE, versions)`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:tests/test_changelog_tag_coverage.py | grep -nE 'def test_every_changelog_section_has_tag'` -> `68:def test_every_changelog_section_has_tag():`

No `release_state` code changes. The rule the entry relies on is already unit-tested:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:tests/test_release_state.py | grep -nE 'def test_disposition_exempts_only_the_named_version'` -> `109:def test_disposition_exempts_only_the_named_version():`

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:tests/test_release_state.py | grep -nE 'def test_sealed_unpublished_version_with_local_tag_is_clean'` -> `115:def test_sealed_unpublished_version_with_local_tag_is_clean():`

The entry is recorded by `/qor-implement` (Phase 3), not written by hand at seal time. No entry is recorded for `0.175.5`: after the seal it is the implicit candidate. No ledger entry, seal, gate artifact or dated CHANGELOG section is edited.

### LD-12: canonical governance shape

This file is the canonical `docs/plan-qor-phase301-*.md` plan on branch `phase/301-shadow-breach-header`, created from the base:

`git show e062a3dd8d9499b678ff6f694107dd57a0d7f311:qor/scripts/governance_helpers.py | grep -nE 'plan-qor-phase.nn'` -> `64:    candidates = sorted(docs_dir.glob(f"plan-qor-phase{nn}*.md"))`

No other `docs/plan-qor-phase301*.md` exists at the base. The branch stays plan-only until `/qor-audit` returns PASS on this revision. No governance evidence is hand-authored.

## Feature Inventory Touches

Empty. This plan changes a governance script and its tests; it introduces no `src/` or user-touchable product feature surface.

`feature_inventory_touches`: `[]`.

## Phase 1: Regression tests

### Affected Files

- `tests/test_shadow_issue_header.py` - new file, six test functions (12 items), written before Phase 2 (LD-7).

### Changes

The file defines local helpers: `_event(severity, gate)` builds an unaddressed `gate_override` event with fixed `ts` `2026-04-15T12:00:00Z`, `details={"gate": gate}` and its id from `shadow_process.compute_id`; `_events(severities)` gives each a distinct gate so no two share a signature; `_write_log` writes them as JSONL to `tmp_path / "shadow.md"`; `_write_marker(tmp_path, monkeypatch, ids, threshold=10)` writes a marker with `breach_ts` `2026-04-15T12:30:00Z` and points `csi.MARKER_PATH` at it; `_dry_run(monkeypatch, capsys, argv)` sets `sys.argv` to `["create_shadow_issue.py", "--dry-run", *argv]`, asserts `csi.main() == 0`, and returns the text after `Title: ` and the body lines (everything after the first blank line of the output). Module constants: `BREACH_TITLE_PREFIX = "[qor-shadow] Process threshold breach \u2014 "`, `BREACH_HEADING = "## Process Shadow Genome \u2014 threshold breach"`, `NEUTRAL_HEADING = "## Process Shadow Genome - unaddressed events"`.

### Unit Tests

- `tests/test_shadow_issue_header.py::test_events_selection_never_claims_a_breach`, parametrized over severities `(1,)` and `(5, 5)`, with `MARKER_PATH` pointing at a missing file - runs `--events <ids> --log <log>`; asserts the title is exactly `[qor-shadow] Process shadow events - N events, sev S`, body line 0 is `NEUTRAL_HEADING`, body line 2 is exactly `Severity sum: **S** (threshold T; not checked: the events were named with --events)` with T `cst.THRESHOLD`, no body line starts with `Detected:`, and `breach` does not occur in the title or body (case-insensitive). RED at the base for both items.
- `tests/test_shadow_issue_header.py::test_marker_subset_below_threshold_is_not_framed_as_breach` - two severity-5 events, a marker naming both with threshold 10, then `csi.mark_resolved(log, {first id})` returns 1 (the documented workflow); a default run; asserts the title is exactly `[qor-shadow] Process shadow events - 1 events, sev 5`, body lines 0, 2, 3 and 4 are `NEUTRAL_HEADING`, `Severity sum: **5** (threshold 10; not reached by these events)`, `Event count: 1` and `Marker written: 2026-04-15T12:30:00Z`, and `breach` does not occur. RED at the base.
- `tests/test_shadow_issue_header.py::test_marker_at_threshold_keeps_the_breach_title_and_header` - two severity-5 events, marker threshold 10, a default run; asserts the title is exactly `BREACH_TITLE_PREFIX + "2 events, sev 10"` and the first five body lines are exactly `BREACH_HEADING`, blank, `Severity sum: **10** (threshold 10)`, `Event count: 2`, `Detected: 2026-04-15T12:30:00Z`. GREEN at the base and after (regression pin for the unchanged breach text and the `>=` boundary).
- `tests/test_shadow_issue_header.py::test_breach_is_judged_against_the_marker_threshold`, parametrized `(threshold 3, severities (4,), breach)` and `(threshold 20, severities (5, 5, 2), no breach)` - a default run; asserts the title starts with `BREACH_TITLE_PREFIX` and body line 0 is `BREACH_HEADING` exactly when the case is a breach. The first item is GREEN at the base; the second is RED at the base (plain sum 12 reaches the constant 10 but not the marker's 20).
- `tests/test_shadow_issue_header.py::test_events_threshold_is_read_from_the_writer`, parametrized over 7 and 13 - `monkeypatch.setattr(cst, "THRESHOLD", value)`, one severity-1 event, `--events`; asserts body line 2 is exactly `Severity sum: **1** (threshold <value>; not checked: the events were named with --events)`. RED at the base for both items.
- `tests/test_shadow_issue_header.py::test_load_marker_rejects_a_non_integer_threshold`, parametrized over `"10"`, `None`, `True` and `10.0` - writes a marker with that threshold; asserts `csi.load_marker()` raises `SystemExit` whose message contains `threshold` and `expected an integer`. RED at the base for all four items.

TDD: observed RED at the base before Phase 2 (`10 failed, 2 passed`). Discrimination is proven after Phase 2 by local, uncommitted mutations of `qor/scripts/create_shadow_issue.py`, each run with `python -B -m pytest tests/test_shadow_issue_header.py tests/test_shadow.py -q` and then reverted:

- M1: replace the body of `is_breach` with `return True` -> both `test_events_selection_never_claims_a_breach` items, `test_marker_subset_below_threshold_is_not_framed_as_breach`, the no-breach item of `test_breach_is_judged_against_the_marker_threshold`, and both `test_events_threshold_is_read_from_the_writer` items FAIL.
- M2: change `>= marker["threshold"]` in `is_breach` to `> marker["threshold"]` -> `test_marker_at_threshold_keeps_the_breach_title_and_header` FAILS.
- M3: on the `--events` path, set `marker = {"breach_ts": "2026-01-01T00:00:00Z", "threshold": _cst.THRESHOLD}` instead of `marker = None` (a synthesised marker again, even with the single-owner constant) -> both `test_events_selection_never_claims_a_breach` items and both `test_events_threshold_is_read_from_the_writer` items FAIL.
- M4: in `is_breach`, compare with `_cst.THRESHOLD` instead of `marker["threshold"]` -> both `test_breach_is_judged_against_the_marker_threshold` items FAIL.
- M5: in the `--events` header, write `{10}` in place of `{_cst.THRESHOLD}` -> both `test_events_threshold_is_read_from_the_writer` items FAIL.
- M6: replace the threshold type condition in `load_marker` with `if False:` -> all four `test_load_marker_rejects_a_non_integer_threshold` items FAIL.
- M7: restore the base title line in `main` (fixed breach wording) while keeping the Phase 2 body -> both `test_events_selection_never_claims_a_breach` items, `test_marker_subset_below_threshold_is_not_framed_as_breach` and the no-breach item of `test_breach_is_judged_against_the_marker_threshold` FAIL.
- M8: drop the `isinstance(threshold, bool) or` part of the type condition -> the `True` item of `test_load_marker_rejects_a_non_integer_threshold` FAILS.

Observed in the scratch clone with the Phase 2 code (60 items in the two files): M1 `6 failed, 54 passed`; M2 `1 failed, 59 passed`; M3 `4 failed, 56 passed`; M4 `2 failed, 58 passed`; M5 `2 failed, 58 passed`; M6 `4 failed, 56 passed`; M7 `4 failed, 56 passed`; M8 `1 failed, 59 passed`. Each failing set is exactly the one named above. After each mutation the implementer restores the Phase 2 content and runs the file twice GREEN.

## Phase 2: Honest header and one threshold owner

### Affected Files

- `qor/scripts/create_shadow_issue.py` - import the writer module; type the marker threshold in `load_marker` and update its docstring sentence (LD-6); add `_severity_sum`, `is_breach`, `build_title` and `_header`; `build_body` takes `marker: dict | None` and builds its header from `_header`; `main` passes `None` on the `--events` path and titles with `build_title` (LD-2, LD-4).

`build_body` has one caller, `main` (line 385 at the base); no test calls it directly, so the widened `marker` type needs no other caller change. No new caller of `load_marker` is added.

### Changes

- After line 85 at the base, add `from qor.scripts import check_shadow_threshold as _cst`.
- In `load_marker`, after the event-id loop and before `return data`:

  ```python
      # Phase 301 (GH #474): the writer stores an int; bool is an int subclass.
      threshold = data["threshold"]
      if isinstance(threshold, bool) or not isinstance(threshold, int):
          raise SystemExit(
              f"Marker at {MARKER_PATH} has threshold as {type(threshold).__name__}, "
              f"expected an integer; {_REGEN}"
          )
  ```

  and replace the docstring's two lines 133 and 134 at the base with four lines saying that since Phase 301 (GH #474) a wrong-typed `threshold` also produces a wrong verdict, because it decides whether the issue header says breach, that both are typed, and that `breach_ts` only interpolates into an issue body and produces a visibly odd line nobody acts on.
- Replace the head of `build_body` (lines 174 to 182 at the base) with:

  ```python
  def _severity_sum(events: list[dict]) -> int:
      return sum(e["severity"] for e in events)


  def is_breach(events: list[dict], marker: dict | None) -> bool:
      """True only when a threshold marker was loaded and the selected events'
      own severity sum reaches that marker's threshold. (Docstring continues
      with the GH #474 cause and that this decides wording only; the marker's
      lifecycle stays with check_shadow_threshold, which owns the predicate.)"""
      if marker is None:
          return False
      return _severity_sum(events) >= marker["threshold"]


  def build_title(events: list[dict], marker: dict | None) -> str:
      sev_sum = _severity_sum(events)
      if is_breach(events, marker):
          return f"[qor-shadow] Process threshold breach \u2014 {len(events)} events, sev {sev_sum}"
      return f"[qor-shadow] Process shadow events - {len(events)} events, sev {sev_sum}"


  def _header(events: list[dict], marker: dict | None) -> list[str]:
      sev_sum = _severity_sum(events)
      count = f"Event count: {len(events)}"
      if is_breach(events, marker):
          return [
              "## Process Shadow Genome \u2014 threshold breach",
              "",
              f"Severity sum: **{sev_sum}** (threshold {marker['threshold']})",
              count,
              f"Detected: {marker['breach_ts']}",
          ]
      heading = "## Process Shadow Genome - unaddressed events"
      if marker is None:
          # No threshold check ran for an --events selection; the threshold is
          # read from its one owner, never restated here.
          return [
              heading,
              "",
              f"Severity sum: **{sev_sum}** (threshold {_cst.THRESHOLD}; "
              "not checked: the events were named with --events)",
              count,
          ]
      return [
          heading,
          "",
          f"Severity sum: **{sev_sum}** (threshold {marker['threshold']}; not reached by these events)",
          count,
          f"Marker written: {marker['breach_ts']}",
      ]


  def build_body(events: list[dict], marker: dict | None) -> str:
      counts = Counter(e["event_type"] for e in events)
      lines = _header(events, marker) + [
          "",
          "### Event type distribution",
          "",
      ]
  ```

  The rest of `build_body` (from the event-type loop on) is unchanged. The `is_breach` docstring is written out in full in the module; the parenthesis above summarizes its last sentences.
- In `main`, replace the synthesised marker on line 370 at the base with `marker = None`, and the title on line 384 with `title = build_title(selected, marker)`. The marker removal guard, `if MARKER_PATH.exists() and not args.events:` (line 402 at the base), is unchanged, so the `--events` path still never removes a marker.

### Unit Tests

- Re-run `tests/test_shadow_issue_header.py` after the edit: 12 items GREEN, twice in a row.
- Run mutations M1-M8 (Phase 1) and observe each named failure; revert.
- The existing consumers stay GREEN unchanged: `python -m pytest tests/test_shadow.py tests/test_e2e.py tests/test_collect.py tests/test_advisory_filing_control.py tests/test_security_fixes.py -q` (observed `113 passed` at the base and in the scratch clone with Phase 2 applied). `test_create_shadow_issue_flips_addressed` in `tests/test_shadow.py` files a full marker at sum 10, threshold 10, through the breach branch.
- Full suite: `python -m pytest tests/ -q` stays GREEN (observed in the scratch clone with Phases 1 to 3 applied: `3627 passed, 3 skipped, 4 deselected`); `python -m ruff check qor/ tests/` prints `All checks passed!`; `python -m qor.scripts.publication_boundary_lint --repo-root .` reports `0 finding(s)`.

## Phase 3: Release-state continuity and CHANGELOG note

### Affected Files

- `docs/release-state.json` - append the `0.175.4` `sealed_unpublished` entry (LD-11).
- `CHANGELOG.md` - the Phase 301 bullet under `## [Unreleased]` (LD-10). No dated section is edited.

### Changes

Append the LD-11 entry as the last element of `exceptions`, with the same key order and indentation as the existing entries. No other entry changes. Add the LD-10 bullet under a `### Fixed` heading in `## [Unreleased]`. `/qor-substantiate` stamps `[0.175.5]` and records the seal; this phase writes no ledger entry, tag or dated section.

### Unit Tests

- None added. The record is data consumed by the existing suite; `tests/test_release_state.py::test_disposition_exempts_only_the_named_version` and `tests/test_release_state.py::test_sealed_unpublished_version_with_local_tag_is_clean` already prove the rule it relies on (LD-11).
- At `/qor-implement`, `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` and `python -m pytest tests/test_changelog_format.py -q` stay GREEN (observed in the scratch clone with both Phase 3 edits applied: `34 passed` for the three files together).
- At `/qor-implement`, the CI-view simulation in `## CI Commands` models the post-seal state (project version `0.175.5`, remote tags only). At the base, before the entry exists, it prints `{'0.175.4'} {'0.175.4'}` (observed while authoring): the gap is RED. After the entry is appended it must print `set() {'0.175.4'}`: no orphan with the entry, exactly `{'0.175.4'}` with the entry removed in memory. That shows the entry is what keeps coverage green (observed in the scratch clone).
- Post-seal verification: the substantiating operator runs the guarded CI-view clone proof in `## CI Commands` after `/qor-substantiate` Step 9.5.5 (seal commit and local `v0.175.5` tag exist) and before Step 9.6 (push/merge). It must exit 0, which requires the guard to pass, pytest to pass, and no test to be skipped. It clones the seal commit, so it proves the committed bump, stamp and entry together. The operator records the observed output in the substantiation hand-off report. A non-zero exit blocks Step 9.6; the legal next action is `/qor-remediate`, and the seal is not pushed. Run earlier, the clone holds a `0.175.4` commit and the guard fails by design.
- Proof that the post-seal verification discriminates (observed while authoring, in a scratch clone of the base outside the repository with `origin` set to the real remote and `TMPDIR` inside the scratch area; the simulated commits never entered this repository):
  - base commit (`version = "0.175.4"`), no entry: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.5 (project version 0.175.4)`;
  - a commit that bumps `version` to `0.175.5` without the `[0.175.5]` CHANGELOG stamp: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.5 (project version 0.175.5)`;
  - simulated seal commit (`version = "0.175.5"`, `## [0.175.5] - ` section, local `v0.175.5` tag), no `0.175.4` entry: exit 1, `1 failed, 3 passed`, with `test_every_changelog_section_has_tag` asserting on orphan `0.175.4`;
  - the same seal commit with the LD-11 entry added: exit 0, `4 passed`, and the same result on a second run.

## Definition of Done

### Deliverable: the shadow issue header is true of its own numbers

- **D1**: `create_shadow_issue` titles and heads an issue as a threshold breach only when a breach marker was loaded and the plain severity sum it prints reaches that marker's threshold; otherwise the title is `[qor-shadow] Process shadow events - N events, sev S` and the header reports the sum against the threshold as not reached (marker) or not checked (`--events`). A qualifying breach filing keeps the base title and header byte for byte. The LD-5 residuals are declared, and the LD-10 bullet states no wider guarantee.
- **D2**: `qor/scripts/create_shadow_issue.py` defines `is_breach(events: list[dict], marker: dict | None) -> bool` and `build_title(events: list[dict], marker: dict | None) -> str`; `build_body(events: list[dict], marker: dict | None) -> str` keeps its name and return type; `main` passes `None` as the `--events` marker; `load_marker` exits naming a non-integer `threshold`.
- **D3**: no documentation, skill, schema, spec or compiled variant changes (LD-8). Phase 301 follows canonical branch and plan resolution and receives current-revision audit and substantiation evidence before promotion. The `## [Unreleased]` bullet carries exactly the LD-10 text at implement time.
- **D4**: the Phase 1 file is `10 failed, 2 passed` at the base and `12 passed` twice after Phase 2. Each mutation M1-M8 turns exactly its named items RED. The consumer tests stay GREEN (`113 passed`).

### Deliverable: the threshold has one owner

- **D1**: `create_shadow_issue` takes the shadow threshold value only from `check_shadow_threshold.THRESHOLD` (on the `--events` path) or from a loaded marker, which that module writes; it no longer restates the value or synthesises a marker. `collect_shadow_genomes` keeps its own configured threshold (Non-goals).
- **D2**: `create_shadow_issue` contains no threshold-value literal and imports `check_shadow_threshold as _cst`, reading `_cst.THRESHOLD` at call time.
- **D3**: no other module changes; the writer is untouched.
- **D4**: `test_events_threshold_is_read_from_the_writer` passes for 7 and 13, RED at the base; mutations M3 and M5 turn it RED.

### Deliverable: release-state continuity for 0.175.4

- **D1**: after the Phase 301 seal bumps the project version to `0.175.5`, `0.175.4` (sealed on `main` at META_LEDGER #829, with no remote tag) stays covered by a truthful `sealed_unpublished` disposition.
- **D2**: `docs/release-state.json` gains exactly one entry, `0.175.4` / `sealed_unpublished` with the LD-11 reason. No other entry and no `release_state` code changes.
- **D3**: the entry is recorded by `/qor-implement`, and the seal changes the version from `0.175.4` to `0.175.5` (hotfix). No tag is pushed and nothing is published.
- **D4**: at `/qor-implement`, the CI-view simulation prints `set() {'0.175.4'}` and `tests/test_release_state.py` stays GREEN. After the seal commit and before push, the guarded post-seal clone proof exits 0 on the seal commit: its guard confirms `[project].version` is `0.175.5` with a dated `[0.175.5]` CHANGELOG section, and `tests/test_changelog_tag_coverage.py::test_every_changelog_section_has_tag` passes in the CI view (remote tags only), with no skip.

## CI Commands

- `python -m pytest tests/test_shadow_issue_header.py -q` - verifies the breach wording rule, the neutral wording, the unchanged breach text, the marker-threshold judgment in both directions, the single threshold owner and the typed marker threshold (12 test items).
- `python -m pytest tests/test_shadow.py tests/test_e2e.py tests/test_collect.py tests/test_advisory_filing_control.py tests/test_security_fixes.py -q` - verifies the existing issue-creation, marker, collector and filing-control consumers are unchanged.
- `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` - verifies the release-state record validates with the new entry and local tag coverage holds.
- `python -m pytest tests/test_changelog_format.py -q` - verifies the `## [Unreleased]` section with the LD-10 bullet keeps the Keep-a-Changelog structure.
- `python -c "import subprocess; from pathlib import Path; from qor.scripts import release_state as rs; import tests.test_changelog_tag_coverage as t; remote = {l.rsplit('/', 1)[1] for l in subprocess.run(['git', 'ls-remote', '--tags', 'origin'], capture_output=True, text=True, check=True).stdout.split() if l.startswith('refs/tags/v') and not l.endswith('^{}')}; tags = {v for v in rs.merged_semver_tags(t.REPO) if 'v' + v in remote}; versions = t._changelog_versions() | {'0.175.5'}; ex = rs.load_release_state(t.RELEASE_STATE, versions); print(rs.coverage_violations(versions, tags, '0.175.5', ex).orphans, rs.coverage_violations(versions, tags, '0.175.5', {k: v for k, v in ex.items() if k != '0.175.4'}).orphans)"` - CI-view simulation of the post-seal state at `/qor-implement` (network: reads remote tag names only); expected output `set() {'0.175.4'}`.
- `(T=$(mktemp -d) && R=$(git ls-remote --tags origin | awk '{print $2}') && git clone -q --no-local . "$T/c" && git -C "$T/c" tag -l 'v*' | while read tg; do printf '%s\n' "$R" | grep -qx "refs/tags/$tg" || git -C "$T/c" tag -d "$tg" >/dev/null; done && cd "$T/c" && python -c "import sys, tomllib; v = tomllib.load(open('pyproject.toml', 'rb'))['project']['version']; c = open('CHANGELOG.md', encoding='utf-8').read(); sys.exit(0 if v == '0.175.5' and '## [0.175.5] - ' in c else 'CI-view guard FAIL: clone is not a sealed 0.175.5 (project version ' + v + ')')" && PYTHONPATH=. python -m pytest tests/test_changelog_tag_coverage.py -q -rs -p no:cacheprovider > "$T/out" 2>&1; rc=$?; cat "$T/out" 2>/dev/null; [ "$rc" -eq 0 ] && ! grep -q skipped "$T/out")` - post-seal verification: after `/qor-substantiate` Step 9.5.5 and before Step 9.6, runs the real tag-coverage suite in the CI view (remote tags only) on a clone of the seal commit. It fails unless the clone is a sealed `0.175.5`, and it fails on any skip.
- `python -m pytest tests/ -q` - verifies repository regression safety.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - verifies the ledger chain.
- `python -m ruff check qor/ tests/` - lints the changed module and the new test file.
- `python -m qor.scripts.publication_boundary_lint --repo-root .` - verifies the publication-boundary surface remains clean.

## CI Coverage Exemptions

- `python -m qor.reliability.seal_entry_check` - seal-time check; runs at `/qor-substantiate`.
- `python -m qor.reliability.ledger_base_currency` - WARN-only ledger freshness; not affected by this plan.
- `python -m qor.reliability.gate_chain_completeness` - sealed-phase gate-chain check; runs at seal.
- `python -m qor.reliability.intent_lock_committed` - sealed-phase intent-lock check; runs at seal.
- `python -m qor.scripts.seal_artifacts` - seal-artifact currency; runs at seal.
- `python -m qor.scripts.gate_provenance` - sealed-phase provenance verify/attest; runs at seal and in CI with a secret.
- `python -m qor.scripts.status_json --self-test` - nightly health self-test; not affected by this plan.
- `tests/test_packaging_install.py` - packaging integration smoke; no packaging surface changes.
- `python -m qor.scripts.dependency_admission_lint` - PR Dependency Review admission steps; no dependency or lockfile changes in this plan.
- `python qor/scripts/check_variant_drift.py` - no skill or compiled variant changes in this plan (LD-8).

## Non-goals

- recomputing the collapsed sum, pending discounts or any other part of the breach predicate in `create_shadow_issue` (LD-2, LD-5);
- changing when `check_shadow_threshold` writes or removes the marker, or when `create_shadow_issue` removes it;
- refusing to file, or changing which events are selected, on any path;
- changing `--flip-only`, `--mark-resolved`, or `collect_shadow_genomes` (its own title, body and configured threshold);
- rewriting issues already filed;
- the second `MARKER_PATH` definition in `create_shadow_issue` (LD-5);
- splitting the over-cap module or `tests/test_shadow.py` (LD-7);
- documentation, skill, schema, spec or compiled-variant edits (LD-8);
- release-state dispositions for any version other than `0.175.4`, changes to `qor/scripts/release_state.py`, remote tag pushes, or publication;
- hand-issuing governance evidence;
- unrelated repository cleanup.
