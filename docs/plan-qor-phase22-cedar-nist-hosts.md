# Plan: Phase 22 -- Cedar-Inspired Policy Engine + NIST SSDF Alignment + Host LLM Expansion

**change_class**: feature
**version**: 0.12.0 -> 0.13.0
**branch**: `phase/22-cedar-nist-hosts`
**baseline**: 298 passed, 4 deselected

## Track A -- Cedar-inspired policy evaluator (4 files)

1. `qor/policy/__init__.py` -- public API: `evaluate(request, policies, entities) -> Decision`
2. `qor/policy/types.py` -- data model: `EntityUID`, `Request`, `Decision`, `Policy`
3. `qor/policy/parser.py` -- parse Cedar subset (`permit`/`forbid`, `==`, `in`, `when`)
4. `qor/policy/evaluator.py` -- evaluate request against policy set; default-deny; forbid overrides permit

Policy files (2 files):

1. `qor/policies/gate_enforcement.cedar` -- permit/forbid on gate verdict
2. `qor/policies/skill_admission.cedar` -- permit on registered + has_frontmatter

CLI subcommand: `qorlogic policy check <request.json>`

Tests (12 tests in `tests/test_policy.py`):

1. `test_entity_uid_creation`
2. `test_request_creation`
3. `test_decision_enum`
4. `test_policy_creation`
5. `test_parser_permit_simple`
6. `test_parser_forbid_with_when`
7. `test_parser_unconstrained_principal`
8. `test_parser_in_constraint`
9. `test_evaluator_default_deny`
10. `test_evaluator_permit_match`
11. `test_evaluator_forbid_overrides_permit`
12. `test_evaluator_condition_evaluation`

## Track B -- NIST SP 800-218A alignment doctrine (1 file)

1. `qor/references/doctrine-nist-ssdf-alignment.md` -- maps PO/PS/PW/RV to QorLogic lifecycle

Tests (5 tests in `tests/test_nist_ssdf.py`):

1. `test_nist_ssdf_alignment_exists`
2. `test_po_section_present`
3. `test_ps_section_present`
4. `test_pw_section_present`
5. `test_rv_section_present`

## Track C -- Host LLM expansion + `qorlogic init` (3 files modified)

1. `qor/hosts.py` -- codex target resolved (not NotImplementedError); `register_host()` for extensibility
2. `qor/scripts/dist_compile.py` -- `emit_codex` now copies claude variant (identity for now)
3. `qor/cli.py` -- `init` subcommand; `policy check` subcommand; version bump to 0.13.0

Tests (8 tests in `tests/test_phase22_hosts.py`):

1. `test_codex_host_resolves`
2. `test_register_host_custom`
3. `test_register_host_overrides_builtin`
4. `test_init_writes_config`
5. `test_init_sdlc_profile`
6. `test_init_filesystem_profile`
7. `test_install_reads_config`
8. `test_policy_check_cli`

## File inventory

New files (9):

1. `qor/policy/__init__.py`
2. `qor/policy/types.py`
3. `qor/policy/parser.py`
4. `qor/policy/evaluator.py`
5. `qor/policies/gate_enforcement.cedar`
6. `qor/policies/skill_admission.cedar`
7. `qor/references/doctrine-nist-ssdf-alignment.md`
8. `tests/test_policy.py`
9. `tests/test_nist_ssdf.py`

Modified files (5):

1. `qor/hosts.py`
2. `qor/scripts/dist_compile.py`
3. `qor/cli.py`
4. `pyproject.toml`
5. `tests/test_phase22_hosts.py` (new)

Total new files: 10 (9 + 1 test file for Track C)
Total modified files: 4

## Success criteria

- 298 + 25 = 323 tests passing (12 + 5 + 8 = 25 new)
- `qorlogic policy check <request.json>` evaluates a JSON request against `.cedar` policies
- `qorlogic init --profile sdlc --host claude` writes `.qorlogic/config.json`
- Codex host resolves without NotImplementedError
- `register_host("cursor", factory)` works for third-party hosts
- `python -m build` clean
- All files < 250 lines, all functions < 40 lines

## SG-038 lockstep verification

- Track A tests: 12 items enumerated, 12 in list = MATCH
- Track B tests: 5 items enumerated, 5 in list = MATCH
- Track C tests: 8 items enumerated, 8 in list = MATCH
- Total: 25 new tests claimed, 12 + 5 + 8 = 25 = MATCH
- New files: 10 enumerated (9 + 1), 10 in inventory = MATCH
- Modified files: 4 enumerated, 4 in list = MATCH
