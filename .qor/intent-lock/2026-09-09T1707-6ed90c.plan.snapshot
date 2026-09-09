# Plan: nightly-health advisory boundary gate

**change_class**: hotfix

**doc_tier**: standard

**iteration**: 3 (scope split after a second VETO; the detection half moves to its own phase)

**boundaries**:
- limitations: The step stops killing the job and the close path stops
  overstating. **A completed scan with findings opens nothing on its own.** Its
  count always reaches the run's step summary, and reaches a GitHub issue only
  when one is already open or is opened for another reason -- in the create
  body, or in the close comment of an issue being resolved. So on a night where
  health and smoke are green, no issue is open, and the count rises, no person
  is told. Making a *new* finding reportable on its own is deferred to a
  follow-on phase for the reason in LD-4. This plan is strictly better than the
  present state, in which nothing after the boundary step runs at all, and it is
  not the whole repair.
  Separately, no test executes GitHub Actions `if:` semantics, and only two
  Phase 2 tests execute anything at all: the conditions, the env wiring, the
  comment wording and the issue-body binding are all pinned by parsing the
  workflow text. That is a real limit of the test layer for a file that is
  configuration rather than code, not a shortcut.
- non_goals: Anonymizing the GitHub surface (GH #431, and the boundary half of
  GH #465) is reserved to a human operator by
  `qor/references/doctrine-publication-boundary.md:82-83`. Editing published
  issue or pull-request bodies is outside this plan. So is GH #465's
  audit-report pairing question and the deferred shadow-threshold remediation
  (GH #439).
- exclusions: No change to `github_surface.py`. Its return values are correct;
  the consumer was wrong. **The self-test step at `nightly-health.yml:41` is
  deliberately excluded** -- it carries the same job-killing shape, and that
  shape is correct there: a checker that fails its own self-test must not be
  trusted to file an issue about itself. Operator decision, this cycle. No new
  dependency, no new pinned action, no new tracked file, no permission change.

## Open Questions

None. Three were decided by the operator: the lifecycle asymmetry, the
self-test exclusion (V5), and the scope split recorded in LD-4.

## Locked Decisions

### LD-1: the consumer is wrong, not the scanner

> `git show HEAD:qor/scripts/github_surface.py | grep -nE 'return (1 if findings|2)'`
> -> `123:        return 2`
> -> `130:    return 1 if findings else 0`

Read failure returns 2 at `:123`; a completed scan returns 1 or 0 at `:130`.
The docstring at `:13` and `qor/references/doctrine-publication-boundary.md:82`
both state the scan reports for a human. Nothing in the scanner changes.

### LD-2: the advisory step is the only step whose documentation forbids it to gate

An earlier iteration claimed this step was the only step in the job that can
fail it. That is false and was vetoed as V5.

> `git show HEAD:.github/workflows/nightly-health.yml | grep -c '^      - '`
> -> `9`

**Nine steps, of which eight can fail the job.** An earlier iteration said five,
derived from a grep matching `^      - (run|uses):` plus two single-line
`run: python -m qor` lines. That pattern is structurally blind to every step
that leads with `- name:` and carries a `run: |` block -- five of the nine. The
count and the prose agreed with each other and both were wrong, which is why the
enumeration below is taken from the step list rather than from a pattern chosen
to match the steps already in mind.

| step | line | can fail the job | should it |
|---|---|---|---|
| checkout | 31 | yes | yes, precondition |
| setup-python | 35 | yes | yes, precondition |
| pip install | 39 | yes | yes, precondition |
| self-test | 41 | yes | yes; an unvalidated checker's verdict is worth nothing |
| **publication boundary** | **51** | **yes** | **no -- its own documentation forbids it to gate** |
| aggregate health | 54 | no (`set +e`) | no |
| packaging smoke | 71 | no (`set +e`) | no |
| create-or-update issue | 79 | yes | incidental: no `set +e`, so a failing `gh ... \| jq` kills it |
| close issue | 97 | yes | incidental: same shape |

The two steps whose verdicts gate already refuse to fail, so the lifecycle after
them can read those verdicts. The step at `:51` is the only one whose own
documentation says it cannot gate, and it gates. That narrower claim is what
this plan rests on. The two lifecycle steps' shape is noted for accuracy and is
not repaired here -- when `gh` is unusable there is no issue to file anyway
(LD-3a), so a red job is the correct channel.

### LD-3: exit code alone cannot classify the scan; the completion line can

`main()` returns 2 only from the `except (RuntimeError, OSError, ValueError)`
wrapping `fetcher(args.repo)`. An unhandled exception -- `KeyError` on
`row["number"]`, anything raised inside `scan_surface` at `:125`, which sits
outside the try entirely -- exits **1**, indistinguishable from findings.
Measured: a script raising `KeyError` exits 1.

The scanner emits its completion line only on a completed scan:

> `git show HEAD:qor/scripts/github_surface.py | grep -n 'finding(s)'`
> -> `129:    print(f"github_surface: {len(findings)} finding(s) ({coverage})")`

Classification therefore keys on that line. Measured across four stubbed modes,
this separates all four where the exit code conflates the crash case with
findings:

| stub mode | scanner exit | classified `boundary_rc` |
|---|---|---|
| clean | 0 | 0 |
| findings | 1 | 1 |
| crash (traceback, no completion line) | 1 | **2** |
| could-not-read | 2 | 2 |

The completion line is matched **anywhere in the output, anchored to line
start**, not only at the last line. A `tail -1` form was drafted first and is
sensitive to output the scanner does not own -- an `Exception ignored in:` at
interpreter shutdown, a late `atexit` warning -- which becomes the last line,
misses the match, and misreports a healthy scan as could-not-scan. Anchoring
removes that sensitivity at no cost. Measured, with the anchored form:

| output | classified |
|---|---|
| completion line only | rc unchanged (0 or 1) |
| findings then completion line | rc unchanged |
| overlay coverage form (`(terms overlay: 3 terms)`) | rc unchanged |
| completion line then trailing `Exception ignored in:` | rc unchanged |
| traceback, no completion line | **2** |

The anchor is what makes this safe against a finding line quoting the
completion text: findings begin `[boundary] `, so only a line the scanner itself
started can match.

### LD-3a: the could-not-scan path cannot always file its own report

Exit 2 arises only when `_gh_json` raises (`github_surface.py:74-84`), so its
dominant causes are token, auth, and rate-limit failures. The create step then
invokes `gh issue create` with the same token in the same job, and in those
causes it fails too: the job goes red and no issue appears.

This is not repaired here and is not hidden. When `gh` itself is unavailable,
the workflow-failure notification is the only channel left, and it is the
correct one -- there is no way to file a GitHub issue reporting that GitHub is
unreachable. The case where the fix matters is the one it does cover: a scan
that completes and finds things, which is every night for the last five.

### LD-4: reporting a new finding is a separate problem and is not solved here

Two designs for making findings reportable were written and both failed review.

Opening an issue on any finding would open one tonight and hold it open until
the operator anonymization pass lands, reproducing the state
`doctrine-publication-boundary.md:92-95` records against this control's
predecessor. Annotating an already-open issue reports nothing on the ordinary
night, because the create step does not run when health and smoke are green.

A delta against a recorded count fails for a reason neither design anticipated:

> `git show HEAD:qor/scripts/github_surface.py | grep -n '"--limit", "200"'`
> -> `93:            "--limit", "200", "--json", "number,title,body,author",`

The scanner fetches a 200-item window per kind over `--state all`. This
repository exceeds the window on both:

> `gh issue list --state all --limit 1000 --json number -q 'length'` -> `229`
> `gh pr list --state all --limit 1000 --json number -q 'length'` -> `250`

An earlier draft cited the highest issue and pull-request *numbers* (477 and
479) as evidence here. Issues and pull requests share one number space, so the
highest number shows neither list's length; the conclusion held and the evidence
did not establish it. Both lists are counted separately above and both exceed
200, so both windows are full
and slide with ordinary activity. The scanned item set therefore changes for
reasons unrelated to the boundary, and any count over it churns. A count is also
not an identity: one finding anonymized and one new violation appearing on the
same day leaves the count unmoved.

The design that survives both is the one `.qor/dialect-ownership-baseline.json`
already implements (Phase 282): baseline the finding **identities** and report
the one-directional difference, so an identity leaving the window never fires
and a new identity always does. An earlier iteration cited that precedent and
then stored a count, taking the shape of the idiom and dropping its substance.

Building it belongs in its own phase with its own research, not bolted to a
repair that is already verified. **This plan therefore leaves findings reported
only to the run's step summary, and says so in its limitations rather than
implying otherwise.**

### LD-5: extraction anchors on the step name, which exists at HEAD

An earlier iteration extracted by step `id` and was vetoed as V1: the step
carries no `id:` until this plan's own Phase 2, so every Phase 1 test would have
failed with step-not-found rather than by observing the defect.

> `git show HEAD:.github/workflows/nightly-health.yml | grep -n 'publication boundary'`
> -> `42:      - name: publication boundary (GitHub surface)`

The name exists now, so Phase 1's tests run against the pre-change body and go
red for the reason claimed. Phase 2 does not change the name.

## Phase 1: pin the advisory contract with an executing test

### Affected Files

- `tests/test_nightly_health_wiring.py` - a helper that extracts a step's shell
  body by step name, and five tests that execute it against a recording stub.

### Changes

The helper locates the step block by `name:` and returns its `run:` body,
raising when the step is absent so a rename fails loudly rather than passing
vacuously.

**It must accept both scalar and block forms.** At HEAD the boundary step's
command is a single-line scalar:

> `git show HEAD:.github/workflows/nightly-health.yml | sed -n '51p'`
> -> `        run: python -m qor.scripts.github_surface --repo "${{ github.repository }}"`

Phase 2 converts it to `run: |`. A helper that recognises only the block form
raises at HEAD, and every Phase 1 test then goes red with helper-raised rather
than by observing the pre-change body propagate exit 1 -- the vacuous red that
V1 was raised about, in a new costume. The helper returns the scalar's text as
a one-line body, so the Phase 1 red is the claimed observation.

For the pre-change scalar the `${{ github.repository }}` expression is left
literal; the tests set `REPO` and assert on the recorded argv, and the argv test
is written to accept the pre-change form failing that assertion, since it is
Phase 2 that introduces `$REPO`.

Each test writes an executable stub named `python` onto `PATH` that records its
argv, emits chosen stdout and stderr, and exits with a chosen code, then runs
the extracted body under `bash -e` -- matching the `bash -e {0}` shell Actions
uses on Linux -- with `GITHUB_OUTPUT` and `GITHUB_STEP_SUMMARY` pointed at temp
files. Assertions are on the body's exit status, the pairs it wrote, and the
argv the stub recorded. The body reads no file and needs no fixture beyond the
stub.

`bash` is present on the Linux runner and on the developer hosts in use; the
tests skip with a stated reason where `shutil.which("bash")` is None.

### Unit Tests

- `test_boundary_step_body_exits_zero_when_the_scan_reports_findings` - stub
  exits 1 and emits the completion line; the body exits 0 and writes
  `boundary_rc=1`. Red before Phase 2: the pre-change body has no `set +e` and
  propagates 1. This is the five-night failure reproduced.
- `test_boundary_step_body_exits_zero_when_the_scanner_cannot_read_the_surface` -
  stub exits 2 with the ERROR line and no completion line; body exits 0,
  `boundary_rc=2`.
- `test_a_scanner_crash_is_classified_as_could_not_scan_not_as_findings` - stub
  prints a traceback and exits 1 with **no** completion line; body exits 0 and
  writes `boundary_rc=2`. This is LD-3's whole content.
- `test_a_clean_scan_is_reported_as_zero` - stub exits 0 with a zero-count
  completion line; body exits 0, `boundary_rc=0`. Its value is not excluding a
  hardcoded constant, which the tests above already do; it excludes a body that
  classifies every invocation as a failure.
- `test_the_step_invokes_the_scanner_module_with_the_repository_argument` - the
  stub records argv; the assertion is that it received `-m`,
  `qor.scripts.github_surface`, `--repo`, and the value of `REPO`. Without it a
  renamed module, wrong module path, or dropped flag passes every test above.

## Phase 2: make the step advisory and stop the close path overstating

### Affected Files

- `.github/workflows/nightly-health.yml` - the boundary step becomes non-fatal
  and classifying; both lifecycle steps gain `if: !cancelled()`; the close
  condition becomes an enumerated allow-list; the close comment names what was
  checked.

### Changes

```yaml
      - name: publication boundary (GitHub surface)
        id: boundary
        # Phase 211: the tracked-surface lint scans `git ls-files`, so issue and
        # pull-request titles, bodies, and comments were never examined -- the
        # surface was cleaned by hand twice, and one issue title survived a
        # body-only anonymization the same day. This runs here rather than in
        # the fail-closed PR job because that job runs on forks with no token.
        # Reports only; a finding is for a human to anonymize. The identity-term
        # overlay is gitignored, so this applies the structural detectors and
        # says so in its summary rather than claiming an unqualified "clean".
        # Phase 283: reports only is now true of the mechanism as well as the
        # prose. Classification keys on the scanner's completion line, not its
        # exit code -- an unhandled exception also exits 1 and would otherwise
        # read as findings (LD-3).
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          REPO: ${{ github.repository }}
        run: |
          set +e
          OUTPUT=$(python -m qor.scripts.github_surface --repo "$REPO" 2>&1)
          RC=$?
          if printf '%s\n' "$OUTPUT" | grep -q '^github_surface: [0-9][0-9]* finding(s) ('; then
            SUMMARY=$(printf '%s\n' "$OUTPUT" | grep '^github_surface: ' | tail -1)
          else
            SUMMARY=$(printf '%s' "$OUTPUT" | tail -1)
            RC=2
          fi
          set -e
          printf '%s\n' "$OUTPUT"
          printf 'boundary_rc=%s\n' "$RC" >> "$GITHUB_OUTPUT"
          printf 'boundary_summary=%s\n' "$SUMMARY" >> "$GITHUB_OUTPUT"
          {
            echo "### Publication boundary (advisory)"
            echo '```'
            printf '%s\n' "$OUTPUT"
            echo '```'
          } >> "$GITHUB_STEP_SUMMARY"
```

Every fallible command sits inside the `set +e` region. `printf` replaces `echo`
for each `$GITHUB_OUTPUT` write, so a value beginning with `-` or containing a
backslash is written literally; `tail -1` keeps the value single-line, which is
what makes the `key=value` form safe.

Both lifecycle steps gain `if: !cancelled() && (...)`. `!cancelled()` rather
than `always()`: `concurrency.cancel-in-progress: true` at `:19-21` means a
superseded run is cancelled, and `always()` would run the lifecycle on it with
every output empty. With `!cancelled()`, a failed `pip install` leaves
`health_failed` empty, which satisfies `!= '0'` and opens an issue -- correct.

Create:

```yaml
        if: "!cancelled() && (steps.health.outputs.health_failed != '0' || steps.smoke.outputs.smoke_failed != '0' || steps.boundary.outputs.boundary_rc == '2')"
```

Close, as an enumerated allow-list rather than a negation:

```yaml
        if: "!cancelled() && steps.health.outputs.health_failed == '0' && steps.smoke.outputs.smoke_failed == '0' && (steps.boundary.outputs.boundary_rc == '0' || steps.boundary.outputs.boundary_rc == '1')"
```

`!= '2'` was V2: a crash, a missing interpreter (127/137) and a skipped step
(empty string) all satisfy it and close the issue. Both conditions above are
fail-safe on an empty output: a skipped boundary step leaves `boundary_rc`
empty, which is neither `'0'` nor `'1'`, so close does not fire, while the
health and smoke outputs are empty too and open one.

The create step's title and opening sentence become conditional on what actually
failed, so a boundary-only failure no longer reports `Nightly self-check failed`
above a green payload (V4). Drafted rather than described, since a rewording
nobody can read is not reviewable:

```bash
          if [[ "$HEALTH_FAILED" == "0" && "$SMOKE_FAILED" == "0" ]]; then
            TITLE="Nightly governance health: boundary scan did not complete"
            OPENING="The publication-boundary scan could not read the GitHub surface as of $STAMP. The governance and packaging checks both passed."
          else
            TITLE="Nightly governance health: drift detected"
            OPENING="Nightly self-check failed as of $STAMP."
          fi
```

Both branches keep the existing `Nightly governance health` prefix, which
`tests/test_nightly_health_wiring.py` requires in both the create and close
search paths. The body then carries, in every case:

```
Publication boundary: <boundary_summary>
```

passed through `env:`, never inline `${{ }}`.

The close comment drops `All nightly checks green.` -- false whenever findings
stand (V12) -- for wording that names what was checked:

```bash
            gh issue close "$EXISTING" --comment "Resolved as of $STAMP. Governance and packaging checks passed; publication boundary: $BOUNDARY_SUMMARY."
```

### Unit Tests

- `test_lifecycle_opens_when_the_surface_could_not_be_scanned` - parses the
  create condition and asserts it tests `boundary_rc` against `'2'`. Red before
  the change. Without it, deleting `|| steps.boundary.outputs.boundary_rc == '2'`
  leaves the whole suite green while removing the only new reporting path this
  plan adds.
- `test_the_create_and_close_boundary_codes_partition_the_scanner_contract` -
  parses the codes the close condition enumerates and the codes the create
  condition's boundary disjunct enumerates, and asserts the two sets are
  disjoint and together cover `{0, 1, 2}`. Red before the change, and it
  subsumes a weaker draft that only checked the close condition matched `'0'`
  and `'1'` with no `!= '2'` form.

  The weaker pair was satisfiable by a workflow that creates on `{2}` and closes
  on `{0}` alone: on a findings night (`health=0`, `smoke=0`, `boundary_rc=1`)
  neither condition fires, and an open issue persists forever with no comment.
  Two tests each checking one side cannot see a gap between them; only an
  assertion about the pair can.
- `test_every_step_output_reference_resolves_to_a_step_that_writes_it` - scans
  the workflow for every `steps.<id>.outputs.<key>` reference, and for each one
  asserts a step declares that `id` and its `run:` body writes that `key` to
  `$GITHUB_OUTPUT`. Red before the change, since `boundary` does not exist yet.
  This is the test that makes the two new conditions mean anything: Actions
  resolves an unknown step or key to the empty string in silence, so dropping
  `id: boundary` or typing `boundary-rc` in one place leaves close permanently
  false, any open health issue permanently open, and every condition-parsing
  test green. Asserting `id: boundary` alone would catch deletion and not the
  typo.
- `test_the_boundary_step_precedes_the_checks_whose_outputs_gate_the_lifecycle` -
  asserts the boundary step appears before the health and smoke steps in the
  workflow. The state `health == '0' && smoke == '0' && boundary_rc == ''`
  satisfies neither lifecycle condition, and is unreachable *only* because a
  skipped boundary step means health and smoke were skipped too. Nothing else
  pins that ordering, so a future reorder would make the dead state reachable
  in silence.
- `test_both_lifecycle_conditions_declare_not_cancelled` - asserts both
  lifecycle conditions carry `!cancelled()` and neither carries `always()`.
  Red before the change; pins the distinction `cancel-in-progress` makes
  load-bearing. Named for what it checks -- condition text -- rather than for
  the runtime property that text is intended to produce, which nothing in this
  suite executes.
- `test_the_repository_reaches_the_scanner_through_env_not_interpolation` -
  asserts the boundary step declares `REPO:` under `env:` and its run body
  contains no `${{` at all. Covers D2's wiring claim (V7).
- `test_the_close_comment_does_not_claim_every_check_is_green` - asserts the
  close comment carries the boundary summary variable and no longer contains
  `All nightly checks green`. Red before the change (V12).
- `test_a_boundary_only_failure_gets_its_own_title` - extracts the create step's
  body and executes it under `bash` twice with the health and smoke variables
  set green and then non-zero, asserting the two branches produce different
  titles and that both retain the `Nightly governance health` prefix the
  existing search paths depend on. Red before the change (V4). Executed rather
  than parsed, because a conditional is behavior.
- `test_the_lifecycle_reads_its_inputs_from_env_not_interpolation` - asserts the
  create step declares `HEALTH_FAILED`, `SMOKE_FAILED` and `BOUNDARY_SUMMARY`
  under `env:`, and that its run body contains no `${{`. The new conditional
  reads step outputs, and reading them inline is the shape
  `tests/test_nightly_health_wiring.py:45` already forbids.
- `test_the_issue_body_carries_the_boundary_summary_from_step_output` - asserts
  the create step's env block binds a variable to
  `steps.boundary.outputs.boundary_summary` and its body references that
  variable rather than interpolating the output inline. Covers D2's second
  claim (V7).
- `test_workflow_runs_self_test_before_status_and_uses_lifecycle_idioms` -
  already present at `tests/test_nightly_health_wiring.py:31`; its assertion at
  `:45` forbids `${{ steps.` inside any run body and must stay green across the
  rewrite. An earlier iteration cited this assertion under a test name that does
  not exist (V6); this is its real name.

## Phase 3: record the consumer contract in the doctrine

### Affected Files

- `tests/test_boundary_scope_disclosure.py` - the agreement test below. Named
  here because a phase that declares a test and no file to hold it leaves
  nothing to review.
- `qor/references/doctrine-publication-boundary.md` - one paragraph under
  Enforcement.

### Changes

The text, drafted here so the claim below is checkable before implementation
(V10):

> A consumer of the scheduled scan reads three exit values and must not treat
> them alike. Exit 0 reports a completed scan with nothing found. Exit 1 reports
> a completed scan with findings awaiting a human, and a consumer suppresses it:
> a finding cannot gate, because the operator who must clear it is not the job.
> Exit 2 reports that the surface could not be read, and a consumer routes it
> into whatever reporting path it owns, because an unchecked surface is not a
> clean one. `continue-on-error` erases that distinction and must not be used.
> Exit 1 also carries an unhandled exception, so a consumer that needs the
> distinction keys on the scanner's completion line rather than on the exit
> code. Suppressing exit 1 leaves open how a consumer surfaces a *newly appeared*
> finding, which the count of an item-windowed scan cannot answer; no consumer in
> this repository solves it yet, and one that needs to must baseline finding
> identities rather than their number.

No sentence takes the form `<term> is <definition>` for any registered glossary
term. `doc_integrity_strict.py:144` compiles `(?:is|means|refers to)` with
`re.IGNORECASE` at `:224` against 135 terms, so this is checked, not assumed.

### Unit Tests

- `test_the_doctrine_contract_and_the_workflow_condition_agree` - parses the
  doctrine paragraph into `{code -> suppress | route}` (exit 1 suppress, exit 2
  route), then asserts against the workflow's **create** condition: every code
  the doctrine says to suppress is absent from it, and every code the doctrine
  says to route is present. Red before the change.

  An earlier draft asserted the suppressed set equals the codes the close
  condition enumerates. That is unsatisfiable by construction -- the doctrine
  suppresses `{1}`, the close condition enumerates `{0, 1}` -- and the only
  mechanical extraction from the prose yields `{0, 1, 2}`, so the assertion
  could pass only via a hardcoded mapping, which is a tautology rather than a
  test. Keying on the create condition instead needs no change to the doctrine:
  suppression is exactly "does not trigger reporting", which is what absence
  from the create condition means, and the doctrine says nothing about closing
  because closing is a consumer's own lifecycle policy and not this doctrine's
  business.

  A yet earlier iteration planned a substring assertion over doctrine prose,
  vetoed as presence-only (V15).

## Feature Inventory Touches

Empty. This plan touches `.github/workflows/`, `tests/`, and
`qor/references/`. It introduces and modifies no user-touchable feature and no
file under a product source tree.

## Definition of Done

### Deliverable: an advisory boundary step that cannot fail the nightly job

- **D1**: The publication-boundary step reports without gating, so every step
  after it runs on a night when the surface is unclean. The job remains failable
  at its four precondition steps, which is intended, and at the two lifecycle
  steps, which is incidental and unrepaired (LD-2).
- **D2**: The boundary step carries `id: boundary`, a `set +e` body that
  classifies on the scanner's completion line, `printf`-based `$GITHUB_OUTPUT`
  writes, and `REPO` passed through `env:`.
- **D3**: Plan gate artifact; audit verdict; seal entry citing this plan by
  content hash.
- **D4**: `test_boundary_step_body_exits_zero_when_the_scan_reports_findings` --
  stub emits the completion line and exits 1; the extracted body exits 0 and
  writes `boundary_rc=1`. This is the five-night failure itself, and it is what
  establishes D1: the unclean-surface night is precisely the case where the step
  must not gate. Observed against the pre-change body: exit 1 propagates and the
  body fails.
  `test_a_scanner_crash_is_classified_as_could_not_scan_not_as_findings` extends
  the same property to the case the exit code alone cannot distinguish.

### Deliverable: a lifecycle that refuses to close blind and stops overstating

- **D1**: A run that could not scan the surface never closes an issue, and opens
  one **when the failure left `gh` usable**. Exit 2 is dominated by `gh` itself
  failing (LD-3a), and the create step calls `gh issue create` with the same
  token; in those causes the create step fails too and the red job is the only
  signal. The half that holds unconditionally is the refusal to close.
- **D2**: The create condition tests `boundary_rc == '2'`; the close condition
  enumerates `'0'` and `'1'`; both lifecycle steps carry `!cancelled()`; the
  close comment carries `boundary_summary` and no longer contains
  `All nightly checks green`.
- **D3**: LD-3 records why the exit code alone cannot classify, and LD-4 records
  what is deliberately not solved here.
- **D4**: D1 has two halves and needs three tests.
  `test_lifecycle_opens_when_the_surface_could_not_be_scanned` establishes that
  a could-not-scan run opens, and
  `test_the_create_and_close_boundary_codes_partition_the_scanner_contract`
  that it cannot close and that no scanner outcome falls between the two
  conditions.
  `test_the_close_comment_does_not_claim_every_check_is_green` establishes the
  second -- the close comment carries `boundary_summary` and no longer asserts
  that every check passed.

### Deliverable: the consumer exit-code contract, written down

- **D1**: A future consumer can read what to do with each exit code before
  wiring it.
- **D2**: The paragraph drafted in Phase 3 lands under Enforcement, and the
  agreement test lands in `tests/test_boundary_scope_disclosure.py`.
- **D3**: Doctrine change appears in the seal entry's surface list.
- **D4**: `test_the_doctrine_contract_and_the_workflow_condition_agree` -- the
  code the doctrine says to route (`2`) appears in the workflow's create
  condition, and the code it says to suppress (`1`) does not.

## CI Commands

- `python -m pytest tests/test_nightly_health_wiring.py -q` — the advisory
  contract, the classification rule, the lifecycle conditions, and the
  script-injection guard.
- `python -m pytest tests/test_boundary_scope_disclosure.py tests/test_publication_boundary_lint.py tests/test_github_surface_boundary.py -q` — the doctrine/workflow agreement test and the unchanged detector behavior.
- `python -m qor.scripts.status_json --self-test` — the checker the nightly job validates before trusting its own verdict.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — the packaging smoke the nightly job runs.
- `python -m qor.scripts.publication_boundary_lint` — this plan and its artifacts introduce no boundary finding.
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` — chain
  integrity across the phase's entries.
- `python -m pytest -q` — full suite; the seal writes badges and header state
  that freshness tests read.
