# Behavioral Spec Corpus

Per-capability behavioral specs live here as `<capability>/spec.md`, in the
grammar defined by `qor/references/spec-grammar.md`.

- Lint a spec: `python -m qor.scripts.spec_lint --files <spec.md>`
- Fold a delta: `python -m qor.scripts.spec_merge --spec <spec.md> --delta <delta.md> --write`

Accretion rule: spec only what a plan touches. The corpus grows where change
happens; unaccreted legacy behavior is not a defect.

Phase A (GH #239) ships the tools without gate-chain authority; deltas fold
manually. Phase B wires plan-declared deltas, an audit grammar pre-pass, and
the fold inside the seal ceremony.
