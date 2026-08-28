"""Independent carrier delivery and deadline validation."""

from datetime import datetime

from backend.domain.enums import EvidenceType, VerificationStatus
from backend.domain.models import Dispute, EvidenceClaim, EvidenceDocument
from backend.validators.common import ValidationIssue, claims_for, mark


def _parse(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def validate_delivery(
    dispute: Dispute,
    claims: list[EvidenceClaim],
    documents: list[EvidenceDocument],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    carrier_ids = {doc.id for doc in documents if doc.type == EvidenceType.TRACKING_RECORD and doc.source == "carrier_api"}
    status_claims = [claim for claim in claims_for(claims, "delivery_status") if claim.document_id in carrier_ids]
    date_claims = [claim for claim in claims_for(claims, "delivery_datetime") if claim.document_id in carrier_ids]
    delivered = next((claim for claim in status_claims if claim.normalized_value == "delivered"), None)
    delivered_date = next((claim for claim in date_claims if claim.normalized_value), None)

    if delivered is None or delivered_date is None:
        for claim in status_claims + date_claims:
            mark(claim, VerificationStatus.FAILED, "Independent carrier delivery event is missing")
        return [ValidationIssue("delivery_event", "error", "No independent carrier delivery event found")]

    event_time = _parse(delivered_date.normalized_value)
    if event_time is None:
        mark(delivered_date, VerificationStatus.FAILED, "Delivery timestamp cannot be parsed")
        return [ValidationIssue("delivery_datetime", "error", "Delivery timestamp is invalid", [delivered_date.id])]

    # Fixture dates are timezone-naive; apply the dispute deadline's timezone only
    # for comparison, without changing the source claim itself.
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=dispute.respond_by.tzinfo)
    before_deadline = event_time <= dispute.respond_by
    before_filed = event_time <= dispute.filed_date
    if before_deadline and before_filed:
        mark(delivered, VerificationStatus.VERIFIED, "Carrier confirms delivery before deadline")
        mark(delivered_date, VerificationStatus.VERIFIED, "Carrier delivery timestamp is before deadline")
        # A POD is a required evidence document. Its delivery facts are
        # accepted only after the independent carrier event has passed.
        for claim in claims:
            if claim.document_id in {
                document.id for document in documents if document.type == EvidenceType.PROOF_OF_DELIVERY
            } and claim.field_name in {"delivery_status", "delivery_datetime"}:
                if claim.field_name == "delivery_status" and claim.normalized_value == "delivered":
                    mark(claim, VerificationStatus.VERIFIED, "POD delivery is corroborated by carrier event")
                elif claim.field_name == "delivery_datetime" and claim.normalized_value == delivered_date.normalized_value:
                    mark(claim, VerificationStatus.VERIFIED, "POD timestamp is corroborated by carrier event")
    else:
        mark(delivered, VerificationStatus.FAILED, "Delivery is after the required dispute timeline")
        mark(delivered_date, VerificationStatus.FAILED, "Delivery is after the required dispute timeline")
        issues.append(ValidationIssue("delivery_before_deadline", "error", "Delivery is not before the required deadline", [delivered.id, delivered_date.id]))
    return issues
