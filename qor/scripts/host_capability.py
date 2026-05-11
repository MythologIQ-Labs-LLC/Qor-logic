"""Phase 47 (#38 + B23): host-repo posture checks.

Provides:
- `check_module(name)`, `check_file(path)` — primitive presence checks.
- `check_step_prerequisites(step_name, prereqs)` — aggregate per substantiate step.
- `check_qor_logic_freshness(repo_root, latest_known)` — install-staleness detection.
- `emit_prerequisite_absent_event(...)`, `emit_freshness_event(...)` — JSONL emitters
  conforming to qor/gates/schema/shadow_event.schema.json.

Stdlib-only. No subprocess. All emits use json.dumps with sorted keys.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from dataclasses import dataclass
from pathlib import Path

_PYPROJECT_VERSION = re.compile(r'^\s*version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"\s*$', re.MULTILINE)


@dataclass(frozen=True)
class CheckResult:
    name: str
    present: bool
    detail: str = ""


@dataclass(frozen=True)
class PrereqSummary:
    step_name: str
    checks: tuple[CheckResult, ...]
    can_proceed: bool


@dataclass(frozen=True)
class FreshnessResult:
    installed_version: str | None
    latest_known: str | None
    drift: bool
    detail: str = ""


def check_module(name: str) -> CheckResult:
    try:
        spec = importlib.util.find_spec(name)
    except (ValueError, ModuleNotFoundError, ImportError) as exc:
        return CheckResult(name=name, present=False, detail=f"{type(exc).__name__}: {exc}")
    if spec is None:
        return CheckResult(name=name, present=False, detail="find_spec returned None")
    return CheckResult(name=name, present=True)


def check_file(path: str | Path) -> CheckResult:
    p = Path(path)
    if p.exists():
        return CheckResult(name=str(path), present=True, detail=str(p.resolve()))
    return CheckResult(name=str(path), present=False, detail=f"missing: {p}")


def check_step_prerequisites(step_name: str, prereqs: list[dict]) -> PrereqSummary:
    results: list[CheckResult] = []
    for spec in prereqs:
        kind = spec.get("kind")
        target = spec.get("target", "")
        if kind == "module":
            results.append(check_module(target))
        elif kind == "file":
            results.append(check_file(target))
        else:
            results.append(CheckResult(name=target, present=False, detail=f"unknown kind: {kind}"))
    can_proceed = all(r.present for r in results)
    return PrereqSummary(step_name=step_name, checks=tuple(results), can_proceed=can_proceed)


def _read_installed_version(repo_root: Path) -> str | None:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return None
    m = _PYPROJECT_VERSION.search(pyproject.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def check_qor_logic_freshness(
    repo_root: str | Path,
    latest_known: str | None = None,
) -> FreshnessResult:
    root = Path(repo_root)
    installed = _read_installed_version(root)
    if latest_known is None:
        marker = root / ".qor" / "freshness" / "latest_known"
        if marker.exists():
            latest_known = marker.read_text(encoding="utf-8").strip()
    if installed is None:
        return FreshnessResult(
            installed_version=None,
            latest_known=latest_known,
            drift=False,
            detail="pyproject.toml absent or version unreadable",
        )
    if latest_known is None:
        return FreshnessResult(
            installed_version=installed,
            latest_known=None,
            drift=False,
            detail="no latest_known reference provided",
        )
    drift = installed != latest_known
    detail = (
        f"installed={installed} latest_known={latest_known}"
        if drift
        else "versions match"
    )
    return FreshnessResult(
        installed_version=installed,
        latest_known=latest_known,
        drift=drift,
        detail=detail,
    )


def _event_id(payload: dict) -> str:
    parts = (
        payload["ts"],
        payload["skill"],
        payload["session_id"],
        payload["event_type"],
        str(payload["severity"]),
        json.dumps(payload["details"], sort_keys=True),
        payload.get("source_entry_id") or "",
    )
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()


def _write_event(payload: dict, log_path: str | Path) -> None:
    payload = dict(payload)
    payload.setdefault("addressed", False)
    payload.setdefault("issue_url", None)
    payload.setdefault("addressed_ts", None)
    payload.setdefault("addressed_reason", None)
    payload.setdefault("source_entry_id", None)
    payload["id"] = _event_id(payload)
    log = Path(log_path)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")


def emit_prerequisite_absent_event(
    step_name: str,
    missing: list[CheckResult],
    session_id: str,
    log_path: str | Path,
    ts: str = "",
) -> None:
    if not ts:
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "ts": ts,
        "skill": "qor-substantiate",
        "session_id": session_id,
        "event_type": "prerequisite_absent",
        "severity": 2,
        "details": {
            "step": step_name,
            "missing": [{"name": c.name, "detail": c.detail} for c in missing],
        },
    }
    _write_event(payload, log_path)


def emit_freshness_event(
    result: FreshnessResult,
    session_id: str,
    log_path: str | Path,
    skill: str = "qor-plan",
    ts: str = "",
) -> None:
    if not ts:
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "ts": ts,
        "skill": skill,
        "session_id": session_id,
        "event_type": "qor_logic_stale_install",
        "severity": 1,
        "details": {
            "installed_version": result.installed_version,
            "latest_known": result.latest_known,
            "drift": result.drift,
            "detail": result.detail,
        },
    }
    _write_event(payload, log_path)
