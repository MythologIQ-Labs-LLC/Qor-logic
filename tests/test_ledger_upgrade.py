"""Phase 179 (GH #271 V1 slice): one-command ledger recovery + versioned format.

`upgrade` orchestrates the Phase 170 migrator and the post-anchor verifier
under a swap-on-success-only contract: the original ledger is byte-untouched
on any residual failure. The schema-version marker makes the format
machine-detectable (absent == 0/legacy).
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

from qor.scripts import ledger_upgrade as lu

_C1 = hashlib.sha256(b"one").hexdigest()
_P1 = "0" * 64
_X1 = hashlib.sha256((_C1 + "|" + _P1).encode()).hexdigest()
_C2 = hashlib.sha256(b"two").hexdigest()
_X2 = hashlib.sha256((_C2 + _X1).encode()).hexdigest()  # legacy no-separator formula

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
"""

_HEX_RE = re.compile(r"[0-9a-f]{64}")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_legacy(tmp_path: Path) -> Path:
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(_LEGACY, encoding="utf-8")
    return ledger


def test_upgrade_normalizes_legacy_markup_and_swaps(tmp_path):
    ledger = _write_legacy(tmp_path)
    report = lu.upgrade(ledger)
    assert report.swapped and report.verify_rc == 0
    text = ledger.read_text(encoding="utf-8")
    assert "```" not in text  # fenced hash blocks normalized away
    assert lu.schema_version(text) == 1
    assert not list(tmp_path.glob("*.tmp"))  # no temp residue


def test_upgrade_preserves_hashes_verbatim(tmp_path):
    ledger = _write_legacy(tmp_path)
    before = set(_HEX_RE.findall(ledger.read_text(encoding="utf-8")))
    lu.upgrade(ledger)
    after = set(_HEX_RE.findall(ledger.read_text(encoding="utf-8")))
    assert after == before  # markup moves, math does not


def test_upgrade_failure_leaves_original_untouched(tmp_path):
    # Corrupt Entry #2's chain hash so post-anchor verification fails.
    broken = _LEGACY.replace(_X2, "f" * 64)
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(broken, encoding="utf-8")
    original = _sha(ledger)
    report = lu.upgrade(ledger)
    assert not report.swapped and report.verify_rc != 0
    assert _sha(ledger) == original  # byte-untouched on residual failure
    assert not list(tmp_path.glob("*.tmp"))


def test_upgrade_is_idempotent(tmp_path):
    ledger = _write_legacy(tmp_path)
    lu.upgrade(ledger)
    first = _sha(ledger)
    report = lu.upgrade(ledger)
    assert report.swapped is False or _sha(ledger) == first  # no rewrite churn
    assert _sha(ledger) == first
    assert ledger.read_text(encoding="utf-8").count("qor:meta-ledger-schema") == 1


def test_schema_version_parses_marker(tmp_path):
    assert lu.schema_version("# L\n\n### Entry #1: X\n") == 0
    assert lu.schema_version("# L\n<!-- qor:meta-ledger-schema=1 -->\n") == 1


def test_dry_run_writes_nothing(tmp_path):
    ledger = _write_legacy(tmp_path)
    original = _sha(ledger)
    report = lu.upgrade(ledger, dry_run=True)
    assert report.verify_rc == 0 and not report.swapped
    assert _sha(ledger) == original
    assert not list(tmp_path.glob("*.tmp"))


def test_cli_exit_codes(tmp_path, monkeypatch):
    ledger = _write_legacy(tmp_path)
    assert lu.main(["--ledger", str(ledger)]) == 0
    broken = _LEGACY.replace(_X2, "f" * 64)
    bad = tmp_path / "BAD.md"
    bad.write_text(broken, encoding="utf-8")
    assert lu.main(["--ledger", str(bad)]) == 1


def test_current_ledger_declares_schema_version():
    # Phase 179 self-application lock: this repository's own ledger carries
    # the version-1 marker; fails if it is ever dropped.
    text = (Path(__file__).resolve().parent.parent / "docs" / "META_LEDGER.md"
            ).read_text(encoding="utf-8")
    assert lu.schema_version(text) == 1
