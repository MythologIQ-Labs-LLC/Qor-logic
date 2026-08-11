# Plan: governance-skill headroom recovery (Phase 215, Phase A of GH #285)

**change_class**: governance

**doc_tier**: standard

**terms_introduced**: none

**boundaries**:
- limitations: Relocation only. No sentence changes meaning, no gate is
  softened, no ABORT or VETO semantics move. The two skills behave identically
  after this phase; only where a reader finds the rationale changes.
- non_goals: No new reference files. No glossary edits. No continuity semantics
  (that is Phase B). No relocation of operative checklists, ABORT clauses, or
  any token a test asserts.
- exclusions: The other five lifecycle skills #285 touches have 15-32 KB of
  slack and are out of scope here.

## Open Questions

None.

## Locked Decisions

**LD-1 — The guardrail tests are the specification, and the enumerated list is
a lower bound.**

Ledger entry #432 (Phase 178) ran this same pass on these same two files and
records that its implementer "discovered and honored MORE token locks than the
plan enumerated" -- a literal `|| true` required inside Step 4.6.8 prose,
`option_b_required` / `Option B` tokens, and hash-integrity helper names.

Static analysis here found 49 asserted strings per skill across 49 guardrail
test files. **That is a lower bound.** Any sentence a test asserts stays
inline, including sentences that read as pure rationale. Discovery during
implementation is expected, not a plan defect; the response to a newly found
lock is to leave that sentence inline and record it, never to weaken the test.

**LD-2 — Unpinned is not the same as safe to move.**

The largest unpinned sections are operative, not explanatory:
`Test Functionality Audit` (2,370 B), `Security Audit` (1,192 B),
`OWASP Top 10 Pass` (935 B), `Ghost UI Audit` (886 B) in the audit skill;
`Test Audit`, `Step 2.5: Version Validation`, `Step 9.6: Push/Merge Options` in
the seal skill. These are executed, not read for background. Relocating them
would trade a size problem for a usability one. Only rationale and worked
detail move; the operative instruction stays with a pointer.

**LD-3 — Append to already-cited references; create none.**

`git show HEAD:qor/scripts/doc_integrity.py | grep -nE 'referenced_by|Orphan concept' -> 48: referenced_by: list[str] = field(default_factory=list) | 109: if e.referenced_by: | 114: f"Orphan concept: {e.term!r} has no referenced_by and was not "`

`doc_integrity` tracks `referenced_by` per glossary term and raises on orphan
concepts; the glossary carries 119
`referenced_by` entries, 104 naming skills or reference files. A new reference
file pulls this phase onto that surface for no benefit. Phase 178 appended to
`adversarial-mode.md`, `phase37-subpasses.md`, and `seal-gate-ladder.md` and
touched no glossary entry. Same approach here means zero glossary risk.

**LD-4 — Target roughly 1.5 KB per skill, not the 520/360 minimum.**

Phase 178 landed the files at 39,355 and 39,321 bytes. They are now 39,416 and
39,576 -- drift of +61 and +255, with Phases 213 and 214 each adding inline
prose. Recovering only what Phase B strictly needs would return both files to
the ceiling within a few phases. Phase 178's ~1.5 KB per skill bought roughly a
year of edits.

This target is uniform only where the supply of movable prose allows it. LD-5
records where it does not.

**LD-5 — `qor-substantiate` has a lower ceiling than `qor-audit`, and the
target follows the supply rather than the reverse.**

Measured during Phase 1 rather than assumed: `qor-substantiate` carries 2,786
bytes of unpinned prose, of which roughly 1,567 bytes is operative -- ABORT
clauses, escape idioms, and operator actions that LD-2 forbids moving. That
leaves roughly 1,219 bytes genuinely explanatory against the 1,176 bytes a
38,400-byte target demands. A 43-byte margin over a heuristic classification is
not a margin.

The hazard is specific and directional: a numeric target reachable only by
moving essentially all available explanatory prose creates pressure to
reclassify an operative sentence as rationale in order to make the number. The
size budget exists to protect the skill's readability; a target that induces
relocation of seal steps inverts it.

`qor-audit` is not similarly constrained -- 5,512 bytes of unpinned prose
against 1,016 bytes needed -- so it keeps the LD-4 target. `qor-substantiate`
takes a target with real margin instead, and the shortfall is recorded rather
than closed by force. That file was disclosed heavily in Phase 178; the
remaining density is that pass succeeding, not this one failing.

## Phase 1: Prove the headroom is absent before claiming it was recovered

### Unit Tests

- `tests/test_substantiate_staging_gates.py::test_governance_skills_keep_headroom` -
  the existing parametrized lock. Run it against a temporary target of 38,400
  bytes to confirm it goes RED for both skills at current size, exactly as
  Phase 178 did before relocating. This establishes the pass actually moved
  something rather than asserting a bound already satisfied.

### Affected Files

None. This is a verification step whose output is evidence, not a change.

### Changes

None. Recording the red measurement is the deliverable.

## Phase 2: Relocate rationale

### Affected Files

- `qor/skills/governance/qor-audit/SKILL.md` - rationale subsections moved out,
  inline pointers left behind.
- `qor/skills/governance/qor-audit/references/adversarial-mode.md` and
  `references/phase37-subpasses.md` - receive appended titled subsections.
- `qor/skills/governance/qor-substantiate/SKILL.md` - same treatment.
- `qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md` and
  `references/release-and-tag-timing.md` - receive appended titled subsections.

### Changes

Per moved block: append a titled subsection to the already-cited reference,
replace the inline prose with a one-line pointer naming that subsection, and
where the prose already exists verbatim in the reference, compress to a pointer
without appending a duplicate.

Every candidate is checked against the guardrail set before moving. A block
containing an asserted token is not moved, regardless of how explanatory it
reads.

## Phase 3: Verify at four widths

### Unit Tests

- The focused guardrail suite: every test file that references either
  `SKILL.md`, run as one selection.
- A skill-referencing sweep: every test that reads any skill file, catching
  cross-skill assertions the focused suite misses.
- The full suite.
- `qor-logic scripts dist_compile` with a zero-drift check, since the variants
  embed skill bodies.

### Affected Files

None beyond Phase 2.

### Changes

None. Phase 178's verification shape is reused because a focused suite alone
did not catch dist drift there.

## Definition of Done

### Deliverable: recovered headroom

- **D1**: Both governance skills have room for Phase B's additions without a
  further disclosure pass.
- **D2**: `qor-audit` lands at or below 38,400 bytes LF-normalized, recovering
  ~1 KB or more. `qor-substantiate` lands at or below 38,876 bytes
  LF-normalized, recovering at least 700 bytes -- the reduced target LD-5
  establishes, which still clears Phase B's 360-byte requirement by roughly 2x
  while leaving margin against the operative/explanatory boundary.
- **D3**: Seal entry records the before and after sizes, the blocks moved,
  their destination subsections, any token lock discovered during
  implementation that the plan did not enumerate, and the LD-5 measurement --
  including that `qor-substantiate` cannot reach 38,400 bytes without moving
  operative prose, so a future pass on that file needs a structural remedy
  rather than another relocation round.
- **D4**: The headroom test is shown RED at a 38,400-byte target before the
  pass for both skills, and GREEN after at each skill's LD-5 target (38,400 for
  `qor-audit`, 38,876 for `qor-substantiate`); the four verification widths in
  Phase 3 all pass.

### Deliverable: behavior unchanged

- **D1**: The two skills instruct identically; only the location of rationale
  changes.
- **D2**: No operative checklist, ABORT clause, VETO semantic, or asserted
  token is relocated.
- **D3**: Seal entry states that no gate was softened and names the
  guardrail-is-specification rule as the constraint that kept it so.
- **D4**: The full guardrail suite passes unchanged -- no test is edited,
  weakened, or skipped as part of this pass. A test edit would invalidate the
  evidence, since the tests are the specification being preserved.

## Feature Inventory Touches

None. This plan touches `qor/skills/governance/**` only; it introduces no
user-touchable feature and modifies no FEATURE_INDEX row.

## CI Commands

- `python -m pytest tests/test_substantiate_staging_gates.py -q` — the headroom lock.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `qor-logic scripts skill_size_budget_lint --skills-root qor/skills` — both skills clear of EXCEEDED proximity.
- `qor-logic scripts dist_compile` — variants rebuilt with zero drift.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase215-governance-skill-headroom.md` — this plan asserts each path and command identically at every site.
