# Plan: the filing path reports what it is about to publish

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: This adds an **advisory** control to one filing path,
  `create_shadow_issue`. It reports and records; it never refuses, and it has no
  operator escape because there is nothing to escape from. Four other sites
  compose a GitHub body and are untouched: `collect_shadow_genomes`,
  `dep_admit_override_tracker`, the `nightly-health.yml` workflow, and the
  `gh pr create` step of `qor-substantiate/SKILL.md:607`. Nor is anything typed
  into the GitHub web UI. Nor is a product or package name the checkout cannot
  derive and the operator has not declared.
- non_goals: No refusal, no `--acknowledge` flag, no override friction -- those
  belong to a later phase calibrated on what this one measures. No execution
  evidence. No reporting skill. No change to `scan_text`, the detector regexes,
  the terms-overlay format, or `_SELF_REPO`.
- exclusions: No retroactive scan of already-filed issues; `github_surface`
  remains the control for what is already published.

## Open Questions

None.

## Locked Decisions

### LD-1: advisory, because the blocking version cannot be calibrated yet

Research brief #790 measured the path this control guards:

- `create_shadow_issue` has run in production and filed GH #439. Its recorded
  leak rate is **0 of 1**, and that filing was self-destined.
- An advisory scan of the live composed body -- `build_body` over the 74
  unaddressed events, 591 lines, with all 17 of the operator's overlay terms
  active -- reports **0 findings**.
- The seven-of-seven leak rate that justified three prior plan iterations
  measures **hand-filed** reports. The fleet collector has never run. That rate
  belongs to a channel this path is not.

A blocking control needs a refusal rate to size its escape, and no such rate has
been measured on this path. Three prior iterations designed an escape, an
override-friction interaction and a matcher trade-off against a residue that is
entirely hypothetical on the path that runs. This phase measures instead.

Advisory is this repository's idiom rather than a new posture: the `qor-audit`
pre-audit ladder runs fourteen lints wrapped `|| true`, `qor-substantiate` carries
WARN-only steps at 4.6.6, 4.6.7 and 4.6.9, and Phase 283 shipped the
nightly-health boundary step on exactly this split.

**This control is preventive.** It guards a path that has not leaked, before
consumers exercise it. The plan says so rather than inheriting a rate the path
did not earn.

### LD-2: the control belongs at authorship, not at rest

`publication_boundary_lint` scans tracked files; `github_surface` scans the
published surface nightly for a human to anonymize. Neither can reach a report
before it is filed, and filing is the last moment at which the reporter still
knows which details identify them.

### LD-3: identity is anchored on the directory the events came from

The third VETO of the blocking design turned on identity and events resolving to
different repositories. The mechanism:

> `grep -n 'LOCAL_LOG_PATH = ' qor/scripts/shadow_process.py` -> `26:LOCAL_LOG_PATH = _workdir.shadow_log()`
> `grep -n 'def shadow_log' qor/workdir.py` -> `40:def shadow_log() -> Path:`

whose body returns `root() / "docs" / <log name>`.

So the event source is `root()`. A prior plan anchored identity on
`_detect_git_root() or _workdir.root()`; `_detect_git_root` runs
`git rev-parse --show-toplevel` with no `-C` and no `cwd=`, resolving from the
process directory and short-circuiting `$QOR_ROOT` whenever any repository is
present. Terms could then derive from one repository while the body was composed
from another's events, and every term would drop as self-reference.

**The anchor is the log path's own grandparent**, not a root function: for
`<root>/docs/<log>.md` that is `<root>`, and the control takes the log path the
caller actually read. Divergence is then impossible by construction, and a
misconfigured anchor produces a body composed from a repository the operator did
not intend -- which is visible -- rather than a silently disarmed control.

### LD-4: terms are derived, and the overlay is additive

`identity_terms(root, overlay)` returns `origin`'s owner and repository name, the
checkout directory name, and the overlay's terms. The overlay cannot be the sole
source:

> `git check-ignore -v .qor/private/boundary-terms.txt` -> `37:.qor/private/	.qor/private/boundary-terms.txt`

It is gitignored and nothing creates or prompts for it, so in a consuming
repository it will not exist. The overlay path defaults to
`<root>/.qor/private/boundary-terms.txt`, mirroring
`publication_boundary_lint.py:157-158`, so the production path loads one when the
operator has written one.

`origin_pair(root)` returns `owner/name` with any `.git` suffix and scheme
stripped, or `None` when no remote resolves. It is a named function because the
whole destination comparison comes from it, and a retained `.git` suffix would
make it match no destination.

### LD-5: substring matching, and the residue costs nothing here

The guard passes its terms to `scan_text`, which matches by substring
(`:132`), so there is one matcher and no second implementation.

Strict matching was measured and rejected: against a 591-line body built from
the 74 unaddressed events, with an identity injected into the `reason` field
carried by 59 of them, strict misses a branch-name shape
(`phase/12-acme-widgets-fix`) and a case-joined identifier
(`AcmeWidgetsRunner`), both of which machine-written `details` carry.

Substring over-reports on short terms that collide with this repository's
vocabulary -- `qor` at 126 findings on that body, `audit` at 81. **Under an
advisory control that cost is a noisy report, not an outage**, which is why this
phase can take the higher-recall matcher without the escape three prior
iterations argued about.

### LD-6: naming the destination is permitted

> `grep -n 'itself are permitted' qor/references/doctrine-publication-boundary.md` -> `31:References to Qor-logic itself are permitted.`

The control takes `origin` and `destination` as `owner/name` pairs and drops
every **derived** term when the two are equal. The comparison is on the whole
pair, never the name alone -- `publication_boundary_lint.py:21-23` states in the
source that a foreign repository can share a name -- so a fork filing upstream
still reports its own name. Overlay terms are never dropped: they are
operator-declared and may name a party the checkout cannot describe.

When `origin` is `None`, nothing drops.

### LD-7: the record is the deliverable, and it does not go in the genome

An advisory control that warns into a void produces no calibration, and
calibration is this phase's entire purpose.

**The record is not a shadow event.** A draft of this decision appended a
`gate_override` event, which is exactly wrong twice over:

> `grep -n 'if event.get("event_type") != "gate_override"' qor/scripts/shadow_process.py` -> `85:    if event.get("event_type") != "gate_override":`

`_apply_override_friction` returns early for every event type *except*
`gate_override`, so `gate_override` is the one type carrying a raising
escalator. Appending it would let this control refuse a filing at the third
occurrence -- by the same override-friction mechanism this phase's `non_goals`
forbid, reintroduced through the choice of event type. The live log already
carries 40 `gate_override` events, so the cross-session gate axis is long past
`DEFAULT_THRESHOLD = 3`.

Second, that population is what `override_friction.check` reads to detect routine
operator gate bypass. Advisory boundary observations are not gate bypasses, and
writing them there corrupts a signal another control depends on.

**So the record is a JSONL line appended to
`<anchor>/.qor/advisory/filing-observations.jsonl`** -- a new path, declared in
Phase 2's Affected Files and gitignored there, beside the log the events were
read from, by the same anchor rule as LD-3. One line per report that carried
findings: timestamp, destination, finding count, finding classes. No matched
text; that stays in the printed report, which is local operator output.

A clean report appends nothing. A control that recorded on every invocation would
make its own record useless as a rate.

### LD-8: a suppression marker is disclosed, not honoured and not refused

`scan_text` skips any line carrying the allowlist marker:

> `grep -n '_ALLOW_RE.search' qor/scripts/publication_boundary_lint.py` -> `108:        if _ALLOW_RE.search(line):`

That marker records a maintainer's exception in a *tracked* file and carries no
authority over text arriving from a consumer's event log. A blocking design had
to refuse such a line before scanning, and the ordering became load-bearing.

An advisory control has a simpler and honest option: **count the marker-bearing
lines and disclose them**. The report states how many lines were not scanned
because they carried a suppression marker. Nothing is gated, so nothing fails
open, and the operator sees exactly what the scan did not cover. The control
imports `_ALLOW_RE` from `publication_boundary_lint` rather than restating it, so
the two cannot drift.

### LD-9: the control is failure-transparent, structurally

"Advisory" is a claim about failures as well as findings, and a draft of this
plan made it only about findings. Four callees on the control's own path raise:
`origin_pair` shells to git and raises `FileNotFoundError` where git is absent;
the overlay read raises `UnicodeDecodeError` on non-UTF-8 content; a record append
raises `OSError` on a read-only or locked directory; and any schema or parse
failure raises in turn. Each would prevent `gh` from being invoked, which is a
refusal by accident.

**The entire control is wrapped, and any exception yields an empty report and a
filing that proceeds.** The exception is printed and counted in the record as a
`control-error` class, so a control that is silently failing is visible rather
than mistaken for a clean scan.

The wrap catches broadly, `Exception` included, which ordinarily hides defects.
That cost is accepted here and stated: a control whose entire purpose is to
observe without interfering must not become the reason a report cannot be filed,
and the `control-error` class is what keeps the breadth from hiding anything.

This also settles an interaction with the existing suite.
`tests/test_shadow.py:231-236` patches `subprocess.run` with a `fake_run` that
raises `AssertionError` on any call other than `gh auth status` and
`gh issue create`. `origin_pair` shelling to git would hit it. Under the wrap the
`AssertionError` is caught, the report is empty, and the filing proceeds, so that
test passes unchanged -- which is why no change to `tests/test_shadow.py` appears
in Affected Files.

## Phase 1: pin the behaviour

### Affected Files

- `tests/test_advisory_filing_control.py` - NEW.

### Changes

Tests drive `identity_terms`, `origin_pair` and `inspect` directly, with a
`tmp_path` git repository and a `tmp_path` log, so nothing depends on an
operator-local file, this host's remote, or the live genome.

### Unit Tests

- `test_the_anchor_is_the_directory_the_log_was_read_from` - given a log at
  `<tmp>/repo/docs/PROCESS_SHADOW_GENOME.md` and a process working directory
  elsewhere, the derived directory term is `repo`. Red if the anchor is any root
  function: `workdir.root()` returns the working directory when `$QOR_ROOT` is
  unset, so the term would be the working directory's name.
- `test_origin_pair_strips_the_git_suffix` - a remote ending `.git` yields
  `owner/name` with no suffix and no scheme. Red under a naive parse, which
  retains `.git`, matches no destination, and would report every self-run.
- `test_origin_pair_is_none_without_a_remote` - a repo with no `origin` yields
  `None`. Red under an implementation that lets the `git remote get-url` failure
  propagate, and red under one that returns a partial pair such as the bare
  directory name, which would then be compared against a destination and never
  match.
- `test_a_body_naming_the_filing_repository_is_reported` - origin
  `AcmeCorp/widgets`, destination elsewhere, body naming `widgets`: one finding.
  Red before: nothing inspects the body.
- `test_a_body_naming_the_destination_is_not_reported` - origin equal to
  destination, body `See Qor-logic#358 for the prior report.`: no finding. Red if
  derived terms are not dropped, which would report every self-run in this
  repository's own home.
- `test_a_fork_sharing_the_destination_name_is_still_reported` - origin
  `AcmeCorp/Qor-logic`, destination `MythologIQ-Labs-LLC/Qor-logic`, body naming
  `Qor-logic`: one finding. Red under a name-only comparison, which drops the
  term and reports nothing.
- `test_an_overlay_term_is_reported_on_a_self_run` - origin equal to destination
  so every derived term drops, but a body naming an overlay term still reports.
  Red if the drop is applied to the whole term set.
- `test_a_term_is_matched_inside_a_compound_identifier` - term `acme-widgets`
  against `branch phase/12-acme-widgets-fix diverged`: one finding. Red under
  strict matching, whose lookarounds a trailing hyphen defeats.
- `test_marker_bearing_lines_are_counted_and_disclosed` - a body whose line
  carries the allowlist marker *and* an identity term on a **different** line
  reports the second line and states that one line was not scanned. Red if the
  marker count is absent: `scan_text` skips such lines silently, so an operator
  would read a clean scan over unscanned text.
- `test_the_report_files_despite_findings` - with findings present, the filing
  call still reaches the subprocess runner. **This is the advisory property.** Red
  under any implementation that raises, returns early, or short-circuits.
- `test_a_raising_callee_does_not_prevent_the_filing` - parametrised over the
  four failure modes LD-9 names: git absent (`origin_pair`), a non-UTF-8 overlay,
  an unwritable record directory, and a malformed log. Each yields an empty
  report carrying the `control-error` class, and the subprocess runner is still
  reached. Red under any unwrapped implementation; red also under a wrap that
  swallows the error silently instead of classing it.
- `test_the_control_does_not_alter_the_title_or_body` - the exact strings handed
  to the subprocess runner equal the inputs, compared after a run that produced
  findings. Red if the control redacts or rewrites, which the doctrine reserves
  to a human.
- `test_findings_append_one_record_with_the_count_and_destination` - a body with
  three findings appends exactly one JSONL line under the injected anchor,
  carrying count 3 and the destination. Red if nothing is recorded, if one line
  per finding is recorded, or if the count is absent.
- `test_the_record_is_not_a_shadow_event` - after a run with findings, the shadow
  log under the anchor is byte-unchanged. Red if the record is appended as a
  `gate_override` event, which would both trip override friction at the third
  occurrence and corrupt the population `override_friction.check` reads.
- `test_the_record_carries_finding_classes_not_matched_text` - the appended
  event's details name the classes (`identity-term`, `absolute-path`) and contain
  none of the matched strings. Red if the event embeds the text, which would
  publish into the genome exactly what the control exists to notice.
- `test_a_clean_report_records_nothing` - a body with no findings appends no
  event. Red if the control records unconditionally, which would make the rate it
  exists to measure meaningless.
- `test_the_filing_path_invokes_the_control_before_gh` - monkeypatch the control
  to record its keyword arguments and the subprocess runner to record call order;
  drive `create_shadow_issue.create_issue` and assert the control ran first and
  received `destination` equal to the `--repo` value and the log path the events
  were read from. Red before: nothing calls it; red also if the call is wired but
  handed a different log than the one read, which is LD-3's divergence.

## Phase 2: the control, and the path wired to it

### Affected Files

- `qor/scripts/advisory_filing_control.py` - NEW. `AdvisoryReport`,
  `identity_terms`, `origin_pair`, `inspect`, `record`.
- `.gitignore` - add `.qor/advisory/`. The record is operator-local
  observational data, in the same class as `.qor/session/` and
  `.qor/remediate-pending` (`.gitignore:17,19`); tracking it would add churn to
  every commit and it has no value to another reader of the repository. It is
  boundary-safe either way, carrying finding classes and a destination but no
  matched text.
- `qor/scripts/create_shadow_issue.py` - `create_issue` calls `inspect` before
  `gh`, prints the report, and passes the log path it read.

### Changes

```python
@dataclass(frozen=True)
class AdvisoryReport:
    findings: tuple[str, ...]          # human-readable, printed locally
    classes: tuple[str, ...]           # finding classes, recorded
    unscanned_lines: int               # lines skipped for a suppression marker


def identity_terms(root: Path, overlay: Path | None = None) -> list[str]:
    """Origin owner and name, the checkout directory name, and the overlay.

    `overlay` defaults to `<root>/.qor/private/boundary-terms.txt`, mirroring
    `publication_boundary_lint.py:157-158`, so the production path loads one
    when the operator has written one (LD-4).
    """


def origin_pair(root: Path) -> str | None:
    """`owner/name` from `origin`, suffix and scheme stripped, or None."""


def inspect(
    title: str, body: str, *,
    log_path: Path, destination: str, overlay: Path | None = None,
) -> AdvisoryReport:
    """Report what this report would publish. Never raises -- at all.

    The whole body is wrapped; any exception yields an empty report carrying a
    `control-error` class rather than propagating, because a control that
    observes must never be the reason a filing fails (LD-9).

    The identity anchor is `log_path.parent.parent` -- the directory the events
    were read from -- so terms and events cannot come from different
    repositories (LD-3).

    Derived terms are dropped when `origin_pair(anchor) == destination`; overlay
    terms never are (LD-6). Survivors are passed to `scan_text`, which matches by
    substring (LD-5).

    Marker-bearing lines are counted before scanning and reported as
    `unscanned_lines`; they are neither honoured as an exemption nor refused
    (LD-8).
    """
```

`create_issue` calls `inspect`, prints the report when it carries findings,
appends one JSONL line to `<anchor>/.qor/advisory/filing-observations.jsonl` when
it does, and then invokes `gh` unchanged. It does not branch on the report: the
filing proceeds either way, which is what makes this advisory. The append is
inside the wrap, so a failure to record cannot prevent a filing either.

### Unit Tests

The Phase 1 tests go green. No new tests.

## Phase 3: record the advisory posture

### Affected Files

- `qor/references/doctrine-publication-boundary.md` - one paragraph under
  `## Required treatment`.

### Changes

The doctrine's headings are `Rule`, `Required treatment`, `Lessons-learned
exception`, `Standing exceptions and how to record one (Phase 208)`, and `Agent
obligations`. There is no `Enforcement` section; a prior plan specified one and it
does not exist.

> Enforcement also reaches outbound. A report filed from one repository into
> another crosses the boundary at the moment it is transmitted, and that is the
> only moment at which the reporter still knows which details identify them. A
> filing path therefore inspects what it passes to `gh`, derives the reporter's
> identity from the directory the reported events were read from, and records
> what it found. The first form of that control is advisory: it reports and
> records without refusing, because the refusal rate has never been measured on
> the path it guards and an unmeasured control cannot be calibrated. A
> suppression marker in outbound text is disclosed as unscanned rather than
> honoured, because that marker records a maintainer's exception in a tracked
> file and carries no authority over text arriving from elsewhere.

No sentence takes the form of a glossary definition for a registered term;
`doc_integrity_strict.py:144` compiles that pattern with `re.IGNORECASE` against
the registered set.

### Unit Tests

- `test_the_doctrine_states_the_advisory_rule` - the `Required treatment` section
  states the derivation anchor, the advisory posture and the marker disclosure,
  and `inspect`'s own report text names the same three. Red before the change,
  and red if the doctrine and the implementation drift apart.

## Feature Inventory Touches

Empty. This plan touches `qor/scripts/`, `tests/` and `qor/references/`. It
introduces no user-touchable feature under a product source tree.

## Definition of Done

### Deliverable: the filing path reports what it is about to publish

- **D1**: `create_shadow_issue` inspects the composed title and body before
  invoking `gh`, prints any findings, and files regardless.
- **D2**: `qor/scripts/advisory_filing_control.py` exposes `AdvisoryReport`,
  `identity_terms`, `origin_pair` and `inspect`; `create_issue` calls `inspect`
  before the `gh` invocation at `:210`.
- **D3**: Research brief #790 stands behind it; plan gate artifact; audit
  verdict; seal entry citing this plan by content hash.
- **D4**: `test_the_report_files_despite_findings` and
  `test_the_filing_path_invokes_the_control_before_gh` -- with findings present
  the subprocess runner is still reached, and the control ran first. Observed
  before the change: nothing inspects the body.

### Deliverable: identity cannot diverge from the events

- **D1**: The terms the control matches always describe the repository whose
  events composed the body.
- **D2**: `inspect` derives its anchor from `log_path.parent.parent` and takes no
  root function; `create_issue` passes the log it read.
- **D3**: LD-3 records the measured divergence and why the anchor is the log.
- **D4**: `test_the_anchor_is_the_directory_the_log_was_read_from` -- with the
  process working directory elsewhere, the derived term is the log's repository.
  Observed before the change: `workdir.root()` returns the working directory when
  `$QOR_ROOT` is unset.

### Deliverable: the destination may be named, the origin may not

- **D1**: A body naming the repository it is filed into produces no finding; a
  body naming the repository it is filed from, or an operator-declared overlay
  term, produces one.
- **D2**: `inspect` drops derived terms exactly when `origin_pair(anchor)` equals
  `destination`, on the whole pair, and never drops the overlay.
- **D3**: LD-6 records the doctrine's permission at line 31 and the fork case.
- **D4**: `test_a_body_naming_the_destination_is_not_reported`,
  `test_a_fork_sharing_the_destination_name_is_still_reported`, and
  `test_an_overlay_term_is_reported_on_a_self_run`.

### Deliverable: the record is usable as a rate

- **D1**: A report with findings appends exactly one record carrying the count,
  the destination and the finding classes; a clean report appends nothing; and
  the shadow genome is untouched.
- **D2**: `record` appends one JSONL line under
  `<anchor>/.qor/advisory/filing-observations.jsonl`, carrying classes rather
  than matched text, and never a shadow event.
- **D3**: LD-7 records that `gate_override` is the one event type carrying a
  raising escalator and why an advisory observation must not join that
  population.
- **D4**: `test_findings_append_one_record_with_the_count_and_destination`,
  `test_the_record_is_not_a_shadow_event`,
  `test_the_record_carries_finding_classes_not_matched_text`, and
  `test_a_clean_report_records_nothing`.

### Deliverable: the control cannot be the reason a filing fails

- **D1**: No internal failure of the control prevents `gh` from being invoked.
- **D2**: `inspect` wraps its whole body; any exception yields an empty
  `AdvisoryReport` carrying a `control-error` class.
- **D3**: LD-9 names the four raising callees and states the accepted cost of a
  broad catch.
- **D4**: `test_a_raising_callee_does_not_prevent_the_filing` -- parametrised over
  git absent, a non-UTF-8 overlay, an unwritable record directory and a malformed
  log; each reaches the subprocess runner. Observed before the change: each
  propagates and the filing never happens.

### Deliverable: the scan discloses what it did not cover

- **D1**: Lines carrying a suppression marker are counted and reported as
  unscanned rather than silently skipped.
- **D2**: `AdvisoryReport.unscanned_lines` carries the count; the control imports
  `_ALLOW_RE` from `publication_boundary_lint` rather than restating it.
- **D3**: LD-8 records why an outbound control cannot honour that marker and why
  disclosure replaces the blocking design's refusal.
- **D4**: `test_marker_bearing_lines_are_counted_and_disclosed` -- a marker on one
  line and an identity term on another reports the term and states one unscanned
  line. Observed before the change: `scan_text` skips the marked line silently.

## CI Commands

- `python -m pytest tests/test_advisory_filing_control.py -q` — the advisory contract, the anchor, the destination comparison, the record, and the marker disclosure.
- `python -m pytest tests/test_shadow.py tests/test_publication_boundary_lint.py tests/test_boundary_scope_disclosure.py -q` — the filing path and the detectors this must not disturb.
- `python -m qor.scripts.publication_boundary_lint` — this plan and its artifacts introduce no boundary finding.
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` — chain integrity across the phase's entries.
- `python -m pytest -q` — full suite; the seal writes badges and header state that freshness tests read.
