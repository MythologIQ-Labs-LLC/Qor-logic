"""Consumer working-directory anchors for qor.

Resolves the project root at import time via $QOR_ROOT or Path.cwd().
All helpers return concrete Path objects suitable for file I/O on the
consumer's repository (not inside the installed package).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _detect_git_root() -> Path | None:
    """Return the git toplevel, or None if not in a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, timeout=5,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError,
            subprocess.TimeoutExpired):
        return None


def root() -> Path:
    """Project root: $QOR_ROOT > cwd."""
    env = os.environ.get("QOR_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def gate_dir() -> Path:
    """Consumer gate state: ``<root>/.qor/gates``."""
    return root() / ".qor" / "gates"


def shadow_log() -> Path:
    """Local process shadow genome log."""
    return root() / "docs" / "PROCESS_SHADOW_GENOME.md"


def shadow_log_upstream() -> Path:
    """Upstream process shadow genome log."""
    return root() / "docs" / "PROCESS_SHADOW_GENOME_UPSTREAM.md"


def meta_ledger() -> Path:
    """Meta ledger path."""
    return root() / "docs" / "META_LEDGER.md"
