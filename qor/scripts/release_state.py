"""Validate explicit exceptional release dispositions.

The ordinary release path is represented by CHANGELOG + Git tags. This module
owns only the narrow exception record used when those surfaces intentionally or
historically diverge.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


_SCHEMA = "qor.release-state/v1"
_SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_ALLOWED_STATES = frozenset({"sealed_unpublished", "legacy_untagged"})


class ReleaseStateError(ValueError):
    """Raised when the exceptional release-state record is malformed."""


def validate_payload(payload: object, changelog_versions: set[str]) -> set[str]:
    """Validate one release-state payload and return its exceptional versions."""
    if not isinstance(payload, dict) or set(payload) != {"schema", "exceptions"}:
        raise ReleaseStateError("release-state root must contain schema + exceptions")
    if payload.get("schema") != _SCHEMA:
        raise ReleaseStateError(f"release-state schema must be {_SCHEMA}")
    entries = payload["exceptions"]
    if not isinstance(entries, list):
        raise ReleaseStateError("release-state exceptions must be a list")

    seen: set[str] = set()
    for entry in entries:
        version = _validate_entry(entry, changelog_versions)
        if version in seen:
            raise ReleaseStateError(f"duplicate release-state version: {version}")
        seen.add(version)
    return seen


def _validate_entry(entry: object, changelog_versions: set[str]) -> str:
    if not isinstance(entry, dict) or set(entry) != {"version", "state", "reason"}:
        raise ReleaseStateError("release-state entry must contain version/state/reason")
    version = entry["version"]
    state = entry["state"]
    reason = entry["reason"]
    if not isinstance(version, str) or not _SEMVER.fullmatch(version):
        raise ReleaseStateError("release-state version must be strict MAJOR.MINOR.PATCH")
    if state not in _ALLOWED_STATES:
        raise ReleaseStateError(f"unsupported release-state value: {state}")
    if not isinstance(reason, str) or not reason.strip():
        raise ReleaseStateError(f"release-state reason is required for {version}")
    if version not in changelog_versions:
        raise ReleaseStateError(f"release-state version missing CHANGELOG section: {version}")
    return version


def load_exceptions(path: Path, changelog_versions: set[str]) -> set[str]:
    """Load and validate the exceptional release-state JSON file."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseStateError(f"cannot read release-state record: {exc}") from exc
    return validate_payload(payload, changelog_versions)
