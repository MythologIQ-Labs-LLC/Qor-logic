"""Sprint-progress dashboard (Phase 54).

Reads the latest research brief in ``docs/research-brief-*.md``, parses
its Recommendations section for Priority numbers, walks
``docs/META_LEDGER.md`` for SESSION SEAL entries citing each Priority by
phase number, and emits a sprint-progress table.

Useful for operator visibility into multi-phase compliance work and as
audit-readable narrative for external reviewers.

Per ``qor/references/doctrine-ai-rmf.md``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_PRIORITY_RE = re.compile(
    r"###\s+Priority\s+(\d+)\s*[—\-]\s*Phase\s+(\d+)\s+candidate(?:\s*\([^)]*\))?:\s*(.+)$",
    re.MULTILINE,
)
_SEAL_RE = re.compile(
    r"^### Entry #\d+:\s*SESSION SEAL\s*--\s*Phase\s+(\d+)\s",
    re.MULTILINE,
)
# Phase 55: recognize bundled-priority declarations in brief body.
# Matches forms like "folded into Phase 53" or "bundled into Phase 54" within
# a Priority's body paragraph (after the heading line).
_BUNDLED_RE = re.compile(
    r"\b(?:folded|bundled)\s+into\s+Phase\s+(\d+)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Priority:
    number: int
    phase: int
    title: str


@dataclass(frozen=True)
class ProgressEntry:
    priority: Priority
    sealed: bool


_DATE_SUFFIX_RE = re.compile(r"(\d{4}-\d{2}-\d{2})\.md$")


def _latest_brief(repo_root: Path) -> Path | None:
    candidates = list((repo_root / "docs").glob("research-brief-*.md"))
    if not candidates:
        return None

    def sort_key(path: Path) -> tuple:
        match = _DATE_SUFFIX_RE.search(path.name)
        date_str = match.group(1) if match else "0000-00-00"
        return (date_str, path.name)

    return sorted(candidates, key=sort_key)[-1]


def parse_priorities(brief_path: Path) -> list[Priority]:
    content = brief_path.read_text(encoding="utf-8")
    return [
        Priority(number=int(m.group(1)), phase=int(m.group(2)), title=m.group(3).strip())
        for m in _PRIORITY_RE.finditer(content)
    ]


def _bundled_phase_for_priority(content: str, priority_heading: str) -> int | None:
    """Phase 55: scan the body following a priority heading for "folded into Phase NN"."""
    idx = content.find(priority_heading)
    if idx == -1:
        return None
    body_start = idx + len(priority_heading)
    next_heading = content.find("\n### ", body_start)
    body = content[body_start:next_heading] if next_heading != -1 else content[body_start:]
    match = _BUNDLED_RE.search(body)
    return int(match.group(1)) if match else None


def sealed_phases(ledger_path: Path) -> set[int]:
    if not ledger_path.exists():
        return set()
    content = ledger_path.read_text(encoding="utf-8")
    return {int(m.group(1)) for m in _SEAL_RE.finditer(content)}


_BUNDLES_RE = re.compile(
    r"\bBundle[sd]?\s+Priorit(?:y|ies)\s+([\d,\s]+(?:and\s+\d+)?)",
    re.IGNORECASE,
)
_PRIORITY_INDIVIDUAL_RE = re.compile(r"\bPriority\s+(\d+)\b", re.IGNORECASE)
_NUMBER_RE = re.compile(r"\d+")


def sealed_priorities_from_ledger(ledger_path: Path) -> set[int]:
    """Phase 55: extract Priority numbers cited within SESSION SEAL entries.

    A Priority is considered sealed if it appears inside any SESSION SEAL
    entry body. Strategy: locate every sentence mentioning "Priorit(y|ies)"
    inside a seal entry, then extract all digits from that sentence. Handles
    multi-priority bundles like "Bundles Priorities 2 (..), 4 (..), and 5".
    """
    if not ledger_path.exists():
        return set()
    content = ledger_path.read_text(encoding="utf-8")
    sealed: set[int] = set()
    for seal_match in re.finditer(
        r"^### Entry #\d+:\s*SESSION SEAL.*?(?=\n### Entry #\d+:|\Z)",
        content, re.MULTILINE | re.DOTALL,
    ):
        body = seal_match.group(0)
        # Split into sentence-ish chunks; capture sentences mentioning Priorit(y|ies).
        for sentence in re.split(r"(?<=[.!?])\s+", body):
            if not re.search(r"\bPriorit(?:y|ies)\b", sentence, re.IGNORECASE):
                continue
            # Within the sentence, extract numbers cited near Priority mentions.
            # Heuristic: numbers within 60 chars of a Priorit token are sealed.
            for prio_match in re.finditer(r"\bPriorit(?:y|ies)\b", sentence, re.IGNORECASE):
                window = sentence[prio_match.start():prio_match.start() + 200]
                for num in _NUMBER_RE.finditer(window):
                    n = int(num.group(0))
                    if 1 <= n <= 99:  # plausible priority numbers
                        sealed.add(n)
    return sealed


def compute_progress(repo_root: Path) -> tuple[Path | None, list[ProgressEntry]]:
    brief = _latest_brief(repo_root)
    if brief is None:
        return None, []
    priorities = parse_priorities(brief)
    ledger = repo_root / "docs" / "META_LEDGER.md"
    sealed = sealed_phases(ledger)
    sealed_priorities = sealed_priorities_from_ledger(ledger)
    content = brief.read_text(encoding="utf-8")

    entries: list[ProgressEntry] = []
    for p in priorities:
        if p.phase in sealed:
            entries.append(ProgressEntry(priority=p, sealed=True))
            continue
        if p.number in sealed_priorities:
            entries.append(ProgressEntry(priority=p, sealed=True))
            continue
        heading_match = re.search(
            rf"###\s+Priority\s+{p.number}\b[^\n]*",
            content,
        )
        bundled = (
            _bundled_phase_for_priority(content, heading_match.group(0))
            if heading_match else None
        )
        sealed_via_bundle = bundled is not None and bundled in sealed
        entries.append(ProgressEntry(priority=p, sealed=sealed_via_bundle))
    return brief, entries


def render_progress(repo_root: Path) -> str:
    brief, entries = compute_progress(repo_root)
    if brief is None:
        return "No research brief found in docs/research-brief-*.md (no sprint in progress)."
    if not entries:
        return f"Brief: {brief.name}\nNo Priority recommendations parsed."
    lines = [f"Sprint progress (brief: {brief.name}):"]
    sealed_count = sum(1 for e in entries if e.sealed)
    for entry in entries:
        status = "SEALED" if entry.sealed else "PENDING"
        lines.append(
            f"  Priority {entry.priority.number} (Phase {entry.priority.phase}): {status} -- {entry.priority.title}"
        )
    lines.append(f"\nProgress: {sealed_count}/{len(entries)} priorities sealed.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="qor.scripts.sprint_progress")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    repo_root = args.repo_root or Path.cwd()
    print(render_progress(repo_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
