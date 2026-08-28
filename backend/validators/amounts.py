"""Exact Decimal amount validation."""

from backend.domain.enums import VerificationStatus
from backend.domain.models import Dispute, EvidenceClaim
from backend.validators.common import ValidationIssue, claims_for, mark, parse_decimal


def validate_amounts(dispute: Dispute, claims: list[EvidenceClaim]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for claim in claims_for(claims, "amount"):
        amount = parse_decimal(claim.normalized_value)
        if amount is not None and amount == dispute.amount:
            mark(claim, VerificationStatus.VERIFIED, "Exact Decimal amount match with dispute")
        else:
            mark(claim, VerificationStatus.FAILED, "Amount does not exactly match dispute amount")
            issues.append(ValidationIssue("amount_match", "error", "Amount mismatch", [claim.id]))
    return issues
