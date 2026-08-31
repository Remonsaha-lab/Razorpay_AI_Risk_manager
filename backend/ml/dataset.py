"""
backend/ml/dataset.py
Loads all labeled cases from fixtures, runs the workflow for each,
builds feature vectors, and returns train/validation splits.
Split: 70% train, 30% validation (stratified, fixed seed).
No test set — evaluation uses cross-validation on the training set.
"""
from __future__ import annotations
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
from datetime import datetime, timezone
from backend.domain.models import Dispute, EvidenceDocument
from backend.domain.enums import (
    DisputeReason, DisputeStatus, EvidenceType, ExtractionMethod, RiskLevel,
)
from backend.ml.features import FEATURE_NAMES, build_features, features_as_vector
from backend.workflow.engine import run_workflow

# configration
FIXTURES_PATH = Path(__file__).parent.parent.parent / "data" / "fixtures" / "cases.json"
HELD_OUT_TEST_PATH = Path(__file__).parent.parent.parent / "data" / "held_out" / "test.json"
RANDOM_SEED = 42
TRAIN_RATIO = 0.80  # 80% train, 20% validation
# Stable reference timestamp so feature values are reproducible
REFERENCE_NOW = datetime(2026, 8, 29, tzinfo=timezone.utc)


# Fixtures -> Domain model converters

def _parse_dispute(raw:dict) -> Dispute:
    """Convert a raw fixture dict into a typed Dispute domain object."""
    return Dispute(
        id=raw["id"],
        merchant_name=raw.get("merchant_name", ""),
        merchant_id=raw.get("merchant_id", ""),
        transaction_id=raw.get("transaction_id", ""),
        order_id=raw.get("order_id", ""),
        amount=raw.get("amount", "0"),
        currency=raw.get("currency", "INR"),
        transaction_date=datetime.fromisoformat(raw["transaction_date"]),
        reason=DisputeReason(raw.get("reason", "merchandise_not_received")),
        reason_description=raw.get("reason_description", ""),
        status=DisputeStatus.PENDING_REVIEW,
        risk_level=RiskLevel(raw.get("risk_level", "medium")),
        filed_date=datetime.fromisoformat(raw["filed_date"]),
        respond_by=datetime.fromisoformat(raw["respond_by"]),
        customer_name=raw.get("customer_name"),
        customer_email=raw.get("customer_email"),
        shipping_address=raw.get("shipping_address"),
        billing_address=raw.get("billing_address"),
    )

def _parse_documents(raw:dict) -> list[EvidenceDocument]:
    """Convert raw evidence_documents list into typed EvidenceDocument objects."""
    docs = []
    for d in raw.get("evidence_documents", []):
        raw_method = d.get("extraction_method", "direct_text")
        try:
            method = ExtractionMethod(raw_method)
        except ValueError:
            method = ExtractionMethod.DIRECT_TEXT
        docs.append(EvidenceDocument(
            id=d["id"],
            dispute_id=raw["id"],
            type=EvidenceType(d["type"]),
            filename=d.get("filename", ""),
            source=d.get("source", ""),
            extraction_method=method,
            extraction_confidence=float(d.get("extraction_confidence", 1.0)),
            raw_text=d.get("raw_text", ""),
        ))
    return docs

# Load dataset

def load_all_features(
    fixtures_path: Path = FIXTURES_PATH,
    as_of: datetime = REFERENCE_NOW,
    skip_unlabeled: bool = True
    ) -> list[dict]:
    """Run workflow for all cases and return per-case feature dicts."""
    """
    Load fixture cases, run deterministic validation, and
    generate ML features.

    Parameters
    ----------
    fixtures_path:
        Location of cases.json.

    as_of:
        Reference timestamp used for time-dependent features.

    skip_unlabeled:
        If True, cases without a `won` ground-truth label
        are excluded.

    Returns
    -------
    list[dict]
        Feature dictionaries.

        Each row contains:
            - FEATURE_NAMES
            - _case_id
            - won_contest
    """
    
    raw_data = json.loads(fixtures_path.read_text(encoding = "utf-8"))
    cases = raw_data.get("cases", [])
    if not cases:
        raise ValueError("No cases found")

    if not isinstance(cases , list):
        raise ValueError("Expected cases to be a list in case.json")

    # process cases

    rows: list[dict] = []

    skipped_no_label = 0
    skipped_error = 0

    for case_raw in cases:
        case_id = case_raw.get(
            "id",
            "?"
        )

        # ground truth label

        won = case_raw.get("won")

        if skip_unlabeled and won is None:
            skipped_no_label += 1
            continue

        # make sure the target in Binary

        if won not in (0 , 1, True , False):
            print(f"[dataset] skipping {case_id}",
            f"invalid won label: {won!r}")

            skipped_error += 1
            continue

        try:
            #Fixture -> Domain objects

            dispute = _parse_dispute(case_raw)
            documents = _parse_documents(case_raw)

            #Deterministic workflow

            workflow_result = run_workflow(dispute, documents)

            # Workflow result -> Ml features
            features = build_features(
                case_raw,
                workflow_result,
                as_of=as_of
            )  

            #attach meta data
            features["_case_id"] = case_id

            # This is the actual historical/synthetic outcome.
            #
            # IMPORTANT:
            # This must NOT be the policy recommendation.
            features["won_contest"] = float(bool(won))

            rows.append(features)

        except Exception as exc:
            skipped_error += 1

            print(
                f"[dataset] Skipping {case_id}: {exc}"
            ) 

    print(
        f"[dataset] Loaded {len(rows)} labeled cases "
        f"(skipped {skipped_no_label} unlabeled, "
        f"{skipped_error} errors)"
    )

    if not rows:
        raise ValueError(
            "No labeled cases were successfully loaded."
        )

    return rows


def load_held_out_features(
    as_of: datetime = REFERENCE_NOW,
) -> list[dict]:
    """Load labeled cases reserved exclusively for final model evaluation."""
    return load_all_features(fixtures_path=HELD_OUT_TEST_PATH, as_of=as_of)


### Train / validation split

def make_splits(
    rows: list[dict] | None = None,
    train_ratio: float = TRAIN_RATIO,
    seed: int = RANDOM_SEED,
) -> tuple[
    list[list[float]],
    list[float],
    list[list[float]],
    list[float],
]:
    """
    Create a stratified train/validation split.

    There is intentionally NO test set.

    Parameters
    ----------
    rows:
        Feature rows returned by load_all_features().

        If None, the fixture dataset is loaded automatically.

    train_ratio:
        Fraction of cases used for training.

        Default:
            0.70 → 70% train
            0.30 → 30% validation

    seed:
        Random seed used for reproducibility.

    Returns
    -------
    X_train, y_train, X_val, y_val

    X_train:
        Training feature vectors.

    y_train:
        Training labels.

    X_val:
        Validation feature vectors.

    y_val:
        Validation labels.
    """

    if rows is None:
        rows = load_all_features()

    # build x and y
    x = [features_as_vector(row) for row in rows]
    y = [row.get("won_contest", 0.0) for row in rows]
    ids = [row.get("_case_id" , "") for row in rows]

    # Stratified split — preserves label ratio in both sets
    X_train, X_val, y_train, y_val, ids_train, ids_val = train_test_split(
        x, y, ids,
        test_size=1.0 - train_ratio,
        random_state=seed,
        stratify=y,
    )
    n_pos_train = sum(1 for label in y_train if label == 1.0)
    n_pos_val   = sum(1 for label in y_val   if label == 1.0)
    print(
        f"[dataset] Train: {len(X_train)} rows "
        f"({n_pos_train/len(y_train):.0%} won)"
    )

    print(
        f"[dataset]   Val: {len(X_val)} rows "
        f"({n_pos_val/len(y_val):.0%} won)"
    )
    return X_train, y_train, X_val, y_val
    


        
            
        

