# Plan: Phase 30 - System-tier Topology + Hardening + Check-surface D/E

**change_class**: feature

**doc_tier**: system

**terms_introduced**:
- term: Check Surface D              | home: qor/references/doctrine-documentation-integrity.md
- term: Check Surface E              | home: qor/references/doctrine-documentation-integrity.md
- term: Session Rotation             | home: qor/references/doctrine-governance-enforcement.md
- term: Architecture Doc             | home: docs/architecture.md
- term: Lifecycle Doc                | home: docs/lifecycle.md
- term: Operations Doc               | home: docs/operations.md
- term: Policies Doc                 | home: docs/policies.md

**boundaries**:
- limitations:
  - Term-drift grep (check-surface D) is scope-fenced to `qor/references/`, `qor/gates/`, `qor/skills/`, `docs/`, `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, and `CHANGELOG.md`. Code files (`qor/scripts/*.py`, `tests/*.py`) are excluded because identifier usage is not canonical-term usage.
  - Check-surface E compares only exact-text definitions of the same term across files. Semantic similarity (paraphrase, contradiction) is out of scope; this is a prompt system, not an LLM embedding service.
  - Session rotation writes a new `session_id` to `.qor/session/current` at `/qor-substantiate` Step Z completion. Existing `.qor/gates/<old_sid>/` directory is preserved (not deleted); operators can archive or prune manually.
- non_goals:
  - Semantic conflict detection, NLP-based definition comparison, glossary-entry autocompletion.
  - Retroactive session rotation for Phase 28/29 artifacts (session `2026-04-17T2335-f284b9` stays as-is; it is the last hand-rotated session).
  - Full-content authoring for system-tier docs to match external best-practices guides; Phase 30 ships sufficient-content per doc, not exhaustive coverage.
  - Automated pruning of prior-phase gate artifacts.
- exclusions:
  - CI workflow files beyond the tag-fetch fix (`.github/workflows/*.yml` gets `fetch-tags: true` / `fetch-depth: 0`; no other CI changes).
  - Dist-compile invocation from skills other than `/qor-substantiate` Step 8.5 (new step; scoped to seal).
  - Backfill of `referenced_by:` for any glossary entry NOT introduced by Phase 28 (those are all already populated).

**Target Version**: next minor bump after v0.20.0 (governed by Step 7.5 of /qor-substantiate).

**Basis**: `RESEARCH_BRIEF.md` (Phase 28 recon; residual items) + Phase 28/29 implementation inventory + session-runtime observations (session-rotation gap, dist drift during seal, seal-step ordering) + CI runtime observation (`test_every_changelog_section_has_tag` failing in GitHub Actions due to shallow checkout without tags). Pre-plan doctrine check (SG-Phase29-A countermeasure) confirmed: `standard` tier passes cleanly at plan-authoring time; `system` tier will ABORT until Phase 3 authors `docs/{architecture,lifecycle,operations,policies}.md`. Phase 3 is sequenced to land these before Step 4.7 runs at seal.

## Open Questions

1. **Check-surface D scope fence**: plan assumes markdown-only scan (excludes `qor/scripts/*.py` and `tests/*.py`). Confirm before Phase 4; widening to code files has false-positive risk (identifier usage != canonical-term usage).
2. **Session rotation semantics**: on-seal (Step Z writes new session_id) vs on-plan (new session_id at `/qor-plan` Step 0.5). Plan assumes on-seal because substantiate is the natural "this session is done" moment. Confirm before Phase 1.
3. **System-tier doc content depth**: 150-250 lines each with real content drawn from existing repo state (e.g., `docs/architecture.md` synthesized from `qor/gates/chain.md` + `qor/scripts/` module list; `docs/lifecycle.md` from `/qor-*` skill catalog). Plan assumes substantial content. Confirm before Phase 3 if stub is preferred.
4. **Dist recompile placement**: Phase 1 adds `python -m qor.scripts.dist_compile` to `/qor-substantiate` Step 8.5 (between cleanup and report). Alternative is Step 9.5 (co-located with `git add`). Plan assumes 8.5. Confirm before Phase 1.

## Phase 1: Plumbing -- CI fix + seal ordering + session rotation + dist recompile

Close the four session-runtime gaps surfaced during Phase 28/29 plus the CI tag-fetch failure. No new doctrine introduced; existing skills gain small additions.

### Affected Files

- `tests/test_seal_flow_ordering.py` - NEW; asserts `bump_version` runs before `create_seal_tag` (mirroring `changelog_stamp.py` precedent) and fails on inverted order.
- `tests/test_session_rotation.py` - NEW; asserts Step Z rotates the session marker and writes the new `session_id` to `.qor/session/current`.
- `tests/test_session_rotation_glossary_entry_exists.py` - NEW; asserts the `Session Rotation` glossary entry parses with expected `home:` and non-empty `referenced_by:` (Ground 2 remediation from audit pass 1).
- `tests/test_dist_recompile_on_seal.py` - NEW; asserts `/qor-substantiate` Step 8.5 calls `dist_compile.compile_all`.
- `.github/workflows/*.yml` - MODIFY (grep-find the checkout steps); add `fetch-tags: true` or `fetch-depth: 0` to each `actions/checkout@v*` step so `git tag` is populated before `test_every_changelog_section_has_tag` runs.
- `qor/scripts/session.py` - MODIFY; add `rotate()` function that writes a new UTC-stamped session_id to `.qor/session/current` and returns it.
- `qor/references/doctrine-governance-enforcement.md` - MODIFY (Ground 2); add §7 (Session Rotation) defining the rotate-on-seal contract: when (Step Z post-write), how (`session.rotate()` writes a new `<YYYY-MM-DDTHHMM>-<6hex>` id), why (per-phase artifact archaeology), prior-session preservation (no pruning).
- `qor/references/glossary.md` - MODIFY (Ground 2); add `Session Rotation` entry with `home: qor/references/doctrine-governance-enforcement.md` and `referenced_by: [qor/scripts/session.py, qor/skills/governance/qor-substantiate/SKILL.md]`.
- `qor/skills/governance/qor-substantiate/SKILL.md` - MODIFY; (a) reorder Step 7.5 to call `bump_version` first, then `create_seal_tag` (fixes Phase 29's manual pyproject edit); (b) add Step 8.5 (Dist Recompile) invoking `python -m qor.scripts.dist_compile`; (c) extend Step Z to call `session.rotate()` after writing `substantiate.json`.

### Changes

**Seal-step ordering fix** (resolves Phase 29 manual workaround). Current Step 7.5 snippet:

```python
new_version = gh.bump_version(change_class)           # bumps pyproject
tag = gh.create_seal_tag(new_version, ...)
```

Current order is already correct in skill text; the Phase 29 drift was operator-level (I called `create_seal_tag` directly, bypassing `bump_version`). Fix: add a constraint line in `/qor-substantiate` Constraints section: "**ALWAYS** call `governance_helpers.bump_version` before `create_seal_tag`; never author tags manually." Test locks the contract.

**Session rotation** (Step Z new suffix):

```python
import session
gate_chain.write_gate_artifact(phase="substantiate", payload=payload, session_id=sid)
# Phase 30 wiring: rotate session so downstream plans do not carry prior-phase artifacts.
new_sid = session.rotate()
print(f"Session sealed. New session: {new_sid} (prior: {sid} preserved at .qor/gates/{sid}/)")
```

`session.rotate()` writes a new session_id of form `<YYYY-MM-DDTHHMM>-<6hex>` to `.qor/session/current`, leaving the prior session's `.qor/gates/<old_sid>/` directory intact for archaeology.

**Dist recompile Step 8.5**:

```markdown
### Step 8.5: Dist Recompile (Phase 30 wiring)

Rebuild variant outputs so Phase 30+ forward cannot seal with dist drift.

\`\`\`bash
python -m qor.scripts.dist_compile
\`\`\`

On any non-zero exit, ABORT substantiation; the operator must resolve the compile error and re-run seal.
```

**CI tag-fetch** (closes the reported failure). Each `actions/checkout` step in `.github/workflows/*.yml` gains either `with: fetch-tags: true` or `with: fetch-depth: 0`. Plan leaves to implementer which mechanism to use; both give the test suite access to git tags.

### Unit Tests

- `tests/test_seal_flow_ordering.py`:
  - `test_constraints_section_names_bump_before_tag` - greps substantiate SKILL.md Constraints section for the ordering rule.
  - `test_step_7_5_calls_bump_version_first` - parses Step 7.5 block and asserts `bump_version` appears before `create_seal_tag` in source order.
- `tests/test_session_rotation.py`:
  - `test_rotate_writes_new_session_id` - asserts `session.rotate()` returns a new id of the expected format.
  - `test_rotate_preserves_prior_session_dir` - prior `.qor/gates/<old_sid>/` remains after rotation.
  - `test_rotate_changes_marker_file` - `.qor/session/current` contents differ pre- and post-rotate.
- `tests/test_dist_recompile_on_seal.py`:
  - `test_step_85_section_present` - greps substantiate SKILL.md for the new Step 8.5 block.
  - `test_step_85_invokes_dist_compile` - asserts the bash block invokes `python -m qor.scripts.dist_compile`.
- `tests/test_session_rotation_glossary_entry_exists.py` (Ground 2):
  - `test_session_rotation_entry_in_glossary` - parses `qor/references/glossary.md`; asserts `Session Rotation` entry exists with non-empty `definition:`, `home:` pointing to `qor/references/doctrine-governance-enforcement.md`, and `referenced_by:` list containing `qor/scripts/session.py` and `qor/skills/governance/qor-substantiate/SKILL.md`.
  - `test_governance_enforcement_doctrine_has_session_rotation_section` - greps `qor/references/doctrine-governance-enforcement.md` for a section header matching `## 7.` or `## Session Rotation`; asserts body non-empty.

## Phase 2: Wayfinding -- CLAUDE.md + README + terminology

Close GAP-REPO-05 (orphan doctrines from entry point; bare-backtick paths) and GAP-REPO-06 (terminology drift: `change_class`/`change_type` + `<phase>` XML case).

### Affected Files

- `tests/test_wayfinding_discipline.py` - NEW; asserts CLAUDE.md uses markdown links (not bare backticks) for doctrine/gate paths, and README.md links to at least 10 of the ~30 doctrines.
- `tests/test_terminology_unification.py` - NEW; asserts `change_type` does not appear as a synonym for `change_class` in skill text or doctrines, and `<phase>` XML tags match the YAML frontmatter case.
- `CLAUDE.md` - MODIFY; bare-backtick paths to doctrines / gates become `[name](path)` markdown links.
- `README.md` - MODIFY; add a "Doctrines" section (or extend an existing one) listing the full doctrine + reference inventory as markdown links.
- `qor/skills/**/SKILL.md` - MODIFY (grep-targeted); replace any stray `change_type` with `change_class`, normalize `<phase>` XML tag to lowercase (matching YAML frontmatter).

### Changes

**CLAUDE.md link conversion**. Current line (example):

```
Full doctrines: `qor/references/doctrine-token-efficiency.md`, `qor/references/doctrine-test-discipline.md`, `qor/references/doctrine-governance-enforcement.md`.
```

Becomes:

```
Full doctrines: [token-efficiency](qor/references/doctrine-token-efficiency.md), [test-discipline](qor/references/doctrine-test-discipline.md), [governance-enforcement](qor/references/doctrine-governance-enforcement.md).
```

**README.md Doctrines section**. New section listing every `qor/references/doctrine-*.md` and `qor/references/patterns-*.md` and `qor/references/ql-*.md` as markdown links with a one-line purpose pulled from each file's header.

**Terminology normalization**. Grep-find and replace:

- `change_type` -> `change_class` in any skill or doctrine body (not in ledger entries; those are immutable historical records).
- `<phase>PLAN</phase>` (uppercase) -> `<phase>plan</phase>` (matching YAML `phase: plan`). Apply to every SKILL.md carrying an XML `<phase>` tag.

### Unit Tests

- `tests/test_wayfinding_discipline.py`:
  - `test_claude_md_uses_markdown_links_for_doctrines` - scans CLAUDE.md for backtick-wrapped `qor/references/doctrine-*.md` patterns; asserts none exist outside code fences.
  - `test_readme_lists_at_least_ten_doctrines` - counts `[anything](qor/references/doctrine-*.md)` matches in README.md; threshold 10.
- `tests/test_terminology_unification.py`:
  - `test_no_change_type_synonym` - scans `qor/skills/**/*.md` and `qor/references/*.md`; fails if `change_type` appears as a noun (allows contextual prose like "type of change" that is not `change_type`).
  - `test_phase_xml_tag_case_matches_yaml` - parses each SKILL.md; asserts `<phase>X</phase>` case matches YAML frontmatter `phase: X`.

## Phase 3: System-tier topology -- author the four required docs

Author `docs/{architecture,lifecycle,operations,policies}.md` with substantial content so Phase 30's own substantiate-time `doc_tier: system` check passes. Content synthesized from existing repo state (chain.md, skills catalog, doctrines, policies/*.cedar), not invented.

### Affected Files

- `tests/test_system_tier_docs_present.py` - NEW; asserts each of the four docs exists, is non-empty, and contains at least one link back into the rest of the governance docs.
- `docs/architecture.md` - NEW; ~200 lines. Sections: Layer inventory (gates/scripts/skills/references/policies), component relationships (who reads/writes what), layering rules, extension points.
- `docs/lifecycle.md` - NEW; ~200 lines. Sections: Phase sequence (research -> plan -> audit -> implement -> substantiate -> validate -> remediate), per-phase gate artifacts, delegation table summary, session model, branch model.
- `docs/operations.md` - NEW; ~200 lines. Sections: CLI usage (`qorlogic init/install/compile/verify-ledger`), seal ceremony operator runbook, failure recovery (gate override, session reset, ledger repair), CI considerations (tag fetch), dist-variant management.
- `docs/policies.md` - NEW; ~150 lines. Sections: Policy files inventory (`qor/policies/*.cedar`), OWASP enforcement mapping, NIST SSDF alignment, shadow-genome countermeasure catalog pointer, change_class + version bump contract pointer.
- `qor/references/glossary.md` - MODIFY; add `referenced_by:` on `Doctrine` entry to include the four new docs; author new entries for the four `Architecture Doc` / `Lifecycle Doc` / `Operations Doc` / `Policies Doc` terms (per this plan's `terms_introduced:`).

### Changes

**Content strategy** (not invented per SG-016 countermeasure; grounded in existing repo state):

- `architecture.md`: enumerate every module under `qor/` (scripts, references, gates, skills, policies, reliability) with one-line purpose and file-count. Reference `qor/gates/chain.md` for phase relationships. Diagram: ASCII box-and-arrow of the governance pipeline.
- `lifecycle.md`: extract the phase sequence from `chain.md` and expand each with the skill that owns it, the gate artifact written, the typical duration, and the verification gates. Reference `delegation-table.md` for handoffs.
- `operations.md`: document every `qorlogic` CLI subcommand (walk `qor/cli.py`); write a seal-ceremony runbook matching the substantiate SKILL's Step 7-9.6; document failure recovery per `skill-recovery-pattern.md`.
- `policies.md`: enumerate `qor/policies/*.cedar` with one-paragraph summaries; link to `doctrine-owasp-governance.md` and `doctrine-nist-ssdf-alignment.md`; summarize the change_class version-bump contract.

**Glossary extensions** per `terms_introduced:` at plan top-matter. Each of the four doc-term entries has `home:` pointing to its own doc and `referenced_by:` including `CLAUDE.md` (which Phase 2 already updated to list the four docs).

### Unit Tests

- `tests/test_system_tier_docs_present.py`:
  - `test_architecture_md_exists_and_nonempty` - file exists, > 50 lines.
  - `test_lifecycle_md_exists_and_nonempty` - same.
  - `test_operations_md_exists_and_nonempty` - same.
  - `test_policies_md_exists_and_nonempty` - same.
  - `test_each_system_doc_links_back` - each of the four must contain at least one markdown link into `qor/references/`, `qor/gates/`, or `qor/skills/` -- proves they are wired into the wayfinding graph, not isolated.
  - `test_system_tier_check_passes` - runs `doc_integrity.run_all_checks_from_plan({'doc_tier': 'system', 'terms': [...], 'plan_slug': 'phase30-system-tier-hardening'}, repo_root='.')` against the live repo; MUST pass post-Phase-3 (Phase 30's own Step 4.7 will run the same check at seal time).

## Phase 4: Check-surface D + E extensions

Extend `doc_integrity.py` with the two deferred check surfaces, wire them into `/qor-substantiate` Step 4.7 composite, and add corresponding doctrine updates.

### Affected Files

- `tests/test_check_surface_d.py` - NEW; covers term-drift grep (undeclared terms detected, scope fence respected, no false-positives on excluded dirs).
- `tests/test_check_surface_e.py` - NEW; covers cross-doc conflict detection (same term defined with different bodies across files).
- `tests/test_doc_integrity_razor_compliance.py` - NEW (Ground 1 remediation from audit pass 1); asserts `qor/scripts/doc_integrity.py` stays <=250 lines AND `qor/scripts/doc_integrity_strict.py` stays <=250 lines. Prevents cumulative Razor creep at module scope (SG-Phase30-A countermeasure).
- `qor/scripts/doc_integrity_strict.py` - NEW (Ground 1 remediation); sibling module hosting Phase 4 check functions. Public API: `check_term_drift(glossary_path, scan_roots, repo_root, strict=False)` (surface D) and `check_cross_doc_conflicts(glossary_path, scan_roots, repo_root, strict=False)` (surface E). Both raise `ValueError` on violation when `strict=True`; lenient mode returns list of drift findings without raising. Module also owns the `_STRICT_SCAN_ROOTS` and `_STRICT_EXCLUDE_SUFFIXES` scope-fence constants. Keeps `doc_integrity.py` under the Razor limit.
- `qor/scripts/doc_integrity.py` - MODIFY (minimal); add a 3-line `run_all_checks_from_plan` extension that imports `doc_integrity_strict` on-demand and routes to its checks when `strict: bool = False` kwarg is passed. No other changes to this file.
- `qor/references/doctrine-documentation-integrity.md` - MODIFY; promote D and E from "out of scope" to "optional strict mode" in §3 Check surface table; add §3.1 explaining the scope fence and the `strict:` kwarg; cite `qor/scripts/doc_integrity_strict.py` as the implementation home.
- `qor/references/glossary.md` - MODIFY; add `Check Surface D` and `Check Surface E` entries per plan top-matter `terms_introduced:` with `home: qor/references/doctrine-documentation-integrity.md` and `referenced_by: [qor/scripts/doc_integrity_strict.py]`.

### Changes

**`check_term_drift` (surface D)**. Scan in-scope markdown files for canonical terms from the glossary. Flag usage where the term appears with its exact canonical casing but the file is NOT listed in that term's `referenced_by:`. Non-strict mode returns drift list (informational); strict mode raises.

**`check_cross_doc_conflicts` (surface E)**. For every glossary term, grep in-scope files for sentences where the term is defined (pattern: `<Term> is|means|refers to`). Compare the extracted definition against the glossary entry's canonical `definition:`. Non-exact match flags a conflict. Strict mode raises.

**Scope fence** (applies to both D and E): include `qor/references/`, `qor/gates/`, `qor/skills/`, `docs/`, `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, `CHANGELOG.md`. Exclude all `*.py`, `*.json`, `*.toml`, and `qor/vendor/` (mirrors `test_yaml_safe_load_discipline.py` scope-fence pattern).

**`strict:` keyword arg**. Phase 30 ships surfaces D and E as lenient-by-default (drift detected but advisory) so existing plans continue to pass. Future phases can flip `strict=True` after verifying repo hygiene.

### Unit Tests

- `tests/test_check_surface_d.py`:
  - `test_term_drift_flags_undeclared_usage` - synthetic repo; term `Foo` exists in glossary with `referenced_by: [README.md]`; term appears in `docs/other.md`; drift detected.
  - `test_term_drift_respects_scope_fence` - term appears in `qor/scripts/code.py`; drift NOT reported (code files excluded).
  - `test_term_drift_lenient_mode_does_not_raise` - default `strict=False` returns drift list.
  - `test_term_drift_strict_mode_raises` - `strict=True` raises `ValueError` on the first drift.
- `tests/test_check_surface_e.py`:
  - `test_conflict_detects_divergent_definition` - term defined with one sentence in glossary, a different sentence in `docs/architecture.md`; conflict detected.
  - `test_conflict_scope_fence` - divergent definition in `qor/scripts/code.py`; NOT detected.
  - `test_conflict_lenient_mode_does_not_raise` - default behavior.
  - `test_conflict_strict_mode_raises` - `strict=True` raises.
- `tests/test_doc_integrity_razor_compliance.py` (Ground 1):
  - `test_doc_integrity_core_under_250` - asserts `qor/scripts/doc_integrity.py` stays <=250 lines. Guards against future additive creep (SG-Phase30-A countermeasure).
  - `test_doc_integrity_strict_under_250` - asserts `qor/scripts/doc_integrity_strict.py` stays <=250 lines.
  - `test_strict_module_import_surface` - imports `doc_integrity_strict` and asserts `check_term_drift` and `check_cross_doc_conflicts` are callable public names.

## CI Commands

Validate all four phases via:

- `python -m pytest tests/test_seal_flow_ordering.py tests/test_session_rotation.py tests/test_dist_recompile_on_seal.py -v` (Phase 1).
- `python -m pytest tests/test_wayfinding_discipline.py tests/test_terminology_unification.py -v` (Phase 2).
- `python -m pytest tests/test_system_tier_docs_present.py -v` (Phase 3).
- `python -m pytest tests/test_check_surface_d.py tests/test_check_surface_e.py -v` (Phase 4).
- `python -m pytest tests/ 2>&1 | tail -3` (full suite regression; target `553+ passed`).
- `python qor/reliability/skill-admission.py qor-substantiate` (confirms Step 8.5 + Step Z rotation insertion did not break admission).
- `python qor/reliability/gate-skill-matrix.py` (no broken handoffs after doctrine cross-links added).
- `python -c "import sys; sys.path.insert(0, 'qor/scripts'); import doc_integrity; plan = {'doc_tier':'system','terms':[...],'plan_slug':'phase30-system-tier-hardening'}; doc_integrity.run_all_checks_from_plan(plan, repo_root='.')"` (self-check: Phase 30 must pass Step 4.7 at seal with `system` tier).

Each phase's tests must pass on two consecutive runs before the phase is marked complete.

## Self-Dogfood

Per SG-Phase28-A (apply the doctrine to its own plan) + SG-Phase29-A (run helpers before writing):

- **Pre-plan doctrine check**: ran `doc_integrity.run_all_checks_from_plan` with `doc_tier: standard` and `doc_tier: system`. Standard passed; system ABORTed on missing `docs/architecture.md` (expected -- Phase 3 authors it).
- **`doc_tier` declaration**: `system` at top-matter. Phase 3 delivers the prerequisites before Step 4.7 runs at seal. If Phase 3 fails to deliver, Step 4.7 correctly ABORTs.
- **`terms_introduced` block populated**: 7 new terms (Check Surface D/E, Session Rotation, 4 doc-name entries). Each has a `home:` path.
- **`boundaries` block populated**: limitations + non_goals + exclusions each carry non-trivial entries.
- **Every new rule has a test**:
  - Seal ordering -> `test_constraints_section_names_bump_before_tag`.
  - Session rotation -> `test_rotate_writes_new_session_id` + `test_rotate_preserves_prior_session_dir`.
  - Dist recompile on seal -> `test_step_85_invokes_dist_compile`.
  - CI tag fetch -> covered by the existing `test_every_changelog_section_has_tag` green in CI post-fix.
  - CLAUDE.md links -> `test_claude_md_uses_markdown_links_for_doctrines`.
  - Terminology unification -> `test_no_change_type_synonym` + `test_phase_xml_tag_case_matches_yaml`.
  - System-tier docs present -> `test_{architecture,lifecycle,operations,policies}_md_exists_and_nonempty` + `test_system_tier_check_passes`.
  - Check-surfaces D/E -> full test files `test_check_surface_d.py` + `test_check_surface_e.py`.
  - Razor anticipation (SG-Phase30-A countermeasure) -> `test_doc_integrity_razor_compliance` guards both `doc_integrity.py` and `doc_integrity_strict.py` at the 250-line cap.
  - Session Rotation glossary + doctrine authoring (SG-Phase30-B countermeasure) -> `test_session_rotation_glossary_entry_exists` asserts the entry + doctrine section both land.
- **Enumeration cross-check (items)**: plan declares 10 open items in the Basis section; the 4 phases deliver items as follows -- Phase 1 covers items 1, 7, 8, 9; Phase 2 covers items 2, 3; Phase 3 covers items 4, 10; Phase 4 covers items 5, 6. All 10 accounted for.
- **Enumeration cross-check (terms_introduced)** (SG-Phase30-B countermeasure): every term in the plan's top-matter `terms_introduced:` resolves to at least one phase's Affected Files edit authoring the glossary entry AND the home file. Audit:
  - `Check Surface D` -> Phase 4 authors glossary entry + `doctrine-documentation-integrity.md` §3.1 (declared home).
  - `Check Surface E` -> same as above.
  - `Session Rotation` -> Phase 1 authors glossary entry + `doctrine-governance-enforcement.md` §7 (declared home).
  - `Architecture Doc` -> Phase 3 authors `docs/architecture.md` (declared home) + glossary entry extension.
  - `Lifecycle Doc` -> Phase 3 authors `docs/lifecycle.md` + glossary.
  - `Operations Doc` -> Phase 3 authors `docs/operations.md` + glossary.
  - `Policies Doc` -> Phase 3 authors `docs/policies.md` + glossary.
  All 7 terms have a home-file edit AND a glossary edit in a concrete phase. No metadata-only declarations.
- **No bare-word YAML/TOML/JSON** requiring a safe-loader citation; Phase 30 touches markdown docs and existing helpers.
- **No schema change**: doc_integrity.py gains functions; no `qor/gates/schema/*.json` edits.

## Delegation

Per `qor/gates/delegation-table.md`:

- Plan complete -> `/qor-audit` (next phase).
- Phase 1 reveals that session rotation has broader implications (e.g., existing skills hard-code paths assuming a single session) -> halt and re-open dialogue; do not silently widen to a gate-chain rewrite.
- Phase 3 reveals that one of the four system-tier docs cannot be grounded in existing repo state (e.g., `operations.md` requires content the repo does not yet expose) -> halt and invoke `/qor-research` for that doc only; do not invent content per SG-016 countermeasure.
- Phase 4 reveals that check-surface D's false-positive rate is too high even in lenient mode to ship -> narrow the scope fence further or defer strict-mode wiring; do NOT ship a flaky detector.
