"""Phase 56 ledger_entry_id behavior tests."""
from __future__ import annotations

import pytest

from qor.scripts.ledger_entry_id import make_entry_uid, validate_entry_uid


def test_make_entry_uid_is_stable():
    a = make_entry_uid(ts="2026-05-11T17:00:00Z", session_id="sess-x",
                       target="docs/plan-x.md", content_hash="a" * 64)
    b = make_entry_uid(ts="2026-05-11T17:00:00Z", session_id="sess-x",
                       target="docs/plan-x.md", content_hash="a" * 64)
    assert a == b


def test_make_entry_uid_format_is_le_16_hex():
    uid = make_entry_uid(ts="2026-05-11T17:00:00Z", session_id="s",
                         target="t", content_hash="a" * 64)
    assert uid.startswith("le_")
    assert len(uid) == 3 + 16
    int(uid[3:], 16)  # raises if not hex


def test_make_entry_uid_changes_when_content_hash_changes():
    a = make_entry_uid(ts="2026-05-11T17:00:00Z", session_id="s",
                       target="t", content_hash="a" * 64)
    b = make_entry_uid(ts="2026-05-11T17:00:00Z", session_id="s",
                       target="t", content_hash="b" * 64)
    assert a != b


def test_make_entry_uid_changes_when_target_changes():
    a = make_entry_uid(ts="2026-05-11T17:00:00Z", session_id="s",
                       target="A", content_hash="a" * 64)
    b = make_entry_uid(ts="2026-05-11T17:00:00Z", session_id="s",
                       target="B", content_hash="a" * 64)
    assert a != b


def test_validate_entry_uid_accepts_helper_output():
    uid = make_entry_uid(ts="2026-05-11T17:00:00Z", session_id="s",
                         target="t", content_hash="a" * 64)
    assert validate_entry_uid(uid) == uid


def test_validate_entry_uid_rejects_sequential_number():
    with pytest.raises(ValueError):
        validate_entry_uid("160")
    with pytest.raises(ValueError):
        validate_entry_uid("#160")


def test_validate_entry_uid_rejects_wrong_prefix():
    with pytest.raises(ValueError):
        validate_entry_uid("entry_0123456789abcdef")


def test_validate_entry_uid_rejects_uppercase_hex():
    with pytest.raises(ValueError):
        validate_entry_uid("le_0123456789ABCDEF")


def test_validate_entry_uid_rejects_wrong_length():
    with pytest.raises(ValueError):
        validate_entry_uid("le_0123")
