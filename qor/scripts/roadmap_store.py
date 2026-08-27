from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from qor.scripts import roadmap_state

ROADMAP_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_roadmap_id(roadmap_id: str) -> str:
    if not ROADMAP_ID_PATTERN.fullmatch(roadmap_id):
        raise roadmap_state.InvalidHistoryError(
            "invalid roadmap id; use 1-64 alphanumeric, '_' or '-' characters "
            "and start with an alphanumeric character"
        )
    return roadmap_id


def roadmap_dir(repo_root: str | Path, roadmap_id: str) -> Path:
    validate_roadmap_id(roadmap_id)
    root = Path(repo_root).resolve()
    base = (root / ".qor" / "roadmaps").resolve()
    path = (base / roadmap_id).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise roadmap_state.InvalidHistoryError(
            f"roadmap path escapes canonical state root: {roadmap_id!r}"
        ) from exc
    return path


def events_path(repo_root: str | Path, roadmap_id: str) -> Path:
    return roadmap_dir(repo_root, roadmap_id) / "events.jsonl"


def load_events(repo_root: str | Path, roadmap_id: str) -> list[dict]:
    path = events_path(repo_root, roadmap_id)
    if not path.exists():
        return []
    events: list[dict] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise roadmap_state.InvalidHistoryError(
                f"malformed roadmap JSONL at line {line_no}: {exc.msg}"
            ) from exc
        events.append(event)
    roadmap_state.reduce_events(events)
    return events


def load_state(repo_root: str | Path, roadmap_id: str) -> roadmap_state.RoadmapState:
    return roadmap_state.reduce_events(load_events(repo_root, roadmap_id))


def make_event(
    roadmap_id: str,
    *,
    seq: int,
    event_type: str,
    payload: dict,
    event_id: str | None = None,
    ts: str | None = None,
) -> dict:
    validate_roadmap_id(roadmap_id)
    return {
        "contract_version": roadmap_state.CONTRACT_VERSION,
        "event_id": event_id or f"evt_{uuid.uuid4().hex}",
        "roadmap_id": roadmap_id,
        "seq": seq,
        "ts": ts or _now_iso(),
        "type": event_type,
        "payload": payload,
    }


def _atomic_replace(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        suffix=".tmp",
    ) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    try:
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def append_event(repo_root: str | Path, roadmap_id: str, event: dict) -> dict:
    path = events_path(repo_root, roadmap_id)
    existing = load_events(repo_root, roadmap_id)
    candidate = [*existing, event]
    roadmap_state.reduce_events(candidate)
    content = "".join(
        json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n"
        for item in candidate
    )
    _atomic_replace(path, content)
    return event


def append_payload(
    repo_root: str | Path,
    roadmap_id: str,
    *,
    event_type: str,
    payload: dict,
) -> dict:
    existing = load_events(repo_root, roadmap_id)
    event = make_event(
        roadmap_id,
        seq=len(existing) + 1,
        event_type=event_type,
        payload=payload,
    )
    return append_event(repo_root, roadmap_id, event)


def create_roadmap(
    repo_root: str | Path,
    roadmap_id: str,
    *,
    title: str,
    success_conditions: list[str] | None = None,
    exclusions: list[str] | None = None,
) -> dict:
    if load_events(repo_root, roadmap_id):
        raise roadmap_state.InvalidHistoryError(
            f"roadmap already exists: {roadmap_id}"
        )
    return append_payload(
        repo_root,
        roadmap_id,
        event_type="roadmap_created",
        payload={
            "objective": {
                "title": title,
                "success_conditions": success_conditions or [],
                "exclusions": exclusions or [],
            }
        },
    )
