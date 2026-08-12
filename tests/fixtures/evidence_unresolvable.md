# Fixture: path absent at the cited revision

## Locked Decisions

**LD-1**: the path does not exist at this ref.

In-scope citation: `qor/scripts/does_not_exist_anywhere.py:12`.

```
git show 2d356ec:qor/scripts/does_not_exist_anywhere.py | grep -nE 'anything' -> 12:whatever this would have said
```
