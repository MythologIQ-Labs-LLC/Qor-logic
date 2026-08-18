# Plan: A claimed count is a citation and gets checked like one

**iteration**: 2

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: V1 covers the two observed forms only. A wrong count paired with a matching wrong enumeration passes Form B (that failure mode requires an independent sweep no static lint replaces -- the audit's job). Number words beyond twenty and counts split across sentences are out of grammar.
- non_goals: No hard VETO (the Step 0.6 ladder is WARN-only by the SG-PreAuditLintGap-A convention; the binding passes remain Step 3). No NLP; a fixed number-word table.
- exclusions: GH #351, GH #352, GH #320, GH #286.

## Iteration 2 disposition of the iteration-1 VETO (F1, F2)

The iteration-1 grammar was tuned to simplified fixtures and the reviewer's prototype proved it wrong on both sides. Iteration 2 closes both with three changes: (1) Form B counts the repo's shorthand citation continuations (a `:NNN` token following a full citation in the same enumeration) and is scoped to Locked-Decision regions via the shipped `_ld_blocks` -- which makes the sealed Phase 230 LD-3 derive twelve (six full plus six continuations, matching its claim), drops the non-LD disposition paragraph out of scope entirely, and FIRES on the historical iteration-1 LD (claimed eight against a one-citation paragraph); (2) Form A's trigger is a count-plus-`tests` claim co-occurring with a `tests/...py` path and a commit-ish token (7-40 hex or a `v`-tag) -- `git show` is the resolver, not the trigger, so the historical bare-`bd63317` shape fires; (3) adjacency admits up to two intervening modifier tokens ("behavioral", "enumerated", "two-unpack"), and both fixtures are verbatim transcriptions of the recoverable texts.

## Open Questions

None. Both fixtures are now verbatim from the texts the iteration-1 audits of Phases 226 and 230 read and vetoed.

## Locked Decisions

**LD-1: The lint joins the ladder immediately after the presence-test lint, one line, WARN-only.**

```
git show v0.152.0:qor/skills/governance/qor-audit/SKILL.md | grep -nE 'plan_test_lint --plan' -> 157:qor-logic scripts plan_test_lint --plan "$PLAN_PATH" || true
```

The new line follows the same `|| true` WARN-only form.

**LD-2: Form B reuses the shipped citation regex rather than growing a second one.**

```
git show v0.152.0:qor/scripts/plan_evidence.py | grep -nE '^_FILE_LINE_RE' -> 29:_FILE_LINE_RE = re.compile(r"\b[\w./-]+\.(?:" + _PATH_EXT + r"):\d+\b")
```

**LD-3: The grammar is two detectors.** Form A (any paragraph): a count within two tokens of the noun `tests`, co-occurring with a `tests/[\w/]+\.py` path and a commit-ish token (7-40 lowercase hex, or `v`-prefixed dotted tag) -- the lint resolves `git show <token>:<path>` and counts lines matching `^def test_`; an unresolvable token is skipped as unverifiable. Form B (Locked-Decision regions only, per LD-5): a count within two tokens of `call sites`, `sites`, or `unpack sites` -- the lint counts distinct `_FILE_LINE_RE` citations in the claim's paragraph PLUS shorthand continuations (a `:\d+` token following a full citation in the same enumeration, the repo's `` `:237`, `:262` `` convention) and compares when the derived count is nonzero (an enumeration-free claim is unverifiable and skipped, not guessed). Counts parse from digits or the words one through twenty.

**LD-5: Form B's scope is the shipped Locked-Decision region parser, not a new one.**

```
git show v0.152.0:qor/scripts/plan_evidence.py | grep -nE '^def _ld_blocks' -> 126:def _ld_blocks(text: str) -> list[tuple[int, str]]:
```

Scoping to LD regions is what makes the sealed corpus genuinely clean: the Phase 230 disposition paragraph ("TWELVE two-unpack sites -- the eight previously counted plus ...", a deliberately partial enumeration) sits outside every LD region and is never examined, while the same plan's LD-3 derives twelve and matches. Partial enumerations outside LD regions are legitimate prose; completeness claims inside LD regions are contracts.

**LD-4: Findings are WARN lines naming the paragraph's first line number, the claimed count, and the derived count**; exit is 0 with findings (ladder contract), 1 reserved for a future enforce flag, matching the sibling lints' posture.

## Phase 1: Bind both historical failures (tests first)

### Affected Files

- `tests/test_plan_enumeration_lint.py` - NEW.

### Unit Tests

- `test_form_a_catches_the_phase_226_shape` - a tmp git repo commits a test file with 4 `def test_` functions at a known short hash; the plan paragraph is the verbatim historical shape (`- \`tests/test_x.py\` - NEW; cherry-pick of \`<hash>\` (10 behavioral tests: ...)` -- bare commit token, NO git show string); the lint reports claimed 10 / derived 4.
- `test_form_a_passes_a_true_count` - the same fixture claiming `4 behavioral tests` yields no finding (modifier-tolerant adjacency exercised on the passing side).
- `test_form_b_catches_the_historical_ld_shape` - an LD-region paragraph with the verbatim modifier phrase `all eight enumerated call sites` beside a single full citation; the lint reports claimed 8 / derived 1.
- `test_form_b_counts_shorthand_continuations` - an LD-region paragraph claiming `ALL TWELVE call sites` enumerating six full citations and six `:NNN` continuations (the sealed Phase 230 LD-3 shape) yields no finding -- derived twelve.
- `test_form_b_ignores_non_ld_paragraphs` - the partial-enumeration disposition shape (`TWELVE two-unpack sites -- the eight previously counted plus` two citations) outside any LD heading yields no finding.
- `test_form_b_skips_enumeration_free_claims` - `all eight call sites` in an LD region with zero citations yields no finding (unverifiable is not wrong).
- `test_non_inventory_numerics_do_not_trigger` - a paragraph with `40 diff lines` and `the 250 ceiling` and no inventory noun yields no finding.
- `test_number_words_parse` - `twelve unpack sites` in an LD region against eleven full citations reports claimed 12 / derived 11.

All red at v0.152.0 (module absent; ImportError at collection).

## Phase 2: The lint and the ladder line

### Affected Files

- `qor/scripts/plan_enumeration_lint.py` - NEW; the LD-3 detectors under LD-5 scoping, LD-4 reporting, argparse `main` (`--plan`, `--repo-root`); imports `_FILE_LINE_RE` and `_ld_blocks` from `plan_evidence`.
- `qor/skills/governance/qor-audit/SKILL.md` - one ladder line after the LD-1 anchor: `qor-logic scripts plan_enumeration_lint --plan "$PLAN_PATH" --repo-root . || true` (~70 bytes against 1,273 headroom).

### Changes

Phase 1's eight tests go green; the ladder's sibling lint invocations and every existing qor-audit wiring test stay green (additive line).

### Unit Tests

- Phase 1's eight tests observed red-then-green.
- `python -m qor.scripts.plan_enumeration_lint --plan <each of the last three sealed plans> --repo-root .` observed clean (no false positives over shipped plans) in the substantiate sweep.

## Feature Inventory Touches

None. Governance tooling, one ladder line, tests.

## Definition of Done

### Deliverable 1: The two observed failure forms are machine-caught

- **D1**: A plan repeating either historical failure warns before the audit cycle is spent.
- **D2**: `plan_enumeration_lint.py` with the two LD-3 detectors under LD-5 scoping.
- **D3**: Implement-phase ledger entry cites this plan; seal binds this plan file.
- **D4**: `test_form_a_catches_the_phase_226_shape` and `test_form_b_catches_the_historical_ld_shape` observed red at v0.152.0 and green after Phase 2.

### Deliverable 2: No over-flag

- **D1**: Non-inventory numerics and enumeration-free claims never warn.
- **D2**: inventory-noun anchoring plus the nonzero-enumeration guard.
- **D4**: `test_non_inventory_numerics_do_not_trigger` and `test_form_b_skips_enumeration_free_claims` green; the three-sealed-plans sweep observed clean.

## CI Commands

- `python -m pytest tests/ -q` -- full suite.
- `qor-logic-plus scripts plan_text_consistency_lint --check docs/plan-qor-phase232-enumeration-lint.md` -- plan-internal consistency.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase232-enumeration-lint.md --repo-root .` -- citation truth check.
