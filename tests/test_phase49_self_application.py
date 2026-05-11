"""Phase 49 self-application: scan framework's own qor/scripts/.

Acceptable outcomes:
1. Empty findings — framework is clean.
2. Findings whose function names appear in _KNOWN_BENIGN_FUNCTIONS (with the
   rationale documented in the seal entry). Allowlist starts empty in V1;
   framework regressions surface as new findings until allowlisted.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts.pipeline_inversion_lint import scan_repo


_KNOWN_BENIGN_FUNCTIONS: frozenset[str] = frozenset()


def test_framework_python_scripts_have_no_unallowlisted_composition_findings():
    repo_root = Path(__file__).resolve().parent.parent / "qor" / "scripts"
    findings = scan_repo(repo_root, include_tests=False)
    not_allowlisted = [f for f in findings if f.function not in _KNOWN_BENIGN_FUNCTIONS]
    if not_allowlisted:
        lines = "\n".join(
            f"  {f.file}:{f.line}  {f.function}  shared={list(f.shared_fields)}  validator={f.validator_function}"
            for f in not_allowlisted
        )
        pytest.fail(
            "Phase 49 self-application: composition-defect candidate(s) in qor/scripts/.\n"
            "Disposition each finding and either fix the ordering or add the function "
            "to _KNOWN_BENIGN_FUNCTIONS with rationale recorded in the seal entry:\n"
            + lines
        )
