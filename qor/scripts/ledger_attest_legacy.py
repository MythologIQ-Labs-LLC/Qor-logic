"""Phase 193 (GH #278): retroactive attestation of the pre-convention band.

The legacy entries that ``ledger_hash verify`` perpetually skips carry no
hash markup and cannot be retro-chained without editing post-anchor hash
fields (forbidden). This module makes the band tamper-evident the
chain-preserving way: one MIGRATION ATTESTATION entry -- emitted through
the canonical ``ledger_emit`` API -- binds each legacy body to an
LF-normalized digest inside the live chain. The verify extension re-checks
those digests: matches report as attested, mismatches FAIL.

CLI:
    python -m qor.scripts.ledger_attest_legacy --ledger PATH [--write]
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

from qor.scripts.ledger_emit import LedgerEntry, append
from qor.scripts.ledger_hash import ENTRY_RE, _resolve_recorded

# verify()'s markup_required_cutoff default: entries below it skip when
# unresolved; entries at/after it FAIL. The attestation targets the skip band.
_MARKUP_CUTOFF = 123

ATTESTED_LINE_RE = re.compile(r"^#(\d+)=([0-9a-f]{12})\s*$", re.MULTILINE)
ATTESTATION_TITLE = "MIGRATION ATTESTATION"


def _entries(text: str) -> list[tuple[int, str]]:
    parts = ENTRY_RE.split(text)
    return [(int(parts[i]), parts[i + 1] if i + 1 < len(parts) else "")
            for i in range(1, len(parts), 2)]


def body_digest(body: str) -> str:
    data = body.encode("utf-8").replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()[:12]


def collect_unverifiable(ledger_path: Path,
                         cutoff: int = _MARKUP_CUTOFF) -> list[tuple[int, str]]:
    """Exactly the entries verify's skip path takes, with their digests."""
    text = ledger_path.read_text(encoding="utf-8")
    out: list[tuple[int, str]] = []
    for num, body in _entries(text):
        if num < cutoff and _resolve_recorded(body) is None:
            out.append((num, body_digest(body)))
    return out


def attested_map(text: str) -> dict[int, tuple[str, int]]:
    """{legacy_num: (digest12, attesting_entry_num)} from attestation entries."""
    out: dict[int, tuple[str, int]] = {}
    for num, body in _entries(text):
        if ATTESTATION_TITLE not in body and not any(
                ATTESTATION_TITLE in line for line in body.splitlines()[:1]):
            # title lives in the heading, which ENTRY_RE strips; detect via marker field
            pass
        if "**Attested Entries**:" not in body:
            continue
        for m in ATTESTED_LINE_RE.finditer(body):
            out[int(m.group(1))] = (m.group(2), num)
    return out


def build_attestation_entry(ledger_path: Path, number: int,
                            session_id: str, ts: str) -> LedgerEntry:
    collected = collect_unverifiable(ledger_path)
    if not collected:
        raise ValueError("nothing to attest: verify reports no skipped entries")
    listing = "\n".join(f"#{num}={digest}" for num, digest in collected)
    body = (
        f"Retroactive normalization (GH #278, operator-directed): the "
        f"{len(collected)} pre-convention entries below carry no hash markup and "
        f"cannot be retro-chained without editing post-anchor hash fields. Each is "
        f"bound here to the LF-normalized sha256 (first 12 hex) of its current body; "
        f"the verifier re-checks these digests, so any later edit of an attested "
        f"body is a verification FAILURE. History is attested, not rewritten.\n\n"
        f"**Attested Entries**:\n{listing}"
    )
    return LedgerEntry(
        number=number,
        title=f"{ATTESTATION_TITLE} -- pre-convention band",
        fields={
            "Timestamp": ts,
            "Phase": "MIGRATION",
            "Author": "Judge",
            "Session": f"`{session_id}`",
        },
        body=body,
    )


def write_attestation(ledger_path: Path, *, session_id: str = "2026-07-13T0000-000000",
                      ts: str = "2026-07-13T00:00:00Z") -> int:
    text = ledger_path.read_text(encoding="utf-8")
    nums = [n for n, _ in _entries(text)]
    entry = build_attestation_entry(ledger_path, max(nums) + 1, session_id, ts)
    append(ledger_path, entry)
    return entry.number


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="qor.scripts.ledger_attest_legacy")
    ap.add_argument("--ledger", type=Path, required=True)
    ap.add_argument("--session", default="2026-07-13T0000-000000")
    ap.add_argument("--ts", default="2026-07-13T00:00:00Z")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    collected = collect_unverifiable(args.ledger)
    if not collected:
        print("nothing to attest: no unverifiable entries")
        return 0
    print(f"{len(collected)} unverifiable entries: "
          f"#{collected[0][0]}..#{collected[-1][0]}")
    if args.write:
        num = write_attestation(args.ledger, session_id=args.session, ts=args.ts)
        print(f"attestation written as entry #{num}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
