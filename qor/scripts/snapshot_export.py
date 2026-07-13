"""Phase 191 (GH #270): read-only repository governance snapshot export.

Composes repository-local governance facts into one versioned JSON document
(contract: ``qor/references/snapshot-contract.md``; schema:
``qor/gates/schema/repository_snapshot.schema.json``). The snapshot is a
derived read model -- ledgers and gate artifacts remain authoritative.

Fail-safe by construction: every section renders through a guard as
``{"state": "ok"|"unknown"|"error", "source": ..., ...}``; absence,
malformation, or staleness never renders as health. The exporter mutates
nothing and touches no network; exit 0 means the EXPORT succeeded, whatever
state the repository is in.

CLI:
    python -m qor.scripts.snapshot_export --repo-root . --out PATH
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1"

_SESSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{4}-[0-9a-f]{6}$")
_TAIL_RE = re.compile(
    r"\*Session: (\w+)\*\s*\(Phase (\d+); (v[\d.]+); ([^)]*)\)")
_ENTRY_RE = re.compile(r"^### Entry #(\d+): (.+?)\s*$", re.MULTILINE)
_CHAIN_HASH_RE = re.compile(r"\*\*Chain Hash \(Merkle seal\)\*\*:\s*`([0-9a-f]{64})`")
_SEAL_TITLE_RE = re.compile(
    r"^### Entry #(\d+): SESSION SEAL -- (.+?) \((v[\d.]+)\)\s*$", re.MULTILINE)
_ENTRY_ID_RE = re.compile(r"\*\*Entry ID\*\*:\s*`([0-9a-f]+)`")

_PHASES = ("research", "plan", "audit", "implement", "substantiate")


def _section(state: str, source: str | None = None, **data) -> dict:
    out = {"state": state, "source": source}
    out.update(data)
    return out


def _guarded(fn, source: str | None = None) -> dict:
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 -- fail-safe: never raise, never infer health
        return _section("error", source, reason=f"{type(exc).__name__}: {exc}")


# ----- collectors -------------------------------------------------------------

def _meta(repo_root: Path) -> dict:
    version = "unknown"
    pyproject = repo_root / "pyproject.toml"
    if pyproject.is_file():
        with pyproject.open("rb") as fh:
            version = str(tomllib.load(fh).get("project", {}).get("version", "unknown"))
    identifier = None
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "config", "--get", "remote.origin.url"],
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            identifier = proc.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        identifier = None
    return _section(
        "ok" if version != "unknown" else "unknown",
        "pyproject.toml",
        schemaVersion=SCHEMA_VERSION,
        qor_logic_version=version,
        repo_identifier=identifier,
        generated_ts=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _session(repo_root: Path) -> dict:
    marker = repo_root / ".qor" / "session" / "current"
    if not marker.is_file():
        return _section("unknown", ".qor/session/current", reason="no session marker")
    sid = marker.read_text(encoding="utf-8").strip()
    if not _SESSION_RE.match(sid):
        return _section("error", ".qor/session/current",
                        reason=f"marker does not match session pattern: {sid!r}")
    return _section("ok", ".qor/session/current", session_id=sid)


def _lifecycle(ledger_text: str) -> dict:
    match = _TAIL_RE.search(ledger_text)
    if not match:
        return _section("unknown", "docs/META_LEDGER.md",
                        reason="no session status line in ledger tail")
    return _section("ok", "docs/META_LEDGER.md",
                    disposition=match.group(1), phase=int(match.group(2)),
                    version=match.group(3), note=match.group(4))


def _ledger(repo_root: Path, ledger_text: str) -> dict:
    source = "docs/META_LEDGER.md"
    entries = _ENTRY_RE.findall(ledger_text)
    if not entries:
        return _section("unknown", source, reason="no ledger entries found")
    chain_hashes = _CHAIN_HASH_RE.findall(ledger_text)
    from qor.scripts.status_json import _module_main_runner
    rc, output = _module_main_runner(
        "qor.scripts.ledger_hash",
        ["verify", str(repo_root / "docs" / "META_LEDGER.md")])()
    verified = output.count("chain hash verified")
    if rc != 0:
        state = "error"
    elif verified == 0:
        # Fail-safe: a ledger where nothing was verifiable is NOT healthy.
        state = "unknown"
    else:
        state = "ok"
    summary = next((ln for ln in output.splitlines() if ln.strip()), "")
    return _section(
        state, source,
        entries=len(entries),
        seal_entries=sum(1 for _, title in entries if title.startswith("SESSION SEAL")),
        head_chain_hash=chain_hashes[-1] if chain_hashes else None,
        verify_exit=rc,
        verified_entries=verified,
        verify_summary=summary[:200],
    )


def _latest_seal(ledger_text: str) -> dict:
    source = "docs/META_LEDGER.md"
    seals = list(_SEAL_TITLE_RE.finditer(ledger_text))
    if not seals:
        return _section("unknown", source, reason="no SESSION SEAL entry")
    last = seals[-1]
    tail = ledger_text[last.end():]
    merkle = _CHAIN_HASH_RE.search(tail)
    entry_id = _ENTRY_ID_RE.search(tail)
    return _section("ok", source,
                    entry=int(last.group(1)), title=last.group(2),
                    version=last.group(3).lstrip("v"),
                    merkle_seal=merkle.group(1) if merkle else None,
                    entry_id=entry_id.group(1) if entry_id else None)


def _gates(repo_root: Path, session_id: str | None) -> dict:
    gates_root = repo_root / ".qor" / "gates"
    source = ".qor/gates/"
    if not gates_root.is_dir():
        return _section("unknown", source, reason="no gates directory")
    sid = session_id
    if sid is None:
        candidates = sorted(
            (d.name for d in gates_root.iterdir()
             if d.is_dir() and _SESSION_RE.match(d.name)))
        sid = candidates[-1] if candidates else None
    if sid is None or not (gates_root / sid).is_dir():
        return _section("unknown", source, reason="no session gate directory")
    from qor.scripts.validate_gate_artifact import latest_artifact_path
    phases: dict[str, dict] = {}
    found = 0
    for phase in _PHASES:
        path = latest_artifact_path(phase, gates_root / sid)
        if path is None or not path.exists():
            phases[phase] = {"state": "unknown", "reason": "no artifact"}
            continue
        found += 1
        data = json.loads(path.read_text(encoding="utf-8"))
        phases[phase] = {
            "state": "ok",
            "ts": data.get("ts"),
            "verdict": data.get("verdict"),
            "path": path.relative_to(repo_root).as_posix(),
        }
    if not found:
        return _section("unknown", f".qor/gates/{sid}/",
                        reason="session gate directory has no artifacts",
                        session_id=sid, phases=phases)
    return _section("ok", f".qor/gates/{sid}/", session_id=sid, phases=phases)


def _health(repo_root: Path) -> dict:
    from qor.scripts.status_json import default_registry, run_all
    report = run_all(default_registry(repo_root))
    return _section("ok", None,
                    checks=report["checks"], overall_ok=report["overall_ok"])


def _shadow(repo_root: Path) -> dict:
    log = repo_root / "docs" / "PROCESS_SHADOW_GENOME_UPSTREAM.md"
    source = "docs/PROCESS_SHADOW_GENOME_UPSTREAM.md"
    if not log.is_file():
        return _section("unknown", source, reason="no shadow log")
    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    unaddressed: list[dict] = []
    total = 0
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        etype = str(event.get("event_type", "unknown"))
        sev = str(event.get("severity", "unknown"))
        by_type[etype] = by_type.get(etype, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1
        if event.get("addressed") is False:
            unaddressed.append({
                "id": str(event.get("id", ""))[:12],
                "event_type": etype,
                "severity": event.get("severity"),
                "skill": event.get("skill"),
            })
    if total == 0:
        return _section("unknown", source, reason="shadow log has no events")
    return _section("ok", source, total=total, by_type=by_type,
                    by_severity=by_severity, unaddressed=len(unaddressed),
                    unaddressed_events=unaddressed)


def _drift(repo_root: Path) -> dict:
    from qor.scripts.status_json import Check, run_check
    doc = run_check(Check(
        id="doc-currency", module="qor.scripts.doc_integrity_strict",
        argv=["--repo-root", str(repo_root)]))
    install = run_check(Check(
        id="install-drift", module="qor.scripts.install_drift_check",
        argv=["--host", "claude", "--scope", "repo"]))
    return _section(
        "ok" if doc["ok"] else "error", None,
        doc_currency={"ok": doc["ok"], "exit": doc["exit"], "summary": doc["summary"]},
        install={"state": "ok" if install["ok"] else "unknown",
                 "exit": install["exit"], "summary": install["summary"]},
    )


def _findings(health: dict, shadow: dict) -> dict:
    items: list[dict] = []
    for check in health.get("checks", []) or []:
        if not check.get("ok", True):
            items.append({"kind": "health-check", "id": check["id"],
                          "summary": check.get("summary", ""),
                          "source": "status_json ladder"})
    for event in shadow.get("unaddressed_events", []) or []:
        items.append({"kind": "shadow-event", **event,
                      "source": shadow.get("source")})
    return _section("ok", None, count=len(items), items=items)


# ----- assembly ---------------------------------------------------------------

def build_snapshot(repo_root: Path) -> dict:
    repo_root = Path(repo_root)
    ledger_path = repo_root / "docs" / "META_LEDGER.md"
    ledger_text = ""
    if ledger_path.is_file():
        ledger_text = ledger_path.read_text(encoding="utf-8", errors="replace")

    session = _guarded(lambda: _session(repo_root), ".qor/session/current")
    health = _guarded(lambda: _health(repo_root))
    shadow = _guarded(lambda: _shadow(repo_root),
                      "docs/PROCESS_SHADOW_GENOME_UPSTREAM.md")
    return {
        "meta": _guarded(lambda: _meta(repo_root), "pyproject.toml"),
        "session": session,
        "lifecycle": _guarded(lambda: _lifecycle(ledger_text), "docs/META_LEDGER.md"),
        "gates": _guarded(lambda: _gates(repo_root, session.get("session_id")),
                          ".qor/gates/"),
        "ledger": _guarded(lambda: _ledger(repo_root, ledger_text),
                           "docs/META_LEDGER.md"),
        "latest_seal": _guarded(lambda: _latest_seal(ledger_text),
                                "docs/META_LEDGER.md"),
        "health": health,
        "shadow": shadow,
        "drift": _guarded(lambda: _drift(repo_root)),
        "findings": _guarded(lambda: _findings(health, shadow)),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="qor.scripts.snapshot_export",
                                 description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--out", type=Path, default=None,
                    help="write the snapshot here (default: stdout)")
    ap.add_argument("--indent", type=int, default=2)
    args = ap.parse_args(argv)

    try:
        snapshot = build_snapshot(args.repo_root)
        rendered = json.dumps(snapshot, indent=args.indent, sort_keys=True) + "\n"
    except Exception as exc:  # noqa: BLE001 -- the export itself failed
        print(f"SNAPSHOT EXPORT ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
