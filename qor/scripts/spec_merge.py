"""Phase 190 (GH #239 Phase A): deterministic spec delta merge.

Folds a delta document (``## ADDED / MODIFIED / REMOVED Requirements``
sections) into a spec document. Heading-keyed whole-block replacement makes
the merge deterministic; the three ambiguity holes are loud errors (absent
MODIFIED/REMOVED target, duplicate ADDED heading) so concurrent deltas
conflict visibly instead of rotting the corpus.

Grammar contract: ``qor/references/spec-grammar.md``.

CLI:
    python -m qor.scripts.spec_merge --spec PATH --delta PATH [--write]
    Prints the merged document (or rewrites --spec with --write).
    Exit 0: merged. Exit 1: merge error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REQUIREMENT_RE = re.compile(r"^### Requirement:\s*(.+?)\s*$", re.MULTILINE)
_DELTA_SECTION_RE = re.compile(
    r"^## (ADDED|MODIFIED|REMOVED) Requirements\s*$", re.MULTILINE
)
_REMOVED_ITEM_RE = re.compile(r"^[-*]\s*(.+?)\s*$", re.MULTILINE)


class SpecMergeError(ValueError):
    """A delta names a requirement the merge cannot resolve unambiguously."""


def _split_blocks(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (preamble, ordered [(heading, complete_block)])."""
    matches = list(_REQUIREMENT_RE.finditer(text))
    if not matches:
        return text, []
    preamble = text[: matches[0].start()]
    blocks: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        blocks.append((match.group(1), text[match.start():end]))
    return preamble, blocks


def _delta_sections(delta_text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(_DELTA_SECTION_RE.finditer(delta_text))
    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(delta_text)
        sections[match.group(1)] = delta_text[match.end():end]
    return sections


def apply(spec_text: str, delta_text: str) -> str:
    """Fold a delta into a spec; deterministic, loud on ambiguity."""
    preamble, blocks = _split_blocks(spec_text)
    order = [h for h, _ in blocks]
    by_heading = dict(blocks)
    sections = _delta_sections(delta_text)

    for heading, block in _split_blocks(sections.get("MODIFIED", ""))[1]:
        if heading not in by_heading:
            raise SpecMergeError(
                f"MODIFIED names absent requirement: {heading!r}")
        by_heading[heading] = block

    for raw in _REMOVED_ITEM_RE.findall(sections.get("REMOVED", "")):
        if raw not in by_heading:
            raise SpecMergeError(f"REMOVED names absent requirement: {raw!r}")
        del by_heading[raw]
        order.remove(raw)

    for heading, block in _split_blocks(sections.get("ADDED", ""))[1]:
        if heading in by_heading:
            raise SpecMergeError(
                f"ADDED duplicates existing requirement: {heading!r}")
        by_heading[heading] = block
        order.append(heading)

    parts = [preamble.rstrip("\n")] if preamble.strip() else []
    parts.extend(by_heading[h].rstrip("\n") for h in order)
    return "\n\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.spec_merge")
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--delta", required=True, type=Path)
    parser.add_argument("--write", action="store_true",
                        help="rewrite --spec in place instead of printing")
    args = parser.parse_args(argv)

    try:
        merged = apply(
            args.spec.read_text(encoding="utf-8"),
            args.delta.read_text(encoding="utf-8"),
        )
    except (OSError, SpecMergeError) as exc:
        print(f"SPEC MERGE ERROR: {exc}", file=sys.stderr)
        return 1

    if args.write:
        args.spec.write_text(merged, encoding="utf-8")
    else:
        sys.stdout.write(merged)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
