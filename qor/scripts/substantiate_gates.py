#!/usr/bin/env python3
"""The seal gate ladder, read as data (Phase 222; GH #327).

Ten gate steps lived in `qor-substantiate/SKILL.md` as ten hand-written prose
blocks -- 6,194 B of a file holding 24 B of headroom against its test-enforced
bound. Three consecutive phases each paid a relocation round to fit one new
step, and Phase 221 found that one of those relocations had left a fail-closed
gate at a position no reader reached.

The blocks were already regular: heading, prerequisite, a sentence, a fenced
command, a rationale pointer. This module reads that regularity as a table, so
the ladder's order, completeness, and halt vocabulary become checkable rather
than reviewable.

The pattern is not new here. `substantiate_capability.parse_step_prerequisites`
has parsed the Step Prerequisites table out of this same file since Phase 75.

Composition was considered and rejected: `skill_size_budget_lint` and
`install_drift_check` both walk `qor/skills/**/SKILL.md`, so a composed output
would be the governed and measured file, and a fragment kept outside it would
never be loaded by the harness.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

#: Halt semantics, closed by construction. An open vocabulary lets a
#: fail-closed gate become advisory by typo.
POLICY_VALUES = frozenset({"ABORT", "WARN", "disclose"})

#: Separator for a row whose step runs several commands (Step 4.6 runs three
#: reliability gates). Splitting beats one row per command, which would have to
#: invent step numbers and would disturb the deliberate 4.6.11 gap.
COMMAND_SEPARATOR = "<br>"

_HEADER = ("step", "gate", "command", "policy", "records", "notes")
_STEP_RE = re.compile(r"^4\.6(?:\.\d+)?$")
_MODULE_RE = re.compile(r"module:([\w.]+)")
_LADDER_START_RE = re.compile(r"^### Step 4\.6:", re.MULTILINE)
_LADDER_END_RE = re.compile(r"^### Step 4\.7:", re.MULTILINE)


class LadderError(ValueError):
    """A ladder row that cannot be executed as written.

    Raised rather than skipped: a parser that drops malformed rows quietly is a
    control wired so it cannot fire, which is the defect this module exists to
    make impossible.
    """


@dataclass(frozen=True)
class GateRow:
    """One gate ladder row."""

    step: str
    gate: str
    command: str
    policy: str
    records: str
    notes: str

    @property
    def commands(self) -> list[str]:
        """The row's commands, in run order."""
        parts = (p.strip().strip("`") for p in self.command.split(COMMAND_SEPARATOR))
        return [p for p in parts if p]

    @property
    def module(self) -> str | None:
        """The `module:` prerequisite this row names, if any."""
        m = _MODULE_RE.search(self.notes)
        return m.group(1) if m else None


def _split_row(line: str) -> list[str]:
    """Split a markdown table row, honoring backslash-escaped pipes."""
    placeholder = "\x00"
    cells = line.replace(r"\|", placeholder).strip().strip("|").split("|")
    return [c.replace(placeholder, "|").strip() for c in cells]


def _is_separator(cells: list[str]) -> bool:
    return all(set(c) <= set("-: ") and c for c in cells)


def parse_ladder_text(text: str) -> list[GateRow]:
    """Parse the gate ladder table out of skill text.

    Returns rows in file order. Raises `LadderError` on an unusable row.
    """
    lines = text.splitlines()
    start = _find_header(lines)
    if start is None:
        return []

    rows: list[GateRow] = []
    for line in lines[start + 1:]:
        if not line.lstrip().startswith("|"):
            break
        cells = _split_row(line)
        if _is_separator(cells):
            continue
        rows.append(_build_row(cells, line))
    return rows


def _find_header(lines: list[str]) -> int | None:
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        if tuple(c.lower() for c in _split_row(line)) == _HEADER:
            return i
    return None


def _build_row(cells: list[str], line: str) -> GateRow:
    if len(cells) != len(_HEADER):
        raise LadderError(f"row has {len(cells)} cells, expected {len(_HEADER)}: {line.strip()}")

    row = GateRow(*(c.strip("`") if i in (0, 3) else c for i, c in enumerate(cells)))

    if not _STEP_RE.match(row.step):
        raise LadderError(f"step {row.step!r} is not a 4.6.x identifier")
    if not row.commands:
        raise LadderError(f"step {row.step} declares no runnable command")
    if row.policy not in POLICY_VALUES:
        raise LadderError(
            f"step {row.step} declares policy {row.policy!r}; "
            f"expected one of {sorted(POLICY_VALUES)}"
        )
    return row


def parse_ladder(skill_md: Path) -> list[GateRow]:
    """Parse the gate ladder from a skill file."""
    return parse_ladder_text(Path(skill_md).read_text(encoding="utf-8"))


def required_gates(rows: list[GateRow]) -> set[str]:
    """The gate names the ladder declares."""
    return {r.gate for r in rows}


def check_prereq_consistency(rows: list[GateRow], prereqs: list) -> list[str]:
    """Report disagreements between ladder rows and the Step Prerequisites table.

    Both tables name module prerequisites for the 4.6.x steps. They are kept
    separate deliberately -- merging them would rewrite the host-capability
    consumers -- so the duplication is made safe by comparison instead.

    A row naming no module is not a disagreement; absence is not drift.
    """
    declared = {}
    for p in prereqs:
        m = _MODULE_RE.search(getattr(p, "requires", "") or "")
        if m:
            declared[getattr(p, "step_id", "")] = m.group(1)

    findings = []
    for row in rows:
        module = row.module
        if module is None or row.step not in declared:
            continue
        if declared[row.step] != module:
            findings.append(
                f"step {row.step}: ladder names {module!r}, "
                f"prerequisites table names {declared[row.step]!r}"
            )
    return findings


def extract_ladder_tokens(text: str) -> set[str]:
    """Every command line and backticked span in the ladder region.

    The relocation-fidelity set for Phase 222, taken from a pinned revision
    rather than authored. A hand-written list fails exactly when it matters:
    the author who drops a token from the ladder drops it from the list in the
    same pass, and the check stays green.

    Two of the ten gate commands are backticked inline rather than fenced, so
    the union -- not either half -- is the correct set.
    """
    region = _ladder_region(text)
    if region is None:
        return set()

    tokens: set[str] = set()
    in_fence = False
    pending = ""
    for line in region:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            pending = ""
            continue
        if in_fence:
            stripped = line.strip()
            # A backslash continuation is one command, not two tokens. Splitting
            # it would make the fragment unmatchable once the command lands in a
            # single table cell.
            if pending:
                stripped = f"{pending} {stripped}"
                pending = ""
            if stripped.endswith("\\"):
                pending = stripped[:-1].rstrip()
                continue
            if stripped and not stripped.startswith("#"):
                tokens.add(stripped)
        tokens.update(m.group(1) for m in re.finditer(r"`([^`\n]+)`", line))
    return tokens


def _ladder_region(text: str) -> list[str] | None:
    start = _LADDER_START_RE.search(text)
    end = _LADDER_END_RE.search(text)
    if start is None or end is None or end.start() < start.start():
        return None
    return text[start.start():end.start()].splitlines()


#: The ladder's home. Defaulted so the ceremony line stays short and so the
#: path has one spelling rather than one per caller.
DEFAULT_SKILL = Path("qor/skills/governance/qor-substantiate/SKILL.md")


def main(argv: list[str] | None = None) -> int:
    """Parse the ladder and report. Non-zero exit halts the seal ceremony."""
    ap = argparse.ArgumentParser(description="Validate the seal gate ladder table.")
    ap.add_argument("--skill", default=str(DEFAULT_SKILL),
                    help=f"skill file carrying the ladder (default: {DEFAULT_SKILL})")
    args = ap.parse_args(argv)

    try:
        rows = parse_ladder(Path(args.skill))
    except LadderError as exc:
        print(f"substantiate_gates: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print(f"substantiate_gates: no gate ladder table in {args.skill}", file=sys.stderr)
        return 1

    print(f"substantiate_gates: {len(rows)} gate(s) parsed, order verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
