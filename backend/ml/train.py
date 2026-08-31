"""
backend/ml/train.py
Trains XGBoost on the dispute training split and saves artifacts.
Run:
    python -m backend.ml.train
"""

import json
from datetime import datetime , timezone
from pathlib import Path
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score , f1_score , precision_score , recall_score , roc_auc_score 


from backend.ml.features import FEATURE_NAMES
from backend.ml.dataset import RANDOM_SEED , make_splits


ARTIFACTS_DIR = Path(__file__).parent / "artifacts" 
MODEL_VERSION = "xgboost_v2.0.0"
DATASET_VERSION = "fixtures_training_1000cases"
FEATURE_SCHEMA_VERSION = "2.0"

# Conservative hyperparameters for tabular dispute risk
XGBOOST_PARAMS = {
    "n_estimators": 150,
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 3,
    "reg_lambda": 1.0,
    "reg_alpha": 0.1,
    "n_jobs": 1,
    "early_stopping_rounds": 20,
    "eval_metric": "logloss",
    "random_state": RANDOM_SEED,
    "objective": "binary:logistic",
}

def train_model() -> dict:
    """Train XGBoost and save artifacts to backend/ml/artifacts/."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    print("{train} Loading the dataset splits")

    X_train , Y_train , X_val , Y_val = make_splits()

    print(f"[train] Training XGBoost on {len(X_train)} cases ....")

    model = xgb.XGBClassifier(
        **XGBOOST_PARAMS
    )

    model.fit(
        X_train, Y_train,
        eval_set=[(X_val, Y_val)],
        verbose=False,
    )

    ## Validation Evaluation (Raw Probalities)

    y_scores = model.predict_proba(X_val)[:,1]
    y_pred = (y_scores > 0.5).astype(int)

    metrics = {
        "accuracy" : float(accuracy_score(Y_val, y_pred)),
        "f1" : float(f1_score(Y_val, y_pred)),
        "precision" : float(precision_score(Y_val, y_pred)),
        "recall" : float(recall_score(Y_val, y_pred)),
        "auc" : float(roc_auc_score(Y_val, y_scores)),
    }   

    print("\n[train] Raw Validation Metrics")

    for k , v in metrics.items():
        print(f"  {k:9s} : {v:.4f}")

    print(f"\n[train] Saving artifacts to {ARTIFACTS_DIR}")

    # Top feature importances
    importances = dict(zip(FEATURE_NAMES, model.feature_importances_.tolist()))
    top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:8]
    print("\n[train] Top Features by Importance:")
    for name, score in top_features:
        bar = "█" * int(score * 30)
        print(f"  • {name:<35s} {score:.4f} {bar}")


    # Save model

    model_path = ARTIFACTS_DIR / "model.json"
    model.save_model(model_path)
    print(f"[train] Saved model to: {model_path}")

    # Save meta data

    X_validation = None
    feature_schema = {
        "model_version": MODEL_VERSION,
        "dataset_version": DATASET_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "feature_names": FEATURE_NAMES,
        "feature_count": len(FEATURE_NAMES),
        "model_type": "XGBClassifier",
        "model_parameters": model.get_params(),
        "training_rows": int(len(X_train)),
        "validation_rows": int(len(X_val)),
        "validation_metrics_raw_uncalibrated": metrics,
        "label_name": "won_contest",
        "label_definition": "1 means merchant won a contested dispute; 0 means merchant lost.",
    }

    # Save Feature Schema
    schema_path = ARTIFACTS_DIR / "feature_schema.json"
    schema_path.write_text(
        json.dumps(feature_schema, indent=2),
        encoding="utf-8"
    )
    print(
        f"[train] Saved feature schema to: "
        f"{schema_path}"
    )

    return {"model_path": str(model_path), "schema_path": str(schema_path)}

if __name__ == "__main__":
    train_model()

    


