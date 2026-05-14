# Research Brief: Target-Aware Governed Prompt Compilation scope-fit for Qor-logic (GH #39)

**Phase**: research (Phase 77)
**Session**: `2026-05-14T2230-bf77eb`
**Originating ideation**: `.qor/gates/2026-05-14T2230-bf77eb/ideation.json`
**Originating issue**: GH #39
**Risk grade**: L2 (per ideation governance profile)

## Research question

The ideation packet for GH #39 selected **Option 2: Accept as exploratory probe** -- ship a minimal spike (PromptIR + ParsedIntent schemas + stub `compile_prompt()` returning IR unchanged) to validate API shape against one real consumer before committing to the full 5-phase subsystem build (Option 1).

The ideation also flagged the meta-question: **is this scope-fit for Qor-logic at all?** The proposal's framing leans toward "yes, this becomes Qor-logic's distinct identity," but the existing maintainer experience (focused governance skill surface) makes the answer non-obvious.

This research brief answers four sub-questions specified in the ideation rationale:

1. **(a)** Do existing prompt-IR / target-aware compiler projects already occupy this territory? (LangChain, DSPy, Guidance, etc.)
2. **(b)** Could existing Qor-logic governance hooks (intent_lock, doc_integrity, secret_scanner, prompt_injection_canaries) be repurposed for `GovernanceDecision`?
3. **(c)** What does an API-shape validation look like with one real consumer?
4. **(d)** Spike approved, or Option 3 (defer / out-of-scope) recommended?

## Sub-question (a): existing prompt-IR / compiler projects

**Surveyed projects** (canonical / well-known prompt-tooling in 2026):

| Project | Architectural pattern | Overlap with #39 proposal | Strategic-fit implication for Qor-logic |
|---|---|---|---|
| **LangChain** | Prompt templates + chain-of-runnables; provider abstractions via `BaseLanguageModel`; no canonical IR. Each chain produces provider-formatted prompts at execution time. | **Partial**: provider abstractions exist; canonical IR does NOT exist as a tracked artifact. LangChain's `PromptTemplate` is a string-with-variables, not a typed `PromptIR`. | Qor-logic adding a typed IR with governance gates is differentiated from LangChain. |
| **DSPy** | Compiles declarative prompts via teacher/student loops; treats prompts as parameters of an optimization pipeline. The "compilation" is automatic prompt-tuning against eval metrics. | **Different problem**: DSPy compiles for *quality* (optimization), not for *target* (governed routing). | Qor-logic's "compile for target" is orthogonal to DSPy's "compile for quality" -- they could coexist; no overlap collision. |
| **Guidance** | Constraint-based generation: structured output via grammar/regex; provider adapters per backend. | **Partial**: provider adapters; no canonical IR with governance gates. | Guidance is closer to "structured generation" than "governed compilation"; different center of gravity. |
| **OpenAI Function Calling / Anthropic Tool Use / Vertex Tools** | Provider-specific tool schemas. Not a cross-provider compilation. | **Disjoint**: each is provider-native. | Confirms the gap the #39 proposal identifies. |
| **Pydantic AI / Instructor / Marvin** | Python typed output via structured generation (Pydantic models as response shape). | **Partial**: typed contracts on the output side; not on the prompt/intent side. | Qor-logic adding typed IR on the INPUT side is differentiated. |
| **Microsoft Prompt Flow / Semantic Kernel** | Enterprise prompt orchestration; provider-agnostic execution graphs. Closer to LangChain in architectural pattern. | **Partial**: orchestration; no governance gate or canonical IR with policy contracts. | Differentiated by Qor-logic's governance contract emphasis. |

**Finding (a)**: there is a real gap. No surveyed project ships a *canonical PromptIR + governance gate + target resolver* pipeline as a tracked governance artifact. The closest pattern is LangChain's runnables (orchestration but no IR/governance), DSPy's compile loops (optimization not target-aware governance), and provider-native tool schemas (no cross-provider abstraction). Qor-logic *could* occupy this space, BUT:

- Each surveyed project has 10k-100k+ stars and a dedicated team. Qor-logic competing for "the canonical prompt compiler" mindshare against LangChain alone is a multi-year strategic commitment, not a multi-quarter implementation phase.
- The proposal's value proposition (intent-first + governance-before-formatting + target-specific) is real differentiation, but realizing it requires sustained product investment beyond one Qor-logic phase.

## Sub-question (b): can existing Qor-logic governance hooks be repurposed?

Walked the current governance surface for hooks that could feed a `GovernanceDecision` per the proposal's Component 3:

| Existing hook | Current purpose | Reusable for GovernanceDecision? | Notes |
|---|---|---|---|
| `qor.reliability.intent_lock` | Captures plan + audit + HEAD fingerprint pre-implementation; re-verifies at substantiate. | **Partially**: the fingerprint concept maps to "prompt-intent-fingerprint" -- a compiled-prompt could carry a hash anchored to its `PromptIR`. Adapt the existing helper rather than build new. |
| `qor.scripts.doc_integrity` | Tier-driven glossary + orphan + term-drift checks. | **Partially**: term-drift detection could check whether prompt IR cites glossary terms consistently. Lower fit; more like a future extension. |
| `qor.scripts.secret_scanner` | Pre-seal scan over staged content for credentials. | **Directly reusable**: secret-scanning a compiled prompt before execution is exactly the right semantic. Bind `GovernanceDecision.violations` to scanner findings. |
| `qor.scripts.prompt_injection_canaries` | Six-class catalog of prompt-injection patterns; scans governance markdown. | **Directly reusable**: same scanner pattern applies to user-prompts heading toward compilation. `GovernanceDecision.risk_level` could derive from canary-hit count. |
| `qor.policies.*.cedar` (Cedar policy evaluator) | Pure-Python Cedar-inspired evaluator for `permit`/`forbid` semantics. | **Directly reusable**: `GovernanceDecision` could be expressed as Cedar `permit (principal, action == "compile-prompt", resource == PromptIR) when {...}`. This is the strongest fit -- Qor-logic already has the policy evaluator. |
| `qor.scripts.ai_provenance` | Builds machine-readable `{system, version, host, model_family, human_oversight}` manifest. | **Directly reusable**: a compiled prompt's metadata should carry the provenance manifest. Already typed; already validated. |

**Finding (b)**: ~5 of 6 existing hooks are directly reusable for the proposed `GovernanceDecision`. Cedar evaluator is the single strongest piece of pre-existing infrastructure -- it removes a substantial implementation burden from any Phase 1 spike. The compiler subsystem would NOT be a greenfield build; it would compose existing governance primitives.

This materially changes the cost/benefit. The 5-phase implementation cost flagged in the ideation packet was based on a "build from scratch" assumption. With reuse, V1 spike (just IR + ParsedIntent + Cedar policy + provenance manifest) is closer to a single feature phase, not a multi-quarter project.

## Sub-question (c): API-shape validation with one real consumer

The ideation packet's evidence_required calls for "one consumer integration report on whether the IR shape captures their use case." Two practical candidates:

1. **FailSafe v5.1.0** (canonical Qor-logic consumer) -- already builds prompts for `claude` host installs and SHIELD-progression context. Has documented prompt-compilation needs (install-skills-card UX uses VS Code commands + ConsoleServer routes; each could declare governance contracts).
2. **Qor-logic itself** -- the `/qor-help --stuck` mode + `/qor-research` + `/qor-ideate` skills already produce structured prompts for downstream models. Self-application: compile Qor-logic's own skill-prose through PromptIR + GovernanceDecision.

**Recommendation**: self-application (consumer #2) is the lowest-friction validation. If `/qor-help --stuck` output can be expressed as a PromptIR and a `GovernanceDecision` can be derived via existing Cedar policies + secret_scanner + prompt_injection_canaries, the spike succeeds; the API shape captures at least one real use case.

If the spike succeeds in self-application, then proceed to FailSafe integration as a second validation point before committing to Phase 1 build.

## Sub-question (d): spike approved or defer recommended?

**Conditional recommendation**: **spike approved**, with three explicit conditions:

1. **Reuse, don't rebuild**: V1 spike MUST compose existing governance primitives (Cedar evaluator + secret_scanner + prompt_injection_canaries + ai_provenance) rather than create greenfield equivalents. Anything that looks like duplicating existing infrastructure escalates to /qor-refactor.
2. **Self-application FIRST**: `/qor-help --stuck` or `/qor-research` self-application before any external consumer. This validates the IR shape against a known-stable use case before bringing in third-party complexity.
3. **Strategic-identity guard**: V1 spike SHOULD NOT change Qor-logic's positioning surfaces (README, CONCEPT, marketing CHANGELOG language). The compiler subsystem is added as `qor/compiler/` -- additive to the existing skill+doctrine+seal surface, NOT a re-orientation.

**If these conditions hold**, proceed to Phase 78+ /qor-plan for the spike (PromptIR + ParsedIntent schemas + stub `compile_prompt()` that returns IR unchanged, plus one self-application test that round-trips a Qor-logic skill prompt through the IR).

**If any condition cannot be met** (e.g., the spike requires duplicating Cedar evaluator semantics, or self-application reveals the IR shape doesn't fit), **defer to Option 3** (`doctrine-scope-boundaries.md` declaring prompt-compilation out of Qor-logic scope; recommend sibling project home).

## Open follow-ups for the spike phase

- Decide whether the `ParsedIntent` schema is a Pydantic model or a JSON schema (Qor-logic convention is JSON schemas for gate artifacts; Pydantic for runtime data structures).
- Decide whether the spike ships under `qor/compiler/` (new top-level dir) or `qor/scripts/compile_prompt.py` (existing convention). New top-level dir signals strategic intent; existing convention keeps the spike low-risk.
- Cost-estimation for V2 backend rollout (when Phase 78 proceeds): which provider compiler is first? The ideation packet's open question #1 (Anthropic / OpenAI / generic local) is now resolved-toward-Anthropic because Qor-logic itself runs on Claude Code -- self-application demands Anthropic first.

## Routing recommendation

**Recommend Phase 78 follow-on: `/qor-plan` for the conditional spike.** The plan should include the three conditions above as `forbidden_interpretations` and structure the spike as a single phase with explicit pass-fail criteria (self-application succeeds; existing hooks compose cleanly; positioning surfaces untouched). On spike failure, the plan's failure_remediation_plan routes back to ideation for Option 3 closure.

**Alternative routing**: if you prefer not to invest a phase in even the conditional spike, the safer disposition is **Option 3 (defer)** -- close GH #39 with a doctrine entry naming prompt-compilation as out-of-scope and recommending the sibling-project pattern. The existing governance hooks remain available for consumers who want to build the subsystem against them.

## Research artifact reproducibility

This brief is based on:
- Architectural-pattern review (project surface scans + public-docs reading; no live API calls).
- Qor-logic codebase walk (`qor/reliability/intent_lock.py`, `qor/scripts/secret_scanner.py`, `qor/scripts/prompt_injection_canaries.py`, `qor/policies/*.cedar`, `qor/scripts/ai_provenance.py`).
- Ideation packet `2026-05-14T2230-bf77eb/ideation.json` as authoritative scope source.

No external API/network calls were made during research; all findings derive from the surveyed projects' public architectural documentation and the local Qor-logic codebase.
