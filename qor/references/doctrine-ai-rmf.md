# Doctrine: NIST AI RMF 1.0 + AI 600-1 GenAI Profile Alignment

Reference mapping between Qor-logic governance lifecycle phases and NIST
AI Risk Management Framework 1.0 functions, plus AI 600-1 Generative AI
Profile sections. Phase 54.

## Framework summary

NIST AI RMF 1.0 organizes AI risk management around four functions:

- **GOVERN** — establish policies, procedures, and oversight structures
- **MAP** — categorize the AI system context and identify risks
- **MEASURE** — analyze, assess, benchmark, and monitor AI risks
- **MANAGE** — prioritize and act on identified risks

NIST AI 600-1 (GenAI Profile) extends AI RMF 1.0 with sections specific to
generative-AI-system risks, notably §2.7 (information integrity / prompt
injection) and §2.8 (information security).

## GOVERN

| Sub-category | Qor-logic surface | Path |
|---|---|---|
| GV-1.1 Legal/regulatory awareness | Doctrine inventory + Authority line in CLAUDE.md | `qor/references/doctrine-eu-ai-act.md`, `doctrine-ai-rmf.md`, `doctrine-owasp-governance.md`, `doctrine-nist-ssdf-alignment.md` |
| GV-1.4 Risk management process | Shadow genome + cycle-count escalator | `qor/scripts/cycle_count_escalator.py`, `qor/references/doctrine-shadow-genome-countermeasures.md` |
| GV-1.5 Ongoing monitoring | Process shadow genome JSONL + threshold automation | `docs/PROCESS_SHADOW_GENOME.md`, `qor/scripts/check_shadow_threshold.py` |
| GV-2.1 Roles and responsibilities | Persona model + delegation table | `qor/gates/delegation-table.md` |
| GV-3.2 Decision-making transparency | Merkle-chained META_LEDGER + Phase 54 ai_provenance manifest | `docs/META_LEDGER.md`, `qor/gates/schema/_provenance.schema.json` |
| GV-4.2 Documenting AI risks | SG countermeasures catalog + research brief Recommendations | `qor/references/doctrine-shadow-genome-countermeasures.md`, `docs/research-brief-*.md` |
| GV-6.1 Third-party AI risk | Phase 55 candidate (model pinning + SBOM); Phase 54 advisory `permitted_subagents:` frontmatter | `qor/skills/**/SKILL.md` |

## MAP

| Sub-category | Qor-logic surface | Path |
|---|---|---|
| MP-1.1 Context establishment | Documentation-integrity dialogue at /qor-plan Step 1b | `qor/references/doctrine-context-discipline.md`, `qor/references/doctrine-documentation-integrity.md` |
| MP-2.3 Negative impacts mapped | SG entries (SG-016 through SG-PromptInjection-A) | `qor/references/doctrine-shadow-genome-countermeasures.md` |
| MP-3.1 Benefits/risks tradeoff | Phase 54 plan template `impact_assessment` block (optional; required when `high_risk_target: true`) | `qor/gates/schema/plan.schema.json` |
| MP-5.1 Impact assessment | Phase 54 plan template `impact_assessment` block; Step 1c dialogue in /qor-plan | `qor/skills/sdlc/qor-plan/SKILL.md` |

## MEASURE

| Sub-category | Qor-logic surface | Path |
|---|---|---|
| ME-2.1 Performance evaluation | Per-phase ai_provenance.human_oversight signal (Phase 54) | `qor/scripts/ai_provenance.py`, `qor/gates/schema/_provenance.schema.json` |
| ME-2.7 Security/resilience | OWASP doctrine + Cedar policies + 142 security tests | `qor/references/doctrine-owasp-governance.md`, `qor/policies/owasp_enforcement.cedar` |
| ME-3.1 Risk tracking | Process shadow genome severity sums + threshold automation | `qor/scripts/check_shadow_threshold.py` |
| ME-4 Feedback mechanisms | Upstream-reporting protocol (PROCESS_SHADOW_GENOME_UPSTREAM) | `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` |

## MANAGE

| Sub-category | Qor-logic surface | Path |
|---|---|---|
| MG-1.1 Risk treatment | /qor-remediate skill + override-friction escalator (Phase 54) | `qor/skills/sdlc/qor-remediate/`, `qor/scripts/override_friction.py` |
| MG-2 Risk classification | change_class enum (hotfix \| feature \| breaking) + high_risk_target flag (Phase 54) | `qor/gates/schema/plan.schema.json` |
| MG-3.1 Third-party AI risk | Phase 55 candidate (Cedar-enforced subagent admission + model pinning) | (deferred) |
| MG-4.1 Continuous monitoring | Shadow genome ongoing collection | `docs/PROCESS_SHADOW_GENOME.md` |
| MG-4.3 Incident response | SHADOW_GENOME entries + remediation workflow | `qor/skills/sdlc/qor-remediate/`, `docs/SHADOW_GENOME.md` |

## NIST AI 600-1 (Generative AI Profile)

| §  | Risk class | Qor-logic surface | Status |
|---|---|---|---|
| 2.1 | CBRN/dangerous content | Not applicable to code-tooling context | N/A |
| 2.4 | Data privacy / training data provenance | No training; uses pre-trained foundation model | N/A (operator concern) |
| 2.7 | Information integrity / prompt injection | Phase 53 canary catalog + audit-pass + Cedar `forbid` rule | `qor/scripts/prompt_injection_canaries.py`, `qor/references/doctrine-prompt-injection.md` |
| 2.8 | Information security | OWASP doctrine + Cedar policies + intent-lock | `qor/references/doctrine-owasp-governance.md`, `qor/reliability/intent_lock.py` |
| 2.10 | Intellectual property | Phase 56 candidate (secret-scanning gate) | (deferred) |
| 2.12 | Value chain / supply chain | Phase 55 candidate (model pinning + SBOM) | (deferred) |

## Evidence-collection contract

Phase 54 forward-only emission: every gate artifact written by a
Qor-logic skill carries an `ai_provenance` field. The
`ai_provenance.human_oversight` signal serves as **MEASURE-2.1 evidence**
(operator decision quality per gate) and **MANAGE-1.1 evidence** (risk
treatment per session). The `qor-logic compliance ai-provenance --session
<sid>` CLI emits an aggregated session manifest suitable for operator
inclusion in NIST AI RMF documentation packages.

Pre-Phase-54 entries (chain ≤ #176) carry no `ai_provenance` field;
forward-only by design (the Merkle chain is content-addressed and
append-only; retroactive embedding would invalidate prior chain hashes).

## References

- NIST AI RMF 1.0 (NIST AI 100-1)
- NIST AI 600-1 (Generative AI Profile)
- `qor/references/doctrine-eu-ai-act.md` — companion EU AI Act mapping
- `qor/references/doctrine-nist-ssdf-alignment.md` — companion SSDF mapping
- `docs/research-brief-prompt-logic-frameworks-2026-04-30.md` §B — research basis for this mapping
