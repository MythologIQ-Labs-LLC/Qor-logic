# Tutorial Narration Beats

One beat before each phase. Keep each beat to 3-5 sentences: what this phase
proves, which gate artifact it writes, and which doctrine terms the operator
will meet.

## The term rule (binding for this bundle)

At a term's FIRST use, link it to its glossary home:
`[intent lock](../../../references/glossary.md)` -- then use it bare
afterwards. NEVER restate a definition in narration prose; the glossary is
the single definition home, and restated definitions register as term drift
at the seal gate.

## Beats

### Before /qor-ideate
This phase turns "that badge looks stale" into a scoped intent with a success
boundary. It is the only phase where changing your mind is free. Artifact:
none yet -- ideation feeds research. Terms to link: ideation readiness,
success boundary.

### Before /qor-research
Nothing in this chain is allowed to rest on assumption: research verifies the
target against source with file:line citations and writes the first gate
artifact (`research.json`). Terms to link: research brief, gate artifact,
session.

### Before /qor-plan
The plan is the contract the rest of the chain enforces: change_class picks
the version bump, the test list names behaviors (not artifacts), and the
Definition of Done declares acceptance up front. Artifact: `plan.json` bound
to the plan file's content hash. Terms to link: change_class, Definition of
Done, Locked Decision.

### Before /qor-audit
An adversarial judge now tries to find reasons to REJECT the plan; PASS is
binding and so is VETO. A VETO here costs minutes -- the same defect found in
production costs days; that asymmetry is the whole business case. Artifact:
`audit.json` with the verdict and the plan's content hash. Terms to link:
tribunal, VETO, intent lock.

### Before /qor-implement
Test first: watch the new test FAIL before the change exists, then pass twice
(determinism check). The failing run is evidence the test can actually catch
the regression it guards. Artifact: `implement.json` listing files touched.
Terms to link: TDD-Light, red-then-green.

### Before /qor-substantiate
The seal ceremony re-verifies everything (reality equals promise), bumps the
version per change_class, stamps the changelog, and appends the hash-chained
ledger entry. We stop at the LOCAL review boundary -- you will see the exact
publish commands without running them. Artifact: `substantiate.json` with the
Merkle seal. Terms to link: seal, Merkle chain, review boundary.

## Debrief script

Show, in order: the new ledger entries (`docs/META_LEDGER.md` tail), the gate
directory (`.qor/gates/<session>/`), the plan file, the version/changelog
delta, and the held publish commands. Close with: the next real cycle is the
same chain -- `/qor-help` lists every skill, and the delegation table says
which skill handles which failure.
