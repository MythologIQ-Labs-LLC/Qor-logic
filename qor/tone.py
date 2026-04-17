"""Communication-tier resolution primitive.

A pure function that resolves the effective output tier for a skill or CLI
invocation. Resolution order:

1. Session override (e.g., from a ``/qor-tone`` directive in the current
   agent session). If set and valid, wins.
2. Workspace config: ``.qorlogic/config.json``'s ``tone`` field. Read if
   present and well-formed.
3. Default: ``"technical"``.

No side effects beyond reading the config file. Invalid session overrides
raise ``ValueError``; malformed config files fall back to the default.

Tier semantics live in ``qor/references/doctrine-communication-tiers.md``.
"""
from __future__ import annotations

import json
from pathlib import Path


_VALID_TONES = ("technical", "standard", "plain")


def _validate(tone: str) -> None:
    if tone not in _VALID_TONES:
        raise ValueError(
            f"invalid tone: {tone!r} (expected one of {_VALID_TONES})"
        )


def _config_tone(config_path: Path) -> str | None:
    if not config_path.exists():
        return None
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    tone = data.get("tone")
    return tone if tone in _VALID_TONES else None


def resolve_tone(
    session_override: str | None,
    config_path: Path | None,
) -> str:
    """Return the effective tier: session > config > default."""
    if session_override is not None:
        _validate(session_override)
        return session_override
    if config_path is not None:
        from_config = _config_tone(config_path)
        if from_config is not None:
            return from_config
    return "technical"
