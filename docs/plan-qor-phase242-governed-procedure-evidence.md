# Plan: Phase 242 — portable governed-procedure execution evidence

**change_class**: feature

**doc_tier**: standard

**originating_issue**: GH #384

**predecessor**: Phase 241 / PR #383 (`phase/241-portable-governance-boundary`)

## Objective

Implement the smallest canonical-Qor primitive that can deterministically answer:

> Does the complete policy-derived set of required governed procedures have valid execution evidence for this exact governed subject?

Phase 242 implements portable evidence **meaning and satisfaction semantics**. It does not implement a universal signer, hosted observer, GitHub integration, or enterprise trust service.

## Architectural boundary

Canonical Qor owns:

- exact procedure identity semantics;
- exact governed-subject binding semantics;
- evidence-class satisfaction rules;
- required-set completeness checking;
- deterministic fail-closed evaluation;
- the distinction between an execution claim and a claim independently verified by a trusted boundary.

Execution hosts / trusted wrappers own:

- resolving and executing the exact governed procedure bytes;
- observing execution;
- verifying concrete signatures, HMACs, workload identities, or other provider-specific attestations;
- converting successful verification into a claim-bound trusted fact supplied to the Qor evaluator.

Downstream enterprise layers may choose stronger accepted evidence classes and trusted principals. They do not redefine what those classes mean.

## Critical trust rule

Externally verified claims are **not serialized inside the evidence contract**.

The evaluator receives them as a separate trusted input. Each verified claim binds:

- `evidence_id`;
- the SHA-256 of the exact canonical evidence claim;
- the independently authenticated principal id.

This prevents an evidence producer from self-promoting an agent declaration by adding a field that merely says `verified: true`, and prevents verification of one claim from being replayed after its observer, subject, procedure bytes, or status are mutated.

## Contract V1

A procedure requirement contains:

- stable requirement id;
- procedure name;
- source repository;
- source revision;
- source path;
- exact procedure-byte SHA-256;
- governed subject kind;
- governed subject repository;
- governed subject id;
- governed subject revision;
- governed subject SHA-256;
- optional exact input SHA-256;
- explicitly accepted evidence classes;
- trusted principals when an independently observed class is accepted.

An evidence claim contains the same procedure and subject binding plus:

- evidence id;
- invocation id;
- evidence class;
- execution status;
- observer id for independently observed classes;
- optional input/output SHA-256 values.

V1 evidence classes are intentionally categorical, not ordinal:

- `agent-declared`
- `wrapper-observed`
- `ci-attested`

`wrapper-observed` and `ci-attested` require a matching trusted verified-claim fact. Verification does not promote an `agent-declared` claim into either independent class.

`human-declared` is deliberately excluded from V1. Without an authenticated-human identity contract, it would be a stronger-sounding JSON assertion that the governed actor could mint. A future human declaration class requires explicit identity and verification semantics before admission.

## Evaluation invariants

1. Every requirement in the required set is evaluated. Omission cannot disappear from the verdict.
2. Procedure identity matches exactly across name, repository, revision, path, and byte digest.
3. Subject identity matches exactly across kind, repository, id, revision, and digest.
4. When a requirement declares `inputSha256`, evidence must match it exactly.
5. Only explicitly accepted evidence classes are eligible.
6. A failed invocation does not satisfy an execution requirement.
7. Independently observed classes require both an explicitly trusted observer and a verified-claim fact bound to the exact evidence digest.
8. Evidence classes do not imply human approval, merge authority, release authority, or any other consequence grant.
9. Unknown evidence classes fail schema validation.
10. Duplicate requirement ids or evidence ids fail contract validation.

## Existing primitive reuse

Phase 158 already provides:

- per-session local HMAC provenance sidecars, with the documented in-repository-actor ceiling;
- keyless committed sidecar verification;
- optional CI-secret attestation over sealed ledger hashes.

Phase 242 does not stretch those primitives into a claim they do not prove. A trusted wrapper or CI integration may later use existing or new provider-specific verification and then supply the resulting claim-bound trusted fact to this evaluator.

## Affected files

- `qor/gates/schema/procedure_execution_evidence.schema.json` — new portable V1 evidence contract schema.
- `qor/compliance/procedure_evidence.py` — deterministic evaluator and trusted verified-claim boundary type.
- `qor/references/procedure-execution-evidence.md` — draft semantic reference; formal doctrine promotion is deferred until audit/substantiation.
- `tests/test_procedure_evidence.py` — adversarial behavioral coverage.
- `docs/FEATURE_INDEX.md` — add the evaluator only after repository CI proves the behavior.

## New ceremony artifact justification

`new_ceremony_artifacts`:

- `procedure_execution_evidence.schema.json` — This schema is necessary because governed-procedure execution evidence crosses runtime and repository boundaries and must retain one portable, machine-validated meaning. Reusing an unrelated gate schema would weaken exact procedure, subject, evidence-class, and verification binding while hiding those semantics behind a structurally incompatible artifact.

## Explicit non-goals

Phase 242 does not:

- create signatures or a PKI;
- add a hosted signer service;
- add a GitHub client or GitHub App;
- persist trust decisions;
- accept a self-asserted `verified` flag from evidence JSON;
- infer evidence strength with a model;
- create a universal evidence-strength ranking;
- prove model cognition;
- require strong independent evidence for every Qor skill;
- let execution evidence substitute for independent human or consequence authority.

## Behavioral tests

The focused suite must prove at least:

- exact independently verified claim passes;
- missing independent verification fails;
- verification is bound to the exact claim digest;
- same procedure name with wrong bytes fails;
- prior-head evidence fails;
- evidence copied from another change fails;
- untrusted observer fails;
- verified agent self-report does not promote evidence class;
- agent declaration passes only when policy explicitly allows it;
- unauthenticated `human-declared` evidence is schema-rejected in V1;
- failed invocation fails;
- required input digest mismatch fails;
- omitted required procedure fails completeness;
- independent evidence requirement without trusted principals is rejected;
- duplicate evidence ids are rejected;
- unknown evidence class is rejected.

## CI Commands

- `python -m pytest tests/test_procedure_evidence.py -q`
- `python -m pytest tests/ -q`
- `python qor/scripts/check_variant_drift.py`
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md`
- existing gate-chain completeness and provenance jobs

## Governance note

The operator explicitly authorized continued implementation after the post-#131 adversarial review. This plan does not claim a new formal `/qor-audit` PASS or substantiation result. The stacked PR remains draft until repository CI and the normal evidence path support promotion.

Phase 242 deliberately keeps the semantic note as a draft reference rather than increasing the published doctrine inventory before the contract has completed its evidence/admission path.

## Definition of done

- The portable contract and evaluator are implemented without introducing a second evidence authority.
- The evaluator fails closed on the adversarial cases above.
- Focused and full repository CI pass.
- Any feature-index row is added only after behavioral evidence exists.
- GH #384 remains open until the implementation is integrated and its evidence/admission path is complete.
