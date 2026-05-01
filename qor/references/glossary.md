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
  - qor/references/patterns-devops.md
  - qor/references/ql-audit-templates.md
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
