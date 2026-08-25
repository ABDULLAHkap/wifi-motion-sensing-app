"""Train and evaluate the motion/no-motion classifier from app-recorded CSV files.

Input files are CSV files produced by the Android experiment recorder:
    timestamp,label,rssi_dbm,frequency_mhz,link_speed_mbps

Label mapping:
    EMPTY, PERSON_STILL -> NO_MOTION (0)
    PERSON_WALKING, OBJECT_MOVING -> MOTION (1)

The script converts raw time-series readings into rolling windows, extracts
statistical signal features, evaluates a held-out recording split and writes a
machine-readable accuracy report alongside the trained model.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
MODEL_OUT = ROOT / "models" / "motion_model.joblib"
REPORT_OUT = ROOT / "models" / "motion_model_metrics.json"
WINDOW_SIZE = 20
WINDOW_STEP = 10

LABEL_TO_TARGET = {
    "EMPTY": 0,
    "PERSON_STILL": 0,
    "PERSON_WALKING": 1,
    "OBJECT_MOVING": 1,
}

FEATURES = [
    "rssi_mean",
    "rssi_std",
    "rssi_var",
    "rssi_range",
    "rssi_mad",
    "rssi_change_mean",
    "rssi_change_max",
    "rssi_slope",
    "peak_count",
    "frequency_mean",
    "link_speed_mean",
    "link_speed_std",
]


def _slope(values: np.ndarray) -> float:
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values), dtype=float)
    return float(np.polyfit(x, values.astype(float), 1)[0])


def extract_features(window: pd.DataFrame) -> dict[str, float]:
    rssi = window["rssi_dbm"].astype(float).to_numpy()
    changes = np.abs(np.diff(rssi)) if len(rssi) > 1 else np.array([0.0])
    mean = float(np.mean(rssi))
    std = float(np.std(rssi))
    threshold = max(2.0, std * 1.5)
    peaks = int(np.sum(changes >= threshold))

    link = pd.to_numeric(window["link_speed_mbps"], errors="coerce").fillna(0).to_numpy(dtype=float)
    freq = pd.to_numeric(window["frequency_mhz"], errors="coerce").fillna(0).to_numpy(dtype=float)

    return {
        "rssi_mean": mean,
        "rssi_std": std,
        "rssi_var": float(np.var(rssi)),
        "rssi_range": float(np.max(rssi) - np.min(rssi)),
        "rssi_mad": float(np.mean(np.abs(rssi - mean))),
        "rssi_change_mean": float(np.mean(changes)),
        "rssi_change_max": float(np.max(changes)),
        "rssi_slope": _slope(rssi),
        "peak_count": float(peaks),
        "frequency_mean": float(np.mean(freq)),
        "link_speed_mean": float(np.mean(link)),
        "link_speed_std": float(np.std(link)),
    }


def load_windows() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    files = sorted(DATA_DIR.glob("*.csv"))
    if not files:
        raise SystemExit(
            f"No CSV files found in {DATA_DIR}. Copy datasets saved by the app into this folder first."
        )

    for csv_file in files:
        data = pd.read_csv(csv_file)
        required = {"timestamp", "label", "rssi_dbm", "frequency_mhz", "link_speed_mbps"}
        missing = required - set(data.columns)
        if missing:
            print(f"Skipping {csv_file.name}: missing {sorted(missing)}")
            continue

        data = data.dropna(subset=["label", "rssi_dbm"]).reset_index(drop=True)
        if data.empty:
            continue

        label_name = str(data["label"].iloc[0]).strip().upper()
        if label_name not in LABEL_TO_TARGET:
            print(f"Skipping {csv_file.name}: unknown label {label_name}")
            continue

        target = LABEL_TO_TARGET[label_name]
        if len(data) < WINDOW_SIZE:
            print(f"Skipping {csv_file.name}: only {len(data)} samples; need at least {WINDOW_SIZE}")
            continue

        for start in range(0, len(data) - WINDOW_SIZE + 1, WINDOW_STEP):
            window = data.iloc[start : start + WINDOW_SIZE]
            features = extract_features(window)
            features["target"] = target
            features["source_file"] = csv_file.name
            features["source_label"] = label_name
            rows.append(features)

    result = pd.DataFrame(rows)
    if result.empty:
        raise SystemExit("No usable windows were created from the available datasets.")
    return result


def evaluate(model: RandomForestClassifier, test: pd.DataFrame) -> dict[str, object]:
    y_true = test["target"]
    predictions = model.predict(test[FEATURES])
    probabilities = model.predict_proba(test[FEATURES])[:, 1]

    metrics: dict[str, object] = {
        "window_count": int(len(test)),
        "recording_count": int(test["source_file"].nunique()),
        "accuracy": round(float(accuracy_score(y_true, predictions)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_true, predictions)), 4),
        "precision_motion": round(float(precision_score(y_true, predictions, zero_division=0)), 4),
        "recall_motion": round(float(recall_score(y_true, predictions, zero_division=0)), 4),
        "f1_motion": round(float(f1_score(y_true, predictions, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_true, predictions, labels=[0, 1]).tolist(),
        "classification_report": classification_report(
            y_true,
            predictions,
            labels=[0, 1],
            target_names=["NO_MOTION", "MOTION"],
            output_dict=True,
            zero_division=0,
        ),
    }
    if y_true.nunique() == 2:
        metrics["roc_auc"] = round(float(roc_auc_score(y_true, probabilities)), 4)
    else:
        metrics["roc_auc"] = None
    return metrics


def main() -> None:
    windows = load_windows()
    print("Window counts by source label:")
    print(windows["source_label"].value_counts().to_string())

    if windows["target"].nunique() < 2:
        raise SystemExit("Need both NO_MOTION and MOTION recordings before a classifier can be trained.")
    if windows["source_file"].nunique() < 4:
        raise SystemExit("Collect at least four separate recordings before evaluating model accuracy.")

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_idx, test_idx = next(
        splitter.split(windows[FEATURES], windows["target"], groups=windows["source_file"])
    )
    train = windows.iloc[train_idx]
    test = windows.iloc[test_idx]

    model = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(train[FEATURES], train["target"])

    metrics = evaluate(model, test)
    print("\nHeld-out recording metrics:")
    for key in ["accuracy", "balanced_accuracy", "precision_motion", "recall_motion", "f1_motion", "roc_auc"]:
        print(f"{key}: {metrics[key]}")
    print("Confusion matrix [NO_MOTION, MOTION]:")
    print(np.array(metrics["confusion_matrix"]))

    importances = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
    print("\nFeature importance:")
    print(importances.to_string())

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": model,
        "features": FEATURES,
        "window_size": WINDOW_SIZE,
        "window_step": WINDOW_STEP,
        "label_mapping": LABEL_TO_TARGET,
        "metrics": metrics,
    }
    joblib.dump(bundle, MODEL_OUT)
    REPORT_OUT.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\nSaved model bundle to {MODEL_OUT}")
    print(f"Saved accuracy report to {REPORT_OUT}")


if __name__ == "__main__":
    main()
