"""Experimental occupancy trainer for 0 / 1 / 2 / 3+ people.

This script is intentionally not used by the live app until enough real labelled
recordings exist. Expected input CSV files are placed in ml/data/occupancy/ and
must contain: timestamp,rssi_dbm,frequency_mhz,link_speed_mbps,occupancy.
"""

from pathlib import Path
import math

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit

DATA_DIR = Path(__file__).parent / "data" / "occupancy"
MODEL_OUT = Path(__file__).parent / "models" / "occupancy_model.joblib"
WINDOW = 20


def features(frame: pd.DataFrame) -> dict[str, float]:
    rssi = frame["rssi_dbm"].astype(float)
    delta = rssi.diff().dropna()
    link = frame["link_speed_mbps"].fillna(0).astype(float)
    freq = frame["frequency_mhz"].fillna(0).astype(float)
    return {
        "rssi_mean": rssi.mean(),
        "rssi_std": rssi.std(ddof=0),
        "rssi_range": rssi.max() - rssi.min(),
        "rssi_abs_change": delta.abs().mean() if len(delta) else 0.0,
        "rssi_max_change": delta.abs().max() if len(delta) else 0.0,
        "link_mean": link.mean(),
        "link_std": link.std(ddof=0),
        "frequency_mean": freq.mean(),
    }


def load_windows() -> pd.DataFrame:
    rows = []
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

    feature_cols = [c for c in data.columns if c not in {"occupancy", "experiment"}]
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_i, test_i = next(splitter.split(data, groups=data["experiment"]))
    train, test = data.iloc[train_i], data.iloc[test_i]

    model = RandomForestClassifier(
        n_estimators=300, random_state=42, class_weight="balanced"
    )
    model.fit(train[feature_cols], train["occupancy"])
    pred = model.predict(test[feature_cols])

    print(classification_report(test["occupancy"], pred, digits=3))
    print(confusion_matrix(test["occupancy"], pred))

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": feature_cols}, MODEL_OUT)
    print(f"Saved experimental model to {MODEL_OUT}")


if __name__ == "__main__":
    main()
