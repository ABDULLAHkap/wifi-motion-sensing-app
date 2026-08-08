"""Train a first motion/no-motion classifier from labelled Wi-Fi samples.

Expected CSV columns:
    rssi,frequency_mhz,link_speed_mbps,label

`label` should be 0 for a stable/empty-room sample and 1 for a labelled
motion sample. This script is intentionally simple; useful accuracy depends on
collecting data from the real router/phone/room setup.
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

DATASET = Path(__file__).parent / "data" / "motion_samples.csv"
MODEL_OUT = Path(__file__).parent / "models" / "motion_model.joblib"

FEATURES = ["rssi", "frequency_mhz", "link_speed_mbps"]
TARGET = "label"


def main() -> None:
    if not DATASET.exists():
        raise SystemExit(
            f"Dataset not found: {DATASET}. Collect labelled real-device data first."
        )

    data = pd.read_csv(DATASET).dropna(subset=[TARGET])
    if data[TARGET].nunique() < 2:
        raise SystemExit("Dataset must contain both label 0 and label 1 samples.")

    x = data[FEATURES].fillna(0)
    y = data[TARGET].astype(int)

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    print(classification_report(y_test, predictions, digits=3))

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_OUT)
    print(f"Saved model to {MODEL_OUT}")


if __name__ == "__main__":
    main()
