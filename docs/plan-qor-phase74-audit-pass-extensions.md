# Plan: Phase 74 - qor-audit pass extensions (Infrastructure Alignment sixth bullet + Ghost UI Live-Progress Invariant)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #49 (Infrastructure Alignment third-party SDK + Postgres mechanism gap) + GH #58 (Ghost UI Live-Progress Invariant sub-rule).

**terms_introduced**:
- term: third-party SDK citation
  home: qor/skills/governance/qor-audit/SKILL.md
- term: behavioral-semantics claim
  home: qor/skills/governance/qor-audit/SKILL.md
- term: Live-Progress Invariant
  home: qor/skills/governance/qor-audit/SKILL.md
- term: SG-FakeProgress-A
  home: qor/references/doctrine-shadow-genome-countermeasures.md

**boundaries**:
- limitations:
  - V1 ships prose-only audit-pass extensions + 1 SG doctrine entry. The mechanical `plan_live_progress_lint.py` Python helper (per GH #58 reference implementation) is deferred to a follow-on phase pending operator demand from V1 deployment.
  - Behavioral-semantics claims (GH #49) accept inline documentation URLs with quoted text OR file:line citations to docs/types; the audit does not validate the citations programmatically -- operator judgment-based pass.
- non_goals:
  - No new `qor/scripts/plan_live_progress_lint.py`.
  - No new `findings_categories` enum values (the existing `ghost-ui` category absorbs the new sub-rule via prose sub-tagging; no schema change).
  - No `--check` CLI for the Live-Progress Invariant.
- exclusions:
  - No changes to `/qor-plan`, `/qor-implement`, `/qor-substantiate`, `/qor-debug`, `/qor-refactor`, `/qor-remediate`.
  - No CI workflow changes.

## Open Questions

None. Issues #49 + #58 specify acceptance criteria in detail; V1 lands the prose surface + SG doctrine entry; mechanical helpers deferred to V2.

## Phase 1: Infrastructure Alignment Pass sixth verification bullet (#49)

### Affected Files

- `qor/skills/governance/qor-audit/SKILL.md` - extend Infrastructure Alignment Pass with a sixth checklist bullet covering third-party SDK method/property citations + behavioral-semantics claims (Postgres mechanism behavior, supabase-js semantics, auth-schema mutability).
- `tests/test_qor_audit_third_party_sdk_check.py` - NEW. 2 tests asserting the audit SKILL.md Infrastructure Alignment Pass region names third-party SDK and behavioral-semantics claim requirements.

### Changes

Add a sixth bullet to the Infrastructure Alignment Audit checklist requiring:
- Every cited third-party SDK method/property exists in installed `node_modules/<package>/dist/*.d.ts` (or equivalent type declarations for the runtime: `pip show <pkg>` for Python, `Cargo.toml` + `cargo doc` for Rust) OR is explicitly quoted from official documentation with citation.
- Every cited behavioral-semantics claim (Postgres durability/concurrency/transaction semantics, supabase-js method behavior, auth-schema mutability) includes inline citation to upstream docs (URL + quoted text), upstream source (file:line), or in-repo precedent demonstrating the claimed behavior.

VETO category remains `infrastructure-mismatch` (existing enum value; no schema change required).

### Unit Tests

- `tests/test_qor_audit_third_party_sdk_check.py::test_infrastructure_alignment_names_third_party_sdk_check` - reads audit SKILL.md, asserts Infrastructure Alignment Pass region names third-party SDK citation requirement.
- `tests/test_qor_audit_third_party_sdk_check.py::test_infrastructure_alignment_names_behavioral_semantics_claim` - asserts the region names behavioral-semantics claim citation requirement (Postgres / SDK behavior).

## Phase 2: Ghost UI Live-Progress Invariant sub-rule (#58)

### Affected Files

- `qor/skills/governance/qor-audit/SKILL.md` - extend Ghost UI Pass with a Live-Progress Invariant sub-rule (4 checklist items per #58 acceptance criteria).
- `tests/test_qor_audit_live_progress_invariant.py` - NEW. 2 tests asserting the audit SKILL.md Ghost UI Pass region names the Live-Progress Invariant + fake-jump pattern.

### Changes

Append a Live-Progress Invariant sub-rule under the existing Ghost UI Pass:
- Every CSS animation or width transition driven by JS must have at least one intermediate state when the underlying operation takes >2 seconds.
- No `style.width = '0%'` immediately followed by `style.width = '100%'` with no intermediate writes (fake-jump pattern; SG-FakeProgress-A).
- Modals with progress UI MUST subscribe to the backing event stream (WebSocket / EventEmitter / etc.) and re-render on each event.
- Error UI must surface an explicit dismiss/retry control; modal must not trap the operator on a terminal error state.

VETO with `ghost-ui` category, sub-tag `live-progress-fake` (prose sub-tag; no schema enum change).

### Unit Tests

- `tests/test_qor_audit_live_progress_invariant.py::test_ghost_ui_pass_names_live_progress_invariant` - reads audit SKILL.md, asserts Ghost UI Pass region names the Live-Progress Invariant.
- `tests/test_qor_audit_live_progress_invariant.py::test_ghost_ui_pass_names_fake_jump_pattern` - asserts the region names the fake-jump pattern + SG-FakeProgress-A.

## Phase 3: SG-FakeProgress-A doctrine entry (#58)

### Affected Files

- `qor/references/doctrine-shadow-genome-countermeasures.md` - new SG-FakeProgress-A entry catalogueing the pattern, originating recurrence (a sibling product's v5.1.0 install-skills-card 0->100% fake jump over 20-60s wall-clock backing operation), and countermeasure (qor-audit Ghost UI Pass Live-Progress Invariant sub-rule).
- `tests/test_doctrine_sg_fake_progress_a.py` - NEW. 2 tests asserting the doctrine carries the SG entry with pattern description and countermeasure cross-reference.

### Changes

SG entry follows the standard format (Pattern / Originating recurrence / Countermeasure / Cross-reference). Originating recurrence: a sibling product's Install QorLogic Skills card UX defect, two prior qor-audit PASS cycles missed it (the sibling product's META_LEDGER #361 + #362).

### Unit Tests

- `tests/test_doctrine_sg_fake_progress_a.py::test_doctrine_carries_sg_fake_progress_a` - reads doctrine file, asserts `SG-FakeProgress-A` entry exists with the canonical pattern description (fake-jump + progress-bar 0->100% without intermediate state).
- `tests/test_doctrine_sg_fake_progress_a.py::test_doctrine_cites_countermeasure` - asserts the SG entry body cross-references the Ghost UI Pass Live-Progress Invariant countermeasure in qor-audit SKILL.md.

## CI Commands

- `python -m pytest tests/test_qor_audit_third_party_sdk_check.py tests/test_qor_audit_live_progress_invariant.py tests/test_doctrine_sg_fake_progress_a.py -v` - validates Phase 74 tests.
- `python -m qor.scripts.dist_compile` - regenerates dist variants.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase74-audit-pass-extensions.md` - self-application.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite.
