"""Ledger-commitment integrity (Phase 251; GH #408).

A ledger entry binds an artifact by content hash. When a later phase corrects
that artifact -- which is what an audit VETO is for -- the entry's commitment
silently stops describing the file.

Chain integrity is unaffected and correctly so: chain hashes commit to the
recorded hex string, not to live bytes, so ``verify-ledger`` passes and reports
nothing wrong. That is the gap rather than a flaw in the chain. The chain proves
entries were not reordered or edited; it proves nothing about whether the
artifacts they name still say what they said.

The convention that closes it -- append an AMENDMENT recording the superseded
hash, the new hash, and the reason -- was already practiced in this repository
and codified nowhere. See ``qor/references/doctrine-ledger-commitment.md``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from qor.scripts import ledger_hash

_ENTRY_RE = re.compile(r"^### Entry #(\d+):\s*([A-Z][A-Z ]*)", re.MULTILINE)

# Which entry kinds' **Content Hash** actually binds the artifact they cite.
# A GATE TRIBUNAL entry cites **Plan** but its content hash binds the AUDIT
# REPORT, so treating that citation as a commitment would compare the plan's
# bytes against the report's digest -- a false stale reading. Found by running
# this gate against its own phase.
_COMMITTING_KINDS = ("RESEARCH BRIEF", "IMPLEMENTATION", "SESSION SEAL", "AMENDMENT")
_ARTIFACT_RE = re.compile(
    r"^\*\*(?:Artifact|Plan|Brief)\*\*:\s*`?([\w./-]+\.md)`?", re.MULTILINE
)
_CONTENT_RE = re.compile(r"^\*\*Content Hash\*\*:\s*`([0-9a-f]{64})`", re.MULTILINE)
_SUPERSEDED_RE = re.compile(
    r"^\*\*Superseded Content Hash\*\*:\s*`?([^`\s]+)`?", re.MULTILINE
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class MalformedCommitmentError(ValueError):
    """A commitment field is present but not a usable digest.

    A truncated ``Superseded Content Hash`` must not be treated as a valid
    supersession: accepting it would let a malformed amendment silently clear a
    real staleness.
    """


@dataclass(frozen=True)
class StaleCommitment:
    artifact: str
    committed: str
    actual: str


def content_hash(path: Path) -> str:
    """LF-normalized SHA-256, matching what ledger entries record."""
    return ledger_hash.content_hash(Path(path))


def _entries(text: str) -> list[tuple[int, str, str]]:
    parts = _ENTRY_RE.split(text)
    return [
        (int(parts[i]), parts[i + 1].strip(), parts[i + 2])
        for i in range(1, len(parts), 3)
    ]


def latest_commitments(ledger_path: Path) -> dict[str, str]:
    """Return ``{artifact -> most recently committed content hash}``.

    Later entries supersede earlier ones for the same artifact, so an AMENDMENT
    recording a corrected hash becomes the authoritative commitment. Raises
    ``MalformedCommitmentError`` when a ``Superseded Content Hash`` is present
    but is not a full 64-character lowercase digest.
    """
    text = Path(ledger_path).read_text(encoding="utf-8")
    commitments: dict[str, str] = {}
    for num, kind, body in _entries(text):
        superseded = _SUPERSEDED_RE.search(body)
        if superseded and not _HEX64.match(superseded.group(1)):
            raise MalformedCommitmentError(
                f"Entry #{num}: Superseded Content Hash "
                f"{superseded.group(1)!r} is not a 64-character digest"
            )
        if not any(kind.startswith(k) for k in _COMMITTING_KINDS):
            continue
        artifact = _ARTIFACT_RE.search(body)
        content = _CONTENT_RE.search(body)
        if artifact and content:
            commitments[artifact.group(1)] = content.group(1)
    return commitments


def stale_commitments(
    repo_root: Path,
    touched: list[str],
    *,
    ledger_path: Path | None = None,
) -> list[StaleCommitment]:
    """Artifacts in ``touched`` whose file no longer matches its commitment.

    Scoped to ``touched`` -- the implement gate's ``files_touched`` -- rather
    than the whole ledger. A full sweep is a ``/qor-validate`` concern; making
    it a seal gate would grow seal cost with ledger length.
    """
    root = Path(repo_root)
    ledger = ledger_path or root / "docs" / "META_LEDGER.md"
    if not ledger.is_file():
        return []
    commitments = latest_commitments(ledger)
    stale: list[StaleCommitment] = []
    for rel in touched:
        committed = commitments.get(rel.replace("\\", "/"))
        if committed is None:
            continue
        path = root / rel
        if not path.is_file():
            continue
        actual = content_hash(path)
        if actual != committed:
            stale.append(StaleCommitment(rel, committed, actual))
    return stale


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--session", default=None)
    args = ap.parse_args(argv)

    touched: list[str] = []
    if args.session:
        artifact = args.repo_root / ".qor" / "gates" / args.session / "implement.json"
        if artifact.is_file():
            touched = json.loads(artifact.read_text(encoding="utf-8")).get(
                "payload", {}
            ).get("files_touched", []) or json.loads(
                artifact.read_text(encoding="utf-8")
            ).get("files_touched", [])

    stale = stale_commitments(args.repo_root, touched)
    if not stale:
        print(f"ledger_commitment: OK ({len(touched)} touched artifact(s) checked)")
        return 0
    print(f"FAIL: {len(stale)} undisclosed stale commitment(s):")
    for s in stale:
        print(f"  {s.artifact}: committed {s.committed[:12]}..., actual {s.actual[:12]}...")
    print("Append an AMENDMENT recording the superseded and current hashes "
          "(qor/references/doctrine-ledger-commitment.md).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
