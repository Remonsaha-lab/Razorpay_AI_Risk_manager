"""
backend/ml/evaluate.py

Evaluates model performance and business financial metrics.

Run:
    python -m backend.ml.evaluate
"""

from __future__ import annotations

import pickle #used for serializing and de-serializing Python object structures
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score, brier_score_loss

from backend.ml.dataset import load_all_features, load_held_out_features
from backend.ml.features import features_as_vector

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
CONTEST_FEE_INR = 500.0


def evaluate_system() -> dict:
    """Run full benchmark report on the dataset."""
    cal_path = ARTIFACTS_DIR / "calibrator.pkl"
    if not cal_path.exists():
        raise FileNotFoundError("calibrator.pkl not found. Run calibrate.py first.")

    with cal_path.open("rb") as handle:
        model = pickle.load(handle)

    # Final evaluation must use cases never seen during training or calibration.
    training_rows = load_all_features()
    rows = load_held_out_features()
    training_ids = {row["_case_id"] for row in training_rows}
    test_ids = {row["_case_id"] for row in rows}
    overlapping_ids = training_ids & test_ids
    if overlapping_ids:
        sample = ", ".join(sorted(overlapping_ids)[:5])
        raise ValueError(
            "Held-out test data overlaps with the training fixture dataset "
            f"({len(overlapping_ids)} case IDs; examples: {sample}). "
            "Create a disjoint test dataset before benchmarking."
        )
    X = np.array([features_as_vector(r) for r in rows])
    y_true = np.array([r.get("won_contest", 0.0) for r in rows])
    amounts = np.array([r.get("amount_raw", 0.0) for r in rows])

    # Calibrated Probabilities
    probs = model.predict_proba(X)[:, 1]
    y_pred = (probs >= 0.5).astype(int)

    # 1. Standard Metrics
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    auc = roc_auc_score(y_true, probs)
    brier = brier_score_loss(y_true, probs)

    # 2. Confusion Matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    # 3. Financial & Risk Metrics
    # False Contest: Model predicted win (1), but merchant lost (0) → wasted contest fee + lost dispute
    # False Accept:  Model predicted loss (0), but merchant could have won (1) → forfeited dispute value
    false_contest_cost = sum(amounts[i] + CONTEST_FEE_INR for i in range(len(y_true)) if y_pred[i] == 1 and y_true[i] == 0)
    false_accept_loss = sum(amounts[i] for i in range(len(y_true)) if y_pred[i] == 0 and y_true[i] == 1)
    recovered_value = sum(amounts[i] - CONTEST_FEE_INR for i in range(len(y_true)) if y_pred[i] == 1 and y_true[i] == 1)

    print("\n" + "=" * 60)
    print("       DISPUTEGUARD AI RISK MANAGER — BENCHMARK REPORT       ")
    print("=" * 60)
    print(f"Total Cases Evaluated:       {len(rows)}")
    print(f"Accuracy:                    {acc * 100:.2f}%")
    print(f"Contest Precision:           {prec * 100:.2f}% (when contesting, win rate)")
    print(f"Contest Recall:              {rec * 100:.2f}% (of all winnable disputes)")
    print(f"F1 Score:                    {f1:.4f}")
    print(f"ROC-AUC Score:               {auc:.4f}")
    print(f"Brier Score (Calibration):   {brier:.4f}")
    print("-" * 60)
    print(f"True Positives (Winnable Contests):   {tp}")
    print(f"True Negatives (Correctly Accepted):  {tn}")
    print(f"False Contests (Lost Fights):         {fp}  (Cost: ₹{false_contest_cost:,.2f})")
    print(f"False Accepts (Missed Wins):          {fn}  (Cost: ₹{false_accept_loss:,.2f})")
    print("-" * 60)
    print(f"Net Recovered Value:                  ₹{recovered_value:,.2f}")
    print("=" * 60 + "\n")

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": auc,
        "brier_score": brier,
        "false_contests": int(fp),
        "false_accepts": int(fn),
        "net_recovered_value_inr": recovered_value,
    }


if __name__ == "__main__":
    evaluate_system()
