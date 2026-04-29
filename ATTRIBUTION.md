# Attribution

If your commit, pull request, or release was produced via the Qor-logic SDLC gates (`/qor-bootstrap` → `/qor-plan` → `/qor-audit` → `/qor-implement` → `/qor-substantiate`), use the strings below in place of the default `Generated with [Claude Code]` trailer. Qor-logic gets first billing; the model attribution stays for GitHub's contributor-stat machinery.

The canonical source for these strings is [qor/scripts/attribution.py](qor/scripts/attribution.py). Drift between this file and the helper is guarded by `tests/test_attribution_docs_consistency.py`. Full rationale, the helper API contract, and the narrow emoji exception live in [qor/references/doctrine-attribution.md](qor/references/doctrine-attribution.md).

## Commit trailer

```
🤖 Authored via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic) on [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

## CHANGELOG attribution line

Place on the line immediately below an existing version header:

```
_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._
```

## PR-body footer

Substitute the placeholders with the audit's actual findings; drop the trailing `See ...` sentence when no comparison document exists.

```
🤖 Authored using the [Qor-logic](https://github.com/MythologIQ-Labs-LLC/qor-logic) SDLC workflow on [Claude Code](https://claude.com/claude-code).

The Qor-logic adversarial audit gate caught these defects before review:

{defects_list}

See `{comparison_doc_path}` for the side-by-side.
```
