"""State schema for the LangGraph dispute decision workflow."""

from decimal import Decimal
from typing import Any, Optional, TypedDict

from backend.domain.models import Decision, Dispute, EvidenceClaim, EvidenceDocument, StrengthFactor
from backend.validators.common import ValidationIssue


class DisputeState(TypedDict, total=False):
    # Inputs
    dispute: Dispute
    documents: list[EvidenceDocument]
    policy: dict

    # Extraction and Validation
    claims: list[EvidenceClaim]
    issues: list[ValidationIssue]

    # Policy and scoring
    completeness_score: float
    missing_evidence: list[str]
    evidence_strength: float
    positive_factors: list[StrengthFactor]
    negative_factors: list[StrengthFactor]
    assumptions: list[str]

    # Economics
    contest_expected_value: Decimal
    accept_expected_value: Decimal

    # Output decision
    decision: Optional[Decision]
    policy_id: str
    errors: list[str]


# Alias for compatibility
DisputeWorkflowState = DisputeState
    