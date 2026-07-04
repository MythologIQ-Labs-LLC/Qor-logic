"""Phase 170 (GH #252): ledger migration tool tests.

Ports FailSafe-Pro's proven transform with house discipline; the acceptance
bar (LD-3) drives the REAL verifier over pre/post files.
"""
from __future__ import annotations

import hashlib
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import pytest

from qor.scripts import ledger_migrate as lm

_C1 = hashlib.sha256(b"one").hexdigest()
_P1 = "0" * 64
_X1 = hashlib.sha256((_C1 + "|" + _P1).encode()).hexdigest()
_C2 = hashlib.sha256(b"two").hexdigest()
_X2 = hashlib.sha256((_C2 + _X1).encode()).hexdigest()  # legacy no-separator formula
_C3 = hashlib.sha256(b"three").hexdigest()
_X3 = hashlib.sha256((_C3 + "|" + _X2).encode()).hexdigest()

_LEGACY = f"""# LEDGER

### Entry #1: FORMAT A (inline)

body text A

**Content Hash**: `{_C1}`
**Previous Hash**: `{_P1}`
**Chain Hash**: `{_X1}`

### Entry #2: FORMAT B (fenced)

body text B

**Content Hash**:
```
SHA256(x)
= {_C2}
```

**Previous Hash**: `{_X1}`

**Chain Hash**:
```
SHA256(content + previous)
= {_X2}
```

### Entry #3: FORMAT C (session-seal labels)

body text C

**META_LEDGER Content Hash** value `{_C3}`
**Previous Chain Hash**: `{_X2}`
**Session Seal**: `{_X3}`
"""


def test_migrates_all_three_legacy_formats():
    migrated, stats = lm.migrate(_LEGACY)
    assert stats["migrated"] == 3
    assert stats["unchanged_partial"] == 0 and stats["unchanged_no_hash"] == 0
    for h in (_C1, _C2, _C3, _X1, _X2, _X3):
        assert h in migrated  # hashes preserved verbatim
    assert migrated.count("**Chain Hash (Merkle seal)**:") == 3
    assert "```" not in migrated  # fenced blocks normalized away
    assert "**Session Seal**:" not in migrated


def test_canonical_input_is_byte_stable():
    once, _ = lm.migrate(_LEGACY)
    twice, stats = lm.migrate(once)
    assert twice == once, "canonical input must re-migrate byte-stable"
    assert stats["migrated"] == 3


def test_partial_and_no_hash_entries_left_verbatim_and_reported():
    partial = _LEGACY + f"""
### Entry #4: PARTIAL

only content here

**Content Hash**: `{_C1}`

### Entry #5: NO HASH

prose only
"""
    migrated, stats = lm.migrate(partial)
    assert stats["unchanged_partial"] == 1
    assert stats["unchanged_no_hash"] == 1
    assert "only content here" in migrated and "prose only" in migrated


def test_chain_math_mismatch_reported_not_rejected():
    bad = _LEGACY.replace(_X1, "f" * 64, 1).replace("**Previous Hash**: `" + "f" * 64, "**Previous Hash**: `" + _X1)
    # keep entry 2's previous pointing at the original X1 so only entry 1's chain is wrong
    migrated, stats = lm.migrate(bad)
    assert any(m["entry"] == 1 for m in stats["mismatches"])
    assert "f" * 64 in migrated  # recorded value preserved, not corrected


def test_dry_run_writes_nothing_and_reports(tmp_path, capsys):
    src = tmp_path / "in.md"
    dst = tmp_path / "out.md"
    src.write_text(_LEGACY, encoding="utf-8")
    rc = lm.main(["--input", str(src), "--output", str(dst), "--dry-run"])
    out = capsys.readouterr().out
    assert rc == 0
    assert not dst.exists()
    assert "[dry] would write" in out
    assert "migrated=3" in out


def test_main_exit_codes_and_same_path_rejected(tmp_path, capsys):
    src = tmp_path / "in.md"
    dst = tmp_path / "out.md"
    src.write_text(_LEGACY, encoding="utf-8")
    assert lm.main(["--input", str(src), "--output", str(dst)]) == 0
    assert dst.exists()
    src2 = tmp_path / "partial.md"
    src2.write_text(_LEGACY + "\n### Entry #4: NO HASH\n\nprose\n", encoding="utf-8")
    assert lm.main(["--input", str(src2), "--output", str(tmp_path / "o2.md")]) == 1
    with pytest.raises(SystemExit):
        lm.main(["--input", str(src), "--output", str(src)])


def test_migrated_ledger_becomes_verifiable(tmp_path):
    from qor.scripts import ledger_hash

    src = tmp_path / "legacy.md"
    dst = tmp_path / "canonical.md"
    src.write_text(_LEGACY, encoding="utf-8")

    def verify_counts(path: Path) -> tuple[int, int]:
        buf = io.StringIO()
        with mock.patch.object(sys, "argv", ["ledger_hash", "verify", str(path)]), \
             redirect_stdout(buf):
            ledger_hash.main()
        out = buf.getvalue()
        return out.count(": chain hash verified"), out.count("Skipped")

    ok_before, _ = verify_counts(src)
    assert lm.main(["--input", str(src), "--output", str(dst)]) == 0
    ok_after, _ = verify_counts(dst)
    assert ok_after > ok_before, (
        f"migration must make entries verifiable (before={ok_before}, after={ok_after})"
    )
    assert ok_after == 3
