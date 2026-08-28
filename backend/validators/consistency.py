"""Cross-document contradiction checks."""

from collections import defaultdict
import re

from backend.domain.enums import VerificationStatus
from backend.domain.models import Dispute, EvidenceClaim
from backend.validators.common import ValidationIssue, claims_for, normalized_text, mark


def validate_consistency(dispute: Dispute, claims: list[EvidenceClaim]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for field in ("order_id", "amount", "tracking_id", "delivery_datetime"):
        grouped = claims_for(claims, field)
        if field == "tracking_id":
            # An OCR/label near-match is already handled by the identifier
            # validator. The independent carrier value remains authoritative.
            if (
                any(claim.verification_status == VerificationStatus.VERIFIED for claim in grouped)
                and any(claim.verification_status == VerificationStatus.NEEDS_REVIEW for claim in grouped)
            ):
                continue
        values: dict[str, list[EvidenceClaim]] = defaultdict(list)
        for claim in grouped:
            values[claim.normalized_value].append(claim)
        if len(values) > 1:
            all_ids = [claim.id for claim in grouped]
            for claim in grouped:
                if claim.verification_status == VerificationStatus.PENDING:
                    mark(claim, VerificationStatus.NEEDS_REVIEW, f"Contradictory {field} values across evidence")
            issues.append(ValidationIssue(f"{field}_consistency", "error", f"Contradictory {field} values", all_ids))

    address_claims = claims_for(claims, "shipping_address")
    if dispute.shipping_address and address_claims:
        # Compare address tokens without punctuation so a partial carrier
        # address (for example, without state/pincode) is not a false conflict.
        expected = set(re.findall(r"[a-z0-9]+", normalized_text(dispute.shipping_address)))
        for claim in address_claims:
            observed = set(re.findall(r"[a-z0-9]+", normalized_text(claim.normalized_value)))
            if expected and observed and not (expected <= observed or observed <= expected):
                mark(claim, VerificationStatus.NEEDS_REVIEW, "Shipping address differs from dispute address")
                issues.append(ValidationIssue("address_consistency", "warning", "Shipping address contradiction", [claim.id]))
    return issues
