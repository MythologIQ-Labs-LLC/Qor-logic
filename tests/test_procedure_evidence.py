import copy
import hashlib

import pytest

from qor.compliance.procedure_evidence import (
    ProcedureEvidenceError,
    VerifiedClaim,
    canonical_claim_digest,
    evaluate_contract,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def procedure(name="qor-audit", revision="abc", digest=None):
    return {
        "name": name,
        "repository": "MythologIQ-Labs-LLC/Qor-logic",
        "revision": revision,
        "path": f"qor/skills/{name}/SKILL.md",
        "sha256": digest or h(name + revision),
    }


def subject(revision="head-1", ident="pr-42"):
    return {
        "kind": "change",
        "repository": "example/repo",
        "id": ident,
        "revision": revision,
        "sha256": h(ident + revision),
    }


def requirement(
    rid="audit", *, classes=None, revision="head-1", proc=None, input_digest=None
):
    item = {
        "requirementId": rid,
        "procedure": proc or procedure(),
        "subject": subject(revision),
        "acceptedEvidenceClasses": classes or ["wrapper-observed"],
    }
    independent = {"wrapper-observed", "ci-attested"}
    if any(cls in independent for cls in item["acceptedEvidenceClasses"]):
        item["trustedPrincipals"] = ["ci:qor-governance"]
    if input_digest:
        item["inputSha256"] = input_digest
    return item


def evidence(
    eid="ev-1",
    *,
    cls="wrapper-observed",
    revision="head-1",
    proc=None,
    observer="ci:qor-governance",
    status="completed",
    input_digest=None,
):
    item = {
        "evidenceId": eid,
        "invocationId": f"run-{eid}",
        "procedure": proc or procedure(),
        "subject": subject(revision),
        "evidenceClass": cls,
        "status": status,
    }
    if observer is not None:
        item["observerId"] = observer
    if input_digest:
        item["inputSha256"] = input_digest
    return item


def contract(reqs=None, evidence_items=None):
    return {
        "contractVersion": "1",
        "requirements": reqs or [requirement()],
        "evidence": evidence_items or [],
    }


def verified(ev, principal="ci:qor-governance", digest=None):
    return VerifiedClaim(
        ev["evidenceId"], digest or canonical_claim_digest(ev), principal
    )


def test_exact_independently_verified_claim_satisfies_requirement():
    ev = evidence()
    result = evaluate_contract(contract(evidence_items=[ev]), [verified(ev)])
    assert result.satisfied
    assert result.requirements[0].evidence_ids == ("ev-1",)


def test_independent_claim_without_trusted_verification_fails():
    ev = evidence()
    result = evaluate_contract(contract(evidence_items=[ev]))
    assert not result.satisfied
    assert "claim_not_independently_verified" in result.requirements[0].reasons


def test_verification_is_bound_to_exact_claim_digest():
    ev = evidence()
    proof = verified(ev)
    mutated = copy.deepcopy(ev)
    mutated["subject"] = subject("head-2")
    result = evaluate_contract(contract(evidence_items=[mutated]), [proof])
    assert not result.satisfied
    assert "claim_not_independently_verified" in result.requirements[0].reasons
    assert "subject_binding_mismatch" in result.requirements[0].reasons


def test_wrong_procedure_bytes_fail_even_with_same_name():
    wrong = procedure(digest=h("wrong"))
    ev = evidence(proc=wrong)
    result = evaluate_contract(contract(evidence_items=[ev]), [verified(ev)])
    assert not result.satisfied
    assert "procedure_binding_mismatch" in result.requirements[0].reasons


def test_evidence_from_prior_head_fails_current_subject_binding():
    ev = evidence(revision="head-0")
    result = evaluate_contract(contract(evidence_items=[ev]), [verified(ev)])
    assert not result.satisfied
    assert "subject_binding_mismatch" in result.requirements[0].reasons


def test_evidence_copied_from_another_change_fails():
    ev = evidence()
    ev["subject"] = subject("head-1", "pr-99")
    result = evaluate_contract(contract(evidence_items=[ev]), [verified(ev)])
    assert not result.satisfied
    assert "subject_binding_mismatch" in result.requirements[0].reasons


def test_untrusted_observer_fails_even_when_claim_is_verified():
    ev = evidence(observer="ci:other")
    result = evaluate_contract(
        contract(evidence_items=[ev]), [verified(ev, "ci:other")]
    )
    assert not result.satisfied
    assert "untrusted_observer" in result.requirements[0].reasons


def test_verified_agent_declaration_does_not_promote_evidence_class():
    ev = evidence(cls="agent-declared", observer=None)
    result = evaluate_contract(contract(evidence_items=[ev]), [verified(ev)])
    assert not result.satisfied
    assert "evidence_class_not_accepted" in result.requirements[0].reasons


def test_agent_declaration_can_satisfy_only_when_policy_explicitly_allows_it():
    req = requirement(classes=["agent-declared"])
    req.pop("trustedPrincipals", None)
    ev = evidence(cls="agent-declared", observer=None)
    result = evaluate_contract(contract([req], [ev]))
    assert result.satisfied


def test_failed_invocation_does_not_satisfy_execution_requirement():
    ev = evidence(status="failed")
    result = evaluate_contract(contract(evidence_items=[ev]), [verified(ev)])
    assert not result.satisfied
    assert "execution_not_completed" in result.requirements[0].reasons


def test_input_digest_is_exact_when_policy_requires_it():
    req = requirement(input_digest=h("expected"))
    ev = evidence(input_digest=h("different"))
    result = evaluate_contract(contract([req], [ev]), [verified(ev)])
    assert not result.satisfied
    assert "input_digest_mismatch" in result.requirements[0].reasons


def test_required_set_completeness_fails_when_one_requirement_is_omitted():
    req_a = requirement("audit")
    req_b = requirement("research", proc=procedure("qor-research"))
    ev = evidence()
    result = evaluate_contract(contract([req_a, req_b], [ev]), [verified(ev)])
    assert not result.satisfied
    assert result.requirements[1].reasons == ("missing_evidence",)


def test_independent_class_requires_explicit_trusted_principals():
    req = requirement()
    req.pop("trustedPrincipals")
    with pytest.raises(ProcedureEvidenceError, match="trustedPrincipals"):
        evaluate_contract(contract([req], []))


def test_duplicate_evidence_ids_are_rejected():
    ev = evidence()
    with pytest.raises(ProcedureEvidenceError, match="duplicate evidence"):
        evaluate_contract(
            contract(evidence_items=[ev, copy.deepcopy(ev)]), [verified(ev)]
        )


def test_unknown_evidence_class_is_schema_rejected():
    ev = evidence()
    ev["evidenceClass"] = "super-trusted-because-i-said-so"
    with pytest.raises(ProcedureEvidenceError):
        evaluate_contract(contract(evidence_items=[ev]))
