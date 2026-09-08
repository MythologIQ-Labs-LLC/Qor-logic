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

from qor.scripts import ledger_dialect as _dialect


def content_hash(path: Path) -> str:
    """SHA256 of the file's bytes with line endings normalized to LF.

    GAP-GOV-03 follow-on: the content_hash<->plan binding must be invariant to
    line-ending conversion. Git's autocrlf rewrites a committed/checked-out file
    to CRLF, so hashing raw bytes makes the seal-time digest (computed on the LF
    working copy) disagree with the recompute on the committed file. Normalizing
    CRLF -> LF before hashing keeps the digest stable across that conversion; it
    is a no-op for already-LF files, so existing recorded hashes are unchanged.
    """
    data = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def chain_hash(content: str, prev: str) -> str:
    """SHA256(content + "|" + prev) -- Phase 23 format with separator."""
    return hashlib.sha256((content + "|" + prev).encode("utf-8")).hexdigest()


def legacy_chain_hash(content: str, prev: str) -> str:
    """SHA256(content + prev) -- pre-Phase 23 format without separator."""
    return hashlib.sha256((content + prev).encode("utf-8")).hexdigest()


# Smart-punctuation -> ASCII map (GH #201). Opt-in authoring helper: callers
# normalize BEFORE computing a content hash so the seal commits to ASCII bytes.
# The gate (assert_sealable_text) rejects rather than silently rewrites, so a
# hash never desyncs from the bytes it was computed over.
_PUNCTUATION_ASCII = {
    "\u2014": "--",   # em-dash
    "\u2013": "-",    # en-dash
    "\u2018": "'",    # left single quote
    "\u2019": "'",    # right single quote
    "\u201c": '"',    # left double quote
    "\u201d": '"',    # right double quote
    "\u2192": "->",   # rightwards arrow
    "\u2026": "...",  # horizontal ellipsis
}


def normalize_punctuation(text: str) -> str:
    """Map common non-ASCII punctuation to ASCII equivalents (idempotent).

    Output is ASCII for the mapped set; characters outside the map are left
    unchanged (``assert_sealable_text`` is the gate that rejects any residual
    non-ASCII). Re-applying the map is a no-op.
    """
    for src, dst in _PUNCTUATION_ASCII.items():
        text = text.replace(src, dst)
    return text


def assert_sealable_text(text: str, *, label: str = "entry body") -> None:
    """Raise ``ValueError`` if ``text`` is not pure ASCII (GH #201).

    A sealable ledger body/title must be ASCII before its content hash is
    computed, so codepoint-truncated / cp1252 / invalid-UTF-8 bytes can never be
    committed to a hash and render the ledger unreadable. The message names the
    first offending character, its codepoint, and its index for remediation.
    """
    if text.isascii():
        return
    for index, char in enumerate(text):
        if not char.isascii():
            raise ValueError(
                f"{label} contains non-ASCII character U+{ord(char):04X} "
                f"at index {index}; normalize (see normalize_punctuation) or "
                f"remove it before sealing"
            )


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

#: Entry numbers allocated but never committed, verified absent from every
#: commit (`git log --all -S "Entry #510"` returns nothing; #532 was allocated
#: in an abandoned Phase 215 session). Neither can be closed by renumbering --
#: that would invalidate every downstream chain hash. Contiguity is a WARN, so
#: these are silenced rather than tolerated; tests/test_ledger_sequence.py
#: derives the live gap set and asserts it equals this constant, so widening it
#: to silence a NEW gap goes red.
KNOWN_ENTRY_GAPS = frozenset({510, 532})

# GH #282: the hash-markup dialect (inline-backtick, `= <hex>`, and fenced
# bare-hex) and the historical compatibility boundary now live in the shared
# `ledger_dialect` module, so ledger_hash, seal_entry_check, and
# governance_health accept exactly one dialect. The Phase 41 bounded-span /
# bold-anchor protection and the Phase 44 optional-suffix + Phase 66 Session
# Seal recognition are preserved there. Re-exported here so existing callers
# (and tests) that reference these names keep working.
CONTENT_HASH_RE = _dialect.CONTENT_HASH_RE
PREV_HASH_RE = _dialect.PREV_HASH_RE
CHAIN_HASH_RE = _dialect.CHAIN_HASH_RE
SESSION_SEAL_RE = _dialect.SESSION_SEAL_RE

# Phase 119 (GH #148): a RECONCILIATION entry's machine-parseable attestation
# line, e.g. `**Reconciled Entries**: #16, #17, #18`. verify() honors the
# attestation only for entries that are genuinely duplicate-previous_hash
# members (so it cannot launder content tampering of a unique entry).
RECONCILED_ENTRIES_RE = re.compile(r"\*\*Reconciled Entries\*\*:\s*([#0-9,\s]+)")


def is_placeholder_pattern(value: str) -> bool:
    """Return True if a 64-hex string matches an obvious-fabrication pattern.

    Conservative heuristics that flag well-known placeholder shapes without
    rejecting legitimate digests. Phase 66 closes the GH #54 failure mode
    where a sibling product's ledger Entry #331 used `a1b2c3d4e5f6...` pattern hex
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
    # Heuristic 3: issue-54-class pattern -- bytes form a constant arithmetic
    # progression modulo 256. The GH #54 example `a1b2c3d4e5f6a7b8...` parses
    # as bytes [0xa1, 0xb2, 0xc3, ...] with constant +0x11 delta mod 256.
    # Eight byte-pairs (16 hex chars) suffice to characterize the pattern.
    head_bytes = [int(lowered[i:i+2], 16) for i in range(0, 16, 2)]
    byte_diffs = [(head_bytes[i+1] - head_bytes[i]) % 256 for i in range(len(head_bytes) - 1)]
    if len(set(byte_diffs)) == 1 and byte_diffs[0] != 0:
        return True
    # Heuristic 4: high or low nibble across first 8 bytes (16 hex chars)
    # forms a monotonic mod-16 progression. The GH #54 source pattern
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


def find_grandfathered_entries(
    ledger_md: Path,
    cutoff: int = 207,
) -> frozenset[int]:
    """Return entry numbers whose previous_hash is shared by 2+ entries AND
    whose entry number is <= cutoff.

    These are the SG-ConcurrentLedgerRace-A documented residuals (Phase 91
    wiring; GH #85) -- pre-V1 concurrent-append duplicates explicitly
    grandfathered by the Phase 76 forbidden-interpretation clause. The
    cutoff (default 207, matching ``check_previous_hash_uniqueness``'s
    ``min_entry_num``) is a hard upper bound: post-cutoff entries are not
    grandfathered even when they share a previous_hash, preserving the
    forward-only-no-new-grandfathering invariant.
    """
    text = ledger_md.read_text(encoding="utf-8")
    entries: list[tuple[int, str]] = []
    parts = ENTRY_RE.split(text)
    for i in range(1, len(parts), 2):
        num = int(parts[i])
        body = parts[i + 1] if i + 1 < len(parts) else ""
        entries.append((num, body))

    # Group entry numbers by previous_hash value.
    by_prev: dict[str, list[int]] = {}
    for num, body in entries:
        ph = PREV_HASH_RE.search(body)
        if not ph:
            continue
        prev_val = _dialect.hash_value(ph)
        by_prev.setdefault(prev_val, []).append(num)

    grandfathered: set[int] = set()
    for nums in by_prev.values():
        if len(nums) < 2:
            continue
        for n in nums:
            if n <= cutoff:
                grandfathered.add(n)
    return frozenset(grandfathered)


def _duplicate_previous_hash_members(entries: list[tuple[int, str]]) -> set[int]:
    """Entry numbers sharing a previous_hash with >=1 other entry (no cutoff).
    The genuine duplicate-previous_hash residual a RECONCILIATION entry may
    attest. Used to gate reconciliation toleration so a unique-previous_hash
    tampered entry cannot be laundered by an attestation."""
    by_prev: dict[str, list[int]] = {}
    for num, body in entries:
        ph = PREV_HASH_RE.search(body)
        if not ph:
            continue
        by_prev.setdefault(_dialect.hash_value(ph), []).append(num)
    members: set[int] = set()
    for nums in by_prev.values():
        if len(nums) >= 2:
            members.update(nums)
    return members


def _attested_reconciled(entries: list[tuple[int, str]]) -> set[int]:
    """Union of entry numbers named on `**Reconciled Entries**:` lines across
    all RECONCILIATION entries in the ledger."""
    attested: set[int] = set()
    for _num, body in entries:
        m = RECONCILED_ENTRIES_RE.search(body)
        if not m:
            continue
        for tok in re.findall(r"#(\d+)", m.group(1)):
            attested.add(int(tok))
    return attested


_ATTESTED_LINE_RE = re.compile(r"^#(\d+)=([0-9a-f]{12})\s*$", re.MULTILINE)


def _migration_attested(entries: list[tuple[int, str]]) -> dict[int, tuple[str, int]]:
    """Phase 193 (GH #278): {legacy_num: (digest12, attesting_entry)} from
    MIGRATION ATTESTATION entries' **Attested Entries** blocks."""
    out: dict[int, tuple[str, int]] = {}
    for num, body in entries:
        if "**Attested Entries**:" not in body:
            continue
        for m in _ATTESTED_LINE_RE.finditer(body):
            out[int(m.group(1))] = (m.group(2), num)
    return out


def _dispose_unresolvable(
    num: int,
    body: str,
    markup_required_cutoff: int,
    migration_attested: dict[int, tuple[str, int]],
) -> tuple[str, str, bool]:
    """Dispose of an entry whose hashes do not resolve. Shared by both modes.

    Phase 270 (GH #443, #425, #430): verify() disposed of these through four
    rungs and verify_post_anchor reimplemented only the last two, so a modern
    entry with no markup and a migration-attested entry were both invisible to
    the gate that release actually consumes. Measured before the change on this
    repository's ledger: 735 of 757 entries reported, and all 22 omitted were
    migration-attested. A hand-reimplemented subset of a ladder is where this
    phase's defects came from, so there is one ladder and both modes walk it.

    Returns ``(status, message, to_stderr)`` where status is ``"ok"``,
    ``"fail"`` or ``"skip"``. The caller owns printing and counting, because
    the two modes disagree about what an error costs, not about what an entry is.
    """
    # Rung 1 (GAP-GOV-09): a modern entry MUST carry verifiable hash markup.
    if num >= markup_required_cutoff:
        return (
            "fail",
            f"FAIL Entry #{num}: missing canonical hash markup "
            f"(required at/after entry #{markup_required_cutoff})",
            True,
        )
    # Rung 2 (Phase 193, GH #278): the pre-convention band is digest-bound by a
    # MIGRATION ATTESTATION entry, so an edited legacy body is a failure rather
    # than a silent skip. This is stronger than a skip, which is why post-anchor
    # omitting it was a loss and not a tolerance.
    if num in migration_attested:
        digest, attester = migration_attested[num]
        if _legacy_body_digest(body) == digest:
            return ("ok", f"OK   Entry #{num}: attested by migration entry #{attester}", False)
        return (
            "fail",
            f"FAIL Entry #{num}: attestation digest mismatch "
            f"(attested {digest} by entry #{attester})",
            True,
        )
    # Rung 3 (GH #363): an entry that NAMES a hash field is making a claim, and
    # a value the dialect cannot read is a broken claim regardless of number.
    if _dialect.any_hash_label_present(body):
        return (
            "fail",
            f"FAIL Entry #{num}: hash field labeled but its value "
            f"matches no recognized form",
            True,
        )
    # Rung 4: an entry with no hash label at all claims nothing.
    return ("skip", "", False)


def _legacy_body_digest(body: str) -> str:
    data = body.encode("utf-8").replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()[:12]


def _resolve_recorded(body: str) -> tuple[str, str, str] | None:
    """Return (content_val, previous_val, recorded_chain) for an entry body, or
    None when it carries neither canonical Content/Previous/Chain markup nor a
    Session-Seal fallback (the 'skipped, non-verifiable markup' case). Phase 66:
    canonical CHAIN_HASH_RE wins; otherwise the Session-Seal hash is the recorded
    chain hash."""
    ch = CONTENT_HASH_RE.search(body)
    ph = PREV_HASH_RE.search(body)
    xh = CHAIN_HASH_RE.search(body)
    seal_only = None
    if not (ch and ph and xh):
        seal_only = SESSION_SEAL_RE.search(body) if not xh else None
        if not (ch and ph and seal_only):
            return None
    content_val = _dialect.hash_value(ch)
    previous_val = _dialect.hash_value(ph)
    recorded = _dialect.hash_value(xh) if xh else seal_only.group(1)
    return content_val, previous_val, recorded


def _classify_entry(num: int, content_val: str, previous_val: str, recorded: str, *,
                    grandfathered, reconciled, last_failed: int) -> tuple[str, bool, bool, bool]:
    """Classify one resolved entry. Returns (message, to_stderr, is_error,
    sets_last_failed). Pure (no I/O). Order matters and matches the original
    verify() flow: placeholder -> FAIL (sets last_failed even under taint);
    prior failure -> TAINTED (error, but does NOT advance last_failed); chain-math
    OK -> OK; grandfathered/reconciled tolerance -> DISCLOSED_* (no error); else
    a genuine math FAIL (sets last_failed)."""
    placeholder_field = _find_placeholder_field(content_val, previous_val, recorded)
    if placeholder_field is not None:
        return (f"FAIL Entry #{num}: placeholder-pattern detected in {placeholder_field}",
                True, True, True)
    new_expected = chain_hash(content_val, previous_val)
    old_expected = legacy_chain_hash(content_val, previous_val)
    math_ok = (new_expected == recorded or old_expected == recorded)
    if last_failed:
        return (f"TAINTED Entry #{num}: depends on failed predecessor #{last_failed}",
                True, True, False)
    if math_ok:
        return (f"OK   Entry #{num}: chain hash verified", False, False, False)
    if num in grandfathered:
        return (f"DISCLOSED_GRANDFATHERED Entry #{num}: tolerated "
                f"SG-ConcurrentLedgerRace-A residual", False, False, False)
    if num in reconciled:
        return (f"DISCLOSED_RECONCILED Entry #{num}: attested by RECONCILIATION entry",
                False, False, False)
    return (f"FAIL Entry #{num}: computed {new_expected} != recorded {recorded}",
            True, True, True)



def _sequence_break_pairs(
    entries: list[tuple[int, str]],
    tolerated: frozenset[int] | set[int] = frozenset(),
) -> list[tuple[tuple[int, int], str]]:
    """``_sequence_breaks`` with the adjacent pair the break is a property OF.

    Phase 270: a break belongs to a PAIR in file order, not to one entry. The
    post-anchor mode must compare it against a boundary, and comparing only the
    successor's number would fail the wrong entry -- the message says "an entry
    may have been removed", so the successor is not the damaged link. Both
    members are returned and the caller requires both to sit at or below an
    asserted boundary before disclosing it.

    ``_sequence_breaks`` delegates here so the two cannot drift: one traversal,
    one set of tolerance semantics, and the message is produced once.
    """
    pairs: list[tuple[tuple[int, int], str]] = []
    previous_chain: str | None = None
    previous_num: int | None = None
    for num, body in entries:
        resolved = _resolve_recorded(body)
        if resolved is None:
            previous_chain = None
            previous_num = None
            continue
        _content, previous_val, recorded = resolved
        if num in tolerated:
            previous_chain = None
            previous_num = None
            continue
        if previous_chain is not None and previous_val != previous_chain:
            pairs.append(
                (
                    (previous_num if previous_num is not None else num, num),
                    f"BREAK Entry #{num}: previous_hash {previous_val[:16]} was not "
                    f"produced by the preceding entry (chain {previous_chain[:16]}); "
                    "an entry may have been removed",
                )
            )
        previous_chain = recorded
        previous_num = num
    return pairs


def _sequence_breaks(
    entries: list[tuple[int, str]],
    tolerated: frozenset[int] | set[int] = frozenset(),
) -> list[str]:
    """Entries whose previous_hash was not produced by the entry before them.

    File order, not number order. The chain is built by appending, so adjacency
    in the artifact is the real structure and entry numbers are labels; a
    number-keyed check would fail at every KNOWN_ENTRY_GAPS position despite
    intact links.

    Per-entry arithmetic cannot see a deletion: every survivor stays internally
    consistent. This is the assertion that can (GH #316).
    """
    return [message for _pair, message in _sequence_break_pairs(entries, tolerated)]


def _number_gaps(entries: list[tuple[int, str]]) -> list[int]:
    """Undeclared holes in entry numbering. WARN-only; see KNOWN_ENTRY_GAPS."""
    nums = [n for n, _ in entries]
    if not nums:
        return []
    seen = set(nums)
    return [n for n in range(min(nums), max(nums))
            if n not in seen and n not in KNOWN_ENTRY_GAPS]


def _duplicate_entry_numbers(entries: list[tuple[int, str]]) -> list[int]:
    """Entry numbers appearing more than once (a ledger fork: two branches
    independently allocated the same #N). Mirror image of ``_number_gaps``,
    and a hard FAIL rather than a WARN -- unlike a gap, a duplicate number
    cannot be closed by renumbering (that would invalidate every downstream
    chain hash) and is not detectable from per-entry chain math alone: two
    honestly-chained branches forking from the same predecessor each verify
    individually (GH #361)."""
    seen: set[int] = set()
    dupes: list[int] = []
    for num, _ in entries:
        if num in seen and num not in dupes:
            dupes.append(num)
        seen.add(num)
    return dupes



def _report_sequence(
    entries: list[tuple[int, str]],
    tolerated: frozenset[int] | set[int] = frozenset(),
) -> int:
    """Emit sequence breaks and numbering warnings; return the error count.

    Kept out of ``verify`` deliberately. ``verify`` is a pre-existing Section 4
    length violation; Phase 218 must not enlarge it, and this reporting is
    separable on its own merits.
    """
    errors = 0
    dupes = _duplicate_entry_numbers(entries)
    if dupes:
        print(
            f"FAIL: duplicate entry number(s) {dupes}: two entries share the "
            "same #N (a ledger fork). Renumbering is forbidden (it would "
            "invalidate downstream chain hashes); reconcile the branches "
            "before this can verify.",
            file=sys.stderr,
        )
        errors += len(dupes)
    for message in _sequence_breaks(entries, tolerated):
        print(message, file=sys.stderr)
        errors += 1
    gaps = _number_gaps(entries)
    if gaps:
        print(
            f"WARN: undeclared entry-number gap(s): {gaps}. Links may still be "
            "intact; add to KNOWN_ENTRY_GAPS only with a recorded reason."
        )
    return errors


def verify(
    ledger_md: Path,
    *,
    tolerate_known_grandfathered: bool = False,
    grandfather_cutoff: int = 207,
    markup_required_cutoff: int = _dialect.MARKUP_COMPAT_BOUNDARY,
) -> int:
    """Verify chain integrity of META_LEDGER.md. Returns exit code.

    Phase 66 (GH #54) extensions:
    - Recognizes ``**Session Seal**: ... = `<hex>`` markup as a chain-hash source.
    - Flags placeholder-pattern hashes (see ``is_placeholder_pattern``) as FAIL.
    - Reports downstream entries after a FAIL as TAINTED (depend on failed predecessor).

    Phase 91 (GH #85) extension:
    - ``tolerate_known_grandfathered=True`` accepts chain-math failures iff the
      failing entry is in the SG-ConcurrentLedgerRace-A documented residual
      set (its ``previous_hash`` appears in 2+ entries AND its entry number is
      ``<= grandfather_cutoff``). Tolerated failures produce a
      ``DISCLOSED_GRANDFATHERED Entry #N`` line on stdout instead of ``FAIL``
      on stderr, do NOT contribute to the error count, and do NOT propagate
      TAINTED to downstream entries. Flag OFF by default; strict mode is the
      canonical gate.

    Output remains backward-compatible: ``OK Entry #N`` / ``FAIL Entry #N`` lines
    are preserved; new ``TAINTED Entry #N`` lines emit after failures; the
    ``Skipped N entries with non-verifiable markup`` summary counts entries
    that have neither canonical Chain Hash nor Session Seal markup.
    """
    grandfathered = (
        find_grandfathered_entries(ledger_md, cutoff=grandfather_cutoff)
        if tolerate_known_grandfathered
        else frozenset()
    )
    text = ledger_md.read_text(encoding="utf-8")
    entries = []
    parts = ENTRY_RE.split(text)
    for i in range(1, len(parts), 2):
        num = int(parts[i])
        body = parts[i + 1] if i + 1 < len(parts) else ""
        entries.append((num, body))

    # Phase 119 (GH #148): entries attested by an in-chain RECONCILIATION entry
    # are tolerated WITHOUT the --tolerate-known-grandfathered flag, but only
    # when they are genuine duplicate-previous_hash members (security gate).
    reconciled = _attested_reconciled(entries) & _duplicate_previous_hash_members(entries)

    migration_attested = _migration_attested(entries)
    errors = 0
    skipped = 0
    last_failed = 0
    for num, body in entries:
        resolved = _resolve_recorded(body)
        if resolved is None:
            # GAP-GOV-09: a modern entry (>= markup_required_cutoff) MUST carry
            # verifiable hash markup; an unmarked one is a FAIL, not a silent
            # skip. Entries below the cutoff are pre-convention historical
            # entries and stay grandfathered (recorded only in the skip summary).
            if num >= markup_required_cutoff:
                print(
                    f"FAIL Entry #{num}: missing canonical hash markup "
                    f"(required at/after entry #{markup_required_cutoff})",
                    file=sys.stderr,
                )
                errors += 1
                last_failed = num
            elif num in migration_attested:
                # Phase 193 (GH #278): the pre-convention band is digest-bound
                # by a MIGRATION ATTESTATION entry; re-check the digest so an
                # edited legacy body is a FAILURE, not a silent skip.
                digest, attester = migration_attested[num]
                if _legacy_body_digest(body) == digest:
                    print(f"OK   Entry #{num}: attested by migration entry #{attester}")
                else:
                    print(
                        f"FAIL Entry #{num}: attestation digest mismatch "
                        f"(attested {digest} by entry #{attester})",
                        file=sys.stderr,
                    )
                    errors += 1
                    last_failed = num
            elif _dialect.any_hash_label_present(body):
                # GH #404: `markup_required_cutoff` is an absolute entry number
                # from THIS repository's history, so below it every unparseable
                # entry degraded to an informational skip and exit 0 -- in a
                # workspace younger than the cutoff, that is every entry.
                # GH #363 already drew the right line in verify_post_anchor:
                # an entry that NAMES a hash field is making a claim, and a
                # value the dialect cannot read is a broken claim regardless of
                # entry number. An entry with no hash label at all claims
                # nothing and stays a tolerated pre-convention skip.
                print(
                    f"FAIL Entry #{num}: hash field labeled but its value "
                    f"matches no recognized form",
                    file=sys.stderr,
                )
                errors += 1
                last_failed = num
            else:
                skipped += 1
            continue
        content_val, previous_val, recorded = resolved
        message, to_stderr, is_error, sets_last_failed = _classify_entry(
            num, content_val, previous_val, recorded,
            grandfathered=grandfathered, reconciled=reconciled, last_failed=last_failed,
        )
        print(message, file=sys.stderr if to_stderr else None)
        if is_error:
            errors += 1
        if sets_last_failed:
            last_failed = num
    if skipped > 0:
        print(f"Skipped {skipped} entries with non-verifiable markup")

    # GH #361: the sequence-break tolerance must be gated the same way the
    # chain-math path already is (attestation, or a <=cutoff grandfathered
    # residual) -- NOT by bare duplicate-previous_hash membership. Tolerating
    # every duplicate-previous_hash member unconditionally disarms the one
    # check that could otherwise catch a ledger fork: two branches that each
    # honestly chain off the same predecessor are individually valid by
    # per-entry chain math, so sequence continuity is the only signal left.
    errors += _report_sequence(entries, reconciled | grandfathered)
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


def _declared_boundary(repo_root, ledger_md) -> int | None:
    """The operator's declared post-anchor boundary, or None.

    Phase 270: read through the one tolerant config reader, which never raises,
    so a missing file, unreadable path, invalid JSON or non-object section all
    read as "declared nothing" and compose with the fail-closed branch below
    rather than with a tolerated pass.

    `repo_root` is forwarded by callers that hold one. Callers that do not --
    and on the path CI runs, `seal_entry_check --auto` is one -- get an ancestor
    search from the ledger, so the declaration is found without every call site
    changing. The declaration must be COMMITTED: `.qorlogic/` is not gitignored,
    and a local-only config would pass on the operator's machine and fail in
    their CI, which is the worst available shape.
    """
    from qor.scripts import qorlogic_config

    roots = []
    if repo_root is not None:
        roots.append(Path(repo_root))
    else:
        here = Path(ledger_md).resolve().parent
        for candidate in [here, *here.parents]:
            roots.append(candidate)
            if (candidate / ".qorlogic").is_dir():
                break
    for root in roots:
        section = qorlogic_config.load_section(root, "ledger")
        value = section.get("post_anchor_boundary") if isinstance(section, dict) else None
        if isinstance(value, int) and value >= 0:
            return value
    return None


def _post_anchor_refusal(
    failing: list[int],
    breaks: list[str],
    duplicates: list[int],
    reasons: dict[int, tuple[str, bool]] | None = None,
) -> str:
    """The message printed when no boundary can be resolved on a damaged ledger.

    Phase 270: this is a contract, not a fit to a test. It names every condition
    it refuses over and the entries involved, because a refusal that does not
    name the fork is the support question this mode was already generating.

    It enumerates BY KIND deliberately. A scalar boundary cannot separate "I
    disclose these math failures" from "I disclose this fork", and an operator
    clearing a red gate will declare the lowest number producing a clean band --
    so a refusal that recommended a number without saying what it buries would
    replace automatic fork tolerance with fork tolerance the tool recommends.
    """
    lines = ["FAIL post-anchor: no boundary declared and the ledger is not clean."]
    reasons = reasons or {}
    for n in failing[:8]:
        # The ladder's own wording where it has one, so the refusal says WHY
        # rather than only which. A refusal that names a condition without
        # naming its kind is the support question this mode already generates.
        known = reasons.get(n)
        lines.append("  " + (known[0] if known else f"FAIL Entry #{n}: post-anchor verification failure"))
    if len(failing) > 8:
        lines.append(f"  ... and {len(failing) - 8} further entry failure(s)")
    for message in breaks[:8]:
        lines.append(f"  {message}")
    for n in duplicates:
        lines.append(f"  FAIL Entry #{n}: duplicate entry number (ledger fork)")
    candidates = list(failing) + duplicates
    for message in breaks:
        found = re.search(r"Entry #(\d+)", message)
        if found:
            candidates.append(int(found.group(1)))
    if candidates:
        recommended = max(candidates)
        would_bury = [n for n in duplicates if n <= recommended]
        lines.append(
            f"  Declaring post_anchor_boundary = {recommended} in .qorlogic/config.json "
            f'under "ledger" would disclose everything at or below it.'
        )
        if would_bury or breaks:
            lines.append(
                "  That declaration would ALSO disclose "
                + ", ".join(
                    part
                    for part in (
                        f"{len(would_bury)} duplicate entry number(s)" if would_bury else "",
                        f"{len(breaks)} linkage break(s)" if breaks else "",
                    )
                    if part
                )
                + " -- a fork is not the same as a math failure, and this "
                "declaration would not distinguish them."
            )
        lines.append("  Commit the declaration: a local-only config passes here and fails in CI.")
    return "\n".join(lines)


def verify_post_anchor(
    ledger_md: Path,
    boundary_entry: int | None = None,
    repo_root: Path | None = None,
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

    GH #363: an entry that names a Content/Previous/Chain Hash field but
    whose value matches none of the recognized hash forms (e.g. a
    hash-length value that is not hex) is classified ``fail`` rather than
    silently omitted from the post-anchor surface -- so a fabricated
    non-hex value at a post-boundary entry number is a hard error, not an
    invisible skip. An entry that names none of the three fields at all
    remains a tolerated pre-convention skip.
    """
    text = ledger_md.read_text(encoding="utf-8")
    entries = []
    parts = ENTRY_RE.split(text)
    for i in range(1, len(parts), 2):
        num = int(parts[i])
        body = parts[i + 1] if i + 1 < len(parts) else ""
        entries.append((num, body))

    # Phase 270: the same ladder verify() walks, not a subset of it.
    migration_attested = _migration_attested(entries)
    # `reconciled` is passed unconditionally, as verify() does. `grandfathered`
    # is NOT: verify() gates it behind tolerate_known_grandfathered, which the
    # CI invocation does not set, and a tolerated entry is a continuity RESET
    # rather than message suppression -- passing it here would suppress breaks
    # verify()'s default reports, reopening a weaker-than-verify gap inside the
    # phase that closes them.
    reconciled = _attested_reconciled(entries)
    markup_required_cutoff = _dialect.MARKUP_COMPAT_BOUNDARY

    # First pass: classify each entry as ok/fail without auto-anchor detection.
    classifications: list[tuple[int, str]] = []  # [(entry_num, "ok"|"fail")]
    ladder_messages: dict[int, tuple[str, bool]] = {}
    for num, body in entries:
        ch = CONTENT_HASH_RE.search(body)
        ph = PREV_HASH_RE.search(body)
        xh = CHAIN_HASH_RE.search(body)
        if not (ch and ph and xh):
            seal_only = SESSION_SEAL_RE.search(body) if not xh else None
            if not (ch and ph and seal_only):
                status, message, to_stderr = _dispose_unresolvable(
                    num, body, markup_required_cutoff, migration_attested
                )
                if status != "skip":
                    classifications.append((num, status))
                    ladder_messages[num] = (message, to_stderr)
                continue
            recorded = seal_only.group(1)
        else:
            recorded = _dialect.hash_value(xh)
        content_val = _dialect.hash_value(ch)
        previous_val = _dialect.hash_value(ph)
        if _find_placeholder_field(content_val, previous_val, recorded):
            classifications.append((num, "fail"))
            continue
        expected = chain_hash(content_val, previous_val)
        expected_legacy = legacy_chain_hash(content_val, previous_val)
        if expected == recorded or expected_legacy == recorded:
            classifications.append((num, "ok"))
        else:
            classifications.append((num, "fail"))

    # Phase 270 (GH #443, #425, #430): a boundary must be asserted by someone.
    # `max(ok_entries)` was derived from the very entries it judged, so ANY
    # failure was downgraded the moment something valid followed it -- the
    # one-entry detection window that let a fork print as a tolerated residual.
    failing = [n for (n, status) in classifications if status == "fail"]
    break_messages = _sequence_breaks(entries, reconciled)
    duplicates = _duplicate_entry_numbers(entries)
    boundary_pinned = boundary_entry is not None
    if boundary_entry is None:
        boundary_entry = _declared_boundary(repo_root, ledger_md)
        boundary_pinned = boundary_entry is not None
    if boundary_entry is None:
        # Auto-detection is permitted only when a strict evaluation would raise
        # nothing at all. Derived from the error count rather than a list of
        # failure kinds, so a kind added later is covered the day it is added.
        if failing or break_messages or duplicates:
            print(
                _post_anchor_refusal(failing, break_messages, duplicates, ladder_messages),
                file=sys.stderr,
            )
            return 1
        boundary_entry = max((n for n, _ in entries), default=0)

    errors = 0
    for num, status in classifications:
        ladder = ladder_messages.get(num)
        if status == "ok":
            # A ladder disposition carries its own wording (attested, etc.);
            # anything else verified by chain arithmetic.
            if ladder:
                print(ladder[0])
            else:
                print(f"OK Entry #{num}: chain hash verified (post-anchor)")
        elif num <= boundary_entry:
            print(f"DISCLOSED_PRE_ANCHOR Entry #{num}: tolerated pre-boundary failure")
        else:
            if ladder:
                print(ladder[0], file=sys.stderr if ladder[1] else None)
            else:
                print(
                    f"FAIL Entry #{num}: post-anchor verification failure",
                    file=sys.stderr,
                )
            errors += 1

    # Phase 270 (GH #425): a duplicate entry number is a fork, and the only
    # thing that can excuse one is an operator's assertion. The old rule was
    # `n >= boundary_entry` against a boundary that WAS max(ok_entries), so the
    # condition could hold only while the duplicated number was itself the
    # high-water mark -- a one-entry window in an append-only ledger. The
    # originating incident (two branches allocating #597, four entries landing
    # after) exited 0 through exactly that gap.
    for n in duplicates:
        if boundary_pinned and n <= boundary_entry:
            print(
                f"DISCLOSED_PRE_ANCHOR Entry #{n}: duplicate entry number "
                "tolerated (declared pre-boundary residual)"
            )
        else:
            print(
                f"FAIL Entry #{n}: duplicate entry number (ledger fork)",
                file=sys.stderr,
            )
            errors += 1

    # Phase 270 (GH #443): a linkage break is a property of an adjacent PAIR in
    # file order, so it is not collapsed onto one entry number. It is disclosed
    # only when BOTH members sit at or below an asserted boundary: a re-anchored
    # consumer whose pre-anchor history had an entry removed has such a break by
    # construction, and refusing it would make declaring worthless. A straddling
    # break means an entry was removed AT the re-anchor point, which is not
    # disclosed history. The canonical re-anchor shape produces no break at all,
    # because the re-anchor entry records the disclosed predecessor's own hash.
    for pair, message in _sequence_break_pairs(entries, reconciled):
        if boundary_pinned and max(pair) <= boundary_entry:
            print(f"DISCLOSED_PRE_ANCHOR {message}")
        else:
            print(message, file=sys.stderr)
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
