# Plan: a report that names its origin cannot be filed

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: This guards one filing path, `create_shadow_issue`. Four other
  sites compose a GitHub body and are named with their reasons in LD-1:
  `collect_shadow_genomes` and `dep_admit_override_tracker` in Python, the
  `nightly-health.yml` workflow, and the `gh pr create` step of
  `qor-substantiate/SKILL.md:607`. None is guarded here. Nor is anything typed
  into the GitHub web UI, and nor is a product or package name a checkout cannot
  derive (LD-3). That is the residue, enumerated rather than characterised,
  because two earlier iterations of this plan wrote "that is the residue" over a
  list missing one of its own entries.
- non_goals: No execution evidence. No reporting skill. No change to `scan_text`,
  the detector regexes, the terms-overlay format, or `_SELF_REPO`: every change
  here is caller-side, which keeps a verifier shared with the nightly CI gate out
  of this phase's blast radius.
- exclusions: No retroactive scan of already-filed issues; `github_surface`
  remains the control for what is already published. No change to what
  `create_shadow_issue` reports, only to whether it may file.

## Open Questions

None.

## Locked Decisions

### LD-1: four sites compose a body, one is in scope

The three Python argv sites:

> `grep -n '"gh", "issue", "create",' qor/scripts/create_shadow_issue.py` -> `210:            "gh", "issue", "create",`
> `grep -n '"gh", "issue", "create",' qor/scripts/collect_shadow_genomes.py` -> `159:        ["gh", "issue", "create",`
> `grep -n '"gh", "issue", "create",' qor/scripts/dep_admit_override_tracker.py` -> `118:            "gh", "issue", "create",`

The fourth is shell, not argv:

> `grep -n 'gh issue create' .github/workflows/nightly-health.yml` -> `133:            gh issue create --title "$TITLE" --body "$BODY" --label "bug" --label "governance"`

**`create_shadow_issue` is in scope.** It names its destination in the code --
`--repo` at `:211`, defaulted at `:275` -- so an origin-versus-destination
comparison is possible for it, and it is the path this repository and its
consumers actually use.

**`collect_shadow_genomes` is deferred to Phase 287**, not excluded on principle.
It pools events across N repositories and writes each one's configured name into
a section heading, so guarding it correctly requires per-origin term provenance
and a neutral source-label convention. A prior iteration of this plan carried
that machinery and it produced three of the thirteen findings that vetoed it.
The module is inert today -- `~/.qor/repos.json` does not exist on this host --
so deferring it regresses nothing. That inertness is contingent rather than
structural: `load_config` also honours `$QOR_CONFIG` or an explicit path
(`collect_shadow_genomes.py:46-49`), so an operator who sets either has an
unguarded fleet collector until Phase 287 lands.

**`dep_admit_override_tracker` is excluded** because its destination is not
determinable from the code: `:116-124` passes `--title`, `--body` and `--label`
and no `--repo`, so `gh` resolves the target from `GH_REPO` or a prior
`gh repo set-default`. A guard cannot compare an origin against a destination it
cannot name. Bringing it in scope means first making it pass `--repo`.

**`nightly-health.yml` is excluded** because it is a workflow step rather than an
importable call path, and Phase 283 already routes its boundary summary through
`github_surface`.

**`qor-substantiate/SKILL.md:607`'s `gh pr create` is excluded** because a pull
request opens against the repository it was branched from, so it is
self-destined and crosses nothing. It is named because the completeness claim in
`boundaries.limitations` is only worth making if it is complete.

### LD-2: the control belongs at authorship, not at rest

`publication_boundary_lint` scans tracked files; `github_surface` scans the
published GitHub surface nightly for a human to anonymize. Neither can reach a
report before it is filed.

Seven of seven upstream reports from a consuming repository in this tracker named
that consumer in prose until they were anonymized by hand on 2026-09-11. That is
the failure rate of a careful human filing one report at a time.

Filing is the last moment at which the reporter still knows which details
identify them, and the only moment at which anonymizing is cheap.

### LD-3: identity terms are derived from the checkout

The identity-term overlay cannot be the source:

> `git check-ignore -v .qor/private/boundary-terms.txt` -> `37:.qor/private/	.qor/private/boundary-terms.txt`

It is gitignored, and nothing in the repository creates, templates or prompts for
it -- `publication_boundary_lint.py:157-158` names it only as a fallback inside
`collect_findings`, and the argparse default is `None`. In
a consuming repository it will not exist, so a guard that required it would
refuse every report from exactly the repositories that file them.

The terms are already on disk and need no operator action: `origin`'s owner and
repository name, plus the checkout directory name. `identity_terms(root, overlay)`
derives those and unions the overlay.

**`root` must be the git toplevel, not the process working directory.**
`workdir.root()` returns `$QOR_ROOT` or `Path.cwd().resolve()`:

> `grep -n 'Project root' qor/workdir.py` -> `28:    """Project root: $QOR_ROOT > cwd."""`

With `QOR_ROOT` unset -- the default everywhere -- an operator running the filing
command from a subdirectory of the checkout would derive that subdirectory's name
(`docs`, say) rather than the repository's, so LD-3's "a checkout always states an
identity" would state the wrong one.
`workdir._detect_git_root()` (`:14`) returns the toplevel and `root()` does not
call it, so the call site uses `_detect_git_root() or _workdir.root()`. An earlier
iteration of this plan specified `_workdir.root()` while asserting the opposite in
this decision.

**The overlay is loaded by default, not left to the caller.**
`publication_boundary_lint.py:157-158` defaults it to
`repo_root / ".qor" / "private" / "boundary-terms.txt"` when none is passed;
`identity_terms` does the same. Without that default the production path would
supply no overlay at all, and the two tests that exercise overlay terms would
stand over a branch no call reaches.

**Residue, because derivation cannot cover the doctrine.** The doctrine prohibits
more than a checkout can state about itself:

> `grep -n 'repository, organization, owner' qor/references/doctrine-publication-boundary.md` -> `22:- repository, organization, owner, product, and package names;`

Derivation yields owner, repository name and directory name. A **product or
package name** belonging to the origin -- a name that appears in no remote and no
path -- is caught only if the operator has declared it in the overlay. In a
consuming repository with no overlay, a body reading `Widgetron release gate
failed` names its origin and files. That is inside this phase's claimed property
and it is not closed; the deliverable enumerates what is caught rather than
claiming the doctrine's full list, and closing it needs a declared-terms
convention that belongs with the reporting skill.

There is no "unconfigured, refuse" state. `root.name` is non-empty for every real
path, so a checkout always states an identity; measured, only a filesystem root
derives nothing. An earlier iteration carried a refusal for that state and it was
reachable by no repository anybody files from.

### LD-4: the structural detectors are additive and direction-dependent

`scan_text` consults `_SELF_REPO` at `:113` and `_SELF_REPO_NAME`/`_SELF_OWNER`
at `:126-129`, so every structural finding depends on which repository the
constant names. The derived terms do not: they name the reporter's own checkout.
So the derived terms are the primary net and the detectors are additive.

Two measured limits, stated rather than implied. Against the composed body
described in LD-5:

| shape | structural detectors alone |
|---|---|
| bare prose naming a repository | **0 findings** |
| a drive-letter path naming a repository | 1 finding |

`_ABS_PATH_RE` catches path-shaped identity; nothing catches bare prose, which
LD-2 records as the shape of all seven historical leaks. `_CROSS_ISSUE_RE` also
requires a leading capital, so a lowercase cross-repository shape is missed.
Neither gap is fixed here; both are closed by the derived terms.

### LD-5: one corpus, one matcher, and the residue is stated

**Every figure in this plan is measured against one corpus**: `build_body` over
the 74 unaddressed events in the live log, producing a 591-line body. An earlier
iteration measured two tables on two different corpora -- 40 events and 74 -- and
labelled both "the real body", which made them incomparable and understated the
matcher it shipped.

Recall, with a consumer identity injected into the `reason` field carried by 59
of those 74 events:

| identity shape in `details` | substring | strict |
|---|---|---|
| `acme-widgets cycle seal failed` | caught | caught |
| `branch phase/12-acme-widgets-fix diverged` | caught | **missed** |
| `module acme_widgets.scripts.seal raised` | caught | caught |
| `AcmeWidgetsRunner timed out` | caught | **missed** |
| a drive-letter path naming the checkout | caught | caught |

A branch name and a case-joined identifier are what machine-written `details`
carry, and strict matching loses both. Full-corpus recall under substring on the
worst of those shapes is 59 of 59 tagged events.

False positives on the same 591-line body:

| term | substring | strict |
|---|---|---|
| `qor` | **126** | 7 |
| `capability` | 89 | 58 |
| `audit` | 81 | 12 |
| `phase` | 54 | 24 |
| `acme-widgets`, `alpha-service` | **0** | 0 |

No length threshold separates these: at five characters fourteen vocabulary terms
still take substring, and only at thirteen do they clear -- while `acme-widgets`
is twelve, so the only threshold that works sends every realistic consumer name
to strict and loses the two shapes above. A vocabulary-derived selector was also
measured and misses `phase`, `session`, `ledger` and `gates`, which live in event
`details` rather than in the enumerated skill and event-type fields.

**So: plain substring, one regime.** A false pass publishes an identity
permanently; a false refusal blocks a filing and is recoverable through LD-7.
Substring never fails open and needs no fitted constant.

**The residue is over-refusal, and it is large.** A consumer whose checkout name
collides with this repository's vocabulary over-refuses: `qor` at 126 findings,
`audit` at 81. The overlay is **not** a remedy -- LD-3 unions it on top, so adding
terms can only add refusals. The remedy is LD-7's escape, and without it this
matcher would be unshippable.

Because the guard's matcher and `scan_text:132` are now the same operation, the
guard passes its terms to `scan_text` rather than reimplementing the loop. One
matcher, one dialect, no second implementation, and `scan_text` unmodified.

### LD-6: naming the destination is permitted; naming a third party is not this phase's claim

The doctrine permits self-reference:

> `grep -n 'itself are permitted' qor/references/doctrine-publication-boundary.md` -> `31:References to Qor-logic itself are permitted.`

`scan_text:126-129` already honours that for the cross-issue detector. Derived
terms would reinstate the finding that exemption removed, on every self-run: run
here, `See Qor-logic#358 for the prior report.` would refuse, unanswerably,
because the body is machine-generated.

**So the guard takes `origin` and `destination` as `owner/name` pairs and drops
every derived term when the two are equal.** The comparison is on the whole pair,
never on the name alone: `publication_boundary_lint.py:21-23` states in the source
that "the name alone is not sufficient, because a FOREIGN repository can share
it," and a fork at `AcmeCorp/Qor-logic` filing to `MythologIQ-Labs-LLC/Qor-logic`
must still refuse its own name. The overlay is never dropped: it is
operator-declared and may name a third party the checkout cannot describe.

When `origin` is `None` -- a checkout with no remote -- nothing drops. That is
fail-closed, and it is chosen over comparing the directory name against the
destination's name, which is the name-only predicate this decision rejects and
which cannot distinguish a remote-less clone of the destination from a
remote-less fork.

**What this phase does not claim.** On the path where origin equals destination,
every derived term drops and a consuming repository has no overlay, so the term
set is empty and only the structural detectors run -- which LD-4 measures at zero
findings against bare prose. A report filed into its own tracker that names a
*third party* in prose therefore files. That is outside this phase's property,
which is that a report may not name its **origin**, and it is stated here because
an earlier iteration's Definition of Done claimed the broader property and could
not deliver it.

### LD-7: a fail-closed gate needs a logged escape, and this repository has one

LD-5's residue has no remedy without an escape. The body is machine-composed, so
there is no edit surface; the overlay only adds refusals; renaming a checkout
breaks remotes, CI paths and tooling. A consumer named `audit` would simply be
unable to file.

This repository already has the shape. `merge_velocity_check` is a fail-closed
seal gate whose `--override` prints its finding, emits a `gate_override` shadow
event and passes:

> `grep -n 'event_type' qor/scripts/merge_velocity_check.py` -> `255:            "event_type": "gate_override",`

The filing guard takes the same shape, and unlike an earlier iteration it is
specified where it is implemented -- see Phase 2, which carries the flag, the
signature and the event.

**The escape takes an operator-written reason, not a bare flag, because a bare
flag would expire.** `shadow_process.append_event` applies override friction to
every `gate_override` event and exempts only one carrying a justification:

> `grep -n 'DEFAULT_THRESHOLD = ' qor/scripts/override_friction.py` -> `22:DEFAULT_THRESHOLD = 3`

An unjustified override raises `OverrideFrictionRequired` once the per-session or
cross-session count reaches three, and the cross-session axis never resets. A
consumer whose checkout name collides -- the one LD-5 says this escape exists for
-- files twice and is then blocked permanently, by an exception neither the guard
nor `UpstreamReportRefused` names. So `--acknowledge-boundary-findings` takes a
reason of at least `override_friction.MIN_JUSTIFICATION_LEN` (50) characters,
which the guard attaches via `override_friction.record_with_justification` before
appending. That is the same friction the rest of this repository applies to
overrides, honoured rather than sidestepped.

The event is appended with an explicit `log_path`, because `append_event`
requires `attribution=` or `log_path=` and has no default for either. The guard
takes `log_path` so a test can inject a `tmp_path` destination and never write to
the live genome.

**The escape applies to scan findings only, never to the marker refusal of LD-8.**
That refusal fires before `scan_text` runs, so when it fires nothing has been
scanned; overriding it would file text no detector examined. The two are
different conditions and only one is overridable.

The escape is an out-of-band operator flag, which is why it does not contradict
LD-8: that decision forbids the *scanned text* from silencing the scanner, and an
argv flag is not part of the scanned text.

### LD-8: an outbound control must not honour a marker its input can write

`scan_text` skips any line carrying the allowlist marker:

> `grep -n '_ALLOW_RE.search' qor/scripts/publication_boundary_lint.py` -> `108:        if _ALLOW_RE.search(line):`

That marker lets a maintainer record an exception in a *tracked* file. Outbound,
the text is pooled shadow-event `details` not authored by this repository, so the
report being scanned could silence the scanner. Measured, the hole is latent --
0 of 158 live events carry the marker -- but the input class is the one that would
produce it.

**The guard refuses any report carrying the marker**, before `scan_text` runs.
Caller-side, so the detectors are untouched. It **imports `_ALLOW_RE` from
`publication_boundary_lint`** rather than restating the pattern: a second copy is
the duplicate implementation LD-5 forswears, and drift between the two would
silently reopen the hole this decision closes. Importing a private name across
modules in the same package is the lesser cost, and it is named here so the
choice is deliberate rather than incidental. That ordering is load-bearing for a
second reason now that terms are passed into `scan_text`: `:108` skips
marker-bearing lines for *every* detector, so moving this check after the scan
would blind the term detector on exactly the lines an adversarial input controls.

### LD-9: the guard scans the composed body, so the composer is inside the surface

`create_shadow_issue` truncates its details payload:

> `grep -n 'details_str' qor/scripts/create_shadow_issue.py` -> `196:        details_str = json.dumps(e["details"], indent=2)[:500]`

Measured: an identity past 500 characters is **absent from the emitted body**, and
one within 500 is present and caught. Truncation removes it from what is sent
rather than hiding it from the scanner -- but only because the guard scans the
composed `title` and `body` rather than the source events. A guard reading events
would scan text that is never sent while missing text the composer adds.

**The guarded surface is what is passed to `gh`.** `--dry-run` composes a body and
prints it without reaching the guard; that is operator-local output, deliberately
unguarded so an operator can inspect what would have been refused.

## Phase 1: pin the refusal

### Affected Files

- `tests/test_upstream_filing_guard.py` - NEW.

### Changes

Tests drive `identity_terms` against a `tmp_path` git repository and call `guard`
with constructed title/body pairs, so nothing depends on an operator-local file
or on this host's own remote.

### Unit Tests

- `test_origin_pair_is_parsed_from_the_remote_url` - a `tmp_path` repo whose
  origin URL carries this project's owner and name plus the customary `.git`
  suffix yields exactly `MythologIQ-Labs-LLC/Qor-logic`, with no suffix and no
  scheme. Red before: a naive parse keeps the suffix, which never equals a
  destination, so
  nothing drops and **every self-run refuses** -- the outcome
  `test_a_report_naming_its_destination_is_not_refused` exists to prevent and
  cannot catch, because it passes `origin` as a literal.
- `test_the_derivation_root_is_the_git_toplevel_not_the_cwd` - with the process
  working directory set to a subdirectory of a `tmp_path` repo, the derived
  directory term is the repository name, not the subdirectory. Red before:
  `workdir.root()` returns the cwd when `QOR_ROOT` is unset.
- `test_identity_terms_are_derived_from_the_git_remote` - a `tmp_path` repo whose
  origin names owner `acme-widgets` and repo `AcmeWidgets` derives both. Red
  before: no derivation function exists.
- `test_identity_terms_include_the_directory_name_without_a_remote` - a repo with
  no remote still yields its directory name, so the common case is configured.
- `test_the_overlay_adds_to_the_derived_terms_rather_than_replacing_them` - with
  an overlay present the result is the union; fails if the overlay is treated as
  authoritative.
- `test_a_report_carrying_an_identity_term_is_refused` - a body naming the
  derived repository raises.
- `test_a_term_is_matched_inside_a_compound_identifier` - term `acme-widgets`
  against `branch phase/12-acme-widgets-fix diverged` and `AcmeWidgetsRunner
  timed out`, both refused. Red under strict matching, measured: a trailing
  hyphen and a following word character defeat its lookarounds.
- `test_a_vocabulary_collision_over_refuses_rather_than_passing` - term `audit`
  against a fixture body containing this repository's ordinary vocabulary raises.
  The assertion is the raise, not a count: the 81 figure in LD-5 was measured on
  the live log, which the governance cycle appends to, so asserting it would
  couple the suite to moving state. Pins the residue as accepted behaviour so a
  later reader cannot mistake it for a bug and reintroduce a selector that fails
  open on the compound shape.
- `test_a_report_carrying_an_absolute_path_is_refused` - a drive-letter path in
  the body raises, and `str(exc)` contains no absolute path while `exc.findings`
  does.
- `test_a_report_carrying_a_lint_suppression_marker_is_refused` - a body whose
  line carries the allowlist marker raises, naming the marker rather than a
  detector finding. Red before: `scan_text` returns no finding for that line.
- `test_the_marker_refusal_precedes_scan_text` - a line carrying both the marker
  and an identity term raises the marker refusal, not a term finding. Red if the
  check moves after `scan_text`, which would blind the term detector on
  marker-bearing lines.
- `test_the_title_is_scanned_as_well_as_the_body` - a clean body with an offending
  title raises. One of the fourteen findings anonymized on 2026-09-11 was in a
  title.
- `test_a_report_naming_its_destination_is_not_refused` - origin and destination
  both `MythologIQ-Labs-LLC/Qor-logic`; `See Qor-logic#358 for the prior report.`
  files. Red before: it refuses, which makes the module unusable in its own home.
- `test_a_fork_sharing_the_destination_name_is_still_refused` - origin
  `AcmeCorp/Qor-logic`, destination `MythologIQ-Labs-LLC/Qor-logic`, body
  `found in our Qor-logic checkout while sealing` refuses. Red under a name-only
  predicate. This is GH #431 re-entering through the term loop.
- `test_a_checkout_with_no_remote_drops_nothing` - origin `None`; a body naming
  the checkout refuses. Fail-closed.
- `test_an_overlay_term_survives_the_destination_drop` - origin equal to
  destination, so every derived term drops, but an overlay term naming a third
  party still refuses.
- `test_an_empty_term_set_is_not_a_refusal` - origin equal to destination and no
  overlay, so nothing survives; a clean body files. Red if emptiness is treated
  as unconfigured, which would refuse every self-run.
- `test_the_guard_scans_the_composed_body_not_the_source_events` - an identity
  past the `[:500]` truncation is absent from the body and does not refuse; the
  same identity within 500 characters refuses. The pair must move together.
- `test_recall_holds_on_a_composed_body_not_only_on_prose` - a body built by
  `create_shadow_issue.build_body` from events whose `reason` carries an identity
  yields a finding for every tagged event.
- `test_the_override_files_and_logs_a_gate_override_event` - with a reason
  supplied, a body that would otherwise refuse files, and a `gate_override` event
  carrying the finding count, the destination and the reason is appended to an
  injected `tmp_path` log. Red before: there is no escape, so a colliding consumer
  cannot file at all.
- `test_a_reason_shorter_than_the_friction_minimum_is_refused` - a reason under 50
  characters raises before anything is filed or appended. Pins that the escape
  honours `override_friction.MIN_JUSTIFICATION_LEN` rather than sidestepping it.
- `test_the_escape_does_not_expire` - four consecutive acknowledged filings, each
  with a reason, all succeed against an injected log. Red before: an unjustified
  `gate_override` trips `DEFAULT_THRESHOLD = 3` and the third raises
  `OverrideFrictionRequired`, which is how a bare flag would strand the consumer
  the escape exists for.
- `test_the_override_does_not_apply_to_the_marker_refusal` - a body carrying the
  allowlist marker refuses even with the flag set. Red if one flag wraps the whole
  guard, which would file text no detector examined.
- `test_the_filing_path_routes_through_the_guard` - monkeypatch the guard to
  record its keyword arguments and the subprocess runner to raise if reached
  first, drive `create_shadow_issue.create_issue`, and assert the guard recorded
  with `destination` equal to the `--repo` value and `acknowledge` equal to the
  reason `main` was given. Red before: it does not call; red also under an
  implementation that adds the flag to argparse and drops it before `guard`,
  which every other test would pass.
- `test_the_doctrine_states_the_outbound_rule` - the doctrine's Enforcement
  section states the derivation rule, the marker refusal and the override, and
  the guard's own messages name the same three conditions. Binds the written rule
  to the implemented one.

## Phase 2: the guard, and the door routed through it

### Affected Files

- `qor/scripts/upstream_filing_guard.py` - NEW. One exception carrying
  `findings`, plus `identity_terms`, `origin_pair` and `guard`.
- `qor/scripts/create_shadow_issue.py` - `create_issue` derives terms, calls the
  guard before `gh`, and gains an `--acknowledge-boundary-findings` flag threaded
  from `main` to `create_issue`.

### Changes

```python
class UpstreamReportRefused(Exception):
    """A report that identifies its origin must not be filed.

    `str(exc)` is a summary: how many findings, in which field, on which line,
    of which class. It never reproduces the matched text, because a refusal
    message is the thing an operator most naturally pastes into an upstream
    issue. The matched text stays on `.findings` for local display only.
    """
    findings: list[str]


def identity_terms(root: Path, overlay: Path | None = None) -> list[str]:
    """`origin`'s owner and repository name, the directory name, plus the
    overlay when present. Derivation needs no operator action; the overlay is
    additive because it does not exist in a consuming repository (LD-3)."""


def guard(
    title: str, body: str, *,
    terms: list[str], origin: str | None, destination: str,
    acknowledge: str | None = None, log_path: Path | None = None,
) -> None:
    """Raise unless the report is safe to send outside this repository.

    Order is contractual. A line carrying the boundary-lint allowlist marker is
    refused FIRST, before `scan_text` runs and regardless of `acknowledge`:
    `scan_text:108` skips marker-bearing lines for every detector, so scanning
    first would blind the term detector on exactly the lines an adversarial
    input controls, and acknowledging it would file text nothing examined
    (LD-7, LD-8).

    Then, when `origin == destination`, every derived term is dropped -- the
    directory name included, because in that case the checkout IS the
    destination. Overlay terms are never dropped. An empty surviving set is not
    a refusal; it is what a self-run produces (LD-6).

    The survivors are passed to `scan_text`, which already matches terms by
    substring, so there is one matcher and no second implementation (LD-5).

    `acknowledge` is the operator escape of LD-7: an operator-written reason of
    at least `override_friction.MIN_JUSTIFICATION_LEN` characters. The findings
    are printed, a `gate_override` event carrying the finding count, the
    destination and that reason is appended via
    `override_friction.record_with_justification`, and the report proceeds. A
    shorter reason raises before anything is filed. It is a string, not a bare
    flag, because an unjustified override trips `DEFAULT_THRESHOLD = 3` and would
    strand the consumer this escape exists for (LD-7).

    `log_path` is where that event is appended; `append_event` requires it or
    `attribution`, and taking it here lets a test inject a destination instead of
    writing the live genome.

    It is an argv value, never anything the scanned body can set.
    """
```

`create_issue` gains an `acknowledge: str | None = None` parameter, so its
signature becomes `create_issue(repo, title, body, *, acknowledge=None)`, and
`main` passes `--acknowledge-boundary-findings` through to it. It supplies
`destination=repo`, `origin` from `origin_pair()`, and
`terms=identity_terms(_detect_git_root() or _workdir.root())`; `from qor import
workdir as _workdir` is already present at `:86`. The guard call sits immediately
before the `gh` invocation at `:210`, where `title` and `body` are both
parameters and no composition remains.

`origin_pair(root) -> str | None` is exported alongside the other three names. It
returns `owner/name` with any `.git` suffix and scheme stripped, or `None` when no
remote resolves. It is a named, tested function rather than an inline parse
because the entire drop decision compares its output against `destination`, and a
trailing `.git` would make every self-run refuse.

The guard does not rewrite: anonymization is a judgement the doctrine reserves to
a human, and a guard that edited the text would make it silently.

### Unit Tests

The Phase 1 tests go green. No new tests.

## Phase 3: record that the boundary has a reporting-time face

### Affected Files

- `qor/references/doctrine-publication-boundary.md` - one paragraph under
  Enforcement.

### Changes

> Enforcement also applies outbound. A report filed from one repository into
> another crosses the boundary at the moment it is transmitted, and that is the
> only moment at which the reporter still knows which details identify them. The
> tracked-file lint and the scheduled surface scan both act after the fact, so a
> filing path applies the detectors to what it passes to `gh`. It derives the
> reporter's identity terms from the checkout rather than requiring an overlay,
> because the overlay is operator-local and absent in the repositories that file;
> it refuses a report carrying an allowlist marker, because that marker records a
> maintainer's exception in a tracked file and carries no authority over text
> arriving from elsewhere; and it provides an operator acknowledgement that
> records a `gate_override` event, because a control with no escape and no edit
> surface is an outage rather than a gate.

"Transmitted" rather than "leaves": LD-9 scopes the guarded surface to what is
passed to `gh`, and a `--dry-run` print is deliberately outside it.

No sentence takes the form of a glossary definition for a registered term;
`doc_integrity_strict.py:144` compiles that pattern with `re.IGNORECASE` against
the registered set.

### Unit Tests

Covered by `test_the_doctrine_states_the_outbound_rule` in Phase 1.

## Feature Inventory Touches

Empty. This plan touches `qor/scripts/`, `tests/` and `qor/references/`. It
introduces no user-touchable feature under a product source tree.

## Definition of Done

### Deliverable: a report naming its origin cannot be filed

- **D1**: `create_shadow_issue` refuses a report whose composed title or body
  carries the filing repository's own identity as a derived term (origin owner,
  repository name, checkout directory name, or a declared overlay term), a
  cross-repository shape, or an absolute path. A product or package name the
  checkout cannot derive and the operator has not declared is **not** caught;
  LD-3 records that residue.
- **D2**: `qor/scripts/upstream_filing_guard.py` exposes `identity_terms`,
  `origin_pair`, `guard` and `UpstreamReportRefused`;
  `create_shadow_issue.create_issue` invokes the guard before `gh` at `:210`.
- **D3**: Plan gate artifact; audit verdict; seal entry citing this plan by
  content hash; research brief #788 stands behind it.
- **D4**: `test_the_filing_path_routes_through_the_guard` -- monkeypatching the
  guard to record and the subprocess runner to raise if reached first, the guard
  records. Observed before the change: it does not, because nothing calls it.

### Deliverable: the control is configured wherever a report can be filed

- **D1**: A filing path in a consuming repository, with no overlay and no
  operator action, catches a composed body naming that repository.
- **D2**: `identity_terms` derives from `origin` and the directory name and
  unions the overlay; there is no unconfigured refusal, because a checkout always
  states an identity.
- **D3**: LD-3 records why the overlay cannot be the source and LD-5 records the
  recall measured on the emitted surface, on one corpus.
- **D4**: `test_recall_holds_on_a_composed_body_not_only_on_prose` and
  `test_identity_terms_are_derived_from_the_git_remote` -- the first yields a
  finding for every tagged event in a `build_body` body, the second derives owner
  and name from a `tmp_path` remote.

### Deliverable: the guard refuses the origin without refusing the destination

- **D1**: A report naming the repository it is filed *into* is not refused; a
  report naming the repository it is filed *from* is. This deliverable makes no
  claim about a third party named in prose on the self-file path -- LD-6 records
  why the design cannot deliver that and why it is out of scope.
- **D2**: `guard` takes `origin` and `destination` and drops every derived term,
  directory name included, exactly when the two `owner/name` pairs are equal --
  never on the name alone, and never the overlay.
- **D3**: LD-6 records the measured self-refusal, the fork case, and the
  doctrine's permission at line 31.
- **D4**: `test_a_report_naming_its_destination_is_not_refused` and
  `test_a_fork_sharing_the_destination_name_is_still_refused` -- observed before
  the change, `See Qor-logic#358 for the prior report.` refuses, and a name-only
  predicate files a fork's own name.

### Deliverable: the scanned report cannot silence the scanner

- **D1**: A report carrying the boundary-lint allowlist marker is refused rather
  than scanned with that line skipped, and the operator escape does not apply to
  it.
- **D2**: The refusal is in `guard`, before `scan_text` is called and before the
  `acknowledge` branch; `scan_text`, `_ALLOW_RE` and the regexes are unchanged.
- **D3**: LD-8 records the measured latency of the hole -- 0 of 158 live events
  carry the marker -- and why the fix is caller-side.
- **D4**: `test_a_report_carrying_a_lint_suppression_marker_is_refused` and
  `test_the_override_does_not_apply_to_the_marker_refusal`.

### Deliverable: the over-refusal is recoverable

- **D1**: A consumer whose checkout name collides with this repository's
  vocabulary can file, by acknowledging the findings, and the acknowledgement is
  recorded.
- **D2**: `guard` takes `acknowledge: str | None` and `log_path`;
  `create_shadow_issue` exposes `--acknowledge-boundary-findings REASON` and
  threads it through `create_issue` to `guard`; the guard attaches the reason via
  `override_friction.record_with_justification` and appends a `gate_override`
  event carrying the finding count, the destination and the reason.
- **D3**: LD-5 states the residue at its measured size -- `qor` 126, `audit` 81 on
  the 591-line body -- and LD-7 records the `merge_velocity_check` precedent.
- **D4**: `test_the_override_files_and_logs_a_gate_override_event` and
  `test_the_escape_does_not_expire` -- the body files, the event is appended to an
  injected log, and four consecutive acknowledged filings all succeed. Observed
  before the change: no escape exists; and under a bare flag the third filing
  raises `OverrideFrictionRequired`.

### Deliverable: a refusal cannot itself carry what it refused

- **D1**: No refusal message reproduces the matched text or an absolute path.
- **D2**: `UpstreamReportRefused.findings` holds the detail for local display;
  `str(exc)` is a summary of counts, fields, lines and finding classes.
- **D3**: LD-9 records that a refusal is local operator output, in the same class
  as the `--dry-run` print.
- **D4**: `test_a_report_carrying_an_absolute_path_is_refused` asserts the raise,
  and asserts `str(exc)` contains no absolute path while `exc.findings` does.

## CI Commands

- `python -m pytest tests/test_upstream_filing_guard.py -q` — the refusal contract, term derivation, the call site, the escape, and the doctrine binding.
- `python -m pytest tests/test_shadow.py tests/test_publication_boundary_lint.py tests/test_boundary_scope_disclosure.py -q` — the filing path and the detectors this must not disturb.
- `python -m qor.scripts.publication_boundary_lint` — this plan and its artifacts introduce no boundary finding.
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` — chain integrity across the phase's entries.
- `python -m pytest -q` — full suite; the seal writes badges and header state that freshness tests read.
