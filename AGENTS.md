# Repository Agent Rules

These instructions apply to every human or automated agent operating in this
repository.

## Public-repository boundary

Qor-logic is a public, standalone repository. Direct references to any other
repository MUST be deleted or anonymized unless they appear in an intentional
lesson-learned record under `docs/Lessons-Learned/`.

This rule applies retroactively and to every tracked or published surface,
including source code, comments, tests, fixtures, generated distributions,
skills, plans, research, documentation, ledgers, changelogs, issues, pull
requests, release notes, and agent output that may be persisted.

Outside repositories may inform private reasoning only. Before writing,
committing, posting, or publishing, replace their names, owners, URLs, local
paths, package identities, issue references, and operational relationships with
neutral language or synthetic identifiers. Do not create cross-repository
imports, runtime dependencies, destinations, or documentation coupling that
identify or hardcode a specific outside repository. Generic,
operator-configured interfaces are permitted when they remain repository
neutral.

The sole exception is a deliberate, public-safe lesson-learned record. Even
there, disclose only what is necessary to preserve the lesson; secrets,
credentials, private paths, and sensitive operational details remain forbidden.

Canonical contract:
[`qor/references/doctrine-publication-boundary.md`](qor/references/doctrine-publication-boundary.md).
