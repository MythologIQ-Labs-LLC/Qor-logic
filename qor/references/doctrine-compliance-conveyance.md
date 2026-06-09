# Doctrine: Compliance Conveyance

Qor-logic's value to a downstream project is the compliance protection it
*conveys*: the gate scripts, doctrines, schemas, and provenance machinery that a
consumer installs and runs at every seal. A Qor-logic update that silently
weakens a gate strips that protection from every consumer on their next seal.
This doctrine makes the conveyed protection provably complete and
non-regressable.

## Compliance Control Matrix

A declarative registry at `qor/compliance/control_matrix.json` (schema:
`qor/gates/schema/control_matrix.schema.json`) records every conveyed control as
a row: `id`, `framework`, `control`, `enforcing_module`, `posture`, `detection`,
`wired_into`, and `variants`. The matrix is the single source of truth for what
Qor-logic claims to enforce; the conformance test verifies reality matches each
row, and the ratchet guards the set across releases.

The matrix is seeded with the deterministic, already-shipping controls; it is a
working mechanism plus an initial registry, not an exhaustive enumeration. New
controls append. The matrix carries an empty `waivers` array consumed by the
ratchet.

## Control Posture

A control's posture records how hard its gate fails: `ABORT` (a hard-fail that
halts the seal/audit -- shell `|| ABORT`, an `exit 1`, or an audit `VETO`) or
`WARN` (a `|| true` advisory that records a finding without halting). The
conformance test reads the posture from the declared skill step and fails when a
declared `ABORT` control carries a `|| true` marker (a silent downgrade) or a
declared `WARN` control lacks one.

## Conveyance Conformance

The conformance verifier (`qor.scripts.compliance_conformance`) checks, for each
matrix row, that the control is wired at its declared posture and reaches the
conveyed payload. It dispatches on the row's `detection` mode:

- `skill-marker`: the declared skill step contains the invocation at the
  declared posture, AND every declared variant's compiled skill carries the
  invocation (claude/codex/kilo-code compile to `skills/<name>/SKILL.md`; gemini
  to `commands/<name>.toml`).
- `test`: the named behavioral test exists (a control claiming test-enforcement
  cannot point at a vanished test).
- `ci-job`: the named workflow references the enforcing module.

The verifier runs as a pytest gate in CI, so a downgraded or un-conveyed control
reds every pull request. The mechanism is self-validating: a wrongly-recorded
posture reds its own conformance test.

## Compliance Ratchet

The ratchet (`qor.scripts.compliance_ratchet`) compares the current matrix
against the matrix at the prior release ref (`git show <ref>:...`). A regression
is a control that was dropped, or whose posture was downgraded `ABORT -> WARN`,
relative to the prior release. A regression fails CI unless a `waivers` entry
names the control with a non-empty `justification` and `issue`. Growth -- adding
controls or strengthening posture -- is always allowed. The effect is monotonic:
conveyed compliance can only hold or strengthen across versions. First
introduction (no matrix at the prior ref) is a no-op.

## Scope

Hooks (Claude Code session hooks, git hooks) are an out-of-scope trigger layer
for this doctrine; the controls here are enforced through the existing
skill-gate, behavioral-test, and CI-job substrate.

## Engagement Manifest + Enforcement Runner (Phase 142)

The control matrix is also the engagement manifest a downstream enforcement SDK consumes. Two
precursor fields make a control engageable:

- `engagement`: the active enforcement layers a control plugs into -- one or more of
  `pre-commit`, `pre-push`, `pre-tool-write`, `ci`, `seal`. This is the precursor value a downstream
  trigger reads to decide what should fire at its point.
- `runner`: for a control standalone-runnable at a runnable point (`pre-commit`/`pre-push`/
  `pre-tool-write`), the `{module, entry, args}` the SDK imports and calls; `null` for controls that
  only engage at `ci`/`seal` (run in the audit/seal flow, not standalone).

The mini-SDK (`qor.compliance.enforce`, re-exported at `qor.sdk`, surfaced as `qor-logic compliance
enforce --engagement <point>`) loads the control definitions from the installed package, selects the
controls wired to the requested engagement point that carry a runner, runs each against the
consumer's working tree, and returns a `Verdict` (ABORT-posture failures fail the verdict; WARN
failures are advisory). The conveyance conformance test verifies every control engaging a runnable
point has an importable, callable runner.

**Ownership boundary**: Qor-logic owns the manifest, the uniform runner behavior, and the verdict
shape; the downstream consumer owns the trigger -- their git hook, editor hook, or CI step calls
`qor-logic compliance enforce --engagement <point>` and acts on the exit code. Hooks themselves are
addressed exclusively downstream. Two packaging invariants must hold or conveyance silently fails:
`compliance/*.json` ships in package-data, and the import package is `qor`.
