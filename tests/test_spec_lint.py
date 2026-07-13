"""Phase 190 (GH #239 Phase A): spec grammar lint."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qor.scripts.spec_lint import check

REPO_ROOT = Path(__file__).resolve().parent.parent

VALID_SPEC = """# Capability: gate-chain

### Requirement: Artifacts are immutable
The system SHALL never rewrite a versioned gate artifact after it is written.

#### Scenario: Rerun does not mutate
- GIVEN a sealed phase with a versioned artifact on disk
- WHEN the same phase runs again
- THEN a new iteration file is written and the sealed bytes are unchanged

### Requirement: Latest iteration resolves
The resolver MUST return the highest iteration file for a phase.

#### Scenario: Two iterations exist
- GIVEN iter1 and iter2 artifacts for the plan phase
- WHEN the latest artifact path is resolved
- THEN the iter2 path is returned
"""


def test_valid_spec_passes():
    assert check(VALID_SPEC) == []


def test_missing_rfc2119_flagged():
    text = VALID_SPEC.replace(
        "The system SHALL never rewrite", "The system never rewrites"
    )
    findings = check(text)
    assert len(findings) == 1
    assert findings[0].code == "missing-rfc2119"
    assert "Artifacts are immutable" in findings[0].message


def test_double_rfc2119_flagged():
    text = VALID_SPEC.replace(
        "The system SHALL never rewrite a versioned gate artifact after it is written.",
        "The system SHALL never rewrite artifacts. It MUST also log rewrites.",
    )
    findings = check(text)
    assert len(findings) == 1
    assert findings[0].code == "double-rfc2119"


def test_missing_scenario_flagged():
    text = VALID_SPEC.replace(
        """#### Scenario: Rerun does not mutate
- GIVEN a sealed phase with a versioned artifact on disk
- WHEN the same phase runs again
- THEN a new iteration file is written and the sealed bytes are unchanged

""",
        "",
    )
    findings = check(text)
    assert len(findings) == 1
    assert findings[0].code == "missing-scenario"


def test_malformed_scenario_flagged():
    text = VALID_SPEC.replace(
        "- WHEN the same phase runs again\n", ""
    )
    findings = check(text)
    assert len(findings) == 1
    assert findings[0].code == "malformed-scenario"
    assert "WHEN" in findings[0].message


def test_cli_exit_codes(tmp_path):
    good = tmp_path / "spec.md"
    good.write_text(VALID_SPEC, encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text(VALID_SPEC.replace("SHALL never rewrite", "never rewrites"), encoding="utf-8")

    ok = subprocess.run(
        [sys.executable, "-m", "qor.scripts.spec_lint", "--files", str(good)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert ok.returncode == 0, ok.stderr

    fail = subprocess.run(
        [sys.executable, "-m", "qor.scripts.spec_lint", "--files", str(bad)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert fail.returncode == 1
    assert "missing-rfc2119" in fail.stderr
