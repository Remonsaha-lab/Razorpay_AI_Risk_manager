from backend.domain.enums import VerificationStatus
from backend.services.case_loader import CaseStore
from backend.services.claim_extractor import extract_claims


def _document(case_id: str, document_id: str):
    store = CaseStore()
    store.load()
    return next(
        document
        for document in store.get_documents_for_dispute(case_id)
        if document.id == document_id
    )


def _claim(claims, field_name: str):
    return next(claim for claim in claims if claim.field_name == field_name)


def test_invoice_retains_raw_currency_and_normalizes_amount():
    amount = _claim(extract_claims(_document("DSP-2026-001", "DOC-001-INV")), "amount")

    assert amount.raw_value == "\u20b918,400.00"
    assert amount.normalized_value == "18400.00"
    assert amount.verification_status == VerificationStatus.PENDING


def test_tracking_record_uses_delivered_event_not_pickup_event():
    claims = extract_claims(_document("DSP-2026-001", "DOC-001-TRK"))

    assert _claim(claims, "delivery_status").normalized_value == "delivered"
    assert _claim(claims, "delivery_datetime").normalized_value == "2026-08-03T14:22:00"
    assert all(claim.normalized_value != "in_transit" for claim in claims)


def test_ocr_tracking_id_preserves_character_ambiguity():
    tracking_id = _claim(extract_claims(_document("DSP-2026-015", "DOC-015-OCR")), "tracking_id")

    assert tracking_id.raw_value == "SHIP-CCU-20260805-l6l1"
    assert tracking_id.normalized_value == "SHIP-CCU-20260805-L6L1"
    assert tracking_id.extraction_confidence == 0.74


def test_claims_keep_provenance_and_await_validation():
    claims = extract_claims(_document("DSP-2026-001", "DOC-001-POD"))

    assert claims
    for claim in claims:
        assert claim.document_id == "DOC-001-POD"
        assert claim.source_location.startswith("line ")
        assert claim.verification_status == VerificationStatus.PENDING
        assert claim.verification_reason == "Awaiting deterministic validation"
