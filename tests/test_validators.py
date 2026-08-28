"""
Unit tests for deterministic evidence validators.

Covers:
- Exact matching (order ID, amount, delivery)
- Incorrect order ID and amount failures
- Late delivery after dispute filing / deadline
- OCR correction blocked without carrier confirmation
- Claim provenance preservation
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from backend.domain.enums import (
    DisputeReason,
    DisputeStatus,
    EvidenceType,
    ExtractionMethod,
    RiskLevel,
    VerificationStatus,
)
from backend.domain.models import Dispute, EvidenceClaim, EvidenceDocument
from backend.validators.amounts import validate_amounts
from backend.validators.consistency import validate_consistency
from backend.validators.delivery import validate_delivery
from backend.validators.identifiers import validate_identifiers


@pytest.fixture
def base_dispute():
    return Dispute(
        id="DSP-TEST-001",
        merchant_name="TechMart India",
        transaction_id="TXN-20260801-0001",
        order_id="ORD-20260801-7834",
        amount=Decimal("18400.00"),
        currency="INR",
        transaction_date=datetime(2026, 8, 1, 14, 0, tzinfo=timezone.utc),
        reason=DisputeReason.MERCHANDISE_NOT_RECEIVED,
        status=DisputeStatus.PENDING_REVIEW,
        risk_level=RiskLevel.HIGH,
        filed_date=datetime(2026, 8, 20, 10, 0, tzinfo=timezone.utc),
        respond_by=datetime(2026, 9, 4, 18, 0, tzinfo=timezone.utc),
        shipping_address="42 MG Road, Bengaluru, KA 560001",
    )


# ── 1. Identifier Validation Tests ───────────────────────────────────────────

def test_exact_order_id_match_passes(base_dispute):
    claim = EvidenceClaim(
        id="CLM-1",
        dispute_id=base_dispute.id,
        document_id="DOC-INV",
        field_name="order_id",
        raw_value="ORD-20260801-7834",
        normalized_value="ORD-20260801-7834",
        source_location="line 4",
    )
    issues = validate_identifiers(base_dispute, [claim], [])
    assert len(issues) == 0
    assert claim.verification_status == VerificationStatus.VERIFIED
    assert "Exact order ID match" in claim.verification_reason


def test_incorrect_order_id_fails(base_dispute):
    claim = EvidenceClaim(
        id="CLM-1",
        dispute_id=base_dispute.id,
        document_id="DOC-INV",
        field_name="order_id",
        raw_value="ORD-WRONG-9999",
        normalized_value="ORD-WRONG-9999",
        source_location="line 4",
    )
    issues = validate_identifiers(base_dispute, [claim], [])
    assert len(issues) == 1
    assert issues[0].rule_id == "order_id_match"
    assert claim.verification_status == VerificationStatus.FAILED


def test_ocr_near_match_without_carrier_confirmation_fails(base_dispute):
    """If no carrier tracking document exists, OCR near-match cannot verify."""
    ocr_claim = EvidenceClaim(
        id="CLM-OCR",
        dispute_id=base_dispute.id,
        document_id="DOC-LABEL",
        field_name="tracking_id",
        raw_value="SHIP-BLR-2O26O8O2-4421",
        normalized_value="SHIP-BLR-2O26O8O2-4421",
        source_location="line 2",
    )
    # No carrier document provided
    issues = validate_identifiers(base_dispute, [ocr_claim], [])
    assert ocr_claim.verification_status == VerificationStatus.FAILED
    assert "No independent carrier tracking reference" in ocr_claim.verification_reason


def test_ocr_near_match_flags_warning_when_carrier_present(base_dispute):
    """OCR near-match with carrier present flags tracking_ocr_confirmation."""
    carrier_doc = EvidenceDocument(
        id="DOC-TRK",
        dispute_id=base_dispute.id,
        type=EvidenceType.TRACKING_RECORD,
        source="carrier_api",
        raw_text="Tracking ID: SHIP-BLR-20260802-4421",
    )
    carrier_claim = EvidenceClaim(
        id="CLM-TRK",
        dispute_id=base_dispute.id,
        document_id="DOC-TRK",
        field_name="tracking_id",
        raw_value="SHIP-BLR-20260802-4421",
        normalized_value="SHIP-BLR-20260802-4421",
    )
    ocr_claim = EvidenceClaim(
        id="CLM-OCR",
        dispute_id=base_dispute.id,
        document_id="DOC-LABEL",
        field_name="tracking_id",
        raw_value="SHIP-BLR-2O26O8O2-4421",
        normalized_value="SHIP-BLR-2O26O8O2-4421",
    )
    issues = validate_identifiers(base_dispute, [carrier_claim, ocr_claim], [carrier_doc])
    assert carrier_claim.verification_status == VerificationStatus.VERIFIED
    assert ocr_claim.verification_status == VerificationStatus.NEEDS_REVIEW
    assert any(i.rule_id == "tracking_ocr_confirmation" for i in issues)


# ── 2. Amount Validation Tests ───────────────────────────────────────────────

def test_exact_decimal_amount_match_passes(base_dispute):
    claim = EvidenceClaim(
        id="CLM-AMT",
        dispute_id=base_dispute.id,
        document_id="DOC-INV",
        field_name="amount",
        raw_value="₹18,400.00",
        normalized_value="18400.00",
    )
    issues = validate_amounts(base_dispute, [claim])
    assert len(issues) == 0
    assert claim.verification_status == VerificationStatus.VERIFIED


def test_incorrect_amount_fails(base_dispute):
    claim = EvidenceClaim(
        id="CLM-AMT",
        dispute_id=base_dispute.id,
        document_id="DOC-INV",
        field_name="amount",
        raw_value="₹4,800.00",
        normalized_value="4800.00",
    )
    issues = validate_amounts(base_dispute, [claim])
    assert len(issues) == 1
    assert issues[0].rule_id == "amount_match"
    assert claim.verification_status == VerificationStatus.FAILED


# ── 3. Delivery & Deadline Validation Tests ──────────────────────────────────

def test_valid_delivery_before_deadline_passes(base_dispute):
    carrier_doc = EvidenceDocument(
        id="DOC-TRK",
        dispute_id=base_dispute.id,
        type=EvidenceType.TRACKING_RECORD,
        source="carrier_api",
    )
    status_claim = EvidenceClaim(
        id="CLM-STAT",
        dispute_id=base_dispute.id,
        document_id="DOC-TRK",
        field_name="delivery_status",
        raw_value="Delivered",
        normalized_value="delivered",
    )
    date_claim = EvidenceClaim(
        id="CLM-DATE",
        dispute_id=base_dispute.id,
        document_id="DOC-TRK",
        field_name="delivery_datetime",
        raw_value="03-Aug-2026 14:22",
        normalized_value="2026-08-03T14:22:00",
    )
    issues = validate_delivery(base_dispute, [status_claim, date_claim], [carrier_doc])
    assert len(issues) == 0
    assert status_claim.verification_status == VerificationStatus.VERIFIED
    assert date_claim.verification_status == VerificationStatus.VERIFIED


def test_late_delivery_after_dispute_filed_fails(base_dispute):
    """Delivery date (25-Aug) is AFTER dispute was filed (20-Aug)."""
    carrier_doc = EvidenceDocument(
        id="DOC-TRK",
        dispute_id=base_dispute.id,
        type=EvidenceType.TRACKING_RECORD,
        source="carrier_api",
    )
    status_claim = EvidenceClaim(
        id="CLM-STAT",
        dispute_id=base_dispute.id,
        document_id="DOC-TRK",
        field_name="delivery_status",
        raw_value="Delivered",
        normalized_value="delivered",
    )
    date_claim = EvidenceClaim(
        id="CLM-DATE",
        dispute_id=base_dispute.id,
        document_id="DOC-TRK",
        field_name="delivery_datetime",
        raw_value="25-Aug-2026 10:00",
        normalized_value="2026-08-25T10:00:00",
    )
    issues = validate_delivery(base_dispute, [status_claim, date_claim], [carrier_doc])
    assert len(issues) == 1
    assert issues[0].rule_id == "delivery_before_deadline"
    assert status_claim.verification_status == VerificationStatus.FAILED
    assert date_claim.verification_status == VerificationStatus.FAILED


# ── 4. Provenance Preservation Tests ─────────────────────────────────────────

def test_claim_provenance_is_preserved():
    doc = EvidenceDocument(
        id="DOC-001-INV",
        dispute_id="DSP-2026-001",
        type=EvidenceType.INVOICE,
        source="merchant_upload",
        extraction_method=ExtractionMethod.DIRECT_TEXT,
        extraction_confidence=0.98,
        raw_text="Order: ORD-20260801-7834\nTotal: ₹18,400.00",
    )
    claim = EvidenceClaim(
        id="CLM-DOC-001-INV-order_id-L1",
        dispute_id=doc.dispute_id,
        document_id=doc.id,
        field_name="order_id",
        raw_value="ORD-20260801-7834",
        normalized_value="ORD-20260801-7834",
        source_page=1,
        source_location="line 1",
        extraction_method=doc.extraction_method,
        extraction_confidence=doc.extraction_confidence,
    )
    assert claim.document_id == "DOC-001-INV"
    assert claim.source_page == 1
    assert claim.source_location == "line 1"
    assert claim.raw_value == "ORD-20260801-7834"
    assert claim.extraction_confidence == 0.98
