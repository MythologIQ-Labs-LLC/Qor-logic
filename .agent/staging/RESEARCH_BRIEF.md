# Research Brief — Persona framing vs. context control in Qor-logic subagent usage

**Date**: 2026-04-19
**Analyst**: The Qor-logic Analyst
**Target**: Internal doctrine + skill prose — not an external codebase
**Scope**: Evaluate the claim "anthropomorphising subagents is a trap; the real value of subagents is controlled context" against Qor-logic's persona language, skill handoffs, and actual subagent invocations.

---

## Executive summary

The claim is correct, and the codebase already contains its own half-learned proof. Real subagent usage in Qor-logic (`qor-deep-audit-recon`, `qor-debug`) is explicitly justified in terms of context preservation — that justification is in the prose. In parallel, the `<persona>…</persona>` frontmatter and "Identity Activation" Step 1 blocks ("You are now operating as **The Qor-logic Judge**…") are main-thread prompt phrasing that runs in the same context window as the rest of the skill. They are not subagents. Labeling both mechanisms with the same persona vocabulary conflates three distinct levers (context isolation, cognitive stance, handoff target) into one metaphor, which invites exactly the confusion the claim warns about.

Primary drift: the persona metaphor is load-bearing in ~2 skills (audit, substantiate), decorative in most others, and actively *already corrected* in one (`qor-debug` mandates `subagent_type: "general"`, explicitly rejecting `ultimate-debugger`). The fix is not "strip personas"; it is to name the three mechanisms separately.

## Findings

### F1 — Three mechanisms, one vocabulary

Current prose uses the word "persona" (and the persona names Governor/Analyst/Judge/Specialist/Technical Writer) for three structurally different things:

| Mechanism | What it actually is | Where | Context-control value |
|---|---|---|---|
| **Frontmatter tag** `<persona>Governor</persona>` | Metadata label. Read by nothing mechanical. | Every `qor/skills/**/SKILL.md` (30+ files) | None |
| **Identity Activation** "You are now operating as **The Qor-logic Judge** in adversarial mode." | Main-thread prompt phrasing that nudges model stance. | `qor/skills/governance/qor-audit/SKILL.md:54`, `qor-substantiate/SKILL.md:61`, `qor-validate/SKILL.md:61`, `qor-research/SKILL.md:37`, `qor-implement/SKILL.md:62`, `qor-refactor/SKILL.md:60`, `qor-bootstrap/SKILL.md:40`, `qor-document/SKILL.md:38` | Zero — same context window |
| **Actual subagent invocation** via Task/Agent tool | New context window spawned with isolated prompt; result synthesized back. | `qor/skills/sdlc/qor-debug/SKILL.md:66`, `qor/skills/meta/qor-deep-audit-recon/SKILL.md:48` | The actual thing |

The word "persona" floats across all three.

### F2 — The codebase already learned the lesson once

`qor/skills/sdlc/qor-debug/SKILL.md:108` contains this constraint:

> **ALWAYS** use `subagent_type: "general"` (not `ultimate-debugger`)

This rule exists because someone tried the anthropomorphic route ("ultimate-debugger" as a persona-typed subagent) and discovered the plain general-purpose agent performed better. The lesson was recorded as a per-skill constraint but never generalized to doctrine. That is exactly the pattern: the team discovered the context window is the real mechanism; the persona was a decorative wrapper that didn't add anything.

### F3 — Where context-control justification already exists explicitly

`qor/skills/meta/qor-deep-audit-recon/SKILL.md:68`:

> **ALWAYS** delegate investigation to subagents (preserves main context budget)

And line 48:

> Each subagent operates in its own context window; main context receives a structured summary with file:line citations.

This is exactly the claim under review, written into an operational skill. It is not connected to any doctrine file, so the pattern doesn't propagate — skills that *don't* use subagents still carry the same persona vocabulary as if they did.

### F4 — Where persona framing is load-bearing

Two skills use persona-labeled stance changes that plausibly produce measurable behavioral difference:

- `qor-audit/SKILL.md:54` — "Judge in **adversarial mode**"
- `qor-substantiate/SKILL.md:61` — "Judge in **substantiation mode**" with the role "to prove, not to improve"

These are cognitive stance cues. The persona name ("Judge") is interchangeable; the *modifier* ("adversarial", "prove not improve") is the lever. The persona metaphor is along for the ride.

### F5 — Where persona framing is decorative

- `qor-status/SKILL.md:184` — "Governor Persona: Lightweight oversight without full audit overhead" on a read-only status dump. No cognition shift needed.
- `qor-help/SKILL.md:124` — "Governor Persona: Routing guidance without execution" on a command catalog display.
- `qor-document/SKILL.md:252` — "Technical Writer Persona: Pairs with qor-technical-writer agent for quality" — this one conflates a main-thread persona label with a separate sub-agent file (`qor/agents/qor-technical-writer.md`), blurring the two mechanisms in one sentence.

### F6 — Handoff prose borrows the persona vocabulary

`qor/skills/sdlc/qor-debug/SKILL.md:92-94`:

> - Architectural changes needed: hand off to `/qor-plan` for Governor review
> - Implementation ready: hand off to `/qor-implement` for the Specialist
> - Test validation needed: hand off to `/qor-substantiate` for the Judge

The handoff target is a skill (`/qor-plan`, `/qor-implement`, `/qor-substantiate`). "For Governor review" is a flourish — the `delegation-table.md` (the authoritative handoff registry at `qor/gates/delegation-table.md`) does not use persona names anywhere; it names skills. The persona-adjective in the prose either tells the reader something the skill name already tells them, or gestures at the Step 1 stance cue of the destination skill — but the reader has no way to tell which.

### F7 — Shadow-Genome family membership

This is the same family as the Phase 32–35 drift chain ("state-duplicated-from-source-of-truth" per ledger Entry #115): a concept with an authoritative source (the delegation table, the actual Task tool invocation, the stance modifier) is *restated* as a persona label, and the restatement drifts. The lesson in Entry #115 — "when state has a single source of truth, any copy will eventually drift" — applies directly. "Persona" is a copy of three different source-of-truth mechanisms.

## Doctrine alignment

| Doctrine claim / codebase claim | Actual finding | Status |
|---|---|---|
| `patterns-agent-design.md:13-21` — "Design personality traits appropriate to the role" | Generic multi-agent reference, not Qor-specific; imported pattern library. Not referenced by any chain skill. | NEUTRAL (unused aspirational doc) |
| `delegation-table.md` — "Skills name skills explicitly" | Confirmed; the table itself uses zero persona language. Skills-to-skills is the authoritative protocol. | MATCH |
| Persona framework is consistent across skills | `<persona>` frontmatter appears on 30+ skills but the **function** ranges from real stance-cue to decorative label. Same token, different semantics. | DRIFT |
| `qor-debug` rule `subagent_type: "general"` (not `ultimate-debugger`) | Present at line 108. Indicates the team already learned that persona-typed subagents underperform generic ones. Not generalized. | DRIFT (local lesson, no doctrine uplift) |
| `qor-deep-audit-recon` — "delegate to subagents (preserves main context budget)" | Present at line 68. The only skill that names context-preservation as the purpose of subagent use. | MATCH (but isolated) |

## Tensions

1. **Stance-cue vs. identity-cue.** Removing "You are now operating as The Judge" removes a line the model probably pays attention to. The question is whether the lift comes from the persona name or from the modifier ("adversarial mode"). Hypothesis: it's the modifier. Low-cost test: replace persona preamble with a bare directive ("Apply the audit checklist with VETO-prone skepticism: ambiguity defaults to VETO") in one skill; compare VETO/PASS distribution across 5+ runs. Not proposed as mandatory now — flagged as investigable.

2. **Removing persona vocabulary loses a reading affordance.** "Judge" / "Specialist" / "Analyst" are short and memorable. Replacing them with "audit-stance skill" / "implementation skill" / "research skill" is accurate but flatter. The cost is ergonomic; the benefit is disambiguation. Tradeoff is real.

3. **Two skills already mix persona (main-thread) with agent (subprocess).** `qor-document` pairs "Technical Writer Persona" with a separate `qor-technical-writer` agent file. The skill reader currently cannot tell which mechanism a given sentence refers to. This must be disambiguated whether or not the broader refactor happens.

## Recommendations

**R1 — Add `doctrine-context-discipline.md` under `qor/references/`.** Codify the three mechanisms and when each applies:

- Context isolation (Task/Agent tool): use when a phase must read files >50 KB, run parallel independent investigations, or produce a bounded summary back to main. Budget math required: N × M tokens in, <5 KB summary out.
- Cognitive stance cue (main-thread prose): use at the top of a skill only when the skill demands a measurable stance shift (adversarial, conservative, exploratory). State the modifier directly; the persona name is optional flavor.
- Skill handoff (delegation table): skills name skills. Never annotate a handoff with a persona name — it adds no information the skill name lacks.

Priority: HIGH. This is the direct fix for the confusion surfaced by the user's claim.

**R2 — Deprecate `<persona>` frontmatter on skills where it is decorative.** Target list (from F5): `qor-status`, `qor-help`, `qor-document`, `qor-repo-scaffold`, `qor-refactor` line 278 ("Specialist Persona" in Integration section). Keep the tag only where a cognitive stance is declared in the skill body.

Priority: MEDIUM. Low-risk cleanup; makes the remaining uses meaningful.

**R3 — Refactor Identity Activation blocks.** In skills that genuinely shift stance (`qor-audit`, `qor-substantiate`, `qor-validate`), rewrite Step 1 to lead with the directive, not the persona:

    Before: "You are now operating as **The Qor-logic Judge** in adversarial mode."
    After:  "**Stance**: adversarial. Any ambiguity defaults to VETO. Role is to prove the work is unsealable, not to make it sealable."

Persona name optional in parenthesis if ergonomics demand.

Priority: MEDIUM. Keeps the lever, removes the metaphor.

**R4 — Generalize the `qor-debug` lesson.** Add to `doctrine-context-discipline.md`: "Prefer `subagent_type: general` over persona-typed subagents unless the persona agent's SYSTEM prompt demonstrably alters tool selection or output shape. Record the decision." This promotes a per-skill constraint into a policy.

Priority: MEDIUM. Preempts the next recurrence of the "ultimate-debugger" mistake.

**R5 — Disambiguate `qor-document`.** Split the single confusing sentence at line 252 into two: one for the main-thread stance cue (if kept), one for the `qor-technical-writer` subagent file. Never use "pairs with" without specifying the mechanism.

Priority: LOW but fast. One-line fix, high clarity gain.

**R6 — Defer: behavioral A/B on stance cues.** R3 assumes the modifier carries the lift, not the persona. If proven wrong, R3 over-rotates. Cost to validate: ~30 minutes across 5 audit runs. Do not block R1/R2 on this.

## Tension with existing doctrine

None of the above conflicts with `doctrine-governance-enforcement.md`, `doctrine-token-efficiency.md`, or the delegation table. The persona language is orthogonal to the governance chain; removing it does not touch versioning, sealing, or handoffs. R2 actually *reduces* token cost per skill-load (every `<persona>` tag is ~5-10 tokens × 30+ skills × every load).

## Updated knowledge

Add to `memory/` (user memory, not repo memory) if user confirms this framing sticks:

- Persona names in Qor-logic skills are three different mechanisms under one vocabulary. Treat `<persona>` frontmatter, Step 1 "Identity Activation," and subagent-type decorations as distinct levers; do not reason about them as a unified system.

## Open questions for the Governor

1. Is ergonomic readability of persona names ("Judge", "Specialist") worth the mechanism-conflation cost? If yes, R3's rewrite is rejected; if no, proceed.
2. Is a formal Phase 36 plan warranted, or is this a `/qor-document` pass (doctrine file + skill edits, no version bump)?
3. R6 behavioral A/B — run as a one-off investigation, or skip on the hypothesis that the directive is the lever?

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
