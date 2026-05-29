# Research Brief: qor-compliance SKILL.md provenance (GH #151)

**Date**: 2026-05-29
**Analyst**: The Qor-logic Analyst
**Target**: GH #151 — whether `qor-compliance` is redundant (retire) or a value-add (fix F244/FX359 provenance); guarantee no duplicate coverage vs `qor-governance-compliance`.
**Scope**: Read-only investigation of the Qor-logic tree. No source mutated.

---

## Executive Summary

`qor-compliance` **does not exist in the Qor-logic repository** — not in `qor/skills/`, not in compiled variants (`qor/dist/`), and not in `qor/dist/manifest.json`. It is a **FailSafe-extension skill** (the archived `compliance` skill carries `license: Proprietary (FailSafe Project)`). Neither acceptance-criteria branch (a) retire nor (b) value-add-fix applies, because Qor-logic does not own the artifact. The #77 "out-of-scope" determination was legitimate and was already grep-verified at Phase 81. **Recommendation: Option (c) — close #151 as not-actionable-in-this-repo and redirect the F244/FX359 fix to the FailSafe skills bundle.**

## Findings

### F1 — `qor-compliance` is absent from Qor-logic source/dist/manifest
- `find qor -path '*compliance*' -name SKILL.md` returns only `qor-governance-compliance` (source + 3 dist variants). No `qor-compliance` directory exists.
- Repo-wide `grep -rln "qor-compliance"` (excluding build/dist/.git) hits only narrative/historical files: `CHANGELOG.md`, `docs/META_LEDGER.md`, `docs/plan-qor-phase81-skill-provenance-hotfix.md`, `docs/research-brief-half-measure-closures-2026-05-29.md`, and one stale gate artifact `.qor/gates/2026-05-15T0232-150a45/plan.json`. Never as a skill.
- `qor/dist/manifest.json`: `grep -c qor-compliance` = 0.

### F2 — Phase 81 already established external ownership with evidence
- `docs/plan-qor-phase81-skill-provenance-hotfix.md:7` (originating_remediation GH #77): "The other (`qor-compliance`) is NOT in Qor-logic -- no occurrence in `qor/skills/`, `qor/dist/`, or anywhere else in the tree -- so it must be from a different source (likely FailSafe's own skills bundle) and is out of scope for this repo."
- `:16` "No fix for `qor-compliance` (NOT in this repo; file separately against FailSafe upstream)."
- `:18` "F244/FX359 is the consumer-side schema, not a Qor-logic governance contract." The schema belongs to the FailSafe extension's release pipeline, not to Qor-logic.

### F3 — The "compliance" skill is FailSafe-proprietary
- `docs/archive/2026-04-15/ingest/.../\_quarantine/compliance/SKILL.md` frontmatter: `name: compliance`, `license: Proprietary (FailSafe Project)`, "Enforce FailSafe physical isolation and environment compliance constraints." This is the FailSafe-bundled skill that installs as `qor-compliance` downstream; it is quarantined/archived here, not a distributed Qor-logic skill. Corroborates the proprietary/out-of-scope classification recorded for the #80 reclassification.

### F4 — The in-scope half (`qor-governance-compliance`) is correctly fixed
- `qor/skills/governance/qor-governance-compliance/SKILL.md:6-8` declares nested `metadata.source.repository: https://github.com/MythologIQ-Labs-LLC/Qor-logic` + `path: qor/skills/governance/qor-governance-compliance`; `:12` `phase: governance`; `:10` `creator: MythologIQ Labs, LLC`.
- `tests/test_qor_governance_compliance_provenance.py` (F244/FX359 contract: nested source block + https repository + path) — **2 passed**. The F244/FX359 contract is satisfied for the one compliance skill Qor-logic actually owns.

### F5 — No intra-repo duplicate coverage (AC3)
- Within Qor-logic there is exactly one compliance skill (`qor-governance-compliance`). There is no second compliance skill to duplicate it. Any overlap between FailSafe's `qor-compliance` and `qor-governance-compliance` is a FailSafe-side concern, outside this repo's control.

## Blueprint Alignment

| #151 premise / AC | Actual finding | Status |
|---|---|---|
| "Determine whether qor-compliance still exists in source" | Absent from `qor/skills/`, `qor/dist/`, `manifest.json` | RESOLVED: does not exist here |
| AC (a) redundant → retire | Cannot retire — not owned by this repo | N/A (premise off) |
| AC (b) value-add → fix provenance here | Cannot fix here — F244/FX359 is FailSafe's consumer-side schema; skill is FailSafe's | N/A (premise off) |
| AC (3) no duplicate coverage | Only one compliance skill in-repo; no intra-repo duplication | MATCH |
| #77 "out-of-scope" call | Grep-verified legitimate (Phase 81) and reproduced 2026-05-29 | MATCH |

## Recommendations

1. **(High) Close #151 as Option (c): not actionable in Qor-logic.** `qor-compliance` is a FailSafe-extension skill; the F244/FX359 provenance fix must be filed against the FailSafe skills bundle, where the skill's source-of-truth frontmatter lives. The #77 partial-surface closure was correct, not a dodge.
2. **(Med) File/track the FailSafe-side provenance fix** in the FailSafe repo's tracker (nested `metadata.source.repository/path` + `phase` on FailSafe's `compliance` skill), and link it from #151 before closing, so the half-measure audit's "split the remainder into a tracked issue" counter-control (research-brief-half-measure-closures Rec 4) is satisfied.
3. **(Low) Add a one-line note to #77/#151** recording the grep-evidence (F1) so a future audit does not re-flag the same out-of-scope determination.

## Updated Knowledge

The half-measure audit flagged #77 as a "partial-surface closure" (one of two named targets fixed, the other declared out-of-scope). This research confirms the out-of-scope half was **correctly** scoped: `qor-compliance` is genuinely external (FailSafe-proprietary). #151 should resolve via redirection to FailSafe, not an in-repo retire/fix. (Memory: this mirrors the #80 reclassification — an out-of-scope proprietary prompt.)

---

_Research complete. Findings are advisory — the close/redirect decision remains with the operator. Note: the META_LEDGER RESEARCH entry and research gate artifact were intentionally held to avoid interleaving with the staged-but-uncommitted Phase 118 (#150) seal (Entry #311); they can be written once #150 is committed or research is run as its own session._
