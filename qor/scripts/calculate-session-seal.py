#!/usr/bin/env python3
"""Reference implementation for substantiation seal hashing."""

import sys
from hashlib import sha256
from pathlib import Path

# Standalone dashed-name script: ensure package is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from qor import workdir as _workdir  # noqa: E402


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_all_files(root: Path) -> str:
    content_parts = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            content_parts.append(path.read_text(encoding="utf-8"))
    return "".join(content_parts)


def hash_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def calculate_session_seal() -> str:
    root = _workdir.root()
    concept = read_file(root / "docs" / "CONCEPT.md")
    architecture = read_file(root / "docs" / "ARCHITECTURE_PLAN.md")
    audit_report = read_file(root / ".agent" / "staging" / "AUDIT_REPORT.md")
    system_state = read_file(root / "docs" / "SYSTEM_STATE.md")
    source_files = read_all_files(root / "src")

    final_content = concept + architecture + audit_report + system_state + source_files
    content_hash = hash_text(final_content)

    # Placeholder: replace with actual extraction from META_LEDGER.md
    previous_hash = "PREVIOUS_LEDGER_HASH"

    session_seal = hash_text(content_hash + previous_hash)
    return session_seal


if __name__ == "__main__":
    print(calculate_session_seal())
