"""Experimental occupancy trainer for 0 / 1 / 2 / 3+ people.

Expected CSV files live in ml/data/occupancy/ and contain:
    timestamp,rssi_dbm,frequency_mhz,link_speed_mbps,occupancy

This model remains experimental because ordinary Android Wi-Fi APIs expose RSSI
rather than full CSI. Accuracy is therefore measured from held-out recordings
and never assumed.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data" / "occupancy"
MODEL_OUT = ROOT / "models" / "occupancy_model.joblib"
REPORT_OUT = ROOT / "models" / "occupancy_model_metrics.json"
WINDOW = 20


def features(frame: pd.DataFrame) -> dict[str, float]:
    rssi = frame["rssi_dbm"].astype(float)
    delta = rssi.diff().dropna()
    link = frame["link_speed_mbps"].fillna(0).astype(float)
    freq = frame["frequency_mhz"].fillna(0).astype(float)
    return {
        "rssi_mean": float(rssi.mean()),
        "rssi_std": float(rssi.std(ddof=0)),
        "rssi_range": float(rssi.max() - rssi.min()),
        "rssi_abs_change": float(delta.abs().mean()) if len(delta) else 0.0,
        "rssi_max_change": float(delta.abs().max()) if len(delta) else 0.0,
        "link_mean": float(link.mean()),
        "link_std": float(link.std(ddof=0)),
        "frequency_mean": float(freq.mean()),
    }


def load_windows() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for path in sorted(DATA_DIR.glob("*.csv")):
        df = pd.read_csv(path)
        required = {"rssi_dbm", "frequency_mhz", "link_speed_mbps", "occupancy"}
        if not required.issubset(df.columns):
            print(f"Skipping {path.name}: missing columns")
            continue
        for start in range(0, len(df) - WINDOW + 1, WINDOW):
            block = df.iloc[start:start + WINDOW]
            occupancy = str(block["occupancy"].mode().iloc[0])
            row = features(block)
            row["occupancy"] = occupancy
            row["experiment"] = path.stem
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    data = load_windows()
    if len(data) < 20 or data["occupancy"].nunique() < 2:
        raise SystemExit("Need more labelled occupancy experiments before training.")
    if data["experiment"].nunique() < 4:
        raise SystemExit("Collect at least four separate occupancy recordings before evaluating accuracy.")

    feature_cols = [c for c in data.columns if c not in {"occupancy", "experiment"}]
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_i, test_i = next(splitter.split(data, groups=data["experiment"]))
    train, test = data.iloc[train_i], data.iloc[test_i]

    model = RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced")
    model.fit(train[feature_cols], train["occupancy"])
    pred = model.predict(test[feature_cols])

    labels = sorted(data["occupancy"].astype(str).unique().tolist())
    metrics = {
        "window_count": int(len(test)),
        "recording_count": int(test["experiment"].nunique()),
        "accuracy": round(float(accuracy_score(test["occupancy"], pred)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(test["occupancy"], pred)), 4),
        "macro_f1": round(float(f1_score(test["occupancy"], pred, average="macro", zero_division=0)), 4),
        "labels": labels,
        "confusion_matrix": confusion_matrix(test["occupancy"], pred, labels=labels).tolist(),
        "classification_report": classification_report(
            test["occupancy"], pred, labels=labels, output_dict=True, zero_division=0
        ),
    }

    print("Held-out occupancy metrics:")
    print(f"accuracy: {metrics['accuracy']}")
    print(f"balanced_accuracy: {metrics['balanced_accuracy']}")
    print(f"macro_f1: {metrics['macro_f1']}")
    print("confusion_matrix:")
    print(pd.DataFrame(metrics["confusion_matrix"], index=labels, columns=labels))

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": feature_cols, "metrics": metrics}, MODEL_OUT)
    REPORT_OUT.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved experimental model to {MODEL_OUT}")
    print(f"Saved accuracy report to {REPORT_OUT}")


if __name__ == "__main__":
    main()
