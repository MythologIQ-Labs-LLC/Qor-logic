"""Phase 75: substantiate-step prerequisite capability check.

Parses the ## Step Prerequisites table in qor-substantiate SKILL.md and
returns per-step CapabilityReport tuples indicating whether each step's
declared prerequisite is satisfied on the current host.

Predicate kinds recognized in V1:
- file:<path>      -> (repo_root / path).is_file()
- module:<dotted>  -> importlib.util.find_spec(dotted) is not None
- command:<binary> -> shutil.which(binary) is not None

Operator workflow:
    qor-logic substantiate-capability  # prints markdown table

Closes GH #38 V1 (Option 1 from issue body: skill capability declaration).
"""
from __future__ import annotations

import importlib.util
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


_TABLE_HEADER_RE = re.compile(r"^\|\s*Step\s*\|\s*Requires\s*\|\s*Notes\s*\|", re.MULTILINE)
_SEPARATOR_RE = re.compile(r"^\|[\s-]+\|[\s-]+\|[\s-]+\|", re.MULTILINE)


@dataclass(frozen=True)
class PrereqRow:
    step_id: str
    requires: str
    notes: str


@dataclass(frozen=True)
class CapabilityReport:
    step_id: str
    requires: str
    present: bool
    evidence: str


def parse_step_prerequisites(skill_md: Path) -> list[PrereqRow]:
    """Parse the Step Prerequisites markdown table from qor-substantiate SKILL.md."""
    text = skill_md.read_text(encoding="utf-8")
    if "## Step Prerequisites" not in text:
        return []
    start = text.index("## Step Prerequisites")
    next_h2 = text.find("\n## ", start + 5)
    section = text[start: next_h2 if next_h2 != -1 else len(text)]
    header_match = _TABLE_HEADER_RE.search(section)
    if not header_match:
        return []
    body_start = header_match.end()
    sep_match = _SEPARATOR_RE.search(section, body_start)
    if sep_match:
        body_start = sep_match.end()
    rows: list[PrereqRow] = []
    for line in section[body_start:].splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        step_id_raw, requires_raw, notes_raw = cells[0], cells[1], cells[2]
        if not step_id_raw or step_id_raw.lower() in {"step", "---"}:
            continue
        step_id_match = re.match(r"^([0-9]+(?:\.[0-9]+)*)", step_id_raw)
        if not step_id_match:
            continue
        rows.append(PrereqRow(
            step_id=step_id_match.group(1),
            requires=requires_raw,
            notes=notes_raw,
        ))
    return rows


def check_step(row: PrereqRow, repo_root: Path) -> CapabilityReport:
    """Run the predicate kind embedded in row.requires; return CapabilityReport."""
    requires = row.requires.strip()
    if ":" not in requires:
        return CapabilityReport(row.step_id, requires, False, "malformed: no predicate kind")
    kind, _, target = requires.partition(":")
    target = target.strip()
    if kind == "file":
        path = (repo_root / target).resolve()
        if path.is_file():
            return CapabilityReport(row.step_id, requires, True, str(path.relative_to(repo_root.resolve())) if path.is_relative_to(repo_root.resolve()) else str(path))
        return CapabilityReport(row.step_id, requires, False, f"file not found: {target}")
    if kind == "module":
        try:
            spec = importlib.util.find_spec(target)
        except (ImportError, ValueError):
            spec = None
        if spec is not None:
            origin = spec.origin or "(builtin / namespace)"
            return CapabilityReport(row.step_id, requires, True, origin)
        return CapabilityReport(row.step_id, requires, False, f"module not found: {target}")
    if kind == "command":
        path = shutil.which(target)
        if path:
            return CapabilityReport(row.step_id, requires, True, path)
        return CapabilityReport(row.step_id, requires, False, f"command not on PATH: {target}")
    return CapabilityReport(row.step_id, requires, False, f"unknown predicate kind: {kind}")


def collect_all_reports(skill_md: Path, repo_root: Path) -> list[CapabilityReport]:
    rows = parse_step_prerequisites(skill_md)
    return [check_step(r, repo_root) for r in rows]
