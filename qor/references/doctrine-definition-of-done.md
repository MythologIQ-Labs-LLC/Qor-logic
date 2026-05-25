# Doctrine: Definition of Done

**Phase 92 wiring; GH #86.**

## Purpose

Multiple Qor governance phases can return PASS while the artifact in question is still a placeholder or a lie at runtime. The existing gates verify artifact-shape, ledger chain, doc currency, secret hygiene, and procedural fidelity — they do not require empirical observation that the implementation actually behaves as the spec promises. Seal entries land with quietly-incomplete behavioral verification; trust in the seal's "all gates ran" claim erodes one missed lie at a time.

This doctrine names that failure mode and the four-tier contract that closes it. Definition of Done is an explicit, structured plan artifact — emitted by `/qor-plan`, structurally verified by `/qor-substantiate`, and (in V2) empirically verified against runtime test results.

## D-tier definitions

Per plan deliverable, every row declares acceptance at four tiers:

| Tier | Name | Verifies |
|------|------|----------|
| **D1** | Vision / specification | The deliverable's intended behavior is named and constrained. Maps to existing `/qor-ideate` + `/qor-plan` output. Satisfied by plan-section anchored prose. |
| **D2** | Code | The deliverable's source matches the spec; types / signatures / files declared in the plan exist at HEAD. Maps to existing `/qor-implement` + `/qor-audit` Step 3 Infrastructure Alignment Pass. |
| **D3** | Governance | Documentation, doctrine, ledger entries, seal-chain, badge-currency are consistent. Maps to existing `/qor-substantiate` Steps 4.5 / 4.7 / 6.5 / 7. |
| **D4** | Empirical / runtime verification | The implementation has been executed and observed to behave as the spec promises. At minimum: tests written for the spec-named behavior have passed against the implementation, on a build that compiles. V1 enforces the *declaration* of D4 acceptance criteria (the test name and the observed behavior); V2 will verify the *truth* (the test ran and passed in this seal cycle). |

D1–D3 are largely satisfied by existing gates; the new contract surfaces them so operators can attest to coverage per deliverable rather than relying on the implicit per-phase aggregate. D4 is the tier that was missing entirely — it is the lie-shipping prevention surface.

## Plan-section format (V1)

`/qor-plan` plan template includes a top-level `## Definition of Done` section between `## Phase N` and `## CI Commands`. Each deliverable carries a `### Deliverable: <name>` sub-header followed by a bullet list:

- `**D1**: <vision/spec statement>`
- `**D2**: <code-level acceptance: signature, types, file location>`
- `**D3**: <governance acceptance: ledger entry shape, doc surfaces>`
- `**D4**: <test name + observed behavior assertion>`
- OR `**D4.d**: <waiver rationale>` followed by `**Follow-up phase**: <reference>` (see Waiver protocol below)

Parser: `qor.scripts.dod_record.parse_plan(plan_path) -> list[DodRecord]`. Substantiate-time validator: `qor.scripts.dod_check.check_plan(plan_path) -> list[CheckFinding]`.

## Waiver protocol

D4 acceptance may be **waived** in a given cycle when empirical verification is impossible: the compile-gate runtime is offline, an external dependency is unreachable, the deliverable is operator-readable prose with no runtime to exercise, etc.

A `D4.d` row replaces the D4 row. It MUST carry:

1. A **rationale** explaining why empirical verification is not possible this cycle. Empty or whitespace-only rationale is a `waiver-without-rationale` finding.
2. A **`**Follow-up phase**:`** reference naming where the waiver is closed (next phase number, reserved phase slot, or "reserved for future X cycle"). Missing follow-up reference is a `waiver-without-followup` finding.

The waiver path is the operator's escape valve when the substantive verification cannot run *yet*. It preserves operator velocity while the absence of D4 is *named* and *tracked* — the current invisible default ("no one checked") is what enables the lie-shipping failure mode this doctrine closes.

Waiver discipline mirrors the `gate_override` event protocol (Phase 54 + EU AI Act Art. 14 surface): the override is permitted but logged, and accumulation triggers operator-visible thresholds. Future V2 work may add an `override_friction`-style escalator that counts unclosed D4.d waivers per session.

## V1 enforcement (this phase)

At `/qor-substantiate` Step 4.6.7:

- `qor.scripts.dod_check.check_plan` runs against the current phase plan.
- Findings (one per defect, each `severity="warn"` in V1) include:
  - `missing-dod-section` — plan has no `## Definition of Done` block.
  - `deliverable-missing-tier` — a `### Deliverable:` block omits one or more required tiers (D1, D2, D3, and either D4 or D4.d).
  - `waiver-without-rationale` — a `D4.d` row is empty or whitespace-only.
  - `waiver-without-followup` — a `D4.d` row lacks a `**Follow-up phase**:` reference.
- Findings are surfaced in the seal report's `## Definition of Done` block.
- **The check does NOT abort the seal in V1.** Operator amends the plan's DoD block in the next seal cycle. V2 may tighten specific categories to fail-closed once adoption matures and false-positive rates are characterized.

## V2 reserved scope

The following are explicitly deferred to a future Definition-of-Done v2 cycle:

- **D4 empirical-execution check** — cross-reference D4-declared test names against the latest pytest output (or equivalent test-runner artifact); fail seal when a named test did not run or did not pass.
- **Ledger SESSION SEAL body D-tier status block** — emit a structured `## Definition of Done` section in the cryptographically-sealed entry body (not just the operator-reviewable seal report).
- **`/qor-ideate` integration** — emit a preliminary `dod.json` artifact at ideation time so D1 is named before plan-authoring.
- **Implement-time D4 author-intent capture** — `/qor-implement` records which D4 acceptance criteria have a corresponding test author intent at implement time.
- **Waiver-friction escalator** — when accumulated `D4.d` waivers in a session exceed a threshold, prompt operator for written justification (analogous to Phase 54 `override_friction`).

## Cross-references

- `qor/references/doctrine-test-functionality.md` — tests must verify behavior, not artifact presence. D4 acceptance criteria MUST name a behavior assertion, not just "test exists".
- `qor/references/doctrine-procedural-fidelity.md` — Phase 58 procedural-fidelity check at substantiate Step 4.6.6 is structurally adjacent; both surface deviations between ceremonial pass-states and substantive coverage.
- `qor/references/doctrine-governance-enforcement.md` §6 — PR citation surface; D4 acceptance criteria SHOULD be cited in PR descriptions for operator visibility.
- `qor/references/doctrine-shadow-genome-countermeasures.md` `SG-DoDImplicit-A` — catalog entry for the lie-shipping pattern this doctrine closes.
- `qor/references/doctrine-shadow-genome-countermeasures.md` `SG-HalfSealedClaim-A` (Phase 75) — adjacent: structural gaps below the ceremonial-verification surface. Same root family, different leverage point.
