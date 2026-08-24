"""
DisputeGuard domain models — Pydantic v2 entities.

These models are the single source of truth for data shapes flowing through
the system.  Every field is explicitly typed and documented so the API,
validators, workflow engine, and UI all share one contract.

Design notes
────────────
• Money is stored as `Decimal` — never `float` — to avoid rounding errors
  that could mis-compare ₹18,400.00 with ₹18,399.999… .
• Dates use `datetime` with timezone awareness.
• Every evidence claim retains its *raw* extracted text and the *normalized*
  value so auditors can trace exactly what the system did.
• `Decision.review_required` is the only flag for contradictions.  There is
  no fourth action type.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.domain.enums import (
    DisputeAction,
    DisputeReason,
    DisputeStatus,
    EvidenceType,
    ExtractionMethod,
    RiskLevel,
    VerificationStatus,
)


# ── helpers ──────────────────────────────────────────────────────────────


def _new_id() -> str:
    """Short, human-readable ID prefix + 8 hex chars."""
    return uuid4().hex[:8].upper()


# ── Core entities ────────────────────────────────────────────────────────


class Dispute(BaseModel):
    """
    A single chargeback dispute case.

    Contains merchant/transaction metadata and the card-network deadline.
    The `amount` field uses `Decimal` for exact comparisons (e.g. invoice
    vs. dispute amount).
    """

    id: str = Field(default_factory=lambda: f"DSP-{_new_id()}")
    merchant_name: str
    merchant_id: str = ""

    # Transaction details
    transaction_id: str
    order_id: str
    amount: Decimal = Field(description="Dispute amount in INR (exact decimal)")
    currency: str = "INR"
    transaction_date: datetime

    # Dispute metadata
    reason: DisputeReason
    reason_description: str = ""
    status: DisputeStatus = DisputeStatus.PENDING_REVIEW
    risk_level: RiskLevel = RiskLevel.MEDIUM

    # Deadlines
    filed_date: datetime
    respond_by: datetime  # card-network deadline

    # Customer info (synthetic only)
    customer_name: str = ""
    customer_email: str = ""
    shipping_address: str = ""
    billing_address: str = ""

    # Links to evidence and decision
    evidence_document_ids: list[str] = Field(default_factory=list)
    decision_id: Optional[str] = None

    class Config:
        json_encoders = {Decimal: str}


class EvidenceDocument(BaseModel):
    """
    A single source document attached to a dispute (invoice PDF, tracking
    screenshot, delivery confirmation, etc.).

    `raw_text` holds the full extracted text; individual facts pulled from
    it become `EvidenceClaim` objects referencing this document's `id`.
    """

    id: str = Field(default_factory=lambda: f"DOC-{_new_id()}")
    dispute_id: str
    type: EvidenceType
    filename: str = ""
    source: str = Field(
        description="Where the document came from, e.g. 'merchant_upload', 'carrier_api'"
    )
    page_count: int = 1

    # Extraction
    extraction_method: ExtractionMethod = ExtractionMethod.DIRECT_TEXT
    extraction_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="1.0 for deterministic text parse; lower for OCR/LLM",
    )
    raw_text: str = ""

    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.now)


class EvidenceClaim(BaseModel):
    """
    A single fact extracted from an EvidenceDocument.

    Both `raw_value` (what appeared in the document) and `normalized_value`
    (after cleanup/normalisation) are stored so an auditor can see exactly
    what changed and why.

    `verification_status` and `verification_reason` are set by the
    deterministic validator — never by AI.
    """

    id: str = Field(default_factory=lambda: f"CLM-{_new_id()}")
    dispute_id: str
    document_id: str  # FK → EvidenceDocument.id

    # What was extracted
    field_name: str = Field(description="e.g. 'order_id', 'delivery_date', 'tracking_number'")
    raw_value: str = Field(description="Exact text from the source document")
    normalized_value: str = Field(
        default="",
        description="Cleaned/normalised version used for comparison",
    )

    # Source location for provenance
    source_page: int = 1
    source_location: str = Field(
        default="",
        description="e.g. 'line 4', 'header row 2', 'tracking section'",
    )

    # Verification (set by deterministic validators only)
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verification_reason: str = ""

    # Extraction provenance
    extraction_method: ExtractionMethod = ExtractionMethod.DIRECT_TEXT
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class StrengthFactor(BaseModel):
    """A single positive or negative factor affecting evidence strength."""

    description: str
    impact: float = Field(
        description="Positive = helps case, negative = hurts case. Range roughly -1 to +1."
    )
    source_claim_id: Optional[str] = None  # optional link back to a claim


class Decision(BaseModel):
    """
    The output of the deterministic decision engine.

    Contains the recommended action, the reasoning, economic analysis,
    and whether a human must review before proceeding.

    Key design rule: `review_required = True` when contradictions are
    found.  There is *no* fourth action type — contradictions surface
    through this flag, not through a new enum value.
    """

    id: str = Field(default_factory=lambda: f"DEC-{_new_id()}")
    dispute_id: str

    # Recommendation
    action: DisputeAction
    review_required: bool = False

    # Evidence assessment
    completeness_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Verified required evidence / total required evidence",
    )
    evidence_strength: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Explainable score — NOT a calibrated probability",
    )

    # Economic analysis
    contest_expected_value: Decimal = Field(
        default=Decimal("0"),
        description="EV of contesting = P(win) × amount − cost",
    )
    accept_expected_value: Decimal = Field(
        default=Decimal("0"),
        description="EV of accepting loss = −amount (always negative)",
    )

    # Reasoning
    positive_factors: list[StrengthFactor] = Field(default_factory=list)
    negative_factors: list[StrengthFactor] = Field(default_factory=list)
    reasons: list[str] = Field(
        default_factory=list,
        description="Human-readable decision rationale",
    )

    # Assumptions displayed to reviewer
    assumptions: list[str] = Field(
        default_factory=list,
        description="Economic/model assumptions underpinning the recommendation",
    )

    # Timestamps
    decided_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {Decimal: str}
