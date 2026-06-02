"""Phase 119 (GH #148): ledger_hash.verify() recognizes RECONCILIATION entries.

A RECONCILIATION entry attests a duplicate-previous_hash residual set; strict
verify() (no --tolerate flag) then reports DISCLOSED_RECONCILED for exactly
that set, and ONLY when the attested entry is genuinely a duplicate-previous_hash
member (so attestation cannot launder content tampering of a unique entry).
Per doctrine-test-functionality.md, assertions check verify()'s exit code and
stdout/stderr, not section presence.
"""
from __future__ import annotations

import io
import textwrap
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from qor.scripts import reconcile
from qor.scripts.ledger_hash import chain_hash, verify

REPO_ROOT = Path(__file__).resolve().parent.parent
TS = "2026-05-30T00:00:00Z"


def _hex(seed: str) -> str:
    import hashlib
    return hashlib.sha256(seed.encode()).hexdigest()


def _entry(num: int, content: str, previous: str, *, chain_override: str | None = None) -> str:
    chain = chain_override if chain_override is not None else chain_hash(content, previous)
    return textwrap.dedent(
        f"""

        ### Entry #{num}: TEST

        **Content Hash**: `{content}`

        **Previous Hash**: `{previous}`

        **Chain Hash**: `{chain}`
        """
    )


def _corpus() -> str:
    h1, h2, h3 = _hex("H1"), _hex("H2"), _hex("H3")
    return "# META_LEDGER\n" + "".join([
        _entry(16, _hex("c16"), h1, chain_override=_hex("bad16")),
        _entry(17, _hex("c17"), h1, chain_override=_hex("bad17")),
        _entry(18, _hex("c18"), h2, chain_override=_hex("bad18")),
        _entry(19, _hex("c19"), h2, chain_override=_hex("bad19")),
        _entry(20, _hex("c20"), h3, chain_override=_hex("bad20")),
        _entry(21, _hex("c21"), h3, chain_override=_hex("bad21")),
        _entry(22, _hex("c22"), _hex("uniqueprev")),
    ])


def _capture(ledger_path: Path, *, tolerate: bool = False):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = verify(ledger_path, tolerate_known_grandfathered=tolerate)
    return rc, out.getvalue(), err.getvalue()


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "META_LEDGER.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_strict_verify_fails_before_reconciliation(tmp_path):
    """Precondition: the raw corpus FAILs strict verify (the consumer blocker)."""
    led = _write(tmp_path, _corpus())
    rc, _out, err = _capture(led)
    assert rc != 0 and "FAIL" in err


def test_strict_verify_passes_after_reconciliation(tmp_path):
    led = _write(tmp_path, _corpus())
    proposal = reconcile.build_proposal(led, ts=TS)
    reconcile.append_reconciliation_entry(led, proposal, ts=TS)
    rc, out, err = _capture(led)  # strict: NO tolerate flag
    assert rc == 0, err
    for n in (16, 17, 18, 19, 20, 21):
        assert f"DISCLOSED_RECONCILED Entry #{n}" in out
    assert "FAIL" not in err


def test_verify_still_fails_on_unattested_duplicate(tmp_path):
    """A RECONCILIATION attesting only a subset leaves the rest failing."""
    led = _write(tmp_path, _corpus())
    proposal = reconcile.build_proposal(led, ts=TS)
    proposal["residual_entry_nums"] = [16, 17, 18, 19]  # drop 20, 21
    reconcile.append_reconciliation_entry(led, proposal, ts=TS)
    rc, _out, err = _capture(led)
    assert rc != 0
    assert "Entry #20" in err  # the unattested duplicate still FAILs/taints


def test_reconciliation_does_not_launder_content_tampering(tmp_path):
    """Security hardening: attestation is honored ONLY for genuine
    duplicate-previous_hash members. A tampered UNIQUE-previous_hash entry
    named in a RECONCILIATION entry still FAILs."""
    tampered = "# META_LEDGER\n" + "".join([
        _entry(5, _hex("c5"), _hex("uniqA"), chain_override=_hex("tampered5")),
        _entry(6, _hex("c6"), _hex("uniqB")),  # clean
    ])
    led = _write(tmp_path, tampered)
    # Hand-craft a malicious proposal attesting #5 (which is NOT a duplicate).
    proposal = {"status": "pending", "ledger": str(led),
                "residual_entry_nums": [5], "previous_hashes": [_hex("uniqA")],
                "ts": TS, "proposal_id": "deadbeef0000"}
    reconcile.append_reconciliation_entry(led, proposal, ts=TS)
    rc, _out, err = _capture(led)
    assert rc != 0, "unique-previous_hash tampering must not be launderable via RECONCILIATION"
    assert "Entry #5" in err


def test_post_reconciliation_entry_chains_off_reconciliation(tmp_path):
    led = _write(tmp_path, _corpus())
    proposal = reconcile.build_proposal(led, ts=TS)
    result = reconcile.append_reconciliation_entry(led, proposal, ts=TS)
    # Append a normal entry whose previous_hash is the RECONCILIATION chain hash.
    follow_content = _hex("follow")
    follow = _entry(result["entry_num"] + 1, follow_content, result["chain_hash"])
    led.write_text(led.read_text(encoding="utf-8") + follow, encoding="utf-8")
    rc, out, err = _capture(led)
    assert rc == 0, err
    assert f"OK   Entry #{result['entry_num'] + 1}" in out


def test_doctrine_documents_reconcile_v2():
    """Doctrine SG-ConcurrentLedgerRace-A must document the reconcile V2 while
    KEEPING the forbidden-renumbering immutability clause."""
    doctrine = (REPO_ROOT / "qor" / "references"
                / "doctrine-shadow-genome-countermeasures.md").read_text(encoding="utf-8")
    assert "reconcile" in doctrine and "RECONCILIATION" in doctrine
    assert "renumber" in doctrine.lower()  # immutability guarantee preserved
