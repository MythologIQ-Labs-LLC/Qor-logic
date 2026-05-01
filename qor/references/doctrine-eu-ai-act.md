# Doctrine: EU AI Act (Regulation 2024/1689) Alignment

Reference mapping between Qor-logic governance surfaces and applicable
EU AI Act articles. Phase 54.

## Applicability classification

Qor-logic is a **developer-facing CLI tool that orchestrates LLM-assisted
software development**. Under the Act:

- **Not high-risk per Annex III**: Qor-logic itself is not classified as
  high-risk. It is not a biometric, infrastructure, education, employment,
  essential-service, law-enforcement, migration, or justice system. The
  classification holds because Qor-logic is a developer-tooling artifact;
  it does not directly produce decisions affecting natural persons.
- **General-purpose AI system surface**: Art. 50 transparency obligations
  may apply when outputs (audit reports, plan files, implementation diffs)
  are placed on the EU market as AI-generated content.
- **Operator inheritance**: an operator using Qor-logic on EU-market
  high-risk software inherits the Annex III obligations applicable to
  *their* downstream system; Qor-logic provides surfaces (Art. 12 logging,
  Art. 14 oversight, Art. 13/50 transparency) that support their
  compliance posture but does not itself become high-risk by association.

The classification is therefore: Qor-logic is **not high-risk per Annex III**
and is intended as a support tool for downstream high-risk-system development.
The remainder of this doctrine maps each Article surface to the Qor-logic
control that supports operator compliance.

## Article-by-article mapping

### Art. 9 — Risk management (iterative)

**Qor-logic surface**: shadow genome iterative analysis (`docs/PROCESS_SHADOW_GENOME.md`),
cycle-count escalator (`qor/scripts/cycle_count_escalator.py`), three-consecutive-VETO
threshold forcing `/qor-remediate` (`qor/skills/sdlc/qor-remediate/`).

**Operator usage**: when supporting development of a high-risk downstream
system, operators may declare `high_risk_target: true` in their plan
top-matter; this triggers the optional `impact_assessment` block (per
`qor/gates/schema/plan.schema.json`) requiring purpose, affected
stakeholders, identified risks, mitigations, and residual risks.

### Art. 10 — Data governance

**Status**: not applicable to Qor-logic. No training data; uses
pre-trained foundation models supplied by the host harness (Claude Code
in default deployment).

### Art. 12 — Logging (automatically generated)

**Qor-logic surface**: `docs/META_LEDGER.md` Merkle-chained ledger;
`qor.scripts.ledger_hash` chain verification; `qor.reliability.seal_entry_check`
post-seal integrity check. Each phase artifact carries content hash +
chain hash + previous hash; tampering is detected by re-running the
chain verifier (`qor-logic verify-ledger`).

**Operator usage**: the ledger satisfies Art. 12 logging by construction —
every governance decision is recorded with cryptographic provenance.

### Art. 13 — Transparency to deployers/users

**Qor-logic surface**: `ATTRIBUTION.md` + `qor/references/doctrine-attribution.md`
(commit-trailer + CHANGELOG attribution); Phase 54 `ai_provenance` field
embedded in each gate artifact (`qor/gates/schema/_provenance.schema.json`)
declaring system, version, host, model_family, human_oversight, ts.

**Operator usage**: `qor-logic compliance ai-provenance --session <sid>`
(per `qor/cli_handlers/compliance.py`) emits a per-session manifest
aggregating all phase provenances; suitable for inclusion in operator
documentation packages.

### Art. 14 — Human oversight

**Qor-logic surface**: override-with-event pattern at every gate
(`qor/gates/chain.md` §"Override semantics"); binary PASS/VETO at
`/qor-audit`; 4-option push/merge menu at `/qor-substantiate` Step 9.6;
bundle checkpoint protocol per `qor/gates/workflow-bundles.md`; two-stage
remediation flip per `qor/skills/governance/qor-audit/SKILL.md` Step 4.2.
Phase 54 adds `ai_provenance.human_oversight` field — every gate artifact
records the operator decision (`pass | veto | override | absent`) — and
the override-friction escalator (`qor.scripts.override_friction`)
requires written justification after three overrides per session.

**Operator usage**: by treating Qor-logic-mediated AI suggestions as
proposals subject to gate verdicts, operators preserve human-in-the-loop
oversight. The `human_oversight` field in each gate artifact provides
machine-readable evidence for Art. 14 audits.

### Art. 15 — Accuracy, robustness, cybersecurity

**Qor-logic surface**: OWASP doctrine (`qor/references/doctrine-owasp-governance.md`)
+ Cedar policies (`qor/policies/owasp_enforcement.cedar`); Phase 53
prompt-injection canary catalog (`qor/scripts/prompt_injection_canaries.py`)
+ doctrine (`qor/references/doctrine-prompt-injection.md`); intent-lock
plan-and-audit fingerprinting (`qor/reliability/intent_lock.py`); 947+
tests passing including 142 security-specific.

### Art. 50 — Transparency of AI-generated content

**Qor-logic surface**: tiered attribution policy
(`qor/references/doctrine-attribution.md` §"Tiered usage") declaring
required form per surface (seal commit / plan-audit-implement commits
/ merge / PR description / CHANGELOG / GitHub release); Phase 54
machine-readable `ai_provenance` field on every gate artifact.

**Operator usage**: downstream consumers of Qor-logic output can read
`ai_provenance` from the gate artifact JSON to programmatically detect
AI-generated artifacts and apply Art. 50 disclosure requirements.

### Art. 72 — Post-market monitoring

**Qor-logic surface**: `docs/PROCESS_SHADOW_GENOME.md` JSONL event log;
`docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` upstream-reporting protocol;
threshold automation triggering issue creation when severity sum exceeds
10 points.

## Annex IV (Technical documentation) guidance

Not applicable to Qor-logic itself. For operators applying Qor-logic to
high-risk-system development, the following Qor-logic surfaces serve as
inputs to their Annex IV documentation package:

- `docs/META_LEDGER.md` — system development log (Annex IV §2 system description, §3 operational data)
- `docs/SHADOW_GENOME.md` + countermeasures doctrine — risk management documentation (Annex IV §6)
- gate artifacts under `.qor/gates/<sid>/*.json` — per-phase decision evidence (Annex IV §3, §6)
- AI provenance manifests via `qor-logic compliance ai-provenance` — system identification (Annex IV §1)

## Limitations

- Qor-logic does not itself perform downstream classification under Annex III; operators must classify their own systems.
- The `ai_provenance` field is descriptive metadata, not a cryptographic signature. Tampering with the manifest after seal is detected only by the existing Merkle chain integrity, not by the manifest itself.
- The Act's full scope (Art. 51 et seq. for general-purpose AI providers, Art. 99 et seq. for sanctions) lies with the foundation-model provider, not with Qor-logic as a tooling layer.

## Secret-scanning gate (Phase 56)

Phase 56 wires a substantiate-time secret-scanning gate that BLOCKs seal commits containing detected secrets. Closes OWASP LLM Top 10 LLM06 (Sensitive Information Disclosure) and NIST AI 600-1 §2.10 (preventing model and infrastructure credential leakage at the artifact-publication boundary). Drives the previously dormant Cedar attribute `has_hardcoded_secrets` (rule on books since Phase 23 with no scanner driving the boolean).

**Applicability**: enforced at `/qor-substantiate` Step 4.6.5 over the staged set for the seal commit. Pre-staged uncommitted changes are out of scope and rescanned on next stage cycle.

**Pattern catalog** (single source of truth: `qor/scripts/secret_scanner.PATTERNS`): `aws-access-key`, `github-pat-classic`, `github-pat-finegrained`, `github-oauth`, `private-key-header`, `stripe-live`, `slack-token`, `google-api-key`, `anthropic-key`, `generic-high-entropy-assignment`, `private-key-url`. Each entry is a frozen dataclass with `name` (used as gitleaks `RuleID`), regex, severity (3 high-confidence, 2 medium), and description.

**Allowlist semantics**: `qor/scripts/secret_scanner._ALLOWLIST` is a frozenset of literal substrings. A line containing any allowlisted substring is silently passed (false-positive class). Seeded with Cedar/schema attribute names (`permitted_tools`, `permitted_subagents`, `model_compatibility`, `min_model_capability`, `compute_skill_admission_attributes`, etc.) plus the AWS docs sample (`AKIAIOSFODNN7EXAMPLE`) and redaction sentinels (`REDACTED`, `EXAMPLE_SECRET`, `YOUR_API_KEY_HERE`).

**Output format**: gitleaks v8 schema. Each finding emits `{Description, RuleID, File, Line, Match, Secret, Tags}`. The `Match` and `Secret` fields always carry the redacted form (`<first4>...<last2>`) — original match never persisted, so the findings JSON may be committed/shared without leaking the secret. Default output path is `dist/secrets.findings.json` (Phase 55 SBOM convention).

**Operator workflow on BLOCK**: scanner exits 1; substantiate aborts. Operator reviews `dist/secrets.findings.json`, remediates each finding (remove from staging, redact in-place, or — for literal-match false positives — add the discriminating substring to `_ALLOWLIST` and re-stage), then re-runs `/qor-substantiate`. The scanner itself is not gitleaks; for full-history sweeps prior to Phase 56, operators should run `gitleaks detect --source . --log-opts="--all"` separately.

**Limitations**: regex-pattern detection only (no entropy heuristics, no probabilistic ML); allowlist is literal-substring (context-unaware); scope is the staged set at substantiate-time. Encrypted-blob detection, GitHub secret-scanning API integration, and auto-redaction are out of scope.

## References

- EU AI Act (Regulation 2024/1689) consolidated text
- `qor/references/doctrine-ai-rmf.md` — companion NIST AI RMF mapping
- `qor/gates/schema/_provenance.schema.json` — provenance schema
- `qor/scripts/ai_provenance.py` — manifest builder
- `qor/cli_handlers/compliance.py` — `ai-provenance` aggregator subcommand
- `qor/scripts/secret_scanner.py` — Phase 56 secret-scanning gate (LLM06 + AI 600-1 §2.10)
- `docs/research-brief-prompt-logic-frameworks-2026-04-30.md` §C — research basis for this mapping
