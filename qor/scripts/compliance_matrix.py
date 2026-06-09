#!/usr/bin/env python3
"""Compliance control-matrix loader (Phase 141).

Loads + schema-validates ``qor/compliance/control_matrix.json`` -- the declarative
registry of every compliance control Qor-logic conveys downstream. Pure: no side
effects. Consumed by ``compliance_conformance`` (live verifier) and
``compliance_ratchet`` (release-over-release non-regression).

See ``qor/references/doctrine-compliance-conveyance.md``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import jsonschema

POSTURES: tuple[str, ...] = ("ABORT", "WARN")
DETECTIONS: tuple[str, ...] = ("skill-marker", "test", "ci-job")

_MATRIX_REL = "qor/compliance/control_matrix.json"
# The schema ships with qor-logic (package data), resolved relative to this
# module, NOT relative to the caller-supplied root (a consumer repo carries its
# own matrix but reuses qor-logic's schema).
_PKG = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = _PKG / "gates" / "schema" / "control_matrix.schema.json"


@dataclass(frozen=True)
class Control:
    id: str
    framework: str
    control: str
    enforcing_module: str
    posture: str
    detection: str
    wired_into: dict
    variants: tuple[str, ...]
    invocation: str = ""


@dataclass(frozen=True)
class Waiver:
    id: str
    justification: str
    issue: str


def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_raw(root: Path) -> dict:
    data = json.loads((root / _MATRIX_REL).read_text(encoding="utf-8"))
    try:
        jsonschema.validate(data, _schema())
    except jsonschema.ValidationError as exc:
        # Name the offending control id when the failing instance carries one.
        instance = exc.instance
        cid = instance.get("id") if isinstance(instance, dict) else None
        where = f" (control {cid!r})" if cid else ""
        raise ValueError(f"control_matrix.json schema violation{where}: {exc.message}") from exc
    return data


def load_matrix(root: Path) -> tuple[Control, ...]:
    """Return the validated controls. Raises ValueError on schema violation."""
    data = _load_raw(root)
    return tuple(
        Control(
            id=c["id"],
            framework=c["framework"],
            control=c["control"],
            enforcing_module=c["enforcing_module"],
            posture=c["posture"],
            detection=c["detection"],
            wired_into=c["wired_into"],
            variants=tuple(c["variants"]),
            invocation=c.get("invocation", ""),
        )
        for c in data["controls"]
    )


def load_waivers(root: Path) -> tuple[Waiver, ...]:
    data = _load_raw(root)
    return tuple(
        Waiver(id=w["id"], justification=w["justification"], issue=w["issue"])
        for w in data.get("waivers", [])
    )


def enforced_set(controls: tuple[Control, ...]) -> set[tuple[str, str]]:
    """The ``{(id, posture)}`` set the ratchet compares across releases."""
    return {(c.id, c.posture) for c in controls}
