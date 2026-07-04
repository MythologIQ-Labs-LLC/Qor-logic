"""Evidence-bundle reconstruction for a sealed phase (Phase 169; GH #251).

ADR-0018 posture (MS agent-governance-toolkit): audit evidence is
RECONSTRUCTED on demand from signals already recorded -- ledger seal entry,
gate artifacts, provenance sidecars, audit history, intent lock, shadow
events, CHANGELOG section, seal commit/tag -- instead of writing more
per-phase ceremony. Partial reconstruction is surfaced explicitly
(``completeness.missing`` names absent signals); nothing is fabricated and
no collector ever raises. Output follows the Phase 165 contract: human lines
then exactly ONE JSON object as the final stdout line.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
from pathlib import Path

_SEAL_BLOCK_RE = re.compile(
    r"^### Entry #(\d+): SESSION SEAL[^\n]*\n(.*?)(?=^### |\Z)",
    re.MULTILINE | re.DOTALL,
)
_FIELD_RES = {
    "session_id": re.compile(r"^\*\*Session\*\*:\s*`?([0-9A-Za-z._-]+)`?", re.MULTILINE),
    "phase_num": re.compile(r"Phase\s+(\d+)", re.IGNORECASE),
    "content_hash": re.compile(r"^\*\*Content Hash\*\*:\s*`([0-9a-f]{64})`", re.MULTILINE),
    "chain_hash": re.compile(r"^\*\*Chain Hash[^:]*\*\*:\s*`([0-9a-f]{64})`", re.MULTILINE),
    "timestamp": re.compile(r"^\*\*Timestamp\*\*:\s*(\S+)", re.MULTILINE),
    "version": re.compile(r"\(v(\d+\.\d+\.\d+)\)"),
}


def _seal_blocks(ledger_text: str) -> list[dict]:
    out = []
    for m in _SEAL_BLOCK_RE.finditer(ledger_text):
        block = {"entry_num": int(m.group(1)), "header": m.group(0)[:200]}
        body = m.group(0)
        for key, rx in _FIELD_RES.items():
            found = rx.search(body)
            block[key] = found.group(1) if found else None
        if block["phase_num"] is not None:
            block["phase_num"] = int(block["phase_num"])
        out.append(block)
    return out


def resolve_query(ledger_text: str, session: str | None = None,
                  phase: int | None = None) -> tuple[int, str] | None:
    for block in _seal_blocks(ledger_text):
        if session and block["session_id"] == session:
            return (block["phase_num"], block["session_id"])
        if phase is not None and block["phase_num"] == phase:
            return (block["phase_num"], block["session_id"])
    return None


def _collect(fn):
    """Collectors never raise: exceptions become {'found': False, 'errors': [...]}."""
    def wrapped(*args, **kwargs) -> dict:
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 -- reconstruction must survive anything
            return {"found": False, "errors": [f"{type(exc).__name__}: {exc}"]}
    return wrapped


@_collect
def _ledger_entry(repo_root: Path, sid: str, phase_num: int) -> dict:
    text = (repo_root / "docs" / "META_LEDGER.md").read_text(encoding="utf-8")
    for block in _seal_blocks(text):
        if block["session_id"] == sid:
            return {"found": True, "errors": [], **{k: block[k] for k in (
                "entry_num", "phase_num", "content_hash", "chain_hash", "timestamp")}}
    return {"found": False, "errors": []}


@_collect
def _gate_artifacts(repo_root: Path, sid: str) -> dict:
    from qor.scripts import tier_guard, validate_gate_artifact as vga

    sess = repo_root / ".qor" / "gates" / sid
    if not sess.is_dir():
        return {"found": False, "errors": []}
    declared = list(tier_guard.declared_artifacts(sess / "plan.json"))
    artifacts = []
    for ph in declared:
        path = sess / f"{ph}.json"
        errs = vga.validate_one(ph, path) if path.exists() else ["missing"]
        artifacts.append({"phase": ph, "path": str(path),
                          "valid": path.exists() and not errs, "errors": errs[:1]})
    return {"found": any(a["valid"] for a in artifacts), "declared_set": declared,
            "artifacts": artifacts, "errors": []}


@_collect
def _provenance(repo_root: Path, sid: str) -> dict:
    from qor.scripts import gate_provenance as gp, tier_guard

    sess = repo_root / ".qor" / "gates" / sid
    declared = tier_guard.declared_artifacts(sess / "plan.json")
    sidecars = []
    for ph in declared:
        art = sess / f"{ph}.json"
        side = sess / f"{ph}.provenance"
        if not (art.exists() and side.exists()):
            sidecars.append({"phase": ph, "payload_ok": False, "errors": ["missing"]})
            continue
        meta = json.loads(side.read_text(encoding="utf-8"))
        ok = gp.payload_digest(art.read_bytes()) == meta.get("payload_sha256")
        sidecars.append({"phase": ph, "payload_ok": ok, "errors": []})
    return {"found": any(s["payload_ok"] for s in sidecars), "sidecars": sidecars,
            "errors": []}


@_collect
def _audit_history(repo_root: Path, sid: str) -> dict:
    path = repo_root / ".qor" / "gates" / sid / "audit_history.jsonl"
    if not path.is_file():
        return {"found": False, "errors": []}
    events = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return {"found": True, "path": str(path), "events": len(events), "errors": []}


@_collect
def _intent_lock(repo_root: Path, sid: str) -> dict:
    path = repo_root / ".qor" / "intent-lock" / f"{sid}.json"
    if not path.is_file():
        return {"found": False, "errors": []}
    return {"found": True, "path": str(path), "errors": []}


@_collect
def _shadow_events(repo_root: Path, sid: str) -> dict:
    matching = 0
    scanned = False
    for name in ("PROCESS_SHADOW_GENOME.md", "PROCESS_SHADOW_GENOME_UPSTREAM.md"):
        path = repo_root / "docs" / name
        if not path.is_file():
            continue
        scanned = True
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("{") and f'"{sid}"' in line:
                matching += 1
    if not scanned:
        return {"found": False, "errors": []}
    return {"found": matching > 0, "matching_events": matching, "errors": []}


@_collect
def _changelog(repo_root: Path, phase_num: int, version: str | None) -> dict:
    text = (repo_root / "CHANGELOG.md").read_text(encoding="utf-8")
    phase_cited = f"Phase {phase_num}" in text
    version_present = bool(version) and f"## [{version}]" in text
    return {"found": phase_cited or version_present, "version": version,
            "phase_cited": phase_cited, "errors": []}


@_collect
def _seal_commit(repo_root: Path, version: str | None) -> dict:
    if not version:
        return {"found": False, "errors": []}
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-list", "-n", "1", f"v{version}"],
        capture_output=True, text=True, check=False,
    )
    sha = result.stdout.strip()
    return {"found": result.returncode == 0 and bool(sha),
            "tag": f"v{version}", "commit_sha": sha or None, "errors": []}


def assemble(repo_root: Path, sid: str, phase_num: int) -> dict:
    repo_root = Path(repo_root)
    ledger = _ledger_entry(repo_root, sid, phase_num)
    sess = repo_root / ".qor" / "gates" / sid
    version = None
    sub = sess / "substantiate.json"
    if sub.is_file():
        try:
            version = json.loads(sub.read_text(encoding="utf-8")).get("version")
        except (OSError, json.JSONDecodeError):
            version = None
    signals = {
        "ledger_entry": ledger,
        "gate_artifacts": _gate_artifacts(repo_root, sid),
        "provenance": _provenance(repo_root, sid),
        "audit_history": _audit_history(repo_root, sid),
        "intent_lock": _intent_lock(repo_root, sid),
        "shadow_events": _shadow_events(repo_root, sid),
        "changelog": _changelog(repo_root, phase_num, version),
        "seal_commit": _seal_commit(repo_root, version),
    }
    missing = sorted(k for k, v in signals.items() if not v.get("found"))
    return {
        "schema_version": "1",
        "ts": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "query": {"session_id": sid, "phase_num": phase_num},
        "signals": signals,
        "completeness": {"total": len(signals), "found": len(signals) - len(missing),
                         "missing": missing},
        "errors": [],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--session", help="session id to reconstruct")
    group.add_argument("--phase", type=int, help="sealed phase number to reconstruct")
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args(argv)
    ledger_path = args.repo_root / "docs" / "META_LEDGER.md"
    if not ledger_path.is_file():
        print(f"FAIL: ledger not found: {ledger_path}")
        return 1
    resolved = resolve_query(ledger_path.read_text(encoding="utf-8"),
                             session=args.session, phase=args.phase)
    if resolved is None:
        print("FAIL: no SESSION SEAL entry matches the query")
        return 1
    phase_num, sid = resolved
    bundle = assemble(args.repo_root, sid, phase_num)
    comp = bundle["completeness"]
    print(f"evidence bundle: phase {phase_num} session {sid} -- "
          f"{comp['found']}/{comp['total']} signals reconstructed"
          + (f"; missing: {', '.join(comp['missing'])}" if comp["missing"] else ""))
    print(json.dumps(bundle))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
