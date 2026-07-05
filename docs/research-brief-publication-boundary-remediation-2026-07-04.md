# Research Brief: Publication-Boundary Retroactive Remediation

**Date**: 2026-07-04
**Analyst**: The Qor-logic Analyst
**Target**: Retroactive current-tree remediation per `qor/references/doctrine-publication-boundary.md` (mandated follow-on to the policy baseline)
**Scope**: mechanical violation inventory (by class and count), hash-binding constraints, Governor decisions, remediation conventions

---

## Executive Summary

A mechanical sweep of tracked surfaces against the new doctrine found roughly 237 violation instances: ~87 in prose documents (research briefs, plans, CHANGELOG, SYSTEM_STATE, two reference doctrines, a skill reference file), ~51 inside sealed META_LEDGER entry bodies (23 entries), 7 committed gate-artifact sessions whose research payloads cite external workspace paths (each provenance-sidecar-bound), 7 tracked intent-lock records carrying absolute local paths, plus generated dist copies that inherit from canonical sources. The classes of reference: names of sibling governance repositories consulted as design exemplars, an external QA exemplar workspace, an external agent-governance toolkit used as a pattern source, absolute local workspace paths, and one cross-repository issue pointer. Critically, ledger BODY edits do NOT break chain verification (chain math consumes the recorded hash fields, which stay untouched; the plan-file binding is re-verified by CI only for the latest seal), so tip-of-tree scrubbing is mechanically safe; the collision is doctrinal (forward-only sealed entries) and is resolved by the Governor's recorded decision below.

## Findings

1. **Class B (prose docs, ~87)**: two of today's research briefs and one plan carry external names/paths throughout; the perspective-reset brief is the densest single file; CHANGELOG phase entries, SYSTEM_STATE phase summaries, the shadow-genome countermeasure doctrine's incident narratives, one seal-ladder reference file, CONCEPT, BACKLOG, and operations each carry a handful. All freely editable.
2. **Class C (ledger bodies, 23 entries / ~51 refs)**: incident narratives and research-decision summaries name external repositories. `ledger_hash verify` computes `chain = f(recorded_content_hash, recorded_previous_hash)` -- body prose is not hashed -- and `seal_entry_check --auto` re-verifies the plan binding for the LATEST entry only. Body edits therefore keep every gate green.
3. **Class D (gate artifacts, 7 sessions)**: research payloads' `sources`/`citations` fields name external paths; each artifact is bound by a keyless `payload_sha256` sidecar (CI `verify-committed`). Editing requires regenerating the sidecar digest; HMAC tags are session-scoped and not CI-verified keylessly.
4. **Class F (intent-lock, 7 tracked)**: absolute local paths; the capture code writes absolute paths by construction, so the code seam must move to repo-relative or the class regrows.
5. **Published GitHub surfaces**: today's issue bodies/comments and PR bodies name external repositories and local paths; older items need inventory.
6. **Lint constraint**: a tracked mechanical lint cannot itself carry the external names (a denylist of private identifiers in a public repo would violate the boundary it enforces). The tracked lint must use structural patterns (non-repo absolute path shapes; non-self GitHub URLs) plus an optional operator-local, gitignored terms file.

## Governor Decisions (recorded 2026-07-04)

- **Sealed surfaces**: scrub in place + one disclosure entry. Entry bodies and hash-bound docs are anonymized at tip; recorded hash fields stay untouched (they attest pre-remediation bytes, retrievable in git history since history rewrite requires separate authorization); one REMEDIATION ledger entry discloses the scope.
- **GitHub surfaces**: sweep all OPEN issues plus every item created today (issues, PR bodies, comments); closed/historical items are inventoried into a recorded follow-on worklist.

## Recommendations (remediation conventions)

1. Neutral substitutions: `a sibling governance repository` / `sibling repositories` (estate), `an external QA exemplar` (the external QA workspace), `an external agent-governance toolkit` (the pattern-source toolkit), `an external workspace path` or deletion (absolute paths), `an external repository's issue` (cross-repo pointers). Distinct-actor cases use synthetic labels (`External Repo A/B`). Qor-logic self-references (own org/repo URLs, own issues `#N`) are permitted and untouched.
2. Preserve legally required attribution TEXT minus repository-location detail; preserve behavior everywhere (code changes limited to docstrings/comments plus the intent-lock relative-path seam).
3. Gate artifacts: anonymize payload strings, regenerate each `.provenance` sidecar's `payload_sha256`; disclose in the REMEDIATION entry.
4. New `publication_boundary_lint` (tracked, structural patterns + optional gitignored local terms file), wired WARN-only into the audit Step 0.6 ladder after the tree is clean; TDD.
5. Dist regenerated from canonical sources after source scrubbing; no direct dist edits.
6. No Lessons-Learned records this phase: after anonymization nothing requires identifying context, and relocating prose to evade the rule is prohibited.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
