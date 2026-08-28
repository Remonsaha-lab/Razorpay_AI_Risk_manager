"""Shared validation result types and conservative helpers."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import re

from backend.domain.models import EvidenceClaim


@dataclass
class ValidationIssue:
    rule_id: str
    severity: str
    message: str
    claim_ids: list[str] = field(default_factory=list)


def parse_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value.replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def normalized_text(value: str) -> str:
    return " ".join(value.lower().split())


def mark(claim: EvidenceClaim, status, reason: str) -> None:
    """The only shared mutation point for deterministic verification."""
    claim.verification_status = status
    claim.verification_reason = reason


def claims_for(claims: list[EvidenceClaim], field: str) -> list[EvidenceClaim]:
    return [claim for claim in claims if claim.field_name == field]
