# QoreLogic Skill Protocol Audit - 2026-03-29

## Purpose

This report records the first protocol-driven audit of the processed core skill set after marketplace review feedback.

## Directly Updated Skills

- `ql-debug.md`
  - aligned unsupported `ql-fixer` references to the supported `general` agent flow
- `ql-implement.md`
  - aligned audit-report input to `.agent/staging/AUDIT_REPORT.md`
- `ql-research.md`
  - moved durable research artifacts to `docs/`
  - removed the hard-coded `failsafe-bridge` memory file assumption
- `ql-substantiate.md`
  - aligned audit-report input to `.agent/staging/AUDIT_REPORT.md`
  - added first-release version fallback
  - replaced unbundled seal-script dependency with documented Merkle hash steps
  - changed commit/push semantics to staged-for-review
  - added `tests/` to staged artifacts
  - aligned skill-file integrity checks to packaged skill structure
- `ql-repo-release.md`
  - generalized release flow away from a single repo/helper layout
  - added fresh-branch rebase behavior for release/hotfix branches
  - aligned branch constraints with branch gate logic
- `ql-repo-scaffold.md`
  - narrowed template claims to bundled templates only

## Remaining Follow-Up Candidates

These are worth a later pass but were not changed automatically during this audit:

- Normalize references from `.claude/commands/references/...` to the processed reference contract where appropriate.
- Review `ql-bootstrap.md` for whether `.failsafe/governance/` is still an intentional core contract or should be consolidated further into `docs/` plus `.agent/staging/`.
- Review `ql-validate.md` helper-script references and decide whether they are core-repo requirements or should gain manual fallback wording.
- Review `ql-audit.md`, `ql-organize.md`, and `ql-refactor.md` reference paths for consistency with the processed skill source layout.

## Protocol Outcome

The current processed skill set is materially more consistent in:

- audit artifact handoff
- first-run behavior
- staged vs commit semantics
- project-agnostic release behavior
- memory and research artifact portability
- template-claim accuracy

This audit should be treated as the baseline for future skill reviews.
