"""Exact order/tracking validation and OCR correction handling."""

from difflib import SequenceMatcher

from backend.domain.enums import EvidenceType, VerificationStatus
from backend.domain.models import Dispute, EvidenceClaim, EvidenceDocument
from backend.validators.common import ValidationIssue, claims_for, mark


def validate_identifiers(
    dispute: Dispute,
    claims: list[EvidenceClaim],
    documents: list[EvidenceDocument],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for claim in claims_for(claims, "order_id"):
        if claim.normalized_value == dispute.order_id.strip().upper():
            mark(claim, VerificationStatus.VERIFIED, "Exact order ID match with dispute")
        else:
            mark(claim, VerificationStatus.FAILED, "Order ID does not exactly match dispute")
            issues.append(ValidationIssue("order_id_match", "error", "Order ID mismatch", [claim.id]))

    carrier_document_ids = {
        document.id
        for document in documents
        if document.type == EvidenceType.TRACKING_RECORD and document.source == "carrier_api"
    }
    carrier_claims = [
        claim for claim in claims_for(claims, "tracking_id")
        if claim.document_id in carrier_document_ids
    ]
    reference = carrier_claims[0] if carrier_claims else None
    for claim in claims_for(claims, "tracking_id"):
        if reference is None:
            mark(claim, VerificationStatus.FAILED, "No independent carrier tracking reference")
            continue
        if claim.normalized_value == reference.normalized_value:
            mark(claim, VerificationStatus.VERIFIED, "Exact tracking ID match with carrier reference")
        else:
            similarity = SequenceMatcher(None, claim.normalized_value, reference.normalized_value).ratio()
            if similarity >= 0.80:
                mark(claim, VerificationStatus.NEEDS_REVIEW, "OCR correction candidate; carrier confirmation required")
                issues.append(ValidationIssue("tracking_ocr_confirmation", "error", "Tracking ID is a near-match and is not verified", [claim.id, reference.id]))
            else:
                mark(claim, VerificationStatus.FAILED, "Tracking ID does not exactly match carrier reference")
                issues.append(ValidationIssue("tracking_id_match", "error", "Tracking ID mismatch", [claim.id, reference.id]))
    return issues
