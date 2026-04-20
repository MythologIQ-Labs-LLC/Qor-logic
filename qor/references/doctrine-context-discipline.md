# Doctrine: Context Discipline (Phase 39)

Personas in Qor-logic skills are **context-prioritization scaffolds for edge-case determinations within a skill's domain**. They are evaluated by performance, accuracy, and results — not by aesthetic flavor. This doctrine codifies the three distinct mechanisms the word "persona" has historically conflated, and the rules for adding, retaining, or removing each.

## 1. The three mechanisms

The word "persona" appears in three structurally different places. They have different operational semantics; treating them as one thing is the root defect class this doctrine addresses.

### 1.1 Frontmatter tag: `<persona>Governor</persona>`

A metadata label in a skill's frontmatter block. Read by nothing mechanical in the current system. Its only function is reader orientation when browsing the skill catalog. Most instances are decorative.

### 1.2 Identity Activation prose (Step 1 of skill body)

A main-thread prompt directive, e.g., "You are now operating as **The QorLogic Judge** in adversarial mode." This runs in the same context window as the rest of the skill; it is not a subagent spawn. Its potential behavioral effect is in the **stance modifier** (adversarial, prove-not-improve, exploratory), not in the persona name itself.

### 1.3 Subagent invocation: `Task({subagent_type: "..."})` / `Agent(...)`

A new context window spawned with isolated prompt, whose result is synthesized back into the main thread. The persona-like `subagent_type` parameter affects which specialist agent is selected from the available pool. This is a real mechanism with measurable context-isolation effects — but see §4 for the rule about persona-typed subagents specifically.

## 2. Persona as context-prioritization scaffold

A persona exists IFF it measurably prioritizes the context a skill loads for edge-case determinations within the skill's domain. The evaluation question is:

> **What context does this persona load that a bare skill-step directive would not?**

If the answer is "nothing" — the persona is decorative. Remove it.

If the answer is a specific stance modifier (adversarial, prove-not-improve, precision-focused) — the persona is a proxy for that modifier. Prefer stating the modifier directly; retain the persona name only as ergonomic flavor if reviewer readability genuinely benefits.

If the answer cites measurable outcome differences (detection rate, decision-path adherence, error catch rate) — the persona is load-bearing and must be retained, linked to the evidence artifact (per §5).

## 3. Stance directive discipline

Identity Activation blocks (§1.2) should lead with the behavioral modifier, not the persona name. Example rewrite, if evidence supports:

Before:
```
### Step 1: Identity Activation + Mode Selection
You are now operating as **The QorLogic Judge** in adversarial mode.
```

After:
```
### Step 1: Stance + Mode Selection
**Stance**: adversarial. Any ambiguity defaults to VETO. Role is to prove the work is unsealable, not to make it sealable.
```

The stance directive carries the behavioral lever. The persona name is optional flavor — retain iff evidence supports, or if operator judgment determines readability ergonomics outweigh the flatness cost.

## 4. Subagent invocation rule

Phase 35 established a narrow constraint in `qor-debug`: `**ALWAYS** use subagent_type: "general"` (not `ultimate-debugger`). Phase 39 generalizes this as doctrine:

**Default to `subagent_type: "general"` for any Task/Agent tool invocation.** Persona-typed subagents (e.g., `ultimate-debugger`, `code-reviewer`, `architect-reviewer`) require evidence that the persona's system prompt measurably alters tool selection, output structure, or decision path. Absence of evidence = use `general`.

When a skill prescribes a persona-typed subagent, the skill prose must include a reference to the evidence artifact justifying the choice. Without a reference, the skill is in violation of this doctrine and will fail Phase 37's Infrastructure Alignment Pass at audit time.

## 5. Verification protocol

Every `<persona>` frontmatter tag in `qor/skills/**/SKILL.md` must either:

1. Be **removed** (it is decorative and prioritizes no edge-case context), OR
2. Carry a **`<persona-evidence>`** pointer line in the same frontmatter block, referencing an A/B detection-rate artifact (e.g., `docs/phase39-ab-results.md`) or an equivalent measurement. The evidence must declare a measurable outcome delta (detection rate, decision-path adherence, etc.) that the persona contributes beyond a bare stance-directive rewrite.

Phase 39 ships initial evidence for `/qor-audit` and `/qor-substantiate` via a seeded-defect A/B harness (`qor/scripts/ab_harness.py` + `qor/scripts/ab_live_run.py`). Additional skills gain evidence as future operator-driven A/B cycles extend the corpus.

## 6. Anti-patterns this doctrine prevents

- **Persona as aesthetic flavor**: retaining `<persona>` tags or Identity Activation blocks because they feel meaningful without evidence they change behavior. This is the default failure mode documented in the research brief (`.agent/staging/RESEARCH_BRIEF.md`, META_LEDGER #116).
- **Conflating mechanism with metaphor**: labeling a persona's effect "context-prioritization" without being specific about WHICH context it prioritizes and for WHICH edge-case determinations. "Context-prioritization" is a verifiable claim about observable behavior; it is not a blessing that exempts a persona from evidence.
- **Persona-typed subagent by default**: reaching for `subagent_type: "ultimate-debugger"` (or similar) because the name sounds relevant. The Phase 35 lesson: `general` performs better until proven otherwise.

## Cross-references

- `qor/references/doctrine-governance-enforcement.md` §11 — cross-reference to this doctrine as binding.
- `qor/references/doctrine-shadow-genome-countermeasures.md` — `SG-InfrastructureMismatch` countermeasure (verifies plan claims against repo state; applies here when a skill claims persona evidence the artifact does not provide).
- `.agent/staging/RESEARCH_BRIEF.md` — original research that motivated this doctrine.
- `docs/META_LEDGER.md` Entry #116 — research-phase ledger entry recording the directive acceptance.
