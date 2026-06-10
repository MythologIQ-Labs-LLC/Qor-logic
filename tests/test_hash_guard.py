"""Phase 59 (#48): hash_guard helper behavior tests.

V1 contract: validate_sha256 is the seal-critical hash validator;
require_toolkit_modules raises hard when crypto modules are absent.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from qor.scripts.hash_guard import (
    HEX_SHA256_RE,
    HashEvidence,
    hash_file,
    require_toolkit_modules,
    validate_sha256,
)


def test_hash_file_returns_64_lower_hex_digest(tmp_path):
    p = tmp_path / "data.bin"
    p.write_bytes(b"Phase 59 fixture")
    ev = hash_file(p)
    assert isinstance(ev, HashEvidence)
    assert ev.path == str(p)
    assert HEX_SHA256_RE.match(ev.sha256)
    assert ev.byte_count == len(b"Phase 59 fixture")
    assert ev.sha256 == hashlib.sha256(b"Phase 59 fixture").hexdigest()


def test_hash_file_raises_on_missing_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        hash_file(tmp_path / "no-such.bin")


def test_hash_file_normalize_newlines_crlf_invariant(tmp_path):
    # Phase 157 (GAP-GOV-03 follow-on): a seal-text digest produced under
    # normalize_newlines=True must survive git's autocrlf conversion, i.e. a
    # CRLF file and its LF twin hash identically -- and to the LF default.
    crlf = tmp_path / "crlf.md"
    crlf.write_bytes(b"# Seal\r\nline one\r\nline two\r\n")
    lf = tmp_path / "lf.md"
    lf.write_bytes(b"# Seal\nline one\nline two\n")
    crlf_norm = hash_file(crlf, normalize_newlines=True).sha256
    lf_norm = hash_file(lf, normalize_newlines=True).sha256
    assert crlf_norm == lf_norm
    # The normalized CRLF digest equals the default (raw) digest of the
    # already-LF twin -- the value an operator recorded at LF seal time.
    assert crlf_norm == hash_file(lf).sha256


def test_hash_file_default_is_byte_exact_for_crlf(tmp_path):
    # The default (binary/general-purpose) path must NOT silently normalize:
    # a CRLF file and its LF twin differ, and the digest is over the raw bytes.
    crlf = tmp_path / "crlf.bin"
    raw = b"a\r\nb\r\n"
    crlf.write_bytes(raw)
    lf = tmp_path / "lf.bin"
    lf.write_bytes(b"a\nb\n")
    ev = hash_file(crlf)
    assert ev.sha256 == hashlib.sha256(raw).hexdigest()
    assert ev.byte_count == len(raw)
    assert ev.sha256 != hash_file(lf).sha256


def test_hash_file_normalize_byte_count_matches_hashed_bytes(tmp_path):
    # Under normalization, byte_count must describe the bytes actually hashed
    # (the LF-normalized length), not the raw CRLF length.
    crlf = tmp_path / "crlf.md"
    raw = b"x\r\ny\r\nz\r\n"  # 9 raw bytes -> 6 after CRLF->LF
    crlf.write_bytes(raw)
    ev = hash_file(crlf, normalize_newlines=True)
    assert ev.byte_count == len(raw.replace(b"\r\n", b"\n"))
    assert ev.byte_count != len(raw)
    assert ev.sha256 == hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def test_validate_sha256_accepts_real_digest():
    real = hashlib.sha256(b"x").hexdigest()
    assert validate_sha256(real, label="content_hash") == real


def test_validate_sha256_rejects_placeholder_text():
    for placeholder in ("TBD", "TODO", "placeholder", "abcd"):
        with pytest.raises(ValueError) as exc:
            validate_sha256(placeholder, label="chain_hash")
        assert "chain_hash" in str(exc.value)


def test_validate_sha256_rejects_empty_string():
    with pytest.raises(ValueError):
        validate_sha256("", label="content_hash")


def test_validate_sha256_rejects_wrong_length():
    too_short = "abc" * 21  # 63 chars
    too_long = "abc" * 22 + "0"  # 67 chars
    with pytest.raises(ValueError):
        validate_sha256(too_short, label="content_hash")
    with pytest.raises(ValueError):
        validate_sha256(too_long, label="content_hash")


def test_validate_sha256_rejects_uppercase_digest():
    upper = hashlib.sha256(b"x").hexdigest().upper()
    with pytest.raises(ValueError) as exc:
        validate_sha256(upper, label="content_hash")
    assert "content_hash" in str(exc.value)


def test_validate_sha256_rejects_non_hex_characters():
    real = hashlib.sha256(b"x").hexdigest()
    bad = "z" + real[1:]
    with pytest.raises(ValueError):
        validate_sha256(bad, label="content_hash")


def test_require_toolkit_modules_passes_for_stdlib_modules():
    require_toolkit_modules(("json", "pathlib"))


def test_require_toolkit_modules_raises_with_missing_module_names():
    with pytest.raises(RuntimeError) as exc:
        require_toolkit_modules(("qor.scripts.definitely_missing_xyz",))
    assert "definitely_missing_xyz" in str(exc.value)


def test_require_toolkit_modules_lists_all_missing_when_multiple():
    with pytest.raises(RuntimeError) as exc:
        require_toolkit_modules((
            "qor.scripts.missing_a",
            "json",
            "qor.scripts.missing_b",
        ))
    msg = str(exc.value)
    assert "missing_a" in msg
    assert "missing_b" in msg
    assert "json" not in msg


def test_validate_sha256_passes_through_legitimate_real_chain_hash():
    """Regression guard: the real chain hash from META_LEDGER #157 must validate."""
    sealed = "dd96a59a24e694717c90cc048782418e54f817a8128c9ef774fd96e9b04431bc"
    assert validate_sha256(sealed, label="chain_hash") == sealed
