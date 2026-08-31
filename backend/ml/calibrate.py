"""
backend/ml/calibrate.py

Fits probability calibration (Platt Scaling) over the validation set.
This script applies Platt Scaling (Sigmoid Calibration) on the validation set so output probabilities accurately reflect true historical win rates.
Run:
    python -m backend.ml.calibrate
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss

from backend.ml.dataset import make_splits

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


def calibrate_model() -> dict:
    """Calibrate XGBoost model probabilities using the validation split."""
    model_path = ARTIFACTS_DIR / "model.json"
    if not model_path.exists():
        raise FileNotFoundError("model.json not found. Run python -m backend.ml.train first.")

    # Load trained model
    base_model = xgb.XGBClassifier()
    base_model.load_model(str(model_path))

    # Load splits
    X_train, y_train, X_val, y_val = make_splits()

    X_val_np = np.array(X_val)
    y_val_np = np.array(y_val)

    # 1. Raw Brier Score
    raw_probs = base_model.predict_proba(X_val_np)[:, 1]
    raw_brier = brier_score_loss(y_val_np, raw_probs)

    # 2. Fit Platt Scaling (Sigmoid) on validation set
    calibrator = CalibratedClassifierCV(estimator=base_model, method="sigmoid", cv="prefit")
    calibrator.fit(X_val_np, y_val_np)

    # 3. Calibrated Brier Score
    cal_probs = calibrator.predict_proba(X_val_np)[:, 1]
    cal_brier = brier_score_loss(y_val_np, cal_probs)

    print("\n[calibration] Probability Calibration Results:")
    print(f"  • Raw Model Brier Score:        {raw_brier:.4f}")
    print(f"  • Calibrated Model Brier Score: {cal_brier:.4f} (lower is better)")
    print(f"  • Improvement:                  {(raw_brier - cal_brier) / raw_brier * 100:.1f}%")

    # 4. Calibration Curve (Reliability Bins)
    prob_true, prob_pred = calibration_curve(y_val_np, cal_probs, n_bins=5)
    print("\n[calibration] Reliability Diagram (Predicted vs Actual Win Rate):")
    for pred, true in zip(prob_pred, prob_true):
        print(f"  • Predicted: {pred * 100:5.1f}%  →  Actual Win Rate: {true * 100:5.1f}%")

    # 5. Save Calibrator Artifact
    cal_path = ARTIFACTS_DIR / "calibrator.pkl"
    with cal_path.open("wb") as handle:
        pickle.dump(calibrator, handle)
    print(f"\n[calibration] Calibrator saved → {cal_path}")

    return {
        "raw_brier": raw_brier,
        "calibrated_brier": cal_brier,
        "calibrator_path": str(cal_path),
    }


if __name__ == "__main__":
    calibrate_model()
