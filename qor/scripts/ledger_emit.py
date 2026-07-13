"""Phase 193 (GH #278): canonical typed ledger-entry renderer + append.

One emission path whose output the verifier round-trips: ``render`` produces
exactly the markup ``ledger_hash._resolve_recorded`` parses, and ``append``
computes the content/chain hashes with the ledger_hash primitives, enforces
the ASCII seal rule at the API, and inserts the entry before the
chain-integrity tail marker.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from qor.scripts.ledger_hash import assert_sealable_text, chain_hash
import hashlib

_TAIL_MARKER = "*Chain integrity: VALID*"
_CHAIN_RE = re.compile(r"\*\*Chain Hash \(Merkle seal\)\*\*:\s*`([0-9a-f]{64})`")


@dataclass
class LedgerEntry:
    """A typed ledger entry: heading, ordered field lines, decision body."""

    number: int
    title: str
    fields: dict[str, str] = field(default_factory=dict)
    body: str = ""


def render(entry: LedgerEntry, *, content: str, previous: str, chain: str) -> str:
    """Render the canonical entry markup (parser contract: _resolve_recorded)."""
    lines = [f"### Entry #{entry.number}: {entry.title}", ""]
    for key, value in entry.fields.items():
        lines.append(f"**{key}**: {value}")
    lines += [
        "",
        f"**Content Hash**: `{content}`",
        f"**Previous Hash**: `{previous}`",
        f"**Chain Hash (Merkle seal)**: `{chain}`",
        "",
        f"**Decision**: {entry.body}",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def _tail_chain_hash(text: str) -> str:
    hashes = _CHAIN_RE.findall(text)
    if not hashes:
        raise ValueError("ledger carries no chain hash to link off")
    return hashes[-1]


def _body_content_hash(entry: LedgerEntry) -> str:
    """Self-bound entries hash their own decision body (LF-normalized)."""
    data = entry.body.encode("utf-8").replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def append(ledger_path: Path, entry: LedgerEntry,
           *, content: str | None = None) -> tuple[str, str]:
    """Append an entry linked off the current tail; return (content, chain).

    ``content`` defaults to the LF-normalized sha256 of the entry body
    (self-bound); pass an explicit hash to bind an external artifact.
    """
    assert_sealable_text(entry.body, label=f"entry #{entry.number} body")
    for key, value in entry.fields.items():
        assert_sealable_text(f"{key}: {value}", label=f"entry #{entry.number} field")

    text = ledger_path.read_text(encoding="utf-8")
    previous = _tail_chain_hash(text)
    content_val = content or _body_content_hash(entry)
    chain_val = chain_hash(content_val, previous)

    rendered = render(entry, content=content_val, previous=previous, chain=chain_val)
    idx = text.rindex(_TAIL_MARKER)
    # back up over the separator preceding the tail block
    head = text[:idx].rstrip("\n")
    if head.endswith("---"):
        head = head[:-3].rstrip("\n")
    tail = text[idx:]
    ledger_path.write_text(
        head + "\n\n" + rendered + "\n" + tail, encoding="utf-8")
    return content_val, chain_val
