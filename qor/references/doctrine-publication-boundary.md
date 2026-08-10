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

## Standing exceptions and how to record one (Phase 208)

Two exceptions are granted outright, both because the text is legally required
and is not this project's to rewrite:

1. **Third-party attribution under `qor/vendor/`.** The lint skips this tree
   structurally; no marker is needed.
2. **`license:` lines naming a proprietary owner** in skill frontmatter and in
   the frozen `docs/archive/` tree.

Beyond those, a line that legitimately names an outside identity records the
exception where it applies:

```
<any line> # boundary-lint: ok=<reason>
```

The marker suppresses findings for **that line only**. There is no wildcard, no
per-file form, and no directory suppression. A reason is required; a bare
`ok=` does not suppress. The comment character is not part of the pattern, so
the same marker works in Markdown (`<!-- ... -->`), Python (`# ...`), and YAML.

Legitimate uses are narrow: a detector's own test fixtures, a specification
describing the detector, and frozen archive material. An exception is not a
place to park prose that should have been anonymized.

**Enforcement.** `publication_boundary_lint` runs fail-closed in CI's
`gate-chain-completeness` job. Before Phase 208 it could express neither
standing exception above, so it reported granted exceptions as violations,
stayed permanently red, and was wired to no gate — a control nobody can satisfy
is a control nobody enforces. CI runs the structural detectors only; the
identity-term overlay at `.qor/private/boundary-terms.txt` is gitignored and
verified locally.

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
