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
) -> dict:
    """Assemble a qa.json payload.

    ``verdict`` is FAIL iff any pillar status is ``"fail"``; otherwise PASS
    (``skip`` does not fail the verdict, but is visible per-pillar).
    """
    overrides = {"security": security, "stability": stability, "coverage": coverage}
    pillars: dict[str, dict] = {"regression": _regression_pillar(regression_summary)}
    for name in ("security", "stability", "coverage"):
        if overrides[name] is not None:
            pillars[name] = overrides[name]
        else:
            pillars[name] = {"status": "skip", "note": _DEFERRED_NOTE[name]}

    verdict = "FAIL" if any(p["status"] == "fail" for p in pillars.values()) else "PASS"

    payload: dict = {"phase": "qa", "verdict": verdict, "pillars": pillars}
    if ts is not None:
        payload["ts"] = ts
    if session_id is not None:
        payload["session_id"] = session_id
    return payload


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
