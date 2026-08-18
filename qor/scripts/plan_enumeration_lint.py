"""Pre-audit lint: asserted-completeness enumerations (Phase 232; GH #349).

Two same-day VETOs (ledger #593, #611) asserted exhaustive countable
inventories the artifact surface contradicted, while every citation-truth
check passed -- the citations were true, the enumeration around them was not.
SG-AssertedCompleteness-A's countermeasure: a claimed count is a citation and
gets checked like one.

Form A (any paragraph): a count within two tokens of the plural noun ``tests``,
co-occurring with a ``tests/...py`` path and a commit-ish token -- resolved via
``git show`` and compared against the ``def test_`` count.
Form B (Locked-Decision regions only): a count within two tokens of a sites
noun, compared against the paragraph's distinct ``file:line`` citations plus
comma-separated shorthand continuations (the repo's ``:237``, ``:262``
convention; and-separated tokens deliberately excluded -- audit O2). A zero
derived count skips as unverifiable. WARN-only per SG-PreAuditLintGap-A.

Known limitation (audit O3): a TRUE count whose referent spans more than the
paragraph's one resolvable file warns -- subset counts, multi-file totals, and
suite-wide counts read as mismatches. The warn prompts exactly the completion
check the audit wants; the posture is advisory.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from qor.scripts.plan_evidence import _FILE_LINE_RE, _ld_blocks

_WORDS = {w: i + 1 for i, w in enumerate(
    "one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
_COUNT = r"(\d{1,3}|" + "|".join(_WORDS) + r")"
#: count, up to two modifier tokens, then the trigger noun.
_FORM_A_RE = re.compile(_COUNT + r"\s+(?:[\w-]+\s+){0,2}tests\b", re.IGNORECASE)
_FORM_B_RE = re.compile(_COUNT + r"\s+(?:[\w-]+\s+){0,2}(?:call\s+sites|unpack\s+sites|sites)\b", re.IGNORECASE)
_TEST_PATH_RE = re.compile(r"\btests/[\w/]+\.py\b")
_COMMITISH_RE = re.compile(r"\b(?:[0-9a-f]{7,40}|v\d+(?:\.\d+)+)\b")
#: comma-separated shorthand continuation of the preceding full citation.
_CONTINUATION_RE = re.compile(r",\s*`?:\d+`?")


@dataclass(frozen=True)
class Finding:
    plan: str
    line: int
    form: str
    claimed: int
    derived: int


def _to_int(token: str) -> int:
    return int(token) if token.isdigit() else _WORDS[token.lower()]


def _paragraphs(text: str, start_line: int = 1):
    line = start_line
    for para in re.split(r"\n\s*\n", text):
        yield line, para
        line += para.count("\n") + 2


def _derived_test_count(token: str, path: str, repo_root: Path) -> int | None:
    completed = subprocess.run(
        ["git", "show", f"{token}:{path}"],
        cwd=repo_root, capture_output=True, text=True, encoding="utf-8",
    )
    if completed.returncode != 0:
        return None
    return sum(1 for ln in completed.stdout.splitlines() if ln.startswith("def test_"))


def _check_form_a(text: str, plan: str, repo_root: Path) -> list[Finding]:
    findings = []
    for line, para in _paragraphs(text):
        count_m = _FORM_A_RE.search(para)
        path_m = _TEST_PATH_RE.search(para)
        if not count_m or not path_m:
            continue
        token_m = _COMMITISH_RE.search(para.replace(path_m.group(0), ""))
        if not token_m:
            continue
        derived = _derived_test_count(token_m.group(0), path_m.group(0), repo_root)
        if derived is None:  # unresolvable is unverifiable, not wrong
            continue
        claimed = _to_int(count_m.group(1))
        if claimed != derived:
            findings.append(Finding(plan, line, "tests-vs-artifact", claimed, derived))
    return findings


def _check_form_b(text: str, plan: str) -> list[Finding]:
    findings = []
    for block_line, block in _ld_blocks(text):
        for offset, para in _paragraphs(block, block_line):
            count_m = _FORM_B_RE.search(para)
            if not count_m:
                continue
            full = {m.group(0) for m in _FILE_LINE_RE.finditer(para)}
            derived = len(full) + len(_CONTINUATION_RE.findall(para))
            if derived == 0:  # enumeration-free claims are unverifiable
                continue
            claimed = _to_int(count_m.group(1))
            if claimed != derived:
                findings.append(Finding(plan, offset, "sites-vs-enumeration", claimed, derived))
    return findings


def check_plan_text(text: str, plan: str = "<plan>", repo_root: Path | None = None) -> list[Finding]:
    root = repo_root or Path.cwd()
    return _check_form_a(text, plan, root) + _check_form_b(text, plan)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.plan_enumeration_lint")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    if not args.plan.is_file():
        return 0
    text = args.plan.read_text(encoding="utf-8", errors="replace")
    findings = check_plan_text(text, plan=str(args.plan), repo_root=args.repo_root)
    for f in findings:
        print(
            f"WARN [plan-enumeration-lint] {f.plan}:{f.line} [{f.form}] "
            f"claimed {f.claimed}, derived {f.derived}",
            file=sys.stderr,
        )
    if findings:
        print(
            f"\n{len(findings)} asserted-completeness mismatch(es); re-derive each "
            f"count from the artifact it claims (SG-AssertedCompleteness-A).",
            file=sys.stderr,
        )
    return 0  # WARN-only; 1 reserved for a future enforce flag


if __name__ == "__main__":
    raise SystemExit(main())
