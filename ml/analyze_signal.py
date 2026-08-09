"""Analyze labelled Wi-Fi CSV recordings produced by the Android app.

Usage:
    python analyze_signal.py

Place exported recorder CSV files inside ml/data/. The script prints per-file
statistics including RSSI mean/variance/std, moving-average variation, peaks,
rate of change, frequency and link-speed summaries.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
ROLLING_WINDOW = 10


def analyze_file(path: Path) -> dict[str, object]:
    df = pd.read_csv(path)
    required = {"timestamp", "label", "rssi_dbm", "frequency_mhz", "link_speed_mbps"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    df = df.dropna(subset=["rssi_dbm"]).copy()
    if df.empty:
        raise ValueError("no RSSI samples")

    rssi = pd.to_numeric(df["rssi_dbm"], errors="coerce").dropna()
    changes = rssi.diff().abs().dropna()
    moving_average = rssi.rolling(ROLLING_WINDOW, min_periods=1).mean()
    residual = (rssi - moving_average).abs()

    std = float(rssi.std(ddof=0))
    peak_threshold = max(2.0, std * 1.5)
    peak_count = int((changes >= peak_threshold).sum())

    freq = pd.to_numeric(df["frequency_mhz"], errors="coerce").dropna()
    link = pd.to_numeric(df["link_speed_mbps"], errors="coerce").dropna()

    return {
        "file": path.name,
        "label": str(df["label"].iloc[0]),
        "samples": int(len(rssi)),
        "rssi_mean": round(float(rssi.mean()), 3),
        "rssi_std": round(std, 3),
        "rssi_variance": round(float(rssi.var(ddof=0)), 3),
        "rssi_min": int(rssi.min()),
        "rssi_max": int(rssi.max()),
        "rssi_range": round(float(rssi.max() - rssi.min()), 3),
        "mean_abs_change": round(float(changes.mean()) if len(changes) else 0.0, 3),
        "max_abs_change": round(float(changes.max()) if len(changes) else 0.0, 3),
        "moving_average_residual": round(float(residual.mean()), 3),
        "peak_threshold_db": round(peak_threshold, 3),
        "peak_count": peak_count,
        "frequency_mean_mhz": round(float(freq.mean()), 3) if len(freq) else None,
        "link_speed_mean_mbps": round(float(link.mean()), 3) if len(link) else None,
        "link_speed_std": round(float(link.std(ddof=0)), 3) if len(link) else None,
    }


def main() -> None:
    files = sorted(DATA_DIR.glob("*.csv"))
    if not files:
        raise SystemExit(
            f"No CSV files found in {DATA_DIR}. Export/copy app recordings into this folder first."
        )

    results = []
    for path in files:
        try:
            results.append(analyze_file(path))
        except Exception as exc:
            print(f"Skipping {path.name}: {exc}")

    if not results:
        raise SystemExit("No usable recordings were found.")

    report = pd.DataFrame(results)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    print("\nPer-recording signal analysis:\n")
    print(report.to_string(index=False))

    print("\nAverage statistics by label:\n")
    numeric = report.select_dtypes(include=[np.number]).columns
    grouped = report.groupby("label")[numeric].mean(numeric_only=True)
    print(grouped.to_string())

    out = ROOT / "analysis_summary.csv"
    report.to_csv(out, index=False)
    print(f"\nSaved summary to {out}")


if __name__ == "__main__":
    main()
