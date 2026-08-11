"""Phase 221: the headroom bound must have exactly one definition.

`HEADROOM_BYTES = 39 * 1024` is canonical, documented, and parametrized over both
governance skills. Three test files hardcoded the literal instead -- all three
added by the author in Phases 217, 219, and 220, each while wiring a step into
the constrained file under size pressure.

Tuning the constant would have left three copies silently disagreeing. This is
`SG-SingleEntryPointGuard-A` in its simplest form: a value bound to a name in one
place and to a literal in three others.
"""
from __future__ import annotations

from pathlib import Path

from tests.test_substantiate_staging_gates import HEADROOM_BYTES

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS = REPO_ROOT / "tests"
CANONICAL = TESTS / "test_substantiate_staging_gates.py"

# Built, not written: a test that greps for a literal must not be the reason the
# grep matches. An exclusion list would work and is one more thing to forget.
_LITERAL = str(39 * 1024)


def test_headroom_constant_is_the_documented_bound():
    """The canonical value is what the seal ceremony is actually held to."""
    assert HEADROOM_BYTES == 39 * 1024
    assert HEADROOM_BYTES < 40_000, "must stay under the EXCEEDED ceiling"


def test_no_hardcoded_headroom_literals():
    """THE COUNTERFACTUAL. Fails at HEAD with three occurrences."""
    offenders = []
    for path in sorted(TESTS.glob("*.py")):
        if path == CANONICAL or path.name == Path(__file__).name:
            continue
        if _LITERAL in path.read_text(encoding="utf-8"):
            offenders.append(path.name)

    assert offenders == [], (
        f"{offenders} hardcode the headroom bound; import HEADROOM_BYTES so "
        "tuning it changes the bound everywhere"
    )


def test_canonical_definition_still_exists():
    """Guards against the offenders being fixed by deleting the source.

    Without this, removing HEADROOM_BYTES entirely would make the sweep pass.
    """
    assert "HEADROOM_BYTES" in CANONICAL.read_text(encoding="utf-8")
