# Phase 268 -- the cross-repo detector flags this repository's own issues

**change_class**: hotfix
**iteration**: 20
**risk_grade**: L2
**closes**: part of GH #431

## Problem

`publication_boundary_lint._CROSS_ISSUE_RE` matches any `Repo#123` shape and  <!-- boundary-lint: ok=detector-specification -->
reports it as a cross-repository reference, including references to the
repository being scanned. Measured against the live GitHub surface, 5 of the 17
cross-repo issue-shape findings name `Qor-logic` itself:

```
pr #387 (body):38: cross-repo issue shape: Qor-logic#357
pr #386 (body):43: cross-repo issue shape: Qor-logic#359
pr #372 (body):44: cross-repo issue shape: Qor-logic#366
pr #371 (body):41: cross-repo issue shape: Qor-logic#364
pr #370 (body):36: cross-repo issue shape: Qor-logic#363
```

The flagged line has this shape, with the outside identifier replaced by a
synthetic one per the doctrine's required treatment:

> Relay: `ExampleOrg/ExternalRepo#97` (...). Native owner:  <!-- boundary-lint: ok=detector-specification -->
> `MythologIQ-Labs-LLC/Qor-logic#357`.

The first reference is a genuine finding. The second names this repository's own
issue and is correct behaviour.

**The detector already holds the concept it is missing.** Executed against the
synthetic identifiers this document uses, so the record and the inputs match:

```
see OtherRepo#123                      -> FLAGGED  <!-- boundary-lint: ok=detector-specification -->
see #45                                -> clean
see Qor-logic#357                      -> FLAGGED
see MythologIQ-Labs-LLC/Qor-logic#357  -> FLAGGED
see ExternalRepo#97                    -> FLAGGED  <!-- boundary-lint: ok=detector-specification -->
see ExampleOrg/ExternalRepo#97         -> FLAGGED  <!-- boundary-lint: ok=detector-specification -->
```

A bare `#45` passes as a self-reference; the same reference written in its
qualified form is flagged. And the sibling detector on the line above already
excludes self: the URL detector's loop compares its match against the
`_SELF_REPO` constant declared above it. The issue-shape loop beside it
appended unconditionally. One detector knew which repository it was scanning
and the one beside it did not.

## Why an unfixable finding is worse than a missing one

A self-reference cannot be remediated. Naming your own issue is what a
cross-reference is for, so the only ways to clear these five findings are to
delete correct text or to add an allowlist marker to every line that cites an
issue in the ordinary way. Both are worse than the finding.

`doctrine-publication-boundary.md:93-95` records where that leads for this exact
control: before Phase 208 it "reported granted exceptions as violations, stayed
permanently red, and was wired to no gate -- a control nobody can satisfy". This
is the same failure re-entering through a different detector, and the count it
inflates is the one an operator uses to decide whether the surface is clean.

## Design

### D1: the skip, and what it compares

The issue-shape loop skips a match only when it names THIS repository -- by
exact name AND by owner. The shipped form:

```python
_SELF_OWNER, _SELF_REPO_NAME = _SELF_REPO.split("/")
_OWNER_PREFIX_RE = re.compile(r"([\w.-]+)\s*[\\/]\s*$")
...
    for m in _CROSS_ISSUE_RE.finditer(line):
        if m.group(1).lower() == _SELF_REPO_NAME.lower():
            owner = _OWNER_PREFIX_RE.search(line[: m.start()])
            if owner is None or owner.group(1).lower() == _SELF_OWNER.lower():
                continue  # ours: bare, or owner-qualified with our owner
        findings.append(...)
```

The name comparison is exact rather than prefix, because `[\w-]{2,}` is greedy
and captures a sibling repository's full name; a `startswith` would stop
reporting one whose name extends this one's. The owner qualification and the
separator are D2, which is where the reasoning for both lives.

An earlier iteration compared the name alone, with no owner check, and justified
it at length. That version is not described here because it is not what ships and
this document is what the seal binds. D2 records what was wrong with it.

### D2: the skip compares the owner as well as the name

An earlier iteration compared the repository name alone and recorded the owner
case as an accepted limitation: a repository named `Qor-logic` under a different
owner would be treated as self and skipped. That was the wrong call and it was
reached by weighing the change's size rather than its reach.

This detector gates CI fail-closed (`ci.yml:126`, no `|| true`) and is shared by
the nightly surface scan. Narrowing it removes findings, and a removed finding is
indistinguishable from a clean scan by the output the gate prints. So a widened
blind spot here under-reports a doctrine violation silently, which is the one
failure mode this control cannot tolerate.

The skip therefore checks an owner written immediately before the name, and
treats the reference as ours only when the owner is ours or absent:

```
see Qor-logic#357                       clean   (bare: ours)
see MythologIQ-Labs-LLC/Qor-logic#357   clean   (our owner)
see SomeOtherOrg/Qor-logic#5            FLAGGED (foreign owner, same name)  <!-- boundary-lint: ok=detector-specification -->
see ExternalRepo#97                     FLAGGED  <!-- boundary-lint: ok=detector-specification -->
see Qor-logic-plus#129                  FLAGGED (exact-name equality, not prefix)  <!-- boundary-lint: ok=detector-specification -->
see #45                                 clean
```

Two tests pin this. One is red under the name-only comparison; the other is red
under a slash-only separator, because the separator accepts `\` and surrounding
space as well as `/`. That generosity is deliberate and asymmetric: an
unrecognised separator makes the owner lookup return `None`, which the code
reads as "ours" and skips, so every way of failing to see an owner fails toward
silence. Over-reporting is resolvable per line with a marker; under-reporting is
not visible at all. This project is Windows-primary and the lint's own findings
print with backslash paths on this platform.

The capture is safe against truncation by construction: `[\w.-]+` is anchored
only by the separator, so `re.search` returns the leftmost start that completes
and the capture is always the whole owner token, never a suffix. That is what
stops `Not-<our-owner>/` and `evil.<our-owner>/` from reading as ours; an
`endswith` comparison would not.

**How this was found, because the method is the point.** Twelve review rounds
examined this document's internal consistency and none examined what the change
stops catching. Enumerating that -- one command, running the detector over a
foreign-owner case -- surfaced the gap immediately. For any change to a detector,
the question "what does this stop reporting" is cheaper than a consistency pass
and answers something a consistency pass cannot.

## Blast radius, measured

`scan_text` is shared by two surfaces:

| surface | consumer | detectors | findings |
|---|---|---|---|
| tracked files | `publication_boundary_lint`, fail-closed in CI `gate-chain-completeness` (`ci.yml:126`, no `\|\| true`) | structural + overlay locally, structural in CI | see below |
| GitHub surface | `github_surface`, read-only on `nightly-health.yml:51` | **structural only** -- the workflow passes no `--terms-file` | 17 -> 12 |

**The tracked-file number is not zero and this plan previously said it was.** The
lint scans `git ls-files` PLUS `--others --exclude-standard`, so it covers the
uncommitted gate artifacts and this document. Measured on a tree that included
them, before markers: **23 findings**. The earlier "0" was measured before this
phase authored anything, and was quoted afterwards as though it still held --
the same measure-before-asserting failure recorded against earlier phases in
this session.

The tracked-file number is a function of the tree and is stated with its
precondition rather than as a bare figure:

| tree | tracked-file lint |
|---|---|
| plan present, D1 absent | **19 findings, exit 1** |
| plan present, D1 present | **0 findings, exit 0** |

The 19 are self-references on lines of this document and of its test file, and they carry no
exception marker deliberately: `doctrine:31` permits a self-reference, so
recording an exception on one would argue against this phase's own thesis. D1
declassifies them, which is why the plan is gate-clean only once the change it
proposes exists. The consequence is that this branch is red in
`gate-chain-completeness` for the plan-audit window and green from the
implementation commit onward; the shipped commit carries both.

Re-derive rather than trust either figure. CI Commands carries both: the lint
alone gives the with-D1 row, and the lint with only the detector restored from
the parent gives the without-D1 row. It restores by `git checkout` rather than
`git stash` deliberately, and the two forms differ by whether the change is
committed.

Before the implementation commit git holds no copy of D1, so the sequence must
save one explicitly. `git stash` looks like it does this and does not do it
safely: a blocked pop is silent when the sequence uses `;` and `-q`, its failure
leaves the detector absent, and the lint then reports exactly the without-D1
figure the reader expected. That happened once during this phase and the change
survived only because an unrelated temporary copy existed. A bare
`git checkout -- <path>` restore is no better -- it restores from the index,
which for an uncommitted change is the version without D1, so it destroys the
change while appearing to undo the experiment. Both failures are silent and both
produce the expected number.

After the implementation commit git holds both versions and no copy is needed. Neither is
referred to by position, because an earlier draft pointed at a line number and
then gained a second command in the same edit, leaving the pointer reaching only
one of the two figures it governed. Both figures describe the tree this phase ships: the detector change, the tests named
in the Tests table, this document, and the gate artifacts, all present together. No commit
that currently exists is that tree -- the parent lacks the entire phase, and a
clean checkout of it yields neither figure, because this document supplies most
of the without-D1 findings and is not there. The first tree where both rows
reproduce is the seal commit, but NOT by running CI Commands unmodified: after
the implementation commit `git stash push` on an unchanged path saves nothing
and both lint invocations report the with-D1 figure. Restore only the detector,
leaving this document and the tests in place, because they supply most of the
without-D1 findings and any method that removes them yields a third number:

```
git checkout <seal>^ -- qor/scripts/publication_boundary_lint.py
python -m qor.scripts.publication_boundary_lint      # the without-D1 row
git checkout HEAD -- qor/scripts/publication_boundary_lint.py
```

**That sequence is correct only AFTER the implementation commit**, where `<seal>^`
lacks D1 and `HEAD` carries it. Substituting `HEAD` for `<seal>^` before the
commit makes the measure and restore steps the same command: it overwrites the
only copy of D1 in both the index and the working tree, then restores that same
D1-less file. `git checkout <tree-ish> -- <path>` writes both, and a bare
`git checkout -- <path>` restores from the index it just overwrote, so nothing
survives. The lint then prints the without-D1 figure a reader expects, which is
what makes the failure invisible.

Before the commit the working tree is the only place D1 exists, so no git-only
method is safe and the copy must be taken outside git first. CI Commands gives
that form. Both rows in the table above were obtained with it. An earlier draft cited the parent commit as the
identity of a working tree that differed from it; a commit is not the identity
of a dirty tree.

**The 35/30 pair belongs to a local run, not to the workflow.**
`nightly-health.yml:51` invokes the scanner with no `--terms-file`, and
`github_surface.py:118` loads terms only when that flag is given, so the nightly
run is structural-only: it sees the 17 issue-shape findings and will see 12. The
35 and 30 figures include the 18 identity-term findings that only a local run
with the gitignored overlay can produce. Both pairs are arithmetically
consistent (17-5=12, 12+18=30, 17+18=35); the earlier table attributed the local
number to the workflow.

**Neither number changes the job's colour.** `github_surface.py:130` returns
`1 if findings else 0`, and `nightly-health.yml` sets no `continue-on-error`, so
the step fails at 17 and fails at 12. The benefit is that all 12 are actionable;
there is no gate-state improvement and this plan does not claim one.

## Tests

No existing test pins the current behaviour. `tests/test_publication_boundary_lint.py:51-54`
uses `OtherRepo#123` and asserts that a bare `#45` passes as a self-reference,  <!-- boundary-lint: ok=detector-specification -->
which is the precedent this change extends rather than contradicts.

| Test | Status before |
|---|---|
| `test_qualified_self_reference_is_not_a_cross_repo_finding` | red: `Qor-logic#357` is flagged without D1 |
| `test_owner_qualified_self_reference_is_not_a_cross_repo_finding` | red: `MythologIQ-Labs-LLC/Qor-logic#357` is flagged without D1 |
| `test_a_foreign_repo_issue_shape_is_still_a_finding` | green before; pins that the detector did not simply stop working |
| `test_a_sibling_repo_whose_name_extends_this_one_is_still_a_finding` | red; the highest-value test in the set. `[\w-]{2,}` is greedy and includes the hyphen, so a sibling repository whose name extends this one's is captured in full. A `startswith` comparison instead of `==` would silently stop reporting it, and nothing else in the suite would notice |
| `test_a_line_citing_both_self_and_foreign_reports_only_the_foreign` | red; built from the SHAPE that produced the false positive, using a synthetic foreign identifier. It must not embed the real outside repository name -- the test is a tracked artifact and the doctrine prohibits it there |
| `test_a_foreign_repo_sharing_this_repos_name_is_still_a_finding` | red under the name-only comparison; pins that the skip checks the owner, so a foreign repository sharing this one's name is still reported |
| `test_a_backslash_separated_foreign_owner_is_still_a_finding` | red under a slash-only separator; pins that a Windows-style path does not hide a foreign owner |

`test_a_foreign_repo_issue_shape_is_still_a_finding` is green beforehand and is
labelled as such rather than counted as test-first coverage.
`test_a_line_citing_both_self_and_foreign_reports_only_the_foreign` is the one
that would catch a fix that over-skips: a line holding both kinds must still
report the genuine one. Tests are named here rather than indexed by number,
because an earlier draft renumbered the table and left this sentence pointing at
the wrong row.

**Every test carrying a foreign issue shape must therefore carry the
marker** `# boundary-lint: ok=detector-own-fixture`. Omitting it
reddens the same fail-closed gate this plan is trying not to redden. The foreign identifier in every one is synthetic; the real one this phase found on the live
surface must not enter a tracked test.

## Affected files

| File | Change |
|---|---|
| `qor/scripts/publication_boundary_lint.py` | unpack `_SELF_OWNER, _SELF_REPO_NAME`; add `_OWNER_PREFIX_RE`; the issue-shape loop skips a match only when the name is exactly ours AND the owner is ours or absent |
| `qor/scripts/plan_code_parity.py` | new; asserts this plan's D1 block matches the source it describes, run at the seal because both sides stay editable until the commit |
| `tests/test_publication_boundary_lint.py` | the tests named in the Tests table |

One production file. Three behaviours in one loop: an exact-name comparison, an
owner qualification, and a separator that accepts backslash and surrounding
space as well as forward slash.

## Scope boundary

Not in scope: anonymising the remaining findings on the GitHub surface.
Deferred to the operator, and tracked by GH #431, which stays open after this
phase.

An earlier draft justified that by quoting `doctrine-publication-boundary.md:82-83`,
"rewriting an operator's issue text unattended is not a decision a lint should
make". That sentence is about a scheduled lint's autonomy, not about a governed
cycle's obligation, and `:108` points the other way for an agent: "Treat a
discovered historical reference as remediation work, not precedent." Narrowing
this phase to one detector fix is a defensible scoping call; it is not something
the doctrine requires, and it is stated as a deferral rather than dressed as a
constraint.

Not in scope: the identity-term half of GH #431's findings. Those are genuine and
unaffected by this change.

Not in scope: bare repository-name references in prose, which the issue-shape
detector does not match.

An earlier draft argued these were not violations at all, because the operator's
terms overlay does not list the name. That reasoning is wrong and is corrected
here: the policy is `doctrine-publication-boundary.md:5-7` and `:20-23`, which
prohibit "repository, organization, owner, product, and package names"
outright. The overlay is a local detection aid that CI provably does not load
(`ci.yml:123-125` passes no `--terms-file`). Absence from the overlay
establishes non-detection, not permission. Those references are undetected
violations and belong to GH #431's remediation, not to a category of permitted
text.

## CI Commands

```
python -m qor.scripts.plan_code_parity --plan docs/plan-qor-phase268-self-reference-detector.md --source qor/scripts/publication_boundary_lint.py
python -m qor.scripts.publication_boundary_lint
# without-D1 row, BEFORE the implementation commit (D1 uncommitted, so git holds no copy):
# `&&` is load-bearing: if the copy fails, the destructive checkout must not run.
# Path is repo-relative and gitignored, so it resolves in PowerShell as well as sh.
cp qor/scripts/publication_boundary_lint.py .qor/d1.bak &&   git checkout HEAD -- qor/scripts/publication_boundary_lint.py &&   python -m qor.scripts.publication_boundary_lint
cp .qor/d1.bak qor/scripts/publication_boundary_lint.py
# after the implementation commit, git holds both versions and no copy is needed:
#   git checkout <seal>^ -- qor/scripts/publication_boundary_lint.py
#   python -m qor.scripts.publication_boundary_lint
#   git checkout HEAD -- qor/scripts/publication_boundary_lint.py
python -m pytest tests/test_publication_boundary_lint.py tests/test_github_surface_boundary.py tests/test_boundary_untracked_coverage.py tests/test_boundary_scope_disclosure.py tests/test_publication_boundary_policy.py -q
python -m pytest -q
```

## Limitations stated

Every figure in this section lives in **Blast radius, measured** and is not
restated here. The defects in this plan were overwhelmingly restatements -- a caveat repeating
a count, prose indexing a table by number, a table mirroring the test file --
and not one was at the place the fact is established. Re-deriving from the tree
cannot catch them, because a copy's truth-maker is the other paragraph. So the
copies are deleted rather than corrected.

- An owner separated from the repository name by a line break is not seen, since
  the detector scans one line at a time, so an owner-qualified foreign reference
  split across a wrap is skipped. Inherent rather than introduced: a bare
  `Qor-logic#5` is genuinely indistinguishable from ours, and the name-only rule
  skipped it too. Stated rather than fixed.
- The issue-shape regex requires an uppercase initial, so an all-lowercase
  foreign repository shape is never matched. Pre-existing, not introduced here,
  and not fixed here; stated because it bounds what a clean scan means.
- The change lowers a reported count without remediating anything. A reader
  comparing scans across this phase should not read the drop as progress: it is
  the removal of findings nobody could have cleared. The figures themselves, and
  which of them CI can produce, are in **Blast radius, measured**.
- The tracked-file surface is not inert and the number depends on whether D1 is
  present. Both figures, their precondition, and the command that re-derives
  them are in **Blast radius, measured**. They are deliberately not repeated
  here: an earlier draft of this section carried them, they went stale twice
  across edits to scanned files, and that recurrence is what produced this
  section's present shape.
- The figures in **Blast radius, measured** are hand-maintained, not automated,
  and will go stale on the next edit to any scanned file. The method for
  re-deriving them is stated there.

