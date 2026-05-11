"""Phase 56 ledger_fragment behavior tests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from qor.scripts.ledger_entry_id import make_entry_uid
from qor.scripts.ledger_fragment import (
    LedgerFragment,
    read_fragments,
    write_fragment,
)


def _frag(body: str = "body text\n", uid_seed: int = 0) -> LedgerFragment:
    uid = make_entry_uid(
        ts="2026-05-11T17:00:00Z",
        session_id=f"sess-{uid_seed}",
        target="docs/x.md",
        content_hash="a" * 64,
    )
    return LedgerFragment(
        uid=uid,
        ts="2026-05-11T17:00:00Z",
        session_id=f"sess-{uid_seed}",
        title=f"TEST {uid_seed}",
        body=body,
        content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
    )


def test_write_fragment_uses_uid_filename(tmp_path):
    f = _frag()
    p = write_fragment(tmp_path, f)
    assert p.name == f"{f.uid}.json"
    assert p.parent == tmp_path / ".qor" / "ledger" / "fragments"


def test_write_fragment_idempotent_on_same_body(tmp_path):
    f = _frag()
    write_fragment(tmp_path, f)
    write_fragment(tmp_path, f)  # second write OK
    files = list((tmp_path / ".qor" / "ledger" / "fragments").glob("*.json"))
    assert len(files) == 1


def test_write_fragment_refuses_uid_collision_with_different_body(tmp_path):
    f = _frag(body="first body\n")
    write_fragment(tmp_path, f)
    g = LedgerFragment(
        uid=f.uid, ts=f.ts, session_id=f.session_id, title=f.title,
        body="DIFFERENT BODY\n",
        content_hash=hashlib.sha256(b"DIFFERENT BODY\n").hexdigest(),
    )
    with pytest.raises(ValueError):
        write_fragment(tmp_path, g)


def test_write_fragment_refuses_content_hash_mismatch(tmp_path):
    f = LedgerFragment(
        uid="le_0123456789abcdef",
        ts="2026-05-11T17:00:00Z",
        session_id="sess-x",
        title="X",
        body="real body\n",
        content_hash="0" * 64,
    )
    with pytest.raises(ValueError):
        write_fragment(tmp_path, f)


def test_read_fragments_returns_empty_tuple_when_dir_missing(tmp_path):
    assert read_fragments(tmp_path) == ()


def test_read_fragments_sorts_by_ts_then_uid(tmp_path):
    early = LedgerFragment(
        uid="le_0000000000000001",
        ts="2026-05-11T16:00:00Z", session_id="s", title="A",
        body="x\n", content_hash=hashlib.sha256(b"x\n").hexdigest(),
    )
    late = LedgerFragment(
        uid="le_0000000000000002",
        ts="2026-05-11T17:00:00Z", session_id="s", title="B",
        body="y\n", content_hash=hashlib.sha256(b"y\n").hexdigest(),
    )
    write_fragment(tmp_path, late)
    write_fragment(tmp_path, early)
    out = read_fragments(tmp_path)
    assert [f.uid for f in out] == [early.uid, late.uid]
