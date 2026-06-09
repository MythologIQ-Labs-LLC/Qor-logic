# Feature Index

Per `qor/references/doctrine-feature-inventory.md`: one row per user-touchable feature, cross-
referenced to the test that proves it works. V1 (Phase 144) enumerates the `qor-logic` CLI command
surface -- the primary product features. Status is assigned honestly from real tests (`verified`
only where a behavioral test exists and passes; `unverified` where no dedicated test exists yet).
Rows append as the surface grows; the seal-time `feature_index_verify.tally()` pass guards against
`verified -> unverified` regression.

| ID | Name | Source-of-truth file:line | Doc citation | Test path | Verification status |
| --- | --- | --- | --- | --- | --- |
| FX001 | `qor-logic install` | qor/cli.py:151 | README.md (Quick start) | tests/test_cli_install_gemini.py | verified |
| FX002 | `qor-logic uninstall` | qor/cli.py:157 | README.md | tests/test_cli_install_gemini.py::test_gemini_uninstall_cleans_commands_dir | verified |
| FX003 | `qor-logic list` | qor/cli.py:162 | README.md | tests/test_cli_feature_index_backfill.py::test_do_list_available_enumerates_skills | verified |
| FX004 | `qor-logic init` | qor/cli.py:168 | qor/references/doctrine-governance-enforcement.md | tests/test_cli_init_scope.py | verified |
| FX005 | `qor-logic info` | qor/cli.py:177 | README.md | tests/test_cli_feature_index_backfill.py::test_do_info_prints_known_skill | verified |
| FX006 | `qor-logic compile` | qor/cli.py:179 | docs/ARCHITECTURE_PLAN.md | tests/test_compile.py | verified |
| FX007 | `qor-logic verify-ledger` | qor/cli.py:184 | qor/references/doctrine-governance-enforcement.md | tests/test_verify_ledger_cli.py | verified |
| FX008 | `qor-logic seed` | qor/cli.py:205 | qor/references/skill-recovery-pattern.md | tests/test_cli_seed.py | verified |
| FX009 | `qor-logic governance-health` | qor/cli.py:207 | qor/references/doctrine-prompt-resilience.md | tests/test_cli_governance_health.py | verified |
| FX010 | `qor-logic governance-index` | qor/cli.py:210 | qor/references/doctrine-governance-index.md | tests/test_governance_index.py | verified |
| FX011 | `qor-logic capabilities` | qor/cli.py:221 | qor/references/doctrine-governance-enforcement.md | tests/test_cli_capabilities.py | verified |
| FX012 | `qor-logic compliance report` | qor/cli_handlers/compliance.py:90 | qor/references/doctrine-nist-ssdf-alignment.md | tests/test_compliance_report_post_phase52.py | verified |
| FX013 | `qor-logic compliance enforce` | qor/compliance/enforce.py:73 | qor/references/downstream-enforcement-sdk.md | tests/test_compliance_enforce.py | verified |
| FX014 | `qor-logic policy check` | qor/cli.py:241 | qor/references/doctrine-prompt-injection.md | tests/test_policy.py | verified |
| FX015 | `qor-logic release` | qor/cli_handlers/release.py:24 | qor/references/release-and-tag-timing.md | tests/test_release_backends.py | verified |
| FX016 | `qor-logic reconcile` | qor/cli_handlers/reconcile.py | qor/references/doctrine-shadow-genome-countermeasures.md | tests/test_cli_reconcile.py | verified |
| FX017 | `qor-logic scripts` / `reliability` module dispatch | qor/cli.py:251 | qor/references/doctrine-governance-enforcement.md | tests/test_skill_active_env.py | verified |
