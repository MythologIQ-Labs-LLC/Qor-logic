"""Phase 223 (GH #330): the doctrine and the shipped classification agree.

Iteration 3 of the plan proposed asserting that the P1 paragraph contained
certain wording. That could not fail on a behavior break -- the paragraph would
still say what it said while the lint classified differently (ledger #571 F11).

This parses the kind lists out of the amended paragraph, runs the CLI, and
asserts the two agree. A doctrine edit that drifts from the shipped
classification fails here; so does a code change that reclassifies a kind
without amending the doctrine.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-shadow-genome-countermeasures.md"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "evidence_false_line.md"

_TRUTH_RE = re.compile(r"truth-checked kinds?:\s*(?P<kinds>[^.\n]+)", re.IGNORECASE)
_PRESENCE_RE = re.compile(r"presence-only kinds?:\s*(?P<kinds>[^.\n]+)", re.IGNORECASE)


def _split(raw: str) -> set[str]:
    return {k.strip().strip("`") for k in raw.replace(" and ", ",").split(",") if k.strip()}


def _doctrine_kinds() -> tuple[set[str], set[str]]:
    body = DOCTRINE.read_text(encoding="utf-8")
    truth = _TRUTH_RE.search(body)
    presence = _PRESENCE_RE.search(body)
    assert truth, "doctrine does not name its truth-checked kinds"
    assert presence, "doctrine does not name its presence-only kinds"
    return _split(truth.group("kinds")), _split(presence.group("kinds"))


def _cli_kinds(tmp_path: Path) -> tuple[set[str], set[str]]:
    plan = tmp_path / "plan-doctrine-check.md"
    plan.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    out = subprocess.run(
        [sys.executable, "-m", "qor.scripts.plan_grep_lint",
         "--plan", str(plan), "--repo-root", str(REPO_ROOT)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    line = next(ln for ln in out.stderr.splitlines() if "truth-checked" in ln)
    truth = _split(re.search(r"\[([^\]]+)\]", line).group(1))
    presence = _split(re.findall(r"\[([^\]]+)\]", line)[1])
    return truth, presence


def test_the_lint_ceiling_matches_the_doctrine_kinds(tmp_path):
    """Behavioral on both sides: parsed doctrine against executed CLI output."""
    doc_truth, doc_presence = _doctrine_kinds()
    cli_truth, cli_presence = _cli_kinds(tmp_path)

    assert doc_truth == cli_truth, (
        f"doctrine names truth-checked {doc_truth}; the lint reports {cli_truth}"
    )
    assert doc_presence == cli_presence, (
        f"doctrine names presence-only {doc_presence}; the lint reports {cli_presence}"
    )


def test_the_two_kind_sets_are_disjoint_and_non_empty():
    """A kind in both lists, or an empty list, would make the agreement vacuous."""
    truth, presence = _doctrine_kinds()
    assert truth and presence
    assert truth.isdisjoint(presence)
