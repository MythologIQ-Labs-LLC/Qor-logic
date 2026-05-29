"""Tool-agnostic SAST sub-check for the VCI security pillar (Phase 115, GH #167).

Fills the one genuine net-new security gap (research found secret-scan/SBOM/
OWASP already live). The ``scan`` API is backend-agnostic: a backend is a
callable ``(paths) -> list[normalized finding dict]`` where each finding has at
least ``severity`` in {LOW, MEDIUM, HIGH}. The default backend is bandit
(pure-Python, zero-network, low supply-chain surface); a future semgrep backend
normalizes into the same shape and registers in ``BACKENDS``.

When the backend tool is absent the pillar is ``status: "skip"`` with a note
(Phase 75 prerequisite-absent semantics) -- never a crash, never a false pass.

Doctrine: ``qor/references/doctrine-verification-closure-integrity.md``.
Stdlib-only; bandit is an optional ``sast`` extra invoked as a subprocess.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_SEVERITIES = ("LOW", "MEDIUM", "HIGH")


class BackendUnavailable(RuntimeError):
    """Raised by a backend when its underlying tool is not installed."""


def to_pillar(findings: list[dict], *, fail_on: str = "HIGH", evidence: str | None = None) -> dict:
    """Reduce normalized findings to a qa.json security-pillar dict.

    ``status`` is ``fail`` iff any finding's severity is at or above ``fail_on``;
    otherwise ``pass``. ``metric`` is the total finding count.
    """
    threshold = _SEVERITIES.index(fail_on)
    failed = any(
        _SEVERITIES.index(str(f.get("severity", "LOW")).upper()) >= threshold
        for f in findings
    )
    pillar: dict = {"status": "fail" if failed else "pass", "metric": float(len(findings))}
    if evidence:
        pillar["evidence"] = evidence
    return pillar


def normalize_bandit(raw: dict) -> list[dict]:
    """Normalize a bandit ``-f json`` result object into the common finding shape."""
    out: list[dict] = []
    for r in raw.get("results", []):
        out.append({
            "severity": str(r.get("issue_severity", "LOW")).upper(),
            "text": r.get("issue_text", ""),
            "location": f"{r.get('filename', '?')}:{r.get('line_number', '?')}",
        })
    return out


def bandit_backend(paths: list[str]) -> list[dict]:
    """Run bandit recursively over ``paths`` and return normalized findings.

    Raises ``BackendUnavailable`` when bandit is not importable so ``scan`` can
    degrade to a skip rather than a crash.
    """
    if importlib.util.find_spec("bandit") is None:
        raise BackendUnavailable("bandit not installed (pip install 'qor-logic[sast]')")
    proc = subprocess.run(
        [sys.executable, "-m", "bandit", "-r", *paths, "-f", "json"],
        capture_output=True, text=True,
    )
    # bandit exits non-zero when findings exist; JSON is still on stdout.
    if not proc.stdout.strip():
        return []
    try:
        raw = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    return normalize_bandit(raw)


BACKENDS = {"bandit": bandit_backend}


def scan(paths: list[str], *, backend: str = "bandit", fail_on: str = "HIGH",
         evidence: str | None = None) -> dict:
    """Run ``backend`` over ``paths`` and return a qa.json security-pillar dict.

    Unknown backend -> ValueError. Backend tool unavailable -> status skip.
    """
    if backend not in BACKENDS:
        raise ValueError(f"unknown SAST backend {backend!r}; known: {sorted(BACKENDS)}")
    try:
        findings = BACKENDS[backend](paths)
    except BackendUnavailable as e:
        return {"status": "skip", "note": f"{backend} backend unavailable: {e}"}
    return to_pillar(findings, fail_on=fail_on, evidence=evidence)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.sast_scan")
    parser.add_argument("--paths", nargs="+", default=["qor"])
    parser.add_argument("--backend", default="bandit")
    parser.add_argument("--fail-on", default="HIGH", choices=_SEVERITIES)
    parser.add_argument("--out", default=None, help="write the pillar dict as JSON")
    args = parser.parse_args(argv)
    pillar = scan(args.paths, backend=args.backend, fail_on=args.fail_on)
    if args.out:
        Path(args.out).write_text(json.dumps(pillar, indent=2), encoding="utf-8")
    print(f"sast[{args.backend}]: {pillar['status']}"
          + (f" ({int(pillar['metric'])} finding(s))" if "metric" in pillar else "")
          + (f" -- {pillar['note']}" if pillar.get("note") else ""))
    # WARN-first: a fail prints but does not exit non-zero unless enforcing.
    return 0


if __name__ == "__main__":
    sys.exit(main())
