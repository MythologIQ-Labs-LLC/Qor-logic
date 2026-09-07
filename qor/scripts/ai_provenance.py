"""AI provenance manifest builder (Phase 54).

Composes the ``ai_provenance`` field embedded in gate artifacts.
Maps to EU AI Act Art. 13/50 transparency obligations and NIST AI RMF
MEASURE-2.1 / MANAGE-1.1 evidence collection.

Single source of truth for manifest shape: ``_provenance.schema.json``.
This module is the canonical builder; skills do not construct manifests
by hand.

Per ``qor/references/doctrine-eu-ai-act.md`` and ``qor/references/doctrine-ai-rmf.md``.
"""
from __future__ import annotations

import importlib.metadata
import os
import re
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PYPROJECT = _REPO_ROOT / "pyproject.toml"
_PROJECT_NAME = "qor-logic"

# Phases that have an operator decision gate (Art. 14 oversight surface).
_OPERATOR_DECISION_PHASES: frozenset[str] = frozenset({"audit", "substantiate", "validate"})

# Suppression env var for tests/CI.
_QUIET_ENV = "QOR_PROVENANCE_QUIET"
# Override env var for model family (set by harness when available).
_MODEL_ENV = "QOR_MODEL_FAMILY"

_warned_keys: set[str] = set()


class HumanOversight(Enum):
    PASS = "pass"
    VETO = "veto"
    OVERRIDE = "override"
    ABSENT = "absent"


@dataclass(frozen=True)
class _ProvenanceContext:
    host: str
    model_family: str
    version: str


def _canonical(name: str) -> str:
    # PEP 503, applied to the UNTRUSTED name out of the foreign file. The
    # metadata call below passes _PROJECT_NAME, already canonical, so this is
    # the only side that normalises: its job is to stop us rejecting a spelling
    # that metadata itself would have resolved.
    return re.sub(r"[-_.]+", "-", name).lower()


def _read_system_version() -> str:
    """Resolve this project's version, from the only sources that can know it.

    Phase 269 (GH #427): _REPO_ROOT resolves to site-packages under an installed
    package, so _PYPROJECT may be a FOREIGN project's file that merely sits at
    the path we computed. EVERY failure to establish the file as ours falls
    through to metadata: nothing about a stranger's file, not even an exception,
    may escape a provenance helper, because build_manifest calls this on every
    gate artifact and a raise here means no gate can be written at all.

    Order is load-bearing. pyproject is authoritative in a source checkout;
    metadata reports the last install and would under-report a working tree.
    """
    # One rule, applied to both readers: every call into external state is
    # wrapped in `except Exception`, and none of our own logic sits inside a
    # handler. Enumerating exceptions is the wrong tool for a total contract
    # because it predicts an open set -- three escapes were found that way
    # here (UnicodeDecodeError from the decode tomllib owns, RecursionError
    # from its recursive-descent parse, MemoryError on an oversized file).
    # Any Exception from the call means we could not read a stranger's file.
    try:
        with _PYPROJECT.open("rb") as fh:
            data = tomllib.load(fh)
    except Exception:
        data = None

    # Outside every handler from here down, so our own bugs stay loud.
    if isinstance(data, dict):
        project = data.get("project", {})
        if isinstance(project, dict) and _canonical(str(project.get("name", ""))) == _PROJECT_NAME:
            version = project.get("version")
            if isinstance(version, str) and version:
                return version
            # Ours, but dynamic = ["version"]. The name selects the SOURCE, not
            # the RESULT; metadata knows what this file does not state.
    try:
        version = importlib.metadata.version(_PROJECT_NAME)
    except Exception:
        # Same rule as above. metadata parses METADATA out of a .dist-info,
        # so a damaged install raises past PackageNotFoundError; an undecodable
        # METADATA gives UnicodeDecodeError. Any Exception here means we could
        # not obtain a version, which is what a total function needs.
        return "unknown"
    # version() returns None for a .dist-info with no METADATA, or one with no
    # Version field. The schema requires a non-empty string, so a None here
    # would emit an invalid gate artifact rather than an ugly one.
    return version if isinstance(version, str) and version else "unknown"


def _detect_host() -> str:
    try:
        from qor.scripts import qor_platform
    except ImportError:
        return "unknown"
    state = qor_platform.current() or {}
    if isinstance(state, dict):
        detected = state.get("detected", {})
        if isinstance(detected, dict):
            host = detected.get("host", "unknown")
            if isinstance(host, str) and host and host != "unknown":
                return host
    # Phase 186 (GH #242): no marker (or marker says unknown) -- a session
    # that never ran apply_profile still gets fresh env-signal detection.
    return qor_platform.detect_host()


def _detect_model_family() -> str:
    return os.environ.get(_MODEL_ENV, "unknown") or "unknown"


def _warn_once(key: str, message: str) -> None:
    if os.environ.get(_QUIET_ENV) == "1":
        return
    if key in _warned_keys:
        return
    _warned_keys.add(key)
    print(f"WARN [ai_provenance]: {message}", file=sys.stderr)


def _validate_human_oversight(phase: str, oversight: HumanOversight) -> None:
    if phase in _OPERATOR_DECISION_PHASES:
        if oversight == HumanOversight.ABSENT:
            raise ValueError(
                f"phase {phase!r} has an operator decision gate; "
                f"human_oversight must be one of pass/veto/override, not absent"
            )
    else:
        if oversight not in {HumanOversight.ABSENT, HumanOversight.OVERRIDE}:
            raise ValueError(
                f"phase {phase!r} has no operator decision gate; "
                f"human_oversight must be absent or override, not {oversight.value!r}"
            )


def build_manifest(
    phase: str,
    *,
    host: str | None = None,
    model_family: str | None = None,
    human_oversight: HumanOversight,
    system_version: str | None = None,
) -> dict[str, Any]:
    """Compose an AI provenance manifest dict.

    Auto-derives ``system_version`` from ``pyproject.toml``, ``host`` from
    ``qor.scripts.qor_platform.current()``, and ``model_family`` from the
    ``QOR_MODEL_FAMILY`` env var when their respective arguments are None.
    Emits a one-time stderr warning per process when either falls back to
    "unknown" (suppress with ``QOR_PROVENANCE_QUIET=1``).
    """
    _validate_human_oversight(phase, human_oversight)

    if host is None:
        host = _detect_host()
        if host == "unknown":
            _warn_once("host", "host fell back to 'unknown' (no platform state detected)")

    if model_family is None:
        model_family = _detect_model_family()
        if model_family == "unknown":
            _warn_once("model_family", f"model_family fell back to 'unknown' (set ${_MODEL_ENV} to record)")

    if system_version is None:
        system_version = _read_system_version()
        if system_version == "unknown":
            _warn_once("version", "version fell back to 'unknown' (no project manifest or installed distribution found)")

    return {
        "system": "Qor-logic",
        "version": system_version,
        "host": host,
        "model_family": model_family,
        "human_oversight": human_oversight.value,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
