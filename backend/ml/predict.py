"""
backend/ml/predict.py

Inference service loading trained and calibrated models.
"""

from __future__ import annotations

import pickle
import json
from pathlib import Path
from typing import Any

import numpy as np
import xgboost as xgb

from backend.ml.features import FEATURE_NAMES, features_as_vector

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"

_model = None
_calibrator = None
_schema = None


class ModelNotAvailableError(RuntimeError):
    """Raised when a complete, compatible ML model artifact is unavailable."""


def load_artifacts() -> None:
    """Load model and calibrator into memory singleton."""
    global _model, _calibrator, _schema

    model_path = ARTIFACTS_DIR / "model.json"
    cal_path = ARTIFACTS_DIR / "calibrator.pkl"
    schema_path = ARTIFACTS_DIR / "feature_schema.json"
    missing = [str(path.name) for path in (model_path, cal_path, schema_path) if not path.exists()]
    if missing:
        raise ModelNotAvailableError(
            "ML prediction is unavailable; missing artifact(s): " + ", ".join(missing)
        )

    if _schema is None:
        _schema = json.loads(schema_path.read_text(encoding="utf-8"))
        artifact_features = _schema.get("feature_names")
        if artifact_features != FEATURE_NAMES:
            raise ModelNotAvailableError(
                "ML feature schema mismatch. Retrain and recalibrate the model before prediction."
            )
        if _schema.get("feature_count") != len(FEATURE_NAMES):
            raise ModelNotAvailableError("ML feature count mismatch. Retrain the model.")

    if _model is None:
        _model = xgb.XGBClassifier()
        _model.load_model(str(model_path))

    if _calibrator is None:
        with cal_path.open("rb") as handle:
            _calibrator = pickle.load(handle)


def predict_contest_probability(feature_dict: dict[str, float]) -> dict[str, Any]:
    """
    Predict contest win probability for a single case.

    Returns
    -------
    dict:
        calibrated_probability: float [0.0 - 1.0]
        raw_score: float [0.0 - 1.0]
        is_calibrated: bool
    """
    load_artifacts()
    vec = np.array([features_as_vector(feature_dict)])

    raw_score = float(_model.predict_proba(vec)[0, 1])
    cal_prob = float(_calibrator.predict_proba(vec)[0, 1])

    return {
        "raw_score": round(raw_score, 4),
        "calibrated_probability": round(cal_prob, 4),
        "is_calibrated": True,
        "model_version": _schema.get("model_version", "unknown"),
        "dataset_version": _schema.get("dataset_version", "unknown"),
        "feature_schema_version": _schema.get("feature_schema_version", "unknown"),
    }
