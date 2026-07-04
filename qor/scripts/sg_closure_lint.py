"""WARN-only lint: every SG countermeasure entry must cite an executable enforcer.

Phase 166 (GH #249): prose codification went 0-for-4 against SG-038 recurrence;
only executable checks have stuck. This lint walks the ``## SG-`` entries in
the countermeasure doctrine and flags any entry whose body cites neither a
test path, a qor module, a gate-step reference, nor an explicit
``cannot-automate`` decision. Exit 1 when findings exist (the audit Step 0.6
ladder wraps ``|| true``; a V2 phase removes the wrap). The finding list is
the standing backfill worklist.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_DEFAULT_DOCTRINE = Path("qor/references/doctrine-shadow-genome-countermeasures.md")

_ENTRY_RE = re.compile(r"^## (SG-[^\s(]+)", re.MULTILINE)

_ENFORCER_PATTERNS = (
    re.compile(r"tests/test_[a-z0-9_]+\.py"),
    re.compile(r"\bqor\.(scripts|reliability)\.[a-z0-9_]+"),
    re.compile(r"\bqor/(scripts|reliability)/[a-z0-9_]+\.py"),
    re.compile(r"/qor-[a-z-]+[^\n]{0,40}Step\s+[0-9]"),
    re.compile(r"\bqor-logic\s+(scripts|reliability)\s+[a-z0-9_]+"),
    re.compile(r"\bcannot-automate\b", re.IGNORECASE),
    re.compile(r"schema\.json"),
)


def parse_entries(text: str) -> list[tuple[str, str]]:
    """Split doctrine text into (entry_name, body) pairs on '## SG-' headers."""
    matches = list(_ENTRY_RE.finditer(text))
    entries: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        entries.append((m.group(1).rstrip(":"), text[m.start():end]))
    return entries


def entry_cites_enforcer(body: str) -> bool:
    return any(p.search(body) for p in _ENFORCER_PATTERNS)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doctrine", type=Path, default=_DEFAULT_DOCTRINE)
    args = ap.parse_args(argv)
    text = args.doctrine.read_text(encoding="utf-8")
    entries = parse_entries(text)
    findings = [name for name, body in entries if not entry_cites_enforcer(body)]
    for name in findings:
        print(f"WARN [sg-closure] {name}: no executable enforcer cited "
              f"(add a test/module/gate citation or a 'cannot-automate:' decision)")
    print(f"sg_closure_lint: {len(entries)} entries, {len(findings)} without enforcer citation")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
