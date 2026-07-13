"""QA evidence artifact builder/writer (Phase 114, GH #166).

Emits a compact, schema-validated ``qa.json`` gate artifact recording per-pillar
verification status plus an overall verdict, readable by the acceptance-criteria
close guard (``ac_close_guard``) at substantiation.

Spine slice (#166): the ``regression`` pillar is derived from a real
``feature_index_verify.IndexSummary``; ``security``/``stability``/``coverage``
are emitted with ``status="skip"`` and a ``note`` naming their follow-on issue.
This is explicit partial coverage (anti-half-measure), not silent omission.

The artifact is off-CHAIN (like ``remediate``); the close guard reads it via
``gate_chain.read_phase_artifact("qa", session_id=sid)``.

Doctrine: ``qor/references/doctrine-verification-closure-integrity.md``.
Stdlib-only except the qor toolkit.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts.feature_index_verify import IndexSummary

PILLARS = ("regression", "security", "stability", "coverage")

# Follow-on issues for the pillars deferred in the Phase 114 spine slice.
_DEFERRED_NOTE = {
    "security": "deferred: SAST pillar follow-on (secret-scan/SBOM/OWASP already live)",
    "stability": "deferred: seal-time runtime-contract re-walk follow-on (#108)",
    "coverage": "deferred: coverage-posture pillar follow-on",
}


def _regression_pillar(summary: IndexSummary | None) -> dict:
    if summary is None:
        return {"status": "skip", "note": "no FEATURE_INDEX summary supplied"}
    if summary.missing_index:
        return {"status": "skip", "note": "FEATURE_INDEX.md absent"}
    if summary.newly_unverified:
        return {
            "status": "fail",
            "metric": float(len(summary.newly_unverified)),
            "note": "outside-scope regression(s): " + ", ".join(summary.newly_unverified),
        }
    return {"status": "pass", "metric": float(summary.verified)}


def build_payload(
    regression_summary: IndexSummary | None = None,
    *,
    security: dict | None = None,
    stability: dict | None = None,
    coverage: dict | None = None,
    session_id: str | None = None,
    ts: str | None = None,
    policy: str = "adoption",
    required_pillars: set[str] | frozenset[str] | None = None,
) -> dict:
    """Assemble a qa.json payload.

    Under the default ``adoption`` policy ``verdict`` is FAIL iff any pillar
    status is ``"fail"``; otherwise PASS (``skip`` does not fail the verdict,
    but is visible per-pillar). Phase 177 (GH #269): under
    ``policy="production"`` every pillar named in ``required_pillars`` must be
    ``"pass"`` -- a required ``skip`` (or ``fail``) fails the verdict, so
    skipped security/stability/coverage evidence cannot yield a
    production-grade PASS. Production with an empty required set is a
    misconfiguration and raises ``ValueError``. Adoption payloads are
    byte-identical to the pre-177 output (no new keys).
    """
    if policy not in ("adoption", "production"):
        raise ValueError(f"unknown qa policy: {policy!r}")
    required = frozenset(required_pillars or ())
    if policy == "production":
        if not required:
            raise ValueError(
                "policy='production' requires a non-empty required_pillars set"
            )
        unknown = required - set(PILLARS)
        if unknown:
            raise ValueError(f"unknown required pillars: {sorted(unknown)}")

    overrides = {"security": security, "stability": stability, "coverage": coverage}
    pillars: dict[str, dict] = {"regression": _regression_pillar(regression_summary)}
    for name in ("security", "stability", "coverage"):
        if overrides[name] is not None:
            pillars[name] = overrides[name]
        else:
            pillars[name] = {"status": "skip", "note": _DEFERRED_NOTE[name]}

    failed = any(p["status"] == "fail" for p in pillars.values())
    if policy == "production":
        required_unmet = any(
            pillars.get(name, {}).get("status") != "pass" for name in required
        )
        verdict = "FAIL" if failed or required_unmet else "PASS"
    else:
        verdict = "FAIL" if failed else "PASS"

    payload: dict = {"phase": "qa", "verdict": verdict, "pillars": pillars}
    if policy == "production":
        payload["policy"] = "production"
        payload["required_pillars"] = sorted(required)
    if ts is not None:
        payload["ts"] = ts
    if session_id is not None:
        payload["session_id"] = session_id
    return payload


def run_sast(paths: tuple[str, ...] = ("qor",), backend: str = "bandit") -> dict:
    """Convenience: run the SAST sub-check and return a security-pillar dict.

    Degrades to ``{"status": "skip", ...}`` when the backend tool is absent
    (Phase 115; GH #167). Pass the result as ``build_payload(security=...)``.
    """
    from qor.scripts import sast_scan

    return sast_scan.scan(list(paths), backend=backend)


def coverage_pillar(total_pct: float, *, min_pct: float = 80.0) -> dict:
    """Coverage pillar (Phase 116; #168): pass at/above threshold, else fail."""
    return {"status": "pass" if total_pct >= min_pct else "fail", "metric": float(total_pct)}


def run_coverage(data_file: str = ".coverage", min_pct: float = 80.0) -> dict:
    """Read an existing coverage data file -> coverage pillar; skip when absent.

    Does NOT re-run the suite (Phase 75 graceful-skip when no data present).
    """
    if not Path(data_file).exists():
        return {"status": "skip", "note": f"no coverage data at {data_file}"}
    import io
    import coverage

    cov = coverage.Coverage(data_file=data_file)
    cov.load()
    total = cov.report(file=io.StringIO())
    return coverage_pillar(float(total), min_pct=min_pct)


def run_stability(plan_path: str, repo_root: str = ".") -> dict:
    """Stability pillar (Phase 116; #169): re-walk the plan's runtime contract at
    seal time, reusing ``runtime_contract_walk`` (#108). Skip when the plan is absent.
    """
    from qor.scripts import runtime_contract_walk

    if not Path(plan_path).exists():
        return {"status": "skip", "note": "plan absent"}
    findings = runtime_contract_walk.walk_plan(Path(plan_path), Path(repo_root))
    if findings:
        return {"status": "fail", "metric": float(len(findings)),
                "note": f"{len(findings)} runtime-contract finding(s)"}
    return {"status": "pass", "metric": 0.0}


def write(
    session_id: str | None = None,
    regression_summary: IndexSummary | None = None,
    **pillar_overrides: dict,
) -> Path:
    """Build and write the qa.json gate artifact for ``session_id``.

    Imports the gate toolkit lazily so ``build_payload`` stays usable without
    a session context (and so unit tests need not touch the gate dir).
    """
    from qor.scripts import gate_chain, ai_provenance, session, shadow_process

    sid = session_id or session.get_or_create()
    payload = build_payload(
        regression_summary,
        session_id=sid,
        ts=shadow_process.now_iso(),
        **pillar_overrides,
    )
    manifest = ai_provenance.build_manifest(
        "qa", human_oversight=ai_provenance.HumanOversight.ABSENT
    )
    return gate_chain.write_gate_artifact(
        phase="qa", payload=payload, session_id=sid, ai_provenance=manifest, skill="qa"
    )
