# Qor-logic Glossary

Canonical term registry. Each entry is a YAML fence with required fields
`term`, `definition`, `home`; optional `aliases`, `referenced_by`,
`introduced_in_plan`. Parsed by `qor/scripts/doc_integrity.py` using
`yaml.safe_load`.

An entry is simultaneously a term definition AND a concept map entry: `home:`
names the authoritative file for the concept; `referenced_by:` names the
consumers. No separate concept-map artifact exists.

Phase 28 bootstrap scope: five foundational terms. Full Qor-logic terminology
(`Phase`, `Gate`, `Shadow Genome`, etc.) lands in Phase 3 dogfood expansion.

---

```yaml
term: Doctrine
definition: A canonical rule document in qor/references/ that skills cite as authority. Doctrines are binding on the phases that cite them; they evolve through plans, not ad-hoc edits.
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - CLAUDE.md
  - qor/gates/delegation-table.md
  - qor/skills/sdlc/qor-plan/SKILL.md
  - qor/skills/sdlc/qor-plan/references/step-extensions.md
  - qor/skills/memory/log-decision.md
  - qor/skills/memory/track-shadow-genome.md
  - qor/skills/meta/qor-meta-log-decision/SKILL.md
  - qor/skills/meta/qor-meta-track-shadow/SKILL.md
  - CONTRIBUTING.md
  - docs/architecture.md
  - docs/lifecycle.md
  - docs/operations.md
  - docs/policies.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Doc Tier
definition: A per-plan declaration (minimal, standard, system, or legacy) that selects which documentation artifacts are required at substantiate time.
home: qor/references/doctrine-documentation-integrity.md
aliases:
  - doc_tier
referenced_by:
  - qor/skills/sdlc/qor-plan/SKILL.md
  - qor/gates/schema/plan.schema.json
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Glossary Entry
definition: A YAML-fence record in qor/references/glossary.md defining one canonical term and naming its concept home.
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - qor/scripts/doc_integrity.py
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Concept Home
definition: The file path where a concept is canonically defined. Every glossary entry declares its home; orphan detection verifies the path resolves.
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - qor/references/glossary.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Orphan Concept
definition: A glossary entry with no referenced_by consumers that was not introduced in the current session's plan. Detected by check_orphans and raises at substantiate time.
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - qor/scripts/doc_integrity.py
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Doc Integrity Check Surface
definition: The three checks performed by doc_integrity.py at substantiate time -- topology presence, glossary hygiene, orphan scan. Term-drift grep (D) and cross-doc conflict detection (E) are documented as out-of-scope extensions.
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - qor/references/doctrine-documentation-integrity.md
introduced_in_plan: phase28-documentation-integrity
```

## Qor-logic canonical terms (Phase 28 Phase 3 dogfood expansion)

Closes GAP-REPO-02/03/04 from `RESEARCH_BRIEF.md`: the three-way "Phase" ambiguity, the missing glossary, and the Shadow Genome three-way split.

```yaml
term: Phase (SDLC)
definition: One stage in the governance lifecycle -- research, plan, audit, implement, substantiate, validate, or remediate. Governed by qor/gates/chain.md. Not to be confused with skill-step "Phase N" (plan-internal structure) or execution-stage labels like TDD / BUILD / CLEANUP.
home: qor/gates/chain.md
referenced_by:
  - CLAUDE.md
  - qor/gates/delegation-table.md
  - docs/META_LEDGER.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Gate
definition: A prior-phase artifact check at the boundary between two SDLC phases. Implemented by gate_chain.check_prior_artifact; override permitted but logged as severity-1 shadow event.
home: qor/gates/chain.md
aliases:
  - Gate Artifact
referenced_by:
  - qor/skills/sdlc/qor-plan/SKILL.md
  - qor/skills/sdlc/qor-implement/SKILL.md
  - qor/skills/sdlc/qor-refactor/SKILL.md
  - qor/skills/sdlc/qor-remediate/SKILL.md
  - qor/skills/governance/qor-audit/SKILL.md
  - qor/skills/governance/qor-substantiate/SKILL.md
  - qor/skills/governance/qor-validate/SKILL.md
  - qor/skills/meta/qor-repo-audit/SKILL.md
  - qor/skills/meta/qor-repo-release/SKILL.md
  - qor/skills/meta/qor-repo-scaffold/SKILL.md
  - qor/skills/memory/qor-document/SKILL.md
  - qor/skills/meta/qor-ab-run/SKILL.md
  - qor/skills/sdlc/qor-research/SKILL.md
  - qor/skills/governance/qor-audit/references/qor-audit-templates.md
  - qor/references/doctrine-nist-ssdf-alignment.md
  - qor/references/doctrine-governance-enforcement.md
  - qor/references/patterns-devops.md
  - qor/references/ql-audit-templates.md
  - qor/skills/sdlc/qor-ideate/SKILL.md
  - docs/architecture.md
  - docs/lifecycle.md
  - docs/operations.md
  - docs/policies.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Shadow Genome
definition: The event-logging substrate for governance-relevant observations (gate overrides, capability shortfalls, degradations, repeated-VETO patterns). Structured events live in JSONL under qor/dist/.shadow/; narrative patterns with countermeasures live in this doctrine file.
home: qor/references/doctrine-shadow-genome-countermeasures.md
aliases:
  - Process Shadow Genome
referenced_by:
  - docs/SHADOW_GENOME.md
  - qor/scripts/shadow_process.py
  - qor/gates/chain.md
  - qor/gates/delegation-table.md
  - qor/skills/sdlc/qor-plan/SKILL.md
  - qor/skills/sdlc/qor-implement/SKILL.md
  - qor/skills/sdlc/qor-research/SKILL.md
  - qor/skills/sdlc/qor-refactor/SKILL.md
  - qor/skills/sdlc/qor-remediate/SKILL.md
  - qor/skills/governance/qor-audit/SKILL.md
  - qor/skills/governance/qor-shadow-process/SKILL.md
  - qor/skills/governance/qor-substantiate/SKILL.md
  - qor/skills/governance/qor-validate/SKILL.md
  - qor/skills/governance/qor-process-review-cycle/SKILL.md
  - qor/skills/governance/qor-audit/references/qor-audit-templates.md
  - qor/skills/meta/qor-help/SKILL.md
  - qor/skills/meta/qor-meta-track-shadow/SKILL.md
  - qor/skills/memory/track-shadow-genome.md
  - docs/architecture.md
  - docs/lifecycle.md
  - docs/operations.md
  - docs/policies.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Substantiate
definition: The final governance phase that verifies Reality equals Promise, bumps version, stamps changelog, and produces the session's Merkle seal.
home: qor/skills/governance/qor-substantiate/SKILL.md
aliases:
  - Seal
referenced_by:
  - qor/gates/chain.md
  - qor/references/doctrine-governance-enforcement.md
  - qor/references/doctrine-procedural-fidelity.md
  - qor/references/ql-substantiate-templates.md
  - qor/skills/governance/qor-substantiate/references/qor-substantiate-templates.md
  - docs/lifecycle.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Workflow Bundle
definition: A meta-skill that orchestrates a sequence of single-purpose skills under one trigger, with declared checkpoints and a budget for graceful abort.
home: qor/gates/workflow-bundles.md
referenced_by:
  - CLAUDE.md
  - qor/skills/meta/qor-deep-audit/SKILL.md
  - qor/skills/meta/qor-onboard-codebase/SKILL.md
  - qor/skills/governance/qor-process-review-cycle/SKILL.md
  - docs/lifecycle.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: change_class
definition: A per-plan declaration of version impact -- hotfix, feature, or breaking. Governs the version bump performed at substantiate time by governance_helpers.bump_version.
home: qor/references/doctrine-governance-enforcement.md
referenced_by:
  - CLAUDE.md
  - qor/skills/sdlc/qor-plan/SKILL.md
  - qor/skills/sdlc/qor-plan/references/step-extensions.md
  - qor/skills/governance/qor-substantiate/SKILL.md
  - docs/lifecycle.md
  - docs/operations.md
  - docs/policies.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Delegation Table
definition: The single source of truth for cross-skill handoffs. Skills name their successor skill explicitly per the table, never invent routing inline.
home: qor/gates/delegation-table.md
referenced_by:
  - CLAUDE.md
  - qor/references/doctrine-audit-report-language.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Complecting
definition: Rich Hickey's term for braiding independent concerns together (state with time, data with behavior, config with code). Qor-logic's /qor-plan skill treats complecting as a design smell to detect and unwind.
home: qor/skills/sdlc/qor-plan/SKILL.md
referenced_by:
  - qor/skills/sdlc/qor-plan/SKILL.md
introduced_in_plan: phase28-documentation-integrity
```

```yaml
term: Session Rotation
definition: Writing a fresh session_id to the session marker after /qor-substantiate Step Z completes, so the next /qor-plan starts with a clean .qor/gates/<session_id>/ directory. Prior session directories are preserved (not pruned) so per-phase gate-artifact archaeology survives across seals.
home: qor/references/doctrine-governance-enforcement.md
referenced_by:
  - qor/scripts/session.py
  - qor/skills/governance/qor-substantiate/SKILL.md
introduced_in_plan: phase30-system-tier-hardening
```

```yaml
term: Install Drift
definition: Divergence between qor/skills/**/SKILL.md source and the operator's installed copies (e.g., under .claude/skills/). Detected by SHA256 byte-match in qor/scripts/install_drift_check.py. Non-blocking WARN semantics; fix via `qor-logic install --host <host>`.
home: qor/references/doctrine-governance-enforcement.md
referenced_by:
  - qor/scripts/install_drift_check.py
  - qor/skills/sdlc/qor-plan/SKILL.md
introduced_in_plan: phase32-strict-enforcement
```

```yaml
term: Strict Mode
definition: The hard-blocking variant of Check Surface D and E invoked by /qor-substantiate Step 4.7 via run_all_checks_from_plan(..., strict=True). Any term-drift or cross-doc conflict raises ValueError and aborts seal. Lenient mode (default) returns finding list without raising and is used by the ad-hoc drift report CLI.
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - qor/scripts/doc_integrity.py
  - qor/scripts/doc_integrity_strict.py
  - qor/skills/governance/qor-substantiate/SKILL.md
introduced_in_plan: phase32-strict-enforcement
```

```yaml
term: Architecture Doc
definition: docs/architecture.md -- system-tier required document describing the layer stack (entry points, references, gates, skills, scripts, policies, artifacts) and layering rules. One of four docs a plan must cite at doc_tier=system.
home: docs/architecture.md
referenced_by:
  - CLAUDE.md
  - docs/lifecycle.md
  - docs/operations.md
  - docs/policies.md
introduced_in_plan: phase30-system-tier-hardening
```

```yaml
term: Lifecycle Doc
definition: docs/lifecycle.md -- system-tier required document describing the phase sequence, per-phase contracts, session model, branch model, version model, and gate-artifact chain.
home: docs/lifecycle.md
referenced_by:
  - CLAUDE.md
  - docs/architecture.md
  - docs/operations.md
introduced_in_plan: phase30-system-tier-hardening
```

```yaml
term: Operations Doc
definition: "docs/operations.md -- system-tier required document. Operator runbook covering CLI usage, seal ceremony, push/merge decisions, failure recovery, CI considerations, dist-variant management, and troubleshooting."
home: docs/operations.md
referenced_by:
  - CLAUDE.md
  - docs/architecture.md
  - docs/lifecycle.md
introduced_in_plan: phase30-system-tier-hardening
```

```yaml
term: Policies Doc
definition: "docs/policies.md -- system-tier required document. Enumerates qor/policies/*.cedar files, OWASP/NIST mappings, change_class contract, shadow-genome rubric, exception and escape paths."
home: docs/policies.md
referenced_by:
  - CLAUDE.md
  - docs/architecture.md
  - docs/lifecycle.md
introduced_in_plan: phase30-system-tier-hardening
```

```yaml
term: Check Surface D
definition: "Term-drift grep: scans markdown files in qor/references, qor/gates, qor/skills, docs, and root-level CLAUDE/CONTRIBUTING/README/CHANGELOG for canonical glossary terms used outside their declared referenced_by. Implemented by doc_integrity_strict.check_term_drift."
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - qor/scripts/doc_integrity_strict.py
  - docs/architecture.md
  - docs/operations.md
  - docs/lifecycle.md
introduced_in_plan: phase30-system-tier-hardening
```

```yaml
term: Check Surface E
definition: "Cross-doc conflict detection: scans in-scope markdown for sentences defining a glossary term (patterns like 'Term is X', 'Term means X') and flags bodies whose exact text diverges from the canonical glossary definition. Implemented by doc_integrity_strict.check_cross_doc_conflicts."
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - qor/scripts/doc_integrity_strict.py
introduced_in_plan: phase30-system-tier-hardening
```

```yaml
term: release_docs
definition: "README.md and CHANGELOG.md -- user-facing narrative docs that carry release-specific claims. When plan.change_class is feature or breaking, check_documentation_currency requires both to appear in files_touched. Hotfix exempt."
home: qor/references/doctrine-documentation-integrity.md
referenced_by:
  - qor/scripts/doc_integrity_strict.py
  - qor/skills/governance/qor-substantiate/SKILL.md
introduced_in_plan: phase33-seal-tag-timing
```

```yaml
term: seal_tag_timing
definition: "The Phase 33 fix that moves create_seal_tag from /qor-substantiate Step 7.5 (pre-seal-commit, pointing at stale HEAD) to Step 9.5.5 (post-seal-commit, targeting the sealed SHA explicitly via required `commit` argument). Prevents the off-by-one tag drift observed across v0.19.0-v0.22.0."
home: qor/references/doctrine-governance-enforcement.md
referenced_by:
  - qor/scripts/governance_helpers.py
  - qor/skills/governance/qor-substantiate/SKILL.md
  - docs/SHADOW_GENOME.md
introduced_in_plan: phase33-seal-tag-timing
```



```yaml
term: prompt-injection canary
definition: "A regex pattern (six classes: instruction-redirect, role-redefinition, pass-coercion, meta-override, unicode-directionality, hidden-html) that detects attempts to embed LLM-subverting instructions inside operator-authored governance markdown. Frozen catalog at qor/scripts/prompt_injection_canaries.py CANARIES. Production audit scans without code-block masking; documentation scanning uses --mask-code-blocks. Closes OWASP LLM Top 10 (2025) LLM01 at the audit-prose layer."
home: qor/references/doctrine-prompt-injection.md
referenced_by:
  - qor/scripts/prompt_injection_canaries.py
  - qor/policies/owasp_enforcement.cedar
  - qor/policy/resource_attributes.py
  - qor/skills/governance/qor-audit/SKILL.md
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase53-prompt-injection-defense
```

```yaml
term: untrusted-data quarantine
definition: "The discipline of treating operator-authored governance markdown (plan files, ledger, concept) as untrusted data when the trust boundary spans multiple authors. Realized at runtime via the canary scan invoked from /qor-audit Step 3 Prompt Injection Pass. The quarantine boundary is the canary scanner; content that passes the scan is admitted into LLM context."
home: qor/references/doctrine-prompt-injection.md
referenced_by:
  - qor/skills/governance/qor-audit/SKILL.md
  - qor/scripts/prompt_injection_canaries.py
introduced_in_plan: phase53-prompt-injection-defense
```

```yaml
term: instruction-anchor regex
definition: 'A multiline-anchored regex form (caret-Verdict-colon-whitespace-PASS-dollar with markdown-bold + colon/dash separator tolerance) used by qor.reliability.intent_lock._audit_has_pass to recognize a canonical PASS verdict line in an audit report. Replaces the pre-Phase-53 substring match (re.search VERDICT.*PASS) which admitted any audit body containing both substrings on the same line, including narrative prose. Closes OWASP (2021) LOW-4.'
home: qor/references/doctrine-prompt-injection.md
referenced_by:
  - qor/reliability/intent_lock.py
introduced_in_plan: phase53-prompt-injection-defense
```


```yaml
term: AI provenance manifest
definition: 'Phase 54 metadata embedded in each gate artifact JSON declaring system, version, host, model_family, human_oversight, and ts. Computed by qor.scripts.ai_provenance.build_manifest. Aggregated across a session via qor-logic compliance ai-provenance. Maps to EU AI Act Art. 13/50 transparency and NIST AI RMF MEASURE-2.1 / MANAGE-1.1 evidence-collection.'
home: qor/references/doctrine-eu-ai-act.md
referenced_by:
  - qor/scripts/ai_provenance.py
  - qor/gates/schema/_provenance.schema.json
  - qor/cli_handlers/compliance.py
introduced_in_plan: phase54-ai-provenance-and-act-alignment
```

```yaml
term: human-oversight signal
definition: 'The human_oversight enum field on the AI provenance manifest, valued pass / veto / override / absent. Records the operator decision at the gate this artifact represents. Maps to EU AI Act Art. 14 (human oversight) by giving each gate a machine-readable verdict-or-absence marker.'
home: qor/references/doctrine-eu-ai-act.md
referenced_by:
  - qor/scripts/ai_provenance.py
  - qor/gates/schema/_provenance.schema.json
introduced_in_plan: phase54-ai-provenance-and-act-alignment
```

```yaml
term: subagent tool scope
definition: 'Advisory frontmatter keys permitted_tools and permitted_subagents on each gate-checking SKILL.md declaring which Tools and which subagent types the skill is intended to invoke. Phase 54 is declarative-only; Phase 55 candidate wires Cedar-based admission enforcement. Maps to NIST AI RMF GV-6.1 / MG-3.1 third-party AI risk and OWASP LLM Top 10 LLM07 (Insecure Plugin Design).'
home: qor/references/doctrine-ai-rmf.md
referenced_by:
  - qor/skills/sdlc/qor-plan/SKILL.md
  - qor/skills/sdlc/qor-implement/SKILL.md
  - qor/skills/sdlc/qor-research/SKILL.md
  - qor/skills/governance/qor-audit/SKILL.md
  - qor/skills/governance/qor-substantiate/SKILL.md
  - qor/skills/governance/qor-validate/SKILL.md
introduced_in_plan: phase54-ai-provenance-and-act-alignment
```

```yaml
term: override-friction escalator
definition: 'Per-session count-based escalator at qor.scripts.override_friction. Threshold = 3 (symmetric with cycle-count escalator). When the gate_override count for a session reaches the threshold, qor.scripts.gate_chain.emit_gate_override raises OverrideFrictionRequired unless the caller passes justification of at least 50 chars. Closes OWASP LLM Top 10 LLM08 (Excessive Agency) strengthening and EU AI Act Art. 14 oversight.'
home: qor/references/doctrine-ai-rmf.md
referenced_by:
  - qor/scripts/override_friction.py
  - qor/scripts/gate_chain.py
  - qor/gates/schema/shadow_event.schema.json
  - qor/references/doctrine-governance-enforcement.md
introduced_in_plan: phase54-ai-provenance-and-act-alignment
```


```yaml
term: tool-scope policy
definition: 'Phase 55 Cedar admission rule pair on qor/policies/skill_admission.cedar that forbids skill invocations whose actual prose-cited Tool invocations or Agent(subagent_type=...) callsites exceed the declared permitted_tools / permitted_subagents YAML frontmatter allowlist. Resource attributes computed by qor.policy.resource_attributes.compute_skill_admission_attributes; enforcement at the qor.reliability.skill_admission helper layer (not harness Tool/Agent invocation). Closes OWASP LLM Top 10 LLM07 (Insecure Plugin Design) at the manifest layer; Phase 55 wires what Phase 54 declared advisory-only.'
home: qor/references/doctrine-ai-rmf.md
referenced_by:
  - qor/policies/skill_admission.cedar
  - qor/policy/resource_attributes.py
  - qor/reliability/skill_admission.py
introduced_in_plan: phase55-subagent-admission-and-supply-chain
```

```yaml
term: model-pinning frontmatter
definition: 'Per-skill YAML frontmatter keys model_compatibility (list of compatible model families) and min_model_capability (declared minimum capability tier from the ordered set haiku/sonnet/opus). Lint at qor.scripts.model_pinning_lint walks scoped skills and warns when the operator-running model falls below the declared minimum or is not in the compatibility list. WARN-only at /qor-plan Step 0.3 (Phase 54-style declarative-only rollout); Phase 56+ may promote to ABORT. Closes OWASP LLM Top 10 LLM05 (Supply Chain).'
home: qor/references/doctrine-ai-rmf.md
referenced_by:
  - qor/scripts/model_pinning_lint.py
  - qor/skills/sdlc/qor-plan/SKILL.md
introduced_in_plan: phase55-subagent-admission-and-supply-chain
```

```yaml
term: CycloneDX SBOM
definition: 'CycloneDX v1.5 Software Bill of Materials JSON document emitted by qor.scripts.sbom_emit at /qor-repo-release Step Z as a sidecar artifact at dist/sbom.cdx.json. Lists the Qor-logic root component plus skill, doctrine, and variant components with bom-ref, name, version, type, description, and a root-depends-on-all dependency edge. Path captured into the deliver gate payload as sbom_path. Maps to EU AI Act Art. 50 transparency-of-AI-generated-content surface; downstream operator inclusion in compliance packages.'
home: qor/references/doctrine-eu-ai-act.md
referenced_by:
  - qor/scripts/sbom_emit.py
  - qor/cli_handlers/release.py
  - qor/skills/meta/qor-repo-release/SKILL.md
introduced_in_plan: phase55-subagent-admission-and-supply-chain
```

```yaml
term: secret-scanning gate
definition: 'Phase 56 substantiate-time enforcement gate that runs qor.scripts.secret_scanner over the staged set before seal. BLOCKs on any detected secret (regex-based catalog with literal-substring allowlist) and aborts substantiation. Drives the previously dormant has_hardcoded_secrets Cedar attribute (rule on books since Phase 23). Closes OWASP LLM Top 10 LLM06 (Sensitive Information Disclosure) and NIST AI 600-1 §2.10. Wired into /qor-substantiate Step 4.6.5 with || ABORT semantics matching the existing reliability-sweep idiom.'
home: qor/references/doctrine-eu-ai-act.md
referenced_by:
  - qor/scripts/secret_scanner.py
  - qor/policy/resource_attributes.py
  - qor/skills/governance/qor-substantiate/SKILL.md
introduced_in_plan: phase56-secret-scanning-gate
```

```yaml
term: gitleaks-compatible findings
definition: 'JSON output format produced by qor.scripts.secret_scanner.to_gitleaks_json. Emits a list of objects each carrying Description, RuleID (the Pattern.name), File, Line, Match (redacted), Secret (redacted), and Tags (severity:N). Compatible with gitleaks v8 downstream tooling without requiring gitleaks itself. Default output path is dist/secrets.findings.json (parallels Phase 55 SBOM sidecar convention). Match and Secret fields always carry the redacted form (<first4>...<last2>) so the findings JSON may be committed/shared without leaking secrets.'
home: qor/references/doctrine-eu-ai-act.md
referenced_by:
  - qor/scripts/secret_scanner.py
  - qor/skills/governance/qor-substantiate/SKILL.md
introduced_in_plan: phase56-secret-scanning-gate
```

```yaml
term: gate_written hook
definition: 'Phase 57 non-authoritative observer event fired after every successful qor.scripts.gate_chain.write_gate_artifact call. Carries a frozen GateWrittenEvent payload (phase, session_id, artifact_path, payload_sha256, ts) to consumers via two channels: Python entry-points under the qor_logic.events.gate_written group, and project-local config at <root>/.qor/hooks.yaml (dotted-path or list-form subprocess argv). Hooks run synchronously on the calling thread AFTER the authoritative artifact is on disk; Exception is swallowed and JSONL-logged to <root>/.qor/hooks/hooks.log; KeyboardInterrupt and SystemExit propagate so operators retain Ctrl-C control. Closes the polling-vs-push gap that prompted PR #12.'
home: qor/references/doctrine-hook-contract.md
referenced_by:
  - qor/scripts/gate_hooks.py
  - qor/scripts/gate_chain.py
introduced_in_plan: phase57-gate-written-observer-channel
```

```yaml
term: hook contract
definition: 'Phase 57 doctrine specifying the gate_written hook event payload, dispatch order (entry-points then config-file), log format (JSONL one-line-per-fire), trust model (consumer-repo trust mirroring .github/workflows/ and .pre-commit-config.yaml), performance characteristics (sub-millisecond no-op when no hooks registered), and SIGINT-propagation invariant (except Exception not BaseException; Phase 57 fix vs. PR #12 origin per SG-BareExceptionSwallowsSignals-A). The contract is the public-API surface that downstream consumers (FailSafe-Pro and any future packages) depend on.'
home: qor/references/doctrine-hook-contract.md
referenced_by:
  - qor/scripts/gate_hooks.py
  - qor/scripts/gate_chain.py
  - CHANGELOG.md
introduced_in_plan: phase57-gate-written-observer-channel
```

```yaml
term: procedural-fidelity check
definition: 'Phase 58 static-analysis pass at /qor-substantiate Step 4.6.6 that verifies the seal commit''s surface coverage matches the doc-surface coverage rule. Reads .qor/gates/<sid>/implement.json files_touched; runs four detectors (doc-surface-uncovered active in v1; missing-step, ordering-drift, argv-shape-divergence stubs reserved for future phases). WARN posture: deviations append severity-2 events to the Process Shadow Genome via shadow_process.append_event but do NOT abort substantiate. Closes B23 (operator request from Phase 57 substantiate cycle).'
home: qor/references/doctrine-procedural-fidelity.md
referenced_by:
  - qor/scripts/procedural_fidelity.py
  - qor/skills/governance/qor-substantiate/SKILL.md
introduced_in_plan: phase58-procedural-fidelity-and-tech-debt-wrapup
```

```yaml
term: procedural deviation
definition: 'A finding emitted by the Phase 58 procedural-fidelity check. Frozen Deviation dataclass with (deviation_class, severity, step_id, description, files_referenced) fields. The deviation_class is one of the four values in the frozen DEVIATION_CLASSES catalog (doc-surface-uncovered, missing-step, ordering-drift, argv-shape-divergence). Severity is rule-based (3 missing-step, 2 doc-surface-uncovered + argv-shape-divergence, 1 ordering-drift). Each deviation also appends a severity-N procedural_deviation event to the Process Shadow Genome.'
home: qor/references/doctrine-procedural-fidelity.md
referenced_by:
  - qor/scripts/procedural_fidelity.py
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase58-procedural-fidelity-and-tech-debt-wrapup
```

```yaml
term: doc-surface coverage
definition: 'Phase 58 rule that any seal commit touching qor/skills/, qor/scripts/, qor/references/doctrine-, or qor/gates/schema/ paths MUST also update at least one of the four system-tier docs (docs/SYSTEM_STATE.md, docs/operations.md, docs/architecture.md, docs/lifecycle.md). Threshold is at-least-one; different phases legitimately affect different doc surfaces. Enforced by _detect_doc_surface_coverage in qor/scripts/procedural_fidelity.py and supplemented by tests/test_system_state_phase_coverage.py forward-only drift prevention (every META_LEDGER SESSION SEAL entry must have a corresponding SYSTEM_STATE.md heading).'
home: qor/references/doctrine-procedural-fidelity.md
referenced_by:
  - qor/scripts/procedural_fidelity.py
  - qor/skills/governance/qor-substantiate/SKILL.md
  - tests/test_system_state_phase_coverage.py
introduced_in_plan: phase58-procedural-fidelity-and-tech-debt-wrapup
```

```yaml
term: ideation phase
definition: 'Phase 59 optional pre-research SDLC phase. Skill /qor-ideate writes .qor/gates/<sid>/ideation.json validated against qor/gates/schema/ideation.schema.json. Advisory-gate posture: /qor-research and /qor-plan accept either ideation OR research as their prior artifact via gate_chain.check_prior_artifact extension. Hotfixes MAY skip ideation. Captures intent and assumptions before they become inferred by downstream agents; closes Issue #20.'
home: qor/references/doctrine-ideation-readiness.md
referenced_by:
  - qor/skills/sdlc/qor-ideate/SKILL.md
  - qor/skills/meta/qor-help/SKILL.md
  - qor/scripts/gate_chain.py
  - qor/gates/chain.md
introduced_in_plan: phase59-ideation-readiness-phase
```

```yaml
term: spark record
definition: 'First section of the ideation artifact. Captures the originating signal before it becomes over-compressed into requirements language. Required fields: spark.observation (what was noticed), spark.initial_question (the question raised), spark.why_now (recurrence/deadline/strategic charge that makes the signal worth preserving today). Schema-enforced via qor/gates/schema/ideation.schema.json.'
home: qor/references/doctrine-ideation-readiness.md
referenced_by:
  - qor/skills/sdlc/qor-ideate/SKILL.md
  - qor/skills/sdlc/qor-ideate/references/dialogue-protocol.md
introduced_in_plan: phase59-ideation-readiness-phase
```

```yaml
term: problem frame
definition: 'Second section of the ideation artifact. Defines the actual failure mode without prescribing a solution. Required fields: problem_frame.affected_actors (list of users/systems affected), problem_frame.failure_mode (what goes wrong), problem_frame.cost_of_failure (operator hours, lost work, etc.). Anti-pattern guard for SG-PrematureSolutioning-A: skill REFUSES to advance to Transformation Statement until problem_frame is populated.'
home: qor/references/doctrine-ideation-readiness.md
referenced_by:
  - qor/skills/sdlc/qor-ideate/SKILL.md
  - qor/skills/meta/qor-help/SKILL.md
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase59-ideation-readiness-phase
```

```yaml
term: transformation statement
definition: 'Third section of the ideation artifact. Single-sentence statement of the desired change. Form: [Actor] moves from [current state] to [desired state] without [unacceptable cost]. Schema-enforced minLength=1 via qor/gates/schema/ideation.schema.json. Becomes the success definition that downstream substantiate refers back to (anti-pattern guard for validation-collapse).'
home: qor/references/doctrine-ideation-readiness.md
referenced_by:
  - qor/skills/sdlc/qor-ideate/SKILL.md
introduced_in_plan: phase59-ideation-readiness-phase
```

```yaml
term: assumption ledger
definition: 'Optional fourth section of the ideation artifact. Each entry: statement (text), category (user/market/technical/workflow/governance/operational/security/compliance), confidence (low/medium/high), impact_if_wrong (low/medium/high), validation_method (text), blocking (bool). Anti-pattern guard for assumption-laundering: tentative belief becoming requirement without evidence. Confidence + validation_method force explicit testing planning.'
home: qor/references/doctrine-ideation-readiness.md
referenced_by:
  - qor/skills/sdlc/qor-ideate/SKILL.md
  - qor/gates/schema/ideation.schema.json
introduced_in_plan: phase59-ideation-readiness-phase
```

```yaml
term: ideation readiness
definition: 'Tenth section of the ideation artifact. The readiness.status enum encodes the routing decision (ready / blocked / research_required / planning_advisory_only) and recommended_next_phase enum (research / plan / hold) determines downstream skill handoff. Status ready + research routes to /qor-research; status ready + plan routes to /qor-plan; status blocked remains in ideation; status research_required overrides recommended_next_phase to research; status planning_advisory_only routes to /qor-plan with advisory flag.'
home: qor/references/doctrine-ideation-readiness.md
referenced_by:
  - qor/skills/sdlc/qor-ideate/SKILL.md
  - qor/gates/delegation-table.md
introduced_in_plan: phase59-ideation-readiness-phase
```

```yaml
term: TAINTED entry
definition: 'A META_LEDGER entry whose own chain hash math is internally consistent but whose recorded previous_hash chains from a failed predecessor entry. Per Phase 66 (GH #54), `qor.scripts.ledger_hash.verify` reports such entries as `TAINTED Entry #N: depends on failed predecessor #M`. Math consistency alone is not trust; once an upstream FAIL poisons the chain root, every subsequent entry is tainted until the operator fixes the predecessor.'
home: qor/scripts/ledger_hash.py
referenced_by:
  - qor/skills/governance/qor-validate/SKILL.md
  - qor/references/doctrine-governance-enforcement.md
introduced_in_plan: phase66-qor-validate-integrity-bundle
```

```yaml
term: DISCLOSED_PRE_ANCHOR
definition: 'A META_LEDGER entry id at or below the operator-pinned (or auto-detected) post-anchor boundary whose chain math fails. Per Phase 66 (GH #55), `qor.scripts.ledger_hash.verify_post_anchor` reports such entries as `DISCLOSED_PRE_ANCHOR Entry #N: tolerated pre-boundary failure` and does NOT count them as errors. Used by consumer workspaces with sealed re-anchors that have documented pre-anchor edit clusters in their shadow genome.'
home: qor/scripts/ledger_hash.py
referenced_by:
  - qor/skills/governance/qor-validate/SKILL.md
  - qor/references/doctrine-governance-enforcement.md
introduced_in_plan: phase66-qor-validate-integrity-bundle
```

```yaml
term: post-anchor boundary
definition: 'The entry id partition between disclosed pre-anchor failures (tolerated) and the post-anchor surface (strict). Default: highest-numbered cleanly-verifying entry. Operator override via `--boundary N` on `qor-logic verify-ledger --post-anchor`. See `qor.scripts.ledger_hash.verify_post_anchor` for the auto-detection algorithm.'
home: qor/references/doctrine-governance-enforcement.md
referenced_by:
  - qor/scripts/ledger_hash.py
  - qor/skills/governance/qor-validate/SKILL.md
introduced_in_plan: phase66-qor-validate-integrity-bundle
```

```yaml
term: Infrastructure Citation Inventory
definition: 'A sub-section of /qor-plan Step 2 (Phase 72 wiring) that requires every Locked Decision citing sealed infrastructure (migration name, function signature, file:line reference, table schema, enum value, index/constraint name, env-var name, edge-function path) to carry a paired grep-evidence statement of the canonical form `git show <sealed-ref>:<path> | grep -nE ''<pattern>'' -> <exact observed text>`. Citations without paired evidence are Open Questions, not Locked Decisions, and block submission to /qor-audit. Closes SG-CitationDrift-A.'
home: qor/skills/sdlc/qor-plan/SKILL.md
referenced_by:
  - qor/skills/governance/qor-audit/SKILL.md
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase72-sg-citation-drift-countermeasure
```

```yaml
term: grep-evidence statement
definition: 'A one-line inline citation paired with each Locked Decision that references sealed infrastructure. Canonical form: `git show <sealed-ref>:<path> | grep -nE ''<pattern>'' -> <exact observed text>`. Documents the observed reality the LD is encoded against so downstream auditors and the next plan iteration can re-execute the same grep without re-reading the source. Required by /qor-plan Step 2 Infrastructure Citation Inventory; enforced by /qor-audit Step 3 Infrastructure Alignment Pass iter-N>1 full re-walk. Per Phase 72 (GH #56) SG-CitationDrift-A countermeasure.'
home: qor/skills/sdlc/qor-plan/SKILL.md
referenced_by:
  - qor/skills/governance/qor-audit/SKILL.md
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase72-sg-citation-drift-countermeasure
```

```yaml
term: Feature Inventory
definition: 'A tracked governance artifact (canonical name `FEATURE_INDEX.md`) enumerating every user-touchable feature of the product, cross-referenced against the test surface. One row per feature with columns `ID | Name | Source-of-truth file:line | Doc citation | Test path | Verification status`. Status enum: `verified | unverified | n/a`. Cross-referenced at /qor-substantiate Step 6 verification pass; counts surfaced in the SESSION SEAL ledger entry. Phase 73 wiring (GH #40).'
home: qor/references/doctrine-feature-inventory.md
referenced_by:
  - qor/skills/governance/qor-substantiate/SKILL.md
  - qor/skills/governance/qor-audit/SKILL.md
  - qor/skills/sdlc/qor-implement/SKILL.md
  - qor/skills/sdlc/qor-plan/SKILL.md
  - qor/references/doctrine-feature-tdd.md
introduced_in_plan: phase73-feature-inventory-tdd
```

```yaml
term: Feature Inventory Touches
definition: 'A required section in /qor-plan plan markdown (and `feature_inventory_touches` array in plan.json) listing every Feature Inventory entry the plan touches, with `entry_id`, `operation` (NEW/MODIFIED/n/a-justified), `test_path`, and `test_descriptor`. Consumed at /qor-audit Step 3 Feature Test Coverage Pass (VETO category `feature-test-undeclared`) and at /qor-implement Step 5 (per-feature TDD-Light). Phase 73 wiring (GH #41).'
home: qor/references/doctrine-feature-tdd.md
referenced_by:
  - qor/skills/sdlc/qor-plan/SKILL.md
  - qor/skills/governance/qor-audit/SKILL.md
  - qor/skills/sdlc/qor-implement/SKILL.md
introduced_in_plan: phase73-feature-inventory-tdd
```

```yaml
term: per-feature TDD
definition: 'Test-driven development discipline applied at user-touchable-feature scope. Distinct from per-unit TDD-Light (which operates on helpers/functions). For each entry in the plan''s `Feature Inventory Touches` table, the implementer authors the failing feature-level test first at the declared path with the declared assertion, runs it red, implements the feature, runs it green. Both per-unit and per-feature layers coexist in /qor-implement Step 5. Phase 73 wiring (GH #41).'
home: qor/references/doctrine-feature-tdd.md
referenced_by:
  - qor/skills/sdlc/qor-implement/SKILL.md
  - qor/skills/sdlc/qor-plan/SKILL.md
  - qor/skills/governance/qor-audit/SKILL.md
introduced_in_plan: phase73-feature-inventory-tdd
```

```yaml
term: feature-test-undeclared
definition: 'VETO findings category emitted by /qor-audit Step 3 Feature Test Coverage Pass when a row in the plan''s `Feature Inventory Touches` table cites a presence-only test descriptor (one that fails the SG-035 acceptance question at feature scope: "If the feature were silently broken but the test artifact still existed, would this assertion fail?"). Added to `audit.schema.json` findings_categories enum at Phase 73 (GH #41).'
home: qor/references/doctrine-feature-tdd.md
referenced_by:
  - qor/gates/schema/audit.schema.json
  - qor/skills/governance/qor-audit/SKILL.md
introduced_in_plan: phase73-feature-inventory-tdd
```

```yaml
term: third-party SDK citation
definition: 'A required citation form at /qor-audit Step 3 Infrastructure Alignment Pass (Phase 74 wiring, GH #49): every plan claim referencing a third-party SDK method or property must cite either an installed type declaration (node_modules/<package>/dist/*.d.ts for JS/TS; pip show + module inspection for Python; Cargo.toml + cargo doc for Rust) OR an official documentation URL with quoted text. Missing citation triggers VETO with `infrastructure-mismatch` category. Closes SG-006 PostHog SDK hallucination class.'
home: qor/skills/governance/qor-audit/SKILL.md
referenced_by:
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase74-audit-pass-extensions
```

```yaml
term: behavioral-semantics claim
definition: 'A plan assertion about runtime behavior of an external mechanism (Postgres durability/concurrency/transaction semantics, lock lifecycle, trigger side-effects, supabase-js method behavior, auth-schema mutability, managed-schema constraints). Required at /qor-audit Step 3 Infrastructure Alignment Pass (Phase 74 wiring, GH #49) to include inline citation: upstream docs URL + quoted text, upstream source file:line, or in-repo precedent demonstrating the claimed behavior. Closes SG-010 mechanism-detail hallucination recurrence class.'
home: qor/skills/governance/qor-audit/SKILL.md
referenced_by:
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase74-audit-pass-extensions
```

```yaml
term: Live-Progress Invariant
definition: 'A sub-rule under /qor-audit Step 3 Ghost UI Pass (Phase 74 wiring, GH #58): every UI element with progress semantics (progress bar, spinner, phase indicator, step list) must reflect the underlying operation''s progress at intermediate points. Required behaviors: intermediate state when backing op takes >2s; no fake-jump pattern (0%->100% without intermediate writes); modals subscribe to backing event stream and re-render; error UI surfaces explicit dismiss/retry. Violations VETO with `ghost-ui` category, sub-tag `live-progress-fake`.'
home: qor/skills/governance/qor-audit/SKILL.md
referenced_by:
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase74-audit-pass-extensions
```

```yaml
term: SG-FakeProgress-A
definition: 'Shadow-genome pattern: UI element with progress semantics animates 0%->100% with no intermediate writes while the backing operation runs silently for >2 seconds. Operator perceives the click as having done nothing. Originating recurrence: FailSafe v5.1.0 Install QorLogic Skills card (META_LEDGER #360/#361/#362/#366). Countermeasure: /qor-audit Ghost UI Pass Live-Progress Invariant sub-rule. Phase 74 wiring (GH #58).'
home: qor/references/doctrine-shadow-genome-countermeasures.md
referenced_by:
  - qor/skills/governance/qor-audit/SKILL.md
introduced_in_plan: phase74-audit-pass-extensions
```

```yaml
term: substantiate step prerequisite
definition: 'A machine-readable declaration in qor-substantiate SKILL.md (`## Step Prerequisites` table) naming the artifact or module each step requires (predicate kinds: `file:<path>`, `module:<dotted>`, `command:<binary>`). Parsed by `qor/scripts/substantiate_capability.py` and surfaced by `qor-logic substantiate-capability` CLI as a markdown table of PRESENT/ABSENT status for each step. Operators on non-Python hosts use the report to identify which steps will run vs skip on their archetype. Phase 75 wiring (GH #38).'
home: qor/scripts/substantiate_capability.py
referenced_by:
  - qor/skills/governance/qor-substantiate/SKILL.md
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase75-skill-capability-declaration
```

```yaml
term: gate_skipped_prerequisite_absent
definition: 'Shadow Process Genome event_type (severity 1 default) emitted when an operator skips a /qor-substantiate step whose declared prerequisite is absent on the host archetype (e.g., Step 7.5 version bump on a non-Python host without pyproject.toml). Catches the SG-HalfSealedClaim-A pattern. Schema enum entry added at Phase 75.'
home: qor/gates/schema/shadow_event.schema.json
referenced_by:
  - qor/skills/governance/qor-substantiate/SKILL.md
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase75-skill-capability-declaration
```

```yaml
term: SG-HalfSealedClaim-A
definition: 'Shadow-genome pattern: /qor-substantiate runs against a host whose archetype lacks Python toolkit prerequisites; multiple gate steps silently fail or no-op; the operator hand-skips after the first failure; the resulting SESSION SEAL entry Merkle hash anchors a half-checked state. Originating recurrence: 2026-05-06 Customer-App-3.0 React+bun+Supabase incident (SUBSTANTIATE DEFERRED). Countermeasure: qor-logic substantiate-capability CLI + gate_skipped_prerequisite_absent shadow events. Phase 75 wiring (GH #38).'
home: qor/references/doctrine-shadow-genome-countermeasures.md
referenced_by:
  - qor/scripts/substantiate_capability.py
  - qor/skills/governance/qor-substantiate/SKILL.md
introduced_in_plan: phase75-skill-capability-declaration
```

```yaml
term: content-addressable entry ID
definition: 'A deterministic 12-char hex identifier derived from SHA256(timestamp|phase|content_hash)[:12] for each META_LEDGER entry. Per Phase 76 wiring (GH #51): forward-only -- new entries from Phase 76 onward carry an `**Entry ID**:` body line; past Entries #1-#207 are unchanged. Survives concurrent federation append because no entry-number-allocation coordination is required. Set env QOR_ENTRY_ID_FULL_HASH=1 for 64-char full-hash mode at federation scale.'
home: qor/scripts/entry_id.py
referenced_by:
  - qor/skills/governance/qor-substantiate/SKILL.md
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase76-meta-ledger-federation
```

```yaml
term: SG-ConcurrentLedgerRace-A
definition: 'Shadow-genome pattern: META_LEDGER sequential entry-numbering is single-writer; concurrent federation workers race on number allocation, producing duplicate-numbered entries with intact chain math but corrupted human-readable structure. Originating recurrence: cross-workspace Entries #16a/b, #17a/b, #18a/b plus canonical Qor-logic #109/#111/#113. Countermeasure: forward-only content-addressable Entry IDs + previous_hash uniqueness detection at /qor-substantiate Step 7.7. Retroactive renumbering of past sealed entries is structurally forbidden. Phase 76 wiring (GH #51).'
home: qor/references/doctrine-shadow-genome-countermeasures.md
referenced_by:
  - qor/scripts/entry_id.py
  - qor/reliability/seal_entry_check.py
  - qor/skills/governance/qor-substantiate/SKILL.md
introduced_in_plan: phase76-meta-ledger-federation
```

```yaml
term: pipeline stage dependency graph
definition: 'A directed graph constructed at /qor-audit Step 3 Filter-Stage Ordering Coherence sub-pass for any pipeline-shaped function (candidate set -> multiple filter stages -> selection). Stage N depends on stage M iff M enforces an invariant that N''s correctness assumes. The audit verifies that the code execution order is a topological sort of the graph. Phase 78 wiring (GH #47).'
home: qor/skills/governance/qor-audit/SKILL.md
referenced_by:
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase78-filter-stage-ordering
```

```yaml
term: filter-stage ordering coherence
definition: 'A /qor-audit Step 3 sub-pass (Phase 78 wiring, GH #47) that runs a 4-step procedure on pipeline-shaped functions: identify each filter stage''s preconditions; identify each filter stage''s invariants; construct the pipeline stage dependency graph; verify code execution order is a topological sort. Any inversion VETOes with `composition` category, sub-tag `filter-order-inversion` (or `infrastructure-mismatch` when the missing precondition is an external-state assumption). Catches the COREFORGE Skill-Forge dispatcher pattern (META_LEDGER #209): validator invoked elsewhere instead of as first filter stage, allowing invalid candidates to dominate selection.'
home: qor/skills/governance/qor-audit/SKILL.md
referenced_by:
  - qor/references/doctrine-shadow-genome-countermeasures.md
introduced_in_plan: phase78-filter-stage-ordering
```

```yaml
term: SG-FilterOrderInversion-A
definition: 'Shadow-genome pattern: a pipeline-shaped function composes filter stages out of their dependency order; stage-by-stage correctness review passes each stage individually but misses that an upstream invariant is enforced elsewhere in the codebase instead of as a stage of the same pipeline. Originating recurrence: COREFORGE Skill-Forge V1 dispatcher (META_LEDGER #209): tier -> classification -> vendor -> cost filters without validator-first; invalid manifests with low cost dominated selection; operator-caught at PR #82 merge review (commit 0999e47). Countermeasure: /qor-audit Step 3 Filter-Stage Ordering Coherence sub-pass. Phase 78 wiring (GH #47).'
home: qor/references/doctrine-shadow-genome-countermeasures.md
referenced_by:
  - qor/skills/governance/qor-audit/SKILL.md
introduced_in_plan: phase78-filter-stage-ordering
```
