# Plan: Phase 158 / GAP-GOV-05 — non-forgeable provenance for gate artifacts

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: provenance sidecar
  home: qor/references/doctrine-provenance-binding.md
- term: session provenance key
  home: qor/references/doctrine-provenance-binding.md
- term: CI attestation
  home: qor/references/doctrine-provenance-binding.md

**boundaries**:
- limitations:
  - Layer A (local HMAC) ceiling is an in-repo filesystem actor: the per-session
    key lives in the working tree, so a process that can both set
    `QOR_SKILL_ACTIVE` and read the key can still forge a tag. Layer A buys
    tamper-evidence (post-hoc edits to a committed artifact fail verification
    where the key is present) and cross-session replay resistance, NOT
    non-forgeability against the operator.
  - Layer B (CI attestation) is verifiable only in CI: the attestation HMAC is
    keyed by a CI-held secret absent from forks and local checkouts. It proves
    "verified by trusted Qor-logic CI", not "authored by a specific human".
- non_goals:
  - Cryptographic non-forgeability against the repo owner (impossible by
    construction: the operator is both author and the bound party).
  - Per-developer signing identities / a PKI. Out of scope for V1.
  - Binding the attestation into the ledger hash chain (a substantiate-format
    change); deferred to a V2 follow-on.
- exclusions:
  - `intent_lock._hash_file` and other intra-checkout hashers are unaffected.
  - Legacy sealed sessions (phase < 158) are grandfathered; no sidecar backfill.

## Open Questions

None. Architecture decided 2026-06-10: layered A+B (local per-session HMAC for
everyday integrity/replay + CI attestation as the non-forgeable merge gate).

## Threat model (load-bearing; the honesty contract)

Current binding (`gate_chain.write_gate_artifact`, `gate_chain.py:245-257`) is a
self-asserted env string: any process that exports `QOR_SKILL_ACTIVE=<phase>`
writes a schema-valid gate artifact. Verified by grep:

> `grep -nE "QOR_SKILL_ACTIVE" qor/scripts/gate_chain.py` -> lines 192-193 (set),
> 246/253 (the only authorization check).

`.qor/session/` is gitignored (`.gitignore:17`) so a per-session key placed under
`.qor/session/keys/` is local-only by construction. `.qor/gates/<sid>/*.json`
ARE committed (`git ls-files .qor/gates` -> 507 files) and re-validated in CI by
`gate_chain_completeness --phase-min 52`. The two layers attach to those two
realities: Layer A protects the local working tree (where the key exists); Layer
B protects the merge boundary (CI, where the key does not exist but a CI-only
secret does).

## Phase 1: Layer A — local per-session HMAC provenance

### Affected Files

- `tests/test_gate_provenance.py` - NEW. Behavioral tests for the sign/verify
  round-trip, per-session key isolation, replay resistance, and tamper-evidence.
- `qor/scripts/gate_provenance.py` - NEW. stdlib-only (`hmac`, `hashlib`,
  `secrets`, `json`) provenance signer/verifier + sidecar I/O.
- `qor/scripts/gate_chain.py` - EDIT. After the authoritative `vga.write_artifact`
  succeeds, write the provenance sidecar beside the returned artifact path. Add
  `verify_artifact_provenance(phase, session_id)` delegating to gate_provenance.

### Changes

`gate_provenance.py` public surface (each function within the Section 4 Razor
≤40-line budget):

- `session_key(session_id, *, create=True) -> bytes` — load the per-session key
  from `.qor/session/keys/<sid>.key` (validates `session_id` via
  `session.validate_session_id` before path use); create with
  `secrets.token_bytes(32)` on first use when `create=True`; raise
  `FileNotFoundError` when absent and `create=False`.
- `_canonical(payload) -> bytes` — `json.dumps(payload, sort_keys=True,
  separators=(",", ":")).encode()`; the provenance field itself is excluded from
  the signed material (sign the artifact, not the signature).
- `sign(phase, payload, session_id, *, key=None) -> str` — HMAC-SHA256 over
  `f"{session_id}|{phase}|".encode() + _canonical(payload)`; hex digest. The
  `session_id|phase` prefix binds the tag to its session and phase (replay
  resistance: a `plan` tag cannot be presented as an `audit` tag, and a tag from
  session X fails under session Y's distinct key).
- `verify(phase, payload, session_id, tag, *, key=None) -> bool` — recompute and
  `hmac.compare_digest`.
- `sidecar_path(artifact_path) -> Path` — `artifact_path.with_suffix(".provenance")`.
- `write_sidecar(phase, payload, session_id, artifact_path) -> Path` — writes
  `{"alg":"HMAC-SHA256","session_id":...,"phase":...,"hmac_tag":...,
  "payload_sha256":...,"ts":...}`. `payload_sha256` is the keyless SHA-256 of
  `_canonical(payload)` (Layer B consumes it for keyless recomputation).
- `verify_sidecar(artifact_path, *, require_key=True) -> ProvResult` — loads the
  artifact + sidecar; recomputes `payload_sha256` (always) and `hmac_tag` (when
  the session key is present); returns a result with `payload_ok`, `hmac_ok`,
  `key_present`, and `errors`.

`gate_chain.write_gate_artifact` wiring: immediately after
`path = vga.write_artifact(...)` (and the audit-history append), call
`gate_provenance.write_sidecar(phase, payload, sid, path)`. The sidecar write is
inside the existing function, after the provenance-env gate, so the pytest bypass
path still produces a sidecar (tests exercise it). Wrap in the same
signal-safe `try/except Exception` discipline as `_fire_gate_written_hook` is NOT
used here: the sidecar is a security control, so a failure to write it MUST
propagate (fail-closed) rather than be swallowed.

### Unit Tests

- `tests/test_gate_provenance.py`:
  - `test_sign_verify_round_trip_true` — `verify` returns True for a tag produced
    by `sign` over the same `(phase, payload, session_id)`.
  - `test_verify_false_on_payload_edit` — mutating one payload field after signing
    makes `verify` return False (tamper-evidence).
  - `test_verify_false_on_phase_swap` — a tag signed for `phase="plan"` fails when
    verified as `phase="audit"` (replay resistance across phases).
  - `test_distinct_sessions_get_distinct_keys` — `session_key` for two session ids
    returns different bytes; a tag from one fails under the other's key
    (cross-session replay resistance).
  - `test_session_key_persisted_and_stable` — second `session_key` call for the
    same id returns the identical bytes (load, not regenerate).
  - `test_session_key_rejects_pathunsafe_id` — `session_key("../evil")` raises
    `ValueError` (path-safety, reuses `session.validate_session_id`).
  - `test_write_sidecar_then_verify_sidecar_ok` — round-trips through disk:
    `write_sidecar` then `verify_sidecar` yields `payload_ok and hmac_ok`.
  - `test_verify_sidecar_detects_artifact_tamper` — editing the written `.json`
    artifact after `write_sidecar` makes `verify_sidecar().payload_ok` False.
  - `test_payload_sha256_is_keyless_and_matches_recompute` — the sidecar's
    `payload_sha256` equals `hashlib.sha256(_canonical(payload))` (Layer B can
    recompute without any key).
- `tests/test_gate_chain_provenance.py` (EDIT): add
  `test_write_gate_artifact_emits_valid_provenance_sidecar` — a successful
  `write_gate_artifact` produces a sidecar beside the artifact whose
  `verify_sidecar` passes; the existing five env-binding tests remain green.

## Phase 2: Layer B — CI attestation (non-forgeable at merge boundary)

### Affected Files

- `tests/test_gate_provenance.py` - EDIT. Tests for `ci_attest` /
  `verify_ci_attestation` and the keyless sidecar recomputation gate.
- `qor/scripts/gate_provenance.py` - EDIT. Add the CI-attestation primitive and a
  `verify_committed --phase-min` CLI entry that recomputes sidecar
  `payload_sha256` over committed artifacts (keyless; the merge gate's teeth).
- `.github/workflows/ci.yml` - EDIT. Add a `provenance-attest` job that (a) runs
  the keyless `verify_committed --phase-min 158` recomputation gate as a required
  check, and (b) when `secrets.QOR_CI_ATTEST_SECRET` is present, emits the
  attestation over the latest sealed entry; logs a disclosed skip when absent.

### Changes

- `ci_attest(content_hash, chain_hash, *, secret=None) -> str | None` — read the
  CI secret from the `secret` arg or `QOR_CI_ATTEST_SECRET` env; return
  `HMAC-SHA256(secret, f"{content_hash}|{chain_hash}")` hex, or `None` when no
  secret is configured (honest skip, never a fabricated value).
- `verify_ci_attestation(content_hash, chain_hash, attestation, *, secret=None)
  -> bool` — recompute and `hmac.compare_digest`; returns False when the secret
  is absent (cannot verify without it — the documented CI-only property).
- `verify_committed(repo_root, *, phase_min=158) -> CommittedResult` — for each
  sealed phase >= `phase_min` (reuse `gate_chain_completeness._extract_seal_sessions`),
  load each gate artifact + its `.provenance` sidecar and assert the keyless
  `payload_sha256` recomputes (FAIL on missing sidecar or mismatch). This is the
  branch-protected merge gate; it needs no secret, so it runs on every PR
  including forks.
- `main(argv)` CLI: `verify-committed --repo-root . --phase-min 158` (exit 1 on
  any mismatch) and `ci-attest --content-hash H --chain-hash C` (prints the
  attestation or a disclosed-skip line).
- `ci.yml` `provenance-attest` job: checkout (fetch-depth 0), pip install, run
  `python -m qor.scripts.gate_provenance verify-committed --phase-min 158`
  (required check); then a guarded step `if: ${{ secrets.QOR_CI_ATTEST_SECRET != '' }}`
  that emits the attestation. The keyless `verify-committed` is what makes a
  forged committed artifact fail at merge; the secret-keyed `ci-attest` is the
  cryptographic proof-of-CI-execution layered on top.

### Unit Tests

- `tests/test_gate_provenance.py`:
  - `test_ci_attest_returns_none_without_secret` — `ci_attest(h, c)` with no
    secret env and no arg returns `None`.
  - `test_ci_attest_deterministic_with_secret` — same `(h, c, secret)` yields the
    same hex; a different secret yields a different hex.
  - `test_verify_ci_attestation_round_trip` — `verify_ci_attestation` is True for
    an attestation from `ci_attest` under the same secret, False under a wrong
    secret, and False when no secret is supplied.
  - `test_verify_committed_passes_on_consistent_sidecars` — build a tmp repo with
    a sealed entry + matching artifact/sidecar; `verify_committed` returns ok.
  - `test_verify_committed_fails_on_artifact_tamper` — edit the committed artifact
    after sidecar write; `verify_committed` returns not-ok naming the phase.
  - `test_verify_committed_fails_on_missing_sidecar` — a phase-≥-158 sealed
    artifact with no `.provenance` sidecar fails (no fail-open).
  - `test_verify_committed_grandfathers_below_phase_min` — a phase-100 sealed
    session with no sidecar is ignored under `--phase-min 158`.

## Definition of Done

### Deliverable: gate_provenance module (Layer A)

- **D1**: A stdlib-only per-session HMAC scheme gives gate artifacts
  tamper-evidence and cross-session replay resistance, with the in-repo-actor
  ceiling stated honestly.
- **D2**: `qor/scripts/gate_provenance.py` exposing `session_key`, `sign`,
  `verify`, `sidecar_path`, `write_sidecar`, `verify_sidecar`; no third-party
  imports.
- **D3**: `gate_chain.write_gate_artifact` writes a sidecar on the authoritative
  path; new doctrine `doctrine-provenance-binding.md` is the home for the three
  introduced terms; glossary `referenced_by` updated.
- **D4**: `tests/test_gate_provenance.py::test_verify_false_on_payload_edit` and
  `::test_distinct_sessions_get_distinct_keys` pass.

### Deliverable: CI attestation (Layer B)

- **D1**: The merge boundary carries a keyless recomputation gate plus an optional
  CI-secret attestation that only trusted CI can produce.
- **D2**: `ci_attest`, `verify_ci_attestation`, `verify_committed` in
  `gate_provenance.py`; `verify-committed` + `ci-attest` CLI subcommands.
- **D3**: `.github/workflows/ci.yml` runs `verify-committed --phase-min 158` as a
  required job and emits the attestation under the guarded secret step.
- **D4**: `tests/test_gate_provenance.py::test_verify_committed_fails_on_artifact_tamper`
  and `::test_verify_ci_attestation_round_trip` pass.

## CI Commands

- `python -m pytest tests/test_gate_provenance.py tests/test_gate_chain_provenance.py -v` — Layer A + B unit behavior.
- `python -m pytest tests/ -q` — full suite stays green (no regression in the 14 existing gate_chain/provenance tests).
- `python -m qor.scripts.gate_provenance verify-committed --phase-min 158` — keyless merge gate over committed sidecars.
- `python -m qor.scripts.gate_provenance attest-latest` — emit the CI-secret-keyed attestation over the latest sealed entry (disclosed-skip without the secret).
- `python qor/scripts/check_variant_drift.py` — dist variants in sync after any `qor/skills/**` touch (none expected; module-only change).
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — existing completeness gate unaffected.
