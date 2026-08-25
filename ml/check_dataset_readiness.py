"""Check whether collected Wi-Fi motion datasets are ready for ML training.

Run from repository root:
    python ml/check_dataset_readiness.py

The script never fabricates accuracy. It reports exactly what recordings exist
and what is still missing for a defensible held-out evaluation.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
REQUIRED_LABELS = ["EMPTY", "PERSON_STILL", "PERSON_WALKING", "OBJECT_MOVING"]
MIN_SAMPLES_PER_RECORDING = 60
MIN_RECORDINGS_PER_LABEL = 3


def main() -> None:
    files = sorted(DATA_DIR.glob("*.csv"))
    if not files:
        print(f"NOT READY: no CSV recordings found in {DATA_DIR}")
        raise SystemExit(2)

    recordings = Counter()
    samples = Counter()
    invalid: list[str] = []

    for path in files:
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            invalid.append(f"{path.name}: cannot read ({exc})")
            continue

        required = {"timestamp", "label", "rssi_dbm", "frequency_mhz", "link_speed_mbps"}
        missing = required - set(df.columns)
        if missing:
            invalid.append(f"{path.name}: missing {sorted(missing)}")
            continue
        if df.empty:
            invalid.append(f"{path.name}: empty")
            continue

        label = str(df["label"].iloc[0]).strip().upper()
        if label not in REQUIRED_LABELS:
            invalid.append(f"{path.name}: unsupported label {label}")
            continue
        if len(df) < MIN_SAMPLES_PER_RECORDING:
            invalid.append(
                f"{path.name}: only {len(df)} samples (recommend >= {MIN_SAMPLES_PER_RECORDING})"
            )

        recordings[label] += 1
        samples[label] += len(df)

    print("Dataset readiness")
    print("-----------------")
    for label in REQUIRED_LABELS:
        count = recordings[label]
        total = samples[label]
        status = "OK" if count >= MIN_RECORDINGS_PER_LABEL else "MORE NEEDED"
        print(f"{label:16} recordings={count:2} samples={total:5}  {status}")

    if invalid:
        print("\nRecording warnings:")
        for item in invalid:
            print(f"- {item}")

    missing_labels = [
        label for label in REQUIRED_LABELS if recordings[label] < MIN_RECORDINGS_PER_LABEL
    ]
    if missing_labels:
        print(
            "\nNOT READY: collect at least "
            f"{MIN_RECORDINGS_PER_LABEL} separate recordings for every label."
        )
        print("Still needed for: " + ", ".join(missing_labels))
        raise SystemExit(2)

    print("\nREADY: enough separate recordings exist to train and evaluate the first motion model.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
