"""Enumerations shared across the DisputeGuard domain."""

from enum import Enum


class DisputeReason(str, Enum):
    """Card-network reason codes (demo subset)."""

    MERCHANDISE_NOT_RECEIVED = "merchandise_not_received"
    NOT_AS_DESCRIBED = "not_as_described"
    DUPLICATE_CHARGE = "duplicate_charge"
    UNAUTHORIZED_TRANSACTION = "unauthorized_transaction"
    SERVICE_NOT_PROVIDED = "service_not_provided"
    CREDIT_NOT_PROCESSED = "credit_not_processed"


class DisputeStatus(str, Enum):
    """Lifecycle states of a dispute case."""

    PENDING_REVIEW = "pending_review"
    EVIDENCE_GATHERED = "evidence_gathered"
    VALIDATION_COMPLETE = "validation_complete"
    REPRESENTMENT_SENT = "representment_sent"
    WON = "won"
    LOST = "lost"
    ACCEPTED_LOSS = "accepted_loss"


class EvidenceType(str, Enum):
    """Types of documents that can support a representment."""

    INVOICE = "invoice"
    SHIPPING_LABEL = "shipping_label"
    TRACKING_RECORD = "tracking_record"
    PROOF_OF_DELIVERY = "proof_of_delivery"
    CUSTOMER_COMMUNICATION = "customer_communication"
    REFUND_POLICY = "refund_policy"
    ORDER_CONFIRMATION = "order_confirmation"
    AVS_CVV_RESULT = "avs_cvv_result"
    SIGNED_RECEIPT = "signed_receipt"
    OTHER = "other"


class VerificationStatus(str, Enum):
    """Outcome of a deterministic claim verification step."""

    VERIFIED = "verified"
    FAILED = "failed"
    PENDING = "pending"
    NEEDS_REVIEW = "needs_review"  # contradiction detected → human review


class ExtractionMethod(str, Enum):
    """How a data point was extracted from a source document."""

    DIRECT_TEXT = "direct_text"           # parsed from structured text
    OCR = "ocr"                          # optical character recognition
    LLM_EXTRACTION = "llm_extraction"    # bounded AI structured extraction
    MANUAL_ENTRY = "manual_entry"        # entered by an operator


class DisputeAction(str, Enum):
    """
    The three — and only three — allowed recommendation outcomes.

    A contradiction sets `review_required = True` on the Decision; it does
    NOT create a fourth action.
    """

    CONTEST = "contest"
    REQUEST_MORE_EVIDENCE = "request_more_evidence"
    ACCEPT_LOSS = "accept_loss"


class RiskLevel(str, Enum):
    """Qualitative risk tier for display and prioritisation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
