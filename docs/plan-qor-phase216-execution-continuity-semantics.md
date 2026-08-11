# Plan: execution-continuity semantics (Phase 216, Phase B of GH #285)

**change_class**: feature

**doc_tier**: system

**terms_introduced**: execution continuity, execution checkpoint, verification receipt, continuity outcome, stale receipt, live writer, successor actor, continuity contract version

**boundaries**:
- limitations: Qor-logic classifies and routes continuity evidence. It does not
  define the checkpoint, reconstruction, or receipt schemas, does not write
  receipts, and does not evaluate leases or claims. It consumes those artifacts
  by shape and by declared contract version. Conformance to that version is
  asserted by the operator, not verified here; LD-5 states the ceiling.
- non_goals: No named execution vendor enters gate semantics. No upstream field
  definitions are copied into skill prose or schema. No change to
  `intent_lock`'s ancestry semantics. No worker gains merge, release,
  deployment, credential, or policy-mutation authority. No checkpoint store is
  built in the Shadow Genome.
- exclusions: The upstream executable contract itself is out of scope. GH #39
  (target compilation), #51 (ledger identity), #108 (evidence integrity), and
  #139 (Shadow Genome) remain authoritative and are referenced, not re-decided.

## Open Questions

None.

## Locked Decisions

**LD-1 — The receipt binding sits beside `intent_lock`, never inside it.**

`git show HEAD:qor/reliability/intent_lock.py | grep -n 'is-ancestor' -> 159:        ["git", "merge-base", "--is-ancestor", captured_head, "HEAD"],`

`intent_lock` verifies by ancestry, deliberately since Phase 43, so the implement
commit may advance HEAD between capture and verify. GH #285 requires exact
revision equality in three clauses: the verification target is the exact revision
under review; a receipt whose revision differs from head is stale; revision
movement after verification requires re-verification.

These are different questions. `intent_lock` asks whether this is still the work
that was audited; the receipt asks whether this exact tree was verified. Folding
the second into the first either strips the Phase 43 tolerance that normal
implementation depends on, or lets receipt checking inherit ancestry -- under
which a receipt cut at commit A still passes after head moves to B, which is the
stale acceptance the issue forbids. Exact equality lives in the new classifier.

**LD-2 — `inconclusive` is a new value in a new field, not an addition to an
existing enum.**

`git show HEAD:qor/gates/schema/validate.schema.json | grep -n '"skip"' -> 20:          "status": { "type": "string", "enum": ["pass", "fail", "skip"] },`

`skip` already means the Phase 75 disclosed-skip: a prerequisite is absent and
the gate deliberately did not run, which is acceptable to seal. `inconclusive`
means the gate ran and the environment denied it a conclusion, which must route
to evidence-environment repair rather than to seal.

Adding `inconclusive` to `validate.status` would both overload a settled token
and change an enum existing consumers read. The continuity outcome therefore
occupies its own field, `continuity_outcome`, with enum
`verified | rejected | inconclusive`. Existing enums are untouched.

That field needs a persisted home, or the two skills instructed to route on it
are routing on nothing. It is added as an optional property to
`qor/gates/schema/validate.schema.json` and
`qor/gates/schema/remediate.schema.json`, the two artifacts whose skills GH #285
requires to route typed outcomes. Both remain optional so existing artifacts stay
valid, and `validate.status` keeps its `pass | fail | skip` enum unchanged --
asserted directly by a regression test, because the whole decision is that these
two vocabularies stay separate.

**LD-3 — Qor-logic ships an executable classifier, because the issue's own test
bar requires one.**

GH #285's final required test rejects presence-only assertions where runtime
behavior is claimed. Nine of its thirteen required tests -- resumability under
exhaustion, fail-closed on missing or malformed checkpoint, live-writer
rejection, revision mismatch, exact-revision acceptance, staleness after head
movement, environment outage yielding `inconclusive`, self-report insufficiency,
worker-authority containment -- are decisions over typed inputs with nothing to
invoke if this repository ships only skill prose.

The ownership boundary grants the upstream line the schemas and their validators
and grants Qor-logic "audit classifications and fail-closed checks." Those are
not the same artifact. A classifier consuming contract-shaped inputs it does not
define, returning an outcome plus a routing directive, is what makes the thirteen
tests meetable without duplicating a single upstream field definition.

**LD-4 — Checkpoints and receipts reference derived ledger identity, never entry
numbers.**

`git show HEAD:qor/reliability/ledger_base_currency.py | grep -n 'derive_entry_id' -> 104:        eid = entry_id.derive_entry_id(e["ts"], e["phase"], e["content_hash"])`

GH #51 is closed and `derive_entry_id(ts, phase, content_hash)` is the settled
identity. The demonstration is live in this repository: the ledger runs #531 ->
#533 because #532 was allocated in an abandoned session and never committed, the
chain is intact because #533 links to #531, and `ledger_hash verify` reports OK
having no contiguity check (GH #316). A checkpoint citing "entry #532" would
reference nothing and nothing would detect it.

**LD-5 — The contract pin is asserted, not verified, and the phase says so.**

`git show HEAD:qor/scripts/qorlogic_config.py | grep -n 'def load_section' -> 22:def load_section(repo_root: Path | None, name: str) -> dict:`

The pinned compatibility version is read from `.qorlogic/config.json` through the
existing tolerant reader, following the `external_reviewer` precedent. Qor-logic
records that it declares compatibility with version X. It cannot check that a
received artifact conforms to X without holding the upstream schema, which the
ownership boundary forbids duplicating.

The pin is therefore assertable but not verifiable from this repository. That
ceiling is stated in the skill prose, in the classifier's own output, and in the
seal entry. A declaration that reads like a guarantee while delivering an
assertion is the shape of GH #314, filed this week; naming the limit is the
countermeasure.

**LD-6 — Vendor-neutrality is tested as outcome-independence, not name absence.**

`qor-audit/SKILL.md` carries three vendor-name occurrences and
`qor-remediate/SKILL.md` two, all legitimate optional-integration references to
the codex-plugin adversarial path that falls back to solo and logs a capability
shortfall. GH #285 forbids named vendors in core semantics, not their mention.

The test asserts that the classifier returns identical outcomes for evidence
differing only in provider identity. A grep-for-vendor-names test would go red on
existing legitimate text and would not test the property that matters.

## Phase 1: Declaration surface

### Unit Tests

- `tests/test_continuity_declaration.py::test_lint_accepts_versioned_declaration` -
  invokes `plan_continuity_lint.lint()` on a plan declaring a well-formed
  `execution_continuity` block and asserts exit 0 with zero findings.
- `::test_lint_rejects_malformed_declaration` - parametrized over missing
  contract version, unknown key, non-string revision, and empty successor-actor
  list; asserts a non-zero exit and a specific finding code for each.
- `::test_plan_schema_accepts_and_rejects_declaration` - validates a plan payload
  carrying `execution_continuity` against `plan.schema.json` via
  `validate_gate_artifact`, and asserts a malformed block is rejected.
- `::test_contract_pin_reads_from_config` - writes a `.qorlogic/config.json` with
  an `execution_continuity.contract_version` value, calls the reader, and asserts
  the returned pin; asserts absent config yields the disclosed-unpinned state
  rather than raising.
- `::test_continuity_outcome_persists_in_routing_artifacts` - validates a
  `validate` payload and a `remediate` payload carrying `continuity_outcome`
  against their schemas; asserts each of `verified`, `rejected`, and
  `inconclusive` is accepted and a fourth value is rejected. This is what makes
  the outcome routable rather than merely returned.
- `::test_status_and_outcome_vocabularies_stay_separate` - the LD-2 regression.
  Asserts `validate.status` still enumerates exactly `pass`, `fail`, `skip`, and
  that `inconclusive` is absent from it. Fails the moment someone takes the
  cheap path of widening the existing enum.
- `::test_no_upstream_field_duplication` - the thirteenth required behavior,
  stated as a property Qor-logic can actually check. Asserts three things: the
  `execution_continuity` declaration's key set is a subset of a closed
  Qor-owned allowlist exported by `continuity_contract.py`; the declaration
  carries `contract_version` and no key holds a nested object, so it references
  the contract by version rather than restating its structure; and
  `continuity_outcome` is a bare string enum of exactly the three values.

  The obvious phrasing -- "no upstream field name appears in Qor-logic" --
  is not testable here and was rejected. Enumerating upstream field names to
  assert their absence would require holding the upstream schema, which is the
  precise thing LD-5 says this repository does not have. An allowlist of
  Qor-owned keys tests the same property from the side Qor-logic can see: not
  "we did not copy their fields", but "we carry only our own, and only
  scalars". Duplication cannot hide inside a declaration that admits no nested
  structure.

### Affected Files

- `qor/gates/schema/plan.schema.json` - add optional `execution_continuity`
  object; `required` is unchanged so existing plans stay valid.
- `qor/gates/schema/validate.schema.json` - add optional `continuity_outcome`;
  the existing `status` enum is untouched.
- `qor/gates/schema/remediate.schema.json` - add optional `continuity_outcome`.
- `qor/scripts/continuity_contract.py` - NEW. Declaration shape, the config-backed
  pin reader delegating to `qorlogic_config.load_section`, and the disclosed
  -unpinned state.
- `qor/scripts/plan_continuity_lint.py` - NEW. Plan-declaration lint following the
  established `plan_*_lint` argv-only pattern.
- `tests/test_continuity_declaration.py` - NEW.

### Changes

The declaration binds base and target revision, contract version, permitted
successor actor classes, checkpoint production points, and receipt requirement.
No upstream field definition is restated; the block references the contract by
version and carries only what Qor-logic itself routes on.

## Phase 2: The classifier

### Unit Tests

- `tests/test_continuity_gate.py::test_valid_checkpoint_under_exhaustion_is_resumable` -
  invokes `classify()` with provider-exhaustion interruption plus a well-formed
  checkpoint; asserts outcome `verified` and a resume directive naming an
  authorized successor class, not human escalation.
- `::test_missing_or_malformed_checkpoint_fails_closed` - parametrized over
  absent, truncated, and tampered-digest checkpoints; asserts `rejected` for each
  with distinct reason codes.
- `::test_live_writer_and_claim_conflict_rejected` - asserts `rejected` when a
  competing writer holds the claim.
- `::test_revision_mismatch_prevents_continuation` - asserts `rejected` when the
  checkpoint's target revision differs from the current revision.
- `::test_receipt_accepted_only_for_exact_revision` - asserts `verified` when the
  receipt revision equals the target and `rejected` when it is an ancestor. The
  ancestor case is the LD-1 regression: it must fail, where `intent_lock` would
  pass.
- `::test_receipt_goes_stale_after_head_movement` - asserts a previously accepted
  receipt returns stale once the target revision advances.
- `::test_environment_outage_yields_inconclusive` - asserts `inconclusive` with an
  environment reason, and asserts it is neither `verified` nor `rejected`.
- `::test_self_report_cannot_satisfy_verification` - asserts prose or status-badge
  evidence without a receipt returns `rejected`, never `verified`.
- `::test_worker_authority_cannot_expand` - parametrized over merge, release,
  deployment, credential, and policy-mutation requests; asserts each is refused
  regardless of checkpoint validity.
- `::test_outcome_is_independent_of_provider_identity` - LD-6. Asserts identical
  outcomes for two evidence bundles differing only in provider name.

### Affected Files

- `qor/scripts/continuity_gate.py` - NEW. `classify()` returning an outcome, a
  reason code, and a routing directive.
- `tests/test_continuity_gate.py` - NEW.

### Changes

`classify()` is a pure function over already-parsed inputs; the module performs no
network access and no upstream-schema validation. Section 4 limits apply: if the
reason-code table plus `classify()` approaches the file cap, the reason codes move
to `continuity_contract.py` rather than growing a second decision site.

## Phase 3: Lifecycle wiring

### Affected Files

- `qor/skills/sdlc/qor-research/SKILL.md` - durable-versus-volatile fact
  distinction; provider session URLs are evidence metadata, never authority.
- `qor/skills/governance/qor-plan/SKILL.md` - the required declarations.
- `qor/skills/governance/qor-audit/SKILL.md` - the fail-closed classifications,
  and that a plan must consume the contract by version rather than duplicate it.
- `qor/skills/sdlc/qor-implement/SKILL.md` - tests before continuity behavior;
  checkpoint before voluntary handoff; successor reconstruction assessment;
  no secrets in checkpoints.
- `qor/skills/governance/qor-substantiate/SKILL.md` - exact-revision receipt
  requirement; artifacts referenced by path and digest, not duplicated in ledger
  prose; verification kept separate from merge, release, and deployment.
- `qor/skills/sdlc/qor-validate/SKILL.md` and `qor/skills/sdlc/qor-remediate/SKILL.md` -
  typed-outcome routing for `verified`, `rejected`, and `inconclusive`.

### Changes

Operative instructions inline; rationale to each skill's `references/`. The two
constrained skills carry 1,547 and 1,120 bytes of slack against the 39,936-byte
lock, so additions there are measured before and after and must not exceed it.

## Phase 4: Glossary and documentation

### Affected Files

- `qor/references/glossary.md` - the eight declared terms, each with `home` and
  `referenced_by`. The `skip` versus `inconclusive` distinction is written into
  the `continuity outcome` entry, because LD-2 exists to prevent that conflation.
- `qor/references/doctrine-execution-continuity.md` - NEW. The doctrine home.
- `docs/architecture.md`, `docs/lifecycle.md` - the new module and gate behavior.

### Changes

Per LD-5, the doctrine states plainly that the contract pin is asserted and not
verified, and why that ceiling is structural rather than an omission.

## Phase 5: Verification

### Unit Tests

- The two new test modules, run twice for determinism.
- The full suite.
- `skill_size_budget_lint` with a before/after measurement for the two
  constrained skills.
- `dist_compile` with a zero-drift check, since variants embed skill bodies.

### Affected Files

None beyond Phases 1-4.

### Changes

None. Phase 215 recorded that a focused suite alone missed dist drift; the same
verification shape applies here.

## Definition of Done

### Deliverable: provider-neutral continuity semantics

- **D1**: A provider stopping for budget, context, capacity, credentials, or
  environment is classified as resumable when a valid checkpoint exists, rather
  than as product failure or automatic human escalation.
- **D2**: `qor/scripts/continuity_gate.py` and `qor/scripts/continuity_contract.py`
  ship with `plan_continuity_lint.py` and the `plan.schema.json` declaration.
- **D3**: Seal entry records the contract version pinned, the LD-5 ceiling, and
  the before/after sizes of the two constrained skills.
- **D4**: All thirteen behavioral tests from GH #285 pass, each invoking the unit
  under test. No test asserts only that an artifact exists.

### Deliverable: fail-closed evidence handling

- **D1**: Absence, malformation, tampering, revision mismatch, live-writer
  conflict, claim conflict, and actor-authority mismatch each fail closed with a
  distinct reason code.
- **D2**: `continuity_outcome` carries `verified | rejected | inconclusive` as
  distinct values; no existing enum is modified.
- **D3**: Seal entry states that `inconclusive` is not `skip` and why the
  conflation was refused.
- **D4**: A receipt bound to an ancestor revision is REJECTED by
  `test_receipt_accepted_only_for_exact_revision`. This is the LD-1 regression and
  is the single test that proves the classifier did not inherit `intent_lock`'s
  ancestry semantics.

### Deliverable: no duplicated authority

- **D1**: Upstream schemas are referenced by version; no field definition is
  copied into Qor-logic prose or schema, asserted by
  `test_continuity_declaration.py::test_no_upstream_field_duplication`.
- **D2**: No named execution vendor appears in gate semantics; existing optional
  integrations are unchanged.
- **D3**: Seal entry states that #39, #51, #108, and #139 remain authoritative and
  were not re-decided.
- **D4**: `test_outcome_is_independent_of_provider_identity` passes, asserting
  outcome equality across provider identity.

## Feature Inventory Touches

| Feature | Touch | Source-of-truth | test_descriptor |
|---|---|---|---|
| Continuity classification | NEW | `qor/scripts/continuity_gate.py` | `test_continuity_gate.py::test_valid_checkpoint_under_exhaustion_is_resumable` asserts a resume directive is returned |
| Plan continuity declaration | NEW | `qor/scripts/plan_continuity_lint.py` | `test_continuity_declaration.py::test_lint_rejects_malformed_declaration` asserts a finding code per malformation |

## CI Commands

- `python -m pytest tests/test_continuity_gate.py tests/test_continuity_declaration.py -q` — the thirteen behavioral tests.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `python -m ruff check qor/ tests/` — the new modules are lint clean.
- `qor-logic scripts skill_size_budget_lint --skills-root qor/skills` — the two constrained skills stay under the lock.
- `qor-logic scripts dist_compile` — variants rebuilt with zero drift.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase216-execution-continuity-semantics.md` — this plan asserts each path and command identically at every site.
