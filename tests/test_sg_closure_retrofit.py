"""Phase 212 (GH #305): every SG countermeasure cites an enforcer or declines.

The ten legacy numeric-ID entries predate the rule GH #249 introduced. Each now
either names something that fails when its pattern recurs, or records a
`cannot-automate:` decision with a reason.

The trap these tests exist to prevent: `tests/test_shadow_genome_doctrine.py`
references every SG ID, but it asserts the DOCTRINE MENTIONS them -- it does not
fail when a pattern recurs. Citing it would have silenced `sg_closure_lint`
without stopping anything, which is the "advisory shipped, enforcer deferred"
shape one level more deceptive.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-shadow-genome-countermeasures.md"

# A citation that would silence the lint without enforcing anything.
_NON_ENFORCING = "test_doctrine_lists_all_sg_ids"


def test_no_entry_lacks_an_enforcer_or_decision():
    """`sg_closure_lint` reports zero uncited entries over the live doctrine."""
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.sg_closure_lint"],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    uncited = [
        line for line in result.stdout.splitlines()
        if "no executable enforcer cited" in line
    ]
    assert not uncited, (
        "every countermeasure must cite an enforcer or record a "
        "cannot-automate decision:\n  " + "\n  ".join(uncited)
    )


def test_every_cited_enforcer_names_a_resolvable_target():
    """A citation must point at a file that exists, not at nothing."""
    text = DOCTRINE.read_text(encoding="utf-8")
    # Scope to ENFORCER lines only. "Cross-reference" and "Originating
    # recurrence" prose legitimately names artifacts belonging to other
    # workspaces or lints that were proposed and never built; those are not
    # claims that this repository enforces anything.
    enforcer_lines = [
        line for line in text.splitlines() if line.lstrip().startswith("**Enforcer**:")
    ]
    assert enforcer_lines, "expected the doctrine to carry enforcer citations"
    cited = {
        m for line in enforcer_lines
        for m in re.findall(r"`((?:tests|qor)/[\w./-]+\.py)", line)
    }
    assert cited, "expected enforcer citations to name paths"
    missing = sorted(c for c in cited if not (REPO_ROOT / c).is_file())
    assert not missing, f"cited enforcer paths do not exist: {missing}"


def test_cannot_automate_decisions_carry_a_reason():
    """The escape may not be used as a bare silencer."""
    text = DOCTRINE.read_text(encoding="utf-8")
    bare = []
    for match in re.finditer(r"cannot-automate:(.*)", text):
        if len(match.group(1).strip()) < 20:
            bare.append(match.group(0)[:60])
    assert not bare, f"cannot-automate decisions need a stated reason: {bare}"


def test_the_doctrine_presence_test_is_not_used_as_an_enforcer():
    """Guards the specific mis-citation this retrofit was at risk of making.

    `test_doctrine_lists_all_sg_ids` asserts each ID appears in the doctrine.
    It passes whether or not the pattern it names is ever caught, so it can
    never serve as an enforcer citation.
    """
    text = DOCTRINE.read_text(encoding="utf-8")
    assert _NON_ENFORCING not in text, (
        f"{_NON_ENFORCING!r} asserts doctrine presence, not enforcement; "
        "citing it would silence sg_closure_lint without stopping the pattern"
    )
