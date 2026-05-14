#!/usr/bin/env python3
"""Ledger hash and manifest utilities for Qor-logic migration.

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

# Phase 41 (issue #13): all three hash fields require the `**Field**` bold anchor,
# accept either inline-backtick `<hex>` or fenced `= <hex>` forms, and use a bounded
# non-greedy span that stops at the next `**FieldName**` marker. This prevents the
# pre-Phase-41 defects where CHAIN_HASH_RE matched prose mentions and where unbounded
# `.*?` under re.DOTALL swept across field boundaries into unrelated hex values.
#
# Phase 44: hash field labels MAY carry an optional parenthetical suffix inside the
# bold markers (e.g., `**Chain Hash (Merkle seal)**:`, `**Content Hash (session seal)**:`).
# This is the standard SESSION SEAL convention since Phase 23. The Phase 41 strict
# anchor `\*\*Field\*\*` did not match these and silently skipped seal entries; the
# `(?:\s*\([^)]+\))?` segment restores coverage without weakening bold-anchor protection.
_HASH_SPAN = r"(?:(?!\n\s*\*\*[A-Z])[\s\S])*?"
_HASH_VALUE = r"(?:`([0-9a-f]{64})`|=\s*([0-9a-f]{64})\b)"
_FIELD_SUFFIX = r"(?:\s*\([^)]+\))?"

CONTENT_HASH_RE = re.compile(rf"\*\*Content Hash{_FIELD_SUFFIX}\*\*{_HASH_SPAN}{_HASH_VALUE}")
PREV_HASH_RE = re.compile(rf"\*\*Previous Hash{_FIELD_SUFFIX}\*\*{_HASH_SPAN}{_HASH_VALUE}")
CHAIN_HASH_RE = re.compile(rf"\*\*Chain Hash{_FIELD_SUFFIX}\*\*{_HASH_SPAN}{_HASH_VALUE}")

# Phase 66 (GH #54): Session Seal markup recognition. Some historical seal
# entries use the form `**Session Seal**:\n SHA256(content + prev) = \`<hex>\``
# instead of the canonical `**Chain Hash (...)**: \`<hex>\``. The verifier
# treats the captured digest as the chain hash for those entries. The bounded
# span between the field anchor and the digest tolerates multi-line bodies
# but stops at the next `**Field**` marker, mirroring _HASH_SPAN in the
# canonical Chain Hash regex.
SESSION_SEAL_RE = re.compile(
    r"\*\*Session Seal\*\*"
    + _HASH_SPAN
    + r"=\s*`([0-9a-f]{64})`"
)


def is_placeholder_pattern(value: str) -> bool:
    """Return True if a 64-hex string matches an obvious-fabrication pattern.

    Conservative heuristics that flag well-known placeholder shapes without
    rejecting legitimate digests. Phase 66 closes the GH #54 failure mode
    where the FailSafe ledger Entry #331 used `a1b2c3d4e5f6...` pattern hex
    and downstream entries chain-verified against that untrusted seed.
    """
    if not isinstance(value, str) or len(value) != 64:
        return False
    lowered = value.lower()
    # Anchor exception: the all-zeros 64-hex string is the conventional
    # genesis previous_hash for an unrooted ledger. Verify() callers rely
    # on this convention; placeholder detector must not flag it.
    if lowered == "0" * 64:
        return False
    # Heuristic 1: ascending hex sequence "0123456789abcdef" appears as a unit.
    if "0123456789abcdef" in lowered or "fedcba9876543210" in lowered:
        return True
    # Heuristic 2: single repeating bigram across all 64 chars.
    if all(lowered[i:i+2] == lowered[0:2] for i in range(0, 64, 2)):
        return True
    # Heuristic 3: FailSafe-class pattern -- bytes form a constant arithmetic
    # progression modulo 256. The GH #54 example `a1b2c3d4e5f6a7b8...` parses
    # as bytes [0xa1, 0xb2, 0xc3, ...] with constant +0x11 delta mod 256.
    # Eight byte-pairs (16 hex chars) suffice to characterize the pattern.
    head_bytes = [int(lowered[i:i+2], 16) for i in range(0, 16, 2)]
    byte_diffs = [(head_bytes[i+1] - head_bytes[i]) % 256 for i in range(len(head_bytes) - 1)]
    if len(set(byte_diffs)) == 1 and byte_diffs[0] != 0:
        return True
    # Heuristic 4: high or low nibble across first 8 bytes (16 hex chars)
    # forms a monotonic mod-16 progression. The GH #54 FailSafe pattern
    # `a1b2c3d4e5f6a7b8` has low-nibbles [1,2,3,4,5,6,7,8] (monotonic +1)
    # paired with cycling high-nibbles. Either nibble being monotonic is
    # sufficient evidence of operator fabrication.
    head_high = [int(c, 16) for c in lowered[0:16:2]]
    head_low = [int(c, 16) for c in lowered[1:16:2]]
    if _is_monotonic_progression(head_high) or _is_monotonic_progression(head_low):
        return True
    # Heuristic 5: low entropy -- fewer than 6 distinct hex chars used.
    if len(set(lowered)) < 6:
        return True
    return False


def _is_monotonic_progression(nibbles: list[int]) -> bool:
    """Return True if a nibble sequence forms a single arithmetic
    progression modulo 16 (allowing wrap). Used by placeholder heuristic 4."""
    if len(nibbles) < 4:
        return False
    diffs = [(nibbles[i+1] - nibbles[i]) % 16 for i in range(len(nibbles) - 1)]
    return len(set(diffs)) == 1 and diffs[0] in {1, 15}


def verify(ledger_md: Path) -> int:
    """Verify chain integrity of META_LEDGER.md. Returns exit code.

    Phase 66 (GH #54) extensions:
    - Recognizes ``**Session Seal**: ... = `<hex>`` markup as a chain-hash source.
    - Flags placeholder-pattern hashes (see ``is_placeholder_pattern``) as FAIL.
    - Reports downstream entries after a FAIL as TAINTED (depend on failed predecessor).

    Output remains backward-compatible: ``OK Entry #N`` / ``FAIL Entry #N`` lines
    are preserved; new ``TAINTED Entry #N`` lines emit after failures; the
    ``Skipped N entries with non-verifiable markup`` summary counts entries
    that have neither canonical Chain Hash nor Session Seal markup.
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
    last_failed = 0
    for num, body in entries:
        ch = CONTENT_HASH_RE.search(body)
        ph = PREV_HASH_RE.search(body)
        xh = CHAIN_HASH_RE.search(body)
        seal_only = None
        if not (ch and ph and xh):
            # Phase 66: try Session Seal fallback when canonical markup absent.
            seal_only = SESSION_SEAL_RE.search(body) if not xh else None
            if not (ch and ph and seal_only):
                skipped += 1
                continue
        # Resolve recorded chain hash: canonical CHAIN_HASH_RE wins; else Session Seal.
        content_val = ch.group(1) or ch.group(2)
        previous_val = ph.group(1) or ph.group(2)
        if xh:
            recorded = xh.group(1) or xh.group(2)
        else:
            recorded = seal_only.group(1)
        # Phase 66 placeholder check: reject obvious fabrications before chain math.
        placeholder_field = _find_placeholder_field(content_val, previous_val, recorded)
        if placeholder_field is not None:
            print(
                f"FAIL Entry #{num}: placeholder-pattern detected in {placeholder_field}",
                file=sys.stderr,
            )
            errors += 1
            last_failed = num
            continue
        new_expected = chain_hash(content_val, previous_val)
        old_expected = legacy_chain_hash(content_val, previous_val)
        math_ok = (new_expected == recorded or old_expected == recorded)
        # Phase 66 taint propagation (per GH #54): once an earlier entry has
        # FAILed, every subsequent verifiable entry is TAINTED regardless of
        # its own math, because the chain root is poisoned. Math consistency
        # alone is not trust. Re-anchor / fix the upstream entry to clear taint.
        if last_failed:
            print(
                f"TAINTED Entry #{num}: depends on failed predecessor #{last_failed}",
                file=sys.stderr,
            )
            errors += 1
        elif math_ok:
            print(f"OK   Entry #{num}: chain hash verified")
        else:
            print(
                f"FAIL Entry #{num}: computed {new_expected} != recorded {recorded}",
                file=sys.stderr,
            )
            errors += 1
            last_failed = num
    if skipped > 0:
        print(f"Skipped {skipped} entries with non-verifiable markup")
    return 1 if errors else 0


def _find_placeholder_field(content: str, previous: str, chain: str) -> str | None:
    """Return the field name whose value matches a placeholder pattern, or None.

    Used by ``verify()`` to attribute placeholder failures to a specific hash
    field for operator remediation. Returns the first match in canonical order
    (content_hash > previous_hash > chain_hash) so messages remain stable
    across runs.
    """
    if is_placeholder_pattern(content):
        return "content_hash"
    if is_placeholder_pattern(previous):
        return "previous_hash"
    if is_placeholder_pattern(chain):
        return "chain_hash"
    return None


def verify_post_anchor(
    ledger_md: Path,
    boundary_entry: int | None = None,
) -> int:
    """Verify META_LEDGER.md post-anchor invariant. Returns exit code.

    Phase 66 (GH #55): re-anchored consumer ledgers carry disclosed
    pre-anchor failures by design. The post-anchor surface is what
    release gates check; pre-anchor failures are tolerated.

    Default boundary = highest-numbered entry whose chain math verifies under
    canonical or Session Seal markup AND whose hashes pass placeholder check.
    Operator may override via ``boundary_entry``.

    Exits 0 if every post-boundary entry verifies; non-zero if any
    post-boundary entry fails.
    """
    text = ledger_md.read_text(encoding="utf-8")
    entries = []
    parts = ENTRY_RE.split(text)
    for i in range(1, len(parts), 2):
        num = int(parts[i])
        body = parts[i + 1] if i + 1 < len(parts) else ""
        entries.append((num, body))

    # First pass: classify each entry as ok/fail without auto-anchor detection.
    classifications: list[tuple[int, str]] = []  # [(entry_num, "ok"|"fail")]
    for num, body in entries:
        ch = CONTENT_HASH_RE.search(body)
        ph = PREV_HASH_RE.search(body)
        xh = CHAIN_HASH_RE.search(body)
        if not (ch and ph and xh):
            seal_only = SESSION_SEAL_RE.search(body) if not xh else None
            if not (ch and ph and seal_only):
                continue  # unparseable: omitted from post-anchor surface
            recorded = seal_only.group(1)
        else:
            recorded = xh.group(1) or xh.group(2)
        content_val = ch.group(1) or ch.group(2)
        previous_val = ph.group(1) or ph.group(2)
        if _find_placeholder_field(content_val, previous_val, recorded):
            classifications.append((num, "fail"))
            continue
        expected = chain_hash(content_val, previous_val)
        expected_legacy = legacy_chain_hash(content_val, previous_val)
        if expected == recorded or expected_legacy == recorded:
            classifications.append((num, "ok"))
        else:
            classifications.append((num, "fail"))

    # Auto-detect boundary: highest entry id that classified ok.
    if boundary_entry is None:
        ok_entries = [n for (n, status) in classifications if status == "ok"]
        boundary_entry = max(ok_entries) if ok_entries else 0

    errors = 0
    for num, status in classifications:
        if status == "ok":
            print(f"OK Entry #{num}: chain hash verified (post-anchor)")
        elif num <= boundary_entry:
            print(f"DISCLOSED_PRE_ANCHOR Entry #{num}: tolerated pre-boundary failure")
        else:
            print(
                f"FAIL Entry #{num}: post-anchor verification failure",
                file=sys.stderr,
            )
            errors += 1

    if errors == 0:
        print(f"post-anchor clean (boundary=#{boundary_entry})")
    else:
        print(
            f"post-anchor DIRTY (boundary=#{boundary_entry}; {errors} post-boundary failures)",
            file=sys.stderr,
        )
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
