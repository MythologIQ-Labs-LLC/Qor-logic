"""Pre-audit lint: struct-field persistence-cascade completeness (Phase 110, #134).

Per ``qor/references/doctrine-shadow-genome-countermeasures.md``
SG-AffectedFilesContract-A (persistence sub-leaf). When a plan adds a field to a
struct that flows through a persistence layer (SQL schema, INSERT/SELECT,
FromRow derive), the persistence-layer update must appear in the plan's
``### Affected Files`` block or the field must be declared transient; otherwise
the value silently drops at the persistence boundary. WARN-only V1 (exit 0).
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from qor.scripts._lint_utils import _iter_sources

# (struct, field) capture. Pattern 1: struct then field. Pattern 2: field then struct.
_FIELD_ADD_STRUCT_FIRST = re.compile(
    r"widen\s+`(\w+)`\s+(?:struct\s+)?to\s+add\s+(?:field\s+)?`?(\w+)`?", re.IGNORECASE
)
_FIELD_ADD_FIELD_FIRST = re.compile(
    r"add\s+(?:a\s+)?(?:new\s+)?field\s+`(\w+)`\s+to\s+`?(\w+)`?", re.IGNORECASE
)
_AFFECTED_FILE_RE = re.compile(r"^[-*]\s+`([^`]+)`", re.MULTILINE)
_TRANSIENT_EXEMPT_RE = re.compile(r"<!--\s*transient-field:\s*(\w+)\.(\w+)\b")
_CREATE_TABLE_RE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"']?(\w+)[`\"']?\s*\((.*?)\)", re.IGNORECASE | re.DOTALL)
_CREATE_TABLE_BARE_RE = re.compile(r"CREATE\s+TABLE\b", re.IGNORECASE)
_FROMROW_RE = re.compile(r"FromRow")


@dataclass(frozen=True)
class LintWarning:
    struct: str
    field: str
    persistence_file: str
    reason: str


def _field_additions(text: str) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for m in _FIELD_ADD_STRUCT_FIRST.finditer(text):
        pairs.add((m.group(1), m.group(2)))
    for m in _FIELD_ADD_FIELD_FIRST.finditer(text):
        pairs.add((m.group(2), m.group(1)))
    return pairs


def _affected_paths(text: str) -> set[str]:
    return {m.group(1) for m in _AFFECTED_FILE_RE.finditer(text)}


def _exempt_pairs(text: str) -> set[tuple[str, str]]:
    return {(m.group(1), m.group(2)) for m in _TRANSIENT_EXEMPT_RE.finditer(text)}


def _is_transient_prose(text: str, field: str) -> bool:
    window = re.search(rf"`?{re.escape(field)}`?[^.\n]{{0,80}}(transient|in-memory-only)", text, re.IGNORECASE)
    return window is not None


def _schema_columns(repo_root: Path) -> tuple[set[str], bool]:
    """Return (all-column-names across parseable CREATE TABLE blocks, saw_unparseable)."""
    columns: set[str] = set()
    saw_unparseable = False
    for path in _iter_sources(repo_root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not _CREATE_TABLE_BARE_RE.search(text):
            continue
        matched = list(_CREATE_TABLE_RE.finditer(text))
        if not matched:
            saw_unparseable = True
            continue
        for m in matched:
            for col_line in m.group(2).split(","):
                tok = col_line.strip().split()
                if tok:
                    columns.add(tok[0].strip('`"\''))
    return columns, saw_unparseable


def _persistence_files(struct: str, repo_root: Path) -> set[str]:
    """Files that bind ``struct`` to persistence: a FromRow derive near the struct,
    or a CREATE TABLE block."""
    hits: set[str] = set()
    struct_re = re.compile(rf"\b{re.escape(struct)}\b")
    for path in _iter_sources(repo_root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _FROMROW_RE.search(text) and struct_re.search(text):
            hits.add(path.relative_to(repo_root).as_posix())
        elif _CREATE_TABLE_BARE_RE.search(text):
            hits.add(path.relative_to(repo_root).as_posix())
    return hits


def check_plan(plan_path: Path, repo_root: Path) -> list[LintWarning]:
    plan_path = Path(plan_path)
    repo_root = Path(repo_root)
    if not plan_path.exists():
        return []
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    affected = _affected_paths(text)
    exempt = _exempt_pairs(text)
    columns, saw_unparseable = _schema_columns(repo_root)
    warnings: list[LintWarning] = []
    for struct, field in sorted(_field_additions(text)):
        if (struct, field) in exempt or _is_transient_prose(text, field):
            continue
        persistence = _persistence_files(struct, repo_root)
        if not persistence:
            continue  # in-memory-only struct; no cascade
        if field in columns:
            continue  # schema already carries the field
        if saw_unparseable and not columns:
            print(f"skipping {struct}.{field}: CREATE TABLE present but column list not parseable", file=sys.stderr)
            continue
        for pfile in sorted(persistence):
            if pfile not in affected:
                warnings.append(LintWarning(struct, field, pfile, "persistence file not enumerated in Affected Files"))
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.plan_data_round_trip_lint")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    warnings = check_plan(args.plan, args.repo_root)
    for w in warnings:
        print(f"WARN [data-round-trip]: `{w.struct}.{w.field}` persistence file {w.persistence_file} not in Affected Files", file=sys.stderr)
    if warnings:
        print(f"{len(warnings)} persistence-cascade gap(s); see SG-AffectedFilesContract-A.", file=sys.stderr)
    return 0  # WARN-only V1


if __name__ == "__main__":
    raise SystemExit(main())
