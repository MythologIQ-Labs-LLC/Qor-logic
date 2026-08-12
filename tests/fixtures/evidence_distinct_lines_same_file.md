# Fixture: two distinct lines in one file, each paired

## Locked Decisions

**LD-1**: two locations, one file.

In-scope citations: `qor/scripts/plan_grep_lint.py:97` and `qor/scripts/plan_grep_lint.py:101`.

```
git show 2d356ec:qor/scripts/plan_grep_lint.py | grep -nE '_EVIDENCE_RE = re.compile' -> 97:_EVIDENCE_RE = re.compile(r"grep\b.*->")
git show 2d356ec:qor/scripts/plan_grep_lint.py | grep -nE '_FILE_LINE_RE = re.compile' -> 101:_FILE_LINE_RE = re.compile(r"\b[\w./-]+\.(?:py|ts|tsx|sql|rs|go|js):\d+\b")
```
