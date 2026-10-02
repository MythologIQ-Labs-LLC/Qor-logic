#!/usr/bin/env python3
"""Verify qor/dist/ matches what compile.py would produce.

Regenerates into a tempdir, then diffs byte-for-byte via hashlib against
the committed qor/dist. Exits 0 on clean, 1 on drift.
A manifest.json is compared as its parsed JSON without the volatile
generated_ts key (Phase 302, GH #440).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from qor.scripts import dist_compile as compile_mod

from qor import resources as _resources

COMMITTED_DIST = Path(str(_resources.asset("dist")))


# Phase 302 (GH #440): manifest.json was excluded from the comparison because
# it carries a compile-time timestamp. It is now compared with that one key
# removed, so a manifest whose file list or sha256 values do not describe the
# shipped bytes is drift.
_MANIFEST_NAME = "manifest.json"
_VOLATILE_MANIFEST_KEYS = ("generated_ts",)


def _comparable_bytes(p: Path) -> bytes:
    """The bytes drift compares: the file's own bytes, except that a manifest
    is compared as its parsed JSON without its volatile keys. An unparseable
    manifest is compared raw, so it differs from any regenerated one."""
    data = p.read_bytes()
    if p.name != _MANIFEST_NAME:
        return data
    try:
        doc = json.loads(data)
    except ValueError:
        return data
    if isinstance(doc, dict):
        doc = {k: v for k, v in doc.items() if k not in _VOLATILE_MANIFEST_KEYS}
    return json.dumps(doc, sort_keys=True).encode("utf-8")


def hash_tree(root: Path) -> dict[str, str]:
    """Map of relative-path -> sha256. Deterministic snapshot of a directory tree."""
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            h = hashlib.sha256(_comparable_bytes(p)).hexdigest()
            out[rel] = h
    return out


def compare(committed: dict[str, str], regenerated: dict[str, str]) -> list[str]:
    diffs: list[str] = []
    all_paths = set(committed) | set(regenerated)
    for p in sorted(all_paths):
        c = committed.get(p)
        r = regenerated.get(p)
        if c is None:
            diffs.append(f"  + {p} (only in regenerated)")
        elif r is None:
            diffs.append(f"  - {p} (only in committed; stale?)")
        elif c != r:
            diffs.append(f"  ~ {p} (content differs)")
    return diffs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--committed", type=Path, default=COMMITTED_DIST)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="qor-drift-") as tmp:
        tmp_path = Path(tmp)
        compile_mod.compile_all(tmp_path)
        regenerated_root = tmp_path
        # compile_all writes under <out>/variants/, and committed dist also has variants/
        # Hash both roots at the same level
        committed_hashes = hash_tree(args.committed)
        regenerated_hashes = hash_tree(regenerated_root)

    diffs = compare(committed_hashes, regenerated_hashes)
    if diffs:
        print(f"DRIFT DETECTED: {len(diffs)} difference(s)")
        for d in diffs[:50]:
            print(d)
        if len(diffs) > 50:
            print(f"  ... and {len(diffs) - 50} more")
        print("\nFix: BUILD_REGEN=1 python qor/scripts/dist_compile.py && git add qor/dist/")
        return 1
    print(f"OK: {len(committed_hashes)} files, no drift")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
