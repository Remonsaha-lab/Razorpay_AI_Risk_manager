"""Ordered deterministic dispute workflow."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from backend.domain.enums import DisputeAction, EvidenceType, VerificationStatus
from backend.domain.models import Decision, Dispute, EvidenceClaim, EvidenceDocument, StrengthFactor
from backend.services.claim_extractor import extract_claims_for_case
from backend.validators import validate_amounts, validate_consistency, validate_delivery, validate_identifiers
from backend.validators.common import ValidationIssue

POLICY_PATH = Path(__file__).parent.parent / "policies" / "merchandise_not_received_v1.json"


def load_policy(path: Path = POLICY_PATH) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _required_types(policy: dict) -> list[EvidenceType]:
    return [EvidenceType(item["type"]) for item in policy["required_evidence"] if item.get("required")]


def _completeness(documents: list[EvidenceDocument], claims: list[EvidenceClaim], policy: dict) -> tuple[float, list[str]]:
    required = _required_types(policy)
    verified_types = {
        document.type
        for document in documents
        if any(claim.document_id == document.id and claim.verification_status == VerificationStatus.VERIFIED for claim in claims)
    }
    missing = [evidence_type.value for evidence_type in required if evidence_type not in verified_types]
    return ((len(required) - len(missing)) / len(required) if required else 1.0, missing)


def _strength(claims: list[EvidenceClaim], issues: list[ValidationIssue], completeness: float) -> tuple[float, list[StrengthFactor], list[StrengthFactor]]:
    positives: list[StrengthFactor] = []
    negatives: list[StrengthFactor] = []
    verified = {claim.field_name for claim in claims if claim.verification_status == VerificationStatus.VERIFIED}
    if "delivery_status" in verified:
        positives.append(StrengthFactor(description="Independent carrier delivery is verified", impact=0.30))
    if "tracking_id" in verified:
        positives.append(StrengthFactor(description="Tracking identifier is exactly verified", impact=0.20))
    if "order_id" in verified and "amount" in verified:
        positives.append(StrengthFactor(description="Order and amount linkage is verified", impact=0.20))
    if completeness < 1:
        negatives.append(StrengthFactor(description="Required evidence is missing or unverified", impact=-0.25))
    blocking_issues = [issue for issue in issues if issue.rule_id not in {"tracking_ocr_confirmation"}]
    if blocking_issues:
        negatives.append(StrengthFactor(description="Validation contradictions or blockers remain", impact=-0.30))
    score = 0.25 + sum(f.impact for f in positives) + sum(f.impact for f in negatives)
    return max(0.0, min(1.0, score)), positives, negatives


def run_workflow(dispute: Dispute, documents: list[EvidenceDocument], policy: dict | None = None) -> dict:
    policy = policy or load_policy()
    claims = extract_claims_for_case(documents)
    issues: list[ValidationIssue] = []
    issues.extend(validate_identifiers(dispute, claims, documents))
    issues.extend(validate_amounts(dispute, claims))
    issues.extend(validate_delivery(dispute, claims, documents))
    issues.extend(validate_consistency(dispute, claims))

    completeness, missing = _completeness(documents, claims, policy)
    strength, positives, negatives = _strength(claims, issues, completeness)
    assumptions = policy["economic_assumptions"]
    contest_cost = Decimal(str(assumptions["contest_cost_inr"]))
    contest_ev = (Decimal(str(strength)) * dispute.amount) - contest_cost
    accept_ev = -dispute.amount
    thresholds = policy["thresholds"]
    now = datetime.now(timezone.utc)
    deadline_open = dispute.respond_by > now
    contradictions = bool(issues)
    blocking_issues = [issue for issue in issues if issue.rule_id not in {"tracking_ocr_confirmation"}]

    if missing and deadline_open:
        action = DisputeAction.REQUEST_MORE_EVIDENCE
        reason = "Required evidence is missing and the response deadline is still open"
    elif not blocking_issues and completeness >= float(thresholds["min_completeness_to_contest"]) and strength >= float(thresholds["min_evidence_strength_to_contest"]) and contest_ev > accept_ev:
        action = DisputeAction.CONTEST
        reason = "Required evidence is verified and contest expected value exceeds acceptance"
        if contradictions:
            reason += "; human review is required for a near-match or warning"
    elif contradictions:
        action = DisputeAction.ACCEPT_LOSS
        reason = "Contradictory or unverified evidence requires human review"
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
    return {
        "decision": decision,
        "claims": claims,
        "issues": [issue.__dict__ for issue in issues],
        "missing_evidence": missing,
        "policy_id": policy["policy_id"],
    }
