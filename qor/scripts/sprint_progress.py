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


def sealed_phases(ledger_path: Path) -> set[int]:
    if not ledger_path.exists():
        return set()
    content = ledger_path.read_text(encoding="utf-8")
    return {int(m.group(1)) for m in _SEAL_RE.finditer(content)}


def compute_progress(repo_root: Path) -> tuple[Path | None, list[ProgressEntry]]:
    brief = _latest_brief(repo_root)
    if brief is None:
        return None, []
    priorities = parse_priorities(brief)
    sealed = sealed_phases(repo_root / "docs" / "META_LEDGER.md")
    entries = [ProgressEntry(priority=p, sealed=p.phase in sealed) for p in priorities]
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
