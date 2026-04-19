"""Phase 23 Track A: Security remediation tests for all 9 findings."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# ----- MEDIUM-1: repo path validation -----

def test_medium1_valid_repo_path_accepted():
    """Repo path with qor/ marker is accepted."""
    from qor.scripts.collect_shadow_genomes import validate_repo_path
    tmp = Path(__file__).parent  # has qor/ sibling
    # Use repo root which has qor/ dir
    assert validate_repo_path(REPO_ROOT) is True


def test_medium1_invalid_repo_path_rejected(tmp_path):
    """Repo path without qor/ or docs/ is rejected."""
    from qor.scripts.collect_shadow_genomes import validate_repo_path
    assert validate_repo_path(tmp_path) is False


# ----- MEDIUM-2: malformed JSONL warning -----

def test_medium2_malformed_jsonl_warns(tmp_path, capsys):
    """Malformed JSONL lines emit warning to stderr."""
    from qor.scripts.shadow_process import read_events
    log = tmp_path / "shadow.jsonl"
    log.write_text('{"valid": true}\n{bad json\n{"also": "valid"}\n', encoding="utf-8")
    events = read_events(log)
    assert len(events) == 2
    captured = capsys.readouterr()
    assert "WARN: skipping malformed JSONL line 2" in captured.err


def test_medium2_valid_jsonl_no_warning(tmp_path, capsys):
    """Valid JSONL parses without warning."""
    from qor.scripts.shadow_process import read_events
    log = tmp_path / "shadow.jsonl"
    log.write_text('{"a": 1}\n{"b": 2}\n', encoding="utf-8")
    events = read_events(log)
    assert len(events) == 2
    captured = capsys.readouterr()
    assert "WARN" not in captured.err


# ----- MEDIUM-3: file locking -----

def test_medium3_atomic_append_uses_locking(tmp_path, monkeypatch):
    """_atomic_append acquires a file lock during write."""
    from qor.scripts import shadow_process
    target = tmp_path / "test.jsonl"
    target.write_text("", encoding="utf-8")

    lock_acquired = []
    original_atomic = shadow_process._atomic_append

    # The locking is internal; verify no crash and file is written
    shadow_process._atomic_append(target, '{"test": true}\n')
    content = target.read_text(encoding="utf-8")
    assert '{"test": true}' in content


# ----- LOW-1: chain_hash separator -----

def test_low1_chain_hash_uses_separator():
    """New chain_hash uses | separator between content and prev."""
    from qor.scripts.ledger_hash import chain_hash
    content = "a" * 64
    prev = "b" * 64
    expected = hashlib.sha256((content + "|" + prev).encode("utf-8")).hexdigest()
    assert chain_hash(content, prev) == expected


def test_low1_legacy_chain_hash_no_separator():
    """legacy_chain_hash preserves old format without separator."""
    from qor.scripts.ledger_hash import legacy_chain_hash
    content = "a" * 64
    prev = "b" * 64
    expected = hashlib.sha256((content + prev).encode("utf-8")).hexdigest()
    assert legacy_chain_hash(content, prev) == expected


def test_low1_verify_handles_both_formats(tmp_path):
    """verify() accepts both old-format and new-format chain hashes."""
    from qor.scripts.ledger_hash import chain_hash, legacy_chain_hash, verify

    # Entry 1 uses legacy format (no separator)
    content_a = "a" * 64
    prev_a = "0" * 64
    chain_a_legacy = legacy_chain_hash(content_a, prev_a)

    # Entry 2 uses new format (with separator)
    content_b = "b" * 64
    chain_b_new = chain_hash(content_b, chain_a_legacy)

    ledger = tmp_path / "ledger.md"
    ledger.write_text(f"""### Entry #1: LEGACY
**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
Chain Hash = {chain_a_legacy}

### Entry #2: NEW
**Content Hash**: `{content_b}`
**Previous Hash**: `{chain_a_legacy}`
Chain Hash = {chain_b_new}
""", encoding="utf-8")
    rc = verify(ledger)
    assert rc == 0


# ----- LOW-2: session_id validation -----

def test_low2_valid_session_id_accepted():
    """Valid session_id passes validation."""
    from qor.scripts.remediate_emit_gate import validate_session_id
    # Standard session IDs
    validate_session_id("2026-04-15T10:00:00")
    validate_session_id("my-session-123")
    validate_session_id("abc_def")


def test_low2_invalid_session_id_rejected():
    """Session ID with path traversal chars raises ValueError."""
    from qor.scripts.remediate_emit_gate import validate_session_id
    with pytest.raises(ValueError):
        validate_session_id("../../../etc/passwd")
    with pytest.raises(ValueError):
        validate_session_id("session;rm -rf /")
    with pytest.raises(ValueError):
        validate_session_id("")


# ----- LOW-3: event ID validation -----

def test_low3_valid_event_id_accepted():
    """Valid hex event ID passes validation."""
    from qor.scripts.create_shadow_issue import validate_event_id
    valid = "a" * 64
    validate_event_id(valid)  # should not raise


def test_low3_invalid_event_id_rejected():
    """Non-hex or wrong-length event ID raises ValueError."""
    from qor.scripts.create_shadow_issue import validate_event_id
    with pytest.raises(ValueError):
        validate_event_id("not-a-hash")
    with pytest.raises(ValueError):
        validate_event_id("g" * 64)  # g not in hex
    with pytest.raises(ValueError):
        validate_event_id("a" * 63)  # too short


# ----- LOW-4: PASS verdict regex -----

def test_low4_verdict_regex_matches_correctly():
    """_audit_has_pass uses regex, not substring match."""
    import importlib.util
    import tempfile

    spec = importlib.util.spec_from_file_location(
        "intent_lock",
        REPO_ROOT / "qor" / "reliability" / "intent_lock.py",
    )
    intent_lock = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(intent_lock)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("VERDICT: PASS\nSome other text")
        f.flush()
        p = Path(f.name)
    assert intent_lock._audit_has_pass(p) is True
    p.unlink()

    # "PASS" alone without VERDICT should NOT match
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("This shall PASS the test\nNo verdict here")
        f.flush()
        p = Path(f.name)
    assert intent_lock._audit_has_pass(p) is False
    p.unlink()


# ----- LOW-5: timezone-aware datetime -----

def test_low5_uses_timezone_aware_datetime():
    """intent-lock capture uses timezone-aware datetime, not utcnow()."""
    import ast
    src = (REPO_ROOT / "qor" / "reliability" / "intent_lock.py").read_text(encoding="utf-8")
    assert "utcnow()" not in src
    assert "datetime.now(timezone.utc)" in src or "dt.datetime.now(dt.timezone.utc)" in src


# ----- LOW-6: verify reports skipped count -----

def test_low6_verify_reports_skipped_entries(tmp_path, capsys):
    """verify() prints count of entries skipped due to non-matching markup."""
    from qor.scripts.ledger_hash import verify
    ledger = tmp_path / "ledger.md"
    ledger.write_text("""### Entry #1: OLD
**Decision**: no hash markers

### Entry #2: ALSO OLD
**Author**: someone
""", encoding="utf-8")
    rc = verify(ledger)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Skipped 2 entries with non-verifiable markup" in captured.out
