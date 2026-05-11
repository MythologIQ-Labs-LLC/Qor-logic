"""Phase 56 (GH #51): worker fragments + canonicalization.

Federation workers write ledger entries as fragments under
``.qor/ledger/fragments/<uid>.json``. They do NOT guess `Entry #N`.
The sealing worker (typically `/qor-substantiate`) canonicalizes all
pending fragments: sorts by ``(ts, uid)``, appends them to
``docs/META_LEDGER.md`` with sequential display numbers, recomputes the
chain, archives consumed fragments to ``.qor/ledger/fragments/consumed/``.

Sequential `Entry #N` is PRESENTATION ONLY post-Phase-56. UID is the
cross-worker identity.

Stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from qor.scripts.ledger_entry_id import validate_entry_uid


@dataclass(frozen=True)
class LedgerFragment:
    uid: str
    ts: str
    session_id: str
    title: str
    body: str
    content_hash: str


def _body_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def write_fragment(root: Path, fragment: LedgerFragment) -> Path:
    """Write a fragment under ``root/.qor/ledger/fragments/<uid>.json``.

    Raises ``ValueError`` on duplicate UID with a different payload (idempotent
    write of the same fragment is OK; conflicting payloads for the same UID
    indicate a federation worker collision).
    """
    validate_entry_uid(fragment.uid)
    if fragment.content_hash != _body_hash(fragment.body):
        raise ValueError(
            f"fragment {fragment.uid}: content_hash does not match SHA256 of body"
        )
    base = Path(root) / ".qor" / "ledger" / "fragments"
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{fragment.uid}.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != asdict(fragment):
            raise ValueError(
                f"fragment uid collision with different payload: {fragment.uid}"
            )
    path.write_text(json.dumps(asdict(fragment), sort_keys=True, indent=2), encoding="utf-8")
    return path


def read_fragments(root: Path) -> tuple[LedgerFragment, ...]:
    """Return pending fragments sorted by (ts, uid)."""
    base = Path(root) / ".qor" / "ledger" / "fragments"
    if not base.exists():
        return ()
    fragments: list[LedgerFragment] = []
    for path in sorted(base.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        fragments.append(LedgerFragment(**data))
    fragments.sort(key=lambda f: (f.ts, f.uid))
    return tuple(fragments)


def archive_fragments(root: Path, fragments: tuple[LedgerFragment, ...]) -> None:
    """Move consumed fragments to ``fragments/consumed/``."""
    base = Path(root) / ".qor" / "ledger" / "fragments"
    consumed = base / "consumed"
    consumed.mkdir(parents=True, exist_ok=True)
    for f in fragments:
        src = base / f"{f.uid}.json"
        if src.exists():
            src.rename(consumed / f"{f.uid}.json")


_ENTRY_NUM_RE = re.compile(r"^### Entry #(\d+):", re.MULTILINE)
_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


def next_entry_number(ledger_md_text: str) -> int:
    """Return the next sequential entry number.

    Strips fenced code blocks before matching so that prose like
    ``` ```\n### Entry #999:\n``` ``` inside a code fence does not cause
    numbering to leap. Closes M2 from the Phase 60 qor-debug review.
    """
    cleaned = _FENCE_RE.sub("", ledger_md_text)
    nums = [int(m.group(1)) for m in _ENTRY_NUM_RE.finditer(cleaned)]
    return (max(nums) + 1) if nums else 1


def canonicalize_fragments(ledger_md: Path, fragment_root: Path) -> int:
    """Append pending fragments to META_LEDGER with sequential display numbers.

    Returns the number of entries appended. Fragments are consumed (moved to
    ``consumed/``) only after the ledger write succeeds. Caller is responsible
    for re-running ``qor.scripts.ledger_hash.verify`` after canonicalization.
    """
    fragments = read_fragments(fragment_root)
    if not fragments:
        return 0
    text = ledger_md.read_text(encoding="utf-8")
    next_num = next_entry_number(text)
    appendix_parts: list[str] = []
    for f in fragments:
        # Each fragment body must be a fully-formatted SESSION SEAL entry minus
        # the heading line; canonicalization prepends ``### Entry #N: <title>``.
        appendix_parts.append(f"\n---\n\n### Entry #{next_num}: {f.title}\n\n{f.body}\n")
        next_num += 1
    ledger_md.write_text(text + "".join(appendix_parts), encoding="utf-8")
    archive_fragments(fragment_root, fragments)
    return len(fragments)
