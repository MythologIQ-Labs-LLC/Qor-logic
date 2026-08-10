# Plan: publication-boundary scan of the GitHub surface (Phase 211)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: none

**boundaries**:
- limitations: The scan reads this repository's own issues and pull requests.
  It is single-repository and read-only; it never edits, closes, or comments.
  Identity terms come from the same gitignored operator overlay as the tracked
  surface, so an unattended run applies only the structural detectors.
- non_goals: No auto-remediation. A finding is reported for a human to
  anonymize, because rewriting someone's issue text unattended is not a
  decision a lint should make. No change to the four structural detectors, the
  exemption marker, or the tracked-surface scan. No org-scope or multi-repo
  scanning, which belongs to the enterprise line.
- exclusions: Review comments on pull-request diffs, discussions, releases, and
  wiki content are out of scope for this pass; issue and PR titles, bodies, and
  issue comments are the surfaces where the observed leaks occurred.

## Open Questions

None.

## Locked Decisions

**LD-1 — The control has never examined the GitHub surface.**

`git show HEAD:qor/scripts/publication_boundary_lint.py | grep -nE "ls-files|def scan_text" -> 43:        result = subprocess.run(["git", "-C", str(repo_root), "ls-files"], | 62: def scan_text(rel: str, text: str, terms: list[str]) -> list[str]:`

The scan enumerates tracked files. Issue and pull-request titles, bodies, and
comments are not files, so they were never in scope. A manual sweep against the
operator terms file found identity leaks across six issues and three pull
requests, including one issue whose body was anonymized earlier the same day
while its title was missed. The tracked surface has been fail-closed and green
since the previous phase; the GitHub surface was cleaned by hand twice and has
nothing holding it.

**LD-2 — Fetching must be separable from scanning, or the tests need a network.**

`scan_text` is already pure over `(rel, text, terms)`. The GitHub scan keeps
that shape: a pure function over a list of already-fetched surface items, plus a
thin fetcher that is the only part touching `gh`. Every behavioral test drives
the pure function with fixture items, and the CLI wiring is tested with an
injected fetcher. No test performs network I/O, in keeping with
`doctrine-test-discipline.md`.

**LD-3 — This cannot join the fail-closed CI job.**

The tracked-surface step runs in `gate-chain-completeness` on every pull
request, including from forks, with no token and no network expectation. A scan
requiring authentication would fail there for reasons unrelated to the boundary.
The scheduled workflow is the correct host and already has what this needs:

`git show HEAD:.github/workflows/nightly-health.yml | grep -nE "cron|GH_TOKEN|issues: write" -> 16:    - cron: '0 9 * * *' | 25:  issues: write | 70:          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}`

**LD-4 — An unattended run cannot see identity terms, and must say so.**

The terms overlay is gitignored by design: a tracked denylist of private
identifiers in a public repository would violate the boundary it enforces. A
scheduled run therefore applies structural detectors only. Reporting "clean"
without qualification would overstate what was checked, so the summary line
names which detector classes ran.

## Phase 1: Scan an already-fetched surface

### Unit Tests

- `tests/test_github_surface_boundary.py::test_scans_title_and_body_and_comments` -
  passes items whose leak is in the title only, the body only, and a comment
  only; asserts one finding each, and that the reported reference names the
  item kind, number, and field so an operator can navigate to it.
- `::test_reports_clean_for_a_surface_with_no_findings` - asserts the empty
  list for items carrying only neutral prose and an own-repository URL.
- `::test_honors_the_exemption_marker_per_line` - an item body where one line
  carries `boundary-lint: ok=<reason>` and another does not; asserts only the
  unmarked line is reported, so the marker means the same thing on both
  surfaces.
- `::test_applies_identity_terms_when_supplied` - the same item scanned with
  and without a terms list; asserts the term finding appears only when terms
  are supplied, while structural findings appear in both.

### Affected Files

- `qor/scripts/github_surface.py` - NEW. A `SurfaceItem` value (kind, number,
  field, text) and `scan_surface(items, terms) -> list[str]`, delegating each
  item's text to `publication_boundary_lint.scan_text` so both surfaces share
  one detector set and one exemption idiom.
- `tests/test_github_surface_boundary.py` - the tests above.

## Phase 2: Fetch, and wire the CLI

### Unit Tests

- `::test_cli_reports_findings_from_an_injected_fetcher` - runs the CLI entry
  with a fetcher returning fixture items containing one leak; asserts exit 1
  and that the finding is printed. No network.
- `::test_cli_exit_zero_when_surface_is_clean` - same with clean items; asserts
  exit 0.
- `::test_cli_reports_which_detector_classes_ran` - asserts the summary names
  structural-only when no terms are supplied, and names the term count when
  they are, so a clean report cannot overstate its coverage.
- `::test_fetch_failure_is_reported_not_swallowed` - an injected fetcher that
  raises; asserts the CLI exits non-zero and the message names the failure,
  rather than reporting a clean surface it never read.

### Affected Files

- `qor/scripts/github_surface.py` - `fetch_surface(repo)` invoking `gh` in
  list-form argv, and a `main` accepting `--repo`, `--terms-file`, and an
  injectable fetcher for tests.

### Changes

A fetch that fails is a hard error, never a clean result. This is the same
distinction the earlier release failure got wrong: an absent input reported as
a generic success or a misleading cause is worse than an explicit failure.

## Phase 3: Run it on a schedule

### Affected Files

- `.github/workflows/nightly-health.yml` - a `publication boundary (GitHub
  surface)` step running the scan with the workflow's existing `GH_TOKEN`.
- `docs/plan-qor-phase89-ci-commands-reconciliation.md` - the new command is
  registered in the CI-surface list.
- `qor/references/doctrine-publication-boundary.md` - documents that the
  GitHub surface is scanned on a schedule, what an unattended run can and
  cannot see, and that findings are reported for human anonymization.

### Changes

The step reports; it does not gate a merge and does not edit anything. A
scheduled finding is an operator action, consistent with the non-goal above.

## Definition of Done

### Deliverable: the GitHub surface is scanned

- **D1**: An identity reference introduced into an issue or pull-request title,
  body, or comment is detected rather than persisting until someone sweeps by
  hand.
- **D2**: `qor/scripts/github_surface.py` exports `SurfaceItem`,
  `scan_surface`, `fetch_surface`, and `main`; scanning delegates to
  `publication_boundary_lint.scan_text`.
- **D3**: Seal entry records that the control never covered this surface, that
  the leaks were found and cleaned by hand twice, and that one title survived a
  body-only anonymization the same day.
- **D4**: The Phase 1 tests assert returned findings for title-, body-, and
  comment-only leaks and assert the empty list for a clean surface.

### Deliverable: no network in tests, no silence on failure

- **D1**: The suite never performs network I/O, and a scan that could not read
  the surface never reports it clean.
- **D2**: Fetching is injectable; `main` accepts a fetcher.
- **D3**: Seal entry records the pure-scan/thin-fetch split and why.
- **D4**: `test_fetch_failure_is_reported_not_swallowed` asserts a non-zero
  exit and a message naming the failure; every other test supplies items
  directly.

### Deliverable: honest coverage reporting

- **D1**: A clean report states which detector classes actually ran.
- **D2**: The summary line distinguishes structural-only from
  structural-plus-terms.
- **D3**: Seal entry records that an unattended run cannot see identity terms
  because the overlay is gitignored by design.
- **D4**: `test_cli_reports_which_detector_classes_ran` asserts both summary
  forms.

## Feature Inventory Touches

None. This plan touches `qor/scripts/`, `qor/references/`, `.github/workflows/`,
`docs/`, and `tests/`; it introduces no user-touchable feature and modifies no
FEATURE_INDEX row.

## CI Commands

- `python -m pytest tests/test_github_surface_boundary.py -q` — the scan, the CLI wiring, and the failure contract.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `python -m qor.scripts.github_surface --repo MythologIQ-Labs-LLC/Qor-logic` — nightly-health.yml step: the GitHub surface carries no identity reference.
- `qor-logic scripts publication_boundary_lint --repo-root .` — the tracked surface stays clean.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase211-github-surface-boundary-scan.md` — this plan asserts each path and command identically at every site.
