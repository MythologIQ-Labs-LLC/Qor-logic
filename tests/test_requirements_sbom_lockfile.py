"""Phase 107 D-107.2: requirements-sbom.txt hash-pinned lockfile assertions."""
from __future__ import annotations

import pathlib
import re

_LOCKFILE = pathlib.Path("requirements-sbom.txt")
_LOCKFILE_IN = pathlib.Path("requirements-sbom.in")


def test_sbom_lockfile_files_exist():
    assert _LOCKFILE.is_file(), "requirements-sbom.txt must be committed"
    assert _LOCKFILE_IN.is_file(), "requirements-sbom.in (source) must be committed"


def test_sbom_lockfile_pins_cyclonedx_bom_with_hash():
    text = _LOCKFILE.read_text(encoding="utf-8")
    m = re.search(r"^cyclonedx-bom==[0-9]+\.[0-9]+", text, re.MULTILINE)
    assert m is not None, "lockfile must pin 'cyclonedx-bom' to a specific version"
    # Find at least one --hash line tied to cyclonedx-bom
    cdx_block = re.search(
        r"^cyclonedx-bom==[0-9.]+(?:\s+\\?\n\s+--hash=sha256:[0-9a-f]{64})+",
        text,
        re.MULTILINE,
    )
    assert cdx_block is not None, (
        "cyclonedx-bom must carry at least one --hash=sha256:... line"
    )


def test_sbom_lockfile_hashes_are_sha256_format():
    text = _LOCKFILE.read_text(encoding="utf-8")
    hash_lines = re.findall(r"--hash=(\S+)", text)
    assert len(hash_lines) >= 10, (
        f"lockfile must carry multiple --hash entries; got {len(hash_lines)}"
    )
    for h in hash_lines:
        assert h.startswith("sha256:"), f"hash {h!r} must use sha256: prefix"
        digest = h.split(":", 1)[1]
        assert re.match(r"^[0-9a-f]{64}$", digest), (
            f"hash digest {digest!r} must be 64 lowercase hex chars"
        )
