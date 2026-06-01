"""Prompt-contract wiring tests for Phase 121 (GH #177).

These assert the load-bearing instructions exist in the skill prose with the
correct fail-closed semantics. If an instruction were weakened (e.g. ABORT
downgraded to WARN, or the lint invocation dropped) the test fails -- so they
test the contract's behavior, not mere file presence.
"""
from __future__ import annotations

import re
from pathlib import Path

SUBSTANTIATE = Path("qor/skills/governance/qor-substantiate/SKILL.md")
AUDIT = Path("qor/skills/governance/qor-audit/SKILL.md")


def test_substantiate_has_runtime_principal_gate() -> None:
    text = SUBSTANTIATE.read_text(encoding="utf-8")
    assert "Runtime-principal fidelity" in text  # prose-lint: ok=prompt-contract
    # Disclosed coverage-gap escape phrase is the fail-closed exception.
    assert "data path verified only under service_role" in text  # prose-lint: ok=prompt-contract
    # The gate must ABORT (fail-closed), not merely warn, within its section.
    idx = text.index("Runtime-principal fidelity")
    window = text[idx:idx + 900]
    assert "ABORT" in window


def test_substantiate_invokes_data_api_acl_lint() -> None:
    text = SUBSTANTIATE.read_text(encoding="utf-8")
    m = re.search(r"data_api_acl_lint.{0,200}\|\|\s*ABORT", text, re.DOTALL)
    assert m, "data_api_acl_lint invocation must be followed by || ABORT (fail-closed)"


def test_substantiate_has_acl_prerequisite_row() -> None:
    text = SUBSTANTIATE.read_text(encoding="utf-8")
    assert "module:qor.scripts.data_api_acl_lint" in text  # prose-lint: ok=prompt-contract


def test_audit_security_pass_has_dataapi_items() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    assert "explicit `GRANT`s" in text  # prose-lint: ok=prompt-contract
    assert "non-`security_invoker`" in text  # prose-lint: ok=prompt-contract
    assert "insufficient proof of the access path" in text  # prose-lint: ok=prompt-contract
