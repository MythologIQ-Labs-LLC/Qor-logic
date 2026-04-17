# Doctrine: Audit Report Language

> Each VETO ground names its correct next skill. The generic "Mandated
> Remediation" header is replaced by a per-ground `**Required next action:**`
> line. Operators never have to guess which skill to invoke.

## Ground-class -> skill directive mapping

This mapping is the canonical ground-class-to-skill contract for AUDIT_REPORT
authoring. Upstream authority for all cross-skill handoffs is
`qor/gates/delegation-table.md`; this file narrows that catalog to the subset
that shows up in audit VETOs.

| Ground class | Required next action |
|---|---|
| **Section 4 Razor** (function >40 lines, file >250 lines, nesting >3, nested ternaries) | `/qor-refactor` |
| **Orphan file / Macro-arch breach** (cyclic deps, mixed domains, layering reversal, orphan files) | `/qor-organize` |
| **Plan-text** (A08 safe-load commit, dependency audit, missing tests, ghost-feature declaration, wording) | Governor: amend plan text, re-run `/qor-audit` |
| **Process-level** (repeated VETO pattern, SG severity-sum threshold, capability-shortfall cascade) | `/qor-remediate` |
| **Code-logic defect** (regression, hallucination, behavioral break detected during audit) | `/qor-debug` |

## Template contract

Every `.agent/staging/AUDIT_REPORT.md` produced by `/qor-audit` MUST:

1. Contain a section per VETO ground class it flags, with the exact header
   text listed in the mapping above.
2. Close each ground-class section with a single `**Required next action:**`
   line naming the correct skill (or the literal string "Governor" for
   plan-text grounds).
3. Include a `## Process Pattern Advisory` section carrying the marker
   `<!-- qor:veto-pattern-advisory -->`. When the repeated-VETO pattern
   detector (`qor/scripts/veto_pattern.py`) fires, the section is populated
   with the recommendation to run `/qor-remediate`. When it does not fire,
   the section reads `No repeated-VETO pattern detected in the last N sealed
   phases.`

Enforcement:

- `tests/test_audit_template_slots.py` lints `qor/skills/governance/qor-audit/references/qor-audit-templates.md`.
- `tests/test_audit_language_doctrine.py` cross-checks this doctrine file.

## Repeated-VETO pattern

The detector in `qor/scripts/veto_pattern.py` parses the Meta Ledger and
fires when the last **2** consecutive sealed phases each required more than
one `/qor-audit` pass. When fired, the pattern emits a Shadow Genome event:

- `event_type: repeated_veto_pattern`
- `severity: 3`
- `details`: `{recent_phases: [...], max_pass_count: N}`
- **Remediation recommendation**: invoke `/qor-remediate`.

The pattern advisory is **non-blocking**. It never itself constitutes a new
VETO ground. Current-audit VETO grounds stand on their own merits; the
advisory is a process-level observation that Governor and operator can act
on independently.

Emission is handled by `maybe_emit_pattern_event` in the same module; the
`/qor-audit` skill invokes `check()` during Step 3 and populates the
advisory section from the returned `PatternResult`.

## Rationale

"Mandated Remediation" as a header pattern is ambiguous: operators read it
and naturally reach for `/qor-remediate`, but that skill is for process-level
failures only. Most audit VETOs have code-shape or plan-text causes whose
correct remediation is a different skill or a Governor edit. Naming the
skill explicitly per ground eliminates the ambiguity at the point of
decision.

## Upstream

Per `qor/gates/delegation-table.md` (single source of truth for cross-skill
handoffs), the delegation rows that feed this doctrine are:

- `qor-audit` Section 4 Razor violation -> `/qor-refactor`
- `qor-audit` Orphan / Macro-arch breach -> `/qor-organize`
- any phase Process Shadow Genome threshold -> `/qor-remediate`
- `qor-debug` Root cause is code defect -> `/qor-implement` or `/qor-refactor`

Plan-text grounds are not in the delegation table because the correct actor
is the Governor (not a skill). The doctrine flags this explicitly to
prevent future skill-selection ambiguity.
