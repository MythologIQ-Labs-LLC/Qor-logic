"""Per-feature TDD mechanical lint (Phase 130; GH #159 / #41 V2).

Plan-text lint over a plan's `## Feature Inventory Touches` block. For each row
whose `operation` is NEW or MODIFIED (a src-touching feature), require a
failing-test-first declaration: a real `test_path` (not n/a) and a behavioral
`test_descriptor` (not presence-only). Also flags a plan that touches `src/` in
its Affected Files while declaring no Feature Inventory Touches block.

WARN-only at `/qor-audit` Step 0.6; the binding VETO remains the Step 3 Feature
Test Coverage Pass. Enforces the plan-time half of `doctrine-feature-tdd.md`.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

KNOWN_FINDING_KINDS = (
    "missing-failing-test", "presence-only-feature-test", "undeclared-feature-tdd",
)
_FIT_HEADING_RE = re.compile(r"^#+\s*Feature Inventory Touches\s*$", re.IGNORECASE | re.MULTILINE)
_ANY_HEADING_RE = re.compile(r"^#+\s", re.MULTILINE)
_SRC_AFFECTED_RE = re.compile(r"^[-*]\s+`(src/[^`]+)`", re.MULTILINE)
_PRESENCE_ONLY_RE = re.compile(
    r"\b(exists|is defined|appears in|present|defined|has a row|method defined)\b",
    re.IGNORECASE,
)
_FIELD_RES = {
    "entry_id": re.compile(r"entry_id:\s*`([^`]+)`"),
    "operation": re.compile(r"operation:\s*`([^`]+)`"),
    "test_path": re.compile(r"test_path:\s*`([^`]+)`"),
    "test_descriptor": re.compile(r"test_descriptor:\s*`(.+?)`\s*$"),
}


@dataclass(frozen=True)
class FeatureTddFinding:
    kind: str
    entry_id: str
    detail: str


def _fit_section(text: str) -> str | None:
    m = _FIT_HEADING_RE.search(text)
    if not m:
        return None
    rest = text[m.end():]
    nxt = _ANY_HEADING_RE.search(rest)
    return rest[:nxt.start()] if nxt else rest


def parse_fit_rows(plan_text: str) -> list[dict]:
    section = _fit_section(plan_text)
    if section is None:
        return []
    rows: list[dict] = []
    for line in section.splitlines():
        if "entry_id:" not in line:
            continue
        row = {}
        for key, rx in _FIELD_RES.items():
            mm = rx.search(line)
            row[key] = mm.group(1).strip() if mm else ""
        rows.append(row)
    return rows


def _is_missing(value: str) -> bool:
    return value == "" or value.lower() in ("n/a", "na", "none", "tbd")


def check_feature_tdd(plan_text: str) -> list[FeatureTddFinding]:
    findings: list[FeatureTddFinding] = []
    rows = parse_fit_rows(plan_text)
    has_fit_heading = _FIT_HEADING_RE.search(plan_text) is not None

    for row in rows:
        op = row.get("operation", "").lower()
        if op not in ("new", "modified"):
            continue  # n/a-justified and others are exempt
        entry = row.get("entry_id", "?")
        if _is_missing(row.get("test_path", "")):
            findings.append(FeatureTddFinding(
                "missing-failing-test", entry,
                f"{op.upper()} feature row declares no test_path (failing-test-first required)",
            ))
            continue
        desc = row.get("test_descriptor", "")
        if not desc or _PRESENCE_ONLY_RE.search(desc):
            findings.append(FeatureTddFinding(
                "presence-only-feature-test", entry,
                f"{op.upper()} feature row test_descriptor is presence-only / empty: {desc!r}",
            ))

    if not has_fit_heading and _SRC_AFFECTED_RE.search(plan_text):
        findings.append(FeatureTddFinding(
            "undeclared-feature-tdd", "n/a",
            "plan touches src/ in Affected Files but declares no Feature Inventory Touches block",
        ))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="plan_feature_tdd_lint")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)

    path = Path(args.plan)
    if not path.exists():
        print(f"plan_feature_tdd_lint: no such file: {path}")
        return 0
    findings = check_feature_tdd(path.read_text(encoding="utf-8"))
    if not findings:
        return 0
    for f in findings:
        print(f"[{f.kind}] {f.entry_id}: {f.detail}")
    print(f"plan_feature_tdd_lint: {len(findings)} finding(s)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
