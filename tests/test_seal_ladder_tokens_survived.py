"""Phase 222 (GH #327): the rewrite relocated the ladder; it did not rewrite it.

The distinction is the whole risk. Collapsing ten prose blocks into a table is a
relocation only if every command, field name, escape, and pattern ID that was
load-bearing before is still readable after. Otherwise it is a rewrite wearing a
relocation's justification.

The token set is EXTRACTED from a pinned pre-rewrite revision, never enumerated
here. A hand-written list fails exactly when it matters: the author who drops a
token from the ladder drops it from the list in the same pass, and the check
stays green. Entry #561 recorded the rule -- a test that greps for a literal must
not be the reason the grep matches -- and Phase 221 honored it by constructing
the headroom bound from its factors rather than writing the product, which
`test_headroom_constant_single_source` enforces across every test file
(including, correctly, this one).

Tokens may land in the ladder table or in `references/seal-gate-ladder.md`.
Rationale pointers legitimately relocate to the reference file; requiring them in
a table cell would force either a false assertion or a padded table.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from qor.scripts import substantiate_gates as sg

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate"
SEAL_SKILL = SKILL_DIR / "SKILL.md"
LADDER_REF = SKILL_DIR / "references" / "seal-gate-ladder.md"

BASELINE_REV = "6424413"


def _baseline_text() -> str:
    out = subprocess.run(
        ["git", "show", f"{BASELINE_REV}:qor/skills/governance/qor-substantiate/SKILL.md"],
        cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode != 0:
        pytest.skip(f"baseline revision {BASELINE_REV} unreachable (shallow clone?)")
    return out.stdout


def _destination_text() -> str:
    """The two files Phase 2 writes, plus the ladder's commands as parsed.

    A markdown table escapes `|` as `\\|`, so a shell command containing `||`
    is present in the cell but not raw-matchable against the pre-rewrite form.
    Parsing unescapes it; comparing against the parsed command is comparing
    against what the ceremony will actually run, which is the stronger check.
    """
    parsed = "\n".join(c for row in sg.parse_ladder(SEAL_SKILL) for c in row.commands)
    return "\n".join((
        SEAL_SKILL.read_text(encoding="utf-8"),
        LADDER_REF.read_text(encoding="utf-8"),
        parsed,
    ))


def _missing(destination: str) -> list[str]:
    return sorted(t for t in sg.extract_ladder_tokens(_baseline_text()) if t not in destination)


def test_every_baseline_token_survives_the_rewrite():
    missing = _missing(_destination_text())
    assert missing == [], (
        f"{len(missing)} token(s) lost in the rewrite; a relocation that drops a "
        f"token is a rewrite:\n  " + "\n  ".join(missing)
    )


def test_the_survival_check_can_fail():
    """THE COUNTERFACTUAL.

    Without it the survival assertion would hold over an empty token set, and an
    extractor that silently returned nothing would certify any rewrite at all.
    """
    gutted = _destination_text().replace(
        "qor-logic scripts merge_velocity_check --repo-root . --window-days 7", ""
    )
    missing = _missing(gutted)
    assert missing, "removing a gate command must be reported as a lost token"


def test_the_baseline_token_set_is_not_empty():
    assert len(sg.extract_ladder_tokens(_baseline_text())) > 40
