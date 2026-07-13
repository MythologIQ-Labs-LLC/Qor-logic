# Spec-Delta Pre-Pass (Phase 192; GH #277)

Deterministic half (runs before the adversarial passes):

```bash
# for each entry in the plan artifact's spec_deltas
qor-logic scripts spec_lint --delta --files <delta_path> || VETO
```

Findings VETO with category `specification-drift`. Required next action:
Governor amends the delta document, re-runs `/qor-audit` (plan-text ground).

Judge half (prose duty, not mechanical): when the plan's Changes sections
alter CONTRACTED BEHAVIOR but the plan declares no `spec_deltas`, raise a
`specification-drift` finding -- exactly the drift class this gate exists
to catch: a contracted-behavior change carrying no declared delta. Scenario-intent-vs-implementation
correctness likewise stays a Judge judgment; the mechanical pass verifies
grammar and structure only (no fabricated verification).
