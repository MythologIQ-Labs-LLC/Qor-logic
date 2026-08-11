# Research Brief

**Date**: 2026-08-11
**Analyst**: The Qor-logic Analyst
**Target**: GH #309, #311, #312 -- gates that report clean on a surface they cannot see
**Scope**: Verify each claim by running it; correct #309's premise before it shapes a fix

---

## Executive Summary

All three are real. **#309 is mis-stated in a way that changes the remedy**, and the
correction came from running the lint rather than reading its source.

The filed title says the lint "misses files staged but not yet committed". Staged
files are in fact scanned -- `git ls-files` reads the index. **Untracked** files
are invisible, and the seal ceremony runs the lint before `git add`, which is
precisely when new files are untracked. The remedy is therefore ordering and
untracked coverage, not a `--staged` flag.

## Findings

### 1. #309 gap 1: untracked, not staged

Counterfactual against a probe file carrying a structural violation:

| state | findings | rc |
|---|---|---|
| untracked | **0** | 0 |
| staged | 1 | 1 |

`_tracked_files` (`publication_boundary_lint.py:41-43`) shells out to
`git ls-files`, which lists the index. A `git add`ed file is in the index and is
scanned. An untracked file is not listed and is not scanned.

The issue's three cited misses are all consistent with the corrected reading --
in each, the file was new and unstaged when the operator ran the lint. So is the
fourth, from this session: `research-iter1.json` carried an operator path,
reported clean while the gate directory was untracked, and surfaced only after
`git add -A`.

**The remedy the issue proposes -- add `--staged` like the secret scanner -- would
not have caught any of the four.** A `--staged` mode narrows the surface to the
index, which is a subset of what is already scanned. The real fixes are:

- scan untracked-but-not-ignored files as well (`git ls-files --others
  --exclude-standard`), and
- run the boundary lint **after** staging in the seal ceremony, where the issue's
  second suggestion is correct.

**DRIFT -- and the drift is in the direction of a fix that does nothing.**

### 2. #309 gap 2 is structural and cannot be closed by scanning

`.gitignore:37` ignores `.qor/private/`, so the terms overlay is absent in CI by
design: a tracked denylist of private identifiers in a public repository would
publish the very strings it exists to suppress.

CI therefore runs the four structural detectors only. Both identity-term leaks the
issue cites were invisible to it, correctly.

No amount of scope widening fixes this. The honest response is to state that the
local gate is **authoritative** for identity terms and that CI is authoritative
only for structural patterns -- and to make the seal record which of the two ran.
A gate whose coverage differs by environment should say so where the evidence
lands.

### 3. #311 confirmed, and it is a closed loop

`seal_artifacts.py:67-72`: `render_system_state_header` raises
`SYSTEM_STATE header markers missing` when either marker is absent.

The remediation the sibling `--check` prints on failure is *re-run Step 6
`--write`* -- and `--write` is the raiser. A repository adopting the toolkit
whose `SYSTEM_STATE.md` never carried the markers cannot bootstrap out, so the
documented remediation does not close its own loop.

The upstream fix (recorded in the issue) seeds whichever marker is absent rather
than raising, with two details worth preserving: insert **positionally** under
the `# ` title rather than appending, because both patterns are line-anchored
under `re.MULTILINE` and a marker at end-of-file satisfies the regex while
producing a document whose header block is not its header; and seed **only** the
missing marker, because a file with one and not the other is half-migrated, not
broken.

An existing test asserts `raises(ValueError)` on that path -- it encoded the
defect as a contract and must change. The malformed-`snapshot` `ValueError` is a
different check (it validates the caller's argument, not the document) and stays.

### 4. #312 is the inverse of a countermeasure already on the record

`SG-GrepShapedRunclaim-A` covers grep-shaped evidence producing a false
*positive*. #312 proposes the false-*negative* half: a module's absence from an
importer's symbols read as an absent control, when the two are connected through
an intermediary by design.

Both reduce to accepting a lexical result as a semantic one. Having only the
positive half on record demonstrably did not prevent the negative-half mistake.

The second tell generalizes and is worth keeping: the claim under test came from
an ADR, and ADRs are written in the vocabulary of authorities and consumption,
not imports. Testing an architectural claim by import graph is a category error
from the first step.

## Blueprint Alignment

| Claim as filed | Verified | Status |
|---|---|---|
| #309: staged files are missed | staged are SCANNED; **untracked** are missed | **DRIFT** |
| #309: `--staged` mode is the fix | would narrow to a subset already covered | **DRIFT** |
| #309: run the lint after staging | correct, and sufficient with untracked coverage | MATCH |
| #309: CI cannot see identity terms | confirmed structural (`.gitignore:37`) | MATCH |
| #311: `--write` cannot seed its own markers | confirmed at `seal_artifacts.py:67-72` | MATCH |
| #312: inverse of an existing countermeasure | confirmed; both are lexical-for-semantic | MATCH |

## Recommendations

1. **Scan untracked-but-not-ignored files**, and move the seal ceremony's boundary
   lint to after staging. Do not add `--staged`; it would narrow the surface.
2. **Record which detector set ran** in the seal entry -- structural-only versus
   structural-plus-identity -- so a green boundary result carries its own scope.
3. **Seed the missing marker positionally**, one marker at a time, and rewrite the
   test that encoded the raise as a contract.
4. **Add `SG-GrepAbsenceAsIntegrationAbsence-A`** and cross-reference it with
   `SG-GrepShapedRunclaim-A`, so the pair is reachable from either direction.
5. **Counterfactual tests throughout**, per Phase 218's LD-5: an untracked
   violating file must be found, a markerless `SYSTEM_STATE.md` must be seeded.
   Each must fail against `HEAD`.

## Updated Knowledge

This is the fourth correction this session where a written claim disagreed with
the same claim executed -- #314's premise, #316's mechanism, the 510 gap, and now
#309's surface. The pattern is stable enough to name: **a defect report written
from reading is a hypothesis, not a finding.** Candidate framing for the Shadow
Genome if it recurs once more.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
