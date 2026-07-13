"""Phase 190 (GH #239 Phase A): behavioral spec grammar lint.

Validates per-capability spec files against the grammar contract in
``qor/references/spec-grammar.md``: ``### Requirement:`` headings carrying
exactly one RFC-2119 SHALL/MUST statement and at least one nested
``#### Scenario:`` in GIVEN/WHEN/THEN bullets.

CLI:
    python -m qor.scripts.spec_lint --files PATH [PATH ...]
    Exit 0: clean. Exit 1: at least one finding.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_REQUIREMENT_RE = re.compile(r"^### Requirement:\s*(.+?)\s*$", re.MULTILINE)
_SCENARIO_RE = re.compile(r"^#### Scenario:\s*(.+?)\s*$", re.MULTILINE)
_RFC2119_RE = re.compile(r"\b(?:SHALL|MUST)\b")
_BULLET_RE = re.compile(r"^[-*]\s*(GIVEN|WHEN|THEN)\b", re.IGNORECASE | re.MULTILINE)


@dataclass(frozen=True)
class Finding:
    line: int
    code: str
    message: str


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def check(text: str, strict: bool = True) -> list[Finding]:
    """Return grammar findings for a spec document (empty list = clean)."""
    findings: list[Finding] = []
    matches = list(_REQUIREMENT_RE.finditer(text))
    for idx, match in enumerate(matches):
        name = match.group(1)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end]
        line = _line_of(text, match.start())

        scenario_starts = list(_SCENARIO_RE.finditer(body))
        prose = body[: scenario_starts[0].start()] if scenario_starts else body
        rfc_count = len(_RFC2119_RE.findall(prose))
        if rfc_count == 0:
            findings.append(Finding(line, "missing-rfc2119",
                                    f"requirement '{name}' has no SHALL/MUST statement"))
        elif rfc_count > 1:
            findings.append(Finding(line, "double-rfc2119",
                                    f"requirement '{name}' has {rfc_count} SHALL/MUST statements; exactly one required"))

        if not scenario_starts:
            findings.append(Finding(line, "missing-scenario",
                                    f"requirement '{name}' has no Scenario"))
            continue
        for s_idx, s_match in enumerate(scenario_starts):
            s_end = (scenario_starts[s_idx + 1].start()
                     if s_idx + 1 < len(scenario_starts) else len(body))
            s_body = body[s_match.end():s_end]
            keywords = {m.group(1).upper() for m in _BULLET_RE.finditer(s_body)}
            missing = [k for k in ("GIVEN", "WHEN", "THEN") if k not in keywords]
            if missing:
                findings.append(Finding(
                    _line_of(text, start + s_match.start()), "malformed-scenario",
                    f"scenario '{s_match.group(1)}' in requirement '{name}' "
                    f"lacks bullets: {', '.join(missing)}"))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.spec_lint")
    parser.add_argument("--files", nargs="+", required=True, type=Path)
    args = parser.parse_args(argv)

    total = 0
    for path in args.files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        for f in check(text):
            total += 1
            print(f"SPEC LINT [{f.code}] {path}:{f.line}: {f.message}", file=sys.stderr)
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
