"""Fixture loader — reads synthetic cases from JSON into domain models."""
"""
it converts JSON fixture data into typed Dispute and EvidenceDocument objects, so every later step uses one consistent data contract.

"""
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Optional

from backend.domain.models import Dispute, EvidenceDocument
from backend.domain.enums import (
    DisputeReason,
    DisputeStatus,
    EvidenceType,
    ExtractionMethod,
    RiskLevel,
)

# ── Path to fixtures (relative to repo root) ──
FIXTURES_PATH = Path(__file__).parent.parent.parent / "data" / "fixtures" / "cases.json"


def _parse_evidence_doc(raw: dict, dispute_id: str) -> EvidenceDocument:
    """Convert a raw JSON evidence document into a domain model."""
    return EvidenceDocument(
        id=raw["id"],
        dispute_id=dispute_id,
        type=EvidenceType(raw["type"]),
        filename=raw.get("filename", ""),
        source=raw.get("source", "unknown"),
        extraction_method=ExtractionMethod(raw.get("extraction_method", "direct_text")),
        extraction_confidence=raw.get("extraction_confidence", 1.0),
        raw_text=raw.get("raw_text", ""),
    )


def _parse_dispute(raw: dict) -> Dispute:
    """Convert a raw JSON case into a Dispute domain model."""
    return Dispute(
        id=raw["id"],
        merchant_name=raw["merchant_name"],
        merchant_id=raw.get("merchant_id", ""),
        transaction_id=raw["transaction_id"],
        order_id=raw["order_id"],
        amount=Decimal(raw["amount"]),
        currency=raw.get("currency", "INR"),
        transaction_date=datetime.fromisoformat(raw["transaction_date"]),
        reason=DisputeReason(raw["reason"]),
        reason_description=raw.get("reason_description", ""),
        status=DisputeStatus.PENDING_REVIEW,
        risk_level=RiskLevel(raw.get("risk_level", "medium")),
        filed_date=datetime.fromisoformat(raw["filed_date"]),
        respond_by=datetime.fromisoformat(raw["respond_by"]),
        customer_name=raw.get("customer_name", ""),
        customer_email=raw.get("customer_email", ""),
        shipping_address=raw.get("shipping_address", ""),
        billing_address=raw.get("billing_address", ""),
        evidence_document_ids=[doc["id"] for doc in raw.get("evidence_documents", [])],
    )


class CaseStore:
    """
    In-memory store for synthetic dispute cases.

    Loaded once at startup. In production this would be a database,
    but for the prototype a simple dict lookup is sufficient.
    """

    def __init__(self):
        self._disputes: dict[str, Dispute] = {}
        self._documents: dict[str, EvidenceDocument] = {}
        self._case_metadata: dict[str, dict] = {}  # extra fields like case_type, expected_action

    def load(self, path: Path = FIXTURES_PATH) -> None:
        """Load all cases from the fixtures JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._disputes.clear()
        self._documents.clear()
        self._case_metadata.clear()

        for raw_case in data.get("cases", []):
            # Parse the dispute
            dispute = _parse_dispute(raw_case)
            self._disputes[dispute.id] = dispute

            # Parse each evidence document
            for raw_doc in raw_case.get("evidence_documents", []):
                doc = _parse_evidence_doc(raw_doc, dispute.id)
                self._documents[doc.id] = doc

            # Store metadata for evaluation later
            self._case_metadata[raw_case["id"]] = {
                "case_type": raw_case.get("case_type", ""),
                "expected_action": raw_case.get("expected_action", ""),
                "notes": raw_case.get("notes", ""),
            }

    def get_all_disputes(self) -> list[Dispute]:
        return list(self._disputes.values())

    def get_dispute(self, dispute_id: str) -> Optional[Dispute]:
        return self._disputes.get(dispute_id)

    def get_documents_for_dispute(self, dispute_id: str) -> list[EvidenceDocument]:
        return [doc for doc in self._documents.values() if doc.dispute_id == dispute_id]

    def get_document(self, doc_id: str) -> Optional[EvidenceDocument]:
        return self._documents.get(doc_id)

    def get_case_metadata(self, dispute_id: str) -> dict:
        return self._case_metadata.get(dispute_id, {})


# ── Singleton instance ──
# Created once, imported everywhere. Call store.load() at app startup.
store = CaseStore()
