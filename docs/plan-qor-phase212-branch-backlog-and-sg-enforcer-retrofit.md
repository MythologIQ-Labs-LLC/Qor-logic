# Plan: branch backlog and SG enforcer retrofit (Phase 212, GH #303 + GH #305)

**change_class**: governance

**doc_tier**: standard

**terms_introduced**: none

**boundaries**:
- limitations: Branch deletion covers refs proven reachable from `origin/main`
  only. The unmerged remainder is enumerated, not judged. Enforcer retrofit
  covers the ten legacy entries; it does not convert the lint to fail-closed.
- non_goals: No WARN-to-ABORT conversion of `sg_closure_lint` (only reasonable
  once the backlog is zero, and a separate decision). No deletion of any
  unmerged branch. No new detector for the ref surface.
- exclusions: GH #302 is a watch condition with nothing to implement; GH #304
  is a project-wide policy decision reserved for the operator. Neither is
  touched.

## Open Questions

None.

## Locked Decisions

**LD-1 — 111 of 129 remote heads are provably reachable from `origin/main`.**

`git ls-remote --heads origin | wc -l -> 129`; per-ref `git merge-base --is-ancestor <tip> origin/main` -> 111 exit-0, 18 non-zero or excluded.

Deletion is driven by that per-ref ancestry proof, not by `git branch -r --merged`
alone, because the porcelain form reflects a possibly stale local remote-tracking
view. The 18 retained are 16 genuinely unmerged, one open-pull-request head
(`dependabot/...`), and `main`. Every deleted ref's tip SHA is recorded first, so
a deletion is recoverable by SHA.

**LD-2 — The ten uncited entries are a closed legacy generation, not ongoing drift.**

`qor-logic scripts sg_closure_lint -> 40 entries, 10 without enforcer citation: SG-016 SG-017 SG-019 SG-021 SG-032 SG-034 SG-035 SG-036 SG-037 SG-038`

All ten carry numeric IDs; every entry added after GH #249 introduced the rule
uses a named ID (`SG-I…`, `SG-S…`, `SG-V…`). The rule has held for everything
filed since, so this is a bounded retrofit with a fixed denominator.

**LD-3 — A citation that does not enforce is worse than an admitted gap.**

`grep -n "cannot-automate" qor/scripts/sg_closure_lint.py -> 27:    re.compile(r"\bcannot-automate\b", re.IGNORECASE),`

The lint accepts either an enforcer citation or a `cannot-automate:` decision.
Citing a test that does not actually fail when the pattern recurs would silence
the lint without stopping the pattern -- the "advisory shipped, enforcer
deferred" shape catalogued under GH #147, one level more deceptive. Each
citation is therefore verified by confirming the named enforcer fails when its
pattern is reintroduced, and entries whose pattern is genuinely judgment-shaped
take the honest `cannot-automate:` route instead.

**LD-4 — Branch names are a third publication surface, and nothing scans it.**

`publication_boundary_lint` enumerates tracked files; `github_surface` reads
issue and pull-request text. Neither reads refs. The retained unmerged branch
the leaking branch name carries an identity term in its name, on a
public remote. Found while enumerating for LD-1 and remediated here rather than
left standing, because it is a live leak; building a ref-surface detector is a
follow-on and explicitly out of scope.

## Phase 1: Retire the merged branch backlog

### Affected Files

None tracked. The change is to remote refs.

### Changes

Delete the 111 refs proven reachable from `origin/main`, tip SHAs recorded
first. Rename the leaking branch name to a neutral name, preserving
its commits (create-then-delete; the branch is unmerged and its work is kept).
Enumerate the remaining unmerged refs in the seal entry for separate triage.

### Verification

- `git ls-remote --heads origin | wc -l` reports 18 before the rename and after
  deletion; the count is stated in the seal.
- `qor-logic scripts workspace_fragility_check --repo-root .` no longer reports
  `branch_only` on `active_branch_count`, or the residual signal is named.

## Phase 2: Retrofit the ten legacy enforcer citations

### Unit Tests

- `tests/test_sg_closure_retrofit.py::test_no_entry_lacks_an_enforcer_or_decision` -
  runs `sg_closure_lint` over the live doctrine and asserts zero uncited
  entries, so the retrofit cannot silently regress.
- `::test_every_cited_enforcer_names_a_resolvable_target` - for each citation
  added, asserts the named test file or module path exists on disk, so a
  citation cannot point at nothing.
- `::test_cannot_automate_decisions_carry_a_reason` - asserts every
  `cannot-automate:` marker is followed by non-empty prose, so the escape
  cannot be used as a bare silencer.

### Affected Files

- `qor/references/doctrine-shadow-genome-countermeasures.md` - ten entries gain
  either an enforcer citation or a `cannot-automate:` decision with a reason.
- `tests/test_sg_closure_retrofit.py` - NEW, the three tests above.

### Changes

Per entry, the existing codebase is searched for a test or module that already
fails when the pattern recurs; where one exists it is cited by path, and where
none does and the pattern is judgment-shaped, a `cannot-automate:` decision
records why. No new enforcers are written in this phase -- inventing ten
enforcers under a cleanup banner would be a far larger change wearing a small
label.

## Definition of Done

### Deliverable: merged-branch backlog retired

- **D1**: The fragility signal reflects real stabilization capacity rather than
  firing permanently on an accumulated ref count.
- **D2**: 111 refs deleted, each proven an ancestor of `origin/main`; 18
  retained with a stated reason each.
- **D3**: Seal entry records the before and after counts, the retained list, and
  the ancestry proof used.
- **D4**: `git ls-remote --heads origin` returns 18, and
  `workspace_fragility_check` is re-run and its output recorded.

### Deliverable: enforcer citations retrofitted

- **D1**: Every Shadow Genome countermeasure either names something that fails
  when its pattern recurs, or states honestly that it cannot be automated.
- **D2**: Ten entries updated in
  `qor/references/doctrine-shadow-genome-countermeasures.md`.
- **D3**: Seal entry records the split between cited and `cannot-automate:`,
  and states that no new enforcers were written.
- **D4**: `test_no_entry_lacks_an_enforcer_or_decision` asserts
  `sg_closure_lint` reports zero uncited entries; the other two tests assert
  citations resolve and decisions carry reasons.

### Deliverable: the leaking ref name

- **D1**: No public ref name carries an identity term.
- **D2**: the leaking branch name renamed, commits preserved.
- **D3**: Seal entry records that refs are a third surface no detector reads,
  and that a ref-surface detector is a declared follow-on.
- **D4**: `git ls-remote --heads origin` shows no identity term in any name,
  checked against the operator overlay.

## Feature Inventory Touches

None. This plan touches `qor/references/` and `tests/`, plus remote refs; it
introduces no user-touchable feature and modifies no FEATURE_INDEX row.

## CI Commands

- `python -m pytest tests/test_sg_closure_retrofit.py -q` — the retrofit contract.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `qor-logic scripts sg_closure_lint` — zero entries without citation or decision.
- `qor-logic scripts workspace_fragility_check --repo-root .` — the branch-count signal after deletion.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase212-branch-backlog-and-sg-enforcer-retrofit.md` — this plan asserts each path and command identically at every site.
