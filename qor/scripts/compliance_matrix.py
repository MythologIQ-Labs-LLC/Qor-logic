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
# Engagement points a control can plug into (the precursor values a downstream
# enforcement layer reads); RUNNABLE_POINTS are the ones the SDK can run
# standalone and therefore require a runner (Phase 142).
ENGAGEMENTS: tuple[str, ...] = ("pre-commit", "pre-push", "pre-tool-write", "ci", "seal")
RUNNABLE_POINTS: tuple[str, ...] = ("pre-commit", "pre-push", "pre-tool-write")

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
    engagement: tuple[str, ...] = ()
    runner: dict | None = None
    invocation: str = ""
    runner_unavailable_reason: str | None = None


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
            engagement=tuple(c["engagement"]),
            runner=c.get("runner"),
            invocation=c.get("invocation", ""),
            runner_unavailable_reason=c.get("runner_unavailable_reason"),
        )
        for c in data["controls"]
    )


def load_packaged_matrix() -> tuple[Control, ...]:
    """Load the matrix that ships inside the installed qor-logic package.

    The SDK reads control definitions from here (so a downstream consumer gets
    the matrix from `pip install qor-logic`, not from their own repo tree), then
    runs each control's runner against the consumer's working tree. In the dev
    repo this resolves to the same file as ``load_matrix(REPO)``.
    """
    return load_matrix(_PKG.parent)


def load_waivers(root: Path) -> tuple[Waiver, ...]:
    data = _load_raw(root)
    return tuple(
        Waiver(id=w["id"], justification=w["justification"], issue=w["issue"])
        for w in data.get("waivers", [])
    )


def enforced_set(controls: tuple[Control, ...]) -> set[tuple[str, str]]:
    """The ``{(id, posture)}`` set the ratchet compares across releases."""
    return {(c.id, c.posture) for c in controls}
