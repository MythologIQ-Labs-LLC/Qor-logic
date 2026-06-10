# Doctrine: Gate-Artifact Provenance Binding (GAP-GOV-05)

Phase 158. Defines how a gate artifact is bound to the governed run that produced
it, and states the threat-model ceiling honestly.

## The problem

Before Phase 158, `gate_chain.write_gate_artifact` authorized a write on a single
self-asserted env string: `QOR_SKILL_ACTIVE == phase`. Any process that exported
that variable could write a schema-valid `plan/audit/implement/substantiate.json`.
GAP-GOV-05 (production-gap audit, Entry #353) flagged this as forgeable
provenance. The honest design truth: the operator is both the author and the
bound party, so cryptographic non-forgeability *against the repo owner* is
impossible by construction. The achievable guarantees attach to two real
boundaries -- the local working tree and the CI merge boundary -- and Phase 158
hardens both.

## Layer A -- local per-session HMAC (tamper-evidence + replay resistance)

A **provenance sidecar** is a `<phase>.provenance` JSON file written beside each
gate artifact by `qor.scripts.gate_provenance.write_sidecar`. It carries a keyless
`payload_sha256` over the artifact bytes and an `hmac_tag` keyed by the
**session provenance key** -- a per-session 32-byte secret created on first use
under `.qor/session/keys/<session_id>.key`. Because `.qor/session/` is gitignored,
that key is local-only by construction.

The signed material is `f"{session_id}|{phase}|"` + the artifact's LF-normalized
bytes. The `session_id|phase` prefix binds the tag to its session and phase, so a
`plan` tag cannot be presented as an `audit` tag and a tag from one session fails
under another session's distinct key (cross-session replay resistance). LF
normalization mirrors `ledger_hash.content_hash`: gate artifacts are committed and
git autocrlf may rewrite them to CRLF, so a byte-exact digest would drift.

What Layer A buys: tamper-evidence -- a post-hoc edit to a committed artifact
fails `verify_sidecar` where the session key is present. What Layer A does NOT
buy: protection against an in-repo filesystem actor who can read the key and
re-sign. That ceiling is intrinsic and is stated rather than hidden.

## Layer B -- CI attestation (non-forgeable at the merge boundary)

`gate_provenance.verify_committed` is a keyless gate: for every sealed phase at or
above `phase_min` (158) it recomputes each committed artifact's `payload_sha256`
against its sidecar and fails on any missing sidecar or mismatch (no fail-open).
It needs no secret, so it runs on pull requests from forks, and it is wired as a
required CI check in `.github/workflows/ci.yml` -- a forged or post-seal-edited
committed artifact fails the merge boundary.

A **CI attestation** is a CI-secret-keyed HMAC over a sealed ledger entry's
content hash and chain hash, computed by `gate_provenance.ci_attest` only when
`QOR_CI_ATTEST_SECRET` is configured. Because that secret lives only in the
trusted CI environment (absent from forks and local checkouts), only genuine CI
can produce a valid attestation, and it is verifiable only where the secret lives.
It proves "verified by trusted Qor-logic CI", not human authorship. When the
secret is absent the step emits a disclosed skip rather than a fabricated value.

## Grandfathering

The 507 gate artifacts sealed before Phase 158 carry no sidecar; `verify_committed`
ignores phases below `phase_min` exactly as `gate_chain_completeness` grandfathers
phases below 52. No backfill.

## V2 follow-on (deferred)

Binding the CI attestation into the ledger hash chain (so editing an artifact
requires editing a hash-chained entry) is a substantiate-format change and is
deferred. Consuming the attestation as a hard release-pipeline gate in a separate
repository is likewise out of this repo's scope.
