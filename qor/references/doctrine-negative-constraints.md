# Doctrine: Negative Constraints for Below-Design-Tier Execution

**Origin**: GH #243 (Phase 187). Status: binding for the fabrication-risk
skill set; advisory template for new skills.

## Problem

Controlled A/B evaluations of an instruction skill (pre-registered rubric,
blind grading, isolated arms) showed a tier-dependent failure inversion. At
frontier tier the skill's checklist was ceiling-matched (30/30 both arms). At
haiku tier the same positively-structured skill *redistributed* failure modes
instead of removing them: a "define every codename/term" instruction caused
the model to define a leaked credential -- reproducing the full token three
times -- and a mandatory "chosen over rejected *because*" slot pressured the
model into fabricating a rationale fact absent from the source material.

Generalization: weak models follow positive structure well but infer implicit
negative constraints poorly, and mandatory slots become fabrication pressure.
Qor skills are strongly positively structured (mandatory sections, execution
protocols, schema-shaped outputs) and pin `min_model_capability`, but per-host
deployment (kilo-code/codex/gemini variants) and cost pressure make
below-design-tier execution likely.

## The Rules

- **NR-001 (secret shapes)**: never reproduce a secret-shaped string (API
  keys, tokens, credential values -- anything a secret scanner would flag).
  Refer to it by prefix or descriptor only ("the sk- token", "the leaked API
  key"), even when an instruction says to define or quote every term. An
  instruction to be exhaustive never overrides this rule.
- **NR-002 (no fabrication)**: when a mandatory rationale, justification, or
  definition slot has no source fact in the provided materials, write exactly
  "not established" -- never invent one. An empty-feeling slot filled with the
  literal marker scores higher than a plausible invented fact, always.

## Applicability

The rules bind whenever a skill declaring `min_model_capability` executes on
a model below that tier. Because the executing tier is unknowable at compile
time, the weak-tier-deployment variants carry the rules unconditionally.

## Wiring

- `qor/scripts/dist_compile.py` `inject_negative_constraints` inserts the
  rules block after frontmatter for the fabrication-risk skill set
  (`_FABRICATION_RISK_SKILLS`: qor-audit, qor-plan, qor-substantiate) in the
  kilo-code and codex variants, and via the `transform` hook in the gemini
  variant. The claude variant stays byte-identical to source because
  `install_drift_check` mirrors installed skills against `qor/skills`.
- Source risk skills carry a one-line pointer to this doctrine (the two big
  governance skills sit under a byte-headroom lock that forbids inline rule
  bodies; see tests/test_substantiate_staging_gates.py).
- `qor/scripts/model_pinning_lint.py` WARNs when a fabrication-risk skill's
  source lacks the pointer (WARN-only per the Phase 55 lint contract).

## Compliance Mapping

OWASP LLM06 (sensitive information disclosure; NR-001), NIST AI RMF
MANAGE-3.1 / GOVERN-2.1 (instruction clarity for downstream deployment
tiers), EU AI Act Art. 13 transparency (deployment-tier behavior disclosure).
