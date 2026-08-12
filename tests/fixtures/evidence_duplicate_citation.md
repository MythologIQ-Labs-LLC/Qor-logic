# Fixture: one location cited three times

## Locked Decisions

**LD-1**: `qor/scripts/plan_grep_lint.py:97` in prose.

```
git show 2d356ec:qor/scripts/plan_grep_lint.py | grep -nE '_EVIDENCE_RE = re.compile' -> 97:_EVIDENCE_RE = re.compile(r"grep\b.*->")
```

| citation | paired in |
|---|---|
| `qor/scripts/plan_grep_lint.py:97` | LD-1 |
| `qor/scripts/plan_grep_lint.py:97` | LD-1 |
