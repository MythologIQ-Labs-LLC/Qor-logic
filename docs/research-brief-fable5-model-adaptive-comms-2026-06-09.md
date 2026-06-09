# Research Brief: Claude Fable 5 (Mythos class) and qor-logic model-adaptive communication

**Date**: 2026-06-09
**Analyst**: The Qor-logic Analyst
**Target**: Claude Fable 5 (external model release, 2026-06-09) and its impact on qor-logic's model-capability seam
**Scope**: verify the model exists (API-assumption-drift discipline), extract verified facts, locate the in-repo seam, and scope the deferred model-adaptive-communication feature.

---

## Executive Summary

Claude Fable 5 is **real**, released 2026-06-09 (the day of this brief), and verified against multiple independent sources (Anthropic, AWS, GitHub, CNBC). It introduces a **fourth model class, "Mythos"** (Haiku < Sonnet < Opus < Mythos); Fable 5 is the publicly-available, safeguarded Mythos-class model with API id `claude-fable-5`. Two facts make it directly relevant to qor-logic: (1) qor-logic's model-capability seam (`model_pinning_lint`) hard-codes a three-tier ladder and a regex that does **not** recognize `claude-fable-5`, so a Fable session is currently invisible to the tier lint (DRIFT); (2) Fable's safeguards **auto-route cybersecurity and biology requests to Opus 4.8** -- and qor-logic is security-heavy, so a declared-Fable session has a *different model* answering exactly its gate/security work. (2) is the decisive technical argument for the enforcement line already chosen by the operator: communication register may adapt, but ABORT/VETO gates and test-discipline must stay model-invariant.

## Findings (verified external facts)

### Fable 5 / Mythos class
- **Release**: 2026-06-09, alongside Claude Mythos 5. Source: Anthropic news <https://www.anthropic.com/news/claude-fable-5-mythos-5>; CNBC <https://www.cnbc.com/2026/06/09/anthropic-mythos-claude-fable-5.html>.
- **Class**: new fourth class "Mythos" above Haiku/Sonnet/Opus. Fable and Mythos names denote the safeguard tiering of the same underlying Mythos-class capability. Source: Anthropic, Tom's Hardware <https://www.tomshardware.com/tech-industry/artificial-intelligence/claude-fable-5-brings-mythos-to-the-masses-anthropics-next-frontier-model-is-state-of-the-art-on-nearly-all-tested-benchmarks>.
- **API id**: `claude-fable-5`. Source: Anthropic product page <https://www.anthropic.com/claude/fable>.
- **Capability**: built for long autonomous agent runs (days) in Claude Code / Managed Agents; plans, checks progress against a goal, refines; "thorough, proactive, and tests its own work." SWE-Bench Pro 80.3% vs Opus 4.8 69.2%. Source: Anthropic, AWS <https://aws.amazon.com/blogs/aws/anthropic-claude-fable-5-on-aws-mythos-class-capabilities-with-built-in-safeguards-now-available/>.
- **Selection / version**: `/model fable` in Claude Code; requires Claude Code v2.1.170+ (per operator-supplied release note; the product page did not restate the CLI version -- treat the exact floor as operator-sourced pending the Claude Code changelog).
- **Safety fallback**: requests flagged by Fable's classifiers -- "most often in cybersecurity and biology domains" -- auto-route to **Opus 4.8**; not charged at Fable rates. Source: Anthropic product page + Yellow.com <https://yellow.com/news/anthropic-fable-5-risky-queries>.
- **Data retention**: Fable 5 requires 30-day retention for safety monitoring; **not available under zero-data-retention** (the `/model` picker omits/disables it). Source: Anthropic product page + operator-supplied note.

### Best practices (verified design input, not yet encoded)
From the announcement + product page (corroborated): describe the **outcome, not the steps**, and set a goal to keep it working until the outcome holds; hand it **ambiguous problems** (root-cause, outage debugging, architecture); **skip verification reminders** (it self-verifies -- "tests its own work"); **size up larger tasks** it can hold across a long session.

## Blueprint Alignment (qor-logic seam)

The in-repo "blueprint" for model handling is `qor/scripts/model_pinning_lint.py` (+ AI-RMF MANAGE-3.1).

| Blueprint claim | Actual finding | Status |
|---|---|---|
| Capability tiers = haiku < sonnet < opus | `_CAPABILITY_ORDER = ("haiku","sonnet","opus")` (`model_pinning_lint.py:25`) -- no `mythos` | DRIFT |
| Model family -> tier via `claude-(haiku\|sonnet\|opus)-` | `_TIER_RE` (`model_pinning_lint.py:36`) does NOT match `claude-fable-5`; `extract_capability_tier` returns None -> Fable session is tier-invisible | DRIFT |
| min_model_capability lint warns when running model is too weak | A Fable session yields `current_tier=None`, so the comparison at `model_pinning_lint.py:86-87` is skipped -- no warn, no recognition | DRIFT (silent) |
| The running model answers the whole session | Cyber/biology turns auto-route to Opus 4.8; `QOR_MODEL_FAMILY=claude-fable-5` can mismatch the real responder on security gate work | DRIFT (semantic) |

## Recommendations (for the deferred Fable 5 adaptive-comms feature; NOT executed here)

1. **Extend the tier ladder + family map** (the one seam): add `"mythos"` to `_CAPABILITY_ORDER` (highest), and a family->tier map so `claude-fable-5` and `claude-mythos-5` resolve to `mythos`. Update `_TIER_RE` to match the fable/mythos family tokens. This alone closes the silent-invisibility DRIFT and is the minimal correct change (per qor-plan un-braid doctrine).
2. **Adaptive register keyed off the resolved tier** (operator decision: register + soft-nudge suppression): when resolved tier >= a configured threshold (mythos, optionally opus), skills render outcome-first prose and suppress WARN-only advisory nudges. Falls back to the explicit register otherwise and under ZDR (where Fable is unavailable).
3. **Hold the enforcement line -- now with a hard technical reason**: ABORT/VETO gates + test-discipline stay model-invariant. The security/biology auto-fallback means a declared-Fable session is answered by Opus 4.8 on exactly the security-critical turns; "the model self-verifies" therefore cannot be trusted to relax a gate. Conflating declared model with actual responder would be unsound.
4. **Treat `QOR_MODEL_FAMILY` as advisory, not authoritative** for any gate decision; it reflects the declared model, not the per-request responder. Do not gate enforcement on it.

## Updated Knowledge

Candidate Shadow Genome entry: **SG-DeclaredModelResponderSkew-A** -- under safeguarded model classes (Mythos/Fable), the declared session model is not necessarily the per-request responder (security/biology auto-fallback to Opus 4.8). Any model-adaptive logic must key *communication* off the declared model but must NOT key *enforcement* off it.

---

_Research complete. Findings are advisory; the model-adaptive-communication implementation remains deferred to its own governed cycle per the operator's sequencing._
