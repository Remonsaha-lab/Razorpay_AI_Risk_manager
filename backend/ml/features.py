"""
backend/ml/features.py

Feature engineering for the XGBoost dispute outcome predictor.

IMPORTANT DESIGN RULE:
  This module NEVER reimplements validation logic.
  It runs the deterministic workflow and reads numbers off the results.

  Case fixture
      ↓
  run_workflow(dispute, documents)   ← all real validation happens here
      ↓
  build_features(case, workflow_result)  ← only reads output numbers
      ↓
  Feature vector [float, float, ...]
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

# ── Feature schema (MUST stay in this exact order forever) ──────────────────
# Changing this list invalidates any previously saved model artifact.
FEATURE_NAMES: list[str] = [
    # ── Layer 1: Case-level (from fixture, no workflow needed) ──
    "amount_log",                        # log(amount+1) — reduces skew from ₹500 to ₹500,000
    "amount_raw",                        # raw INR amount
    "days_remaining",                    # (respond_by - now).days, clamped to [−60, 120]
    "deadline_already_passed",           # 1 if respond_by < now
    "reason_merchandise_not_received",   # one-hot: dispute reason
    "reason_services_not_received",      # one-hot
    "reason_wrong_item",                 # one-hot
    "reason_other",                      # one-hot: catch-all
    "risk_level_low",                    # one-hot: risk level
    "risk_level_medium",                 # one-hot
    "risk_level_high",                   # one-hot
    "risk_level_critical",               # one-hot
    "n_docs_attached",                   # total documents attached
    "has_invoice_doc",                   # 1 if any doc type == invoice
    "has_tracking_doc",                  # 1 if any doc type == tracking_record
    "has_pod_doc",                       # 1 if any doc type == proof_of_delivery
    "has_shipping_label_doc",            # 1 if any doc type == shipping_label
    "has_ocr_doc",                       # 1 if any doc has extraction_method == ocr
    "min_ocr_confidence",                # lowest OCR confidence score across docs (1.0 if none)

    # ── Layer 2: Workflow output — decision-level ──
    "completeness_score",                # fraction of required docs with ≥1 VERIFIED claim
    "evidence_strength",                 # explainable scoring function output [0, 1]
    "contest_ev_normalised",             # contest_EV / amount  (sign-preserving)
    "accept_ev_normalised",              # accept_EV / amount   (always -1.0)

    # ── Layer 2: Workflow output — claim-level counts ──
    "n_claims_total",                    # total claims extracted
    "n_claims_verified",                 # VERIFIED claims
    "n_claims_failed",                   # FAILED claims
    "n_claims_pending",                  # PENDING / unresolved claims
    "pct_claims_verified",               # n_verified / n_total (0 if n_total == 0)

    # ── Layer 2: Workflow output — specific field verification ──
    "has_verified_order_id",             # order_id claim is VERIFIED
    "has_verified_amount",               # amount claim is VERIFIED
    "has_verified_tracking_id",          # tracking_id claim is VERIFIED
    "has_verified_delivery_status",      # delivery_status claim is VERIFIED
    "has_verified_recipient",            # recipient_name claim is VERIFIED
    "has_verified_address",              # shipping_address claim is VERIFIED

    # ── Layer 2: Workflow output — validation issues ──
    "n_issues_total",                    # total ValidationIssue count
    "has_amount_mismatch",               # rule_id == "amount_match"
    "has_order_id_mismatch",             # rule_id == "order_id_match"
    "has_late_delivery",                 # rule_id == "delivery_before_deadline"
    "has_no_delivery_event",             # rule_id == "delivery_independent"
    "has_ocr_unconfirmed",               # rule_id == "tracking_ocr_confirmation"
    "has_address_conflict",              # rule_id == "address_consistency"
    "n_blocking_issues",                 # issues excluding tracking_ocr_confirmation
]

# Canonical reason → index mapping
_REASON_MAP: dict[str, str] = {
    "merchandise_not_received": "reason_merchandise_not_received",
    "services_not_received":    "reason_services_not_received",
    "wrong_item":               "reason_wrong_item",
}

# Canonical risk level → feature name
_RISK_MAP: dict[str, str] = {
    "low":      "risk_level_low",
    "medium":   "risk_level_medium",
    "high":     "risk_level_high",
    "critical": "risk_level_critical",
}


def build_features(
    case_fixture: dict,
    workflow_result: dict,
    as_of: datetime | None = None,
) -> dict[str, float]:
    """
    Convert one case fixture + its workflow result into a flat numeric feature dict.

    Parameters
    ----------
    case_fixture : dict
        Raw JSON object from cases.json for one dispute case.
    workflow_result : dict
        Output of run_workflow(dispute, documents) — contains:
          decision, claims (list[EvidenceClaim]), issues (list[dict]), missing_evidence

    Returns
    -------
    dict[str, float]
        Keys match FEATURE_NAMES exactly, in the same order.
        Also includes "case_id" and "won_contest" label (when available).
    """
    # Training must be reproducible. Production callers can pass the current
    # time explicitly; otherwise use a stable reference timestamp.
    now = as_of or datetime(2026, 8, 29, tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    # ── Parse case-level values ─────────────────────────────────────────────
    amount = float(case_fixture.get("amount", 0) or 0)

    # Days remaining before response deadline
    respond_by_str = case_fixture.get("respond_by", "")
    try:
        respond_by = datetime.fromisoformat(respond_by_str)
        if respond_by.tzinfo is None:
            respond_by = respond_by.replace(tzinfo=timezone.utc)
        days_remaining = (respond_by - now).days
    except (ValueError, TypeError):
        days_remaining = 0

    # Document-level features
    docs = case_fixture.get("evidence_documents", [])
    doc_types = {d.get("type", "") for d in docs}
    ocr_docs = [d for d in docs if d.get("extraction_method") == "ocr"]
    min_ocr_conf = min((d.get("extraction_confidence", 1.0) for d in ocr_docs), default=1.0)

    # ── Unpack workflow result ───────────────────────────────────────────────
    decision = workflow_result.get("decision")
    claims   = workflow_result.get("claims", [])
    issues   = workflow_result.get("issues", [])   # list of dicts (serialised ValidationIssue)

    # Decision-level numbers
    completeness    = float(_value(decision, "completeness_score", 0) or 0)
    evidence_str    = float(_value(decision, "evidence_strength",  0) or 0)

    contest_ev_raw  = _value(decision, "contest_expected_value", Decimal("0"))
    accept_ev_raw   = _value(decision, "accept_expected_value",  Decimal("-1"))
    contest_ev_norm = float(contest_ev_raw) / amount if amount else 0.0
    accept_ev_norm  = float(accept_ev_raw)  / amount if amount else -1.0

    # Claim-level aggregates
    n_total    = len(claims)
    n_verified = sum(1 for c in claims if _status(c) == "verified")
    n_failed   = sum(1 for c in claims if _status(c) == "failed")
    n_pending  = sum(1 for c in claims if _status(c) in ("pending", "needs_review"))
    pct_verified = n_verified / n_total if n_total else 0.0

    # Verified field lookup
    verified_fields = {c.field_name for c in claims if _status(c) == "verified"}

    # Issue rule IDs
    issue_rules = {i.get("rule_id", "") if isinstance(i, dict) else getattr(i, "rule_id", "") for i in issues}
    n_blocking  = sum(
        1 for i in issues
        if (i.get("rule_id", "") if isinstance(i, dict) else getattr(i, "rule_id", "")) != "tracking_ocr_confirmation"
    )

    # ── Assemble feature dict ────────────────────────────────────────────────
    feat: dict[str, float] = {
        # Layer 1 — case fixture
        "amount_log":                      math.log1p(amount),
        "amount_raw":                      amount,
        "days_remaining":                  max(-60, min(120, days_remaining)),
        "deadline_already_passed":         1.0 if days_remaining < 0 else 0.0,

        # Reason one-hot
        "reason_merchandise_not_received": 0.0,
        "reason_services_not_received":    0.0,
        "reason_wrong_item":               0.0,
        "reason_other":                    0.0,

        # Risk level one-hot
        "risk_level_low":      0.0,
        "risk_level_medium":   0.0,
        "risk_level_high":     0.0,
        "risk_level_critical": 0.0,

        # Document counts/flags
        "n_docs_attached":      float(len(docs)),
        "has_invoice_doc":      1.0 if "invoice"          in doc_types else 0.0,
        "has_tracking_doc":     1.0 if "tracking_record"  in doc_types else 0.0,
        "has_pod_doc":          1.0 if "proof_of_delivery" in doc_types else 0.0,
        "has_shipping_label_doc": 1.0 if "shipping_label" in doc_types else 0.0,
        "has_ocr_doc":          1.0 if ocr_docs else 0.0,
        "min_ocr_confidence":   float(min_ocr_conf),

        # Layer 2 — decision
        "completeness_score":    completeness,
        "evidence_strength":     evidence_str,
        "contest_ev_normalised": contest_ev_norm,
        "accept_ev_normalised":  accept_ev_norm,

        # Layer 2 — claim counts
        "n_claims_total":    float(n_total),
        "n_claims_verified": float(n_verified),
        "n_claims_failed":   float(n_failed),
        "n_claims_pending":  float(n_pending),
        "pct_claims_verified": pct_verified,

        # Layer 2 — specific field verification
        "has_verified_order_id":       1.0 if "order_id"         in verified_fields else 0.0,
        "has_verified_amount":         1.0 if "amount"           in verified_fields else 0.0,
        "has_verified_tracking_id":    1.0 if "tracking_id"      in verified_fields else 0.0,
        "has_verified_delivery_status":1.0 if "delivery_status"  in verified_fields else 0.0,
        "has_verified_recipient":      1.0 if "recipient_name"   in verified_fields else 0.0,
        "has_verified_address":        1.0 if "shipping_address" in verified_fields else 0.0,

        # Layer 2 — issues
        "n_issues_total":       float(len(issues)),
        "has_amount_mismatch":  1.0 if "amount_match"              in issue_rules else 0.0,
        "has_order_id_mismatch":1.0 if "order_id_match"            in issue_rules else 0.0,
        "has_late_delivery":    1.0 if "delivery_before_deadline"  in issue_rules else 0.0,
        "has_no_delivery_event":1.0 if "delivery_event"            in issue_rules else 0.0,
        "has_ocr_unconfirmed":  1.0 if "tracking_ocr_confirmation" in issue_rules else 0.0,
        "has_address_conflict": 1.0 if "address_consistency"       in issue_rules else 0.0,
        "n_blocking_issues":    float(n_blocking),
    }

    # Set one-hot fields from reason
    reason_key = _REASON_MAP.get(case_fixture.get("reason", ""), "reason_other")
    feat[reason_key] = 1.0

    # Set one-hot field from risk_level
    risk_key = _RISK_MAP.get(str(case_fixture.get("risk_level", "")).lower(), None)
    if risk_key:
        feat[risk_key] = 1.0

    # ── Metadata (not used by model, stripped before training) ──────────────
    feat["_case_id"] = case_fixture.get("id", "")

    # Ground-truth label (present in fixture, stripped during inference)
    won = case_fixture.get("won")
    if won is not None:
        feat["won_contest"] = 1.0 if won else 0.0

    return feat


def features_as_vector(feat: dict[str, float]) -> list[float]:
    """
    Return features in the canonical FEATURE_NAMES order as a plain list.
    Use this when feeding to XGBoost — order MUST match the training schema.
    Missing keys default to 0.0.
    """
    return [feat.get(name, 0.0) for name in FEATURE_NAMES]


def _status(claim) -> str:
    """Safely extract verification_status string from an EvidenceClaim object."""
    status = getattr(claim, "verification_status", None)
    if status is None:
        return "pending"
    # Handles both enum and plain string
    return status.value if hasattr(status, "value") else str(status)


def _value(obj: Any, name: str, default: Any = None) -> Any:
    """Read a field from either a Pydantic/model object or a dictionary."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)
