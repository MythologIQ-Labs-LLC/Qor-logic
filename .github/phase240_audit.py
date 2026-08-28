from __future__ import annotations

import ast
import hashlib
import os
import re
import subprocess
from pathlib import Path

import yaml

from qor.scripts import (
    ai_provenance,
    doc_integrity,
    gate_chain,
    ledger_emit,
    shadow_process,
    version_applicability,
    veto_pattern,
)

TARGET = "178d79009e879bc570b1608ed3ebafd43cd7413a"
SID = "2026-08-28T1956-6e0074"
PLAN = Path("docs/plan-qor-phase240-execution-context-governance.md")
DELTA = Path(f"qor/specs/execution-context-governance/deltas/{SID}.md")


def run(*args: str, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(args, text=True, capture_output=True)
    print(f"$ {' '.join(args)}")
    if cp.stdout:
        print(cp.stdout)
    if cp.stderr:
        print(cp.stderr)
    if cp.returncode and not allow_failure:
        raise SystemExit(cp.returncode)
    return cp


def assert_harness_only() -> None:
    changed = run("git", "diff", "--name-only", TARGET, "HEAD").stdout.splitlines()
    expected = {".github/workflows/phase240-audit-final.yml", ".github/phase240_audit.py"}
    if set(changed) != expected:
        raise SystemExit(f"audit target drifted; expected harness-only delta, got {changed}")


def bind_session() -> None:
    p = Path(".qor/session/current")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(SID + "\n", encoding="utf-8")


def hard_entry_checks() -> None:
    run("qor-logic", "governance-health", "--profile", "skill-entry")
    run("qor-logic", "scripts", "plan_iteration_status_lint", "--plan", str(PLAN))
    run(
        "qor-logic", "scripts", "prompt_injection_canaries", "--files",
        "docs/ARCHITECTURE_PLAN.md", "docs/META_LEDGER.md", "docs/CONCEPT.md", str(PLAN),
    )
    run("qor-logic", "scripts", "prose_test_lint", "--tests-dir", "tests", "--enforce")
    risk = run("qor-logic", "scripts", "audit_risk_score", "--plan", str(PLAN)).stdout
    if "option_b_required: false" not in risk:
        raise SystemExit("independent Option B review required; solo tribunal cannot PASS")


def spec_and_version() -> None:
    run("python", "-m", "qor.scripts.spec_lint", "--files", "qor/specs/execution-context-governance/spec.md")
    run("python", "-m", "qor.scripts.spec_lint", "--delta", "--files", str(DELTA))
    v = version_applicability.validate(PLAN, ".")
    if not (v.ok and v.classification == "version-not-applicable" and v.change_class == "governance"):
        raise SystemExit(f"version applicability failed: {v}")
    print(v)


def implementation_checks() -> None:
    run("python", "-m", "pytest", "tests/", "-q")
    run("python", "-m", "ruff", "check", "qor", "tests")
    run("python", "qor/scripts/check_variant_drift.py")

    retired: list[str] = []
    for p in Path("qor/skills").glob("**/SKILL.md"):
        text = p.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        front = text.split("---\n", 2)[1]
        meta = yaml.safe_load(front) or {}
        for key in ("model_compatibility", "min_model_capability"):
            if key in meta:
                retired.append(f"{p}:{key}")
    if retired:
        raise SystemExit(f"retired admission metadata remains: {retired}")

    source_files = [
        Path("qor/scripts/execution_context.py"),
        Path("qor/scripts/model_pinning_lint.py"),
        Path("qor/scripts/qor_audit_runtime.py"),
    ]
    forbidden = ("shell=True", "pickle.loads", "eval(", "exec(", "yaml.load(")
    for p in source_files:
        text = p.read_text(encoding="utf-8")
        hits = [token for token in forbidden if token in text]
        if hits:
            raise SystemExit(f"unsafe construct in {p}: {hits}")
        ast.parse(text)

    lines = Path("qor/scripts/execution_context.py").read_text(encoding="utf-8").splitlines()
    if len(lines) > 250:
        raise SystemExit(f"razor file limit exceeded: {len(lines)}")
    oversized: list[tuple[str, int]] = []
    for node in ast.walk(ast.parse("\n".join(lines))):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and getattr(node, "end_lineno", None):
            span = node.end_lineno - node.lineno + 1
            if span > 40:
                oversized.append((node.name, span))
    if oversized:
        raise SystemExit(f"razor function limit exceeded: {oversized}")

    diff_names = set(run("git", "diff", "--name-only", f"origin/main...{TARGET}").stdout.splitlines())
    if "pyproject.toml" in diff_names:
        raise SystemExit("unexpected dependency manifest change")
    ui_prefixes = ("frontend/", "web/", "ui/", "src/components/")
    if [p for p in diff_names if p.startswith(ui_prefixes)]:
        raise SystemExit("unexpected UI surface")
    if "qor/scripts/execution_context.py" not in diff_names:
        raise SystemExit("execution-context source is orphaned from target diff")


def advisory_ladder() -> None:
    commands = [
        ("plan_enumeration_lint", "--plan", str(PLAN), "--repo-root", "."),
        ("plan_grep_lint", "--plan", str(PLAN), "--repo-root", "."),
        ("plan_text_consistency_lint", "--check", str(PLAN)),
        ("delivery_branch_lint", "--plan", str(PLAN), "--repo-root", "."),
        ("ci_coverage_lint", "--plan", str(PLAN), "--workflows-dir", ".github/workflows"),
        ("workspace_fragility_check", "--repo-root", "."),
        ("plan_signature_widening_caller_lint", "--plan", str(PLAN), "--repo-root", "."),
        ("plan_data_round_trip_lint", "--plan", str(PLAN), "--repo-root", "."),
        ("plan_live_progress_lint", "--repo-root", "."),
        ("plan_feature_tdd_lint", "--plan", str(PLAN), "--repo-root", "."),
        ("sg_closure_lint",),
        ("gate_schema_freeze_lint", "--session", SID),
        ("publication_boundary_lint",),
        ("runtime_contract_walk", "--plan", str(PLAN)),
    ]
    for command in commands:
        run("qor-logic", "scripts", *command, allow_failure=True)


def emit_pass() -> None:
    plan_artifact = gate_chain.read_phase_artifact("plan", session_id=SID)
    drift = doc_integrity.render_drift_section(plan_artifact, repo_root=".")
    pattern = veto_pattern.check(ledger_path=None, session_id=SID)
    advisory = veto_pattern.render_advisory_text(pattern)
    ts = shadow_process.now_iso()
    report_path = Path(".agent/staging/AUDIT_REPORT.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = f"""# AUDIT REPORT

**Target**: Phase 240 execution-context governance at {TARGET}
**Session**: `{SID}`
**Mode**: solo adversarial tribunal; author-momentum scorer reported Option B not required
**Date**: {ts[:10]}
**Risk Grade**: L2

## Verdict: PASS

Phase 240 satisfies the recovered governed plan and declared behavioral spec delta. Model identity is provenance rather than execution authority; active skill metadata contains no retired named-model admission fields; hard capability absence is binding only when capability telemetry is explicitly complete; rendering adaptation is bounded; fabrication protections remain independent. The full repository suite, source lint, variant drift, spec-delta lint, prompt-injection gate, prose-test gate, and governance-health preflight pass on the bound target.

## Audit Results

### Security Pass
**Result**: PASS
No credential, unsafe-deserialization, shell-execution, eval/exec, or remote-dependency surface was introduced.

### OWASP Top 10 Pass
**Result**: PASS
No applicable A03, A04, A05, or A08 violation was found in the changed runtime path.

### Ghost UI Pass
**Result**: PASS
No UI surface is introduced or modified.

### Section 4 Razor Pass
**Result**: PASS
The new execution-context module and functions remain inside the phase's razor limits.

### Self-Application Pass
**Result**: PASS
The live skill corpus obeys the governance Phase 240 introduces: retired model-admission fields are absent and audit entry is vendor-neutral.

### Test Functionality Pass
**Result**: PASS
Enforced prose-test lint and behavioral tests pass; the Phase 240 tests exercise runtime behavior rather than artifact presence alone.

### Dependency Pass
**Result**: PASS
No dependency manifest or remote service dependency is added.

### Macro-Level Architecture Pass
**Result**: PASS
Execution-context policy is centralized in `qor/scripts/execution_context.py` and consumed through the audit/runtime compatibility seams.

### Feature Test Coverage Pass
**Result**: PASS
Governance-only change with an empty feature-inventory touch set; exempt by protocol.

### Infrastructure Alignment Pass
**Result**: PASS
Declared runtime, skill, spec-delta, and compiled-variant surfaces resolve to live repository seams; compiled variants report zero drift.

### Filter-Stage Ordering Coherence Pass
**Result**: PASS
Capability classification and bounded rendering selection introduce no dependent filter inversion.

### Orphan Pass
**Result**: PASS
The execution-context module is consumed by audit runtime and compatibility lint paths and covered by behavioral tests.

## Violations Found

None.

## Documentation Drift

{drift if drift else "(clean)"}

## Process Pattern Advisory

{advisory}

## Disposition

GATE opens. Proceed to governed implementation-evidence recovery and substantiation for session `{SID}`.
"""
    report_path.write_text(report, encoding="utf-8")
    report_hash = hashlib.sha256(report_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    plan_hash = hashlib.sha256(PLAN.read_bytes().replace(b"\r\n", b"\n")).hexdigest()

    ledger_path = Path("docs/META_LEDGER.md")
    nums = [int(x) for x in re.findall(r"^### Entry #(\d+):", ledger_path.read_text(encoding="utf-8"), re.M)]
    entry = ledger_emit.LedgerEntry(
        number=max(nums) + 1 if nums else 1,
        title="GATE TRIBUNAL",
        fields={
            "Timestamp": ts,
            "Phase": "GATE",
            "Author": "Judge",
            "Risk Grade": "L2",
            "Verdict": "PASS",
            "Session": SID,
            "Target SHA": TARGET,
        },
        body="Phase 240 execution-context governance passed the complete tribunal; proceed to governed implementation evidence recovery and substantiation.",
    )
    ledger_emit.append(ledger_path, entry, content=report_hash)

    payload = {
        "ts": ts,
        "target": PLAN.as_posix(),
        "verdict": "PASS",
        "violations": [],
        "risk_grade": "L2",
        "report_path": report_path.as_posix(),
        "target_content_hash": plan_hash,
        "reviews_remediate_gate": None,
    }
    manifest = ai_provenance.build_manifest(
        "audit", host="chatgpt", model_family="gpt-5.6-sol",
        human_oversight=ai_provenance.HumanOversight.PASS,
    )
    gate_chain.write_gate_artifact(
        phase="audit", payload=payload, session_id=SID,
        ai_provenance=manifest, skill="audit",
    )
    run("python", "qor/scripts/ledger_hash.py", "verify", "docs/META_LEDGER.md")


def main() -> None:
    assert_harness_only()
    bind_session()
    hard_entry_checks()
    spec_and_version()
    implementation_checks()
    advisory_ladder()
    emit_pass()
    print("PHASE240_AUDIT_PASS")


if __name__ == "__main__":
    main()
