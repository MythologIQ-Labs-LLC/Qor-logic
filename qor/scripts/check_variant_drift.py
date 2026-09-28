#!/usr/bin/env python3
"""Verify qor/dist/ matches what dist_compile.py would produce.

Regenerates into a tempdir, then diffs deterministic content against the
committed qor/dist. Manifest timestamps are intentionally ignored, but every
other manifest field, including per-artifact SHA256 claims, is verified.
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


def _content_hash(path: Path) -> str:
    """Return a deterministic hash, normalizing only manifest generated_ts."""
    if path.name == "manifest.json":
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("generated_ts", None)
        payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    else:
        payload = path.read_bytes()
    return hashlib.sha256(payload).hexdigest()


def hash_tree(root: Path) -> dict[str, str]:
    """Map relative path to deterministic content hash for every dist file."""
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            out[rel] = _content_hash(p)
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
        committed_hashes = hash_tree(args.committed)
        regenerated_hashes = hash_tree(tmp_path)

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
