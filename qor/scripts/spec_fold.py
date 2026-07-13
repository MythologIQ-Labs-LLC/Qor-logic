"""Phase 192 (GH #277): seal-time fold of declared spec deltas.

Runs inside /qor-substantiate AFTER the reliability gates (a session that
never reaches the seal never folds -- deltas on VETO'd or unsealed work stay
unconsumed). Reads the session plan artifact's ``spec_deltas``, applies each
delta to its capability spec via ``spec_merge``, lints the folded result,
writes the spec, deletes the consumed delta (git history is the archive),
and returns the LF-normalized sha256 per capability for the seal record.

Loud by design: a merge conflict (``SpecMergeError``) or a fold that would
produce a grammar-violating spec (``FoldError``) aborts with the tree
untouched.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from qor.scripts.spec_lint import check
from qor.scripts.spec_merge import apply


class FoldError(ValueError):
    """The fold would produce an invalid spec, or inputs are malformed."""


def _lf_hash(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def _plan_spec_deltas(repo_root: Path, session_id: str) -> list[dict]:
    plan_path = repo_root / ".qor" / "gates" / session_id / "plan.json"
    if not plan_path.is_file():
        return []
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FoldError(f"plan artifact unreadable: {exc}") from exc
    deltas = plan.get("spec_deltas") or []
    if not isinstance(deltas, list):
        raise FoldError("plan spec_deltas is not a list")
    return deltas


def fold_session_deltas(repo_root: Path, session_id: str) -> dict[str, str]:
    """Fold the session's declared deltas; return {capability: spec sha256}."""
    repo_root = Path(repo_root)
    entries = _plan_spec_deltas(repo_root, session_id)
    if not entries:
        return {}

    # Stage all folds in memory first; nothing is written until every
    # capability's folded result exists and lints clean.
    staged: list[tuple[Path, Path, str, str]] = []
    for entry in entries:
        capability = entry["capability"]
        delta_path = repo_root / entry["delta_path"]
        spec_path = repo_root / "qor" / "specs" / capability / "spec.md"
        if not delta_path.is_file():
            raise FoldError(f"declared delta missing: {entry['delta_path']}")
        if not spec_path.is_file():
            raise FoldError(f"capability spec missing: {capability}")
        merged = apply(
            spec_path.read_bytes().decode("utf-8"),
            delta_path.read_bytes().decode("utf-8"),
        )
        findings = check(merged)
        if findings:
            detail = "; ".join(f"{f.code}: {f.message}" for f in findings[:3])
            raise FoldError(
                f"fold of {capability} produces an invalid spec ({detail})")
        staged.append((spec_path, delta_path, capability, merged))

    result: dict[str, str] = {}
    for spec_path, delta_path, capability, merged in staged:
        data = merged.encode("utf-8")
        spec_path.write_bytes(data)
        delta_path.unlink()
        result[capability] = _lf_hash(data)
    return result
