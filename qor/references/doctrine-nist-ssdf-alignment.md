# Doctrine: NIST SP 800-218A (SSDF) Alignment

Reference mapping between Qor-logic governance lifecycle phases and NIST Secure Software Development Framework practices. This is an alignment mapping, not a compliance certification claim.

AI-specific augmentations from SP 800-218A (the AI-focused addendum) are noted where applicable.

## PO -- Prepare the Organization

| SSDF Practice | Qor-logic Equivalent | Path |
|---|---|---|
| PO.1.1 -- Define security requirements | `/qor-bootstrap` project initialization | `qor/skills/meta/qor-bootstrap/SKILL.md` |
| PO.1.2 -- Implement roles and responsibilities | Delegation table + skill handoff matrix | `qor/gates/delegation-table.md` |
| PO.1.3 -- Implement supporting toolchains | `CLAUDE.md` + doctrine files | `CLAUDE.md`, `qor/references/doctrine-*.md` |
| PO.1.4 -- Define criteria for software security checks | Gate chain definitions | `qor/gates/chain.md` |

AI augmentation (SP 800-218A): `/qor-bootstrap` detects host LLM and configures governance scope, ensuring AI-assisted development operates within defined security boundaries from project inception.

## PS -- Protect the Software

| SSDF Practice | Qor-logic Equivalent | Path |
|---|---|---|
| PS.1.1 -- Protect all forms of code | Shadow genome integrity monitoring | `qor/references/doctrine-shadow-genome-countermeasures.md` |
| PS.2.1 -- Archive and protect each release | `/qor-substantiate` Merkle seal + META_LEDGER | `docs/META_LEDGER.md` |
| PS.3.1 -- Protect integrity of development tools | Reliability scripts for CI/CD | `qor/reliability/` |
| PS.3.2 -- Monitor development infrastructure | `/qor-audit` gate tribunal | `qor/skills/governance/qor-audit/` |

AI augmentation (SP 800-218A): Process shadow genome (`docs/PROCESS_SHADOW_GENOME.md`) captures AI agent decision provenance, enabling audit trail reconstruction for AI-assisted changes.

## PW -- Produce Well-Secured Software

| SSDF Practice | Qor-logic Equivalent | Path |
|---|---|---|
| PW.1.1 -- Design software to meet security requirements | `/qor-plan` structured planning with grounding protocol | `qor/skills/sdlc/qor-plan/SKILL.md` |
| PW.4.1 -- Review and analyze human-readable code | `/qor-audit` adversarial code review | `qor/skills/governance/qor-audit/` |
| PW.5.1 -- Test executable code | Test discipline doctrine (TDD mandatory) | `qor/references/doctrine-test-discipline.md` |
| PW.7.1 -- Configure software to have secure settings | Cedar-inspired policy engine | `qor/policy/` |
| PW.9.1 -- Verify third-party components | `/qor-validate` + dependency checks | `qor/skills/governance/qor-validate/` |

AI augmentation (SP 800-218A): The `/qor-plan` -> `/qor-audit` -> `/qor-implement` -> `/qor-substantiate` pipeline enforces that AI-generated code passes the same governance gates as human-authored code. Policy evaluator provides machine-readable authorization for skill invocations.

## RV -- Respond to Vulnerabilities

| SSDF Practice | Qor-logic Equivalent | Path |
|---|---|---|
| RV.1.1 -- Identify and confirm vulnerabilities | `/qor-debug` root cause analysis | `qor/skills/sdlc/qor-debug/` |
| RV.1.2 -- Assess vulnerability severity | Process shadow genome threshold monitoring | `docs/PROCESS_SHADOW_GENOME.md` |
| RV.2.1 -- Analyze vulnerabilities to determine remediation | `/qor-remediate` course correction | `qor/skills/sdlc/qor-remediate/` |
| RV.3.1 -- Communicate vulnerability information | Shadow genome upstream reporting | `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` |

AI augmentation (SP 800-218A): Shadow genome countermeasures doctrine (`SG-016` through `SG-038`) catalogues AI-specific failure patterns and their mechanical mitigations, addressing the AI-introduced vulnerability surface described in SP 800-218A.

## Evidence Collection

Starting with Phase 23, ledger entries include `**SSDF Practices**: PW.1.1, PS.1.1` tags mapping each governance decision to the SSDF practice it satisfies. This transforms the alignment mapping above into verifiable evidence.

### How it works

1. Each `/qor-substantiate` seal adds SSDF practice tags to the ledger entry body.
2. `qor-logic compliance report` reads META_LEDGER.md, extracts practice tags, and reports coverage.
3. Coverage gaps (practices with zero entries) indicate areas where governance evidence is missing.

### Running the report

```
$ qor-logic compliance report
SSDF Practice Coverage:
  PO.1.1: 3 entries (Entry #14, Entry #31, Entry #45)
  PS.1.1: 5 entries (Entry #33, Entry #35, ...)
  PW.1.1: 12 entries
  RV.1.1: 2 entries
Coverage: 4 practice groups, 4 individual practices, 22 total tags
```

### Practice tag format

Tags use the SSDF practice ID format: `{GROUP}.{TASK}.{SUBTASK}` (e.g., `PW.1.1`, `PS.2.1`). Multiple practices per entry are comma-separated.

### Phase 52 wiring (forward-only emission)

Starting with Phase 52's SESSION SEAL entry, every SEAL entry carries `**SSDF Practices**: <tags>`. The tagger (`qor/scripts/ssdf_tagger.py`) computes practices from `change_class` + `files_touched` (derived via `git diff --name-only origin/main...HEAD`).

**Grandfathering**: entries before Phase 52's seal do not carry tags. The Merkle chain is content-addressed and append-only; retroactive edits would invalidate the chain (Phase 47's `seal_entry_check` would reject the rebuild). `qor.cli compliance report` shows coverage starting from Phase 52's seal — this is forward-only by design.

**Operator workflow**: at `/qor-substantiate` Step 7.4, the skill runs `python -m qor.scripts.ssdf_tagger --change-class <c>` (no `python -c "...${VAR}..."` interpolation; SG-Phase47-A compliant) and pastes the printed tag line into the SESSION SEAL entry body before content_hash is computed in Step 7.

**Verification**: `qor.scripts.ledger_hash.extract_ssdf_practices(ledger_path)` parses any entry with the `**SSDF Practices**:` block and returns `{entry_num: [practices]}`. Round-trip integrity tested by `tests/test_ssdf_tagger.py::test_extract_ssdf_practices_round_trips_emitted_block`.
