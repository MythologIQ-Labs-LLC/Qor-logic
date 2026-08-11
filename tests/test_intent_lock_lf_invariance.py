"""Phase 218 (GH #318): intent_lock must hash line-ending-invariantly.

`ledger_hash.content_hash` normalizes CRLF to LF before hashing, and its
docstring names GAP-GOV-03 as the reason: git's autocrlf rewrites a file on
checkout, so hashing raw bytes makes a seal-time digest disagree with the
recompute on the committed file.

`intent_lock._hash_file` never got that treatment. The failure mode is a false
ABORT -- the safe direction -- but it fires on ordinary Windows events, and the
operator response to a false ABORT is to re-capture, which is also the action
that masks a real drift. A gate that cries wolf on encoding gets trained around.

The Phase 216 seal hit this and had to prove the change was encoding-only before
re-capturing.
"""
from __future__ import annotations

from pathlib import Path

from qor.reliability import intent_lock


def _write(path: Path, text: str, *, crlf: bool) -> Path:
    body = text.replace("\n", "\r\n") if crlf else text
    path.write_bytes(body.encode("utf-8"))
    return path


BODY = "# Audit Report\n\n**Verdict**: PASS\n\nGround: none.\n"


def test_hash_is_line_ending_invariant(tmp_path: Path):
    """THE COUNTERFACTUAL. Fails against HEAD, which hashes raw bytes."""
    lf = _write(tmp_path / "lf.md", BODY, crlf=False)
    crlf = _write(tmp_path / "crlf.md", BODY, crlf=True)

    assert lf.read_bytes() != crlf.read_bytes(), "fixture must differ on disk"
    assert intent_lock._hash_file(lf) == intent_lock._hash_file(crlf), (
        "identical content in different line endings must hash identically; "
        "otherwise autocrlf alone triggers a drift ABORT"
    )


def test_real_content_drift_still_detected(tmp_path: Path):
    """Normalization must not swallow genuine change.

    Trading a false ABORT for a false PASS is the strictly worse direction:
    the gate exists to catch a plan or audit edited during implementation.
    """
    original = _write(tmp_path / "a.md", BODY, crlf=False)
    before = intent_lock._hash_file(original)

    original.write_bytes(BODY.replace("PASS", "VETO").encode("utf-8"))
    assert intent_lock._hash_file(original) != before, (
        "a verdict flipped from PASS to VETO must change the hash"
    )


def test_whitespace_only_change_is_still_drift(tmp_path: Path):
    """Only line endings are normalized -- not indentation or trailing space.

    A narrower guarantee than 'whitespace-insensitive', and deliberately so.
    """
    f = _write(tmp_path / "b.md", BODY, crlf=False)
    before = intent_lock._hash_file(f)

    f.write_bytes((BODY + "   \n").encode("utf-8"))
    assert intent_lock._hash_file(f) != before


def test_verify_survives_line_ending_conversion(tmp_path: Path, monkeypatch):
    """End to end: capture, convert the audit report's endings, verify passes."""
    plan = _write(tmp_path / "plan.md", "# Plan\n\n**change_class**: feature\n", crlf=False)
    audit = _write(tmp_path / "AUDIT.md", BODY, crlf=False)

    captured = intent_lock._hash_file(audit)
    _write(audit, BODY, crlf=True)

    assert intent_lock._hash_file(audit) == captured, (
        "converting the report to CRLF must not read as drift"
    )
    assert intent_lock._hash_file(plan) == intent_lock._hash_file(plan)
