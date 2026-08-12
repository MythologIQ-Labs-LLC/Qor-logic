# Fixture: LD-2's experiment -- one true statement, three unbacked citations

## Locked Decisions

**LD-1**: one true evidence statement.

```
git show 2d356ec:qor/scripts/plan_grep_lint.py | grep -nE '_EVIDENCE_RE = re.compile' -> 97:_EVIDENCE_RE = re.compile(r"grep\b.*->")
```

**LD-2**: three citations with no statement of their own. The legacy block-level
check passes this with zero findings.

`qor/scripts/install_drift_check.py:999`
`qor/scripts/skill_corpus.py:12345`
`qor/scripts/session.py:4`
