"""Phase 222 (GH #327): the parser runs in the ceremony, not only in CI.

Iteration 1 of the plan claimed `substantiate_gates` was consumed by the seal
ceremony and built no such consumer; ledger #565 VETOed it as
`specification-drift`. A module whose only consumer is its own tests is
`SG-InertControl-A` -- a control that exists, is correct, and cannot fire where
it matters.

The remedy is one line in the ladder preamble. These tests hold it there.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qor.scripts import substantiate_gates as sg

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
SEAL_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"


def test_ceremony_parses_the_ladder_before_executing_it():
    """Position, not presence.

    A validation that runs after the gates it validates is not a validation.
    The invocation must precede the table it checks.
    """
    body = SEAL_SKILL.read_text(encoding="utf-8")

    invocation = body.find("qor-logic scripts substantiate_gates")
    table_header = body.find("| Step | Gate | Command | Policy | Records | Notes |")

    assert invocation != -1, "the ceremony never invokes substantiate_gates"
    assert table_header != -1, "no gate ladder table found"
    assert invocation < table_header, (
        "substantiate_gates is invoked after the table it validates; a check "
        "that runs downstream of its subject cannot halt anything"
    )


def test_the_ceremony_invocation_is_fail_closed():
    """A parse failure must halt the seal, not warn."""
    body = SEAL_SKILL.read_text(encoding="utf-8")
    start = body.find("qor-logic scripts substantiate_gates")
    line = body[start:body.find("\n", start)]
    assert "|| ABORT" in line, f"invocation is not fail-closed: {line!r}"


def test_a_malformed_table_fails_the_ceremony_entry_point():
    """The wired command must actually be able to halt a seal."""
    out = subprocess.run(
        [sys.executable, "-m", "qor.scripts.substantiate_gates",
         "--skill", str(FIXTURES / "seal_ladder_malformed.md")],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert out.returncode != 0


def test_the_default_skill_path_resolves_to_the_real_ladder():
    """The ceremony line omits --skill; the default must find the ladder.

    A default pointing at a non-existent path would make the ceremony
    invocation fail for the wrong reason, or -- worse, if the parser tolerated
    it -- pass while checking nothing.
    """
    assert (REPO_ROOT / sg.DEFAULT_SKILL).resolve() == SEAL_SKILL.resolve()
    assert sg.parse_ladder(REPO_ROOT / sg.DEFAULT_SKILL)
