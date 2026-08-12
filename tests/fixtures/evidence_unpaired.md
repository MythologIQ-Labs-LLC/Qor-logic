# Fixture: one citation paired, a sibling not

## Locked Decisions

**LD-1**: paired.

In-scope citation: `qor/scripts/plan_grep_lint.py:97`.

```
git show 2d356ec:qor/scripts/plan_grep_lint.py | grep -nE '_EVIDENCE_RE = re.compile' -> 97:_EVIDENCE_RE = re.compile(r"grep\b.*->")
```

**LD-2**: no statement of its own, riding on LD-1's.

In-scope citation: `qor/scripts/plan_grep_lint.py:101`.
