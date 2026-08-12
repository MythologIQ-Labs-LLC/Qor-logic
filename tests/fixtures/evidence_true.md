# Fixture: evidence that reproduces

## Locked Decisions

**LD-1**: the shape predicate lives here.

In-scope citation: `qor/scripts/plan_grep_lint.py:97`.

```
git show 2d356ec:qor/scripts/plan_grep_lint.py | grep -nE '_EVIDENCE_RE = re.compile' -> 97:_EVIDENCE_RE = re.compile(r"grep\b.*->")
```
