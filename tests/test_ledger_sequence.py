"""Phase 218 (GH #316): the ledger must notice a deleted entry.

`verify` checks each entry's internal arithmetic -- `chain_hash` recomputed from
that entry's own `content_hash` and `previous_hash`. Tampering with
`previous_hash` therefore fails, because the recorded chain hash no longer
matches.

Deletion does not fail. Every surviving entry stays internally consistent, and
nothing asserts that entry N's `previous_hash` is the chain hash *produced by*
the entry preceding it. Excising a middle entry leaves a ledger that verifies
clean.

The assertion is over FILE order, not entry numbers: this repository's ledger
has real numbering gaps (510, 532) whose links are intact, so a number-keyed
check would red-light its own history.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

from qor.scripts import ledger_hash

REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_LEDGER = REPO_ROOT / "docs" / "META_LEDGER.md"


def _entry(num: int, content: str, previous: str) -> str:
    chain = ledger_hash.chain_hash(content, previous)
    return (
        f"### Entry #{num}: TEST ENTRY\n\n"
        f"**Content Hash**: `{content}`\n"
        f"**Previous Hash**: `{previous}`\n"
        f"**Chain Hash (Merkle seal)**: `{chain}`\n\n"
        "**Decision**: fixture.\n\n"
    )


def _ledger(nums: list[int]) -> str:
    """Build a well-formed chain over the given entry numbers."""
    # Real digests: `is_placeholder_pattern` (Phase 66) rejects synthetic
    # monotonic hex, so a fixture built from f"{n:064x}" fails for the wrong
    # reason and would mask what these tests actually assert.
    out, prev = ["# Ledger\n\n"], hashlib.sha256(b"genesis").hexdigest()
    for n in nums:
        content = hashlib.sha256(f"entry-{n}".encode()).hexdigest()
        out.append(_entry(n, content, prev))
        prev = ledger_hash.chain_hash(content, prev)
    return "".join(out)


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "META_LEDGER.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_deleted_entry_is_detected(tmp_path: Path):
    """THE COUNTERFACTUAL. Fails against HEAD, which returns 0.

    Entry #2 is excised. #1 and #3 remain internally consistent -- each one's
    recorded chain hash still recomputes from its own fields -- but #3's
    `previous_hash` is now produced by nothing in the file.
    """
    full = _ledger([1, 2, 3])
    i = full.index("### Entry #2:")
    j = full.index("### Entry #3:")
    gapped = _write(tmp_path, full[:i] + full[j:])

    assert ledger_hash.verify(gapped) != 0, (
        "a deleted entry must break the sequence assertion; every survivor is "
        "internally consistent, so per-entry arithmetic alone cannot see it"
    )


def test_tampered_previous_hash_still_detected(tmp_path: Path):
    """REGRESSION. The sequence check must supplement, not replace, the math."""
    text = _ledger([1, 2, 3])
    prev = re.findall(r"\*\*Previous Hash\*\*: `([0-9a-f]{64})`", text)[-1]
    tampered = _write(tmp_path, text.replace(prev, "f" * 64, 1))

    assert ledger_hash.verify(tampered) != 0


def test_intact_ledger_verifies_clean(tmp_path: Path):
    """No false positives on a well-formed chain."""
    assert ledger_hash.verify(_write(tmp_path, _ledger([1, 2, 3]))) == 0


def test_number_gap_warns_without_failing(tmp_path: Path):
    """A numbering gap with intact links is a WARN, not a failure.

    Entry numbers are labels; adjacency in the file is the real structure.
    """
    assert ledger_hash.verify(_write(tmp_path, _ledger([1, 3, 4]))) == 0


@pytest.mark.parametrize("gap", sorted(ledger_hash.KNOWN_ENTRY_GAPS))
def test_declared_gap_exceptions_are_silent(gap: int):
    """Both declared gaps are real absences in this repository's own ledger."""
    text = LIVE_LEDGER.read_text(encoding="utf-8")
    nums = [int(m.group(1)) for m in ledger_hash.ENTRY_RE.finditer(text)]
    assert gap not in nums, f"#{gap} is declared a gap but is present"


def test_live_ledger_gap_set_matches_declared_exceptions():
    """The exception list is derived from reality, not trusted as a constant.

    Goes red when a new gap appears AND when someone widens the constant to
    silence one. That second direction is the mechanism by which gap 510 went
    unnoticed until Phase 218 enumerated instead of recalling.
    """
    text = LIVE_LEDGER.read_text(encoding="utf-8")
    nums = [int(m.group(1)) for m in ledger_hash.ENTRY_RE.finditer(text)]
    observed = {n for n in range(min(nums), max(nums)) if n not in nums}

    assert observed == set(ledger_hash.KNOWN_ENTRY_GAPS), (
        f"ledger gaps {sorted(observed)} != declared "
        f"{sorted(ledger_hash.KNOWN_ENTRY_GAPS)}"
    )


def test_live_ledger_still_verifies_clean():
    """The real ledger, with its real gaps, must stay green."""
    assert ledger_hash.verify(LIVE_LEDGER) == 0
