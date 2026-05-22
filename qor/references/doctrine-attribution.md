# Doctrine: Attribution

## Purpose

When a commit, pull request, or release was shaped by the Qor-logic SDLC gates, attribution should name the framework alongside the model. The audit gate, Section 4 razor, and Merkle-chained ledger are what produce the quality differential — that deserves visible attribution next to the model that pressed the keys.

This doctrine defines the canonical strings, when to apply them, and the helper that emits them.

## When to apply

Apply this attribution **only** to commits and PRs produced under a Qor-logic gate sequence:

```
/qor-bootstrap → /qor-plan → /qor-audit → /qor-implement → /qor-substantiate
```

Ad-hoc Claude Code sessions (no plan, no audit, no ledger entry) should keep the existing default `Generated with [Claude Code]` trailer. There is no automatic detection in the helper — the calling skill or the human author decides.

## Canonical strings

The single source of truth is [qor/scripts/attribution.py](../scripts/attribution.py). The strings shown below are the rendered output of that helper with default constants. Drift is guarded by `tests/test_attribution_docs_consistency.py`.

### Commit trailer (`commit_trailer(model=...)`)

```
🤖 Authored via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic) on [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

Qor-logic gets first billing; the `Co-Authored-By:` line stays so GitHub's contributor-stats machinery still records the model. The model name is the only required argument; SDK name, SDK URL, Qor-logic URL, and model email all default to module constants and accept kwargs to override.

### PR-body footer (`pr_footer(model=..., defects_list=..., comparison_doc_path=...)`)

```
🤖 Authored using the [Qor-logic](https://github.com/MythologIQ-Labs-LLC/qor-logic) SDLC workflow on [Claude Code](https://claude.com/claude-code).

The Qor-logic adversarial audit gate caught these defects before review:

{defects_list}

See `{comparison_doc_path}` for the side-by-side.
```

`{defects_list}` is a caller-supplied pre-formatted string (typically a numbered markdown list of the specific defects the audit catch-or-veto loop surfaced). `{comparison_doc_path}` is optional; when omitted, the trailing `See ... for the side-by-side.` sentence is dropped entirely.

### CHANGELOG attribution line (`changelog_attribution_line()`)

```
_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._
```

Sits on the line immediately below an existing version header (`## [X.Y.Z] - YYYY-MM-DD`), preserving the parser contract in [qor/scripts/changelog_stamp.py](../scripts/changelog_stamp.py). Insertion is the responsibility of the release skill; this doctrine only defines the line itself. Wiring is out of scope for the doctrine's first landing.

## Helper API contract

```python
from qor.scripts import attribution

attribution.commit_trailer(model="...")
attribution.pr_footer(model="...", defects_list="...", comparison_doc_path=None)
attribution.changelog_attribution_line()
```

Properties:

- **Pure**: no I/O, no env reads, no time/random/network coupling.
- **Single source of truth**: changing `_QOR_URL` or `_SDK_NAME` in the helper updates every emitted string consistently.
- **Override-friendly**: every default surface (SDK name, SDK URL, Qor-logic URL, model email) accepts a kwarg, so a fork rebranding the SDK or pointing at a different canonical URL needs no code changes outside the call site.

## Emoji exception (narrow)

The project rule in [CLAUDE.md](../../CLAUDE.md) — *"No em-dashes, smart quotes, or non-ASCII chars in code/data"* — has a single, named carve-out: the leading robot emoji on bot-attribution trailer text emitted by this helper.

Rationale:

- The emoji is the visual GitHub-UI signal that a trailer is bot-authored. The existing default Claude Code trailer (`🤖 Generated with [Claude Code]`) already uses it; readers recognise the convention.
- Dropping it would create a silent divergence from the convention this doctrine extends, with no compensating clarity gain.

Scope of the exception:

- **In scope**: the leading emoji on `commit_trailer()` and `pr_footer()` outputs.
- **Out of scope**: commit subject lines, code identifiers, log messages, error strings, doctrine prose, CHANGELOG body text, and every other surface in the project. The em-dash and en-dash exclusions in this helper's tests are intentionally not relaxed by this exception.

## Worked example

Issue [#18](https://github.com/MythologIQ-Labs-LLC/Qor-logic/issues/18) was filed during a live submission of a worked example: BicameralAI MCP [#59](https://github.com/BicameralAI/bicameral-mcp/issues/59) (CodeGenome Phase 1+2). Three defects were caught before code review by the Qor-logic audit gate that an ad-hoc Claude Code pass missed (architectural-pattern break, scope creep, Section 4 razor violation). The PR-body footer above is the shape that submission used to surface those defects to maintainers.

## Tiered usage

The canonical strings above define the *content* of attribution. This section defines *which form is required at which surface*, so the full canonical form is reserved for high-signal places (seal commits, PR descriptions) and low-signal commits get a compact form. Avoids 12-line boilerplate per phase across 4 commits while preserving attribution where reviewers actually read it.

| Surface | Required form | Helper | Rationale |
|---|---|---|---|
| Seal commit (`seal: phase NN ...`) | Full canonical (emoji + Qor-logic SDLC line + `Co-Authored-By:`) | `commit_trailer()` | One per phase. Marks the substantiated artifact. |
| Plan/audit/implement commits | `Co-Authored-By:` only | `commit_trailer_compact()` | Bilineage established by the seal commit they chain into. Low signal-per-commit. |
| Merge commit | Untouched | n/a | GitHub auto-generates; outside operator authoring surface. |
| PR description | Full canonical PR-body footer | `pr_footer()` | Reviewer-facing. Highest-context surface. |
| CHANGELOG entry | `_Built via [Qor-logic SDLC](url)._` once per `## [X.Y.Z]` header | `changelog_attribution_line()` | Per-version, not per-entry. Reader scans CHANGELOG version-by-version. |
| GitHub release notes | Once per release | `changelog_attribution_line()` | Same rationale as CHANGELOG. |

Locked by `tests/test_attribution_tiered_usage.py`. The Phase-49 enforcement boundary is expressed two ways for two surfaces: CHANGELOG sections key on version (`≥ 0.36.0`); seal-commit walks key on phase number (`≥ 49`) parsed from the commit subject. Same boundary, different artifact identifiers.

**Grandfathered seal commits (Phase 85, GH #96).** The phase 82 (`fb052e4`) and phase 83 (`ce138b2`) seal commits were authored locally with only the compact `Co-Authored-By:` line, missing the `Authored via [Qor-logic SDLC]` line. They predate the `/qor-substantiate` Step 9.5.4 seal-trailer guard. Rewriting published `main` history to backfill the line is rejected as disproportionate; the two phases are a disclosed exception in `tests/test_attribution_tiered_usage.py` (`_GRANDFATHERED_SEAL_PHASES`). From Phase 85 onward, Step 9.5.4 runs `qor.scripts.seal_trailer_check` after the seal commit and ABORTs substantiation if the full trailer is absent, so the omission cannot recur.
