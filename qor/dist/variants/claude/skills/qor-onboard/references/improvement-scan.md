# Improvement Scan: Finding the Tutorial Change

The tutorial needs a change that is REAL (the operator's own repo, sealed for
real) and TINY (30 minutes end-to-end, trivially reversible). Scan in this
order and stop at the first class that yields candidates.

## Candidate classes (safest first)

1. **Doc drift**: a README statement contradicted by the code it describes
   (stale count, renamed command, dead link). Grep the README's concrete
   claims against the tree.
2. **Stale badge or version string**: any badge/count a script can verify.
3. **Missing docstring**: a public function whose module has docstring
   conventions the function ignores.
4. **Lint cleanup**: one file with an existing-linter warning (unused import,
   shadowed name) -- only when the repo already runs that linter.
5. **Orphan link**: a relative markdown link to a moved/deleted file.

## Risk criteria (all must hold)

- Single file, or two files with one obvious pairing (code + its test).
- No behavior change to production code paths (docs/lint/docstring classes),
  OR behavior change fully covered by one new test (lint class at most).
- Reversible with one `git checkout -- <file>`.
- No security surface, no dependency changes, no CI workflow edits.

## Exclusions (never tutorial material)

- Anything touching auth, secrets, crypto, or payment paths
- Schema or migration files
- Generated/compiled artifacts (fix the generator or nothing)
- Files with uncommitted operator changes

## Presenting candidates

Offer 2-3 with one line each: the file, the defect, the fix shape, and why it
is safe. The operator picks one or declines. On decline or an empty scan,
stop honestly -- a manufactured change teaches ceremony without meaning.
