# Phase 290 Plan: Governance Freshness and Supersession Control

**Issue:** GH #500, child of #497  
**Change class:** governance  
**State:** proposed; implementation prohibited until `/qor-audit` PASS

## Intent

Strengthen the existing Governance Index so Qor can distinguish document freshness from semantic authority lifecycle. This phase extends the current owner rather than creating a second registry.

## Locked decisions

### LD-1 — One registry

`docs/GOVERNANCE_INDEX.md` remains the authoritative governance-artifact registry. No parallel freshness or supersession registry is introduced.

### LD-2 — Date freshness is not authority state

`Last Reviewed` continues to describe review currency only. It MUST NOT encode whether an artifact is current, amended, superseded, or historical.

### LD-3 — Tier 2 gains explicit authority lifecycle

Tier 2 rows gain machine-readable authority lifecycle metadata. V1 statuses are a closed vocabulary:

- `current`
- `amended`
- `superseded`
- `historical`

Each row also declares `Supersedes` as either `—` or one or more registered artifact paths. A new artifact that does not replace prior authority explicitly declares itself additive through `Supersedes: —`.

### LD-4 — Fail closed on authority ambiguity

The Governance Index checker MUST report a defect when:

- a Tier 2 row lacks a recognized lifecycle status;
- a `Supersedes` target is not registered;
- an artifact marked `superseded` is simultaneously selectable as current authority;
- a historical artifact is selected as current authority;
- a supersession cycle exists;
- two current artifacts make an explicit replacement claim over the same authority without an explicit amendment relationship.

Unknown or contradictory authority state is not silently ranked by date, table order, filename, or prose similarity.

### LD-5 — ADR implementation status is reconciled

An ADR that remains `Proposed` after a sealed implementing phase is a governance defect unless the ADR or registry records an explicit allowed reason. V1 may report this conservatively where implementation evidence is mechanically available; it MUST NOT fabricate implementation state from semantic inference.

### LD-6 — Historical evidence remains immutable

Supersession changes authority selection, not history. Historical plans, ledgers, review outputs, and archived artifacts remain evidence of what was true at the time.

### LD-7 — Review guidance expands before automation claims completeness

Adversarial/self-review guidance must explicitly challenge requirement completeness, environment-model completeness, evaluator adequacy, evidence freshness, authority, operational/recovery posture, Shadow Genome impact, and supersession.

## Implementation slice

1. Extend Tier 2 of `docs/GOVERNANCE_INDEX.md` with `Status` and `Supersedes` columns.
2. Classify every existing Tier 2 artifact using the closed vocabulary, with evidence for any non-current classification.
3. Extend the existing governance-index checker/parser rather than introducing a new checker family.
4. Add behavioral tests for missing/invalid status, invalid target, supersession cycle, stale current-authority selection, and a valid additive/current case.
5. Add ADR proposed-after-implementation detection only where implementation evidence is mechanically bound; otherwise emit a visible unresolved finding rather than guessing.
6. Update adversarial/self-review guidance with the eight #500 review questions.
7. Re-run Governance Index drift checks and full repository CI.

## Required behavioral evidence

- A valid current additive Tier 2 artifact passes.
- A missing or unknown lifecycle status fails.
- A superseded artifact cannot be selected as current authority.
- An unregistered supersession target fails.
- A supersession cycle fails.
- `Last Reviewed` changes do not alter authority state.
- Historical artifacts remain referenceable as history without becoming current authority.
- ADR status drift is reported only from mechanically bound implementation evidence.

## Non-goals

- rewriting frozen historical documentation;
- creating a second governance index;
- inferring authority from timestamps;
- broad #498 evidence-envelope implementation;
- #499 Shadow Spectrum runtime wiring;
- Qortara Logic migration.

## Promotion gate

No implementation begins until this plan receives a formal `/qor-audit` PASS. Mechanical CI is necessary but not sufficient.

## CI Commands

```bash
python -m pytest tests -q
python -m ruff check qor tests
python -m qor.scripts.governance_index_check
```

If the governance-index checker exposes a different canonical CLI on `main`, use that existing entry point rather than adding an alias solely for this plan.
