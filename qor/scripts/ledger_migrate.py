"""Normalize legacy META_LEDGER hash markup to the canonical verifiable form.

Phase 170 (GH #252): absorbed from FailSafe-Pro's proven
``scripts/migrate_ledger_v0_14.py`` with house discipline added: ``--dry-run``
(Phase 167 contract), idempotence (canonical input re-migrates byte-stable),
honest exit codes (1 when partial/no-hash entries remain), and same-path
rejection. Never in-place: ``--output`` is required and must differ from
``--input``. Hashes are preserved verbatim -- the tool moves MARKUP, not math;
chain-hash mismatches against both formulas (modern ``SHA256(content+"|"+prev)``
and legacy no-separator) are reported, never corrected.

Handles three legacy formats: (A) inline backticks; (B) fenced code blocks;
(C) session-seal labels (META_LEDGER Content Hash / Previous Chain Hash /
Session Seal). Canonical output is the form `qor.scripts.ledger_hash` parses:

    **Content Hash**: `<hex>`
    **Previous Hash**: `<hex>`
    **Chain Hash (Merkle seal)**: `<hex>`
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

ENTRY_RE = re.compile(r"^### Entry #(\d+):(.*)$", re.MULTILINE)

_HEX = r"[0-9a-f]{64}"

PATTERNS = [
    ("content_inline_hash", re.compile(
        r"\*\*Content Hash\*\*[^\n:]*:\s*`(" + _HEX + r")`")),
    ("content_inline_metaledger", re.compile(
        r"\*\*META_LEDGER Content Hash\*\*[^`]*`(" + _HEX + r")`")),
    ("content_fenced", re.compile(
        r"\*\*Content Hash\*\*[^\n:]*:\s*\n```[^`]*?=\s*(" + _HEX + r")\s*\n```",
        re.DOTALL)),
    ("content_bare", re.compile(
        r"\*\*Content Hash\*\*[^\n:]*:\s*(" + _HEX + r")\b")),
    ("content_merkle_fenced", re.compile(
        r"\*\*Session Merkle Seal[^\n*]*\*\*[^\n:]*:\s*\n```[^`]*?=\s*("
        + _HEX + r")\s*\n```", re.DOTALL)),
    ("prev_inline", re.compile(r"\*\*Previous Hash\*\*:\s*`(" + _HEX + r")`")),
    ("prev_bare", re.compile(r"\*\*Previous Hash\*\*:\s*(" + _HEX + r")\b")),
    ("prev_inline_chain", re.compile(
        r"\*\*Previous Chain Hash\*\*:\s*`(" + _HEX + r")`")),
    ("prev_bare_chain", re.compile(
        r"\*\*Previous Chain Hash\*\*:\s*(" + _HEX + r")\b")),
    ("chain_inline", re.compile(
        r"\*\*Chain Hash[^\n*]*\*\*[^\n:]*:\s*`(" + _HEX + r")`")),
    ("chain_fenced", re.compile(
        r"\*\*Chain Hash[^\n*]*\*\*[^\n:]*:\s*\n```[^`]*?=\s*(" + _HEX
        + r")\s*\n```", re.DOTALL)),
    ("chain_bare", re.compile(
        r"\*\*Chain Hash[^\n*]*\*\*[^\n:]*:\s*(" + _HEX + r")\b")),
    ("chain_session_seal", re.compile(
        r"\*\*Session Seal\*\*:\s*`(" + _HEX + r")`")),
]


def extract(body: str) -> tuple[str | None, str | None, str | None]:
    """Return (content, previous, chain); first match per family wins."""
    content = prev = chain = None
    for name, pat in PATTERNS:
        m = pat.search(body)
        if not m:
            continue
        if name.startswith("content_") and content is None:
            content = m.group(1)
        elif name.startswith("prev_") and prev is None:
            prev = m.group(1)
        elif name.startswith("chain_") and chain is None:
            chain = m.group(1)
    return content, prev, chain


_FENCED_STRIPS = [
    re.compile(r"\*\*(?:META_LEDGER )?Content Hash[^\n*]*\*\*[^\n:]*:\s*\n```[^`]*?```\n?", re.DOTALL),
    re.compile(r"\*\*Session Merkle Seal[^\n*]*\*\*[^\n:]*:\s*\n```[^`]*?```\n?", re.DOTALL),
    re.compile(r"\*\*Chain Hash[^\n*]*\*\*[^\n:]*:\s*\n```[^`]*?```\n?", re.DOTALL),
]
_INLINE_STRIPS = [re.compile(p) for p in (
    r"\*\*Content Hash[^\n*]*\*\*[^\n:]*:\s*`" + _HEX + r"`\s*\n?",
    r"\*\*Content Hash[^\n*]*\*\*[^\n:]*:\s*" + _HEX + r"\s*\n?",
    r"\*\*META_LEDGER Content Hash\*\*[^\n]*\n?",
    r"\*\*Previous Hash\*\*:\s*`" + _HEX + r"`\s*\n?",
    r"\*\*Previous Hash\*\*:\s*" + _HEX + r"\s*\n?",
    r"\*\*Previous Chain Hash\*\*:\s*`" + _HEX + r"`\s*\n?",
    r"\*\*Previous Chain Hash\*\*:\s*" + _HEX + r"\s*\n?",
    r"\*\*Chain Hash[^\n*]*\*\*[^\n:]*:\s*`" + _HEX + r"`\s*\n?",
    r"\*\*Chain Hash[^\n*]*\*\*[^\n:]*:\s*" + _HEX + r"\s*\n?",
    r"\*\*Session Seal\*\*:\s*`" + _HEX + r"`\s*\n?",
)]


def strip_hash_blocks(body: str) -> str:
    for pat in _FENCED_STRIPS:
        body = pat.sub("", body)
    for pat in _INLINE_STRIPS:
        body = pat.sub("", body)
    return body


def canonical_block(content: str, prev: str, chain: str) -> str:
    return (
        f"**Content Hash**: `{content}`\n"
        f"**Previous Hash**: `{prev}`\n"
        f"**Chain Hash (Merkle seal)**: `{chain}`\n"
    )


def _inject(body: str, tail: str) -> str:
    body = re.sub(r"\n{3,}", "\n\n", body)
    if "\n---\n" in body:
        before, _, after = body.rpartition("\n---\n")
        return before.rstrip() + "\n\n" + tail + "\n---\n" + after
    return body.rstrip() + "\n\n" + tail


def migrate(text: str) -> tuple[str, dict]:
    """Return (migrated_text, stats). Byte-stable on already-canonical input."""
    out: list[str] = []
    stats = {"total": 0, "migrated": 0, "unchanged_partial": 0,
             "unchanged_no_hash": 0, "mismatches": [], "partial_entries": []}
    parts = ENTRY_RE.split(text)
    out.append(parts[0])
    for i in range(1, len(parts), 3):
        num = int(parts[i])
        heading_rest = parts[i + 1]
        body = parts[i + 2] if i + 2 < len(parts) else ""
        stats["total"] += 1
        content, prev, chain = extract(body)
        out.append(f"### Entry #{num}:{heading_rest}")
        if content and prev and chain:
            legacy = hashlib.sha256((content + prev).encode("utf-8")).hexdigest()
            modern = hashlib.sha256((content + "|" + prev).encode("utf-8")).hexdigest()
            if chain not in (legacy, modern):
                stats["mismatches"].append({"entry": num, "recorded": chain})
            tail = canonical_block(content, prev, chain)
            candidate = _inject(strip_hash_blocks(body), tail)
            # Idempotence: if the entry is already canonical, keep bytes as-is.
            out.append(body if tail in body and "```" not in body else candidate)
            stats["migrated"] += 1
        else:
            out.append(body)
            if content or prev or chain:
                stats["unchanged_partial"] += 1
                stats["partial_entries"].append(num)
            else:
                stats["unchanged_no_hash"] += 1
    return "".join(out), stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true",
                    help="run the full transform + stats; write nothing (Phase 167)")
    args = ap.parse_args(argv)
    if args.input.resolve() == args.output.resolve():
        ap.error("--output must differ from --input (never in-place)")
    migrated, stats = migrate(args.input.read_text(encoding="utf-8"))
    residual = stats["unchanged_partial"] + stats["unchanged_no_hash"]
    for m in stats["mismatches"][:10]:
        print(f"WARN entry #{m['entry']}: chain hash matches neither formula "
              f"(recorded {m['recorded'][:16]}...; preserved verbatim)")
    for num in stats["partial_entries"][:10]:
        print(f"WARN entry #{num}: partial hash markup; left verbatim (manual review)")
    if args.dry_run:
        print(f"[dry] would write {args.output}")
    else:
        args.output.write_text(migrated, encoding="utf-8")
        print(f"wrote {args.output}")
    print(f"ledger_migrate: total={stats['total']} migrated={stats['migrated']} "
          f"partial={stats['unchanged_partial']} no_hash={stats['unchanged_no_hash']} "
          f"mismatches={len(stats['mismatches'])}")
    return 1 if residual else 0


if __name__ == "__main__":
    raise SystemExit(main())
