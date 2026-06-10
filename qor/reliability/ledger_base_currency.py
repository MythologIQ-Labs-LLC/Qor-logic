"""Phase 162 (GH #231 Option 1): ledger base-currency gate + re-anchor helper.

The META_LEDGER is a linear hash chain (each entry binds to one predecessor via
``Previous Hash``) carried in a file that lives in a git branch DAG. A branch
that seals against a stale ``main`` tip -- its first new-on-branch entry's
``previous_hash`` does not equal ``origin/main``'s tip ``chain_hash`` -- forks the
chain, and git can auto-merge the two appends silently.

``check`` surfaces that drift (WARN-first in V1). ``reanchor`` is a pure fold that
rebuilds a provisional sub-chain onto the live base tip so an operator can fix a
stale-base branch deterministically at merge. The existing
``seal_entry_check.check_previous_hash_uniqueness`` post-hoc detector is retained
as defense-in-depth; this gate is the forward-looking, pre-merge complement.

Stdlib + ``ledger_hash``/``entry_id``. New entries are identified by chain-hash
set membership (robust to the entry-number reuse #231 is about), not by number.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from qor.scripts import entry_id, ledger_hash

_ENTRY_RE = re.compile(r"^### Entry #(\d+):", re.MULTILINE)
_PREV_RE = re.compile(r"\*\*Previous Hash(?:\s*\([^)]+\))?\*\*:\s*`([0-9a-f]{64})`")
_CHAIN_RE = re.compile(r"\*\*Chain Hash \(Merkle seal\)\*\*:\s*`([0-9a-f]{64})`")
_LEDGER_REL = "docs/META_LEDGER.md"


@dataclass(frozen=True)
class Entry:
    num: int
    previous_hash: str | None
    chain_hash: str | None


def _entries(text: str) -> list[Entry]:
    """Parse ``(num, previous_hash, chain_hash)`` per ledger entry, in order."""
    out: list[Entry] = []
    matches = list(_ENTRY_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.start():end]
        prev = _PREV_RE.search(block)
        chain = _CHAIN_RE.search(block)
        out.append(Entry(int(m.group(1)),
                         prev.group(1) if prev else None,
                         chain.group(1) if chain else None))
    return out


@dataclass(frozen=True)
class BaseCurrencyResult:
    ok: bool
    message: str


def check_base_currency(branch_text: str, base_text: str) -> BaseCurrencyResult:
    """Assert the branch's first new-on-branch entry chains from the base tip."""
    base = _entries(base_text)
    base_chains = {e.chain_hash for e in base if e.chain_hash}
    base_tip = next((e.chain_hash for e in reversed(base) if e.chain_hash), None)
    first_new = next(
        (e for e in _entries(branch_text) if e.chain_hash and e.chain_hash not in base_chains),
        None,
    )
    if first_new is None:
        return BaseCurrencyResult(True, "no new entries on branch; base-current")
    if base_tip is None:
        return BaseCurrencyResult(True, "base has no sealed tip; skip")
    if first_new.previous_hash == base_tip:
        return BaseCurrencyResult(
            True, f"branch entry #{first_new.num} chains from base tip {base_tip[:8]}...")
    recorded = (first_new.previous_hash or "<none>")[:8]
    return BaseCurrencyResult(
        False,
        f"stale base: branch entry #{first_new.num} previous_hash {recorded}... != "
        f"origin tip {base_tip[:8]}...; rebase onto current base and re-seal "
        f"(reanchor recomputes the sub-chain).",
    )


@dataclass(frozen=True)
class ReanchoredEntry:
    previous_hash: str
    chain_hash: str
    entry_id: str


def reanchor(base_tip_chain: str, new_entries: list[dict]) -> list[ReanchoredEntry]:
    """Pure fold: rebuild a sub-chain onto ``base_tip_chain``.

    Each item is ``{content_hash, ts, phase}``. Returns the corrected
    ``(previous_hash, chain_hash, entry_id)`` sequence linking from the live base
    tip. Does NOT edit the ledger -- the operator applies the values."""
    out: list[ReanchoredEntry] = []
    prev = base_tip_chain
    for e in new_entries:
        chain = ledger_hash.chain_hash(e["content_hash"], prev)
        eid = entry_id.derive_entry_id(e["ts"], e["phase"], e["content_hash"])
        out.append(ReanchoredEntry(prev, chain, eid))
        prev = chain
    return out


def _base_ledger_text(repo_root: Path, base_ref: str) -> str | None:
    """Return the base ref's META_LEDGER, or None when the ref is unresolvable."""
    try:
        r = subprocess.run(
            ["git", "show", f"{base_ref}:{_LEDGER_REL}"],
            cwd=str(repo_root), capture_output=True, text=True,
            encoding="utf-8", check=True,  # force UTF-8 (Windows locale is cp1252)
        )
        return r.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--base-ref", default="origin/main")
    ap.add_argument("--enforce", action="store_true",
                    help="V2: exit 1 on a stale-base finding (default WARN-only)")
    args = ap.parse_args(argv)
    branch_path = args.repo_root / "docs" / "META_LEDGER.md"
    if not branch_path.is_file():
        print(f"SKIP: no {_LEDGER_REL}")
        return 0
    base_text = _base_ledger_text(args.repo_root, args.base_ref)
    if base_text is None:
        print(f"SKIP: base ref {args.base_ref!r} unresolvable (disclosed skip)")
        return 0
    res = check_base_currency(branch_path.read_text(encoding="utf-8"), base_text)
    if res.ok:
        print(f"OK: {res.message}")
        return 0
    print(f"WARN: {res.message}")
    return 1 if args.enforce else 0


if __name__ == "__main__":
    raise SystemExit(main())
