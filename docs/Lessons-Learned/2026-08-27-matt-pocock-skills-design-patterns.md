# Lessons Learned: Design Patterns from Matt Pocock's Skills Repository

**Date reviewed:** 2026-08-27
**Source:** https://github.com/mattpocock/skills
**Observed source revision:** `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`
**License observed:** MIT

## Why this record exists

This is a deliberate public-safe lessons-learned record under the exception defined by Qor-logic's publication-boundary doctrine. The external repository is research input, not an operational dependency.

Matt Pocock's repository contains several unusually disciplined patterns for agent-oriented engineering. Qor-logic should learn from those patterns without importing another project's identity, vocabulary, or implementation wholesale.

No source code or skill text is vendored by this change. The intended Qor work is an independent implementation informed by general design ideas and evaluated against Qor's own governance architecture.

## Primary lesson: design agent workflows as systems, not prompts

The strongest recurring pattern is not any one skill. It is the way the repository treats agent work as a designed system with explicit state, phase boundaries, test surfaces, context budgets, handoffs, and human decision points.

The relevant question for Qor is therefore not "which skills should we copy?" It is "which design disciplines expose weaknesses or improvement seams in Qor's current architecture?"

## 1. Large work should expose decision topology before implementation

The Wayfinder skill models large, uncertain, multi-session work as a progressively resolved graph rather than a large implementation plan written too early.

High-value ideas:

- start from a destination or outcome, not a task list;
- represent unresolved decisions and prerequisites explicitly;
- work the currently actionable frontier rather than pretending all future work is specifiable;
- distinguish uncertainty from deliberately out-of-scope work;
- preserve enough state that a fresh session can resume without reconstructing the entire problem;
- separate mapping the work from doing the implementation.

Qor adaptation: `qor-roadmap` should provide a Qor-native pre-S.H.I.E.L.D. decision-topology capability. It should not use the Wayfinder name, should not reproduce its tracker model literally, and should never become an implementation bypass around Qor's existing gates.

Observed upstream failure reports also argue against wholesale adoption. They expose practical weaknesses around issue-body limits, sub-issue limits, abandoned assignee claims, stale closed decisions, naive frontier ordering, research cost, and execution paths that can bypass normal implementation discipline. Qor should design those failure modes out rather than inherit them.

## 2. Facts and decisions have different owners

The grilling and research skills repeatedly separate factual discovery from decisions that belong to the operator.

Qor should sharpen this into a reusable rule:

> Factual prerequisites are agent obligations. Consequential choices are authority-scoped decisions. The agent should not ask the operator for facts it can establish itself, and it should not silently consume decisions that require operator authority.

Implications:

- `qor-roadmap` can block a downstream decision on an unresolved fact while continuing other independent frontier work;
- `/qor-plan` and `/qor-ideate` can ask independent ready decisions in breadth-first rounds instead of serially asking one question at a time;
- research should happen before operator questioning whenever evidence can remove the question entirely.

## 3. Design alternatives before auditing a favorite

The codebase-design skill uses a "Design It Twice" pattern: multiple agents independently propose radically different interfaces under different constraints, then compare them on leverage, locality, and seam placement.

This fills a different role from Qor's adversarial audit.

- design divergence asks whether a better solution family exists before commitment;
- adversarial audit attacks the selected plan after commitment.

For consequential architecture work, Qor should add an optional design-divergence step before locking a plan. It should not be mandatory for routine changes because generating four architectures for a typo would be a triumph of ceremony over judgment.

## 4. Deep modules are a useful lens for skills too

The codebase-design skill defines a deep module as substantial behavior behind a small interface at a clean seam. Its useful tests include:

- the deletion test: if deleting the module merely removes complexity, it was shallow; if complexity reappears across callers, the module was earning its keep;
- interface as test surface;
- dependencies are accepted rather than created internally;
- a seam is real when behavior actually varies across it, not merely because an abstraction can be imagined.

Applied to Qor:

- a skill's invocation contract and declared handoffs are its interface;
- references, helpers, and internal orchestration are implementation detail;
- repeated wrapper skills should be tested with the deletion test;
- shared abstractions should hide real repeated complexity rather than add another forwarding layer;
- host adapters should exist where hosts genuinely differ, while canonical behavior stays behind the Qor interface.

This is especially relevant to prompt-corpus size reduction and to deciding which repeated governance text belongs in a shared reference or deterministic helper.

## 5. Prompt context is a budget, not free documentation space

The writing-for-agents material treats agent instructions as a constrained information architecture.

Strong lessons:

- always-loaded text should primarily be navigation and trigger information;
- branch-specific detail should sit behind precise context pointers;
- context load and human cognitive load are separate budgets;
- user-invoked and model-invoked skills have different economics;
- one rule should have one authoritative home;
- environment facts should be looked up rather than cached in prose where they can drift;
- completion criteria should be observable rather than rhetorical;
- prompt sediment that does not change behavior should be measured and removed.

Qor already has progressive disclosure and compiled weak-tier variants. That gives it a stronger adaptation path than simple prompt shortening: keep mandatory runtime behavior inline, move explanatory and branch-specific doctrine behind exact pointers, and let compilation selectively expand context for weaker hosts or models.

## 6. Verify claims before asking more questions

The triage skill checks whether a reported bug or request is real, already implemented, or previously rejected before it grills the maintainer for more detail.

This sequencing rule is broadly useful:

> Verify what the environment can verify before asking the operator to spend attention resolving ambiguity.

Qor opportunities:

- issue intake and roadmap research should search for existing behavior by domain concept, not only by the request's wording;
- known rejected approaches should be recoverable so agents do not repeatedly rediscover dead ends;
- `ready-for-agent` versus `ready-for-human` is a useful projection of Qor's existing authority model;
- durable agent briefs can improve cross-session and cross-agent handoff quality.

Qor's Shadow Genome is related but not identical to a rejected-work knowledge base. Shadow Genome records failure and governance patterns. Product or architectural paths deliberately rejected for this codebase are a separate class of memory and should remain distinguishable.

## 7. Domain modeling should be active only when the model changes

The domain-modeling skill distinguishes consuming an existing glossary from actively changing the domain model.

Useful disciplines:

- challenge terms that contradict the canonical glossary;
- replace vague or overloaded words with precise canonical terms;
- invent concrete edge-case scenarios to test relationships between concepts;
- check whether code behavior agrees with the stated domain model;
- record architecture decisions sparingly.

Its ADR threshold is particularly useful. An ADR is warranted when a decision is all three:

1. costly to reverse;
2. surprising without historical context;
3. the result of a genuine trade-off.

Qor can use this as an ADR admission heuristic while retaining its own decision and evidence machinery.

## 8. Debugging should begin with a tight falsifiable loop

The diagnosing-bugs skill makes feedback-loop construction the first-class debugging task. It prioritizes a fast, deterministic, red-capable command that reproduces the exact symptom before hypothesis generation.

This aligns strongly with Qor's deterministic-governance direction and can sharpen `/qor-debug`:

- no causal theory before a red-capable signal exists, unless the inability to construct one is itself explicitly recorded;
- minimize the reproduction before widening hypotheses;
- generate several falsifiable hypotheses before testing;
- map each probe to a prediction;
- turn the minimal reproduction into a regression test at the highest correct seam;
- if no correct test seam exists, report that as an architectural finding rather than manufacture a shallow test.

## 9. Implementation work benefits from tracer-bullet slicing

The to-tickets skill prefers narrow but complete vertical slices, each independently demonstrable or verifiable, each small enough for a fresh context window, with explicit blocking edges.

For wide refactors it uses expand-contract rather than pretending the work can be vertically sliced cleanly.

This should influence Qor Roadmap's transition to implementation:

- resolve decision topology first;
- emit implementation-ready slices only when prerequisites are settled;
- prefer vertical end-to-end slices;
- use expand-contract for broad compatibility migrations;
- model blockers explicitly;
- keep each slice context-window sized where practical.

## 10. Synthesis should not reopen settled decisions

The to-spec skill explicitly synthesizes the conversation without interviewing the user again. The handoff skill references existing artifacts rather than copying them into a new summary.

These are small rules with outsized value:

- once a decision is settled and durably recorded, downstream synthesis should consume it rather than re-ask it;
- handoffs should point to canonical specs, plans, decisions, issues, commits, and evidence instead of creating another mutable copy;
- a fresh session should load the lowest-resolution sufficient state first and zoom into details only when required.

These rules should become part of Qor Roadmap's resumption contract.

## 11. Retrospectives should improve the agent environment

The in-progress retro skill does not merely ask whether the code was good. It audits the environment that shaped agent performance:

- navigation;
- automated checks;
- coding standards and review responsibility;
- always-loaded instruction size;
- tool economy;
- no-op instructions;
- information access.

This maps naturally to Qor's Process Shadow Genome and process-review cycle. A future Qor process review should explicitly ask whether a failure is best fixed by:

1. better information access;
2. a deterministic check;
3. a reviewer rule;
4. a navigation pointer;
5. a workflow or skill change;
6. or no additional instruction at all.

That ordering helps prevent every failure from becoming three more paragraphs in an always-loaded prompt.

## 12. Human checkpoints should be pushed right

The in-progress loop skill uses a useful workflow rule: do as much safe, deterministic preparation as possible before interrupting the human, then present a decision-ready brief rather than raw work.

Qor should apply this carefully within authority limits:

- research and evidence gathering should usually precede operator checkpoints;
- independent safe work should continue when one branch is waiting on a human decision;
- the checkpoint should expose the decision, evidence, recommendation, and consequences;
- no amount of checkpoint efficiency grants authority the agent does not have.

## Adoption matrix

| Pattern | Qor disposition | Likely home |
|---|---|---|
| Decision topology for large work | Adapt as Qor-native capability | `qor-roadmap` |
| Actionable frontier | Adopt generic graph concept, harden ranking | `qor-roadmap` |
| Explicit unresolved space | Adapt | `qor-roadmap` |
| Breadth-first ready decisions | Adapt | `qor-roadmap`, `/qor-plan`, `/qor-ideate` |
| Facts vs authority-scoped decisions | Generalize | roadmap and planning doctrine |
| Design It Twice divergence | Adapt selectively | planning reference or subroutine |
| Deep-module/deletion-test lens | Generalize | `/qor-refactor`, `/qor-audit` |
| Progressive disclosure/context pointers | Strengthen existing behavior | prompt mechanics program |
| Verify-before-grill | Generalize | roadmap, triage/intake, planning |
| Active domain-model refinement | Strengthen existing glossary discipline | planning/ideation |
| Tight red-capable debugging loop | Strengthen `/qor-debug` | debugging |
| Tracer-bullet implementation slices | Adapt | roadmap-to-plan transition |
| Expand-contract wide migrations | Adopt | planning/reference doctrine |
| Handoff by pointers, not duplication | Strengthen | handoff/resumption |
| Environment-focused retrospective | Adapt into Process Shadow Genome review | process review |
| Push-right checkpoints | Adapt within Qor authority limits | roadmap/automation |
| Assignee-only claim ownership | Reject unchanged | use lease-like Qor claim model |
| One mutable tracker body as canonical state | Reject | use reconstructible state + projections |
| Creation-order frontier selection | Reject | use leverage-ranked frontier |
| Unlimited high-reasoning research fanout | Reject | capability/cost-aware research routing |
| Implementation inside roadmap resolution | Reject | hand off to S.H.I.E.L.D. |

## Attribution and independence

The ideas above were identified by studying Matt Pocock's public `skills` repository and its active development history. The Qor Roadmap design should explicitly preserve this attribution in lessons/research documentation.

The implementation itself should remain Qor-native:

- no Wayfinder naming;
- no operational dependency on the external repository;
- no copied skill body;
- no assumption that another project's tracker semantics are Qor's canonical state model;
- no bypass of Qor's governance lifecycle.

The source repository's MIT license permits reuse subject to its notice requirements, but this work deliberately favors conceptual adaptation over source copying. If future implementation copies a substantial source fragment, the applicable MIT copyright and permission notice must accompany that copied material.
