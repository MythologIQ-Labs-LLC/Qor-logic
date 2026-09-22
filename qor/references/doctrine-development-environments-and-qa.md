# Doctrine: Development Environments and Quality Assurance

**Status:** proposed implementation slice for GH #497 / #502; subject to formal `/qor-audit` before merge

## Purpose

Define how Qor distinguishes automated verification, environment fidelity, human quality assurance, acceptance, and production observation.

The problem addressed here is practical: agentic implementation can move faster than human evaluation. Without an explicit QA contract, automated tests become a false proxy for product quality and delivery pressure quietly converts `implemented` into `accepted`.

## Core invariant

> Automated verification establishes bounded technical confidence. Human QA establishes experiential acceptability in a representative environment. Neither substitutes for the other.

## Environment classes

Qor recognizes the following conceptual environment classes.

### development

Fast local, workspace, containerized, or ephemeral environment used while building and debugging.

Characteristics may include:

- developer-local state;
- mocks/stubs;
- reduced datasets;
- development credentials;
- unstable intermediate revisions;
- rapid iteration.

A development PASS does not imply staging or production fitness.

### test

Environment or harness optimized for repeatable automated verification.

Characteristics may include:

- deterministic fixtures;
- isolated dependencies;
- test-specific configuration;
- repeatable automated execution;
- synthetic or bounded datasets.

A test PASS establishes only what the tests and modeled conditions actually cover.

### preview

Per-change or per-branch environment intended for inspection of the integrated change where the delivery platform supports it.

Typical uses:

- rendered UI inspection;
- interactive workflow review;
- stakeholder preview;
- integration behavior using non-production resources.

Preview is useful but may differ materially from production.

### staging

Shared or release-candidate environment intended to represent production closely enough for integration, human QA, operational rehearsal, or acceptance evidence.

Staging fidelity must be described rather than assumed.

### production

The real environment in which actual users, traffic, data, dependencies, policies, and operational conditions exist.

Production evidence participates in the outer assurance-revision loop. Production is not merely a larger test suite.

## Environment collapse

Not every repository requires five physically separate environments.

A project may intentionally collapse conceptual classes, for example:

- development + test;
- preview + staging;
- local executable as the only meaningful pre-production runtime for a desktop application.

Any collapse must be explicit when it affects an assurance claim.

The following equivalences must never be silently assumed:

- `development == staging`;
- `test == staging`;
- `staging == production`;
- `preview == production`.

## Environment fidelity

QA or verification evidence should disclose material differences between the evaluated environment and the target environment.

Examples include:

- mocked or absent third-party services;
- different authentication/identity configuration;
- different authorization policy;
- different secrets or permissions;
- synthetic rather than realistic data;
- reduced data volume;
- absent concurrency/load;
- different network/security boundaries;
- disabled feature flags;
- different infrastructure topology;
- unavailable hardware/device characteristics;
- unavailable production-only integrations.

A staging PASS remains bounded by those differences.

## QA applicability

Human QA is not mandatory for every change.

QA applicability should be determined from the change contract, risk, product surface, and acceptance requirements rather than habit.

Likely QA-required examples:

- user-facing UI or interaction changes;
- responsive/device-specific behavior;
- checkout/payment or other consequential workflows;
- installers, upgrade flows, and migration experiences;
- operator/admin workflows;
- accessibility-sensitive interaction;
- complex integration journeys;
- changes whose acceptability depends on tacit stakeholder intent;
- changes where automated evidence cannot answer the acceptance question.

Likely automation-sufficient examples, absent contrary risk:

- isolated pure-function refactor with strong regression evidence;
- typo-only documentation correction;
- deterministic generated-file correction whose outputs are mechanically verified;
- narrow internal change with no experiential acceptance dimension.

Governed attention/applicability work under GH #501 should eventually automate or assist this determination without creating new authority.

## QA dimensions

A QA profile may include relevant combinations of:

- human functional walkthrough;
- visual quality review;
- responsive/device behavior;
- usability and interaction coherence;
- accessibility experience;
- realistic integration behavior;
- negative/destructive path behavior;
- install/upgrade/migration experience;
- operator/admin workflow;
- recovery/rollback rehearsal;
- human-perceived performance;
- stakeholder/user acceptance testing.

A profile should contain only dimensions relevant to the change.

## Agent role in QA

Agents should make human QA faster and higher quality rather than impersonating it.

Agents may:

- provision or locate the correct environment;
- verify revision/build identity;
- run deterministic preflight;
- derive QA scenarios from the problem/change contract;
- incorporate applicable Shadow Genome patterns into scenario suggestions;
- navigate workflows under bounded authority;
- capture screenshots, logs, traces, and state;
- identify obvious anomalies;
- prepare a compact evidence packet;
- rerun deterministic checks after fixes.

Agents must not label their own observations as human QA when the acceptance question requires human judgment.

## Human role

Human judgment is required when acceptance is materially:

- experiential;
- subjective;
- tacit;
- product/business-sensitive;
- stakeholder-authority scoped;
- dependent on visual or interaction quality that current automated evaluation cannot establish reliably.

Human QA should not waste time repeating deterministic checks machines already prove reliably. Automated preflight should happen first whenever practical.

## QA evidence contract

A durable QA record should bind, as applicable, to:

- exact revision/build/artifact;
- environment identity and class;
- meaningful environment-to-production differences;
- QA profile/checklist version;
- tester or tester authority class where relevant;
- scenarios/surfaces exercised;
- defects discovered;
- defect disposition;
- supporting screenshots/recordings/logs/traces where useful;
- limitations and exclusions;
- timestamp/freshness;
- verdict.

Valid verdict vocabulary:

- `PASS`;
- `FAIL`;
- `CONDITIONAL`;
- `INCONCLUSIVE`.

`Looks good` is not durable QA evidence.

## QA debt

Implemented work can outpace human QA.

Qor should represent this truthfully instead of collapsing it into completion.

Where QA is required, work that has completed implementation and automated verification but not QA should remain visibly pending QA.

Candidate lifecycle state:

`QA_REQUIRED`

The exact machine-state implementation is deferred to a later slice, but the semantic invariant is immediate:

> Work requiring QA must not be represented as fully accepted or promotable while required QA remains unresolved.

## Batching and sampling

QA throughput should scale without degrading trust.

Permitted techniques may include:

- reusable QA profiles;
- agent-prepared evidence packets;
- batching related low-risk changes where independent defect attribution remains possible;
- risk-based sampling for repetitive low-risk changes;
- focused regression journeys rather than full-product repetition;
- explicit acceptance of residual uncertainty by the proper authority.

Sampling must not silently replace mandatory acceptance criteria.

## QA, acceptance, and production observation

These are distinct:

### Verification

Did observed behavior satisfy the written contract under evaluated conditions?

### QA

Does the integrated result behave acceptably through the relevant human/experiential surfaces in the evaluated environment?

### Acceptance

Does the authorized stakeholder or acceptance mechanism agree that the result may advance for intended use?

### Production observation

What actually happens when the result encounters the open-world environment?

A QA PASS does not eliminate the model gap between staging and production.

## Promotion rule

Where QA is required:

```text
implementation complete
  -> automated verification complete
  -> representative environment available
  -> QA evidence complete
  -> reconciliation complete
  -> acceptance decision
  -> promotion as separately authorized
```

A project may place substantiation before or after the human QA activity based on evidence architecture, but the final promotion claim must reconcile both machine and required human evidence.

## Shadow Genome integration

Recurring QA discoveries are eligible for governed learning.

Examples:

- tests repeatedly pass while UX fails;
- responsive regressions evade automated checks;
- staging-only integration failures recur;
- environment fidelity assumptions repeatedly prove false;
- acceptance criteria are consistently ambiguous;
- agent-generated QA produces false confidence;
- humans repeatedly catch a defect class absent from the evaluator.

Such observations should enter Shadow learning only according to the Shadow Genome's attribution, promotion, severity, freshness, and countermeasure rules. One defect does not automatically become universal policy.

## Compatibility rule

This doctrine does not require every Qor consumer to provision staging infrastructure and does not make Qor a deployment platform.

It defines the evidence and semantic boundary. External platforms may provide preview/staging/deployment environments.

Existing `qor/scripts/qa_evidence.py`, Feature Index behavior, and acceptance-close mechanics should be audited against this doctrine in a later implementation slice before their schemas or enforcement are changed.
