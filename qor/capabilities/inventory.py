"""Phase 58: static inventory of QorLogic capabilities."""
from __future__ import annotations

from pathlib import Path

from qor.capabilities.types import Capability


KNOWN_CAPABILITIES: tuple[Capability, ...] = (
    Capability(
        id="audit-tribunal",
        skill="qor-audit",
        phase="audit",
        inputs=("plan markdown",),
        outputs=("AUDIT_REPORT.md", "audit gate artifact"),
        risk_level="L2",
    ),
    Capability(
        id="implement-pass",
        skill="qor-implement",
        phase="implement",
        inputs=("PASS audit verdict", "plan blueprint"),
        outputs=("source + tests", "implement gate artifact"),
        risk_level="L2",
    ),
    Capability(
        id="substantiate-seal",
        skill="qor-substantiate",
        phase="substantiate",
        inputs=("implement gate artifact",),
        outputs=("META_LEDGER seal entry", "Merkle chain hash", "annotated tag"),
        risk_level="L3",
    ),
    Capability(
        id="validate-chain",
        skill="qor-validate",
        phase="validate",
        inputs=("META_LEDGER.md",),
        outputs=("chain verification result",),
        risk_level="L1",
    ),
    Capability(
        id="remediate-pattern",
        skill="qor-remediate",
        phase="remediate",
        inputs=("repeated-VETO pattern", "shadow genome events"),
        outputs=("remediation proposal", "addressed events"),
        risk_level="L2",
    ),
    Capability(
        id="policy-check",
        skill="qor-policy",
        phase="gate",
        inputs=("request JSON",),
        outputs=("cedar decision",),
        risk_level="L2",
    ),
    Capability(
        id="doc-integrity",
        skill="qor-substantiate",
        phase="substantiate",
        inputs=("plan gate artifact", "glossary"),
        outputs=("doc-integrity verdict",),
        risk_level="L2",
    ),
    Capability(
        id="ledger-verify",
        skill="qorlogic verify-ledger",
        phase="cli",
        inputs=("META_LEDGER.md",),
        outputs=("per-entry verification status",),
        risk_level="L2",
    ),
    Capability(
        id="install-freshness",
        skill="qor-plan",
        phase="session-start",
        inputs=("pyproject.toml",),
        outputs=("qor_logic_stale_install shadow event", "also invoked by qor-audit and qor-implement"),
        risk_level="L1",
    ),
    Capability(
        id="feature-inventory",
        skill="qor-substantiate",
        phase="substantiate",
        inputs=("FEATURE_INDEX.md", "prior seal snapshot"),
        outputs=("status tally", "newly_unverified list"),
        risk_level="L2",
    ),
    Capability(
        id="filter-stage-ordering",
        skill="qor-audit",
        phase="audit",
        inputs=("Python source",),
        outputs=("composition-defect findings",),
        risk_level="L2",
    ),
    Capability(
        id="sdk-alignment",
        skill="qor-audit",
        phase="audit",
        inputs=("plan SDK claims", "local evidence"),
        outputs=("infrastructure-mismatch findings",),
        risk_level="L2",
    ),
    Capability(
        id="documentation-touches",
        skill="qor-implement",
        phase="implement",
        inputs=("plan doc_tier", "touched files"),
        outputs=("documentation_touches gate field",),
        risk_level="L1",
    ),
    Capability(
        id="hash-integrity",
        skill="qor-substantiate",
        phase="substantiate",
        inputs=("seal-time hashes",),
        outputs=("hash validation verdict",),
        risk_level="L3",
    ),
    Capability(
        id="federated-ledger-fragments",
        skill="qor-substantiate",
        phase="federation",
        inputs=("worker ts + session_id + target + content_hash",),
        outputs=("le_<uid> fragment files",),
        risk_level="L2",
    ),
)


def build_inventory(repo_root: Path | str = ".") -> tuple[Capability, ...]:
    """Return the static inventory of known capabilities. ``repo_root`` is
    accepted for future extension when per-repo customization lands."""
    _ = Path(repo_root)
    return KNOWN_CAPABILITIES
