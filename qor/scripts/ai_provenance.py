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

import os
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PYPROJECT = _REPO_ROOT / "pyproject.toml"

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


def _read_system_version() -> str:
    if not _PYPROJECT.exists():
        return "unknown"
    with _PYPROJECT.open("rb") as fh:
        data = tomllib.load(fh)
    return str(data.get("project", {}).get("version", "unknown"))


def _detect_host() -> str:
    try:
        from qor.scripts.qor_platform import current
    except ImportError:
        return "unknown"
    state = current() or {}
    if not isinstance(state, dict):
        return "unknown"
    detected = state.get("detected", {})
    if not isinstance(detected, dict):
        return "unknown"
    host = detected.get("host", "unknown")
    return host if isinstance(host, str) and host else "unknown"


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

    return {
        "system": "Qor-logic",
        "version": system_version,
        "host": host,
        "model_family": model_family,
        "human_oversight": human_oversight.value,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
