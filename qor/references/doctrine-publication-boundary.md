# Publication Boundary Doctrine

## Rule

Qor-logic is public and standalone. A tracked or published Qor-logic artifact
MUST NOT directly identify, address, depend on, or operationally couple to a
repository outside Qor-logic.

Outside repositories may be consulted as private research inputs. Only the
general lesson, pattern, or constraint may enter this repository. The source
repository's identity and relationship to Qor-logic must not.

## Required treatment

Delete an outside-repository reference when it is not necessary. When the
underlying lesson is necessary, replace identifying details with neutral terms
such as `an external repository`, `an external implementation`, `a consumer`,
or a synthetic fixture identifier.

The prohibition includes:

- repository, organization, owner, product, and package names;
- repository URLs, issue or pull-request links, and cross-repository issue IDs;
- local paths that reveal an outside workspace or repository;
- imports, runtime dependencies, destinations, and automation that identify or
  hardcode a specific outside repository;
- provenance metadata, comments, examples, fixtures, and generated files that
  preserve an outside-repository identity;
- agent messages copied into issues, pull requests, releases, or tracked files.

References to Qor-logic itself are permitted.

Generic, operator-configured interfaces that can target a repository are
permitted when Qor-logic does not name, assume, privilege, or depend on a
specific outside repository.

## Lessons-learned exception

The only exception is an intentional lesson-learned record under
`docs/Lessons-Learned/`. The exception permits the minimum public-safe context
needed to preserve a lesson. It never permits secrets, credentials, private
paths, personal data, or unnecessary operational details.

Moving ordinary research, planning, attribution, or integration prose into the
lessons-learned directory to evade this rule is prohibited.

## Agent obligations

Every agent operating in this repository MUST:

1. Treat outside-repository context as private reasoning material.
2. Sanitize identifying details before producing persistable output.
3. Search changed files for outside-repository names, URLs, paths, and
   relationships before handoff.
4. Reject plans that identify or hardcode a specific outside repository.
5. Treat a discovered historical reference as remediation work, not precedent.

This doctrine applies retroactively to the full tracked repository and
prospectively to every new artifact.
