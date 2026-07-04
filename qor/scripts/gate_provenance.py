#!/usr/bin/env python3
"""Phase 158 (GAP-GOV-05): non-forgeable gate-artifact provenance.

The pre-Phase-158 binding (``gate_chain.write_gate_artifact``) authorized a gate
write on a self-asserted env string (``QOR_SKILL_ACTIVE==phase``): any process
that exported the variable could write a schema-valid artifact. This module adds
two honest layers on top of that env gate.

**Layer A -- local per-session HMAC sidecar.** Each gate artifact gets a sibling
``<phase>.provenance`` file carrying a keyless ``payload_sha256`` and an
``hmac_tag`` keyed by a per-session secret stored under the gitignored
``.qor/session/keys/``. Buys tamper-evidence (a post-hoc edit to a committed
artifact fails verification where the key is present) and cross-session replay
resistance (the key is per-session; ``session_id|phase`` is bound into the signed
material). Honest ceiling: an in-repo filesystem actor can read the key and
forge -- non-forgeability against the operator is impossible by construction
(the operator is both author and bound party).

**Layer B -- CI attestation.** ``verify_committed`` recomputes each committed
artifact's ``payload_sha256`` (keyless, so it runs on forks) and is wired as a
required CI check: a forged committed artifact fails the merge boundary.
``ci_attest`` additionally produces a CI-secret-keyed stamp only trusted CI can
make (verifiable only where the secret lives -- the documented CI-only property).

All signed material is LF-normalized first: gate artifacts are committed and git
autocrlf may rewrite them to CRLF, so a byte-exact digest would drift (the same
GAP-GOV-03 lesson behind ``ledger_hash.content_hash``). Stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
import sys
from dataclasses import dataclass, field
from pathlib import Path

from qor import workdir as _workdir
from qor.scripts import session as _session

_ALG = "HMAC-SHA256"
_CI_SECRET_ENV = "QOR_CI_ATTEST_SECRET"  # noqa: secret-scan (env var NAME, not a secret value)
_REQUIRED_PHASES = ("plan", "audit", "implement", "substantiate")


def _normalize(data: bytes) -> bytes:
    """LF-normalize so a CRLF round-trip through git does not drift the digest."""
    return data.replace(b"\r\n", b"\n")


def _keys_dir() -> Path:
    return _workdir.root() / ".qor" / "session" / "keys"


def session_key(session_id: str, *, create: bool = True) -> bytes:
    """Load the per-session 32-byte key, creating it on first use.

    Raises ``ValueError`` on a path-unsafe ``session_id`` (reuses the session
    validator) and ``FileNotFoundError`` when the key is absent and
    ``create=False``."""
    _session.validate_session_id(session_id)
    path = _keys_dir() / f"{session_id}.key"
    if path.exists():
        return path.read_bytes()
    if not create:
        raise FileNotFoundError(f"session provenance key absent: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_bytes(32)
    path.write_bytes(key)
    return key


def sign(phase: str, session_id: str, data: bytes, *, key: bytes) -> str:
    """HMAC-SHA256 over ``session_id|phase|`` + LF-normalized ``data``.

    The ``session_id|phase`` prefix binds the tag to its session and phase, so a
    ``plan`` tag cannot be replayed as ``audit`` and a tag from one session fails
    under another session's distinct key."""
    prefix = f"{session_id}|{phase}|".encode("utf-8")
    return hmac.new(key, prefix + _normalize(data), hashlib.sha256).hexdigest()


def verify_tag(phase: str, session_id: str, data: bytes, tag: str, *, key: bytes) -> bool:
    """Recompute and constant-time compare against ``tag``."""
    return hmac.compare_digest(sign(phase, session_id, data, key=key), tag)


def payload_digest(data: bytes) -> str:
    """Keyless SHA-256 of LF-normalized bytes (Layer B recomputes this in CI)."""
    return hashlib.sha256(_normalize(data)).hexdigest()


def sidecar_path(artifact_path: Path) -> Path:
    return Path(artifact_path).with_suffix(".provenance")


def write_sidecar(phase: str, session_id: str, artifact_path: Path) -> Path:
    """Write the ``<phase>.provenance`` sidecar beside ``artifact_path``.

    Signs the artifact file's bytes (LF-normalized) so the digest is over what is
    actually persisted/committed, not an in-memory dict."""
    artifact_path = Path(artifact_path)
    raw = artifact_path.read_bytes()
    key = session_key(session_id)
    body = {
        "alg": _ALG,
        "session_id": session_id,
        "phase": phase,
        "payload_sha256": payload_digest(raw),
        "hmac_tag": sign(phase, session_id, raw, key=key),
    }
    out = sidecar_path(artifact_path)
    out.write_text(json.dumps(body, indent=2, sort_keys=True), encoding="utf-8")
    return out


@dataclass(frozen=True)
class ProvResult:
    payload_ok: bool
    hmac_ok: bool
    key_present: bool
    errors: list[str] = field(default_factory=list)


def verify_sidecar(artifact_path: Path, *, require_key: bool = True) -> ProvResult:
    """Verify an artifact against its sidecar.

    ``payload_sha256`` is always recomputed (keyless). The ``hmac_tag`` is checked
    only when the per-session key is present; when it is absent and
    ``require_key`` is False (the CI case) ``hmac_ok`` is reported False with
    ``key_present`` False rather than raising."""
    artifact_path = Path(artifact_path)
    side = sidecar_path(artifact_path)
    errors: list[str] = []
    if not side.exists():
        return ProvResult(False, False, False, [f"sidecar missing: {side}"])
    meta = json.loads(side.read_text(encoding="utf-8"))
    raw = artifact_path.read_bytes()
    payload_ok = hmac.compare_digest(payload_digest(raw), meta.get("payload_sha256", ""))
    if not payload_ok:
        errors.append(f"payload_sha256 mismatch: {artifact_path}")
    try:
        key = session_key(meta["session_id"], create=False)
        key_present = True
    except FileNotFoundError:
        if require_key:
            errors.append(f"session key absent: {meta['session_id']}")
        return ProvResult(payload_ok, False, False, errors)
    hmac_ok = verify_tag(meta["phase"], meta["session_id"], raw, meta.get("hmac_tag", ""), key=key)
    if not hmac_ok:
        errors.append(f"hmac_tag mismatch: {artifact_path}")
    return ProvResult(payload_ok, hmac_ok, key_present, errors)


def ci_attest(content_hash: str, chain_hash: str, *, secret: str | None = None) -> str | None:
    """HMAC over ``content_hash|chain_hash`` keyed by the CI-only secret.

    Returns None when no secret is configured (an honest skip -- never a
    fabricated value). The secret is read from ``secret`` or
    ``QOR_CI_ATTEST_SECRET``."""
    import os
    secret = secret or os.environ.get(_CI_SECRET_ENV)
    if not secret:
        return None
    msg = f"{content_hash}|{chain_hash}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def verify_ci_attestation(
    content_hash: str, chain_hash: str, attestation: str, *, secret: str | None = None
) -> bool:
    """True iff ``attestation`` matches ``ci_attest`` under ``secret``.

    Returns False when no secret is available -- the attestation is verifiable
    only where the CI secret lives."""
    expected = ci_attest(content_hash, chain_hash, secret=secret)
    if expected is None or not attestation:
        return False
    return hmac.compare_digest(expected, attestation)


def latest_seal_hashes(repo_root: Path) -> tuple[str, str] | None:
    """Return the (content_hash, chain_hash) of the last ledger entry that
    carries both canonical hash markers, or None when none is found."""
    import re
    ledger = Path(repo_root) / "docs" / "META_LEDGER.md"
    if not ledger.is_file():
        return None
    text = ledger.read_text(encoding="utf-8")
    content = re.findall(r"\*\*Content Hash\*\*:\s*`([0-9a-f]{64})`", text)
    chain = re.findall(r"\*\*Chain Hash \(Merkle seal\)\*\*:\s*`([0-9a-f]{64})`", text)
    if not content or not chain:
        return None
    return content[-1], chain[-1]


@dataclass(frozen=True)
class CommittedResult:
    ok: bool
    mismatches: list[tuple[int, str]] = field(default_factory=list)
    sessions_checked: list[str] = field(default_factory=list)


def verify_committed(repo_root: Path, *, phase_min: int = 158) -> CommittedResult:
    """Keyless merge-boundary gate: every sealed phase >= ``phase_min`` must have a
    provenance sidecar whose ``payload_sha256`` recomputes over the committed
    artifact. Missing sidecar or digest mismatch is a failure (no fail-open).
    Phases below ``phase_min`` are grandfathered."""
    from qor.reliability.gate_chain_completeness import _extract_seal_sessions

    repo_root = Path(repo_root)
    ledger = repo_root / "docs" / "META_LEDGER.md"
    if not ledger.is_file():
        return CommittedResult(False, [(0, f"ledger missing: {ledger}")], [])
    by_phase = _extract_seal_sessions(ledger.read_text(encoding="utf-8"), phase_min)
    gates = repo_root / ".qor" / "gates"
    mismatches: list[tuple[int, str]] = []
    from qor.scripts import tier_guard

    for phase_num, sid in sorted(by_phase.items()):
        # Phase 168 (GH #248): honor a legally-declared short chain; absent or
        # illegal declarations resolve to the full set (fail-closed).
        declared = tier_guard.declared_artifacts(gates / sid / "plan.json")
        if "audit" not in declared and tier_guard.verify_session(sid, gates):
            declared = _REQUIRED_PHASES
        for ph in declared:
            art = gates / sid / f"{ph}.json"
            if not art.is_file():
                mismatches.append((phase_num, f"{sid}/{ph}.json: artifact missing"))
                continue
            res = verify_sidecar(art, require_key=False)
            if not res.payload_ok:
                why = res.errors[0] if res.errors else "payload mismatch"
                mismatches.append((phase_num, f"{sid}/{ph}.json: {why}"))
    return CommittedResult(not mismatches, mismatches, list(by_phase.values()))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    vc = sub.add_parser("verify-committed", help="keyless merge gate over committed sidecars")
    vc.add_argument("--repo-root", type=Path, default=Path.cwd())
    vc.add_argument("--phase-min", type=int, default=158)
    at = sub.add_parser("ci-attest", help="emit the CI-secret-keyed attestation")
    at.add_argument("--content-hash", required=True)
    at.add_argument("--chain-hash", required=True)
    al = sub.add_parser("attest-latest", help="attest the latest sealed ledger entry")
    al.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args(argv)
    if args.cmd == "verify-committed":
        res = verify_committed(args.repo_root, phase_min=args.phase_min)
        if res.ok:
            print(f"OK: provenance verified for {len(res.sessions_checked)} "
                  f"sessions (phase >= {args.phase_min})")
            return 0
        print(f"FAIL: {len(res.mismatches)} provenance mismatch(es):")
        for phase_num, what in res.mismatches:
            print(f"  phase {phase_num}: {what}")
        return 1
    if args.cmd == "attest-latest":
        hashes = latest_seal_hashes(args.repo_root)
        if hashes is None:
            print("SKIP: no sealed ledger entry with canonical hash markers")
            return 0
        content_hash, chain_hash = hashes
    else:
        content_hash, chain_hash = args.content_hash, args.chain_hash
    att = ci_attest(content_hash, chain_hash)
    if att is None:
        print(f"SKIP: {_CI_SECRET_ENV} absent; attestation not emitted "
              "(disclosed skip -- no CI secret configured)")
        return 0
    print(att)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
