# Qor-logic — token-efficient defaults

Drop-in instructions for Claude Code (and similar harnesses). Keep responses terse and predictable.

## Output

- No sycophantic openers or closers ("Sure!", "Great question!", "I hope this helps!").
- Short prose sentences; code stays normal.
- No em-dashes, smart quotes, or non-ASCII chars in code/data.
- Result first; explanation only when asked.
- Do not restate the question.

## Read/write

- Read once; do not re-read unchanged files.
- Edit, do not rewrite whole files when a diff suffices.
- Skip files >100 KB unless explicitly required.
- Reference by path; do not paste large content inline.

## Investigation

- Use Glob/Grep to locate before Read.
- Delegate high-token research to subagents.

## Long sessions

- Suggest `/cost` on long sessions to monitor cache ratio.
- Suggest a fresh session on topic shift.
- Workflow bundles abort on budget breach; honor resume markers.

## Test discipline (mandatory)

- **Tests before code.** Write the failing test first; then make it green. No "I'll add a test after." Skipped TDD must be classified explicitly as "regression coverage backfill" with rationale.
- **Definition of done = green tests.** Code is not done until its tests pass. A skill, helper, or feature with no tests is not done; it is a draft.
- **Tests must be reliable.** No flakes, no hidden time/random/network coupling, no live-state hardcoding (e.g., asserting against a specific ledger entry's hash). Run new tests at least twice in a row to confirm determinism before claiming green.

## Authority

User instructions override this file. Full doctrines: `qor/references/doctrine-token-efficiency.md`, `qor/references/doctrine-test-discipline.md`. Bundle protocol: `qor/gates/workflow-bundles.md`. Skill handoff matrix: `qor/gates/delegation-table.md`.
