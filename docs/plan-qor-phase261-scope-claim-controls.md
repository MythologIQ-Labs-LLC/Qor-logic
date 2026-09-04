# Plan: Scope-claim controls

**change_class**: feature

**doc_tier**: standard

**iteration**: 7 (amends iteration 1 per the VETO at META_LEDGER entry #731, findings J-1 through J-7, plus three design amendments derived by testing the detector against its own motivating data)

**originating_remediation**: `.qor/gates/2026-09-04T1551-477d51/remediate.json` (Phase 258 attempt-cap remediation; META_LEDGER entry #730)

**terms_introduced**:
- term: scope overgeneralization
  home: qor/references/doctrine-shadow-genome-countermeasures.md

**boundaries**:
- limitations:
  - The lint reads plan Markdown only. It cannot tell whether an absolute claim is true, only whether the plan pairs it with evidence or a scope qualifier. A false claim carrying a grep-evidence statement passes.
  - Detection is lexical. A claim phrased without any listed quantifier is invisible to it.
  - WARN-only in V1, matching how `skill_size_budget_lint` and `procedural_fidelity` shipped. A fail-closed flip is a later decision, taken on observed false-positive rate rather than now.
- non_goals:
  - Judging the truth of any claim.
  - Any change to `/qor-audit`'s verdict rules or to the existing pre-audit lints.
- exclusions:
  - The three Phase 258 plan-text corrections named in META_LEDGER entry #730. They belong to that phase's next cycle, not this one.
  - Capture-time tree state and declared-versus-actual scope fidelity (GH #434). Answered on the boundary, deferred on the build, and explicitly sequenced behind this phase.
  - GH #436's auditor-amendment clauses. Filed, not built here.
  - A corpus-granularity finding kind, which would flag a directory- or tree-scope claim backed only by single-file evidence. Deferred with cause: `plan_evidence._EVIDENCE_STMT_RE` captures ref, path, line and observed text and not the grep flags, so the narrowed-search case it targets is structurally invisible to a detector reusing that parser. Reaching it needs scope captured at statement level, which is a parser change rather than a pairing rule. It also misfires on correct citations, which is why three audits could not state a rule separating it from sound reasoning.

## Scoping

Phase 258 reached its five-attempt cap on one recurring class: a measurement taken at one width, and a sentence written from it asserting a wider one. Sixteen instances across five audits, two of them written inside corrections of earlier instances, one of which escaped the repository as a GitHub issue filed against live code and since closed as an error.

The remediation proposal identified why nothing caught it. Three narrative Shadow Genome entries written during that session did not prevent instances six through sixteen, so narrative capture is not a control. And no mechanism could see the recurrence: the five verdicts carried different category sets, so the escalator never fired.

This phase builds the two mechanical halves and the doctrine that names them. It deliberately does not touch Phase 258's plan.

## Open Questions

None.

## Phase 1: The absolute-claim lint

### Affected Files

- `tests/test_plan_absolute_claim_lint.py` NEW - detector behavior over fixture plans
- `qor/scripts/plan_absolute_claim_lint.py` NEW - the lint

### Locked Decisions

**LD-1. The lint reuses the existing evidence parser rather than adding a second one.** `plan_evidence.parse_evidence_statements` already parses grep-evidence statements and `plan_grep_lint` already keys findings by `(path, line)`.

- `git show 9bb10b61:qor/scripts/plan_evidence.py | grep -nE '_EVIDENCE_STMT_RE'` -> `45:_EVIDENCE_STMT_RE = re.compile(`
- `git show 9bb10b61:qor/scripts/plan_grep_lint.py | grep -nE 'statement'` -> `182:        for (path, line), stmt in statements.items():`

**LD-2. Scope is Locked-Decision regions, but pairing is per-decision, not per-region.** `plan_evidence._ld_blocks` isolates the right region and the lint reuses it to find candidates:

- `git show 9bb10b61:qor/scripts/plan_evidence.py | grep -nE 'def _ld_blocks'` -> `126:def _ld_blocks(text: str) -> list[tuple[int, str]]:`
- `git show 9bb10b61:qor/scripts/plan_evidence.py | grep -nE '_ANY_HEADING_RE.match'` -> `136:            while j < len(lines) and not _ANY_HEADING_RE.match(lines[j]):`

That helper returns one block per `### Locked Decisions` heading, running to the next heading and so spanning every decision under it. Pairing evidence at that granularity is useless: one statement anywhere in a section would satisfy every marker sentence in it, and the lint could not fire on any conventionally structured plan, including this one. The lint therefore subdivides each region at `**LD-` boundaries and pairs within the sub-block. `scan_block` owns that subdivision.

**LD-3. Two detectable shapes, one closed marker set, and a measured coverage figure.**

`ABSOLUTE_MARKERS = ("no ", "none", "nothing", "never", "always", "only", "single", "sole", "every other", "zero", "exactly")`. A sentence in an LD sub-block containing any marker must carry either a grep-evidence statement in that sub-block or an inline scope qualifier matching `SCOPE_QUALIFIER_RE`, which recognizes a stated corpus: `in <path-or-glob>`, `under <path>`, `outside <path>`, `in-scope`, `over the whole <path>`, `at <ref>`.

`CARDINAL_CLAIM_RE` covers the shape markers structurally cannot see: a bare count of repository objects, a number or number-word **immediately** followed by a noun from a closed set, with no intervening token.

Adjacency is load-bearing and is pinned by a declared negative test rather than left to the implementer. A regex tolerating intervening words is the natural choice, because the shapes this lint targets read like "two exact-set enum assertions" and "sixteen instances across five audits". Such a regex also matches "returning 1 on findings" in LD-5 of this plan, which is ordinary prose about a return value and not a count of anything. Without the constraint the self-application test goes red, and the cheapest way to green it at implement time is rewording LD-5 rather than tightening the regex -- a plan edit that would silently widen the detector past what was audited. `CARDINAL_NOUNS = ("files", "tests", "entries", "assertions", "occurrences", "values", "lines", "modules", "skills", "findings", "consumers", "callers")`. Closed, not illustrative: an open list would make the self-application test unstable, since adding a noun could turn it red without any plan text changing. A counting sentence owes the same evidence or qualifier a marker sentence does.

**Backticked spans are removed entirely, content included, before matching.** A marker word inside a code span -- including the `ABSOLUTE_MARKERS` literal above -- is not a claim and must not be a finding.

This deliberately differs from the parser the lint otherwise reuses, and the difference is stated because it would otherwise be assumed:

- `git show 9bb10b61:qor/scripts/plan_evidence.py | grep -nE 'Backticks are removed'` -> `72:    Backticks are removed first: they are markdown span delimiters, not`

That parser strips the delimiters and keeps the span text, which is right for reading an evidence statement out of a styled line and wrong here: it would leave every marker word inside a code span visible to the matcher. `scan_block` therefore applies `re.sub(r"`[^`]*`", " ", line)` before matching, which is span removal rather than delimiter removal.

**Coverage, measured rather than claimed.** Against a ten-sentence sample of the real instances this phase exists to prevent, marker detection alone fires on 7. The three misses were a confidence adjective carrying no quantifier, the word `single` (now in the set), and a bare cardinal (now covered by `CARDINAL_CLAIM_RE`). The residual is the first: "is a reliable predicate" states nothing countable, and widening to adjectives would flag ordinary prose. That case stays uncovered and is declared in Boundaries rather than papered over. An earlier revision of the remediation proposal asserted a coverage figure without counting; correcting it after measurement is what produced `CARDINAL_CLAIM_RE`.

**LD-4. Helper names avoid validator prefixes, and this is load-bearing.** `qor/scripts/` is scanned by a composition lint with an empty allowlist, so a validator-shaped helper name plus a guard loop turns a test red.

- `git show 9bb10b61:qor/scripts/pipeline_inversion_lint.py | grep -nE '_VALIDATOR_NAME'` -> `30:_VALIDATOR_NAME = re.compile(r"^(validate|check|verify|is_valid)", re.IGNORECASE)`
- `git show 9bb10b61:tests/test_phase49_self_application.py | grep -nE '_KNOWN_BENIGN'` -> `18:_KNOWN_BENIGN_FUNCTIONS: frozenset[str] = frozenset()`

Public names are therefore `find_findings`, `scan_block`, `main`, `_emit`. None begins with `validate`, `check`, `verify`, or `is_valid`. Phase 258 discovered this constraint only at its final audit; it is stated up front here.

**LD-5. Finding shape and CLI mirror the existing pre-audit lints.** A frozen `ClaimFinding(kind, line, reason)`, `main(argv) -> int` with `--plan` and `--repo-root`, `_emit` returning 1 on findings, and a module-foot `if __name__ == "__main__": raise SystemExit(main())`.

### Changes

Two finding kinds, each with one rule.

`absolute-claim-unevidenced`: a marker sentence in an LD sub-block carrying neither a grep-evidence statement in that sub-block nor an inline scope qualifier.

`absolute-claim-uncounted`: the same, for a sentence matching `CARDINAL_CLAIM_RE`.

Both fire on an *absence* -- a claim with nothing behind it -- which is decidable from the text alone and does not require judging whether existing evidence is good enough.

**A third kind was specified in iterations 1 through 3 and is dropped.** It would have flagged a corpus-scope claim whose paired evidence cites only individual files, aimed at the case where a `--include=*.py` grep backed a claim about all of `qor/`. Two things killed it, and both are recorded in Boundaries rather than left implicit. It cannot reach its motivating case: `plan_evidence._EVIDENCE_STMT_RE` captures ref, path, line and observed text and not the grep flags, so a narrowed search is invisible to any detector reusing that parser. And it misfires on correct work: LD-4 of this plan claims a property of `qor/scripts/` and cites the single file that implements it, which is the normal and right shape of a citation, yet is indistinguishable from the defect without a rule nothing could state. Three audits failed to find that rule.

### Unit Tests

- `test_marker_sentence_without_evidence_or_qualifier_is_reported` - an LD block asserting "nothing in qor/ writes it" with no statement yields one `absolute-claim-unevidenced` naming the line.
- `test_marker_sentence_with_paired_evidence_passes` - the same sentence with a grep-evidence statement in the block yields zero findings.
- `test_marker_sentence_with_inline_scope_qualifier_passes` - "no `.py` file under `qor/` mentions it" yields zero findings without any statement, because the sentence states its own corpus.
- `test_corpus_claim_with_file_evidence_is_not_reported` - a sentence asserting a property of `qor/` backed by one statement citing a single file under it yields zero findings. Pins the dropped kind as deliberately absent, so a future implementer does not reintroduce it by intuition.
- `test_a_cardinal_not_adjacent_to_its_noun_is_not_reported` - the sentence "`_emit` returning 1 on findings" in an unevidenced LD sub-block yields zero findings. Pins adjacency as behaviour rather than an implementation habit; a regex tolerating intervening tokens fails it. Declared separately from the self-application test on purpose: that test also goes red on a loose regex, but its cheapest repair is rewording the plan, whereas this one can only be satisfied by the regex.
- `test_a_nested_backtick_line_is_stripped_without_residue_findings` - a line carrying an odd number of backticks, as LD-3's own span-removal clause does, yields zero findings. LD-3's body is the worst case for LD-3's rule.
- `test_bare_cardinal_without_evidence_is_reported` - "the suite holds 24 assertions" with no statement yields `absolute-claim-uncounted`. The class markers cannot see, and the class that produced the historical miscounts.
- `test_prose_outside_locked_decisions_is_not_scanned` - the same marker sentence in a Changes section yields zero findings, pinning LD-2.
- `test_every_marker_in_the_closed_set_is_detected` - one fixture per member of `ABSOLUTE_MARKERS`, each yielding a finding. Inverse coverage against the declared set.
- `test_main_exits_one_on_findings_and_zero_when_clean` - `main` against a dirty then a clean fixture; asserts 1 then 0.
- `test_cli_entrypoint_exits_one_on_a_dirty_plan` - subprocess `python -m qor.scripts.plan_absolute_claim_lint`, asserting returncode 1 then 0. In-process `main` cannot detect a missing entry-point guard.
- `test_lint_reports_nothing_on_its_own_plan` - runs the lint against this plan file and asserts zero findings. Meaningful only because LD-2 pairs per decision rather than per section: under the coarser region the assertion would hold for every plan ever written and prove nothing.
- `test_a_section_wide_statement_does_not_satisfy_a_neighbouring_decision` - two decisions in one `### Locked Decisions` section, evidence in the first and an unbacked marker sentence in the second, yields one finding. Pins the LD-2 subdivision; red under the coarser region.

## Phase 2: Make the recurrence machine-visible

### Affected Files

- `tests/test_scope_overgeneralization_taxonomy.py` NEW - enum membership, schema-to-mirror parity, and classification behavior
- `qor/gates/schema/audit.schema.json` - add `scope-overgeneralization` to `findings_categories`
- `qor/gates/schema/shadow_event.schema.json` - add `scope_overgeneralization` to `event_type`
- `qor/scripts/findings_signature.py` - add the same value to `_VALID_CATEGORIES`, and add `feature-test-undeclared`, which is absent today. See LD-6a
- `qor/scripts/remediate_pattern_match.py` - add the pattern rule
- `docs/FEATURE_INDEX.md` - append FX029

### Locked Decisions

**LD-6. Both enums are additive and break no existing assertion.** Measured over the whole `tests/` tree, not a filtered subset: every assertion touching `findings_categories` or `event_type` is either per-payload (`== ["razor-overage"]`, `== []`) or membership (`"live-progress-fake" in schema[...]["enum"]` at `tests/test_plan_live_progress_lint.py:83`; a substring check at `tests/test_skill_integrity.py:34`). None pins either enum's contents.

- `git show 9bb10b61:tests/test_plan_live_progress_lint.py | grep -nE 'live-progress-fake'` -> `83:    assert "live-progress-fake" in schema["properties"]["findings_categories"]["items"]["enum"]`
- `git show 9bb10b61:tests/test_skill_integrity.py | grep -nE 'infrastructure-mismatch'` -> `34:    assert "infrastructure-mismatch" in json.dumps(schema)`
- `git show 9bb10b61:tests/test_continuity_declaration.py | grep -nE 'sorted\(field'` -> `141:        assert sorted(field["enum"]) == sorted(cc.OUTCOMES)`
- `git show 9bb10b61:tests/test_seal_intent_lock_state.py | grep -nE 'sorted\(field'` -> `34:    assert sorted(field["enum"]) == ["absent", "overridden", "verified"]`

**No total is asserted, and the omission is deliberate.** Iterations 4 and 5 stated this count as "one" and then "two"; both were wrong, each from a different narrowing -- a single file, then a two-alternative pattern that structurally cannot match the `:104` form. A quantity mis-stated three times is not a quantity this plan can assert, and nothing in Phase 2 branches on it.

What the decision rests on is an absence, and an absence is warranted by a search rather than by examples. The search is the one recorded two paragraphs above: every assertion in `tests/` touching `findings_categories` or `event_type` is per-payload or membership, and the negative fixtures use invented values (`fictional-category`, `mystery`) that collide with neither added value. The citations above are the opposite direction -- they show exact-set assertions exist and which enums they govern, namely `continuity_outcome`, the validate criteria `status`, and `intent_lock_state`. This phase touches none of the three.

**LD-6a. The schema enum has a hardcoded mirror, and editing one without the other breaks the escalator this phase exists to arm.**

- `git show 9bb10b61:qor/scripts/findings_signature.py | grep -nE '_VALID_CATEGORIES'` -> `28:_VALID_CATEGORIES = frozenset({`
- `git show 9bb10b61:qor/scripts/stall_walk.py | grep -nE 'compute_record'` -> `57:        sig = findings_signature.compute_record(record)`

`compute_record` raises `UnmappedCategoryError` on any category outside that frozenset, and `stall_walk` calls it unguarded at two sites. Those are the functions behind `cycle_count_escalator.check` and `check_session_total`. Adding the new value to the schema alone would make the first audit emitting it raise inside the next cycle's escalation check rather than fire on the third occurrence, which is the opposite of LD-8's intent.

The mirror has already drifted, and the drift is live rather than hypothetical: the schema holds 15 values and the frozenset 14, the missing one being `feature-test-undeclared`, which is item 9 of `/qor-audit`'s own Critical Invariants. A correct audit emitting it crashes the escalator today. Filed as GH #437; this phase closes it because it edits the same pair and would otherwise ship a second copy of the defect.

No test binds the two sources, which is why the suite is green while they diverge. The pairing was understood once and recorded in a plan document rather than a test, so it did not survive. This phase adds the test.

**LD-7. The pattern rule follows the existing table.**

- `git show 9bb10b61:qor/scripts/remediate_pattern_match.py | grep -nE 'PATTERN_RULES'` -> `24:PATTERN_RULES = [`

A `scope_overgeneralization` group of two or more events in one session classifies as `scope-overgeneralization`. It is appended below `gate-loop` for readability, but the ranking is inert: every rule keys on `event_type` and a group carries exactly one, so no group can satisfy two rules. The property worth testing is non-interference with the existing rules, not precedence.

**LD-8. Why this is the load-bearing half.** The escalator fires on a repeated *signature*, and a signature is derived from the finding categories:

- `git show 9bb10b61:qor/scripts/cycle_count_escalator.py | grep -nE 'ESCALATION_THRESHOLD = '` -> `21:ESCALATION_THRESHOLD = 3`
- `git show 9bb10b61:qor/scripts/cycle_count_escalator.py | grep -nE 'count < ESCALATION'` -> `47:    if count < ESCALATION_THRESHOLD:`

Phase 258's five VETO verdicts each carried a different category set, recorded at META_LEDGER entries #726 through #730, so no signature repeated and the threshold at line 47 was never reached. Giving the class its own category means three occurrences share a signature and the existing check fires. This phase adds no escalation machinery; it supplies the category the existing threshold counts.

### Unit Tests

- `test_audit_schema_admits_the_new_category` - a gate payload carrying `scope-overgeneralization` validates; one carrying an invented value does not. Both directions.
- `test_shadow_schema_admits_the_new_event_type` - same, both directions.
- `test_two_scope_events_in_one_session_classify` - two `scope_overgeneralization` events in one session yield the pattern; one event yields nothing.
- `test_scope_pattern_does_not_shadow_an_existing_rule` - a group of `gate_override` events still classifies as `gate-loop` after the new rule is added, asserted directly on the predicate rather than through a mixed session. `classify` keys groups by `(event_type, skill, session_id)`, so one group holds one event type and a mixed session yields two independent matches; the LD-7 ranking is therefore inert and the test pins non-interference, which is the property that actually matters.
- `test_existing_categories_still_validate` - parametrized over **both** enums: every pre-existing `findings_categories` value and every pre-existing `event_type` value still validates against its amended schema, so the addition is proven additive on both surfaces rather than on the audit one alone.
- `test_schema_enum_and_valid_categories_are_identical` - asserts `set(audit.schema.json findings_categories enum) == set(findings_signature._VALID_CATEGORIES)`. Red today, before this phase edits either: the schema holds 15 values and the frozenset 14.
- `test_escalator_survives_the_new_category` - builds an audit record carrying `scope-overgeneralization`, drives `stall_walk.count_session_signature_totals` over it, and asserts it returns rather than raising. Red if the mirror is not updated alongside the schema.
- `test_three_scope_occurrences_return_an_escalation_recommendation` - drives `cycle_count_escalator.check_session_total` with three same-signature records carrying the new category and asserts a recommendation comes back. Makes the third-occurrence clause directly verifiable rather than inferable from a threshold constant.

## Phase 3: Doctrine and wiring

### Affected Files

- `tests/test_scope_overgeneralization_doctrine.py` NEW - doctrine content and enforcer citation
- `qor/references/doctrine-shadow-genome-countermeasures.md` - new SG entry
- `qor/references/glossary.md` - one term entry with a non-empty `referenced_by`
- `qor/skills/governance/qor-audit/SKILL.md` - one lint line in the Step 0.6 ladder
- `tests/test_governance_index_doctrine.py` - unchanged, named as a live consumer of the glossary
- `tests/test_dogfood_glossary_coverage.py` - unchanged, named as a live consumer: it runs the orphan check against the live repository in `pytest`, so the new term's `referenced_by` must be non-empty or the suite goes red before any seal
- `tests/test_sg_closure_retrofit.py` - unchanged, named as the binding live consumer of the edited doctrine: it executes `sg_closure_lint` over the live file and asserts the uncited list is empty, so an uncited new entry turns the suite red. See LD-9
- `tests/test_terminology_unification.py` - unchanged, named as a live consumer of the doctrine corpus: the new entry must not use a bare `change_type` identifier outside code fences
- `tests/test_readme_doctrine_inventory.py` - unchanged, named to record that it does **not** fire: this phase adds a section to an existing doctrine rather than a new `doctrine-*.md` file, so no README inventory row is owed
- `tests/test_substantiate_staging_gates.py` - unchanged, named as the consumer holding the binding size bound on the edited skill. See LD-10
- `tests/test_skill_corpus_consolidation.py` - unchanged, named as a consumer of the edited skill: it pins the literal Step 0.6 heading and carries its own budget assertion. A ladder line added inside that section leaves both intact, but a line added to the wrong section would not
- `tests/test_install_sync_with_source.py` - unchanged, named as the consumer that makes the dist variants mandatory rather than optional: it byte-compares every source SKILL.md against its variant counterpart, so editing the audit skill turns four tests red until the variants are regenerated. See LD-11
- `qor/dist/variants/claude/skills/qor-audit/SKILL.md`, `qor/dist/variants/codex/skills/qor-audit/SKILL.md`, `qor/dist/variants/kilo-code/skills/qor-audit/SKILL.md`, `qor/dist/variants/cursor/skills/qor-audit/SKILL.md` - regenerated by `python -m qor.scripts.dist_compile`, not hand-edited. These four are the ones the sync tests byte-compare
- `qor/dist/variants/cline/workflows/command-qor-audit.md`, `qor/dist/variants/gemini/commands/qor-audit.toml` - also regenerated by the same command, and also carrying the Step 0.6 ladder. No test byte-compares this pair, but the CI drift gate does, so omitting them fails CI rather than shipping silently
- `qor/dist/manifest.json` and the six `qor/dist/variants/*/manifest.json` - regenerated in the same pass. All seven change on every run because `generated_ts` is stamped unconditionally, and the root plus claude, codex, cursor and kilo-code additionally carry a changed `sha256` for the audit skill. They are the one artifact class the drift gate does not compare, so a stale hash here ships unnoticed. See LD-11 and GH #440
- `tests/test_feature_index_citations_resolve.py`, `tests/test_feature_index_present_and_verifies.py` - unchanged, named as live consumers of `docs/FEATURE_INDEX.md`: FX029's source and test citations must both resolve on disk after implementation

- `git show 9bb10b61:tests/test_skill_corpus_consolidation.py | grep -nE 'Step 0\.6'` -> `78:    "### Step 0.6:", "### Step 1:", "### Step 2:", "### Step 3:",`

### Locked Decisions

**LD-9. The SG entry cites its enforcer, because the lint requires it.**

- `git show 9bb10b61:qor/scripts/sg_closure_lint.py | grep -nE '_ENTRY_RE'` -> `19:_ENTRY_RE = re.compile(r"^## (SG-[^\s(]+)", re.MULTILINE)`

The lint walks every `## SG-` entry and flags any citing none of its accepted enforcer forms: a test path, a `qor.scripts` or `qor.reliability` module, either module-path spelling, a gate-step reference, a `schema.json` reference, or an explicit `cannot-automate` decision.

**A citation is compelled, and iteration 3 said otherwise on a narrower reading.** The lint is WARN-only in the audit ladder, but a test executes it over the live doctrine and asserts the uncited list is empty, which is stronger than pinning a count:

- `git show 9bb10b61:tests/test_sg_closure_retrofit.py | grep -nE 'def test_no_entry_lacks'` -> `27:def test_no_entry_lacks_an_enforcer_or_decision():`

The doctrine sits at zero findings today, so an uncited new entry turns `python -m pytest -q` red. Iteration 3 consulted `tests/test_sg_closure_wiring.py`, which pins the ladder line rather than the finding count, and wrote the conclusion unqualified. The same retrofit file, not the wiring one, also constrains the citation form: it harvests paths from `**Enforcer**:` lines and requires each to resolve on disk.

- `git show 9bb10b61:tests/test_sg_closure_retrofit.py | grep -nE 'Enforcer'` -> `52:        line for line in text.splitlines() if line.lstrip().startswith("**Enforcer**:")`

So the entry carries a resolvable `qor/scripts/plan_absolute_claim_lint.py` spelling alongside the dotted module name. Iteration 5 attributed this to `tests/test_sg_closure_wiring.py`, which asserts only that the ladder line is present.

**LD-10. The skill edit fits, measured against the bound that actually fails first.** Two bounds govern `qor/skills/governance/qor-audit/SKILL.md`, and the tighter one is the binding one:

- `git show 9bb10b61:tests/test_substantiate_staging_gates.py | grep -nE 'HEADROOM_BYTES'` -> `54:HEADROOM_BYTES = 39 * 1024  # Phase 178 (GH #266): keep >= 1 KB under EXCEEDED`
- `git show 9bb10b61:qor/scripts/skill_size_budget_lint.py | grep -nE 'EXCEEDED_BYTES = '` -> `24:EXCEEDED_BYTES = 40 * 1024`

The file is 39,251 bytes. Against the test-enforced 39,936 that is **685 bytes** of headroom, not the 1,024-byte-looser figure the lint's own threshold would suggest. One ladder line costs under 100 and fits.

Iteration 1 measured against `EXCEEDED_BYTES` because that is the bound `skill_size_budget_lint` uses, and never checked for a tighter one elsewhere. The tool consulted determined the answer, which is this phase's own subject class. It is recorded here rather than silently corrected. No new size assertion is added: an existing test already guards this bound, and adding a second copy is the duplication Phase 221 removed.

**LD-11. Editing a source skill obliges regenerating its dist variants, and a test enforces it.**

- `git show 9bb10b61:tests/test_install_sync_with_source.py | grep -nE 'def test_claude_variant_skill_sync'` -> `65:def test_claude_variant_skill_sync():`

Four variant sync tests byte-compare `qor/skills/**/SKILL.md` against `qor/dist/variants/<variant>/skills/<name>/SKILL.md`, so the one-line ladder edit turns four tests red until `python -m qor.scripts.dist_compile` regenerates them.

`dist_compile` regenerates **thirteen** artifacts touched by this edit: six skill outputs and seven manifests.

The six are the four compared `SKILL.md` copies plus the cline workflow and the gemini TOML, both of which carry the Step 0.6 ladder. Iteration 6 called that pair "untested" and used it as the reason to name them. That was wrong, and the correction matters because it changes what guards the edit:

- `git show 9bb10b61:.github/workflows/ci.yml | grep -nE 'check_variant_drift'` -> `50:      - run: python qor/scripts/check_variant_drift.py`

That job regenerates the whole dist into a tempdir and byte-diffs it against the committed tree, so the cline and gemini artifacts are guarded -- by CI rather than by pytest. Staging only the four byte-compared copies fails there, not silently. Iteration 6 checked pytest and wrote the conclusion unqualified.

The seven manifests are the genuinely unguarded surface, and are the reason this decision is not merely bookkeeping:

- `git show 9bb10b61:qor/scripts/check_variant_drift.py | grep -nE '_DRIFT_EXCLUDE'` -> `22:_DRIFT_EXCLUDE = {"manifest.json"}`
- `git show 9bb10b61:qor/install.py | grep -nE 'installed.append'` -> `67:            installed.append({"path": str(dst), "sha256": entry["sha256"]})`

`manifest.json` is the only file class the drift gate excludes, to dodge a `generated_ts` field, which takes the deterministic per-artifact `sha256` entries with it. The installer then copies those unverified hashes into the operator's receipt without recomputing. Staging the six outputs without the manifests would leave seven files recording a hash for a skill that no longer matches, and nothing in the repository would notice. That gap predates this phase and is filed as GH #440; this plan does not fix it, it only declines to widen it.

All thirteen are outputs of one `dist_compile` pass, so they are listed as regenerated rather than edited.

### Changes

The SG entry states the pattern, its mechanism, and its countermeasure: a claim derived from a command states that command's scope in the sentence; a retraction restates the scope and is checked against a re-run rather than a recollection, because a retraction is written at the speed of the error it retracts and inherits its scope; and any claim of absence is re-run without the narrowing flag before it leaves the repository.

The Step 0.6 ladder gains one `|| true` line, matching every other entry in it.

### Unit Tests

- `test_doctrine_entry_cites_an_executable_enforcer` - runs `sg_closure_lint` over the amended doctrine and asserts the new SG id is absent from its findings.
- `test_doctrine_states_the_retraction_rule` - asserts the entry's body contains the re-run-not-recollection requirement, by parsing the entry body and asserting on the extracted section rather than a whole-file substring.
- `test_audit_skill_wires_the_lint_into_step_zero_six` - parses the Step 0.6 code block out of the skill and asserts the lint invocation appears within it, so a line added to the wrong section fails.
- `test_glossary_term_has_non_empty_referenced_by` - asserts the new term's `referenced_by` is non-empty, which is what `test_dogfood_glossary_coverage` would otherwise fail on at suite time.

## Definition of Done

### Deliverable: absolute-claim lint

- **D1**: An absolute claim in a Locked Decision must carry evidence or state its own scope, or the lint reports it.
- **D2**: `qor/scripts/plan_absolute_claim_lint.py` exposes `ClaimFinding`, `ABSOLUTE_MARKERS`, `find_findings`, `main(argv) -> int`, and an entry-point guard; no public or private name begins with a validator prefix.
- **D3**: Wired into `/qor-audit` Step 0.6 as a WARN-only ladder entry, with all thirteen regenerated dist artifacts staged: the four `SKILL.md` copies the sync tests byte-compare, the cline workflow and gemini TOML the CI drift gate compares, and the seven manifests nothing compares.
- **D4**: `test_bare_cardinal_without_evidence_is_reported` covers the class that produced the historical miscounts; `test_corpus_claim_with_file_evidence_is_not_reported` pins the deliberately dropped kind; `test_lint_reports_nothing_on_its_own_plan` proves self-application, meaningful because LD-2 pairs per decision; `test_cli_entrypoint_exits_one_on_a_dirty_plan` proves the dispatch path by subprocess.

### Deliverable: recurrence taxonomy

- **D1**: Two occurrences of the class in one session are classifiable, and a third fires the existing escalator.
- **D2**: Both schema enums carry the new value; `findings_signature._VALID_CATEGORIES` carries it too, plus the `feature-test-undeclared` value missing today; `remediate_pattern_match.PATTERN_RULES` carries the rule.
- **D3**: No existing category or event type changes meaning.
- **D4**: `test_schema_enum_and_valid_categories_are_identical` and `test_escalator_survives_the_new_category` pass, both red beforehand; `test_three_scope_occurrences_return_an_escalation_recommendation` proves the third-occurrence clause directly; `test_two_scope_events_in_one_session_classify` and `test_scope_pattern_does_not_shadow_an_existing_rule` pass; `test_existing_categories_still_validate` proves the addition is additive by execution rather than inspection.

### Deliverable: doctrine

- **D1**: The pattern, its mechanism, and its countermeasure are recorded where the countermeasure doctrine lives.
- **D2**: A new `## SG-` entry citing `qor.scripts.plan_absolute_claim_lint`.
- **D3**: One glossary term with a non-empty `referenced_by`; no README inventory row owed, because no new doctrine file is created.
- **D4**: `test_doctrine_entry_cites_an_executable_enforcer` runs the real `sg_closure_lint` and asserts the entry is absent from its findings.

## Feature Inventory Touches

FX028 is skipped deliberately: it is reserved by the Phase 258 plan, which reached its attempt cap without sealing, so the identifier is claimed but never landed. Nothing enforces identifier contiguity, so the gap breaks no test; it is stated here so a later reader does not read it as an omission.

| entry_id | operation | test_path | test_descriptor |
|---|---|---|---|
| FX029 | NEW | tests/test_plan_absolute_claim_lint.py | `qor-logic scripts plan_absolute_claim_lint` exits 1 naming `absolute-claim-unevidenced` for a marker sentence in a Locked Decision carrying neither evidence nor a scope qualifier, and `absolute-claim-uncounted` for a bare cardinal carrying neither, and exits 0 on a plan whose marker and counting sentences all carry one or the other |

## CI Commands

- `python -m pytest tests/test_plan_absolute_claim_lint.py tests/test_scope_overgeneralization_taxonomy.py tests/test_scope_overgeneralization_doctrine.py -v` - the three new suites; run twice to confirm determinism
- `python -m pytest tests/test_phase49_self_application.py tests/test_remediate.py tests/test_audit_gate_artifact.py tests/test_dogfood_glossary_coverage.py tests/test_terminology_unification.py tests/test_governance_index_doctrine.py tests/test_substantiate_staging_gates.py tests/test_skill_corpus_consolidation.py tests/test_readme_doctrine_inventory.py tests/test_feature_index_citations_resolve.py tests/test_feature_index_present_and_verifies.py -v` - the eleven named live consumers, run explicitly rather than relied on incidentally
- `python -m pytest -q` - full suite; no regression
- `qor-logic scripts plan_absolute_claim_lint --plan docs/plan-qor-phase261-scope-claim-controls.md --repo-root .` - the lint reports nothing on its own plan
- `python -m qor.scripts.dist_compile` - regenerate all thirteen touched artifacts after the ladder edit. Four are byte-compared by sync tests and red until it runs, two more are compared by the CI drift gate, and the seven manifests are compared by nothing and must still be staged. See LD-11
- `python -m pytest tests/test_install_sync_with_source.py -v` - the variant sync tests specifically
- `python -m pytest tests/test_sg_closure_retrofit.py -v` - the binding assertion that the uncited list stays empty
- `qor-logic scripts sg_closure_lint` - the new SG entry cites an enforcer
- `qor-logic scripts skill_size_budget_lint` - the audit skill stays below the EXCEEDED threshold
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase261-scope-claim-controls.md` - plan self-consistency
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain integrity
- `ruff check .` - lint
