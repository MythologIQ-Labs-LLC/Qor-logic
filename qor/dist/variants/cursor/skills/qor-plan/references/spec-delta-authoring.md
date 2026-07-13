# Spec Delta Authoring (Phase 192; GH #277)

When a plan changes CONTRACTED BEHAVIOR (what the system promises, not how
it is built), author a spec delta alongside the plan:

1. Write `qor/specs/<capability>/deltas/<session-id>.md` in the delta
   grammar (`qor/references/spec-grammar.md`): ADDED/MODIFIED sections carry
   complete requirement blocks; REMOVED lists headings. MODIFIED restates
   the whole requirement -- that is what makes the fold deterministic.
2. Declare it in the plan gate artifact's `spec_deltas` array:
   `{capability, delta_path, ops[], evidence?}` -- `evidence` is a repo path
   proving the changed surface exists (feeds the seal-time coverage pillar).
3. If the capability has no spec yet, create `qor/specs/<capability>/spec.md`
   with the capability header (brownfield accretion: spec only what the plan
   touches).

Lifecycle: the delta is linted at `/qor-audit` (Step 0.7; failures VETO as
`specification-drift`), folded into the capability spec inside
`/qor-substantiate` after the reliability gates, and DELETED by the fold --
git history is the archive; the corpus is current truth.

Plans that change no contracted behavior declare nothing; the fold is a
no-op for delta-free sessions.
