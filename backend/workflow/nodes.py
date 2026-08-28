"""Individual functional nodes for the LangGraph dispute workflow."""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import json

from backend.domain.enums import DisputeAction, EvidenceType, VerificationStatus
from backend.domain.models import Decision, StrengthFactor
from backend.services.claim_extractor import extract_claims_for_case
from backend.validators import validate_amounts, validate_consistency, validate_delivery, validate_identifiers
from backend.validators.common import ValidationIssue
from backend.workflow.state import DisputeState

POLICY_PATH = Path(__file__).parent.parent / "policies" / "merchandise_not_received_v1.json"


def ingest_node(state: DisputeState) -> dict:
    """Ensure policy is loaded and state is initialized."""
    policy = state.get("policy")
    if not policy:
        with POLICY_PATH.open("r", encoding="utf-8") as handle:
            policy = json.load(handle)
    return {
        "policy": policy,
        "policy_id": policy.get("policy_id", "unknown_policy"),
        "claims": [],
        "issues": [],
        "errors": [],
    }


def extract_node(state: DisputeState) -> dict:
    """Extract raw evidence claims with provenance from attached documents."""
    documents = state["documents"]
    claims = extract_claims_for_case(documents)
    return {"claims": claims}


def validate_node(state: DisputeState) -> dict:
    """Run all deterministic validators (amounts, delivery timeline, IDs, consistency)."""
    dispute = state["dispute"]
    documents = state["documents"]
    claims = state["claims"]

    issues: list[ValidationIssue] = []
    issues.extend(validate_identifiers(dispute, claims, documents))
    issues.extend(validate_amounts(dispute, claims))
    issues.extend(validate_delivery(dispute, claims, documents))
    issues.extend(validate_consistency(dispute, claims))

    return {"claims": claims, "issues": issues}


def policy_evaluate_node(state: DisputeState) -> dict:
    """Assess evidence completeness and identify missing required document types."""
    policy = state["policy"]
    documents = state["documents"]
    claims = state["claims"]

    required_types = [EvidenceType(item["type"]) for item in policy.get("required_evidence", []) if item.get("required")]
    verified_types = {
        document.type
        for document in documents
        if any(claim.document_id == document.id and claim.verification_status == VerificationStatus.VERIFIED for claim in claims)
    }
    missing = [evidence_type.value for evidence_type in required_types if evidence_type not in verified_types]
    completeness = (len(required_types) - len(missing)) / len(required_types) if required_types else 1.0

    return {
        "completeness_score": completeness,
        "missing_evidence": missing,
    }


def evidence_scoring_node(state: DisputeState) -> dict:
    """Compute explainable evidence strength score and positive/negative factors."""
    claims = state["claims"]
    issues = state["issues"]
    completeness = state["completeness_score"]

    positives: list[StrengthFactor] = []
    negatives: list[StrengthFactor] = []

    verified = {claim.field_name for claim in claims if claim.verification_status == VerificationStatus.VERIFIED}
    if "delivery_status" in verified:
        positives.append(StrengthFactor(description="Independent carrier delivery is verified", impact=0.30))
    if "tracking_id" in verified:
        positives.append(StrengthFactor(description="Tracking identifier is exactly verified", impact=0.20))
    if "order_id" in verified and "amount" in verified:
        positives.append(StrengthFactor(description="Order and amount linkage is verified", impact=0.20))
    if completeness < 1.0:
        negatives.append(StrengthFactor(description="Required evidence is missing or unverified", impact=-0.25))

    blocking_issues = [issue for issue in issues if issue.rule_id not in {"tracking_ocr_confirmation"}]
    if blocking_issues:
        negatives.append(StrengthFactor(description="Validation contradictions or blockers remain", impact=-0.30))

    score = 0.25 + sum(f.impact for f in positives) + sum(f.impact for f in negatives)
    strength = max(0.0, min(1.0, score))

    return {
        "evidence_strength": strength,
        "positive_factors": positives,
        "negative_factors": negatives,
    }


def economics_node(state: DisputeState) -> dict:
    """Calculate contest vs. accept expected value with exact Decimal precision."""
    dispute = state["dispute"]
    policy = state["policy"]
    strength = state["evidence_strength"]

    assumptions = policy.get("economic_assumptions", {})
    contest_cost = Decimal(str(assumptions.get("contest_cost_inr", "500.00")))
    contest_ev = (Decimal(str(strength)) * dispute.amount) - contest_cost
    accept_ev = -dispute.amount

    return {
        "contest_expected_value": contest_ev,
        "accept_expected_value": accept_ev,
    }


def decide_node(state: DisputeState) -> dict:
    """Apply policy thresholds and economic EV to finalize dispute recommendation."""
    dispute = state["dispute"]
    policy = state["policy"]
    issues = state["issues"]
    completeness = state["completeness_score"]
    strength = state["evidence_strength"]
    missing = state["missing_evidence"]
    contest_ev = state["contest_expected_value"]
    accept_ev = state["accept_expected_value"]
    positives = state["positive_factors"]
    negatives = state["negative_factors"]

    thresholds = policy.get("thresholds", {})
    assumptions = policy.get("economic_assumptions", {})
    contest_cost = Decimal(str(assumptions.get("contest_cost_inr", "500.00")))

    now = datetime.now(timezone.utc)
    deadline_open = dispute.respond_by > now
    contradictions = bool(issues)
    blocking_issues = [issue for issue in issues if issue.rule_id not in {"tracking_ocr_confirmation"}]

    if missing and deadline_open:
        action = DisputeAction.REQUEST_MORE_EVIDENCE
        reason = "Required evidence is missing and the response deadline is still open"
    elif (
        not blocking_issues
        and completeness >= float(thresholds.get("min_completeness_to_contest", 1.0))
        and strength >= float(thresholds.get("min_evidence_strength_to_contest", 0.75))
        and contest_ev > accept_ev
    ):
        action = DisputeAction.CONTEST
        reason = "Required evidence is verified and contest expected value exceeds acceptance"
        if contradictions:
            reason += "; human review is required for a near-match or warning"
    else:
        action = DisputeAction.ACCEPT_LOSS
        reason = "Evidence strength or contest economics does not meet policy threshold"

    decision = Decision(
        dispute_id=dispute.id,
        action=action,
        review_required=contradictions or action == DisputeAction.CONTEST,
        completeness_score=completeness,
        evidence_strength=strength,
        contest_expected_value=contest_ev,
        accept_expected_value=accept_ev,
        positive_factors=positives,
        negative_factors=negatives,
        reasons=[reason] + [issue.message for issue in issues],
        assumptions=[
            "Evidence strength is an explainable prototype estimate, not a calibrated probability.",
            f"Contest cost assumption: INR {contest_cost:.2f}.",
            assumptions.get("note", "Synthetic economic assumptions."),
        ],
    )

    return {"decision": decision}
