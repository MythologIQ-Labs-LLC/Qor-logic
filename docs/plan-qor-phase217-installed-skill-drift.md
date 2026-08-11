# Plan: installed skill-corpus drift detection (Phase 217, GH #314)

**change_class**: feature

**doc_tier**: system

**terms_introduced**: skill corpus digest, install scope resolution, inert control

**boundaries**:
- limitations: Detection and disclosure only. The check reports which installed
  corpus produced a seal; it does not prevent an operator from running a
  divergent one, and cannot, because the skill executing the check is itself
  part of the corpus under test. That ceiling is stated, not implied.
- non_goals: No change to `qor-logic install` behavior beyond invoking it once
  to resync. No new host archetype. No attempt to make the seal fail-closed on
  drift in V1 -- disclosure first, per the WARN-then-enforce precedent.
- exclusions: The #319 umbrella items (#313, #316, #318) are a different family
  and are out of scope here.

## Open Questions

None.

## Locked Decisions

**LD-1 — The defect is noise, not silence, and the fix is scope resolution.**

`git show HEAD:qor/scripts/install_drift_check.py | grep -n 'def check' -> 27:def check(host: str = "claude", scope: str = "repo") -> list[str]:`

The default scope is `repo`. Verified by running it: `.claude/skills/` does not
exist in this repository, so `check()` returns **30 findings** -- one
`missing install` per source skill -- at exit 1, on every invocation.

An earlier draft of the research brief recorded this as a silent pass. That was
wrong and is corrected in ledger entry #541. The distinction matters for the
remedy: a silent check needs to be made loud, whereas this one needs to be made
quiet where it is meaningless. An absent scope is one fact -- "not installed
here" -- not thirty defects.

**LD-2 — Three defects compound; fixing one leaves the control inert.**

`git show HEAD:qor/skills/sdlc/qor-plan/SKILL.md | grep -n 'install_drift_check' -> 125:qor-logic scripts install_drift_check --host claude --scope repo || \`

The sole invocation is at the wrong scope, cannot block (`|| echo` collapses all
findings into one line), and runs only at plan time. Correcting the scope alone
still yields a warning nobody reads; adding a seal-time call alone still points
at an unused directory. The phase addresses all three or it addresses nothing.

**LD-3 — Record the corpus that produced each seal.**

`git show HEAD:qor/gates/schema/substantiate.schema.json | grep -n '"required"' -> 7:  "required": [`

No seal artifact carries a skill-corpus digest. Across 541 ledger entries,
nothing answers "which skills ran this seal?" That absence is why the wiring
defects compound: drift is invisible retroactively as well as prospectively.

A single digest over the installed `SKILL.md` set, recorded at seal, makes every
future seal attributable to its ceremony. It is also the only part of this phase
that produces evidence rather than warnings.

**LD-4 — Disclosure in V1, not fail-closed.**

The check cannot be trusted to block yet, because the skill running it is part
of the corpus under test: a drifted `qor-substantiate` could carry a weakened or
absent check. Making it ABORT in V1 would assert a guarantee the architecture
does not support -- the GH #314 failure shape, repeated.

V1 records the digest and the drift count in the seal entry unconditionally. An
operator reading a seal can see the ceremony diverged.

Enforcement is deferred to **GH #320**, filed before this plan was re-audited
rather than named as an intention. That issue carries the three decisions V2
owes -- where enforcement can honestly live given that the checker is inside the
corpus it validates, what threshold constitutes drift, and whether the ledger
should distinguish clean-corpus from drifted-corpus seals at query time -- plus
entry criteria requiring real drift data first.

The precedent invoked here is `merge_velocity_check`, WARN at Phase 93 and
fail-closed at Phase 129. What made that work was a tracked follow-on, not a V1
that mentioned a V2. GH #147 catalogued eleven closures that shipped advisory
and deferred the enforcer to an issue nobody filed; this plan does not join
them. The deferral is recorded as a `D4.d` waiver below.

**LD-5 — Resync last, after the detection fix is green.**

The 27 live global-scope mismatches are the only real test fixture available.
Resyncing first would clear them and leave the new check unable to prove itself
against the condition it exists to catch. Installed skills are generated
artifacts and are overwritten as with any update, per operator instruction.

## Phase 1: Scope resolution

### Unit Tests

- `tests/test_install_scope_resolution.py::test_absent_scope_reports_once_not_per_skill` -
  the core regression. Points `check()` at a scope whose skills directory does
  not exist and asserts exactly ONE finding naming the scope, not one per source
  skill. Fails today with 30.
- `::test_auto_scope_finds_real_mismatch` - builds a synthetic install where one
  skill's bytes differ, calls `check(scope="auto")`, and asserts the mismatch is
  reported with that skill's name.
- `::test_auto_scope_clean_when_synced` - byte-identical install returns no
  findings.
- `::test_installed_scopes_lists_only_present_installs` - asserts
  `installed_scopes()` returns scopes whose skills directory exists, and omits
  those that do not.

### Affected Files

- `qor/scripts/install_drift_check.py` - add `installed_scopes(host)`, add
  `scope="auto"` handling, and collapse the absent-scope case to one finding.
- `tests/test_install_scope_resolution.py` - NEW.

### Changes

`check()` keeps its signature and default so existing callers are unaffected;
`auto` is additive. The absent-scope collapse changes output for a case that is
currently pure noise.

## Phase 2: Skill-corpus digest

### Unit Tests

- `tests/test_skill_corpus_digest.py::test_digest_changes_when_a_skill_changes` -
  computes the digest, mutates one installed `SKILL.md` byte, recomputes, and
  asserts the digests differ.
- `::test_digest_is_order_independent` - asserts the digest is stable when the
  filesystem yields skills in a different order, since directory iteration order
  is not guaranteed across platforms.
- `::test_digest_absent_install_is_disclosed` - asserts an absent install
  returns the disclosed-absent sentinel rather than raising or returning the
  digest of an empty set, which would be indistinguishable from a real corpus.

### Affected Files

- `qor/scripts/skill_corpus.py` - NEW. `digest(host, scope)` over the sorted
  `(skill_name, sha256)` pairs of installed `SKILL.md` files.
- `tests/test_skill_corpus_digest.py` - NEW.

### Changes

Sorted input makes the digest order-independent by construction rather than by
accident of iteration. The empty-corpus case is explicitly distinguished from a
real one; a hash over nothing is a real hash and would otherwise read as
evidence.

## Phase 3: Seal wiring

### Unit Tests

- `tests/test_substantiate_skill_corpus_wiring.py::test_schema_accepts_skill_corpus` -
  validates a substantiate payload carrying `skill_corpus` against
  `substantiate.schema.json`, and asserts a malformed digest is rejected.
- `::test_seal_step_invokes_the_check` - asserts the `/qor-substantiate` skill
  text names `skill_corpus` and `install_drift_check` in an executable step, so
  the wiring cannot be removed while the schema field remains.

### Affected Files

- `qor/gates/schema/substantiate.schema.json` - add optional `skill_corpus`
  object (`digest`, `scope`, `drift_count`).
- `qor/skills/governance/qor-substantiate/SKILL.md` - new step running the check
  at `auto` scope and recording digest + drift count in the seal entry.
- `qor/skills/sdlc/qor-plan/SKILL.md` - Step 0.2 corrected to `auto` scope.
- `tests/test_substantiate_skill_corpus_wiring.py` - NEW.

### Changes

Optional field so existing artifacts stay valid. `qor-substantiate` has 313
bytes of slack against the 39,936-byte lock; the step must be measured before
and after and must not exceed it. If it does not fit, the rationale moves to
`references/seal-gate-ladder.md` and only the operative lines stay inline.

## Phase 4: Record the pattern

### Affected Files

- `docs/SHADOW_GENOME.md` - `SG-InertControl-A`: a control that exists, is
  correct, and is wired so it cannot fire. Distinct from `SG-HalfSealedClaim-A`,
  where the prerequisite is genuinely absent, and from the #319 family, where no
  checker exists at all. `closure_enforcer` cites
  `tests/test_install_scope_resolution.py::test_absent_scope_reports_once_not_per_skill`.

### Changes

The entry names the diagnostic: a control whose default output is
guaranteed-irrelevant trains the operator to ignore it, so noise and silence
fail identically.

## Phase 5: Resync the install

### Affected Files

None tracked. `qor-logic install --host claude --scope global` regenerates the
operator's installed copies from source.

### Changes

Run AFTER Phases 1-3 are green, per LD-5. The seal entry records the drift count
observed BEFORE the resync, since that number is the phase's evidence.

## Phase 6: Verification

### Unit Tests

- The three new test modules, run twice for determinism.
- The full suite.
- `skill_size_budget_lint` with a before/after measurement for
  `qor-substantiate`.
- `dist_compile` with a zero-drift check.

### Affected Files

None beyond Phases 1-4.

## Definition of Done

### Deliverable: drift is detectable

- **D1**: An operator running a divergent skill corpus can find that out from a
  single command, without reading 30 irrelevant findings first.
- **D2**: `install_drift_check.installed_scopes` and `scope="auto"` ship;
  `skill_corpus.digest` ships.
- **D3**: Seal entry records the digest, the scope, and the pre-resync drift
  count of 27.
- **D4**: `test_absent_scope_reports_once_not_per_skill` fails against the
  current implementation and passes after. This is the regression that proves
  the noise defect was real and fixed.

### Deliverable: seals are attributable

- **D1**: A reader of any future seal can tell which skill corpus produced it.
- **D2**: `substantiate.schema.json` carries `skill_corpus`; the seal step is
  wired in `/qor-substantiate`.
- **D3**: Seal entry states that V1 discloses rather than enforces, and why --
  the checking skill is part of the corpus under test.
- **D4**: `test_seal_step_invokes_the_check` fails if the wiring is removed
  while the schema field remains, so the field cannot outlive its producer.
- **D4.d**: **Waiver -- enforcement is not shipped in this phase.** No test can
  assert that a drifted corpus is refused, because V1 deliberately does not
  refuse one. Rationale: the skill running the check is part of the corpus under
  test, so an ABORT wired inside it is unreliable by construction -- the drift
  most worth catching is the drift that removes the catcher -- and CI has no
  operator install to compare against. Shipping a fail-closed gate on that
  architecture would assert a guarantee it does not support.
  **Follow-up phase**: GH #320, with entry criteria requiring observed drift
  counts from V1 before the enforcement point is chosen.

### Deliverable: the pattern is on record

- **D1**: The next inert control is recognized as one.
- **D2**: `docs/SHADOW_GENOME.md` carries `SG-InertControl-A`.
- **D3**: Seal entry records that the research brief's own first draft
  mis-stated this defect as silence rather than noise, and that running the
  check is what corrected it.
- **D4**: `sg_closure_lint` reports zero entries without an enforcer citation.

## Feature Inventory Touches

| Feature | Touch | Source-of-truth | test_descriptor |
|---|---|---|---|
| Install scope resolution | NEW | `qor/scripts/install_drift_check.py` | `test_install_scope_resolution.py::test_absent_scope_reports_once_not_per_skill` asserts exactly one finding for an absent scope |
| Skill-corpus digest | NEW | `qor/scripts/skill_corpus.py` | `test_skill_corpus_digest.py::test_digest_changes_when_a_skill_changes` asserts the digest differs after a one-byte change |

## CI Commands

- `python -m pytest tests/test_install_scope_resolution.py tests/test_skill_corpus_digest.py tests/test_substantiate_skill_corpus_wiring.py -q` — the phase's behavioral tests.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `python -m ruff check qor/ tests/` — the new modules are lint clean.
- `qor-logic scripts skill_size_budget_lint --skills-root qor/skills` — `qor-substantiate` stays under the lock.
- `qor-logic scripts dist_compile` — variants rebuilt with zero drift.
- `qor-logic scripts sg_closure_lint` — the new Shadow Genome entry carries an enforcer citation.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase217-installed-skill-drift.md` — this plan asserts each path and command identically at every site.
