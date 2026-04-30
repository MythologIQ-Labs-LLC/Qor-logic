"""Phase 52: defensive wiring tests for /qor-substantiate Step 7.4 + Step 7.8."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"


def _read() -> str:
    return SKILL.read_text(encoding="utf-8")


def _proximity(body: str, header_re: str, phrase_re: str, span: int = 2500) -> bool:
    m = re.search(header_re, body, re.MULTILINE)
    if not m:
        return False
    window = body[m.end(): m.end() + span]
    return re.search(phrase_re, window, re.IGNORECASE | re.DOTALL) is not None


def _strip_section(body: str, header_re: str, span: int = 4000) -> str:
    m = re.search(header_re, body, re.MULTILINE)
    if not m:
        return body
    start = m.end()
    end = min(len(body), start + span)
    filler = "\n# stripped\n" * ((end - start) // 12 + 1)
    return body[:start] + filler[: end - start] + body[end:]


# --- Step 7.4: SSDF emission ---

STEP_7_4_RE = r"^### Step 7\.4: SSDF tag emission"


def test_step_7_4_invokes_ssdf_tagger_module_form():
    body = _read()
    assert _proximity(body, STEP_7_4_RE, r"python -m qor\.scripts\.ssdf_tagger", span=2500)
    assert _proximity(body, STEP_7_4_RE, r"--change-class", span=2500)


def test_step_7_4_negative_path():
    body = _read()
    mutated = _strip_section(body, STEP_7_4_RE)
    assert not _proximity(mutated, STEP_7_4_RE, r"ssdf_tagger", span=2500)


def test_step_7_4_does_not_use_python_c_shell_interpolation():
    """SG-Phase47-A countermeasure: no `python -c "...${VAR}..."` in Step 7.4 body."""
    body = _read()
    m = re.search(STEP_7_4_RE, body, re.MULTILINE)
    assert m, "Step 7.4 header must exist"
    next_step = re.search(r"^### Step 7\.5", body[m.end():], re.MULTILINE)
    section = body[m.end(): m.end() + (next_step.start() if next_step else 2500)]
    # The interpolation pattern is `python -c "..." with $VAR inside the quotes
    # The Step 7.4 prose mentions "$CHANGE_CLASS" only as argv argument (separate),
    # not interpolated into a -c literal. Probe for the forbidden pattern.
    forbidden = re.search(r'python -c "[^"]*\$\{[A-Z_]+\}', section)
    assert forbidden is None, (
        f"Step 7.4 must not interpolate ${{VAR}} into python -c literals "
        f"(SG-Phase47-A countermeasure); found: {forbidden.group(0) if forbidden else None}"
    )


def test_step_7_4_runs_between_step_7_and_step_7_5():
    body = _read()
    m_7 = re.search(r"^### Step 7: Final Merkle Seal", body, re.MULTILINE)
    m_7_4 = re.search(STEP_7_4_RE, body, re.MULTILINE)
    m_7_5 = re.search(r"^### Step 7\.5", body, re.MULTILINE)
    assert m_7 and m_7_4 and m_7_5
    assert m_7.start() < m_7_4.start() < m_7_5.start()


def test_step_7_4_documents_grandfathering():
    body = _read()
    assert _proximity(body, STEP_7_4_RE, r"grandfather|forward.only", span=2500)
    assert _proximity(body, STEP_7_4_RE, r"Phase 52", span=2500)


# --- Step 7.8: gate-chain completeness ---

STEP_7_8_RE = r"^### Step 7\.8: Gate-chain completeness"


def test_step_7_8_invokes_gate_chain_completeness():
    body = _read()
    assert _proximity(body, STEP_7_8_RE, r"gate_chain_completeness", span=2500)
    assert _proximity(body, STEP_7_8_RE, r"phase-min 52", span=2500)
    assert _proximity(body, STEP_7_8_RE, r"ABORT", span=2500)


def test_step_7_8_runs_between_step_7_7_and_step_8():
    body = _read()
    m_7_7 = re.search(r"^### Step 7\.7", body, re.MULTILINE)
    m_7_8 = re.search(STEP_7_8_RE, body, re.MULTILINE)
    m_8 = re.search(r"^### Step 8: Cleanup Staging", body, re.MULTILINE)
    assert m_7_7 and m_7_8 and m_8
    assert m_7_7.start() < m_7_8.start() < m_8.start()


def test_step_7_8_negative_path():
    body = _read()
    mutated = _strip_section(body, STEP_7_8_RE)
    assert not _proximity(mutated, STEP_7_8_RE, r"gate_chain_completeness", span=2500)


def test_step_7_8_provenance_env_var_set():
    """Step 7.8's bash sets QOR_SKILL_ACTIVE=substantiate before invoking the check.

    Without this, the (Phase 52) provenance binding on write_gate_artifact would
    refuse calls from this step's helper invocations.
    """
    body = _read()
    assert _proximity(body, STEP_7_8_RE, r"QOR_SKILL_ACTIVE=substantiate", span=2500)
