# Plan: Decision-record contract

**change_class**: feature

**doc_tier**: standard

**iteration**: 7 (iteration 6 withdrawn without verdict; amends it for one CI-fatal omission, four unnamed live consumers, two corpus invariants, and three prose corrections)

**terms_introduced**:
- term: decision record
  home: qor/references/doctrine-decision-records.md
- term: phase binding field
  home: qor/references/doctrine-decision-records.md

**boundaries**:
- limitations:
  - The detector reads decision records only. It never opens `docs/META_LEDGER.md`, so it cannot judge whether a declared status matches reality. It checks that a record declares a phase and a status the vocabulary admits, and nothing more.
  - The three backfilled statuses are asserted on evidence recorded in LD-6. They become machine-checked when Phase 259 ships the seal binding; until then they are documented facts, not verified ones.
  - Registering the new doctrine in the governance index is correct but unverified. `governance_index` cannot raise `unregistered` for a file under `qor/references/`, so no gate confirms the row exists. LD-4 states the limit rather than implying a check.
- non_goals:
  - Deciding whether a decision record's content is correct.
  - Any change to how `/qor-status` behaves without an explicit flag.
- exclusions:
  - The seal-binding surface: `adr-status-stale`, `adr-phase-unsealed`, the `meta_ledger_walker` plan field, the label-dialect predicate, and the consumer-contract fixture amendment. Phase 259; facts preserved in `.agent/staging/PHASE259_SEED.md`.
  - The machine-author predicate consolidation, its `machine author` glossary term, and the `qor/references/doctrine-attribution.md` edit. Moved to Phase 259 at iteration 6; see Scoping.
  - `qor/scripts/status_full.py` and the `/qor-status --full` flag. Phase 260.
  - The `governance_index.py:143` seal-predicate defect. Phase 259.
  - GH #431 and GH #432, filed separately 2026-09-04. GH #435 was filed during this phase on a false premise and is closed as an error of the plan author.

## Scoping

This phase has been narrowed twice, both times because a surface kept failing audit while the rest of the plan did not.

The first narrowing moved the seal binding to Phase 259 after two VETOes on it. The second, here, moves the machine-author predicate consolidation to Phase 259 after the tribunal found that Phase 3's entire deliverable -- deduplicating one predicate into one home -- had no test that could detect whether the deduplication happened, and that it edited a doctrine without naming the test that reads it. Both findings were real and both were local to Phase 3. Removing that phase discharges them rather than repairing them, and takes with it two of the four false claims the same verdict found, because both were about files only Phase 3 touched.

Phase 259 is the right home: it already carries the seal binding, and the predicate work is attribution-adjacent to nothing else in this plan.

What remains is one coherent thing: decision records get a machine-readable contract, and a detector enforces the two properties that contract can check without reading anything else. It is smaller than the phase began, and it is the part that has never failed an audit on its own merits.

## Open Questions

None.

## Phase 1: Decision-record contract

### Affected Files

- `tests/test_adr_contract.py` NEW - vocabulary, front-matter parser, and tier-table parser behavior, plus conformance over the real `docs/ADR_*.md` set
- `qor/scripts/adr_contract.py` NEW - status vocabulary, `normalize_status`, `parse_record`, `parse_tier_table`
- `qor/references/doctrine-decision-records.md` NEW - the contract as doctrine
- `docs/ADR_QOR_ROADMAP.md` - add `**Phase:** 239`, `**Issue:** GH #373`; status to `Accepted` (not `Implemented`; see LD-6)
- `docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md` - add `**Phase:** 241`; status to `Implemented`
- `docs/ADR_EXECUTION_CONTEXT_ADAPTIVE_GOVERNANCE.md` - add `**Phase:** 240`; status to `Implemented`
- `docs/GOVERNANCE_INDEX.md` - Tier 2 gains a `Freshness marker` column and the amended tier preamble; register the new doctrine; advance `**Last Reviewed**`
- `qor/templates/GOVERNANCE_INDEX.md` - the same column and preamble, so a seeded workspace conforms to the doctrine it receives
- `qor/references/doctrine-governance-index.md` - Tier 2's contract row gains the per-row freshness marker the index now carries
- `qor/references/glossary.md` - two term entries, each with a non-empty `referenced_by`; see LD-5
- `README.md` - add a doctrine-inventory row for the new doctrine. Not cosmetic: see LD-10
- `tests/test_readme_doctrine_inventory.py` - unchanged, named as a live consumer. It is the completeness invariant LD-10 turns on
- `tests/test_governance_index_doctrine.py` - unchanged, named as a live consumer of two edited files: it reads `qor/references/doctrine-governance-index.md` and `qor/references/glossary.md`. Verified non-breaking: its tier test needs the six tier names plus the strings `Governance Index Drift` and `stale-tier1`, all of which survive amending the Tier 2 cell, and its glossary test asserts three named terms and is additive-safe
- `tests/test_dogfood_glossary_coverage.py` - unchanged, named as a live consumer of the glossary and the reason LD-5's orphan rule is proven in `pytest` rather than only at seal. See LD-5
- `tests/test_terminology_unification.py` - unchanged, named as the second corpus invariant over `qor/references/doctrine-*.md`. See LD-10
- `tests/test_feature_index_citations_resolve.py`, `tests/test_feature_index_present_and_verifies.py` - unchanged, named as live consumers of `docs/FEATURE_INDEX.md`: FX028's source and test citations must both resolve on disk
- `qor/scripts/snapshot_export.py` - unchanged, named as a live consumer of `status_json.default_registry`, which it calls with `run_all`. The seventh check appears in snapshot health output; no test asserts a count
- `tests/test_portable_governance_boundary.py` - unchanged, named as a live consumer of an edited record: it reads `docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md` and must be re-run rather than caught incidentally by the full suite. It holds 11 test functions and 24 assertions, several of them whole-file reads of that record, none keyed on the status line; the whole-file assertions are satisfied by the H1 title and body prose, so the front-matter edit is safe

### Locked Decisions

**LD-1. Front-matter shape.** Every decision record carries `**Status:**` and `**Phase:**` as separate contiguous fields. The binding lives in `**Phase:**`; the status line carries no phase reference.

- `git show 9bb10b61:docs/ADR_EXECUTION_CONTEXT_ADAPTIVE_GOVERNANCE.md | grep -nE '^\*\*Status:'` -> `3:**Status:** Accepted for Phase 240 implementation`
- `git show 9bb10b61:docs/ADR_EXECUTION_CONTEXT_ADAPTIVE_GOVERNANCE.md | grep -nE '^\*\*Issue:'` -> `5:**Issue:** GH #379`
- `git show 9bb10b61:docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md | grep -nE '^\*\*Status:'` -> `3:**Status:** Proposed for Phase 241, revised after governed-procedure evidence review`
- `git show 9bb10b61:docs/ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md | grep -nE '^\*\*Issue:'` -> `5:**Issue:** GH #381`
- `git show 9bb10b61:docs/ADR_QOR_ROADMAP.md | grep -nE '^\*\*Date:'` -> `4:**Date:** 2026-08-27`
- `git show 9bb10b61:docs/ADR_QOR_ROADMAP.md | grep -nE '^\*\*Scope:'` -> `5:**Scope:** Qor-logic base capability`

Two records place `**Issue:**` at line 5 after a blank line 4. The roadmap record packs its fields contiguously, so line 4 already holds `**Date:**` and no issue field exists. Its status line carries inline code formatting and no phase number, which is why it cannot be cited here by observed text and why a parser keyed on the status line cannot bind it.

**Vocabulary collision, declared.** `docs/META_LEDGER.md` already carries a `**Phase**:` field whose value is a lifecycle stage rather than a number. Decision records introduce `**Phase:** NNN`. Different artifacts, no technical conflict, but the doctrine states both domains so a future reader does not assume one parser serves them.

**LD-2. Three parsers, all ledger-free.** `qor/scripts/adr_contract.py` holds `CANONICAL_ADR_STATUSES`, `normalize_status(raw)`, `parse_record(path)`, and `parse_tier_table(text, tier)`. No function in this module reads `docs/META_LEDGER.md`.

`parse_tier_table` exists so the tier test invokes a unit rather than asserting document shape directly, which would be the presence-only pattern under `qor/references/doctrine-test-functionality.md`.

**LD-3. Each vocabulary value carries a definition.** A closed vocabulary whose members are undefined cannot be checked by a human either.

| value | means |
|---|---|
| `Proposed` | the decision is drafted and not yet ratified by a gate |
| `Accepted` | the decision is ratified and stands; delivery may be partial or its evaluation still open |
| `Implemented` | the capability the record describes is delivered in full |
| `Superseded` | a later record replaces this one, which is named in the body |
| `Rejected` | the decision was considered and declined; the record is retained for its reasoning |

The `Accepted`/`Implemented` boundary is the one that does work, and it is the boundary LD-6 turns on. No rule in this phase depends on seal state, so `adr-invalid-status` applies uniformly to every value outside the vocabulary and no value inside it produces a finding. Seal-dependent drift arrives in Phase 259.

**LD-4. The Tier 2 freshness contract is amended in all three places that carry it.** In the live index and the seed template that means a new third column, so the table becomes `| Artifact | Path | Freshness marker |`, matching Tier 1's existing shape. In the doctrine it means an amended cell in the existing four-column Tier/Name/Contract/Drift table, not a new column. Decision-record rows carry `status matches sealed phase (enforced from Phase 259)`; every other row, including the template's single `_example_` row, carries `stable`. The qualifier is load-bearing: an unqualified marker would state a live contract no code implements.

- `git show 9bb10b61:docs/GOVERNANCE_INDEX.md | grep -nE '^\| Artifact \| Path'` -> `14:| Artifact | Path | Freshness marker |`
- `git show 9bb10b61:docs/GOVERNANCE_INDEX.md | grep -nE '^\| Artifact \| Path'` -> `30:| Artifact | Path |`
- `git show 9bb10b61:qor/templates/GOVERNANCE_INDEX.md | grep -nE '^\| Artifact \| Path'` -> `29:| Artifact | Path |`
- `git show 9bb10b61:qor/references/doctrine-governance-index.md | grep -nE 'Doctrine & Policy'` -> `21:| 2 | Doctrine & Policy | stable; changes are explicit doctrine events | rules contradict each other or operator memory |`
- `git show 9bb10b61:docs/GOVERNANCE_INDEX.md | grep -niE 'explicit doctrine events'` -> `28:Stable; changes are explicit doctrine events. Drift signal: rules contradict each other or operator memory.`
- `git show 9bb10b61:qor/templates/GOVERNANCE_INDEX.md | grep -niE 'explicit doctrine events'` -> `27:Stable; changes are explicit doctrine events. Drift signal: rules contradict each other or operator memory.`

The doctrine carries the contract as a table row; the live index and the seed template carry it as tier preamble prose. All three move together or Tier 2's own declared drift signal fires.

**Registration is real but unverified, and this plan says so rather than implying a check.** The new doctrine's row is correct and required by the index's own "How to add a governance artifact" procedure, but no gate can confirm it:

- `git show 9bb10b61:qor/scripts/governance_index.py | grep -nE 'for rel_dir in'` -> `57:    for rel_dir in (".", "docs"):`
- `git show 9bb10b61:qor/scripts/governance_index.py | grep -nE 'stale-tier1'` -> `179:    findings = [f for f in check_index_drift(base) if f.kind == "stale-tier1"]`

`_governance_docs` scans root and `docs/` non-recursively, so a file under `qor/references/` is never a candidate for `unregistered`; and `cross_check_index_against_ledger` filters to `stale-tier1`, so it cannot emit that finding at all. The CI Commands entry for that command is annotated accordingly.

The conclusion survives a second way: `docs/GOVERNANCE_INDEX.md` line 75 already carries a `qor/references/*.md` Tier 5 glob row, and `_is_registered` honors glob rows, so even under a hypothetically widened scan the new doctrine reads as registered. The Tier 2 row is added because the index's own procedure requires it, not because a gate would otherwise complain.

**LD-5. The `decision record` glossary entry adopts one skill path, or the seal aborts.** `doc_integrity` runs term drift in strict mode at substantiate over Markdown under `qor/references`, `qor/gates`, `qor/skills` and `docs`, plus four root files.

- `git show 9bb10b61:qor/scripts/doc_integrity.py | grep -nE 'check_term_drift'` -> `211:        dis.check_term_drift(glossary_path, repo_root, strict=True)`
- `git show 9bb10b61:qor/scripts/doc_integrity_strict.py | grep -nE 'rglob'` -> `50:        for p in base.rglob("*.md"):`
- `git show 9bb10b61:qor/scripts/doc_integrity_strict.py | grep -nE '_DOCS_LIVING'` -> `135:    if rel.startswith("docs/") and rel not in _DOCS_LIVING:`

The term occurs in several Markdown files. Every occurrence but one is out of reach: those under `qor/dist` and `qor/vendor` sit outside a scan root or inside an excluded directory, those under `docs/` are fenced by line 135 except the four living docs, and plural uses do not match a word-bounded pattern. The single unfenced in-scope occurrence is in the qor-help skill's command table, at line 114, phrased in the singular. That path must appear in the entry's `referenced_by`. The corpus is Markdown-only, so `.py` docstrings using the phrase are out of scope by construction.

**Both terms take a non-empty `referenced_by`.** `phase binding field` has no *in-scope* Markdown occurrence: it appears once in `docs/META_LEDGER.md`, which the docs fence excludes. So it earns no `referenced_by` from usage, and an empty one is not merely seal-aborting but test-failing:

- `git show 9bb10b61:qor/scripts/doc_integrity.py | grep -nE 'if e.referenced_by'` -> `81:        if e.referenced_by:`
- `git show 9bb10b61:qor/scripts/doc_integrity.py | grep -nE 'introduced_in_plan'` -> `83:        if e.introduced_in_plan == current_session_plan_tag:`

`check_orphans` raises unless one of those two lines matches. The `introduced_in_plan` branch is reachable at seal -- `/qor-substantiate` derives the tag and injects it before the check runs -- but it cannot rescue this phase, because the orphan check also runs in the ordinary test suite against the live repository under a different plan slug:

- `git show 9bb10b61:tests/test_dogfood_glossary_coverage.py | grep -nE 'plan_slug'` -> `65:        "plan_slug": "phase28-documentation-integrity",`
- `git show 9bb10b61:tests/test_dogfood_glossary_coverage.py | grep -nE 'run_all_checks_from_plan'` -> `67:    doc_integrity.run_all_checks_from_plan(plan, repo_root=str(REPO_ROOT))`

`test_doctrine_self_substantiates` calls `run_all_checks_from_plan` with `repo_root` set to the real tree, so a new glossary entry with an empty `referenced_by` fails `pytest -q` regardless of what this plan declares, since the tag it compares against is Phase 28's. That call does not request strict mode, so term drift is not exercised there and the qor-help adoption at LD-5 remains a seal-time obligation; the orphan rule does not. All 135 existing entries pass at line 81, so the fallback has never been exercised in this corpus either. `phase binding field` therefore names `qor/scripts/adr_contract.py` and `qor/scripts/adr_status_lint.py`, which are exactly the parser that reads the field and the reporter that acts on it. `.py` paths are conventional in `referenced_by` and appear in dozens of existing entries; `check_orphans` validates that `home` resolves and never checks `referenced_by` paths.

**LD-10. Creating a doctrine file obliges a README row, and the obligation is CI-enforced.** `qor/references/doctrine-*.md` is a governed corpus with two whole-corpus invariants, both of which this phase must satisfy.

- `git show 9bb10b61:tests/test_readme_doctrine_inventory.py | grep -nE 'missing = files'` -> `36:    missing = files - listed`
- `git show 9bb10b61:tests/test_terminology_unification.py | grep -nE 'DOCTRINES = '` -> `14:DOCTRINES = list((REPO_ROOT / "qor" / "references").glob("doctrine-*.md"))`

The first is completeness: `test_readme_lists_every_doctrine_file` asserts `files - listed` is empty against the hand-maintained doctrine table in `README.md`. Forty doctrine files exist today and the suite is green; a forty-first without a README row makes `missing == {"decision-records"}` and turns `python -m pytest -q`, a declared CI command, red. `README.md` is therefore an Affected File, not an afterthought.

The second is content: `test_no_change_type_synonym` forbids a bare `change_type` identifier outside code fences in any doctrine, and `test_phase_xml_tag_case_matches_yaml` constrains phase-tag case. The new doctrine must observe both.

A repo-wide sweep for corpus invariants a new file can trip, run without a search-narrowing filter, returns exactly these two over `qor/references/` and none over `qor/scripts/`. The two tests that do scan every `.py` -- for a placeholder-hasher literal and for positional calls to keyword-only functions -- constrain the content of the new modules rather than the membership of any set.

**LD-6. Two records are `Implemented`; the roadmap record is `Accepted`.** Under LD-3, `Implemented` requires delivery in full.

Phase 240 sealed at entry #644 and its post-merge findings were closed by Phase 257, so its record is delivered in full. Phase 241 sealed at entry #649; its record describes a boundary whose downstream side the record itself declares out of scope, so `Implemented` means delivered in full on Qor-logic's side of that declared boundary, which is the only side this repository can deliver.

Phase 239 is different. Three artifacts agree that what shipped was a pilot, not the full meta capability the record proposes:

- `git show 9bb10b61:docs/SYSTEM_STATE.md | grep -nE 'Prior phase'` -> `13:**Prior phase**: Phase 239 (feature; governed promotion of the /qor-roadmap P1 pilot; v0.161.0; GH #373). The pilot reached main through its own two-iteration tribunal; PR #378 superseded; evaluation remains GH #373's next task.`
- `git show 9bb10b61:docs/META_LEDGER.md | grep -nE 'Entry #656'` -> `19481:### Entry #656: SESSION SEAL -- Phase 239 roadmap-pilot promotion GH #373 (v0.161.0)`

`docs/FEATURE_INDEX.md` line 38 carries FX027 as an experimental Roadmap pilot, and cannot be cited here by observed text because the row contains inline code formatting.

`Accepted` is true against all three and leaves the record honestly revisable when GH #373's evaluation closes. Since this phase removes every mechanism that could later re-examine a declared status, an overstatement would be permanent by construction.

**The stale ratification clause is retired, not preserved.** The record's status line asserts a formal `/qor-audit` is still required. It is not:

- `git show 9bb10b61:docs/META_LEDGER.md | grep -nE 'Entry #653'` -> `19426:### Entry #653: GATE TRIBUNAL -- Phase 239 roadmap-pilot promotion, iteration 1 (VETO)`
- `git show 9bb10b61:docs/META_LEDGER.md | grep -nE 'Entry #654'` -> `19446:### Entry #654: GATE TRIBUNAL -- Phase 239 roadmap-pilot promotion, iteration 2 (PASS)`

Under LD-3, `Accepted` means ratified by a gate, so carrying that clause into the body would stamp "ratified" over prose saying "not yet ratified". The body records that Phase 239's tribunal ratified the decision and cites entry #654; the clause is deleted as superseded fact.

### Changes

`qor/scripts/adr_contract.py` carries the vocabulary and three parsers. `qor/references/doctrine-decision-records.md` states the contract in prose: required fields, the closed vocabulary with a definition for each value per LD-3, the phase-binding rule, the `**Phase**` domain collision, and a labelled forward reference to the seal-drift rule Phase 259 adds.

Each record gains `**Phase:** NNN` immediately after `**Status:**` and a single-word status. Narrative the old status lines carried moves into the body rather than being deleted, except as LD-6 specifies for the roadmap record's superseded ratification clause.

All three carriers of the Tier 2 contract gain the column or the amended preamble. The live index also registers the new doctrine and advances `**Last Reviewed**`.

### Unit Tests

- `tests/test_adr_contract.py::test_normalize_status_round_trips_every_canonical_value` - forward round-trip over `CANONICAL_ADR_STATUSES`.
- `tests/test_adr_contract.py::test_normalize_status_rejects_values_outside_the_vocabulary` - inverse coverage: `normalize_status("Proposed for Phase 241")` and `normalize_status("")` both return `None`.
- `tests/test_adr_contract.py::test_parse_record_extracts_phase_and_status_as_separate_fields` - a fixture record yields `phase == 41` and `status == "Implemented"` from distinct fields.
- `tests/test_adr_contract.py::test_parse_record_does_not_infer_a_phase_from_the_status_line` - fixture `**Status:** Proposed for Phase 41` with no `**Phase:**` field yields `phase is None`.
- `tests/test_adr_contract.py::test_parse_tier_table_returns_one_row_per_data_line` - `parse_tier_table` over a three-column fixture yields the row and cell counts, exercising the parser rather than the document.
- `tests/test_adr_contract.py::test_tier_two_has_three_cells_in_both_index_and_template` - runs `parse_tier_table` over the real `docs/GOVERNANCE_INDEX.md` and `qor/templates/GOVERNANCE_INDEX.md`, asserting three cells per data row in each. Red today on both.
- `tests/test_adr_contract.py::test_every_decision_record_declares_a_phase_field` - runs `parse_record` over the real `docs/ADR_*.md`, asserts each yields an int phase. Red today on all three: `grep -c '^\*\*Phase' docs/ADR_*.md` returns 0 for each, and LD-1 forbids inferring the phase from the status line.
- `tests/test_adr_contract.py::test_every_declared_status_is_in_the_closed_vocabulary` - asserts `normalize_status` returns non-None for each real record's parsed status. Red today on all three.

## Phase 2: Decision-record conformance detector

### Affected Files

- `tests/test_adr_status_lint.py` NEW - detector behavior over synthetic fixtures
- `qor/scripts/adr_status_lint.py` NEW - the detector, importing `adr_contract`
- `qor/scripts/status_json.py` - register the check in `default_registry`
- `docs/FEATURE_INDEX.md` - append FX028

### Locked Decisions

**LD-7. Finding shape, CLI, and entry-point guard mirror `governance_index`.** A frozen `AdrFinding(kind, path, reason)`, `main(argv) -> int` with `--repo-root`, an `_emit` returning 1 on findings, and a module-foot `if __name__ == "__main__": raise SystemExit(main())`.

- `git show 9bb10b61:qor/scripts/governance_index.py | grep -nE 'class IndexFinding'` -> `34:class IndexFinding:`
- `git show 9bb10b61:qor/scripts/governance_index.py | grep -nE '^def _emit'` -> `215:def _emit(findings: list[IndexFinding], *, fail_closed: bool) -> int:`
- `git show 9bb10b61:qor/scripts/governance_index.py | grep -nE 'return 1 if findings'` -> `224:    return 1 if findings else 0`

The guard is not decoration. The CLI family dispatches by subprocess, so without it the module imports, runs nothing, and exits 0:

- `git show 9bb10b61:qor/cli.py | grep -nE 'subprocess.run'` -> `286:    completed = subprocess.run([sys.executable, "-m", target, *args.args])`
- `git show 9bb10b61:qor/cli.py | grep -nE 'for family in'` -> `266:    for family in ("reliability", "scripts"):`

**LD-8. Record discovery is `docs/ADR_*.md`, and two finding kinds, both ledger-free.** `find_findings(repo_root)` globs `docs/ADR_*.md` relative to `repo_root` and reads nothing else. The glob is stated because the Phase 2 fixture tests construct trees against it, and an unstated discovery rule would let those tests and the implementation drift apart.

| kind | condition |
|---|---|
| `adr-missing-phase` | no `**Phase:**` field, or a value that is not an integer |
| `adr-invalid-status` | no `**Status:**` field, or `normalize_status` returns `None` |

**LD-9. Ladder registration follows the existing `Check` rows and breaks no shape assertion.**

- `git show 9bb10b61:qor/scripts/status_json.py | grep -nE '^def default_registry'` -> `88:def default_registry(repo_root: Path) -> list[Check]:`
- `git show 9bb10b61:qor/scripts/status_json.py | grep -nE 'Check\(id='` -> `93:        Check(id="governance-health", module="qor.scripts.governance_health",`
- `git show 9bb10b61:tests/test_status_json.py | grep -nE 'len\(ids\)'` -> `80:    assert len(ids) >= 6`

The ladder's own test asserts a lower bound, so a seventh check is admissible by construction.

### Changes

`default_registry` gains `Check(id="adr-conformance", module="qor.scripts.adr_status_lint", argv=["--repo-root", root])`. Per GH #432 the nightly ladder's later steps are unreachable when the boundary step fails; tracked separately.

### Unit Tests

- `tests/test_adr_status_lint.py::test_record_without_a_phase_field_reports_missing_phase` - asserts one `adr-missing-phase` naming the path.
- `tests/test_adr_status_lint.py::test_record_with_a_non_integer_phase_reports_missing_phase` - `**Phase:** seventeen` yields the same kind rather than raising.
- `tests/test_adr_status_lint.py::test_record_without_a_status_field_reports_invalid_status` - the absent-field case routes to a finding rather than an exception.
- `tests/test_adr_status_lint.py::test_prose_status_reports_both_kinds_and_infers_no_phase` - `**Status:** Proposed for Phase 41` with no `**Phase:**` yields both kinds, and specifically no binding to 41.
- `tests/test_adr_status_lint.py::test_conformant_record_reports_nothing` - every canonical status in turn, each with a valid phase, yields zero findings. Covers all five values.
- `tests/test_adr_status_lint.py::test_discovery_ignores_a_non_adr_markdown_file` - a fixture tree holding both a malformed `docs/NOTES.md` and a malformed `docs/ADR_X.md` yields exactly one finding, naming the ADR. Asserting the count and the path rather than emptiness makes the negative non-vacuous on its own: a detector that found nothing at all would fail it, where an emptiness assertion would pass.
- `tests/test_adr_status_lint.py::test_main_exits_one_on_findings_and_zero_when_clean` - `main(["--repo-root", str(tmp)])` against a dirty then a clean fixture tree; asserts 1 then 0.
- `tests/test_adr_status_lint.py::test_cli_entrypoint_exits_one_on_a_dirty_tree` - runs `[sys.executable, "-m", "qor.scripts.adr_status_lint", "--repo-root", str(tmp)]` as a subprocess against a dirty tree and asserts returncode 1, then 0 against a clean tree. The only test exercising the dispatch path the CI command and FX028 name; `main()` called in-process cannot detect a missing entry-point guard.
- `tests/test_adr_status_lint.py::test_registry_check_runs_the_detector_and_reports_its_exit` - `status_json.run_check` on the registered `adr-conformance` check against a dirty fixture tree records exit 1, proving ladder membership by execution.
- `tests/test_adr_status_lint.py::test_detector_opens_no_ledger` - the fixture tree must contain a real `docs/META_LEDGER.md` so an `.is_file()` guard passes and any read is actually attempted; the test patches `Path.read_text`, `Path.open` and `builtins.open` to raise on any path whose name contains `META_LEDGER`, runs `find_findings`, and asserts it completes and still returns the fixture's findings. Four failure modes are closed: an absent fixture ledger would let a guard short-circuit before the patched read; `Path.open` binds `io.open` rather than `builtins.open`, so patching the latter alone leaves `path.open().read()` green; patching only `read_text` misses both; and asserting only completion would pass if nothing ran. An audit hook would cover more read paths but cannot be uninstalled, so one added mid-suite would persist and poison later tests that legitimately read the ledger.

## Definition of Done

### Deliverable: decision-record contract

- **D1**: Every decision record declares a machine-readable phase binding and a status drawn from a closed, defined vocabulary.
- **D2**: `qor/scripts/adr_contract.py` exposes `CANONICAL_ADR_STATUSES`, `normalize_status`, `parse_record`, `parse_tier_table`, and reads no ledger; all three `docs/ADR_*.md` carry `**Status:**` and `**Phase:**` as separate fields.
- **D3**: All three carriers of the Tier 2 contract carry the amended marker; `README.md` carries a doctrine-inventory row for the new doctrine; the `decision record` glossary entry lists `qor/skills/meta/qor-help/SKILL.md` in `referenced_by` and `phase binding field` lists two `.py` paths. The live index also registers the new doctrine and advances `**Last Reviewed**`; `Last Reviewed` is gate-checked at substantiate, the registration row is not checkable by any gate and is asserted rather than verified, per LD-4.
- **D4**: `test_every_decision_record_declares_a_phase_field`, `test_every_declared_status_is_in_the_closed_vocabulary`, and `test_tier_two_has_three_cells_in_both_index_and_template` pass, all red beforehand and red for the asserted reason, since Phase 1 owns every unit they call. `test_readme_lists_every_doctrine_file` and `test_doctrine_self_substantiates` stay green, which is what proves the README row and the non-empty `referenced_by` respectively.

### Deliverable: decision-record conformance detector

- **D1**: A record missing a phase binding or carrying a status outside the vocabulary is reported; a conformant record is not.
- **D2**: `qor/scripts/adr_status_lint.py` exposes `AdrFinding`, `find_findings(repo_root)`, `main(argv) -> int`, and an entry-point guard; reachable as `qor-logic scripts adr_status_lint`, proven by subprocess rather than asserted.
- **D3**: Registered in `status_json.default_registry`; `docs/FEATURE_INDEX.md` gains FX028.
- **D4**: `test_conformant_record_reports_nothing` covers all five statuses; `test_discovery_ignores_a_non_adr_markdown_file` pins the glob; `test_cli_entrypoint_exits_one_on_a_dirty_tree` proves the dispatch path by subprocess; `test_registry_check_runs_the_detector_and_reports_its_exit` proves ladder membership by running the check; `test_detector_opens_no_ledger` proves the ledger-free boundary against a fixture tree that does contain a ledger.

## Feature Inventory Touches

| entry_id | operation | test_path | test_descriptor |
|---|---|---|---|
| FX028 | NEW | tests/test_adr_status_lint.py | `qor-logic scripts adr_status_lint` exits 1 naming `adr-missing-phase` for a record with no phase field and `adr-invalid-status` for a status outside the vocabulary, and exits 0 when every record conforms |

## CI Commands

- `python -m pytest tests/test_adr_contract.py tests/test_adr_status_lint.py -v` - the two new suites; run twice to confirm determinism
- `python -m pytest tests/test_portable_governance_boundary.py tests/test_governance_index_doctrine.py tests/test_dogfood_glossary_coverage.py tests/test_readme_doctrine_inventory.py tests/test_terminology_unification.py tests/test_feature_index_citations_resolve.py tests/test_status_json.py -v` - every named live consumer of an edited file, run explicitly rather than relied on incidentally
- `python -m pytest -q` - full suite; no regression
- `python -m pytest tests/test_packaging_install.py -v -m integration` - packaging smoke, matching the nightly job
- `python -m qor.scripts.dependency_admission_lint` - dependency cooling-period check, matching the PR job
- `qor-logic scripts adr_status_lint --repo-root .` - exits 0 after the backfill
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase258-adr-contract-and-status-lint.md` - plan self-consistency
- `qor-logic governance-index --repo-root . --cross-check-ledger` - `Last Reviewed` freshness against the latest seal, and Tier 3 archival. It does not check registration; `cross_check_index_against_ledger` filters to `stale-tier1`
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain integrity
- `python -m qor.scripts.status_json --repo-root .` - the ladder carries the new check
- `ruff check .` - lint
