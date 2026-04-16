#!/usr/bin/env python3
"""Platform detection + capability catalog for Qor skills.

Auto-detected: host (via env vars), gh-cli (via subprocess).
User-declared: codex-plugin, agent-teams, mcp-servers.

State persisted in .qor/platform.json (atomic writes via os.replace).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qor import resources as _resources
from qor import workdir as _workdir

MARKER_PATH = _workdir.root() / ".qor" / "platform.json"
PROFILES_DIR = Path(str(_resources.asset("platform", "profiles")))

KNOWN_HOSTS = ("claude-code", "kilo-code", "codex-standalone", "unknown")


# ----- Host detection -----

def detect_host() -> str:
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        return "claude-code"
    # Future: add kilo-code, codex-standalone env signals when standardized.
    return "unknown"


def detect_gh_cli() -> bool:
    try:
        version = subprocess.run(
            ["gh", "--version"], capture_output=True, text=True, timeout=5
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    if version.returncode != 0:
        return False
    try:
        auth = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True, timeout=5
        )
    except subprocess.TimeoutExpired:
        return False
    return auth.returncode == 0


# ----- Profile I/O -----

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_front_matter(text: str) -> dict:
    """Parse YAML-ish front matter without a YAML dep. Supports scalar + simple lists + 2-space nested dicts."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    body = m.group(1)

    out: dict = {}
    stack: list[tuple[int, dict]] = [(0, out)]

    for raw in body.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        while stack and indent < stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if line.startswith("- "):
            # List item within the most recent key-holding dict's list value
            # Not supported in this minimal parser beyond inline []; skip.
            continue

        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if not val:
            new_dict: dict = {}
            parent[key] = new_dict
            stack.append((indent + 2, new_dict))
            continue

        # Scalar
        if val in ("true", "True"):
            parent[key] = True
        elif val in ("false", "False"):
            parent[key] = False
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            parent[key] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
        elif val.isdigit():
            parent[key] = int(val)
        else:
            parent[key] = val.strip('"').strip("'")
    return out


def load_profile(name: str) -> dict:
    path = PROFILES_DIR / f"{name}.md"
    if not path.exists():
        available = sorted(p.stem for p in PROFILES_DIR.glob("*.md"))
        raise ValueError(f"Unknown profile '{name}'. Available: {available}")
    fm = _parse_front_matter(path.read_text(encoding="utf-8"))
    if not fm.get("profile"):
        raise ValueError(f"Profile file missing front matter: {path}")
    return fm


def list_profiles() -> list[str]:
    return sorted(p.stem for p in PROFILES_DIR.glob("*.md"))


# ----- State I/O -----

def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as tf:
        json.dump(data, tf, indent=2)
        tf.write("\n")
        tmp = tf.name
    os.replace(tmp, path)


def current(marker: Path | None = None) -> dict | None:
    marker = marker or MARKER_PATH
    if not marker.exists():
        return None
    return json.loads(marker.read_text(encoding="utf-8"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def apply_profile(name: str, marker: Path | None = None) -> dict:
    marker = marker or MARKER_PATH
    profile = load_profile(name)
    state = {
        "version": "1",
        "detected": {"host": detect_host(), "gh_cli": detect_gh_cli()},
        "declared": {
            **profile.get("capabilities", {}),
            "host_declared": profile.get("host"),
        },
        "profile_applied": profile["profile"],
        "ts": _now_iso(),
    }
    _atomic_write_json(marker, state)
    return state


def set_capability(name: str, value, marker: Path | None = None) -> dict:
    marker = marker or MARKER_PATH
    state = current(marker) or {
        "version": "1",
        "detected": {"host": detect_host(), "gh_cli": detect_gh_cli()},
        "declared": {},
        "profile_applied": None,
        "ts": _now_iso(),
    }
    state.setdefault("declared", {})[name] = value
    state["ts"] = _now_iso()
    _atomic_write_json(marker, state)
    return state


def is_available(capability: str, marker: Path | None = None) -> bool:
    state = current(marker)
    if state is None:
        return False
    # Check detected first (host, gh_cli)
    detected = state.get("detected", {})
    if capability in detected:
        return bool(detected[capability])
    declared = state.get("declared", {})
    if capability in declared:
        v = declared[capability]
        if isinstance(v, list):
            return len(v) > 0
        return bool(v)
    return False


def clear(marker: Path | None = None) -> None:
    marker = marker or MARKER_PATH
    if marker.exists():
        marker.unlink()


def detect_all() -> dict:
    """Run all auto-detections and return the result without writing."""
    return {"host": detect_host(), "gh_cli": detect_gh_cli()}


# ----- CLI -----

def _parse_bool(s: str) -> bool:
    lower = s.lower()
    if lower in ("true", "1", "yes", "y", "on"):
        return True
    if lower in ("false", "0", "no", "n", "off"):
        return False
    raise ValueError(f"Not a bool: {s!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("detect", help="Run auto-detect, print result (no write)")
    sub.add_parser("get", help="Print current .qor/platform.json")
    sub.add_parser("list", help="List available profiles")
    sub.add_parser("clear", help="Remove the platform marker")

    ap_apply = sub.add_parser("apply", help="Apply a named profile")
    ap_apply.add_argument("profile")

    ap_set = sub.add_parser("set", help="Set a single capability")
    ap_set.add_argument("capability")
    ap_set.add_argument("value")

    ap_check = sub.add_parser("check", help="Check a capability; exit 0 if available")
    ap_check.add_argument("capability")

    args = ap.parse_args()

    if args.cmd == "detect":
        result = detect_all()
        print(json.dumps(result, indent=2))
        return 0

    if args.cmd == "get":
        state = current()
        if state is None:
            print("(no platform marker)")
            return 1
        print(json.dumps(state, indent=2))
        return 0

    if args.cmd == "list":
        for name in list_profiles():
            print(name)
        return 0

    if args.cmd == "clear":
        clear()
        print("Platform marker cleared.")
        return 0

    if args.cmd == "apply":
        try:
            state = apply_profile(args.profile)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
        print(json.dumps(state, indent=2))
        return 0

    if args.cmd == "set":
        try:
            parsed = _parse_bool(args.value)
        except ValueError:
            parsed = args.value  # keep string
        state = set_capability(args.capability, parsed)
        print(json.dumps(state, indent=2))
        return 0

    if args.cmd == "check":
        available = is_available(args.capability)
        print(f"{args.capability}: {'available' if available else 'not available'}")
        return 0 if available else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
