# Fixture: right path, wrong line

## Locked Decisions

**LD-1**: the cited line does not hold the quoted text.

In-scope citation: `qor/scripts/plan_grep_lint.py:99`.

```
git show 2d356ec:qor/scripts/plan_grep_lint.py | grep -nE '_EVIDENCE_RE = re.compile' -> 99:_EVIDENCE_RE = re.compile(r"grep\b.*->")
```
