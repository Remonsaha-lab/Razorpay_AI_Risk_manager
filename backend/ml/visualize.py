"""
backend/ml/visualize.py

Generates comprehensive ML pipeline verification charts:
  1. ROC Curve (held-out test set)
  2. Precision-Recall Curve (held-out test set)
  3. Calibration Curve (held-out test set)
  4. Learning Curve (training data, incremental sizes)
  5. Feature Importance (horizontal bar chart)
  6. Net-Value-by-Threshold Curve (business economics)

Run:
    python -m backend.ml.visualize

All plots are saved to backend/ml/artifacts/charts/
"""

from __future__ import annotations

import pickle
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for saving files
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import xgboost as xgb
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    auc,
    brier_score_loss,
    precision_recall_curve,
    roc_curve,
    roc_auc_score,
    f1_score,
    precision_score,
    recall_score,
)

from backend.ml.dataset import (
    RANDOM_SEED,
    load_all_features,
    load_held_out_features,
    make_splits,
)
from backend.ml.features import FEATURE_NAMES, features_as_vector

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
CHARTS_DIR = ARTIFACTS_DIR / "charts"
CONTEST_FEE_INR = 500.0

# ── Shared style ────────────────────────────────────────────────────────────
RAZORPAY_BLUE = "#072654"
RAZORPAY_TEAL = "#2DD4BF"
ACCENT_GREEN = "#10B981"
ACCENT_RED = "#EF4444"
ACCENT_AMBER = "#F59E0B"
ACCENT_PURPLE = "#8B5CF6"
BG_COLOR = "#0F172A"
GRID_COLOR = "#1E293B"
TEXT_COLOR = "#CBD5E1"
CARD_BG = "#1E293B"

plt.rcParams.update({
    "figure.facecolor": BG_COLOR,
    "axes.facecolor": BG_COLOR,
    "axes.edgecolor": GRID_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "text.color": TEXT_COLOR,
    "grid.color": GRID_COLOR,
    "grid.alpha": 0.3,
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
})


def _load_calibrated_model():
    """Load the calibrated model pipeline."""
    cal_path = ARTIFACTS_DIR / "calibrator.pkl"
    if not cal_path.exists():
        raise FileNotFoundError("calibrator.pkl not found. Run calibrate.py first.")
    with cal_path.open("rb") as f:
        return pickle.load(f)


def _load_base_model():
    """Load the raw XGBoost model."""
    model_path = ARTIFACTS_DIR / "model.json"
    if not model_path.exists():
        raise FileNotFoundError("model.json not found. Run train.py first.")
    model = xgb.XGBClassifier()
    model.load_model(str(model_path))
    return model


def _get_test_data():
    """Load held-out test features, X matrix, y labels, and amounts."""
    rows = load_held_out_features()
    X = np.array([features_as_vector(r) for r in rows])
    y = np.array([r.get("won_contest", 0.0) for r in rows])
    amounts = np.array([r.get("amount_raw", 0.0) for r in rows])
    return rows, X, y, amounts


def _save_fig(fig, name: str):
    """Save figure to the charts directory."""
    path = CHARTS_DIR / name
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  ✓ Saved: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════════
# 1. ROC CURVE
# ═══════════════════════════════════════════════════════════════════════════

def plot_roc_curve(y_true: np.ndarray, probs: np.ndarray) -> Path:
    """Plot ROC curve on held-out test data."""
    fpr, tpr, thresholds = roc_curve(y_true, probs)
    roc_auc = auc(fpr, tpr)

    fig, ax = plt.subplots(figsize=(8, 7))

    # Diagonal reference
    ax.plot([0, 1], [0, 1], "--", color=TEXT_COLOR, alpha=0.4, linewidth=1, label="Random (AUC = 0.50)")

    # Fill under curve
    ax.fill_between(fpr, tpr, alpha=0.15, color=RAZORPAY_TEAL)

    # Main curve
    ax.plot(fpr, tpr, color=RAZORPAY_TEAL, linewidth=2.5, label=f"XGBoost + Platt (AUC = {roc_auc:.4f})")

    # Find optimal point (Youden's J)
    j_scores = tpr - fpr
    best_idx = np.argmax(j_scores)
    ax.scatter(fpr[best_idx], tpr[best_idx], color=ACCENT_AMBER, s=120, zorder=5,
               edgecolors="white", linewidths=1.5)
    ax.annotate(f"Optimal\nThreshold={thresholds[best_idx]:.2f}\nTPR={tpr[best_idx]:.2f}, FPR={fpr[best_idx]:.2f}",
                xy=(fpr[best_idx], tpr[best_idx]),
                xytext=(fpr[best_idx] + 0.15, tpr[best_idx] - 0.15),
                fontsize=9, color=ACCENT_AMBER,
                arrowprops=dict(arrowstyle="->", color=ACCENT_AMBER, lw=1.5))

    ax.set_xlabel("False Positive Rate (FPR)")
    ax.set_ylabel("True Positive Rate (TPR)")
    ax.set_title("ROC Curve — Held-Out Test Set (200 Cases)")
    ax.legend(loc="lower right", framealpha=0.8, facecolor=CARD_BG, edgecolor=GRID_COLOR)
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.grid(True, alpha=0.2)

    return _save_fig(fig, "01_roc_curve.png")


# ═══════════════════════════════════════════════════════════════════════════
# 2. PRECISION-RECALL CURVE
# ═══════════════════════════════════════════════════════════════════════════

def plot_precision_recall_curve(y_true: np.ndarray, probs: np.ndarray) -> Path:
    """Plot Precision-Recall curve on held-out test data."""
    precision, recall, thresholds = precision_recall_curve(y_true, probs)
    pr_auc = auc(recall, precision)

    fig, ax = plt.subplots(figsize=(8, 7))

    # Fill under curve
    ax.fill_between(recall, precision, alpha=0.15, color=ACCENT_GREEN)

    # Main curve
    ax.plot(recall, precision, color=ACCENT_GREEN, linewidth=2.5,
            label=f"Precision-Recall (AUC = {pr_auc:.4f})")

    # Baseline (random classifier) = prevalence
    prevalence = y_true.mean()
    ax.axhline(y=prevalence, linestyle="--", color=TEXT_COLOR, alpha=0.4,
               label=f"Random baseline (prevalence = {prevalence:.2f})")

    # Mark key thresholds
    for thresh_val, marker_color, marker_label in [
        (0.40, ACCENT_AMBER, "τ=0.40"),
        (0.50, RAZORPAY_TEAL, "τ=0.50"),
        (0.70, ACCENT_PURPLE, "τ=0.70"),
    ]:
        idx = np.searchsorted(thresholds, thresh_val, side="left")
        if idx < len(precision) - 1:
            ax.scatter(recall[idx], precision[idx], s=100, color=marker_color,
                       zorder=5, edgecolors="white", linewidths=1.5)
            ax.annotate(f"{marker_label}\nP={precision[idx]:.2f}\nR={recall[idx]:.2f}",
                        xy=(recall[idx], precision[idx]),
                        xytext=(recall[idx] - 0.12, precision[idx] - 0.08),
                        fontsize=8, color=marker_color,
                        arrowprops=dict(arrowstyle="->", color=marker_color, lw=1.2))

    ax.set_xlabel("Recall (True Positive Rate)")
    ax.set_ylabel("Precision (Positive Predictive Value)")
    ax.set_title("Precision-Recall Curve — Held-Out Test Set")
    ax.legend(loc="lower left", framealpha=0.8, facecolor=CARD_BG, edgecolor=GRID_COLOR)
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([0, 1.05])
    ax.grid(True, alpha=0.2)

    return _save_fig(fig, "02_precision_recall_curve.png")


# ═══════════════════════════════════════════════════════════════════════════
# 3. CALIBRATION CURVE (RELIABILITY DIAGRAM)
# ═══════════════════════════════════════════════════════════════════════════

def plot_calibration_curve(y_true: np.ndarray, probs: np.ndarray) -> Path:
    """Plot calibration / reliability diagram on held-out test data."""
    prob_true, prob_pred = calibration_curve(y_true, probs, n_bins=10, strategy="uniform")
    brier = brier_score_loss(y_true, probs)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 9), gridspec_kw={"height_ratios": [3, 1]})

    # Top: Reliability diagram
    ax1.plot([0, 1], [0, 1], "--", color=TEXT_COLOR, alpha=0.5, linewidth=1, label="Perfectly Calibrated")
    ax1.plot(prob_pred, prob_true, "o-", color=RAZORPAY_TEAL, linewidth=2, markersize=8,
             markerfacecolor=ACCENT_GREEN, markeredgecolor="white", markeredgewidth=1.5,
             label=f"XGBoost + Platt (Brier = {brier:.4f})")

    # Highlight deviation bands
    for pred, true in zip(prob_pred, prob_true):
        deviation = abs(true - pred)
        color = ACCENT_GREEN if deviation < 0.05 else (ACCENT_AMBER if deviation < 0.10 else ACCENT_RED)
        ax1.vlines(pred, min(pred, true), max(pred, true), colors=color, alpha=0.6, linewidth=2)

    ax1.set_xlabel("Mean Predicted Probability")
    ax1.set_ylabel("Actual Win Rate (Fraction of Positives)")
    ax1.set_title("Calibration Curve — Held-Out Test Set")
    ax1.legend(loc="lower right", framealpha=0.8, facecolor=CARD_BG, edgecolor=GRID_COLOR)
    ax1.set_xlim([-0.02, 1.02])
    ax1.set_ylim([-0.02, 1.05])
    ax1.grid(True, alpha=0.2)

    # Bottom: Histogram of predicted probabilities
    ax2.hist(probs, bins=20, range=(0, 1), color=RAZORPAY_TEAL, alpha=0.6, edgecolor=BG_COLOR)
    ax2.set_xlabel("Predicted Probability")
    ax2.set_ylabel("Count")
    ax2.set_title("Distribution of Predicted Probabilities", fontsize=11)
    ax2.grid(True, alpha=0.2)

    fig.tight_layout(pad=2.0)
    return _save_fig(fig, "03_calibration_curve.png")


# ═══════════════════════════════════════════════════════════════════════════
# 4. LEARNING CURVE
# ═══════════════════════════════════════════════════════════════════════════

def plot_learning_curve() -> Path:
    """Plot learning curves showing train vs validation performance at increasing dataset sizes."""
    print("  Computing learning curve (this takes a moment)...")

    # Load full training data
    all_rows = load_all_features()
    X_all = np.array([features_as_vector(r) for r in all_rows])
    y_all = np.array([r.get("won_contest", 0.0) for r in all_rows])

    # Create a fixed validation hold-out (20%)
    from sklearn.model_selection import train_test_split
    X_pool, X_val, y_pool, y_val, = train_test_split(
        X_all, y_all, test_size=0.20, random_state=RANDOM_SEED, stratify=y_all
    )

    # Train with increasing fractions of the training pool
    fractions = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    train_sizes = []
    train_scores = []
    val_scores = []
    train_losses = []
    val_losses = []

    for frac in fractions:
        n = max(10, int(len(X_pool) * frac))
        X_sub = X_pool[:n]
        y_sub = y_pool[:n]

        model = xgb.XGBClassifier(
            n_estimators=150, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
            reg_lambda=1.0, reg_alpha=0.1, n_jobs=1,
            eval_metric="logloss", random_state=RANDOM_SEED,
            objective="binary:logistic",
        )
        model.fit(X_sub, y_sub, eval_set=[(X_val, y_val)], verbose=False)

        # Scores (AUC)
        train_probs = model.predict_proba(X_sub)[:, 1]
        val_probs = model.predict_proba(X_val)[:, 1]

        train_auc = roc_auc_score(y_sub, train_probs)
        val_auc = roc_auc_score(y_val, val_probs)

        train_brier = brier_score_loss(y_sub, train_probs)
        val_brier = brier_score_loss(y_val, val_probs)

        train_sizes.append(n)
        train_scores.append(train_auc)
        val_scores.append(val_auc)
        train_losses.append(train_brier)
        val_losses.append(val_brier)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Left: AUC learning curve
    ax1.plot(train_sizes, train_scores, "o-", color=RAZORPAY_TEAL, linewidth=2, markersize=6,
             label="Training AUC")
    ax1.plot(train_sizes, val_scores, "s-", color=ACCENT_AMBER, linewidth=2, markersize=6,
             label="Validation AUC")
    ax1.fill_between(train_sizes, train_scores, val_scores, alpha=0.1, color=ACCENT_AMBER)
    ax1.set_xlabel("Number of Training Cases")
    ax1.set_ylabel("ROC-AUC Score")
    ax1.set_title("Learning Curve — AUC vs Training Size")
    ax1.legend(loc="lower right", framealpha=0.8, facecolor=CARD_BG, edgecolor=GRID_COLOR)
    ax1.set_ylim([0.5, 1.02])
    ax1.grid(True, alpha=0.2)

    # Right: Brier Score (loss) learning curve
    ax2.plot(train_sizes, train_losses, "o-", color=RAZORPAY_TEAL, linewidth=2, markersize=6,
             label="Training Brier Loss")
    ax2.plot(train_sizes, val_losses, "s-", color=ACCENT_RED, linewidth=2, markersize=6,
             label="Validation Brier Loss")
    ax2.fill_between(train_sizes, train_losses, val_losses, alpha=0.1, color=ACCENT_RED)
    ax2.set_xlabel("Number of Training Cases")
    ax2.set_ylabel("Brier Score (Lower = Better)")
    ax2.set_title("Learning Curve — Calibration Loss vs Training Size")
    ax2.legend(loc="upper right", framealpha=0.8, facecolor=CARD_BG, edgecolor=GRID_COLOR)
    ax2.grid(True, alpha=0.2)

    fig.tight_layout(pad=3.0)
    return _save_fig(fig, "04_learning_curve.png")


# ═══════════════════════════════════════════════════════════════════════════
# 5. FEATURE IMPORTANCE CHART
# ═══════════════════════════════════════════════════════════════════════════

def plot_feature_importance() -> Path:
    """Plot horizontal bar chart of XGBoost feature importances."""
    model = _load_base_model()
    importances = dict(zip(FEATURE_NAMES, model.feature_importances_.tolist()))

    # Sort by importance
    sorted_feats = sorted(importances.items(), key=lambda x: x[1], reverse=False)
    names = [f[0] for f in sorted_feats]
    values = [f[1] for f in sorted_feats]

    fig, ax = plt.subplots(figsize=(10, 9))

    # Color gradient based on importance
    max_val = max(values) if values else 1
    colors = [plt.cm.RdYlGn(v / max_val * 0.8 + 0.1) for v in values]

    bars = ax.barh(range(len(names)), values, color=colors, edgecolor=BG_COLOR, linewidth=0.5, height=0.7)

    # Add value labels
    for bar, val in zip(bars, values):
        if val > 0.001:
            ax.text(bar.get_width() + max_val * 0.01, bar.get_y() + bar.get_height() / 2,
                    f"{val:.4f}", va="center", fontsize=8, color=TEXT_COLOR)

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("Feature Importance (Gain)")
    ax.set_title("XGBoost Feature Importance — All 33 Features")
    ax.grid(True, axis="x", alpha=0.2)

    # Highlight top 5
    top5_indices = list(range(len(names) - 5, len(names)))
    for idx in top5_indices:
        ax.get_yticklabels()[idx].set_color(RAZORPAY_TEAL)
        ax.get_yticklabels()[idx].set_fontweight("bold")

    fig.tight_layout()
    return _save_fig(fig, "05_feature_importance.png")


# ═══════════════════════════════════════════════════════════════════════════
# 6. NET-VALUE-BY-THRESHOLD CURVE
# ═══════════════════════════════════════════════════════════════════════════

def plot_net_value_by_threshold(y_true: np.ndarray, probs: np.ndarray, amounts: np.ndarray) -> Path:
    """
    For each threshold, compute:
      - True contests (wins): recovered_value = amount - contest_fee
      - False contests (losses): cost = amount + contest_fee
      - False accepts (missed wins): missed = amount
      - Net value = recovered - false_contest_cost - false_accept_loss
    """
    thresholds = np.linspace(0.05, 0.95, 50)
    net_values = []
    n_contests = []
    false_contest_counts = []
    precisions = []

    for thresh in thresholds:
        y_pred = (probs >= thresh).astype(int)

        # Financial calculation
        tp_mask = (y_pred == 1) & (y_true == 1)  # True contests (won)
        fp_mask = (y_pred == 1) & (y_true == 0)  # False contests (lost)
        fn_mask = (y_pred == 0) & (y_true == 1)  # False accepts (missed wins)

        recovered = np.sum(amounts[tp_mask] - CONTEST_FEE_INR)
        false_cost = np.sum(amounts[fp_mask] + CONTEST_FEE_INR)
        missed = np.sum(amounts[fn_mask])

        net = recovered - false_cost
        net_values.append(net)
        n_contests.append(int(y_pred.sum()))
        false_contest_counts.append(int(fp_mask.sum()))

        prec = precision_score(y_true, y_pred, zero_division=0)
        precisions.append(prec)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), gridspec_kw={"height_ratios": [2, 1]})

    # Top: Net Value curve
    net_values_lakhs = [v / 100_000 for v in net_values]
    ax1.plot(thresholds, net_values_lakhs, color=ACCENT_GREEN, linewidth=2.5, label="Net Recovered Value")
    ax1.fill_between(thresholds, net_values_lakhs, alpha=0.15, color=ACCENT_GREEN)

    # Mark optimal threshold
    best_idx = np.argmax(net_values)
    best_thresh = thresholds[best_idx]
    best_val = net_values_lakhs[best_idx]
    ax1.scatter(best_thresh, best_val, s=150, color=ACCENT_AMBER, zorder=5,
                edgecolors="white", linewidths=2)
    ax1.annotate(f"Optimal τ={best_thresh:.2f}\n₹{best_val:.1f}L net value\n"
                 f"{n_contests[best_idx]} contests, {false_contest_counts[best_idx]} false",
                 xy=(best_thresh, best_val),
                 xytext=(best_thresh + 0.12, best_val - best_val * 0.15),
                 fontsize=9, color=ACCENT_AMBER,
                 arrowprops=dict(arrowstyle="->", color=ACCENT_AMBER, lw=1.5))

    # Mark the default τ=0.50
    idx_50 = np.argmin(np.abs(thresholds - 0.50))
    ax1.axvline(x=0.50, color=TEXT_COLOR, alpha=0.3, linestyle="--")
    ax1.scatter(0.50, net_values_lakhs[idx_50], s=80, color=RAZORPAY_TEAL, zorder=5,
                edgecolors="white", linewidths=1.5)
    ax1.annotate(f"Default τ=0.50\n₹{net_values_lakhs[idx_50]:.1f}L",
                 xy=(0.50, net_values_lakhs[idx_50]),
                 xytext=(0.50 - 0.18, net_values_lakhs[idx_50] + best_val * 0.08),
                 fontsize=9, color=RAZORPAY_TEAL,
                 arrowprops=dict(arrowstyle="->", color=RAZORPAY_TEAL, lw=1.2))

    ax1.set_xlabel("Contest Probability Threshold (τ)")
    ax1.set_ylabel("Net Recovered Value (₹ Lakhs)")
    ax1.set_title("Net Value by Threshold — Financial Risk Analysis")
    ax1.legend(loc="upper right", framealpha=0.8, facecolor=CARD_BG, edgecolor=GRID_COLOR)
    ax1.grid(True, alpha=0.2)

    # Bottom: Precision and contest count
    ax2_twin = ax2.twinx()
    ax2.plot(thresholds, precisions, color=ACCENT_PURPLE, linewidth=2, label="Precision")
    ax2_twin.plot(thresholds, n_contests, color=ACCENT_AMBER, linewidth=2, linestyle="--", label="# Contests")

    ax2.set_xlabel("Contest Probability Threshold (τ)")
    ax2.set_ylabel("Precision", color=ACCENT_PURPLE)
    ax2_twin.set_ylabel("Number of Contests", color=ACCENT_AMBER)
    ax2.set_title("Precision vs Contest Volume by Threshold", fontsize=11)
    ax2.set_ylim([0, 1.05])
    ax2.grid(True, alpha=0.2)

    # Combined legend
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="center right",
               framealpha=0.8, facecolor=CARD_BG, edgecolor=GRID_COLOR)

    fig.tight_layout(pad=2.0)
    return _save_fig(fig, "06_net_value_by_threshold.png")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def generate_all_charts():
    """Generate all 6 verification charts."""
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  DISPUTEGUARD ML PIPELINE — VISUALIZATION REPORT")
    print("=" * 60)

    # Load data
    print("\n[1/6] Loading held-out test data and calibrated model...")
    calibrated_model = _load_calibrated_model()
    rows, X_test, y_test, amounts = _get_test_data()
    probs = calibrated_model.predict_proba(X_test)[:, 1]
    print(f"  Loaded {len(rows)} test cases, {int(y_test.sum())} positive (won)")

    # 1. ROC Curve
    print("\n[1/6] Generating ROC Curve...")
    plot_roc_curve(y_test, probs)

    # 2. Precision-Recall Curve
    print("\n[2/6] Generating Precision-Recall Curve...")
    plot_precision_recall_curve(y_test, probs)

    # 3. Calibration Curve
    print("\n[3/6] Generating Calibration Curve...")
    plot_calibration_curve(y_test, probs)

    # 4. Learning Curve
    print("\n[4/6] Generating Learning Curve...")
    plot_learning_curve()

    # 5. Feature Importance
    print("\n[5/6] Generating Feature Importance Chart...")
    plot_feature_importance()

    # 6. Net-Value-by-Threshold
    print("\n[6/6] Generating Net-Value-by-Threshold Curve...")
    plot_net_value_by_threshold(y_test, probs, amounts)

    print("\n" + "=" * 60)
    print(f"  All 6 charts saved to: {CHARTS_DIR}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    generate_all_charts()
