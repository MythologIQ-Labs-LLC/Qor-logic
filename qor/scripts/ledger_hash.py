#!/usr/bin/env python3
"""Ledger hash and manifest utilities for QorLogic migration.

Provides:
- content_hash(path): SHA256 of file bytes
- chain_hash(content, prev): SHA256(content + prev)
- write_manifest(root, globs, out): enumerate files, emit sorted JSON manifest
- verify(ledger_md): recompute chain hashes from META_LEDGER.md entries

Atomic writes via os.replace (Windows-safe).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def content_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def chain_hash(content: str, prev: str) -> str:
    """SHA256(content + "|" + prev) -- Phase 23 format with separator."""
    return hashlib.sha256((content + "|" + prev).encode("utf-8")).hexdigest()


def legacy_chain_hash(content: str, prev: str) -> str:
    """SHA256(content + prev) -- pre-Phase 23 format without separator."""
    return hashlib.sha256((content + prev).encode("utf-8")).hexdigest()


def write_manifest(root: Path, include_globs: list[str], output: Path) -> dict:
    """Walk root matching include_globs; emit manifest sorted by path."""
    paths: list[dict[str, str]] = []
    for glob in include_globs:
        for p in sorted(root.glob(glob)):
            if p.is_file():
                rel = p.relative_to(root).as_posix()
                paths.append({"path": rel, "sha256": content_hash(p)})
            elif p.is_dir():
                for f in sorted(p.rglob("*")):
                    if f.is_file():
                        rel = f.relative_to(root).as_posix()
                        paths.append({"path": rel, "sha256": content_hash(f)})
    # Dedupe preserving first occurrence
    seen = set()
    deduped = []
    for item in paths:
        if item["path"] not in seen:
            seen.add(item["path"])
            deduped.append(item)
    deduped.sort(key=lambda x: x["path"])
    manifest = {
        "schema_version": "1",
        "generated_ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root.resolve().as_posix()),
        "paths": deduped,
    }
    _atomic_write_json(output, manifest)
    return manifest


def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as tf:
        json.dump(data, tf, indent=2, sort_keys=False)
        tf.write("\n")
        tmp_path = tf.name
    os.replace(tmp_path, path)


ENTRY_RE = re.compile(r"^### Entry #(\d+):", re.MULTILINE)
CONTENT_HASH_RE = re.compile(r"\*\*Content Hash\*\*.*?`([0-9a-f]{64})`", re.DOTALL)
PREV_HASH_RE = re.compile(r"\*\*Previous Hash\*\*.*?`([0-9a-f]{64})`", re.DOTALL)
# Chain Hash accepts either form: `= <hex>` (fenced/equation) or `` `<hex>` `` (inline backtick).
# The inline-backtick form is symmetric with CONTENT_HASH_RE / PREV_HASH_RE; the equation form
# preserves backward compatibility with legacy entries written before Phase 23.
CHAIN_HASH_RE = re.compile(
    r"Chain Hash.*?(?:=\s*([0-9a-f]{64})\b|`([0-9a-f]{64})`)",
    re.DOTALL,
)


def verify(ledger_md: Path) -> int:
    """Verify chain integrity of META_LEDGER.md. Returns exit code.

    Tries new format (with separator) first, falls back to legacy (without).
    Reports count of entries skipped due to non-matching markup.
    """
    text = ledger_md.read_text(encoding="utf-8")
    entries = []
    parts = ENTRY_RE.split(text)
    for i in range(1, len(parts), 2):
        num = int(parts[i])
        body = parts[i + 1] if i + 1 < len(parts) else ""
        entries.append((num, body))

    errors = 0
    skipped = 0
    for num, body in entries:
        ch = CONTENT_HASH_RE.search(body)
        ph = PREV_HASH_RE.search(body)
        xh = CHAIN_HASH_RE.search(body)
        if not (ch and ph and xh):
            skipped += 1
            continue
        # CHAIN_HASH_RE has two alternation groups; exactly one is populated.
        recorded = xh.group(1) or xh.group(2)
        new_expected = chain_hash(ch.group(1), ph.group(1))
        old_expected = legacy_chain_hash(ch.group(1), ph.group(1))
        if new_expected == recorded or old_expected == recorded:
            print(f"OK   Entry #{num}: chain hash verified")
        else:
            print(
                f"FAIL Entry #{num}: computed {new_expected} != recorded {recorded}",
                file=sys.stderr,
            )
            errors += 1
    if skipped > 0:
        print(f"Skipped {skipped} entries with non-verifiable markup")
    return 1 if errors else 0


SSDF_RE = re.compile(r"\*\*SSDF Practices\*\*:\s*(.+)")


def extract_ssdf_practices(ledger_md: Path) -> dict[int, list[str]]:
    """Extract SSDF practice tags from ledger entries. Returns {entry_num: [practices]}."""
    text = ledger_md.read_text(encoding="utf-8")
    result: dict[int, list[str]] = {}
    parts = ENTRY_RE.split(text)
    for i in range(1, len(parts), 2):
        num = int(parts[i])
        body = parts[i + 1] if i + 1 < len(parts) else ""
        m = SSDF_RE.search(body)
        if m:
            practices = [p.strip() for p in m.group(1).split(",")]
            result[num] = practices
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Ledger hash utility")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub_v = sub.add_parser("verify", help="Verify META_LEDGER.md chain")
    sub_v.add_argument("ledger", type=Path)

    sub_h = sub.add_parser("hash", help="SHA256 of a file")
    sub_h.add_argument("path", type=Path)

    sub_m = sub.add_parser("manifest", help="Write manifest of matched paths")
    sub_m.add_argument("--root", type=Path, required=True)
    sub_m.add_argument("--glob", action="append", required=True)
    sub_m.add_argument("--out", type=Path, required=True)

    sub_c = sub.add_parser("chain", help="Compute chain hash")
    sub_c.add_argument("content_hash")
    sub_c.add_argument("previous_hash")

    args = ap.parse_args()
    if args.cmd == "verify":
        return verify(args.ledger)
    if args.cmd == "hash":
        print(content_hash(args.path))
        return 0
    if args.cmd == "manifest":
        m = write_manifest(args.root, args.glob, args.out)
        print(f"Wrote {len(m['paths'])} paths -> {args.out}")
        return 0
    if args.cmd == "chain":
        print(chain_hash(args.content_hash, args.previous_hash))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
