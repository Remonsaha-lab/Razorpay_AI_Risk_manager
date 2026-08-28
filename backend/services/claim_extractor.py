"""Deterministic extraction of source-provenanced evidence claims."""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from backend.domain.enums import EvidenceType, VerificationStatus
from backend.domain.models import EvidenceClaim, EvidenceDocument


def normalize_order_id(raw: str) -> str:
    """Normalize formatting only; do not repair identifier characters."""
    return raw.strip().upper()


def normalize_tracking_id(raw: str) -> str:
    """Normalize case only; preserve OCR ambiguities such as O/0 and l/1."""
    return raw.strip().upper()


def normalize_amount(raw: str) -> str | None:
    """Return an exact two-decimal value without changing its monetary meaning."""
    cleaned = re.sub(r"(?:\u20b9|INR|Rs\.?)", "", raw, flags=re.IGNORECASE)
    cleaned = cleaned.replace(",", "").strip()
    try:
        return f"{Decimal(cleaned):.2f}"
    except (InvalidOperation, ValueError):
        return None


def normalize_text(raw: str) -> str:
    return " ".join(raw.strip().lower().split())


def normalize_delivery_status(raw: str) -> str:
    lowered = raw.strip().lower()
    if "delivered" in lowered:
        return "delivered"
    if "attempt" in lowered:
        return "delivery_attempted"
    if any(term in lowered for term in ("in transit", "transit", "picked up", "out for delivery")):
        return "in_transit"
    if "held" in lowered:
        return "held_at_facility"
    return " ".join(lowered.split())


def normalize_delivery_datetime(raw: str) -> str | None:
    """Normalize supported fixture dates without inventing a document timezone."""
    cleaned = " ".join(raw.replace(" at ", " ").split())
    for date_format in ("%d-%b-%Y %H:%M", "%d-%b-%Y"):
        try:
            return datetime.strptime(cleaned, date_format).isoformat()
        except ValueError:
            continue
    return None


RE_ORDER_ID = re.compile(
    r"(?:Order(?:\s*ID|\s*Ref|\s*No|\s*Number)?\s*[:#\-]?\s*)([A-Za-z0-9_-]+)",
    re.IGNORECASE,
)
RE_TRACKING_ID = re.compile(
    r"(?:Tracking(?:\s*ID|\s*No|\s*Number)?\s*[:#\-]?\s*)([A-Za-z0-9][A-Za-z0-9_-]+)",
    re.IGNORECASE,
)
RE_TOTAL_AMOUNT = re.compile(
    r"(?:(?:Total|Amount|Price)\s*[:#\-]?\s*)((?:(?:\u20b9|INR|Rs\.?)\s*)?[\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
RE_CARRIER = re.compile(
    r"(?:Carrier)\s*[:#\-]?\s*([A-Za-z0-9 ]+?)(?=\s*(?:Tracking|Shipper|Order|Status|$))",
    re.IGNORECASE,
)
RE_SHIP_TO = re.compile(r"Ship\s*To\s*:\s*([^,\n]+)(?:,\s*([^\n]+))?", re.IGNORECASE)
RE_LABEL_TO = re.compile(r"(?:To|Recipient)\s*:\s*([^,\n]+)(?:,\s*([^\n]+))?", re.IGNORECASE)
RE_DELIVERED_LINE = re.compile(
    r"(?:Delivered(?:\s*on|\s*to|\s*at)?\s*[:#\-]?\s*)([0-9]{1,2}-[A-Za-z]{3}-[0-9]{4}(?:\s*(?:at\s*)?[0-9]{1,2}:[0-9]{2})?)",
    re.IGNORECASE,
)
RE_DELIVERY_STATUS_HISTORY = re.compile(
    r"(\d{1,2}-[A-Za-z]{3}-\d{4}(?:\s+\d{2}:\d{2})?)\s*[-—]\s*(Delivered|In transit|Out for delivery|Picked up|DELIVERY ATTEMPTED|Held at facility)",
    re.IGNORECASE,
)
RE_DELIVERED_TO = re.compile(
    r"(?:Delivered(?:\s+on)?\s*:?\s*[0-9]{1,2}-[A-Za-z]{3}-[0-9]{4}"
    r"(?:\s*(?:at\s*)?[0-9]{1,2}:[0-9]{2})?\s+to\s+)(.+?)(?:\s+at\s+|$)",
    re.IGNORECASE,
)


def _make_claim(
    document: EvidenceDocument,
    field_name: str,
    raw_value: str,
    normalized_value: str,
    line_number: int,
) -> EvidenceClaim:
    return EvidenceClaim(
        id=f"CLM-{document.id}-{field_name}-L{line_number}",
        dispute_id=document.dispute_id,
        document_id=document.id,
        field_name=field_name,
        raw_value=raw_value,
        normalized_value=normalized_value,
        source_page=1,
        source_location=f"line {line_number}",
        verification_status=VerificationStatus.PENDING,
        verification_reason="Awaiting deterministic validation",
        extraction_method=document.extraction_method,
        extraction_confidence=document.extraction_confidence,
    )


ALLOWED_FIELDS: dict[EvidenceType, set[str]] = {
    EvidenceType.INVOICE: {"order_id", "amount", "recipient_name", "shipping_address"},
    EvidenceType.ORDER_CONFIRMATION: {"order_id", "amount", "recipient_name", "shipping_address"},
    EvidenceType.TRACKING_RECORD: {
        "carrier_name", "tracking_id", "order_id", "delivery_status", "delivery_datetime",
        "recipient_name", "shipping_address",
    },
    EvidenceType.PROOF_OF_DELIVERY: {
        "tracking_id", "delivery_status", "delivery_datetime", "recipient_name", "shipping_address",
    },
    EvidenceType.SHIPPING_LABEL: {"tracking_id", "order_id", "recipient_name", "shipping_address"},
}


def extract_claims(document: EvidenceDocument) -> list[EvidenceClaim]:
    """Extract factual claims from one document; never verify or compare them."""
    if not document.raw_text:
        return []

    allowed_fields = ALLOWED_FIELDS.get(document.type, set())
    if not allowed_fields:
        return []

    claims: list[EvidenceClaim] = []
    extracted_fields: set[str] = set()
    lines = document.raw_text.splitlines()

    for line_number, line in enumerate(lines, start=1):
        text = line.strip()
        if not text:
            continue

        def add(field_name: str, raw_value: str, normalized_value: str) -> None:
            if field_name in allowed_fields and field_name not in extracted_fields:
                claims.append(_make_claim(document, field_name, raw_value, normalized_value, line_number))
                extracted_fields.add(field_name)

        if (match := RE_ORDER_ID.search(text)) and "order_id" not in extracted_fields:
            add("order_id", match.group(1), normalize_order_id(match.group(1)))

        if (match := RE_TOTAL_AMOUNT.search(text)) and "amount" not in extracted_fields:
            raw_amount = match.group(1)
            normalized_amount = normalize_amount(raw_amount)
            if normalized_amount:
                add("amount", raw_amount, normalized_amount)

        if (match := RE_CARRIER.search(text)) and "carrier_name" not in extracted_fields:
            raw_carrier = match.group(1).strip()
            add("carrier_name", raw_carrier, normalize_text(raw_carrier))

        if (match := RE_TRACKING_ID.search(text)) and "tracking_id" not in extracted_fields:
            add("tracking_id", match.group(1), normalize_tracking_id(match.group(1)))

        # A timeline may start with "Picked up". Only a final delivered event may
        # populate delivery-specific claims used by the later deadline validator.
        if "delivery_status" in allowed_fields:
            if (match := RE_DELIVERY_STATUS_HISTORY.search(text)):
                raw_datetime, raw_status = match.groups()
                if normalize_delivery_status(raw_status) == "delivered":
                    normalized_datetime = normalize_delivery_datetime(raw_datetime)
                    if normalized_datetime:
                        add("delivery_datetime", raw_datetime, normalized_datetime)
                    add("delivery_status", raw_status, "delivered")

            if (match := RE_DELIVERED_LINE.search(text)):
                raw_datetime = match.group(1).strip()
                normalized_datetime = normalize_delivery_datetime(raw_datetime)
                if normalized_datetime:
                    add("delivery_status", "Delivered", "delivered")
                    add("delivery_datetime", raw_datetime, normalized_datetime)

            if (match := RE_DELIVERED_TO.search(text)) and "recipient_name" not in extracted_fields:
                add("recipient_name", match.group(1).strip(), normalize_text(match.group(1)))

        if "recipient_name" not in extracted_fields and (match := RE_SHIP_TO.search(text)):
            add("recipient_name", match.group(1).strip(), normalize_text(match.group(1)))
            if match.group(2):
                add("shipping_address", match.group(2).strip(), normalize_text(match.group(2)))
            elif line_number < len(lines):
                next_line = lines[line_number].strip()
                if next_line and not re.match(r"(?:Payment|Transaction|Item|Total|Order)\s*:", next_line, re.IGNORECASE):
                    add("shipping_address", next_line, normalize_text(next_line))

        if "recipient_name" not in extracted_fields and (match := RE_LABEL_TO.search(text)):
            add("recipient_name", match.group(1).strip(), normalize_text(match.group(1)))
            if match.group(2):
                add("shipping_address", match.group(2).strip(), normalize_text(match.group(2)))

        if "shipping_address" not in extracted_fields and text.lower().startswith("address:"):
            raw_address = text.split(":", 1)[1].strip()
            add("shipping_address", raw_address, normalize_text(raw_address))

    return claims


def extract_claims_for_case(documents: list[EvidenceDocument]) -> list[EvidenceClaim]:
    """Extract claims across all documents for one synthetic dispute."""
    return [claim for document in documents for claim in extract_claims(document)]
